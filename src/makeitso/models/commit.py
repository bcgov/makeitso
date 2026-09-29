from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.extensions import db
from makeitso.github import overall_state

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.commit_status import CommitStatus
    from makeitso.models.stack import Stack


class Commit(db.Model):
    __table_args__ = (sa.UniqueConstraint("stack_id", "commit_sha", name="uq_commit_stack_sha"),)

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    stack_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("stack.id"))
    commit_sha: so.Mapped[str] = so.mapped_column(comment="The sha of the commit")
    commit_message: so.Mapped[str] = so.mapped_column(comment="The commit message from github")
    pull_request_number: so.Mapped[int | None] = so.mapped_column(
        comment="The pull request number that this commit relates to in git"
    )
    is_latest_deployed: so.Mapped[bool] = so.mapped_column(
        default=False,
        comment="Boolean value indicates if this is the commit that was last successfully deployed",
    )
    url: so.Mapped[str] = so.mapped_column(comment="The url of the commit on github")
    committed_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), comment="The datetime that the commit was committed"
    )
    author_name: so.Mapped[str] = so.mapped_column(comment="The git author name of the commit")
    author_login: so.Mapped[str | None] = so.mapped_column(
        comment="The github login of the author, if linked to a github account"
    )
    author_avatar_url: so.Mapped[str | None] = so.mapped_column(
        comment="The github avatar url of the author"
    )
    author_url: so.Mapped[str | None] = so.mapped_column(
        comment="The github profile url of the author"
    )
    ## relationships
    stack: so.Mapped[Stack] = so.relationship(back_populates="commits")
    commit_statuses: so.Mapped[list[CommitStatus]] = so.relationship(
        back_populates="commit", cascade="all, delete-orphan"
    )

    @property
    def short_sha(self) -> str:
        return self.commit_sha[:7]

    @property
    def checks_state(self) -> str | None:
        return overall_state(status.state for status in self.commit_statuses)
