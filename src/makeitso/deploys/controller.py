import datetime
import os
import subprocess

from rq import Callback
from rq.exceptions import NoSuchJobError
from rq.job import Job

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy, DeployStatus
from makeitso.models.stack import Stack
from makeitso.extensions import job_queue, db


def deployment_task(commit_sha: str, stack_id: int) -> int:
    stack = db.session.scalar(sa.select(Stack).filter_by(id=stack_id))
    print(
        f"Starting deployment for commit {commit_sha} on stack {stack.organization}/{stack.repository}"
    )
    proc = subprocess.Popen(
        ["bash", "./bin/checkout_and_deploy.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        env={
            **os.environ.copy(),
            "COMMIT_SHA": commit_sha,
            "STACK_ORG": stack.organization,
            "STACK_REPO": stack.repository,
        },
    )

    while proc.poll() is None:
        line = proc.stdout.readline()
        if line:
            job = Job.fetch(commit_sha, connection=job_queue.queue.connection)
            job.meta["output"] = job.meta.get("output", "") + line
            job.save_meta()

    if proc.returncode != 0:
        raise Exception(
            f"Deployment failed for commit {commit_sha} on stack {stack.organization}/{stack.repository}"
        )

    return proc.returncode


class Controller:

    @classmethod
    def get_job(cls, commit_sha: str) -> Job | None:
        try:
            job = Job.fetch(commit_sha, connection=job_queue.queue.connection)
            return job
        except NoSuchJobError:
            return None

    @classmethod
    def start_deploy(cls, commit_sha: str, bypass: bool = False) -> Deploy:
        commit = db.session.scalar(
            sa.select(Commit)
            .filter_by(commit_sha=commit_sha)
            .options(so.selectinload(Commit.stack))
        )
        stack = commit.stack

        # Check that this stack doesn't have a deploy in progress already
        deploy = db.session.execute(
            sa.select(Deploy).filter_by(
                stack_id=stack.id, status=DeployStatus.IN_PROGRESS
            )
        ).scalar_one_or_none()

        if deploy:
            return deploy
        # Create deploy object

        deploy = Deploy(
            stack_id=stack.id,
            commit_id=commit.id,
            started_at=datetime.datetime.now(datetime.timezone.utc),
            status=DeployStatus.IN_PROGRESS,
            output="",
            deployed_with_bypass=bypass,
        )
        db.session.add(deploy)
        db.session.commit()

        # put new task on rq
        try:
            job = Job.fetch(commit_sha, connection=job_queue.queue.connection)

            if job.get_status() in [
                "queued",
                "started",
                "rate_limited",
                "ready_to_enqueue",
                "scheduled",
                "deferred",
            ]:
                raise Exception(
                    "A deployment job is already in progress for this commit."
                )

        except NoSuchJobError:
            # Happy path: there is no existing job, so we can enqueue a new one
            pass

        job = job_queue.queue.enqueue(
            deployment_task,
            commit_sha,
            stack.id,
            job_id=commit_sha,
            meta={"deploy_id": deploy.id},
            on_success=Callback(Controller._on_success),
            on_failure=Callback(Controller._on_failure),
            on_stopped=Callback(Controller._on_stopped),
        )

        return deploy

    @staticmethod
    def _on_success(job, connection, result, *args, **kwargs):
        deploy_id = job.meta.get("deploy_id")
        deploy = db.session.get(Deploy, deploy_id)
        deploy.status = DeployStatus.SUCCEEDED
        db.session.commit()

    @staticmethod
    def _on_failure(job, connection, type, value, traceback):
        deploy_id = job.meta.get("deploy_id")
        deploy = db.session.get(Deploy, deploy_id)
        deploy.status = DeployStatus.FAILED
        db.session.commit()

    @staticmethod
    def _on_stopped(job, connection):
        deploy_id = job.meta.get("deploy_id")
        deploy = db.session.get(Deploy, deploy_id)
        deploy.status = DeployStatus.ABORTED
        db.session.commit()
