"""
Logger Compatibility Shim - Alpha v1.0.0.0

Provides convenience functions for code that used unified_logger convenience methods.
All calls route to logging_manager.py (canonical logger).

Use this only for backward compatibility. New code should use logging_manager directly.

Migration path:
    OLD: from dev.goblin.core.services.unified_logger import log_performance
    NEW: from dev.goblin.core.services.logger_compat import log_performance

Future (direct usage):
    from dev.goblin.core.services.logging_manager import get_logger
    logger = get_logger('performance')
    logger.info(f"Query: {duration}s")
"""

from dev.goblin.core.services.logging_manager import get_logger


def log_system(message: str, level: str = "info", **context):
    """Log system message.

    Args:
        message: Log message
        level: Log level (debug, info, warning, error, critical)
        **context: Additional context fields
    """
    logger = get_logger("system")
    getattr(logger, level)(message, extra={"context": context})


def log_api(
    service: str, duration: float, cost: float, success: bool = True, **context
):
    """Log API call.

    Args:
        service: API service name (gemini, banana, etc.)
        duration: Call duration in seconds
        cost: Call cost in USD
        success: Whether call succeeded
        **context: Additional context
    """
    logger = get_logger("api")
    status = "OK" if success else "FAIL"
    logger.info(
        f"{service}: {duration:.3f}s, ${cost:.4f}, {status}", extra={"context": context}
    )


def log_performance(query_type: str, duration: float, offline: bool, **context):
    """Log performance metrics.

    Args:
        query_type: Type of query (generate, guide, svg, etc.)
        duration: Query duration in seconds
        offline: Whether query was handled offline
        **context: Additional context
    """
    logger = get_logger("performance")
    mode = "offline" if offline else "online"
    logger.info(f"{query_type}: {mode}, {duration:.3f}s", extra={"context": context})


def log_debug(message: str, script: str = None, line: int = None, **context):
    """Log debug message.

    Args:
        message: Debug message
        script: Script name (optional)
        line: Line number (optional)
        **context: Additional context
    """
    logger = get_logger("debug")
    location = f"{script}:{line}" if script and line else (script or "")
    if location:
        message = f"[{location}] {message}"
    logger.debug(message, extra={"context": context})


def log_error(message: str, exception: Exception = None, **context):
    """Log error message.

    Args:
        message: Error message
        exception: Exception object (optional)
        **context: Additional context
    """
    logger = get_logger("error")
    if exception:
        logger.error(
            f"{message}: {type(exception).__name__}: {str(exception)}",
            extra={"context": context},
            exc_info=True,
        )
    else:
        logger.error(message, extra={"context": context})


def log_command(command: str, params: list, result: str, duration: float, **context):
    """Log command execution.

    Args:
        command: Command name
        params: Command parameters
        result: Command result/output (truncated)
        duration: Execution duration
        **context: Additional context
    """
    logger = get_logger("command")
    result_preview = result[:100] + "..." if len(result) > 100 else result
    logger.info(
        f"{command} {' '.join(params)}: {duration:.3f}s -> {result_preview}",
        extra={"context": context},
    )


def get_unified_logger():
    """Compatibility function - returns logging manager.

    Returns a simple wrapper that provides the old API.
    """

    class UnifiedLoggerCompat:
        """Compatibility wrapper for UnifiedLogger API."""

        def log_system(self, message: str, level: str = "info", **context):
            log_system(message, level, **context)

        def log_api(
            self,
            service: str,
            duration: float,
            cost: float,
            success: bool = True,
            **context,
        ):
            log_api(service, duration, cost, success, **context)

        def log_performance(
            self, query_type: str, duration: float, offline: bool, **context
        ):
            log_performance(query_type, duration, offline, **context)

        def log_debug(
            self, message: str, script: str = None, line: int = None, **context
        ):
            log_debug(message, script, line, **context)

        def log_error(self, message: str, exception: Exception = None, **context):
            log_error(message, exception, **context)

        def log_command(
            self, command: str, params: list, result: str, duration: float, **context
        ):
            log_command(command, params, result, duration, **context)

    return UnifiedLoggerCompat()
