from __future__ import annotations


class QualityGateError(Exception):
    """Base application error."""


class ConfigurationError(QualityGateError):
    """Raised when configuration is invalid."""


class SecurityVerificationError(QualityGateError):
    """Raised when update or source verification fails."""


class PolicyViolationError(QualityGateError):
    """Raised when a requested action violates policy."""
