"""Confusables detection and normalization library."""

import json
import re
from itertools import product
from pathlib import Path
from typing import cast

from .config import CONFUSABLE_MAPPING_PATH, NON_NORMAL_ASCII_CHARS
from .utils import is_ascii

# read confusable mappings from file, build 2-way map of the pairs
with (Path(__file__).parent / CONFUSABLE_MAPPING_PATH).open() as mappings:
    CONFUSABLE_MAP = json.loads(mappings.readline())


def is_confusable(str1: str | None, str2: str | None) -> bool:
    """Check if two strings are visually confusable with each other.

    Args:
        str1: The first string to compare.
        str2: The second string to compare.

    Returns:
        True if the strings are visually confusable, False otherwise.
    """
    while str1 and str2:
        length1, length2 = 0, 0
        for index in range(len(str1), 0, -1):
            if str1[:index] in cast("list[str]", confusable_characters(str2[0])):
                length1 = index
                break
        for index in range(len(str2), 0, -1):
            if str2[:index] in cast("list[str]", confusable_characters(str1[0])):
                length2 = index
                break

        if not length1 and not length2:
            return False
        if not length2 or length1 >= length2:
            str1 = str1[length1:]
            str2 = str2[1:]
        else:
            str1 = str1[1:]
            str2 = str2[length2:]
    return str1 == str2


def confusable_characters(char: str) -> list[str] | None:
    """Return characters that are visually confusable with the given character.

    Args:
        char: The character to find confusable variants for.

    Returns:
        A list of confusable characters, or None if the input is a multi-character
        string with no confusable mapping.
    """
    mapped_chars = CONFUSABLE_MAP.get(char)
    if mapped_chars:
        return mapped_chars
    if len(char) <= 1:
        return [char]
    return None


def confusable_regex(string: str, *, include_character_padding: bool = False) -> str:
    """Build a regex pattern that matches confusable variants of the given string.

    Args:
        string: The string to build a confusable regex for.
        include_character_padding: If True, allow special characters between
            confusable characters in the match.

    Returns:
        A regex pattern string matching confusable variants.
    """
    space_regex = r"[\*_~|`\-\.]*" if include_character_padding else ""
    regex = space_regex
    for char in string:
        escaped_chars = [re.escape(c) for c in cast("list[str]", confusable_characters(char))]
        regex += "(?:" + "|".join(escaped_chars) + ")" + space_regex

    return regex


def normalize(string: str, *, prioritize_alpha: bool = False) -> list[str]:
    """Normalize a string by replacing confusable characters with ASCII equivalents.

    Args:
        string: The string to normalize.
        prioritize_alpha: If True, prefer alphabetic ASCII replacements over
            non-alphabetic ones.

    Returns:
        A sorted list of all possible normalized forms of the string.
    """
    normal_forms = {""}
    for char in string:
        normalized_chars: list[str] = []
        confusable_chars = confusable_characters(char)
        if (not is_ascii(char) or not char.isalpha()) and confusable_chars is not None:
            for confusable in confusable_chars:
                if prioritize_alpha:
                    if (
                        (char.isalpha() and confusable.isalpha() and is_ascii(confusable))
                        or (not char.isalpha() and is_ascii(confusable))
                    ) and confusable not in NON_NORMAL_ASCII_CHARS:
                        normal = confusable
                        if len(confusable) > 1:
                            normal = normalize(confusable)[0]
                        normalized_chars.append(normal)
                elif is_ascii(confusable) and confusable not in NON_NORMAL_ASCII_CHARS:
                    normal = confusable
                    if len(confusable) > 1:
                        normal = normalize(confusable)[0]
                    normalized_chars.append(normal)
        else:
            normalized_chars = [char]

        if len(normalized_chars) == 0:
            normalized_chars = [char]
        normal_forms = {x[0] + x[1].lower() for x in product(normal_forms, normalized_chars)}
    return sorted(normal_forms)
