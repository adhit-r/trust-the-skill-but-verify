from src.core.scheduler import Scheduler


def test_due_returns_ready_jobs():
    s = Scheduler()
    s.add(0, "a")
    assert s.due() == ["a"]

# TODO: add a test for drain ordering
