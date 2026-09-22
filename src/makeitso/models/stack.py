from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from makeitso import db
from datetime import datetime

class Stack(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    repository: so.Mapped[str]
    branch: so.Mapped[str]
    name: so.Mapped[str]
    environment: so.Mapped[str]
    locked: so.Mapped[bool] = so.mapped_column(default=False)
    lock_reason: so.Mapped[Optional[str]]
    continuous_deploy: so.Mapped[bool] = so.mapped_column(default=False)
    archived_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True))
    ## relationships
    stack_env_vars: so.Mapped[List["StackEnvVar"]] = so.relationship(back_populates="stack")