import os
import subprocess
import time

from rq.job import Job

from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy
from makeitso.models.stack import Stack
from makeitso.extensions import job_queue, db


def deployment_task(commit_sha: str, stack: Stack) -> int:
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
        timeout=900,  # 15 min
    )

    while proc.poll() is None:
        time.sleep(1)
        lines = proc.stdout.readlines()
        print(lines)
        if lines and len(lines) > 0:
            job = Job.fetch(commit_sha, connection=job_queue.queue.connection)
            job.meta["output"] = job.meta.get("output", "") + lines
            job.save_meta()

    if proc.returncode != 0:
        raise Exception(
            f"Deployment failed for commit {commit_sha} on stack {stack.organization}/{stack.repository}"
        )

    return proc.returncode


class BashJobController:

    def __init__(self):
        pass

    def start_deploy(self, commit: Commit):

        deploy = db.session.execute(
            db.select(Deploy).filter_by(stack_id=commit.stack_id)
        ).scalar_one_or_none()

        # Create deploy object

        # put new task on rq

        pass
