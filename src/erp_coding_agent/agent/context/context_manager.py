from typing import List
from ...llm.models import Message, Role

class ContextManager:
    def __init__(self, system_prompt: str):
        self._history: List[Message] = []
        if system_prompt:
            self.append_message(Role.SYSTEM, system_prompt)

    @property
    def history(self) -> List[Message]:
        return self._history

    def append_message(self, role: Role, content: str):
        self._history.append(Message(role=role, content=content))

    def append_tool_result(self, tool_name: str, content: str):
        # We model tool results as user messages describing the result,
        # or as specific tool result roles if supported. 
        # For Qwen via OpenAI API, they might be function/tool roles, 
        # but to keep it provider-agnostic and simple, we'll prefix as USER.
        self.append_message(
            Role.USER, 
            f"[Tool Result: {tool_name}]\n{content}"
        )

    def get_messages(self) -> List[Message]:
        return list(self._history)
