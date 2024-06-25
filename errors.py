class UserNotFoundError(Exception):
    """Raised when a user is not found."""
    pass

class GroupNotFoundError(Exception):
    """Raised when a group is not found."""
    pass

class UsernameNotOccupied(Exception):
    """Raised when an invalid username is provided."""
    pass