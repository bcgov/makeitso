from datetime import UTC, datetime

from flask import flash, redirect, url_for
from flask.views import MethodView

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import db
from makeitso.models.stack import Stack


class DeleteStackView(MethodView):
    @requires_auth
    def post(self, stack_id: int):
        """Delete a stack by archiving it, so its history stays in the database"""
        stack = db.first_or_404(Stack.active().where(Stack.id == stack_id))
        stack.archived_at = datetime.now(UTC)
        db.session.commit()
        flash(
            f"Deleted stack {stack.organization}/{stack.repository} ({stack.environment})",
            "success",
        )
        return redirect(url_for("main.index"))
