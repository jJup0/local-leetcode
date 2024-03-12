import logging
import os
import re
import subprocess
from typing import Any, TypedDict

import bs4
from leetcode_fetchers import LeetCodeFetcher, SeleniumRequestsFetcher

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MAX_LINE_LENGTH = 80


def replace_multiple_whitespace_single_space_strip(string: str):
    return replace_multiple_whitespace_single_space(string).strip()


def replace_multiple_whitespace_single_space(string: str):
    return re.sub(r"\s+", " ", string)


def replace_multiple_whitespace_single_space_except_newline(string: str):
    return re.sub(r"\s+", " ", string)


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


full_cookie = """__stripe_mid=d81c75fa-5168-4587-8dc4-b75ad4bc2679eb80ff; cf_clearance=jqwjDhjDaTvbQP5VTJvArFW7IvRm.qIZ4Y9CJ77o4_8-1709743798-1.0.1.1-5mBJOja0.F1bZcW3btW4bIgk7r9lRBqetjecTGykR.R_lGAyGgqFvVZJEl8aaqOw7ZwclVT0QNchNCaYOhNb4w; csrftoken=yVFtTORNlCvpgqr1oAHptaYszp963rF4jaMlObpvzeaVSe4ycfvqDIzfwht0ki12; LEETCODE_SESSION=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMjYzOTk3OCIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImFsbGF1dGguYWNjb3VudC5hdXRoX2JhY2tlbmRzLkF1dGhlbnRpY2F0aW9uQmFja2VuZCIsIl9hdXRoX3VzZXJfaGFzaCI6IjlhMzBiNzNmNzJjYjI1MWNjMTk0YmVlNWFhMGYyYjk3YWJkYjk0MDhlYmEwYTkwZGMyNGI5NWRjM2Y3MjdmYzkiLCJpZCI6MjYzOTk3OCwiZW1haWwiOiJqYWtvYi5yb2l0aGluZ2VyQG1lLmNvbSIsInVzZXJuYW1lIjoiakp1cDAiLCJ1c2VyX3NsdWciOiJqSnVwMCIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNvbS91c2Vycy9kZWZhdWx0X2F2YXRhci5qcGciLCJyZWZyZXNoZWRfYXQiOjE3MDk3NDM4MDksImlwIjoiMmEwMjo4Mzg4OjZiYzA6NWM4MDo3MDBmOjNmMDpmNzY4OmRmZDIiLCJpZGVudGl0eSI6IjRmMDllMDFjODNkNjkxMDBjMzYzYzMzYWVjZmVmOWY4IiwiX3Nlc3Npb25fZXhwaXJ5IjoxMjA5NjAwLCJzZXNzaW9uX2lkIjo1NzA3NzM2OH0.53JJBiaGqC_HG_7a0NMvA3JWY5mxO1BT0bPe0JP-90Y; __cf_bm=3aP3MfTYS3o1ndpCjzmH2qPv8tKiBXdOajpwnwjeL9I-1709756167-1.0.1.1-CW9XX2KqEEjlbGtYYXH_FYGQVRgmwtLM4o64mKvLGttZbYuE2DdmvefZLv2AlmUsf0lcZlOzRXYM0jW4pxXAtw; INGRESSCOOKIE=1edca20352b277c7f2408f99cb66aa33|8e0876c7c1464cc0ac96bc2edceabd27; _dd_s=rum=0&expire=1709757073680"""


def get_daily_question_slug(fetcher: LeetCodeFetcher) -> str:
    daily_q_query = """
    {
        activeDailyCodingChallengeQuestion {
            date
            link
            question {
                titleSlug
            }
        }
    }
    """
    result = fetcher.post_leetcode_graph_ql(daily_q_query)
    daily_q_title_slug = result["data"]["activeDailyCodingChallengeQuestion"][
        "question"
    ]["titleSlug"]
    return daily_q_title_slug


def get_daily_question_description_html(
    fetcher: LeetCodeFetcher, daily_q_title_slug: str
) -> str:
    question_query = """query questionContent($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            content
            mysqlSchemas
            dataSchemas
        }
    }
    """
    question_variables = {
        "titleSlug": daily_q_title_slug,
    }
    result = fetcher.post_leetcode_graph_ql(question_query, question_variables)
    problem_description_html = result["data"]["question"]["content"]
    return problem_description_html


def regular_tag_to_string(tag: bs4.Tag, joiner: str = "", list_depth: int = 0) -> str:
    res_str_list: list[str] = []
    for child in tag.contents:
        if isinstance(child, bs4.NavigableString):
            if child.text.strip():
                res_str_list.append(
                    replace_multiple_whitespace_single_space_except_newline(child.text)
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


def get_daily_question_description(fetcher: LeetCodeFetcher, daily_q_title_slug: str):
    description_html = get_daily_question_description_html(fetcher, daily_q_title_slug)
    description_str = parse_description_html(description_html)
    return description_str


class QuestionInfo(TypedDict):
    questionId: int
    questionFrontendId: int
    title: str
    titleSlug: str
    difficulty: str


def get_question_info(
    fetcher: LeetCodeFetcher, daily_q_title_slug: str
) -> QuestionInfo:
    question_query = """query questionTitle($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            difficulty
        }
    }
    """
    gql_variables = {
        "titleSlug": daily_q_title_slug,
    }
    result = fetcher.post_leetcode_graph_ql(question_query, gql_variables)
    return QuestionInfo(result["data"]["question"])


def get_default_code_unclean(fetcher: LeetCodeFetcher, title_slug: str):
    code_gql_query = """query questionEditorData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            codeSnippets {
                langSlug
                code
            }
        }
    }
    """
    code_gql_variables = {
        "titleSlug": title_slug,
    }
    result = fetcher.post_leetcode_graph_ql(code_gql_query, code_gql_variables)
    all_code_snippets: list[Any] = result["data"]["question"]["codeSnippets"]
    for code_snippet in all_code_snippets:
        if code_snippet["langSlug"] == "python3":
            return code_snippet["code"]
    raise Exception("python3 not found in languages")


def clean_code(unclean_code: str) -> str:
    # todo only match full word for List, otherwise function names with List
    # or ListNode definitions will get messed up
    replacements = (("List", "list"),)
    for str_to_replace, replacement in replacements:
        unclean_code = unclean_code.replace(str_to_replace, replacement)
    return unclean_code


def get_default_code(fetcher: LeetCodeFetcher, title_slug: str) -> str:
    unclean_code = get_default_code_unclean(fetcher, title_slug)
    return clean_code(unclean_code)


def get_question_path(question_info: QuestionInfo) -> str:
    q_number = question_info["questionFrontendId"]
    difficulty = question_info["difficulty"]
    title = question_info["title"]
    file_path = os.path.realpath(
        os.path.join(os.path.dirname(__file__), difficulty, f"{q_number}. {title}.py")
    )
    return file_path


def create_question_file(
    q_description: str, default_code: str, question_info: QuestionInfo
):
    file_path = get_question_path(question_info)
    if os.path.isfile(file_path):
        logger.info("File already exists")
        return

    if not os.path.isdir(os.path.dirname(file_path)):
        raise NotADirectoryError(
            f"Directory {os.path.dirname(file_path)} does not exist."
        )

    with open(file_path, "w") as f:
        f.write('"""\n')
        f.write(q_description)
        f.write('\n"""\n')
        f.write(default_code)
        f.write("...")


def open_question_file(question_info: QuestionInfo):
    file_path = get_question_path(question_info)
    subprocess.run(["code", file_path], shell=True)


def main():
    fetcher = SeleniumRequestsFetcher()
    daily_q_slug = get_daily_question_slug(fetcher)

    default_code = get_default_code(fetcher, daily_q_slug)

    q_description = get_daily_question_description(fetcher, daily_q_slug)

    question_info = get_question_info(fetcher, daily_q_slug)

    create_question_file(q_description, default_code, question_info)

    open_question_file(question_info)


if __name__ == "__main__":
    main()
