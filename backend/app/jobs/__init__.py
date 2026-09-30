"""Standalone background jobs, run as their own processes (systemd), never
from inside the FastAPI app. See deploy/systemd/ for how each is started."""

import logging


def configure_logging() -> None:
    """Log to stderr (captured by the systemd journal): INFO for this
    app's own loggers, WARNING for libraries -- the PDF renderer's INFO
    output would otherwise flood the journal on every report."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("app").setLevel(logging.INFO)
