from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from makeitso.deploys.queries import (
    commits_between,
    current_deploy,
    last_successful_deploy,
    previous_deploys,
)
from makeitso.extensions import db
from makeitso.models.deploy import DeployStatus
from tests.factories import CommitFactory, DeployFactory, StackFactory


def _ago(minutes: int) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=minutes)


class TestCurrentDeploy:
    def test_running_deploy(self):
        commit = CommitFactory.create_sync()
        DeployFactory.create_sync(commit=commit, status=DeployStatus.FAILED)
        running = DeployFactory.create_sync(commit=commit, status=DeployStatus.IN_PROGRESS)

        assert current_deploy(commit.stack_id) == running

    def test_none_when_nothing_runs(self):
        deploy = DeployFactory.create_sync(status=DeployStatus.FAILED)

        assert current_deploy(deploy.stack_id) is None

    def test_only_one_per_stack(self):
        commit = CommitFactory.create_sync()
        DeployFactory.create_sync(commit=commit, status=DeployStatus.IN_PROGRESS)

        # Another stack can run its own deploy
        DeployFactory.create_sync(status=DeployStatus.IN_PROGRESS)

        with pytest.raises(IntegrityError):
            DeployFactory.create_sync(commit=commit, status=DeployStatus.IN_PROGRESS)
        db.session.rollback()


class TestLastSuccessfulDeploy:
    def test_newest_succeeded(self):
        commit = CommitFactory.create_sync()
        DeployFactory.create_sync(commit=commit, started_at=_ago(30))
        newest = DeployFactory.create_sync(commit=commit, started_at=_ago(20))
        DeployFactory.create_sync(commit=commit, status=DeployStatus.FAILED, started_at=_ago(10))

        assert last_successful_deploy(commit.stack_id) == newest

    def test_none_without_success(self):
        deploy = DeployFactory.create_sync(status=DeployStatus.FAILED)

        assert last_successful_deploy(deploy.stack_id) is None


class TestPreviousDeploys:
    def test_finished_newest_first(self):
        commit = CommitFactory.create_sync()
        older = DeployFactory.create_sync(commit=commit, started_at=_ago(30))
        newer = DeployFactory.create_sync(
            commit=commit, status=DeployStatus.FAILED, started_at=_ago(20)
        )
        DeployFactory.create_sync(
            commit=commit, status=DeployStatus.IN_PROGRESS, started_at=_ago(10)
        )

        assert previous_deploys(commit.stack_id) == [newer, older]
        assert previous_deploys(commit.stack_id, limit=1) == [newer]


class TestCommitsBetween:
    def test_range(self):
        stack = StackFactory.create_sync()
        first, second, third, fourth = (CommitFactory.create_sync(stack=stack) for _ in range(4))

        assert commits_between(stack.id, None, third) == [third, second, first]
        assert commits_between(stack.id, first, third) == [third, second]
        assert commits_between(stack.id, second) == [fourth, third]

    def test_skips_other_stacks(self):
        mine = CommitFactory.create_sync()
        # On another stack
        CommitFactory.create_sync()

        assert commits_between(mine.stack_id, None) == [mine]
