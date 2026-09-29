from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.extensions import db

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.commit import Commit


class CommitStatus(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    commit_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("commit.id"))
    name: so.Mapped[str] = so.mapped_column(comment="The name of the check pulled from github")
    state: so.Mapped[str] = so.mapped_column(
        comment="The conclusion of the check if finished (success, failure, ...), else its status"
    )
    html_url: so.Mapped[str] = so.mapped_column(comment="The url to the source of the check")
    ## relationships
    commit: so.Mapped[Commit] = so.relationship(back_populates="commit_statuses")
