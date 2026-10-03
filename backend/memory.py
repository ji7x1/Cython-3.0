"""ذاكرة المحادثات: لكل conversation_id نحتفظ باخر N رسائل بالذاكرة (RAM).

الذاكرة تنمسح اذا انطفى السيرفر. عدد المحادثات محدود (LRU) حتى ما تكبر الذاكرة بلا نهاية.
"""

import threading
from collections import OrderedDict, deque
from typing import Literal

Role = Literal["human", "ai"]


class ConversationStore:
    def __init__(self, max_messages: int, max_conversations: int):
        self.max_messages = max_messages
        self.max_conversations = max_conversations
        self._conversations: "OrderedDict[str, deque]" = OrderedDict()
        self._lock = threading.Lock()

    def history(self, conversation_id: str) -> list[tuple[Role, str]]:
        with self._lock:
            messages = self._conversations.get(conversation_id)
            if messages is None:
                return []
            self._conversations.move_to_end(conversation_id)
            return list(messages)

    def append_exchange(self, conversation_id: str, user_text: str, reply: str) -> None:
        with self._lock:
            messages = self._conversations.get(conversation_id)
            if messages is None:
                messages = deque(maxlen=self.max_messages)
                self._conversations[conversation_id] = messages
            self._conversations.move_to_end(conversation_id)
            messages.append(("human", user_text))
            messages.append(("ai", reply))
            while len(self._conversations) > self.max_conversations:
                self._conversations.popitem(last=False)

    def clear(self, conversation_id: str) -> bool:
        with self._lock:
            return self._conversations.pop(conversation_id, None) is not None

    def __len__(self) -> int:
        with self._lock:
            return len(self._conversations)
