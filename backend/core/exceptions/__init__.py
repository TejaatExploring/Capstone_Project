"""
Custom Exceptions Module
=========================

Defines domain-specific exceptions for the IEMS system.
"""


class IEMSException(Exception):
    """Base exception for all IEMS-related errors."""
    pass


class WeatherServiceError(IEMSException):
    """Raised when weather data retrieval fails."""
    pass


class PhysicsEngineError(IEMSException):
    """Raised when physics simulation encounters an error."""
    pass


class LoadGeneratorError(IEMSException):
    """Raised when load generation fails."""
    pass


class OptimizerError(IEMSException):
    """Raised when optimization fails."""
    pass


class ControllerError(IEMSException):
    """Raised when controller encounters an error."""
    pass


class ConfigurationError(IEMSException):
    """Raised when configuration is invalid."""
    pass


class ValidationError(IEMSException):
    """Raised when input validation fails."""
    pass


class ModelNotTrainedError(IEMSException):
    """Raised when attempting to use an untrained model."""
    pass
