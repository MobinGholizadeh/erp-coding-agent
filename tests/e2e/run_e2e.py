import asyncio
import os
import sys
import json

os.environ["AGENT__MAX_ATTEMPTS"] = "15"

# Ensure the src directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from erp_coding_agent.config.settings import get_settings
from erp_coding_agent.services.task_manager import get_task_manager
from erp_coding_agent.domain.states import TaskStatus
from erp_coding_agent.llm.client import MockLLM
from erp_coding_agent.llm.models import LLMResponse, ToolCall, ToolCallFunction

async def run_e2e():
    print("Starting Phase 10 E2E Agent Test...")
    
    settings = get_settings()
    settings.agent.max_attempts = 15
    settings.llm.provider = "mock"
    
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../mock-erp"))
    print(f"Target repository: {repo_path}")
    
    settings.build.command = "echo 'No build required for python'"
    settings.test.command = "pytest"

    mock_llm = MockLLM()
    
    # 1. Planner response
    mock_llm.queue_response(LLMResponse(
        content="Plan created.",
        structured_data={
            "steps": [
                {"id": 1, "description": "Search code for discount logic", "expected_outcome": "Found code"},
                {"id": 2, "description": "Find Invoice symbol", "expected_outcome": "Found symbol"},
                {"id": 3, "description": "Read invoice.py", "expected_outcome": "Read file"},
                {"id": 4, "description": "Modify invoice.py to add discount but with a bug", "expected_outcome": "File modified"},
                {"id": 5, "description": "Run tests and detect failure", "expected_outcome": "Tests failed"},
                {"id": 6, "description": "Fix the bug in invoice.py", "expected_outcome": "File fixed"},
                {"id": 7, "description": "Run tests successfully", "expected_outcome": "Tests passed"},
                {"id": 8, "description": "Submit solution", "expected_outcome": "Solution submitted"}
            ],
            "initial_context_queries": []
        }
    ))
    
    # 2. Search code
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_search",
            function=ToolCallFunction(
                name="search_code",
                arguments=json.dumps({"query": "customer discount"})
            )
        )]
    ))
    
    # 3. Find symbol
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_symbol",
            function=ToolCallFunction(
                name="find_symbol",
                arguments=json.dumps({"name": "Invoice"})
            )
        )]
    ))
    
    # 4. Read file
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_read",
            function=ToolCallFunction(
                name="read_file",
                arguments=json.dumps({"file_path": "invoice.py"})
            )
        )]
    ))
    
    # 5. Modify code (introduce bug: discount applied after tax)
    edit_bug_args = {
        "target_file": "invoice.py",
        "instruction": "Add customer discount",
        "replacement_chunks": [
            {
                "target_content": "    def calculate_total(self) -> float:\n        # Currently no customer discount logic implemented\n        tax = self.subtotal * 0.10\n        return self.subtotal + tax",
                "replacement_content": "    def __init__(self, subtotal: float):\n        self.subtotal = subtotal\n        self.customer_discount_percentage = 0.0\n\n    def calculate_total(self) -> float:\n        tax = self.subtotal * 0.10\n        discount = self.subtotal * (self.customer_discount_percentage / 100)\n        return self.subtotal + tax - discount"
            }
        ]
    }
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_edit_1",
            function=ToolCallFunction(
                name="edit_file",
                arguments=json.dumps(edit_bug_args)
            )
        )]
    ))
    
    # 6. Run build
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_build",
            function=ToolCallFunction(
                name="run_build",
                arguments="{}"
            )
        )]
    ))
    
    # 7. Run tests (will fail)
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_test_1",
            function=ToolCallFunction(
                name="run_tests",
                arguments="{}"
            )
        )]
    ))
    
    # 8. Fix the bug (discount applied before tax)
    edit_fix_args = {
        "target_file": "invoice.py",
        "instruction": "Fix customer discount logic",
        "replacement_chunks": [
            {
                "target_content": "    def calculate_total(self) -> float:\n        tax = self.subtotal * 0.10\n        discount = self.subtotal * (self.customer_discount_percentage / 100)\n        return self.subtotal + tax - discount",
                "replacement_content": "    def calculate_total(self) -> float:\n        discounted_subtotal = self.subtotal * (1 - self.customer_discount_percentage / 100)\n        tax = discounted_subtotal * 0.10\n        return discounted_subtotal + tax"
            }
        ]
    }
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_edit_2",
            function=ToolCallFunction(
                name="edit_file",
                arguments=json.dumps(edit_fix_args)
            )
        )]
    ))
    
    # 9. Retest (will pass)
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_test_2",
            function=ToolCallFunction(
                name="run_tests",
                arguments="{}"
            )
        )]
    ))
    
    # 10. Submit solution
    mock_llm.queue_response(LLMResponse(
        tool_calls=[ToolCall(
            id="call_submit",
            function=ToolCallFunction(
                name="submit_solution",
                arguments=json.dumps({"summary": "Added customer discount logic before tax calculation and verified with tests."})
            )
        )]
    ))

    # Get TaskManager and inject mock LLM
    tm = get_task_manager()
    tm._llm_client = mock_llm

    # Create Task
    instruction = "Add customer discount support to invoice calculation. Customer discount percentage should be applied to subtotal before tax."
    print(f"Creating task with instruction: {instruction}")
    
    task = tm.create_task(instruction=instruction, repository=repo_path)
    print(f"Task created: {task.task_id}")

    # Subscribe to events
    print("\n--- Event Stream ---")
    async for event_str in tm.subscribe_events(task.task_id):
        if not event_str.startswith("event: "):
            continue
            
        event_type = event_str.split("\n")[0].replace("event: ", "")
        print(f"[{event_type}]")
        
        if event_type in ("TASK_COMPLETED", "TASK_FAILED", "TASK_CANCELLED"):
            break
            
    print("--- Stream Closed ---\n")

    # Verify outcome
    final_task = tm.get_task(task.task_id)
    print(f"Final Task Status: {final_task.status.value}")
    
    if final_task.status == TaskStatus.COMPLETED:
        print("[PASS] End-to-End Test Passed!")
        print("Result Summary:")
        print(final_task.result)
        
        # Print git diff
        os.system(f"cd {repo_path} && git diff")
    else:
        print("[FAIL] End-to-End Test Failed!")
        print("Error:")
        print(final_task.result)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_e2e())
