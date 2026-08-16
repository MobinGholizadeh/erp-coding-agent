import json
from typing import Optional
from ...llm.client import LLMClient
from ...llm.models import LLMRequest, Message, Role, Tool, ToolFunction
from ..context.context_manager import ContextManager
from .tool_executor import ToolExecutor
from ..controller.transitions import StateMachine

class ExecutionLoop:
    def __init__(
        self, 
        llm: LLMClient, 
        executor: ToolExecutor, 
        context: ContextManager, 
        state_machine: StateMachine,
        max_attempts: int = 15
    ):
        self.llm = llm
        self.executor = executor
        self.context = context
        self.state_machine = state_machine
        self.max_attempts = max_attempts

    def _get_tools(self) -> list[Tool]:
        tools = []
        for schema in self.executor.registry.get_all_schemas():
            func_schema = schema["function"]
            tools.append(Tool(
                function=ToolFunction(
                    name=func_schema["name"],
                    description=func_schema["description"],
                    parameters=func_schema["parameters"]
                )
            ))
        
        # Add special submit_solution tool
        tools.append(Tool(
            function=ToolFunction(
                name="submit_solution",
                description="Submit the final result to the user.",
                parameters={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Summary of what was done"}
                    },
                    "required": ["summary"]
                }
            )
        ))
        return tools

    async def run(self) -> str:
        """
        Runs the execution loop until 'submit_solution' is called or max_attempts is reached.
        Returns the final result status or summary.
        """
        attempts = 0
        tools = self._get_tools()
        
        while attempts < self.max_attempts:
            attempts += 1
            
            # 1. Ask LLM what to do next
            request = LLMRequest(
                messages=self.context.get_messages(),
                tools=tools
            )
            
            response = await self.llm.generate(request)
            
            # 2. Append LLM response to context
            self.context.append_message(
                Role.ASSISTANT, 
                content=response.content,
                tool_calls=response.tool_calls
            )
            
            if not response.tool_calls:
                self.context.append_tool_result("system", "Error: No tool calls provided by the model.")
                continue
                
            # We process the first tool call (or all of them, but let's assume sequential for now)
            # Actually, let's process all returned tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    self.context.append_tool_result(tool_name, "Error: Invalid JSON arguments.", tool_call.id)
                    continue
                
                self.state_machine.record_action(
                    "TOOL_CALL", 
                    {"tool": tool_name, "arguments": arguments}
                )
                
                # 3. Check for termination condition
                if tool_name == "submit_solution":
                    self.state_machine.record_action("SUBMIT_SOLUTION_CALLED", arguments)
                    return arguments.get("summary", "Task completed via submit_solution.")
                    
                # 4. Execute the tool
                result_str = await self.executor.execute(tool_name, arguments)
                self.state_machine.record_action("TOOL_RESULT", {"tool": tool_name, "result": result_str})
                
                # 5. Feed result back to context
                self.context.append_tool_result(tool_name, result_str, tool_call.id)

        return f"Max attempts ({self.max_attempts}) reached without completion."
