from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso import db

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.commit import Commit
    from makeitso.models.stack_env_var import StackEnvVar


class Stack(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
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
    archived_at: so.Mapped[datetime | None] = so.mapped_column(
        sa.DateTime(timezone=True),
        comment=(
            "The datetime that this stack was archived. If this is null then the stack is active."
        ),
    )
    ## relationships
    stack_env_vars: so.Mapped[list[StackEnvVar]] = so.relationship(back_populates="stack")
    commits: so.Mapped[list[Commit]] = so.relationship(back_populates="stack")
