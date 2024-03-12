import re

import bs4

MAX_LINE_LENGTH = 80

SPECIAL_NEWLINE_CHAR_PLACEHOLDER = (
    "\u0011"  # device control 1 should not be present in html
)
SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER = (
    "\u0012"  # device control 2 should not be present in html
)


def replace_multiple_whitespace_single_space_replace_special_newling(string: str):
    return (
        re.sub(r"([^\S\n])+", " ", string)
        .replace(SPECIAL_NEWLINE_CHAR_PLACEHOLDER, "\n")
        .replace(SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER, " ")
    )


def replace_multiple_whitespace_single_space(string: str):
    return re.sub(r"\s+", " ", string)


def regular_tag_to_string(tag: bs4.Tag, joiner: str = "", list_depth: int = 0) -> str:
    res_str_list: list[str] = []
    for child in tag.contents:
        if isinstance(child, bs4.NavigableString):
            if child.text.strip():
                res_str_list.append(
                    replace_multiple_whitespace_single_space(child.text)
                )
        elif isinstance(child, bs4.Tag):
            child_type_str = child.name
            str_to_add = ""
            if child_type_str == "sup":
                if child.text.strip().isnumeric():
                    str_to_add += "^"
            elif child_type_str == "sub":
                str_to_add += "_"
            elif child_type_str == "li":
                str_to_add += (
                    SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER * 2 * list_depth + "- "
                )
            elif child_type_str == "ul":
                str_to_add += SPECIAL_NEWLINE_CHAR_PLACEHOLDER + regular_tag_to_string(
                    child, SPECIAL_NEWLINE_CHAR_PLACEHOLDER, list_depth + 1
                )
                res_str_list.append(str_to_add)
                continue

            child_to_str_replaced = (
                replace_multiple_whitespace_single_space_replace_special_newling(
                    regular_tag_to_string(child)
                )
            )
            str_to_add += child_to_str_replaced
            res_str_list.append(str_to_add)
        else:
            print(f"child is other type of page element: {type(child)=}")
    res = joiner.join(res_str_list)
    if tag.name == "ul":
        pass
    return res


def parse_description_html(description_html: str) -> str:
    description_html = f"<div>{description_html}</div>"
    soup = bs4.BeautifulSoup(description_html, "html.parser")

    description_div = soup.find("div")
    assert isinstance(description_div, bs4.Tag)

    full_description_list: list[str] = []
    add_to_list = True
    for description_child in description_div.contents:
        if isinstance(description_child, bs4.NavigableString):
            if not add_to_list:
                continue
            text = description_child.text.strip()
            if text:
                full_description_list.append(text)
            continue
        elif isinstance(description_child, bs4.Tag):
            tag_type_str = description_child.name
            if tag_type_str == "p":
                # p tags containing no text separate description from examples from constraints.
                # do not include examples in the parsed description
                if description_child.text.strip() == "":
                    add_to_list = not add_to_list
                    continue

                if not add_to_list:
                    continue
                full_description_list.append(regular_tag_to_string(description_child))
                full_description_list.append("")
            elif tag_type_str == "ul":
                if not add_to_list:
                    continue
                if full_description_list and full_description_list[-1] == "":
                    full_description_list.pop()
                to_str = regular_tag_to_string(description_child, "\n").split("\n")
                full_description_list.extend(to_str)
                full_description_list.append("")
            elif tag_type_str == "pre" or tag_type_str == "img":
                pass
            else:
                print(f"parsing tag type <{tag_type_str}> not implemented!")

        else:
            print(
                f"description_child is other type of page element: {type(description_child)=}"
            )
    full_description_list.pop()  # pop "" which should be automatically places after constraints <ul>

    line_limited_description_list: list[str] = []
    indent_size = 4
    for line in full_description_list:
        if len(line) <= MAX_LINE_LENGTH:
            line_limited_description_list.append(line)
            continue

        list_depth = 0
        if line.startswith("- "):
            list_depth = 2
        if line.startswith("  - "):
            list_depth = 4

        breaks = 0
        curr_indent_size = 0
        while len(line) + indent_size > MAX_LINE_LENGTH:
            curr_indent_size = list_depth * (breaks > 0)
            split_idx = line.rfind(" ", 0, MAX_LINE_LENGTH - curr_indent_size)
            line_limited_description_list.append(
                " " * curr_indent_size + line[:split_idx]
            )
            line = line[split_idx + 1 :]
            breaks += 1

        line_limited_description_list.append(" " * curr_indent_size + line)

    return "\n".join(line_limited_description_list)
