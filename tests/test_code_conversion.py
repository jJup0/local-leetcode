from local_leetcode.fetch_from_leetcode import clean_code


def test_clean_code():
    str_in = "class Solution:\n    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:"

    expected_out = "class Solution:\n    def insert(self, intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:"

    assert clean_code(str_in) == expected_out
