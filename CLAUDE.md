# CLAUDE.md

Cython 3.0 (سايثون): Iraqi-dialect AI assistant. FastAPI backend + static Arabic RTL frontend.

## Layout
- `backend/` — FastAPI app (`main.py`), persona prompt (`persona.py`, keep verbatim), Groq/LangChain chain (`llm.py`), per-conversation memory (`memory.py`), env config (`config.py`)
- `backend/tests/` — pytest suite; the LLM is always mocked via `app.dependency_overrides[get_reply_chain]`
- `frontend/` — static pages served by FastAPI at `/`; shared `style.css` (color palettes) and `script.js` (`CythonTheme.apply`)

## Commands
- Install: `pip install -r requirements-dev.txt`
- Run everything: `python -m backend` → http://127.0.0.1:8000
- Test: `python -m pytest`

## Notes
- `GROQ_API_KEY` is read per request; never require it at import time. Never commit `.env`.
- Frontend HTML files use CRLF line endings; preserve them when editing.
- Keep the visual design unchanged. Pages differ subtly in theme defaults and palettes; check before sharing more code.
- Render user/model text with `textContent`/text nodes, never `innerHTML`.
- Tests must not touch the network.
