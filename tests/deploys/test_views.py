from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from flask import url_for

from makeitso.deploys import views
from makeitso.extensions import db, job_queue
from makeitso.models.deploy import Deploy
from tests.factories import (
    CommitFactory,
    CommitStatusFactory,
    DeployFactory,
    StackFactory,
    start_running_deploy,
)


def _new_url(commit, **query) -> str:
    return url_for(
        "stacks.deploys.new", stack_id=commit.stack_id, commit_sha=commit.commit_sha, **query
    )


# endpoint: detail, cancel, interrupt or log
def _deploy_url(deploy, endpoint="detail", **query) -> str:
    return url_for(
        f"stacks.deploys.{endpoint}", stack_id=deploy.stack_id, deploy_id=deploy.id, **query
    )


def _deploys(stack_id: int) -> list[Deploy]:
    return list(db.session.scalars(sa.select(Deploy).where(Deploy.stack_id == stack_id)))


class TestNewDeployPage:
    def test_shows_commit(self, client, login):
        commit = CommitFactory.create_sync()
        login()

        response = client.get(_new_url(commit))

        assert response.status_code == 200
        assert commit.commit_message.encode() in response.data

    def test_unknown_commit(self, client, login):
        stack = StackFactory.create_sync()
        login()

        assert (
            client.get(
                url_for("stacks.deploys.new", stack_id=stack.id, commit_sha="nope")
            ).status_code
            == 404
        )

    def test_archived_stack(self, client, login):
        stack = StackFactory.create_sync(archived_at=datetime.now(UTC))
        commit = CommitFactory.create_sync(stack=stack)
        login()

        assert client.get(_new_url(commit)).status_code == 404

    def test_shows_config_error(self, client, login, engage_yaml):
        engage_yaml("deploy:\n  timeout: soon\n")
        login()

        response = client.get(_new_url(CommitFactory.create_sync()))

        assert response.status_code == 200
        assert b"Invalid engage.yaml" in response.data


class TestStartDeployPage:
    # What start_deploy saves is tested in tasks/test_starting.py
    def test_starts_and_shows_deploy(self, client, login):
        commit = CommitFactory.create_sync()
        login("someone")

        response = client.post(_new_url(commit))

        [deploy] = _deploys(commit.stack_id)
        assert response.location == _deploy_url(deploy)
        assert deploy.deployed_by == "someone"

    def test_while_one_runs(self, client, login):
        running = start_running_deploy()
        login()

        response = client.post(_new_url(running.commit))

        assert response.location == _deploy_url(running)
        assert _deploys(running.stack_id) == [running]

    def test_double_click(self, client, login, monkeypatch):
        running = start_running_deploy()
        real_current_deploy = views.current_deploy
        checks = []

        # The first check misses the running deploy, as when two clicks arrive together;
        # the database's one-running-deploy rule then refuses the second save
        def current_deploy(stack_id):
            checks.append(stack_id)
            return None if len(checks) == 1 else real_current_deploy(stack_id)

        monkeypatch.setattr(views, "current_deploy", current_deploy)
        login()

        response = client.post(_new_url(running.commit))

        assert response.location == _deploy_url(running)
        assert _deploys(running.stack_id) == [running]

    @pytest.mark.parametrize("ticked", [[], ["Is it Friday?"]])
    def test_needs_checklist(self, client, login, engage_yaml, ticked):
        commit = CommitFactory.create_sync()
        engage_yaml("review:\n  checklist:\n    - Is it Friday?\n")
        login()

        response = client.post(_new_url(commit), data={"checklist": ticked})

        if ticked:
            assert len(_deploys(commit.stack_id)) == 1
        else:
            assert response.location == _new_url(commit)
            assert _deploys(commit.stack_id) == []

    # Which things block a deploy is tested in test_helpers.py
    @pytest.mark.parametrize("blocker", ["locked", "failed_checks"])
    def test_blocked(self, client, login, blocker):
        stack = StackFactory.create_sync(locked=blocker == "locked", lock_reason="Release freeze")
        commit = CommitFactory.create_sync(stack=stack)
        if blocker == "failed_checks":
            CommitStatusFactory.create_sync(commit=commit, name="tests", state="failure")
        login()

        response = client.post(_new_url(commit))

        assert response.location == _new_url(commit)
        assert _deploys(commit.stack_id) == []

    def test_emergency_bypasses_failed_checks(self, client, login):
        commit = CommitFactory.create_sync()
        CommitStatusFactory.create_sync(commit=commit, name="tests", state="failure")
        login()

        client.post(_new_url(commit, emergency=1))

        [deploy] = _deploys(commit.stack_id)
        assert deploy.deployed_with_bypass is True

    def test_invalid_config(self, client, login, engage_yaml):
        commit = CommitFactory.create_sync()
        engage_yaml("deploy:\n  timeout: soon\n")
        login()

        response = client.post(_new_url(commit))

        assert response.location == _new_url(commit)
        assert _deploys(commit.stack_id) == []


class TestDeployPage:
    def test_shows_deploy(self, client, login):
        deploy = start_running_deploy()
        login()

        response = client.get(_deploy_url(deploy))

        assert response.status_code == 200
        assert deploy.commit.commit_message.encode() in response.data

    def test_deploy_of_other_stack(self, client, login):
        deploy = start_running_deploy()
        other = StackFactory.create_sync()
        login()

        assert (
            client.get(
                url_for("stacks.deploys.detail", stack_id=other.id, deploy_id=deploy.id)
            ).status_code
            == 404
        )


class TestSignal:
    @pytest.mark.parametrize("signal", ["cancel", "interrupt"])
    def test_stores_signal(self, client, login, signal):
        deploy = start_running_deploy()
        login()

        response = client.post(_deploy_url(deploy, signal))

        assert response.location == _deploy_url(deploy)
        job = job_queue.deploys.fetch_job(f"deploy-{deploy.id}")
        assert job is not None
        assert job.meta["signal"] == signal

    def test_finished_deploy(self, client, login):
        deploy = DeployFactory.create_sync()
        login()

        response = client.post(_deploy_url(deploy, "cancel"), follow_redirects=True)

        assert b"Cannot signal a deploy that is not running" in response.data


class TestLog:
    def test_returns_new_output(self, client, login):
        deploy = start_running_deploy()
        deploy.output = "first\nsecond\n"
        db.session.commit()
        login()

        response = client.get(_deploy_url(deploy, "log", offset=6))

        assert response.status_code == 200
        assert b"second" in response.data
        assert b"first" not in response.data

    def test_stops_polling_when_finished(self, client, login):
        deploy = DeployFactory.create_sync()
        login()

        # 286 tells HTMX to stop polling
        assert client.get(_deploy_url(deploy, "log")).status_code == 286


class TestDeployList:
    def test_newest_first(self, client, login):
        stack = StackFactory.create_sync()
        now = datetime.now(UTC)
        older = CommitFactory.create_sync(stack=stack, commit_message="Older")
        newer = CommitFactory.create_sync(stack=stack, commit_message="Newer")
        DeployFactory.create_sync(commit=older, started_at=now - timedelta(days=1))
        DeployFactory.create_sync(commit=newer, started_at=now)
        login()

        response = client.get(url_for("stacks.deploys.list", stack_id=stack.id))

        assert response.status_code == 200
        assert response.data.index(b"Newer") < response.data.index(b"Older")
