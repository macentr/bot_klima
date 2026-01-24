"""Utility functions for invite codes."""

import secrets
import string


def generate_invite_code(length: int = 8) -> str:
    """Generate a short, random invite code.
    
    Args:
        length: Length of the code (default 8)
        
    Returns:
        Random alphanumeric code in uppercase
    """
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))
