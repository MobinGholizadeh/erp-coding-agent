from typing import Optional
from ...llm.client import LLMClient
from ...llm.models import LLMRequest, Message, Role
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

    async def run(self) -> str:
        """
        Runs the execution loop until 'submit_solution' is called or max_attempts is reached.
        Returns the final result status or summary.
        """
        attempts = 0
        
        while attempts < self.max_attempts:
            attempts += 1
            
            # 1. Ask LLM what to do next
            request = LLMRequest(
                messages=self.context.get_messages(),
                response_format={"type": "json_object"}
            )
            
            response = await self.llm.generate(request)
            
            # The LLM's raw response goes into the context as the assistant's action
            self.context.append_message(Role.ASSISTANT, response.content)
            
            # 2. Parse the LLM's requested action
            if not response.structured_data:
                self.context.append_tool_result("system", "Error: Response was not valid JSON.")
                continue
                
            tool_name = response.structured_data.get("tool")
            arguments = response.structured_data.get("arguments", {})
            thought = response.structured_data.get("thought", "")
            
            self.state_machine.record_action(
                "LLM_THOUGHT", 
                {"thought": thought, "tool": tool_name}
            )
            
            if not tool_name:
                self.context.append_tool_result("system", "Error: No 'tool' specified in JSON.")
                continue
                
            # 3. Check for termination condition
            if tool_name == "submit_solution":
                self.state_machine.record_action("SUBMIT_SOLUTION_CALLED", arguments)
                return arguments.get("summary", "Task completed via submit_solution.")
                
            # 4. Execute the tool
            self.state_machine.record_action("TOOL_CALL", {"tool": tool_name, "arguments": arguments})
            result_str = await self.executor.execute(tool_name, arguments)
            self.state_machine.record_action("TOOL_RESULT", {"tool": tool_name, "result": result_str})
            
            # 5. Feed result back to context
            self.context.append_tool_result(tool_name, result_str)

        return f"Max attempts ({self.max_attempts}) reached without completion."
