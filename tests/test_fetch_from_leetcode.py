import logging

import pytest
import selenium.common.exceptions

from local_leetcode.leetcode_fetchers import (
    ClassicRequestsFetcher,
    SeleniumRequestsFetcher,
)

logger = logging.getLogger(__name__)


def test_fetch_using_requests() -> None:
    slug = ClassicRequestsFetcher().get_daily_question_slug()
    assert type(slug) is str
    assert len(slug) > 0


@pytest.mark.skip(reason="Takes too long")
def test_fetch_using_selenium() -> None:
    try:
        slug = SeleniumRequestsFetcher().get_daily_question_slug()
        assert type(slug) is str
        assert len(slug) > 0
    except selenium.common.exceptions.SessionNotCreatedException:
        logger.warning(
            "Selenium could not run, ignore this message if running on a server."
        )
