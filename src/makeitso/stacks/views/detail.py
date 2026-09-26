import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import redirect, render_template, request, url_for
from flask.views import MethodView

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import db
from makeitso.models.commit import Commit
from makeitso.models.stack import Stack
from makeitso.stacks.tasks import enqueue_sync, sync_state


class StackDetailView(MethodView):
    @requires_auth
    def get(self, stack_id: int):
        stack = db.first_or_404(Stack.active().where(Stack.id == stack_id))
        return render_template("stacks/detail.html", **_commits_context(stack))

    @requires_auth
    def post(self, stack_id: int):
        """Queue a sync; the worker loads the commits from GitHub"""
        stack = db.first_or_404(Stack.active().where(Stack.id == stack_id))
        enqueue_sync(stack.id)
        # HTMX swaps in the list, which polls until the sync is done
        if request.headers.get("HX-Request"):
            return render_template("stacks/_commits.html", **_commits_context(stack))
        # Without JavaScript the form posts normally, so reload the page
        return redirect(url_for("stacks.detail", stack_id=stack.id))


class StackCommitsView(MethodView):
    """The commit list on its own, polled by HTMX while a sync runs"""

    @requires_auth
    def get(self, stack_id: int):
        stack = db.first_or_404(Stack.active().where(Stack.id == stack_id))
        return render_template("stacks/_commits.html", **_commits_context(stack))


def _commits_context(stack: Stack) -> dict:
    commits = db.session.scalars(
        sa.select(Commit)
        .where(Commit.stack_id == stack.id)
        .order_by(Commit.committed_at.desc())
        # Load every commit's checks in one extra query, not one query per commit
        .options(so.selectinload(Commit.commit_statuses))
    )
    return {"stack": stack, "commits": list(commits), "sync": sync_state(stack.id)}
