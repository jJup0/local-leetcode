import difflib

import pytest

from local_leetcode.fetch_from_leetcode import clean_code
from local_leetcode.html_parser import parse_description_html
from tests import load_test_data


def test_indent_bullet_point() -> None:
    html_in = load_test_data("1657_description_indent_bullet.html")
    parsed = parse_description_html(html_in)
    expected_parse = load_test_data("1657_description_indent_bullet_expected_parse.txt")

    assert (
        "  - For example, abcde -> aecdb" in parsed
    ), f"Parsed description does not seem to have bullet point indented:\n{parsed}"

    full_diff = "\n".join(
        difflib.context_diff(parsed.splitlines(), expected_parse.splitlines())
    )
    assert full_diff == "", full_diff


def test_clean_code() -> None:
    str_in = "class Solution:\n    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:"
    expected_out = "class Solution:\n    def insert(self, intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:"
    assert clean_code(str_in) == expected_out


@pytest.mark.skip(reason="Replacing ListNode not implemented yet")
def test_optional_replace() -> None:
    unclean_code = load_test_data("21_code_stub_optional_listnode.txt")
    actual_cleaned = clean_code(unclean_code)
    expected_cleaned = load_test_data("21_code_stub_optional_listnode_cleaned.txt")

    full_diff = "\n".join(
        difflib.context_diff(actual_cleaned.splitlines(), expected_cleaned.splitlines())
    )
    assert full_diff == "", full_diff


def test_bold__sup_in_code() -> None:
    html_in = load_test_data("629_description_bold__sup_in_code.html")
    parsed = parse_description_html(html_in)
    expected_parse = load_test_data(
        "629_description_bold__sup_in_code_expected_parse.txt"
    )

    full_diff = "\n".join(
        difflib.context_diff(parsed.splitlines(), expected_parse.splitlines())
    )
    assert full_diff == "", full_diff


if __name__ == "__main__":
    test_indent_bullet_point()
    test_clean_code()
    test_optional_replace()
    test_bold__sup_in_code()
    print("Ran tests")
