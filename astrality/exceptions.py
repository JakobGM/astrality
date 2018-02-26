class AstralityConfigurationError(BaseException):
    pass

class NonExistentEnabledModule(AstralityConfigurationError):
    pass

class MisconfiguredConfigurationFile(AstralityConfigurationError):
    pass
