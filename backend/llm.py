"""ربط الموديل (Groq llama-3.3-70b عن طريق LangChain) مع شخصية سايثون."""

from functools import lru_cache
from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .config import Settings
from .memory import Role
from .persona import SYSTEM_PROMPT


class LLMNotConfigured(RuntimeError):
    """GROQ_API_KEY مو موجود."""


class ReplyChain(Protocol):
    async def ainvoke(self, inputs: dict): ...


def build_prompt() -> ChatPromptTemplate:
    # ربط التعليمات بالموديل، ويه تاريخ المحادثة قبل رسالة المستخدم
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{text}"),
    ])


@lru_cache(maxsize=4)
def _build_chain(api_key: str, settings: Settings) -> ReplyChain:
    # import هنا حتى تحميل السيرفر والاختبارات ما يعتمد على مكتبة Groq
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        api_key=api_key,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=settings.request_timeout,
        max_retries=2,
    )
    return build_prompt() | llm


def get_chain(api_key: str | None, settings: Settings) -> ReplyChain:
    if not api_key:
        raise LLMNotConfigured("GROQ_API_KEY is not set")
    return _build_chain(api_key, settings)


def to_messages(history: list[tuple[Role, str]]) -> list[BaseMessage]:
    return [HumanMessage(text) if role == "human" else AIMessage(text) for role, text in history]
