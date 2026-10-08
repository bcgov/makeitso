from datetime import UTC, datetime, timedelta

import pytest
from rq.job import JobStatus

from makeitso.deploys.tasks import (
    CHECKOUT_TIMEOUT,
    DEPLOY_TIMEOUT,
    fail_if_lost,
    requested_signal,
    run_deploy,
    signal_job,
    start_deploy,
)
from makeitso.extensions import job_queue
from makeitso.models.deploy import DeployStatus
from tests.factories import CommitFactory, DeployFactory, start_running_deploy


def _job(deploy):
    return job_queue.deploys.fetch_job(f"deploy-{deploy.id}")


class TestStartDeploy:
    def test_saves_and_queues(self):
        commit = CommitFactory.create_sync()

        deploy = start_deploy(commit.stack, commit, timeout=600, deployed_by="octocat", bypass=True)

        assert deploy.status is DeployStatus.IN_PROGRESS
        assert deploy.deployed_by == "octocat"
        assert deploy.deployed_with_bypass is True
        job = _job(deploy)
        assert job.func is run_deploy
        assert job.args == (deploy.id,)
        assert job.timeout == CHECKOUT_TIMEOUT + 600 + 2 * DEPLOY_TIMEOUT + 60

    def test_first_deploy_has_no_since_commit(self):
        assert start_running_deploy().since_commit_id is None

    def test_since_commit_is_live_commit(self):
        live = DeployFactory.create_sync()

        deploy = start_running_deploy(CommitFactory.create_sync(stack=live.stack))

        assert deploy.since_commit_id == live.commit_id


class TestSignalJob:
    @pytest.mark.parametrize("signal", ["cancel", "interrupt"])
    def test_stores_signal(self, signal):
        deploy = start_running_deploy()

        signal_job(deploy, signal)

        assert _job(deploy).meta["signal"] == signal
        assert requested_signal(deploy) == signal

    def test_refuses_finished_deploy(self):
        with pytest.raises(ValueError, match="not running"):
            signal_job(DeployFactory.create_sync(), "cancel")

    def test_refuses_missing_job(self):
        deploy = DeployFactory.create_sync(status=DeployStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="no associated job"):
            signal_job(deploy, "cancel")

    def test_no_signal_once_finished(self):
        deploy = start_running_deploy()
        signal_job(deploy, "cancel")
        deploy.status = DeployStatus.CANCELLED

        assert requested_signal(deploy) is None


class TestFailIfLost:
    def test_leaves_finished_deploy(self):
        deploy = DeployFactory.create_sync(status=DeployStatus.SUCCEEDED)

        fail_if_lost(deploy)

        assert deploy.status is DeployStatus.SUCCEEDED

    def test_leaves_live_job(self):
        deploy = start_running_deploy()

        fail_if_lost(deploy)

        assert deploy.status is DeployStatus.IN_PROGRESS

    def test_missing_job(self):
        deploy = DeployFactory.create_sync(status=DeployStatus.IN_PROGRESS)

        fail_if_lost(deploy)

        assert deploy.status is DeployStatus.FAILED
        assert deploy.ended_at is not None
        assert "The worker stopped" in deploy.output

    @pytest.mark.parametrize(
        ("job_status", "expected"),
        [
            (JobStatus.FAILED, DeployStatus.FAILED),
            (JobStatus.STOPPED, DeployStatus.ABORTED),
            (JobStatus.CANCELED, DeployStatus.ABORTED),
        ],
    )
    def test_ended_job(self, job_status, expected):
        deploy = start_running_deploy()
        _job(deploy).set_status(job_status)

        fail_if_lost(deploy)

        assert deploy.status is expected

    @pytest.mark.parametrize(
        ("minutes", "expected"), [(1, DeployStatus.IN_PROGRESS), (3, DeployStatus.FAILED)]
    )
    def test_worker_heartbeat(self, minutes, expected):
        deploy = start_running_deploy()
        job = _job(deploy)
        job.set_status(JobStatus.STARTED)
        job.last_heartbeat = datetime.now(UTC) - timedelta(minutes=minutes)
        job.save()

        fail_if_lost(deploy)

        assert deploy.status is expected
