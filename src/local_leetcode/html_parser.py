import logging
import re

import bs4

logger = logging.getLogger(__name__)

# maximum characters per line when generating docstring,
# whitespace does not count towards this limit
MAX_CHARS_PER_LINE = 80

# device control 1 should not be present in html
SPECIAL_NEWLINE_CHAR_PLACEHOLDER = "\u0011"
# device control 2 should not be present in html
SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER = "\u0012"

SPECIAL_NON_BREAKABLE_SPACE_PLACEHOLDER = "\u0013"


def replace_multiple_whitespace_single_space_replace_special_newline(string: str):
    return (
        re.sub(r"([^\S\n])+", " ", string)
        .replace(SPECIAL_NEWLINE_CHAR_PLACEHOLDER, "\n")
        .replace(SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER, " ")
    )


def replace_multiple_whitespace_single_space(string: str):
    return re.sub(r"\s+", " ", string)


def regular_tag_to_string(
    tag: bs4.Tag,
    joiner: str = "",
    list_depth: int = 0,
    list_type: str = "",
) -> str:
    list_item_count = 0
    res_str_list: list[str] = []
    for child in tag.contents:
        if isinstance(child, bs4.NavigableString):
            if child.text.strip():
                res_str_list.append(
                    replace_multiple_whitespace_single_space(child.text)
                )
        elif isinstance(child, bs4.Tag):
            child_type_str = child.name
            if child_type_str == "ul" or child_type_str == "ol":
                res_str_list.append(
                    SPECIAL_NEWLINE_CHAR_PLACEHOLDER
                    + regular_tag_to_string(
                        child,
                        SPECIAL_NEWLINE_CHAR_PLACEHOLDER,
                        list_depth + 1,
                        list_type=child_type_str,
                    )
                )
                continue

            str_prefix = ""
            child_content_as_str = regular_tag_to_string(child)
            if child_type_str == "sup":
                if child.text.strip().isnumeric():
                    str_prefix = "^"
            elif child_type_str == "sub":
                str_prefix = "_"
            elif child_type_str == "li":
                list_item_count += 1
                if list_type == "ul":
                    str_prefix = (
                        f"{SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER * 2 * list_depth}- "
                    )
                elif list_type == "ol":
                    str_prefix = f"{SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER * (2 * list_depth)}{list_item_count}.{SPECIAL_UNREMOVEABLE_SPACE_PLACEHOLDER}"
                else:
                    logger.error("<li> tag encountered outside of list")
            elif child_type_str == "code":
                # text within a code block should not be broken up
                # inequalities are often in code blocks, which are very ugly when broken up
                strongly_joined_code = re.sub(
                    r"\s", SPECIAL_NON_BREAKABLE_SPACE_PLACEHOLDER, child_content_as_str
                )
                # pad with spaces, to ensure code does not stick to any neighboring styled text like <b> or <u>
                child_content_as_str = f" {strongly_joined_code} "

            res_str_list.append(str_prefix + child_content_as_str)
        else:
            logger.warning("Child element has unexpected type: %s", type(child))

    simple_joined = joiner.join(res_str_list)
    double_space_removed = re.sub(r"([^\S\n])+", " ", simple_joined)
    space_before_punctuation_removed = re.sub(
        r"\s+([.,;:?!^'\"])", r"\1", double_space_removed
    )
    return space_before_punctuation_removed


def parse_description_html(description_html: str) -> str:
    description_html = f"<html>{description_html}</html>"
    soup = bs4.BeautifulSoup(description_html, "html.parser")

    description_div = soup.find("html")
    assert isinstance(description_div, bs4.Tag)

    full_description_list: list[str] = []
    include_in_description = True
    for description_child in description_div.contents:
        # p tags containing a single non breakable space should separate
        # description from examples from constraints. Do not include
        # examples in the parsed description
        if (
            isinstance(description_child, bs4.Tag)
            and description_child.name == "p"
            and description_child.text == "\u00a0"
        ):
            # toggle whether to include html in description
            include_in_description = not include_in_description
            continue

        if not include_in_description:
            continue

        if isinstance(description_child, bs4.NavigableString):
            text = description_child.text.strip()
            if text:
                full_description_list.append(text)
            continue
        elif isinstance(description_child, bs4.Tag):
            tag_type_str = description_child.name
            # the "top level tags" of the description can only be <p>, <ul>, <pre> or <img> tags,
            # these may contain several other tags
            if tag_type_str == "p":
                full_description_list.append(regular_tag_to_string(description_child))
                full_description_list.append("")
            elif tag_type_str == "ul":
                if full_description_list and full_description_list[-1] == "":
                    full_description_list.pop()
                to_str = regular_tag_to_string(
                    description_child, "\n", list_type="ul"
                ).split("\n")
                full_description_list.extend(line for line in to_str)
                full_description_list.append("")
            elif tag_type_str == "ol":
                if full_description_list and full_description_list[-1] == "":
                    full_description_list.pop()
                to_str = regular_tag_to_string(
                    description_child, "\n", list_type="ol"
                ).split("\n")
                full_description_list.extend(line for line in to_str)
                full_description_list.append("")
            elif tag_type_str == "pre" or tag_type_str == "img":
                logger.warning("Handling of <pre> and <img> tags not implemented")
            else:
                print(f"parsing tag type <{tag_type_str}> not implemented!")

        else:
            print(
                f"description_child is other type of page element: {type(description_child)=}"
            )

    if full_description_list[-1] == "":
        full_description_list.pop()

    newlines_replaced_description_list: list[str] = []
    for line in full_description_list:
        split_lines = (
            replace_multiple_whitespace_single_space_replace_special_newline(line)
            .rstrip()
            .split("\n")
        )
        newlines_replaced_description_list.extend(line.rstrip() for line in split_lines)

    line_limited_description_list: list[str] = []
    indent_size = 4
    for line in newlines_replaced_description_list:
        if len(line) <= MAX_CHARS_PER_LINE:
            line_limited_description_list.append(line)
            continue

        list_depth = 0
        if line.startswith("- "):
            list_depth = 2
        elif line.startswith("  - "):
            list_depth = 4
        elif re.findall(r"^\d+\..*", line, re.MULTILINE):
            list_depth = 3
        elif re.findall(r"^  \d+\..*", line, re.MULTILINE):
            list_depth = 5

        breaks = 0
        curr_indent_size = 0
        while len(line) - indent_size > MAX_CHARS_PER_LINE:
            curr_indent_size = list_depth * (breaks > 0)
            split_idx = line.rfind(" ", 0, MAX_CHARS_PER_LINE + curr_indent_size)
            line_limited_description_list.append(
                " " * curr_indent_size + line[:split_idx]
            )
            line = line[split_idx + 1 :]
            breaks += 1

        curr_indent_size = list_depth * (breaks > 0)
        line_limited_description_list.append(" " * curr_indent_size + line)

    return "\n".join(
        line.replace(SPECIAL_NON_BREAKABLE_SPACE_PLACEHOLDER, " ").rstrip()
        for line in line_limited_description_list
    )
