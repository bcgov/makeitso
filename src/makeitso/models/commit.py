from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.extensions import db

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.commit_status import CommitStatus
    from makeitso.models.stack import Stack


class Commit(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    stack_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("stack.id"))
    commit_sha: so.Mapped[str] = so.mapped_column(comment="The sha of the commit")
    commit_message: so.Mapped[str] = so.mapped_column(comment="The commit message from github")
    pull_request_number: so.Mapped[int] = so.mapped_column(
        comment="The pull request number that this commit relates to in git"
    )
    is_latest_deployed: so.Mapped[bool] = so.mapped_column(
        comment="Boolean value indicates if this is the commit that was last successfully deployed"
    )
    ## relationships
    stack: so.Mapped[Stack] = so.relationship(back_populates="commits")
    commit_statuses: so.Mapped[list[CommitStatus]] = so.relationship(back_populates="commit")
