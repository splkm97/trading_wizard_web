"""Custom exception classes for the application."""

from fastapi import HTTPException, status


class TradingWizardException(Exception):
    """Base exception for Trading Wizard."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


# Authentication Exceptions
class AuthenticationError(TradingWizardException):
    """Authentication failed."""

    pass


class InvalidKeyError(AuthenticationError):
    """Invalid PEM key format."""

    pass


class InvalidSignatureError(AuthenticationError):
    """Signature verification failed."""

    pass


class ChallengeExpiredError(AuthenticationError):
    """Challenge has expired."""

    pass


class UserNotFoundError(AuthenticationError):
    """User not found."""

    pass


# General Exceptions
class ValidationError(TradingWizardException):
    """Validation error."""

    pass


class NotFoundError(TradingWizardException):
    """Resource not found."""

    pass


# Trading Exceptions
class InsufficientBalanceError(TradingWizardException):
    """Insufficient cash balance for trade."""

    pass


class InsufficientQuantityError(TradingWizardException):
    """Insufficient stock quantity for sale."""

    pass


class InvalidStockCodeError(TradingWizardException):
    """Invalid stock code format or not found."""

    pass


class PositionNotFoundError(TradingWizardException):
    """Position not found for the stock."""

    pass


class TradeNotFoundError(TradingWizardException):
    """Trade record not found."""

    pass


# Portfolio Exceptions
class PortfolioNotFoundError(TradingWizardException):
    """Portfolio not found for user."""

    pass


# HTTP Exception helpers
def raise_unauthorized(detail: str = "Could not validate credentials"):
    """Raise 401 Unauthorized."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_not_found(detail: str = "Resource not found"):
    """Raise 404 Not Found."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_bad_request(detail: str = "Bad request"):
    """Raise 400 Bad Request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_conflict(detail: str = "Resource already exists"):
    """Raise 409 Conflict."""
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
