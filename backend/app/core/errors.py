from fastapi import HTTPException, status


class VeridionAPIException(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details or {}
            }
        )


class InvalidScopeException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("INVALID_SCOPE", message, status.HTTP_422_UNPROCESSABLE_CONTENT, details)


class SourceUnavailableException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("SOURCE_UNAVAILABLE", message, status.HTTP_404_NOT_FOUND, details)


class AgentTimeoutException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("AGENT_TIMEOUT", message, status.HTTP_504_GATEWAY_TIMEOUT, details)


class InvalidForecastException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("INVALID_FORECAST", message, status.HTTP_400_BAD_REQUEST, details)


class CommitmentMismatchException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("COMMITMENT_MISMATCH", message, status.HTTP_400_BAD_REQUEST, details)


class MarketClosedException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("MARKET_CLOSED", message, status.HTTP_400_BAD_REQUEST, details)


class UnauthorizedResolutionException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("UNAUTHORIZED_RESOLUTION", message, status.HTTP_403_FORBIDDEN, details)


class SettlementAlreadyDoneException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("SETTLEMENT_ALREADY_DONE", message, status.HTTP_409_CONFLICT, details)


class ChainRPCException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("CHAIN_RPC_ERROR", message, status.HTTP_502_BAD_GATEWAY, details)


class InvalidStateTransitionException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("INVALID_STATE_TRANSITION", message, status.HTTP_409_CONFLICT, details)


class InsufficientEvidenceException(VeridionAPIException):
    def __init__(self, message: str, details: dict = None):
        super().__init__("INSUFFICIENT_EVIDENCE", message, status.HTTP_422_UNPROCESSABLE_CONTENT, details)

