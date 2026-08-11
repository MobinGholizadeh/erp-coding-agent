import json
from ...llm.client import LLMClient
from ...tools.registry import ToolRegistry
from ..context.context_manager import ContextManager
from ..planner.planner import Planner
from ..executor.tool_executor import ToolExecutor
from ..executor.tool_loop import ExecutionLoop
from ..prompts.executor import EXECUTOR_SYSTEM_PROMPT
from .transitions import StateMachine
from .state_machine import AgentState

class AgentController:
    def __init__(self, llm_client: LLMClient, tool_registry: ToolRegistry, max_attempts: int = 15):
        self.llm = llm_client
        self.registry = tool_registry
        self.max_attempts = max_attempts
        self.state_machine = StateMachine()

    async def run_task(self, task: str) -> str:
        """
        Executes the entire agent lifecycle for a given task.
        """
        try:
            # 1. PLANNING
            self.state_machine.transition_to(AgentState.PLANNING)
            planner = Planner(self.llm)
            plan = await planner.create_plan(task)
            
            if not plan:
                self.state_machine.transition_to(AgentState.FAILED, "Planner failed to generate a valid plan.")
                return "Failed to generate plan."
                
            self.state_machine.record_action("PLAN_GENERATED", {"steps": len(plan.steps)})

            # 2. RETRIEVING_CONTEXT
            self.state_machine.transition_to(AgentState.RETRIEVING_CONTEXT)
            # In Phase 4, we just initialize the ContextManager with the Executor prompt
            # injecting the tool schemas and the plan.
            schemas = self.registry.get_all_schemas()
            
            system_prompt = EXECUTOR_SYSTEM_PROMPT + "\n\nAvailable Tools:\n" + json.dumps(schemas, indent=2)
            
            context = ContextManager(system_prompt=system_prompt)
            context.append_message(
                role="user", 
                content=f"Task:\n{task}\n\nPlan:\n{plan.model_dump_json(indent=2)}\n\nPlease begin execution."
            )
            
            # 3. EXECUTING
            self.state_machine.transition_to(AgentState.EXECUTING)
            executor = ToolExecutor(self.registry)
            loop = ExecutionLoop(
                llm=self.llm,
                executor=executor,
                context=context,
                state_machine=self.state_machine,
                max_attempts=self.max_attempts
            )
            
            result_summary = await loop.run()
            
            # 4. VALIDATING
            self.state_machine.transition_to(AgentState.VALIDATING)
            
            # In Phase 4, validation is mocked as always passing if loop completes via submit_solution.
            # Real validation would check build/test outcomes or ask the LLM to verify.
            is_valid = "Max attempts" not in result_summary
            
            # 5. COMPLETED or FAILED
            if is_valid:
                self.state_machine.transition_to(AgentState.COMPLETED, "Validation passed.")
            else:
                self.state_machine.transition_to(AgentState.FAILED, "Task reached max attempts or failed validation.")
                
            return result_summary
            
        except Exception as e:
            if self.state_machine.current_state != AgentState.FAILED:
                self.state_machine.transition_to(AgentState.FAILED, str(e))
            return f"Controller Error: {str(e)}"
