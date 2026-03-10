"""Parse Unicode confusables data and build the confusable mapping file."""

import json
import string
from pathlib import Path
from unicodedata import normalize

from .config import CONFUSABLE_MAPPING_PATH, CONFUSABLES_PATH, CUSTOM_CONFUSABLE_PATH, MAX_SIMILARITY_DEPTH


def _asciify(char: str) -> str:
    """Convert a character to its ASCII equivalent via NFD normalization.

    Args:
        char: The character to convert.

    Returns:
        The ASCII equivalent of the character, or an empty string if no
        ASCII equivalent exists.
    """
    return normalize("NFD", char).encode("ascii", "ignore").decode("ascii")


def _get_accented_characters(char: str) -> list[str]:
    """Return all Unicode characters that normalize to the given ASCII character.

    Args:
        char: The ASCII character to find accented variants for.

    Returns:
        A list of Unicode characters that normalize to the given character.
    """
    return [u for u in (chr(i) for i in range(137928)) if u != char and _asciify(u) == char]


def _get_confusable_chars(character: str, unicode_confusable_map: dict[str, set[str]], depth: int) -> set[str]:
    """Recursively collect all characters confusable with the given character.

    Args:
        character: The character to find confusable variants for.
        unicode_confusable_map: A mapping of characters to their confusable sets.
        depth: The current recursion depth.

    Returns:
        A set of all characters confusable with the given character.
    """
    mapped_chars = unicode_confusable_map[character]

    group = {character}
    if depth <= MAX_SIMILARITY_DEPTH:
        for mapped_char in mapped_chars:
            group.update(_get_confusable_chars(mapped_char, unicode_confusable_map, depth + 1))
    return group


def parse_new_mapping_file() -> None:  # noqa: C901, PLR0912, PLR0915
    """Parse confusables files and generate the confusable mapping JSON.

    Reads the Unicode confusables file and custom confusables file, builds a
    bidirectional mapping of confusable characters, and writes the result to
    the confusable mapping JSON file.
    """
    unicode_confusable_map: dict[str, set[str]] = {}

    with (
        (Path(__file__).parent / CONFUSABLES_PATH).open() as unicode_mappings,
        (Path(__file__).parent / CUSTOM_CONFUSABLE_PATH).open() as custom_mappings,
    ):
        mappings = unicode_mappings.readlines()
        mappings.extend(custom_mappings)

        for mapping_line in mappings:
            if not mapping_line.strip() or mapping_line[0] == "#" or mapping_line[1] == "#":
                continue

            mapping = mapping_line.split(";")[:2]
            str1 = chr(int(mapping[0].strip(), 16))

            raw_codepoints = mapping[1].strip().split(" ")
            str2 = "".join(chr(int(x, 16)) for x in raw_codepoints)

            if unicode_confusable_map.get(str1):
                unicode_confusable_map[str1].add(str2)
            else:
                unicode_confusable_map[str1] = {str2}

            if unicode_confusable_map.get(str2):
                unicode_confusable_map[str2].add(str1)
            else:
                unicode_confusable_map[str2] = {str1}

            if len(str1) == 1:
                case_change = str1.lower() if str1.isupper() else str1.upper()
                if case_change != str1:
                    unicode_confusable_map[str1].add(case_change)
                    if unicode_confusable_map.get(case_change) is not None:
                        unicode_confusable_map[case_change].add(str1)
                    else:
                        unicode_confusable_map[case_change] = {str1}

            if len(str2) == 1:
                case_change = str2.lower() if str2.isupper() else str2.upper()
                if case_change != str2:
                    unicode_confusable_map[str2].add(case_change)
                    if unicode_confusable_map.get(case_change) is not None:
                        unicode_confusable_map[case_change].add(str2)
                    else:
                        unicode_confusable_map[case_change] = {str2}

    for char in string.ascii_lowercase:
        accented = _get_accented_characters(char)
        unicode_confusable_map[char].update(accented)
        for accent in accented:
            if unicode_confusable_map.get(accent):
                unicode_confusable_map[accent].add(char)
            else:
                unicode_confusable_map[accent] = {char}

    for char in string.ascii_uppercase:
        accented = _get_accented_characters(char)
        unicode_confusable_map[char].update(accented)
        for accent in accented:
            if unicode_confusable_map.get(accent):
                unicode_confusable_map[accent].add(char)
            else:
                unicode_confusable_map[accent] = {char}

    confusable_map = {}
    for character in list(unicode_confusable_map.keys()):
        char_group = _get_confusable_chars(character, unicode_confusable_map, 0)

        confusable_map[character] = list(char_group)

    with (Path(__file__).parent / CONFUSABLE_MAPPING_PATH).open("w") as mapping_file:
        mapping_file.write(json.dumps(confusable_map))


parse_new_mapping_file()
