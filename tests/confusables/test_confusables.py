import re
import unittest
from typing import cast

from confusables import confusable_characters, confusable_regex, is_confusable, normalize


class TestConfusables(unittest.TestCase):
    def test_is_confusable__unicode_mapping_only(self) -> None:
        assert is_confusable("rover", "Ʀỏ𝕍3ℛ")

    def test_is_confusable__multi_character_mapping(self) -> None:
        assert is_confusable("Ʀỏ𝕍3ℛ", "ro'ver")
        assert is_confusable("ro'ver", "Ʀỏ𝕍3ℛ")

    def test_is_confusable__not_remotely_similar_words(self) -> None:
        assert not is_confusable("Ʀỏ𝕍3ℛ", "salmon")
        assert not is_confusable("salmon", "Ʀỏ𝕍3ℛ")

    def test_is_confusable__prefix_does_not_give_false_positive(self) -> None:
        assert not is_confusable("Ʀỏ𝕍3ℛ", "rover is my favourite dog")
        assert not is_confusable("rover is my favourite dog", "Ʀỏ𝕍3ℛ")

    def test_is_confusable__none_input(self) -> None:
        assert is_confusable(None, None)
        assert not is_confusable("rover is my favourite dog", None)
        assert not is_confusable(None, "rover is my favourite dog")

    def test_is_confusable__empty_input(self) -> None:
        assert is_confusable("", "")
        assert not is_confusable("rover is my favourite dog", "")
        assert not is_confusable("", "rover is my favourite dog")

    def test_confusable_characters__is_two_way(self) -> None:
        for u in [chr(i) for i in range(137928)]:
            mapped_chars = confusable_characters(u)
            if mapped_chars:
                for mapped_char in mapped_chars:
                    assert u in cast("list[str]", confusable_characters(mapped_char))

    def test_confusable_characters__no_confusables_returns_input_character_if_length_is_zero(self) -> None:
        assert confusable_characters("") == [""]

    def test_confusable_characters__no_confusables_returns_input_character_if_length_is_one(self) -> None:
        assert confusable_characters("#") == ["#"]

    def test_confusable_characters__no_confusables_returns_none_if_length_is_not_one(self) -> None:
        assert (
            confusable_characters("This is a long string that has no chance being confusable with a single character")
            is None
        )

    def test_confusable_regex__basic_ascii_regex_with_padding(self) -> None:
        regex = confusable_regex("bore", include_character_padding=True)
        reg = re.compile(regex)
        assert reg.search("Sometimes people say that life can be a ь.𝞂.ř.ɜ, but I don't agree")

    def test_confusable_regex__basic_ascii_regex_without_padding(self) -> None:
        regex = confusable_regex("bore")
        reg = re.compile(regex)
        assert not reg.search("Sometimes people say that life can be a ь.𝞂.ř.ɜ, but I don't agree")
        assert reg.search("Sometimes people say that life can be a ь𝞂řɜ, but I don't agree")

    def test_confusable_regex__match_subwords(self) -> None:
        regex = confusable_regex("bore")
        reg = re.compile(regex)
        assert reg.search("Sometimes people say that life can be a ь𝞂řɜd, but I don't agree")
        assert reg.search("Sometimes people say that life can be a ь𝞂řɜ, but I don't agree")

    def test_confusable_regex__match_multi_character_confusion(self) -> None:
        regex = confusable_regex("‷")
        reg = re.compile(regex)
        assert not reg.search("Sometimes people say that life can be ' , but I don't agree")
        assert reg.search("Sometimes people say that life can be ''' , but I don't agree")

    def test_confusable_regex__dont_treat_pipe_as_wildcard(self) -> None:
        regex = confusable_regex("bore")
        reg = re.compile(regex)
        assert not reg.search("Sometimes people say that life can be a ||||, but I don't agree")

    def test_confusable_regex__regex_special_characters_are_escaped(self) -> None:
        regex = confusable_regex("e|mo")
        reg = re.compile(regex)
        assert reg.search("elmo")
        assert not reg.search("emo")

    def test_normalize__prioritize_alpha_true_and_false(self) -> None:
        assert normalize("Ʀỏ𝕍3ℛ", prioritize_alpha=True) == ["rov3r", "rover"]
        assert (
            normalize("Ʀỏ𝕍3ℛ")
            == normalize("Ʀỏ𝕍3ℛ", prioritize_alpha=False)
            == ["r0v3r", "r0ver", "ro'v3r", "ro'ver", "rov3r", "rover"]
        )

    def test_normalize__at_character_gets_normalized(self) -> None:
        assert normalize("te@time") == ["teatime"]
