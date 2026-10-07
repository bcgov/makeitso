from dataclasses import dataclass
from datetime import datetime

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
    result: str | None
    execution_time: float | None


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

    job_ids = [job_id for registry in registries for job_id in registry.get_job_ids()]
    jobs = [Job(job_id, connection=queue.connection) for job_id in job_ids]

    return jobs


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
                    job.enqueued_at.strftime("%b %d, %Y %H:%M")
                    if job.enqueued_at
                    else None
                ),
                started_at=(
                    job.started_at.strftime("%b %d, %Y %H:%M")
                    if job.started_at
                    else None
                ),
                ended_at=(
                    job.ended_at.strftime("%b %d, %Y %H:%M") if job.ended_at else None
                ),
                result=job.result,
                execution_time=(
                    datetime.now().timestamp() - job.started_at
                    if job.started_at
                    else None
                ),
            )
            for job in jobs
        ],
    )
