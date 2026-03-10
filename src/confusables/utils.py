"""Utility functions for confusables."""

_MAX_ASCII_CODE = 127


def is_ascii(string: str) -> bool:
    """Check if all characters in the string are ASCII.

    Args:
        string: The string to check.

    Returns:
        True if all characters have code points <= 127, False otherwise.
    """
    return all(ord(char) <= _MAX_ASCII_CODE for char in string)
