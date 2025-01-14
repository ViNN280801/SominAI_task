from modules.logger import Logger


class ExceptionHandler:
    """
    A centralized handler for exceptions in a SaaS environment.

    This class handles exceptions, logs them using the Logger, and formats a unified
    response structure for error handling. In an HTTP context, 'path' and 'method' can
    be provided; otherwise, default values are used.
    """

    @staticmethod
    def handle_exception(exc: Exception, context: dict) -> dict:
        """
        Handles an exception and formats a unified response.

        :param exc: Exception to handle.
        :param context: Additional context, e.g., request details.
        :return: Unified error response.
        :raises TypeError: If `exc` is not an instance of Exception or `context` is not a dictionary.
        """
        # Make sure 'exc' is truly an Exception
        if not isinstance(exc, Exception):
            raise TypeError(
                f"`exc` must be an instance of Exception, got {type(exc).__name__}"
            )

        # Make sure 'context' is a dict
        if not isinstance(context, dict):
            raise TypeError(
                f"`context` must be a dictionary, got {type(context).__name__}"
            )

        # Provide default values if 'path' and 'method' are missing
        path = context.get("path", "N/A")
        method = context.get("method", "INTERNAL")

        # Log the exception with contextual info
        Logger.log_error(
            f"Exception: {type(exc).__name__}. Message: {str(exc)}. "
            f"Context: path={path}, method={method}, extras={context}"
        )

        # Return a standardized error dictionary
        return {
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "context": {
                    "path": path,
                    "method": method,
                    **{k: v for k, v in context.items() if k not in {"path", "method"}},
                },
            }
        }
