"""Standalone worker entrypoint: python -m app.workers.runner

Runs the generation and cleanup loops without the API, so the worker can live
in its own container (or on the GPU host) while the API runs elsewhere.
"""

import logging
import signal
import threading

from app.config import get_settings
from app.db import init_db
from app.workers.cleanup_worker import CleanupWorker
from app.workers.generation_worker import GenerationWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("worker")


def main() -> None:
    settings = get_settings()
    init_db()

    generation = GenerationWorker(settings)
    cleanup = CleanupWorker(settings)
    generation.start()
    cleanup.start()
    logger.info("Worker started with backend=%s", settings.generator_backend)

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    stop.wait()

    logger.info("Shutting down worker")
    generation.stop()
    cleanup.stop()
    generation.join(timeout=10)
    cleanup.join(timeout=5)


if __name__ == "__main__":
    main()
