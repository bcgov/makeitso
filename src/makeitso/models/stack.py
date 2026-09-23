from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from makeitso import db
from datetime import datetime

class Stack(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    repository: so.Mapped[str] = so.mapped_column(comment="The repository that this stack deploys from")
    branch: so.Mapped[str] = so.mapped_column(comment="The branch that this stack deploys from")
    name: so.Mapped[str] = so.mapped_column(comment="The name of this stack")
    environment: so.Mapped[str] = so.mapped_column(comment="The environment that this stack should deploy to")
    locked: so.Mapped[bool] = so.mapped_column(default=False, comment="Boolean value indicates whether this stack is locked and should not deploy.")
    lock_reason: so.Mapped[Optional[str]] = so.mapped_column(comment="The reason this branch was locked")
    continuous_deploy: so.Mapped[bool] = so.mapped_column(default=False, comment="Boolean value indicates whether this stack should automatically deploy to the target")
    archived_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), comment="The datetime that this stack was archived. If this is null then the stack is active.")
    ## relationships
    stack_env_vars: so.Mapped[List["StackEnvVar"]] = so.relationship(back_populates="stack")
    commits: so.Mapped[List["Commit"]] = so.relationship(back_populates="stack")
