"""Start the Recipe_IT application with a production WSGI server."""

import os
import sys
from pathlib import Path

from waitress import serve

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app


def _port() -> int:
    value = os.getenv("PORT", "5000")
    try:
        port = int(value)
    except ValueError as exc:
        raise SystemExit(f"PORT must be an integer, got {value!r}.") from exc
    if not 1 <= port <= 65535:
        raise SystemExit(f"PORT must be between 1 and 65535, got {port}.")
    return port


def _threads() -> int:
    value = os.getenv("WAITRESS_THREADS", "4")
    try:
        threads = int(value)
    except ValueError as exc:
        raise SystemExit(
            f"WAITRESS_THREADS must be an integer, got {value!r}."
        ) from exc
    if threads < 1:
        raise SystemExit("WAITRESS_THREADS must be at least 1.")
    return threads


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = _port()
    threads = _threads()

    print(f"Serving Recipe_IT on http://{host}:{port}")
    serve(create_app(), host=host, port=port, threads=threads)
