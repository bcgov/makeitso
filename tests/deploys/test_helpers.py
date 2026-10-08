import pytest

from makeitso.deploys.helpers import deploy_blockers, emergency_mode
from tests.factories import CommitFactory, CommitStatusFactory, StackFactory


class TestDeployBlockers:
    def test_nothing_blocks_passing_commit(self):
        commit = CommitFactory.create_sync()
        CommitStatusFactory.create_sync(commit=commit, name="tests", state="success")

        assert deploy_blockers(commit.stack, commit, []) == []

    def test_locked_stack(self):
        stack = StackFactory.create_sync(locked=True, lock_reason="Release freeze")
        commit = CommitFactory.create_sync(stack=stack)

        assert deploy_blockers(stack, commit, []) == ["The stack is locked: Release freeze"]

    def test_failed_check(self):
        commit = CommitFactory.create_sync()
        CommitStatusFactory.create_sync(commit=commit, name="tests", state="failure")

        assert deploy_blockers(commit.stack, commit, []) == ["Some checks failed"]

    def test_allowed_failure_does_not_block(self):
        commit = CommitFactory.create_sync()
        CommitStatusFactory.create_sync(commit=commit, name="lint", state="failure")

        assert deploy_blockers(commit.stack, commit, ["lint"]) == []

    def test_emergency_skips_failed_checks_but_not_lock(self):
        stack = StackFactory.create_sync(locked=True, lock_reason="Release freeze")
        commit = CommitFactory.create_sync(stack=stack)
        CommitStatusFactory.create_sync(commit=commit, name="tests", state="failure")

        assert deploy_blockers(stack, commit, [], emergency=True) == [
            "The stack is locked: Release freeze"
        ]


class TestEmergencyMode:
    @pytest.mark.parametrize(
        ("query", "expected"), [("?emergency=1", True), ("?emergency=true", False), ("", False)]
    )
    def test_only_on_for_emergency_1(self, app, query, expected):
        with app.test_request_context(f"/{query}"):
            assert emergency_mode() is expected
