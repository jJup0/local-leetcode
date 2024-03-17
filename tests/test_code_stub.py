import difflib

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


if __name__ == "__main__":
    test_indent_bullet_point()
