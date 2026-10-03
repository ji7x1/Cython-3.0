"""سيرفر Cython 3.0 (FastAPI): الـ API للدردشة + يقدم صفحات الواجهة من frontend/."""

import logging
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints

from .config import FRONTEND_DIR, Settings, get_api_key, load_settings
from .llm import LLMNotConfigured, ReplyChain, get_chain, to_messages
from .memory import ConversationStore

logger = logging.getLogger("cython")

MAX_MESSAGE_CHARS = 4000
CONVERSATION_ID_PATTERN = r"^[A-Za-z0-9_-]{8,64}$"

ConversationId = Annotated[str, Field(pattern=CONVERSATION_ID_PATTERN)]


# شكل البيانات اللي راح توصلنا من التطبيق او الموقع
class ChatRequest(BaseModel):
    message: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_CHARS)
    ]
    conversation_id: ConversationId | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def get_reply_chain(request: Request) -> ReplyChain | None:
    # يرجع None بدل ما يرمي خطأ، حتى اخطاء الادخال (422) تنفحص قبل خطأ المفتاح (503)
    try:
        return get_chain(get_api_key(), request.app.state.settings)
    except LLMNotConfigured:
        return None


def upstream_error(exc: Exception) -> HTTPException:
    """يحول اخطاء مزود الموديل الى status code مفهوم، بدون ما يسرب تفاصيل داخلية."""
    upstream_status = getattr(exc, "status_code", None)
    if upstream_status == 429:
        return api_error(429, "llm_rate_limited", "The AI provider is rate limiting requests. Try again shortly.")
    if upstream_status in (401, 403):
        return api_error(503, "llm_auth_failed", "The AI provider rejected the server's API key.")
    if isinstance(exc, TimeoutError) or "Timeout" in type(exc).__name__:
        return api_error(504, "llm_timeout", "The AI provider took too long to answer.")
    return api_error(502, "llm_error", "The AI provider returned an error.")


def create_app(settings: Settings | None = None, store: ConversationStore | None = None) -> FastAPI:
    if settings is None:
        settings = load_settings()
    app = FastAPI(title="Cython 3.0 Server", version="3.0.0")
    app.state.settings = settings
    if store is None:
        store = ConversationStore(
            max_messages=settings.max_history_messages,
            max_conversations=settings.max_conversations,
        )
    app.state.store = store

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": app.version,
            "llm_configured": get_api_key() is not None,
        }

    # نقطة الاتصال (Endpoint)
    @app.post("/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest, chain: ReplyChain | None = Depends(get_reply_chain)):
        if chain is None:
            raise api_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "llm_not_configured",
                "GROQ_API_KEY is not set on the server. Add it to .env and restart.",
            )
        store: ConversationStore = app.state.store
        conversation_id = body.conversation_id or uuid.uuid4().hex
        history = store.history(conversation_id)
        try:
            # ارسال الرسالة للموديل ويه اخر رسائل المحادثة وانتظار الجواب
            response = await chain.ainvoke({"text": body.message, "history": to_messages(history)})
        except Exception as exc:
            logger.exception("LLM call failed for conversation %s", conversation_id)
            raise upstream_error(exc) from None

        reply = getattr(response, "content", None)
        if not isinstance(reply, str) or not reply.strip():
            raise api_error(502, "llm_empty_reply", "The AI provider returned an empty reply.")

        store.append_exchange(conversation_id, body.message, reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id)

    @app.delete("/chat/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
    def clear_conversation(conversation_id: Annotated[str, Path(pattern=CONVERSATION_ID_PATTERN)]):
        app.state.store.clear(conversation_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # الواجهة: لازم تنضاف بعد الـ API routes حتى ما تغطي عليها
    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()
