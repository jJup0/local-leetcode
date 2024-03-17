import abc
import json
import logging
from typing import Any, NoReturn, cast

import requests
import seleniumrequests  # type: ignore[reportMissingTypeStubs]

from local_leetcode.html_parser import (
    parse_description_html,  # pyright: ignore reportMissingTypeStubs
)
from local_leetcode.leetcode_question_info import QuestionInfo

logger = logging.getLogger(__name__)

LEETCODE_GRAPHQL_API_URL = "https://leetcode.com/graphql"
ERROR_DUMP_FILE_LOCATION_HTML = "fetched.html"
ERROR_DUMP_FILE_LOCATION_JSON = "fetched.json"


class LeetCodeFetcher(abc.ABC):
    """Base class for fetching data from LeetCode."""

    def post_leetcode_graph_ql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Sends a post request to the LeetCode GraphQL API and returns the result.

        Args:
            query (str): GraphQL query to send.
            variables (dict[str, Any] | None, optional):
              Variables with which to fill the GraphQL query, set to None if no variables.
              Defaults to None.

        Returns:
            dict[str, Any]: JSON response from the LeetCode GraphQL API.
        """
        raise NotImplementedError()

    def _fetch_fail(self, response: requests.Response) -> NoReturn:
        try:
            response_content = response.json()
            with open(ERROR_DUMP_FILE_LOCATION_JSON, "wb") as f:
                f.write(response.content)
        except requests.exceptions.JSONDecodeError:
            response_content = response.content.decode("utf-8")[:100] + "..."
            with open(ERROR_DUMP_FILE_LOCATION_HTML, "wb") as f:
                f.write(response.content)

        raise Exception(
            f"Error: Failed to make GraphQL request. Status Code: {response.status_code}. Response: {response_content}"
        )

    def get_daily_question_slug(self) -> str:
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
        result = self.post_leetcode_graph_ql(daily_q_query)
        daily_q_title_slug = result["data"]["activeDailyCodingChallengeQuestion"][
            "question"
        ]["titleSlug"]
        assert type(daily_q_title_slug) is str
        return daily_q_title_slug

    def get_daily_question_description_html(self, daily_q_title_slug: str) -> str:
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
        result = self.post_leetcode_graph_ql(question_query, question_variables)
        problem_description_html = result["data"]["question"]["content"]
        assert type(problem_description_html) is str
        return problem_description_html

    def get_daily_question_description(self, daily_q_title_slug: str):
        description_html = self.get_daily_question_description_html(daily_q_title_slug)
        description_str = parse_description_html(description_html)
        return description_str

    def get_question_info(self, daily_q_title_slug: str) -> QuestionInfo:
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
        result = self.post_leetcode_graph_ql(question_query, gql_variables)
        return QuestionInfo(**result["data"]["question"])

    def get_default_code_unclean(self, title_slug: str):
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
        result = self.post_leetcode_graph_ql(code_gql_query, code_gql_variables)
        all_code_snippets: list[Any] = result["data"]["question"]["codeSnippets"]
        for code_snippet in all_code_snippets:
            if code_snippet["langSlug"] == "python3":
                return code_snippet["code"]
        raise Exception("python3 not found in languages")


class ClassicRequestsFetcher(LeetCodeFetcher):
    """Fetches data from leetcode using requests library.

    No longer works due to LeetCode using Cloudflare protection.
    """

    def post_leetcode_graph_ql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # LeetCode GraphQL API endpoint

        # Define the headers with required information
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com/",
        }

        # Define the GraphQL query as a dictionary
        graphql_query: dict[str, Any] = {"query": query}
        if variables:
            graphql_query["variables"] = variables

        # Make the GraphQL request
        response = requests.post(
            LEETCODE_GRAPHQL_API_URL, headers=headers, json=graphql_query
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            json_response = response.json()
            logger.debug("Got response: %s", json_response)
            return cast(dict[str, Any], json_response)

        self._fetch_fail(response)


class SeleniumRequestsFetcher(LeetCodeFetcher):
    """Fetches data from LeetCode using an extended selenium library `seleniumrequests`.

    Needed due to Clouflare protection.
    """

    def __init__(self) -> None:
        super().__init__()
        self.driver = seleniumrequests.Chrome()
        self.driver.get("https://leetcode.com/")

    def post_leetcode_graph_ql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        csrftoken_cookie = self.driver.get_cookie("csrftoken")  # type: ignore # partially unknown
        if csrftoken_cookie is None:
            raise ValueError("CSRF token cookie not found")

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com/",
            "X-Csrftoken": csrftoken_cookie["value"],
        }

        graphql_query: dict[str, Any] = {"query": query}
        if variables:
            graphql_query["variables"] = variables

        response = self.driver.request(  # type: ignore # partially unknown
            "POST",
            LEETCODE_GRAPHQL_API_URL,
            headers=headers,
            data=json.dumps(graphql_query),
        )

        if response.status_code == 200:
            json_response = response.json()
            logger.debug("Got response: %s", json_response)
            return cast(dict[str, Any], json_response)

        self._fetch_fail(response)
