import sqlalchemy as sa
import sqlalchemy.orm as so
from makeitso import db

class CommitStatus(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    commit_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("commit.id"))
    name: so.Mapped[str] = so.mapped_column(comment="The name of the check pulled from github")
    conclusion: so.Mapped[str] = so.mapped_column(comment="The conclusion status of the check pulled from github")
    html_url: so.Mapped[str] = so.mapped_column(comment="The url to the source of the check")
    ## relationships
    commit: so.Mapped["Commit"] = so.relationship(back_populates="commit_statuses")