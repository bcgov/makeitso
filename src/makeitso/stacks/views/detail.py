from flask import redirect, render_template, request, url_for
from flask.views import MethodView

from makeitso.auth.decorators import requires_auth
from makeitso.deploys.helpers import emergency_mode
from makeitso.deploys.queries import (
    commits_between,
    current_deploy,
    last_successful_deploy,
    previous_deploys,
)
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy, DeployStatus
from makeitso.models.stack import Stack
from makeitso.stacks.tasks import enqueue_sync, sync_state


class StackDetailView(MethodView):
    @requires_auth
    def get(self, stack_id: int):
        stack = Stack.active_or_404(stack_id)
        return render_template("stacks/detail.html", **_commits_context(stack))

    @requires_auth
    def post(self, stack_id: int):
        """Queue a sync; the worker loads the commits from GitHub"""
        stack = Stack.active_or_404(stack_id)
        enqueue_sync(stack.id)
        # HTMX swaps in the list, which polls until the sync is done
        if request.headers.get("HX-Request"):
            return render_template("stacks/_commits.html", **_commits_context(stack))
        # Without JavaScript the form posts normally, so reload the page
        return redirect(url_for("stacks.detail", stack_id=stack.id))


class StackCommitsView(MethodView):
    """The commit list on its own, polled by HTMX while a sync or a deploy runs"""

    @requires_auth
    def get(self, stack_id: int):
        stack = Stack.active_or_404(stack_id)
        return render_template("stacks/_commits.html", **_commits_context(stack))


def _commits_context(stack: Stack) -> dict:
    return {
        "stack": stack,
        "sync": sync_state(stack.id),
        "emergency": emergency_mode(),
        **_sections(stack),
    }


def _sections(stack: Stack) -> dict:
    """The three sections of the stack page: currently deploying, undeployed, previous deploys"""
    current = current_deploy(stack.id)
    last = last_successful_deploy(stack.id)
    last_commit = last.commit if last else None
    previous = previous_deploys(stack.id)
    deploying: list[Commit] = []
    if current is not None:
        # A redeploy of an older commit has no range, so show just its commit
        deploying = commits_between(stack.id, last_commit, current.commit) or [current.commit]
    return {
        "current_deploy": current,
        "deploying_commits": deploying,
        "undeployed_commits": commits_between(stack.id, current.commit if current else last_commit),
        "previous_deploys": previous,
        # Ids of the deploys that get a Redeploy/Retry button
        "redeployable": {d.id for d in previous if _can_redeploy(d, last)},
    }


def _can_redeploy(deploy: Deploy, last: Deploy | None) -> bool:
    """For a finished deploy: redeploy only what's deployed now; retry any failed
    deploy since then"""
    if deploy.status is DeployStatus.SUCCEEDED:
        return last is not None and deploy.id == last.id
    return last is None or deploy.started_at > last.started_at
