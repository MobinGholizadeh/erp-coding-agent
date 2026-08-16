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

    def append_message(self, role: Role, content: str = None, **kwargs):
        self._history.append(Message(role=role, content=content, **kwargs))

    def append_tool_result(self, tool_name: str, content: str, tool_call_id: str = None):
        if tool_call_id:
            self.append_message(
                Role.TOOL,
                content=content,
                name=tool_name,
                tool_call_id=tool_call_id
            )
        else:
            self.append_message(
                Role.USER, 
                content=f"[Tool Result: {tool_name}]\n{content}"
            )

    def get_messages(self) -> List[Message]:
        return list(self._history)
