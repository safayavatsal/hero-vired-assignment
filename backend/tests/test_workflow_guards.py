from uuid import uuid4

import pytest

from app.application.workflow import WorkflowService


class _Connection:
    def __init__(self, version: int) -> None:
        self.version = version

    def execute(self, _query, _params):
        return _Result({"version": self.version})


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


def test_human_decision_version_guard_rejects_stale_state() -> None:
    with pytest.raises(ValueError, match="incident version conflict"):
        WorkflowService._check_version(_Connection(3), uuid4(), 2)


def test_human_decision_version_guard_allows_current_state() -> None:
    WorkflowService._check_version(_Connection(3), uuid4(), 3)
