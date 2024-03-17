import dataclasses


@dataclasses.dataclass(kw_only=True)
class QuestionInfo:
    questionId: int
    questionFrontendId: int
    title: str
    titleSlug: str
    difficulty: str
