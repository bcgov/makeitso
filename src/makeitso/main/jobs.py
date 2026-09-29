import os
import subprocess
import time

from rq.job import Job
from makeitso.extensions import job_queue
from makeitso.models.deploy import Deploy
from makeitso.models.stack import Stack


# Example background job: waits `delay` seconds to simulate slow work, then returns the sum
def add_numbers(x: int, y: int, delay: int = 5) -> int:
    time.sleep(delay)
    return x + y
