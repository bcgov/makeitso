import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.extensions import db
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy, DeployStatus


def current_deploy(stack_id: int) -> Deploy | None:
    return db.session.scalar(
        sa.select(Deploy).where(
            Deploy.stack_id == stack_id, Deploy.status == DeployStatus.IN_PROGRESS
        )
    )


def last_successful_deploy(stack_id: int) -> Deploy | None:
    """The deploy that's live now; its commit is the deployed commit"""
    return db.session.scalar(
        sa.select(Deploy)
        .where(Deploy.stack_id == stack_id, Deploy.status == DeployStatus.SUCCEEDED)
        .order_by(Deploy.started_at.desc())
    )


def previous_deploys(stack_id: int, limit: int = 10) -> list[Deploy]:
    """Finished deploys, newest first"""
    return list(
        db.session.scalars(
            sa.select(Deploy)
            .where(Deploy.stack_id == stack_id, Deploy.status != DeployStatus.IN_PROGRESS)
            .order_by(Deploy.started_at.desc())
            .limit(limit)
            .options(so.selectinload(Deploy.commit))
        )
    )


def commits_between(
    stack_id: int, after: Commit | None, until: Commit | None = None
) -> list[Commit]:
    """Commits newer than `after`, up to and including `until`, newest first.
    Ids follow git order (the sync stores commits oldest first), so they're compared, not dates"""
    query = (
        sa.select(Commit)
        .where(Commit.stack_id == stack_id)
        .order_by(Commit.id.desc())
        # Load every commit's checks in one extra query, not one query per commit
        .options(so.selectinload(Commit.commit_statuses))
    )
    if after is not None:
        query = query.where(Commit.id > after.id)
    if until is not None:
        query = query.where(Commit.id <= until.id)
    return list(db.session.scalars(query))
