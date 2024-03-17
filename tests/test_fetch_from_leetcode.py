import pytest

from local_leetcode.leetcode_fetchers import (
    ClassicRequestsFetcher,
    LeetCodeFetcher,
    SeleniumRequestsFetcher,
)


@pytest.mark.parametrize(
    "fetcher", [ClassicRequestsFetcher(), SeleniumRequestsFetcher()]
)
def test_fetch_using_requests(fetcher: LeetCodeFetcher):
    slug = fetcher.get_daily_question_slug()
    assert type(slug) is str
    assert len(slug) > 0
