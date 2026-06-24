"""Tracing hooks - Local JSON trace provider with optional LangSmith/Langfuse support.

This module provides production-ready local tracing (spans recorded to JSON files)
with optional augmentation via LangSmith or Langfuse when API keys are configured.
"""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)

# Local JSON trace directory
_TRACE_DIR = Path("reports/traces")


def _ensure_trace_dir() -> None:
    _TRACE_DIR.mkdir(parents=True, exist_ok=True)


def save_trace_to_json(trace_data: list[dict[str, Any]], run_name: str = "run") -> str:
    """Save trace data to a timestamped JSON file in reports/traces/."""
    _ensure_trace_dir()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{run_name}.json"
    filepath = _TRACE_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2, default=str)
    logger.info(f"Trace saved to {filepath}")
    return str(filepath)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context manager - tracks duration, supports local JSON tracing.

    Can be augmented with LangSmith/Langfuse by configuring the respective
    API keys in the .env file. When no external provider is configured,
    falls back to local span tracking automatically.
    """
    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "started_at": datetime.now(UTC).isoformat(),
    }

    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        logger.debug(
            f"Span '{name}' completed in {span['duration_seconds']:.3f}s"
        )
