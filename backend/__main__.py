"""تشغيل كل شي بأمر واحد: python -m backend"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "").lower() in ("1", "true", "yes"),
    )


if __name__ == "__main__":
    main()
