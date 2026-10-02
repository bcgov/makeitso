from datetime import datetime
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.extensions import db

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.commit import Commit
    from makeitso.models.stack_env_var import StackEnvVar

# Failed syncs in a row before background syncs skip a stack; pressing Sync still works
MAX_SYNC_FAILURES = 5


class Stack(db.Model):
    __table_args__ = (
        # Only one active stack per repo and environment; archived (deleted) ones don't count,
        # so a deleted stack can be created again
        sa.Index(
            "uq_stack_active_repo_environment",
            "organization",
            "repository",
            "environment",
            unique=True,
            postgresql_where=sa.text("archived_at IS NULL"),
        ),
    )

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    organization: so.Mapped[str] = so.mapped_column(
        comment="The organization that this stack belongs to"
    )
    repository: so.Mapped[str] = so.mapped_column(
        comment="The repository that this stack deploys from"
    )
    branch: so.Mapped[str] = so.mapped_column(comment="The branch that this stack deploys from")
    name: so.Mapped[str] = so.mapped_column(comment="The name of this stack")
    environment: so.Mapped[str] = so.mapped_column(
        comment="The environment that this stack should deploy to"
    )
    locked: so.Mapped[bool] = so.mapped_column(
        default=False,
        comment="Boolean value indicates whether this stack is locked and should not deploy.",
    )
    lock_reason: so.Mapped[str | None] = so.mapped_column(
        comment="The reason this branch was locked"
    )
    continuous_deploy: so.Mapped[bool] = so.mapped_column(
        default=False,
        comment=(
            "Boolean value indicates whether this stack should automatically deploy to the target"
        ),
    )
    allow_failures: so.Mapped[list[str]] = so.mapped_column(
        sa.JSON,
        default=list,
        server_default="[]",
        comment="Check names from engage.yaml's ci.allow_failures at the branch head, set on sync",
    )
    synced_at: so.Mapped[datetime | None] = so.mapped_column(
        sa.DateTime(timezone=True),
        comment="When the last sync with GitHub succeeded; null if none has",
    )
    sync_failures: so.Mapped[int] = so.mapped_column(
        default=0,
        server_default="0",
        comment="Syncs that failed in a row; a successful sync resets it",
    )
    archived_at: so.Mapped[datetime | None] = so.mapped_column(
        sa.DateTime(timezone=True),
        comment=(
            "The datetime that this stack was archived. If this is null then the stack is active."
        ),
    )
    ## relationships
    stack_env_vars: so.Mapped[list[StackEnvVar]] = so.relationship(back_populates="stack")
    commits: so.Mapped[list[Commit]] = so.relationship(back_populates="stack")

    @property
    def sync_paused(self) -> bool:
        """Background syncs have given up on this stack until a sync succeeds"""
        return self.sync_failures >= MAX_SYNC_FAILURES

    @classmethod
    def active(cls) -> sa.Select[Self]:
        """Select stacks that aren't archived; deleting a stack archives it"""
        return sa.select(cls).where(cls.archived_at.is_(None))

    @classmethod
    def active_or_404(cls, stack_id: int) -> Self:
        """The stack for a page; a 404 if it doesn't exist or was deleted"""
        return db.first_or_404(cls.active().where(cls.id == stack_id))
