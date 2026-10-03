"""اختبارات الـ backend. الموديل مزيّف (mock): ماكو network وماكو حاجة لـ GROQ_API_KEY."""

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend import config
from backend.llm import build_prompt, get_chain
from backend.main import create_app, get_reply_chain
from backend.memory import ConversationStore
from backend.persona import SYSTEM_PROMPT


class FakeChain:
    """يقلد chain.ainvoke ويسجل شنو وصله."""

    def __init__(self, replies=None, error=None):
        self.replies = list(replies or [])
        self.error = error
        self.calls = []

    async def ainvoke(self, inputs):
        self.calls.append(inputs)
        if self.error:
            raise self.error
        text = self.replies.pop(0) if self.replies else f"جواب على: {inputs['text']}"
        return AIMessage(text)


class UpstreamError(Exception):
    def __init__(self, status_code):
        super().__init__(f"upstream {status_code}")
        self.status_code = status_code


class FakeTimeout(Exception):
    pass


FakeTimeout.__name__ = "APITimeoutError"


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


def make_client(chain=None, max_messages=20, max_conversations=1000):
    settings = config.load_settings()
    store = ConversationStore(max_messages=max_messages, max_conversations=max_conversations)
    app = create_app(settings=settings, store=store)
    if chain is not None:
        app.dependency_overrides[get_reply_chain] = lambda: chain
    return TestClient(app), store


def test_health_without_key():
    client, _ = make_client()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "version": "3.0.0", "llm_configured": False}


def test_health_reports_configured_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    client, _ = make_client()
    assert client.get("/health").json()["llm_configured"] is True


def test_root_serves_frontend():
    client, _ = make_client()
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert 'dir="rtl"' in res.text
    assert client.get("/chat.html").status_code == 200
    assert client.get("/style.css").status_code == 200
    assert client.get("/script.js").status_code == 200


def test_chat_without_key_returns_503():
    client, _ = make_client()
    res = client.post("/chat", json={"message": "هلو"})
    assert res.status_code == 503
    assert res.json()["detail"]["code"] == "llm_not_configured"


def test_chat_returns_reply_and_new_conversation_id():
    chain = FakeChain(replies=["هلا بيك عيني"])
    client, _ = make_client(chain)
    res = client.post("/chat", json={"message": "  شلونك؟  "})
    assert res.status_code == 200
    body = res.json()
    assert body["reply"] == "هلا بيك عيني"
    assert len(body["conversation_id"]) == 32
    # الرسالة توصل للموديل بعد التنظيف وبدون تاريخ
    assert chain.calls == [{"text": "شلونك؟", "history": []}]


def test_chat_remembers_conversation():
    chain = FakeChain(replies=["اول جواب", "ثاني جواب"])
    client, _ = make_client(chain)
    cid = client.post("/chat", json={"message": "اسمي علي"}).json()["conversation_id"]
    res = client.post("/chat", json={"message": "شنو اسمي؟", "conversation_id": cid})
    assert res.status_code == 200
    assert res.json()["conversation_id"] == cid
    history = chain.calls[1]["history"]
    assert [type(m) for m in history] == [HumanMessage, AIMessage]
    assert [m.content for m in history] == ["اسمي علي", "اول جواب"]


def test_conversations_are_isolated():
    chain = FakeChain()
    client, _ = make_client(chain)
    client.post("/chat", json={"message": "سر", "conversation_id": "conversation-a"})
    client.post("/chat", json={"message": "هلو", "conversation_id": "conversation-b"})
    assert chain.calls[1]["history"] == []


def test_history_keeps_only_last_n_messages():
    chain = FakeChain()
    client, store = make_client(chain, max_messages=4)
    for i in range(5):
        client.post("/chat", json={"message": f"m{i}", "conversation_id": "conversation-1"})
    assert [m.content for m in chain.calls[-1]["history"]] == ["m2", "جواب على: m2", "m3", "جواب على: m3"]
    assert len(store.history("conversation-1")) == 4


def test_oldest_conversation_is_evicted():
    client, store = make_client(FakeChain(), max_conversations=2)
    for cid in ("conversation-1", "conversation-2", "conversation-3"):
        client.post("/chat", json={"message": "هلو", "conversation_id": cid})
    assert len(store) == 2
    assert store.history("conversation-1") == []


def test_clear_conversation():
    chain = FakeChain()
    client, store = make_client(chain)
    client.post("/chat", json={"message": "هلو", "conversation_id": "conversation-1"})
    assert client.delete("/chat/conversation-1").status_code == 204
    assert store.history("conversation-1") == []
    # idempotent
    assert client.delete("/chat/conversation-1").status_code == 204


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 4001},
        {"message": 5},
        {"message": "هلو", "conversation_id": "short"},
        {"message": "هلو", "conversation_id": "../../etc/passwd"},
    ],
)
def test_invalid_requests_return_422(payload):
    chain = FakeChain()
    client, _ = make_client(chain)
    assert client.post("/chat", json=payload).status_code == 422
    assert chain.calls == []


@pytest.mark.parametrize(
    "error, expected_status, expected_code",
    [
        (UpstreamError(429), 429, "llm_rate_limited"),
        (UpstreamError(401), 503, "llm_auth_failed"),
        (FakeTimeout("slow"), 504, "llm_timeout"),
        (RuntimeError("boom secret-detail"), 502, "llm_error"),
    ],
)
def test_upstream_errors_map_to_status_codes(error, expected_status, expected_code):
    client, store = make_client(FakeChain(error=error))
    res = client.post("/chat", json={"message": "هلو", "conversation_id": "conversation-1"})
    assert res.status_code == expected_status
    assert res.json()["detail"]["code"] == expected_code
    assert "secret-detail" not in res.text
    # الرسالة الفاشلة ما تنحفظ بالذاكرة
    assert store.history("conversation-1") == []


def test_empty_model_reply_is_502():
    client, _ = make_client(FakeChain(replies=["  "]))
    res = client.post("/chat", json={"message": "هلو"})
    assert res.status_code == 502
    assert res.json()["detail"]["code"] == "llm_empty_reply"


def test_cors_allows_configured_origin():
    client, _ = make_client(FakeChain())
    res = client.options(
        "/chat",
        headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": "POST"},
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:5500"
    res = client.options(
        "/chat",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in res.headers


def test_cors_origins_from_env(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://cython.example, https://other.example")
    assert config.load_settings().cors_origins == ("https://cython.example", "https://other.example")


def test_prompt_keeps_persona_and_places_history():
    messages = build_prompt().format_messages(
        text="سؤال جديد", history=[HumanMessage("قديم"), AIMessage("جواب قديم")]
    )
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == SYSTEM_PROMPT
    assert "Baghdadi Iraqi Dialect" in SYSTEM_PROMPT
    assert [m.content for m in messages[1:]] == ["قديم", "جواب قديم", "سؤال جديد"]


def test_get_chain_builds_offline_with_key():
    # بناء الـ chain ما يسوي اي اتصال بالشبكة
    chain = get_chain("test-key", config.load_settings())
    assert hasattr(chain, "ainvoke")
