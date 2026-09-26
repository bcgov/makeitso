from dataclasses import dataclass

from github import GithubException
from rq import get_current_job
from rq.exceptions import DuplicateJobError
from rq.job import JobStatus

from makeitso.extensions import db, job_queue
from makeitso.github import GitHubError, GitHubRepo, client_for_server
from makeitso.models.stack import Stack
from makeitso.stacks.sync import sync_commits

# Job states that mean a sync is waiting for a worker or running
ACTIVE_STATUSES = {JobStatus.QUEUED, JobStatus.STARTED, JobStatus.DEFERRED, JobStatus.SCHEDULED}


@dataclass(frozen=True)
class SyncState:
    # "queued", "started", ..., or None if no sync is waiting or running
    status: str | None
    error: str | None

    @property
    def active(self) -> bool:
        return self.status is not None


def sync_stack(stack_id: int) -> None:
    """Background job: save a stack's latest commits and checks from GitHub"""
    stack = db.session.scalar(Stack.active().where(Stack.id == stack_id))
    # The stack may have been deleted (archived) before the job ran
    if stack is None:
        return
    try:
        sync_commits(stack, GitHubRepo.for_stack(client_for_server(), stack))
    except (GithubException, GitHubError) as exc:
        # Save a readable message for the page, then fail the job as usual
        job = get_current_job()
        if job is not None:
            job.meta["error"] = _error_message(exc)
            job.save_meta()
        raise


def enqueue_sync(stack_id: int) -> None:
    """Queue a sync for the stack, unless one is already waiting or running"""
    job_id = _job_id(stack_id)
    existing = job_queue.queue.fetch_job(job_id)
    if existing is not None:
        if existing.get_status() in ACTIVE_STATUSES:
            return
        # A failed job keeps its id; remove it so the id is free again
        existing.delete()
    try:
        job_queue.queue.enqueue(
            sync_stack,
            stack_id,
            job_id=job_id,
            # Fails instead of adding a second job if another request just queued one
            unique=True,
            # Finished jobs are deleted right away; failed ones stay a day to show the error
            result_ttl=0,
            failure_ttl=24 * 60 * 60,
        )
    except DuplicateJobError:
        # Another request queued it first
        pass


def sync_state(stack_id: int) -> SyncState:
    job = job_queue.queue.fetch_job(_job_id(stack_id))
    if job is None:
        return SyncState(status=None, error=None)
    status = job.get_status()
    if status in ACTIVE_STATUSES:
        return SyncState(status=status.value, error=None)
    if status == JobStatus.FAILED:
        return SyncState(status=None, error=job.meta.get("error", "The last sync failed"))
    return SyncState(status=None, error=None)


def _job_id(stack_id: int) -> str:
    # One id per stack, so a stack never has two syncs at once
    return f"sync-stack-{stack_id}"


def _error_message(exc: Exception) -> str:
    if isinstance(exc, GithubException):
        message = exc.data.get("message") if isinstance(exc.data, dict) else "unknown error"
        return f"Could not sync commits from GitHub ({exc.status}): {message}"
    return f"Could not sync commits from GitHub: {exc}"
