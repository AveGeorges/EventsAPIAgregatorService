import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def _optional_trace_context() -> dict[str, str]:
    """Добавляет trace_id/span_id, если позже подключён OpenTelemetry."""
    try:
        from opentelemetry import trace
    except ImportError:
        return {}

    span = trace.get_current_span()
    span_context = span.get_span_context()
    if not span_context.is_valid:
        return {}

    return {
        "trace_id": format(span_context.trace_id, "032x"),
        "span_id": format(span_context.span_id, "016x"),
    }


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.PROJECT_NAME,
        }

        request_id = request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id

        payload.update(_optional_trace_context())

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )


def _resolve_handlers() -> set[str]:
    return {part.strip().lower() for part in settings.LOG_HANDLERS.split(",") if part.strip()}


def _build_formatter() -> logging.Formatter:
    if settings.LOG_FORMAT.lower() == "json":
        return JsonFormatter()
    return TextFormatter()


def _build_handlers() -> list[logging.Handler]:
    handlers: list[logging.Handler] = []
    targets = _resolve_handlers()
    formatter = _build_formatter()

    if "stdout" in targets:
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(formatter)
        handlers.append(stdout_handler)

    if "file" in targets:
        log_path = Path(settings.LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.LOG_FILE_MAX_BYTES,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    if not handlers:
        fallback = logging.StreamHandler()
        fallback.setFormatter(formatter)
        handlers.append(fallback)

    return handlers


def _attach_handlers(logger: logging.Logger, handlers: list[logging.Handler]) -> None:
    logger.handlers.clear()
    for handler in handlers:
        logger.addHandler(handler)
    logger.propagate = False


def configure_logging() -> None:
    handlers = _build_handlers()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)

    for logger_name in ("uvicorn.access", "uvicorn.error"):
        _attach_handlers(logging.getLogger(logger_name), handlers)
