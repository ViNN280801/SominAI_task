from Utils.Logger import Logger


class ExceptionHandler:
    """
    A centralized handler for exceptions in a SaaS environment.

    This class handles exceptions, logs them using the Logger, and formats a unified
    response structure for error handling. Ensures that input parameters are validated
    to avoid unexpected runtime errors.

    Methods:
        - handle_exception: Handles and formats an exception into a unified response.
    """

    @staticmethod
    def handle_exception(exc: Exception, context: dict) -> dict:
        """
        Handles an exception and formats a unified response.

        :param exc: Exception to handle.
        :param context: Additional context, e.g., request details.
        :return: Unified error response.
        :raises TypeError: If `exc` is not an instance of Exception or `context` is not a dictionary.
        :raises ValueError: If `context` does not contain required keys or has invalid values.
        """
        if not isinstance(exc, Exception):
            raise TypeError(
                f"`exc` must be an instance of Exception, got {
                    type(exc).__name__}"
            )

        if not isinstance(context, dict):
            raise TypeError(
                f"`context` must be a dictionary, got {type(context).__name__}"
            )

        required_keys = {"path", "method"}
        missing_keys = required_keys - context.keys()
        if missing_keys:
            raise ValueError(f"`context` is missing required keys: {missing_keys}")

        if not isinstance(context.get("path"), str) or not context["path"]:
            raise ValueError(f"{context['path']} must be a non-empty string.")
        if not isinstance(context.get("method"), str) or not context["method"]:
            raise ValueError(f"{context['method']} must be a non-empty string.")

        Logger.log_error(
            f"Exception: {type(exc).__name__}. Message: {
                str(exc)}. Context: {context}"
        )

        return {
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "context": context,
            }
        }
