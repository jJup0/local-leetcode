import abc
import json
import logging
from typing import Any, NoReturn, cast

import requests
import seleniumrequests  # pyright: ignore reportMissingTypeStubs

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

    def fetch_fail(self, response: requests.Response) -> NoReturn:
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

        self.fetch_fail(response)


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

        self.fetch_fail(response)
