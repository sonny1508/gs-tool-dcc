class ObjectDoesntExistError(Exception):
    """Raised anytime the current object is operated on and it doesn't exist.
    """
    pass


class InvalidPlugPathError(Exception):
    """Raised when Provided path doesn't contain '.'
    """
    pass


class ReferenceObjectError(Exception):
    """Raised when an object is a reference and the requested operation is
    not allowed on a reference
    """
    pass


class InvalidTypeForPlugError(Exception):
    """Raised anytime an operation happens on a plug which isn't
    compatible with the datatype, ie. setting fields on non Enum type.
    """
    pass


class ExistingNodeAttributeError(Exception):
    """Raised when attempting to create an attribute that already exists
    """
    pass
