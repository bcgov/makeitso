import os
import subprocess
import time

from rq.job import Job
from makeitso.extensions import job_queue
from makeitso.models.stack import Stack


# Example background job: waits `delay` seconds to simulate slow work, then returns the sum
def add_numbers(x: int, y: int, delay: int = 5) -> int:
    time.sleep(delay)
    return x + y


def run_deployment(commit_sha: str, stack: Stack) -> int:
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
        print(line)
        if line:
            job = Job.fetch(commit_sha, connection=job_queue.queue.connection)
            job.meta["output"] = job.meta.get("output", "") + line
            job.save_meta()

    if proc.returncode != 0:
        raise Exception(
            f"Deployment failed for commit {commit_sha} on stack {stack.organization}/{stack.repository}"
        )

    return proc.returncode
