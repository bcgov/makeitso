from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso import db

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.stack import Stack


class StackEnvVar(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    stack_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("stack.id"), comment="The foreign key to the stack table"
    )
    key: so.Mapped[str] = so.mapped_column(comment="The key portion of the environment variable")
    value: so.Mapped[str] = so.mapped_column(
        comment="The value portion of the environment variable"
    )
    # relationships
    stack: so.Mapped[Stack] = so.relationship(back_populates="stack_env_vars")
