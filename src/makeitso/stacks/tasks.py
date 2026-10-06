from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from flask import current_app
from github import GithubException
from rq import get_current_job
from rq.exceptions import DuplicateJobError
from rq.job import Dependency, JobStatus

from makeitso.extensions import db, job_queue
from makeitso.github import GitHubError, GitHubRepo, client_for_server
from makeitso.models.stack import MAX_SYNC_FAILURES, Stack
from makeitso.stacks.continuous_deployment import check_continuous_deployment
from makeitso.stacks.sync import save_allow_failures, sync_commits

# Job states that mean a sync is waiting for a worker or running
ACTIVE_STATUSES = {
    JobStatus.QUEUED,
    JobStatus.STARTED,
    JobStatus.DEFERRED,
    JobStatus.SCHEDULED,
}
# A stack not synced for this long gets a background sync
SYNC_STALE_AFTER = timedelta(minutes=30)


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
    current_app.logger.info("Worker: syncing stack %s", stack)
    try:
        repo = GitHubRepo.for_stack(client_for_server(), stack)
        sync_commits(stack, repo)
        save_allow_failures(stack, repo)
    except Exception as exc:
        # Count it, so background syncs stop retrying a stack that keeps failing
        db.session.rollback()
        stack.sync_failures += 1
        db.session.commit()
        if isinstance(exc, (GithubException, GitHubError)):
            # Save a readable message for the page, then fail the job as usual
            job = get_current_job()
            if job is not None:
                job.meta["error"] = _error_message(exc)
                job.save_meta()
        raise
    stack.synced_at = datetime.now(UTC)
    stack.sync_failures = 0
    db.session.commit()


def enqueue_sync(stack_id: int, followup: bool = False) -> None:
    """Queue a sync for the stack, unless one is already waiting or running. With followup, a
    running sync gets one more queued after it (for pushes that may have landed mid-sync)
    """
    job_id = _job_id(stack_id)
    running = job_queue.syncs.fetch_job(job_id)
    if followup and running is not None and running.get_status() == JobStatus.STARTED:
        # The running sync may have read the old head, so queue one more after it, even if it fails
        after = Dependency(jobs=[running], allow_failure=True)
        _enqueue(stack_id, f"{job_id}-followup", depends_on=after)
        return
    _enqueue(stack_id, job_id)


def _enqueue(
    stack_id: int,
    job_id: str,
    depends_on: Dependency | None = None,
) -> None:
    existing = job_queue.syncs.fetch_job(job_id)
    if existing is not None:
        if existing.get_status() in ACTIVE_STATUSES:
            return
        # A failed job keeps its id; remove it so the id is free again
        existing.delete()
    try:
        sync_job = job_queue.syncs.enqueue(
            sync_stack,
            stack_id,
            job_id=job_id,
            depends_on=depends_on,
            # Fails instead of adding a second job if another request just queued one. RQ
            # doesn't allow it with depends_on; a racing follow-up just reuses the same id
            unique=depends_on is None,
            # Finished jobs are deleted right away; failed ones stay a day to show the error
            result_ttl=0,
            failure_ttl=24 * 60 * 60,
        )
        job_queue.syncs.enqueue(
            check_continuous_deployment,
            stack_id,
            job_id=f"{job_id}-cd",
            depends_on=sync_job,
            result_ttl=0,
            failure_ttl=24 * 60 * 60,
        )
    except DuplicateJobError:
        # Another request queued it first
        pass


def enqueue_stale_syncs() -> int:
    """Queue a sync for each stack not synced in SYNC_STALE_AFTER, skipping stacks whose syncs
    keep failing. Run by the stack-sync CronJob; returns how many stacks were picked"""
    cutoff = datetime.now(UTC) - SYNC_STALE_AFTER
    stacks = db.session.scalars(
        Stack.active().where(
            sa.or_(Stack.synced_at.is_(None), Stack.synced_at < cutoff),
            Stack.sync_failures < MAX_SYNC_FAILURES,
        )
    ).all()
    for stack in stacks:
        enqueue_sync(stack.id)
    return len(stacks)


def sync_state(stack_id: int) -> SyncState:
    job = job_queue.syncs.fetch_job(_job_id(stack_id))
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
