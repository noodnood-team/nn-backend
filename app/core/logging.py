import logging


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"  # type: ignore[attr-defined]
        return True


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
        )
    )
    handler.addFilter(RequestIdFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, extra={"request_id": "-"})
