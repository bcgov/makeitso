from typing import Literal

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import flash, redirect, render_template, request, session, url_for
from flask.views import MethodView, View
from sqlalchemy.exc import IntegrityError

from makeitso.auth.decorators import requires_auth
from makeitso.deploys import tasks
from makeitso.deploys.helpers import checks_failed, deploy_blockers, emergency_mode
from makeitso.deploys.queries import (
    commits_between,
    current_deploy,
    last_successful_deploy,
)
from makeitso.deploys.tasks import fail_if_lost, start_deploy
from makeitso.engage import EngageConfig, EngageConfigError
from makeitso.engage.loader import load_config
from makeitso.extensions import db
from makeitso.github import GitHubRepo, client_for_current_user
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy, DeployStatus
from makeitso.models.stack import Stack


def _get_deploy(stack_id: int, deploy_id: int) -> Deploy:
    deploy = db.first_or_404(
        sa.select(Deploy)
        .options(so.selectinload(Deploy.commit), so.selectinload(Deploy.stack))
        .where(Deploy.id == deploy_id, Deploy.stack_id == stack_id)
    )
    fail_if_lost(deploy)
    return deploy


def _stack_and_commit(stack_id: int, commit_sha: str) -> tuple[Stack, Commit]:
    stack = Stack.active_or_404(stack_id)
    commit = db.first_or_404(
        sa.select(Commit).where(Commit.stack_id == stack.id, Commit.commit_sha == commit_sha)
    )
    return stack, commit


def _show_running(stack: Stack):
    """Send the user to the deploy that's already running on the stack"""
    flash("A deploy is already running on this stack", "warning")
    running = current_deploy(stack.id)
    if running is None:
        return redirect(url_for("stacks.detail", stack_id=stack.id))
    return redirect(url_for("stacks.deploys.detail", stack_id=stack.id, deploy_id=running.id))


def _config(stack: Stack, commit: Commit) -> tuple[EngageConfig, str | None]:
    """The stack's engage.yaml at the commit, read through the GitHub API (nothing is checked out
    yet), and the file it came from"""
    repo = GitHubRepo.for_stack(client_for_current_user(), stack)
    return load_config(repo, commit.commit_sha, stack.environment)


class NewDeployView(MethodView):
    """The deploy page for a commit; Redeploy and Retry link here too"""

    @requires_auth
    def get(self, stack_id: int, commit_sha: str):
        stack, commit = _stack_and_commit(stack_id, commit_sha)
        last = last_successful_deploy(stack.id)
        last_commit = last.commit if last else None
        emergency = emergency_mode()
        # An invalid engage.yaml is shown on the page and blocks the deploy
        try:
            (config, config_file), config_error = _config(stack, commit), None
        except EngageConfigError as exc:
            config, config_file, config_error = EngageConfig(), None, str(exc)
        return render_template(
            "deploys/new.html",
            stack=stack,
            commit=commit,
            # The first deploy of a stack has nothing before it, so the range is just this commit
            since=last_commit or commit,
            commits=commits_between(stack.id, last_commit, commit),
            running=current_deploy(stack.id),
            config=config,
            config_file=config_file,
            config_error=config_error,
            blockers=deploy_blockers(stack, commit, config.ci.allow_failures, emergency),
            emergency=emergency,
            bypassing=emergency and checks_failed(commit, config.ci.allow_failures),
        )

    @requires_auth
    def post(self, stack_id: int, commit_sha: str):
        """Start the deploy unless something blocks it, then show its log"""
        stack, commit = _stack_and_commit(stack_id, commit_sha)
        retry = redirect(
            url_for(
                "stacks.deploys.new",
                stack_id=stack.id,
                commit_sha=commit.commit_sha,
                emergency=1 if emergency_mode() else None,
            )
        )
        if current_deploy(stack.id) is not None:
            return _show_running(stack)
        try:
            config, _ = _config(stack, commit)
        except EngageConfigError as exc:
            flash(str(exc), "danger")
            return retry
        # Every checklist item has to be ticked
        if len(request.form.getlist("checklist")) != len(config.review.checklist):
            flash("Tick every item on the checklist before deploying", "warning")
            return retry
        allowed = config.ci.allow_failures
        emergency = emergency_mode()
        blockers = deploy_blockers(stack, commit, allowed, emergency)
        if blockers:
            for reason in blockers:
                flash(reason, "warning")
            return retry
        # Only marked when emergency mode actually let failed checks through
        bypass = emergency and checks_failed(commit, allowed)
        try:
            deploy = start_deploy(
                stack,
                commit,
                config.deploy.timeout,
                session["user"]["login"],
                bypass=bypass,
            )
        except IntegrityError:
            # A double-click: the other request started a deploy between our check and the save,
            # and the one-running-deploy index refused this one
            db.session.rollback()
            return _show_running(stack)
        return redirect(url_for("stacks.deploys.detail", stack_id=stack.id, deploy_id=deploy.id))


class DeployView(MethodView):
    @requires_auth
    def get(self, stack_id: int, deploy_id: int):
        return render_template("deploys/detail.html", deploy=_get_deploy(stack_id, deploy_id))


class SignalView(View):
    methods = ["POST"]

    def __init__(self, signal: Literal["cancel", "interrupt"]):
        self.signal = signal

    def dispatch_request(self, stack_id: int, deploy_id: int):
        deploy = _get_deploy(stack_id, deploy_id)
        tasks.signal_job(deploy, self.signal)
        return redirect(url_for("stacks.deploys.detail", stack_id=stack_id, deploy_id=deploy_id))


class DeployLogView(MethodView):
    """Polled while a deploy runs: returns only the output added since `offset`"""

    @requires_auth
    def get(self, stack_id: int, deploy_id: int):
        deploy = _get_deploy(stack_id, deploy_id)
        offset = request.args.get("offset", 0, type=int)
        html = render_template(
            "deploys/_log_update.html", deploy=deploy, chunk=deploy.output[offset:]
        )
        # 286 tells HTMX to stop polling; the text is still added to the log
        return html, 200 if deploy.status is DeployStatus.IN_PROGRESS else 286


class DeployListView(MethodView):
    """Every deploy of a stack, newest first, a page at a time"""

    @requires_auth
    def get(self, stack_id: int):
        stack = Stack.active_or_404(stack_id)
        deploys = db.paginate(
            sa.select(Deploy)
            .where(Deploy.stack_id == stack.id)
            .order_by(Deploy.started_at.desc())
            .options(so.selectinload(Deploy.commit)),
            per_page=20,
        )
        return render_template("deploys/list.html", stack=stack, deploys=deploys)
