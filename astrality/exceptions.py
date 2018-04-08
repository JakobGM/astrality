"""Custom exception definitions."""


class AstralityConfigurationError(BaseException):
    """Exception for when astrality configuration is invalid."""


class NonExistentEnabledModule(AstralityConfigurationError):
    """Exception for when an enabled module is not found."""


class MisconfiguredConfigurationFile(AstralityConfigurationError):
    """Exception for when astrality configuration has semantic errors."""


class GithubModuleError(AstralityConfigurationError):
    """Exception for when GitHub module could not be sourced."""
