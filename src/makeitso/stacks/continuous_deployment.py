from flask import current_app
from redis import client
import sqlalchemy as sa
from makeitso.deploys.helpers import deploy_blockers
from makeitso.deploys.tasks import start_deploy
from makeitso.engage.loader import load_config
from makeitso.extensions import db

from makeitso.github import github_client, GitHubRepo
from makeitso.github.tokens import client_for_server
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy
from makeitso.models.stack import Stack


def check_continuous_deployment(stack_id: int):

    stack = db.session.get(Stack, stack_id)
    current_app.logger.info(
        "Worker: checking continuous deployment for stack %s", stack
    )

    if not stack.continuous_deploy:
        current_app.logger.info("Continuous deployment is disabled for stack %s", stack)
        return

    if stack.locked:
        current_app.logger.info("Stack %s is locked: %s", stack, stack.lock_reason)
        return

    last_deploy = db.session.scalar(
        sa.select(Deploy)
        .where(Deploy.stack_id == stack_id)
        .order_by(Deploy.id.desc())
        .limit(1)
    )
    latest_commit = db.session.scalar(
        sa.select(Commit)
        .where(Commit.stack_id == stack_id)
        .order_by(Commit.id.desc())
        .limit(1)
    )
    if last_deploy:
        if last_deploy.commit_id == latest_commit.id:
            # Do not deploy: Commit already deployed
            return
        if last_deploy.status == "IN_PROGRESS":
            # Do not deploy: A deploy is in progress
            return

    repo = GitHubRepo.for_stack(client_for_server(), stack)
    config, _ = load_config(repo, latest_commit.commit_sha, stack.environment)
    allowed = config.ci.allow_failures
    blockers = deploy_blockers(stack, latest_commit, allowed)
    if blockers:
        # Do not Deploy: Deploy is blocked
        current_app.logger.info("Continuous deployment blocked for stack %s", stack)
        return
    if latest_commit.checks_state(allowed) == "success":
        current_app.logger.info("Continuous deployment triggered for stack %s", stack)
        start_deploy(stack, latest_commit, config.deploy.timeout, "Continuous Deploy")
