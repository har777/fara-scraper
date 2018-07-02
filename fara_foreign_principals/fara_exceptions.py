class FaraError(Exception):
    """
    Base class for exceptions in this module.
    """
    pass

class ApexFieldMissingError(FaraError):
    """
    Exception raised for errors in parsing apex metadata.
    No value present for an Apex metadata field.
    """
    pass

class ApexFieldMultipleValuesError(FaraError):
    """
    Exception raised for errors in parsing apex metadata.
    Multiple values for an Apex metadata field.
    """
    pass

class SelectorEmptyError(FaraError):
    """
    Exception raised when selector returns no value.
    """
    pass

class UnexpectedValueError(FaraError):
    """
    Exception raised when unexpected value received.
    """
    pass
