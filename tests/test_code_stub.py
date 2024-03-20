import difflib

import pytest

from local_leetcode.fetch_from_leetcode import clean_code
from local_leetcode.html_parser import parse_description_html
from tests import load_test_data, write_temp_to_test_data


def _test_html_parse(base_filename: str) -> None:
    html_in = load_test_data(f"{base_filename}.html")
    parsed = parse_description_html(html_in)
    expected_parse = load_test_data(f"{base_filename}_expected_parse.txt")

    full_diff = "\n".join(
        difflib.context_diff(parsed.splitlines(), expected_parse.splitlines())
    )
    if full_diff != "":
        write_temp_to_test_data(parsed)
    assert full_diff == "", full_diff


def test_indent_bullet_point() -> None:
    _test_html_parse("1657_description_indent_bullet")


def test_clean_code() -> None:
    str_in = "class Solution:\n    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:"
    expected_out = "class Solution:\n    def insert(self, intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:"
    assert clean_code(str_in) == expected_out


@pytest.mark.skip(reason="Replacing ListNode not implemented yet")
def test_optional_replace() -> None:
    _test_html_parse("21_code_stub_optional_listnode")


def test_bold__sup_in_code() -> None:
    _test_html_parse("629_description_bold__sup_in_code")


def test_parse_ol() -> None:
    _test_html_parse("2402_description_ol")


def test_artificial_combo() -> None:
    _test_html_parse("artificial_combo")


if __name__ == "__main__":
    test_indent_bullet_point()
    test_artificial_combo()
    print("Ran tests")
