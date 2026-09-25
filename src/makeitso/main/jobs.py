import subprocess
import time

from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq.registry import StartedJobRegistry
from makeitso.extensions import job_queue


# Example background job: waits `delay` seconds to simulate slow work, then returns the sum
def add_numbers(x: int, y: int, delay: int = 5) -> int:
    time.sleep(delay)
    return x + y


def run_bash_script(commit_sha: str) -> int:

    proc = subprocess.Popen(
        ["bash", "test.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    while proc.poll() is None:
        line = proc.stdout.readline()
        if line:
            try:
                job = Job.fetch(commit_sha, connection=job_queue.queue.connection)
                job.meta["output"] = job.meta.get("output", "") + line
                job.save_meta()
        time.sleep(2)

    return proc.returncode
