class ValidationError(Exception):
    """Domain-level validation error (mapped to HTTP 422 in the API)."""


class MissingRateError(ValidationError):
    pass


class InvalidAmountError(ValidationError):
    pass


class InvalidParticipantsError(ValidationError):
    pass


class InvalidWeightsError(ValidationError):
    pass
