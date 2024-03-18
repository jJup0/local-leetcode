import logging
import os
import re
import subprocess

from local_leetcode.leetcode_fetchers import ClassicRequestsFetcher
from local_leetcode.leetcode_question_info import QuestionInfo

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def clean_code(unclean_code: str) -> str:
    # todo only match full word for List, otherwise function names with List
    # or ListNode definitions will get messed up
    replacements = (
        (r"List\[", "list["),
        (r"Optional\[(\w+)\]", r"\1 | None"),
    )
    for pattern_to_replace, replacement in replacements:
        unclean_code = re.sub(pattern_to_replace, replacement, unclean_code)
    return unclean_code


def get_question_path(question_info: QuestionInfo) -> str:
    q_number = question_info.questionFrontendId
    difficulty = question_info.difficulty
    title = question_info.title
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
    daily_q_slug = fetcher.get_daily_question_slug()

    default_code = clean_code(fetcher.get_default_code_unclean(daily_q_slug))

    q_description = fetcher.get_daily_question_description(daily_q_slug)

    question_info = fetcher.get_question_info(daily_q_slug)

    create_question_file(q_description, default_code, question_info)

    open_question_file(question_info)


if __name__ == "__main__":
    main()
