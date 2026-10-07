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
from rq.worker_registration import clean_worker_registry

from makeitso.extensions import job_queue


@dataclass
class QueueData:
    name: str
    count: int
    jobs: list[JobData]


@dataclass
class JobData:
    id: str
    status: str
    enqueued_at: str | None
    started_at: str | None
    ended_at: str | None
    execution_time: str | None


def _get_all_jobs(queue: Queue):
    """
    Queue object doesn't keep track of the jobs in real-time, but the job registries do
    """

    clean_worker_registry(queue)

    registries = [
        StartedJobRegistry(queue=queue),
        FinishedJobRegistry(queue=queue),
        FailedJobRegistry(queue=queue),
        DeferredJobRegistry(queue=queue),
        ScheduledJobRegistry(queue=queue),
        CanceledJobRegistry(queue=queue),
    ]

    # Jobs waiting for a worker are only in the queue itself, not in a registry
    job_ids = queue.get_job_ids()
    job_ids += [job_id for registry in registries for job_id in registry.get_job_ids()]
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
                enqueued_at=(
                    job.enqueued_at.strftime("%b %d, %Y %H:%M") if job.enqueued_at else None
                ),
                started_at=(job.started_at.strftime("%b %d, %Y %H:%M") if job.started_at else None),
                ended_at=(job.ended_at.strftime("%b %d, %Y %H:%M") if job.ended_at else None),
                execution_time=_execution_time(job),
            )
            for job in jobs
        ],
    )


def get_queues_data():
    return [get_queue_data(job_queue.syncs), get_queue_data(job_queue.deploys)]
