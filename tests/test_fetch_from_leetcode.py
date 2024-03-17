import pytest

from local_leetcode.fetch_from_leetcode import get_daily_question_slug
from local_leetcode.leetcode_fetchers import (
    ClassicRequestsFetcher,
    LeetCodeFetcher,
    SeleniumRequestsFetcher,
)


@pytest.mark.parametrize(
    "fetcher", [ClassicRequestsFetcher(), SeleniumRequestsFetcher()]
)
def test_fetch_using_requests(fetcher: LeetCodeFetcher):
    slug = get_daily_question_slug(fetcher)
    assert type(slug) is str
    assert len(slug) > 0
