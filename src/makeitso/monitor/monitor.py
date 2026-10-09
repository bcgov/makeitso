from dataclasses import dataclass
from datetime import UTC, datetime

from rq import Queue
from rq.job import Job
from rq.registry import (
    CanceledJobRegistry,
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    ScheduledJobRegistry,
    StartedJobRegistry,
)

from makeitso.extensions import job_queue
from makeitso.local_time import local_time

# Most jobs to show per queue and per registry, so old failed jobs don't pile up on the page
MAX_JOBS = 50


@dataclass
class QueueData:
    name: str
    count: int
    jobs: list[JobData]


@dataclass
class JobData:
    id: str
    status: str
    started_at: str | None
    execution_time: str | None


def _get_all_jobs(queue: Queue):
    """Jobs waiting for a worker are in the queue, every other state has its own registry"""
    registries = [
        StartedJobRegistry(queue=queue),
        FinishedJobRegistry(queue=queue),
        FailedJobRegistry(queue=queue),
        DeferredJobRegistry(queue=queue),
        ScheduledJobRegistry(queue=queue),
        CanceledJobRegistry(queue=queue),
    ]

    job_ids = queue.get_job_ids(0, MAX_JOBS)
    job_ids += [
        job_id
        for registry in registries
        for job_id in registry.get_job_ids(0, MAX_JOBS - 1, desc=True)
    ]
    jobs = Job.fetch_many(job_ids, connection=queue.connection)

    return [job for job in jobs if job is not None]


def _execution_time(job: Job) -> str | None:
    if job.started_at is None:
        return None
    end = job.ended_at or datetime.now(UTC)
    minutes, seconds = divmod(int((end - job.started_at).total_seconds()), 60)
    return f"{minutes}m {seconds:02d}s"


def get_queue_data(queue: Queue):
    jobs = _get_all_jobs(queue)

    return QueueData(
        name=queue.name,
        count=len(jobs),
        jobs=[
            JobData(
                id=job.id,
                status=job.get_status().value,
                started_at=(local_time(job.started_at) if job.started_at else None),
                execution_time=_execution_time(job),
            )
            for job in jobs
        ],
    )


def get_queues_data():
    return [get_queue_data(job_queue.syncs), get_queue_data(job_queue.deploys)]
