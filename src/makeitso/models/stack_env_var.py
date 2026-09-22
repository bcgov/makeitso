import sqlalchemy as sa
import sqlalchemy.orm as so
from makeitso import db

class StackEnvVar(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    stack_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("stack.id"))
    key: so.Mapped[str]
    value: so.Mapped[str]
    # relationships
    stack: so.Mapped["Stack"] = so.relationship(back_populates="stack_env_vars")
