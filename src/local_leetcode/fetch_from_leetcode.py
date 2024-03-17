import logging
import os
import subprocess
from typing import Any, TypedDict

from .html_parser import parse_description_html
from .leetcode_fetchers import ClassicRequestsFetcher, LeetCodeFetcher

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    replacements = (("List[", "list["),)
    for pattern_to_replace, replacement in replacements:
        # unclean_code = re.sub(pattern_to_replace, replacement, unclean_code)
        unclean_code = unclean_code.replace(pattern_to_replace, replacement)
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
    temp_file_name = "temp.py"

    file_path = get_question_path(question_info)
    if os.path.isfile(file_path):
        logger.info("File already exists")
        return

    if not os.path.isdir(os.path.dirname(file_path)):
        logger.error(
            "Directory %s does not exist. Writing to %s",
            os.path.dirname(file_path),
            temp_file_name,
        )
        file_path = temp_file_name

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
    logger.info("Fetching daily from LeetCode")
    fetcher = ClassicRequestsFetcher()
    daily_q_slug = get_daily_question_slug(fetcher)

    default_code = get_default_code(fetcher, daily_q_slug)

    q_description = get_daily_question_description(fetcher, daily_q_slug)

    question_info = get_question_info(fetcher, daily_q_slug)

    create_question_file(q_description, default_code, question_info)

    open_question_file(question_info)


if __name__ == "__main__":
    main()
