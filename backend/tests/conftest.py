"""
Shared pytest fixtures and reporting for the request-runner tests.

The ``tmp_db`` fixture redirects every database read/write to a temporary file
so tests never touch the real ``data/dashboard.db``. The reporting hooks below
print one short line per test — number, result and description — as the suite
runs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend import db

_test_info: dict[str, tuple[int, str]] = {}
_test_total: int = 0


@pytest.fixture
def tmp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    return path


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    global _test_total
    _test_total = len(items)
    _test_info.clear()
    for index, item in enumerate(items, start=1):
        _test_info[item.nodeid] = (index, _description(item))


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when != "call":
        return
    info = _test_info.get(report.nodeid)
    if info is None:
        return
    index, description = info
    if report.passed:
        result = "PASS"
    elif report.failed:
        result = "FAIL"
    elif report.skipped:
        result = "SKIP"
    else:
        result = "UNKNOWN"
    print(f"[{index:02d}/{_test_total:02d}] {result:4s}  {description}")


def _description(item: pytest.Item) -> str:
    obj = getattr(item, "function", None) or getattr(item, "obj", None)
    doc = getattr(obj, "__doc__", None) if obj is not None else None
    if doc:
        for line in doc.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return item.name.replace("_", " ")