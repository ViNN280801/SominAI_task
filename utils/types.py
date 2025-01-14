from typing import TypedDict


class TaskData(TypedDict):
    """
    TypedDict for task data stored in Redis.
    """

    status: str
    keyword: str
    region: str | None
    result: dict | None
