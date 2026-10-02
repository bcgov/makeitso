import hashlib
import hmac
import json

import sqlalchemy as sa
from flask import Blueprint, abort, current_app, request

from makeitso.extensions import csrf, db
from makeitso.models.stack import Stack
from makeitso.stacks.tasks import enqueue_sync
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy
from makeitso.deploys.tasks import start_deploy
from makeitso.github import GitHubRepo, client_for_current_user
from makeitso.engage.loader import load_config
from makeitso.deploys.helpers import deploy_blockers

bp = Blueprint("webhooks", __name__)


def verify_signature(payload, signature):
    """Verify that the payload matches the GitHub signature."""
    secret = current_app.config["GITHUB_WEBHOOK_SECRET"]
    if not secret or not signature:
        return False
    sha_name, _, signature_hex = signature.partition("=")
    if sha_name != "sha256":
        return False

    # Calculate local signature
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature_hex)
        

def handle_push_event(payload):
    ref = payload.get("ref", "")  # e.g., 'refs/heads/main'
    # Tag pushes and branch deletions don't need a sync
    if not ref.startswith("refs/heads/") or payload.get("deleted"):
        return
    repo_full_name = payload.get("repository", {}).get("full_name")
    branch = ref.removeprefix("refs/heads/")
    org, _, repo = repo_full_name.partition("/")
    matching_stacks = db.session.scalars(
        sa.select(Stack).where(
            Stack.organization == org, Stack.repository == repo, Stack.branch == branch
        )
    )
    for s in matching_stacks:
        current_app.logger.info("Push to %s/%s, syncing stack %s", repo_full_name, branch, s.id)
        enqueue_sync(s.id, followup=True)
        # Trigger Continuous Deploy
        if s.continuous_deploy:
            last_deploy = db.session.scalar(sa.select(Deploy).where(Deploy.stack_id == s.id, Deploy.status == "SUCCEEDED").order_by(Deploy.id.desc()).limit(1))
            latest_commit = db.session.scalar(sa.select(Commit).where(Commit.stack_id == s.id).order_by(Commit.id.desc()).limit(1))
            if last_deploy:
                if last_deploy.commit_id == latest_commit.id:
                    # Do not deploy: Commit already deployed
                    return
                if last_deploy.status == 'IN_PROGRESS':
                    # Do not deploy: A deploy is in progress
                    return
            repo = GitHubRepo.for_stack(client_for_current_user(), s)
            config = load_config(repo, latest_commit.commit_sha, s.environment)
            allowed = config.ci.allow_failures
            blockers = deploy_blockers(s, latest_commit, allowed)
            if blockers:
                # Do not Deploy: Deploy is blocked
                return
            start_deploy(
                s,
                latest_commit,
                config.deploy.timeout
            )


@bp.route("/webhook-receiver", methods=["POST"])
@csrf.exempt
def receive_github_webhook():
    # Get the signature from headers
    signature = request.headers.get("X-Hub-Signature-256")
    # Verify the payload authenticity
    if not verify_signature(request.data, signature):
        abort(403, "Invalid signature")
    # Read the type of GitHub event (e.g., 'push', 'pull_request')
    event_type = request.headers.get("X-GitHub-Event")
    # Extract data from the payload
    payload = request.json

    # Handle Push Events
    if event_type == "push":
        handle_push_event(payload)

    return json.dumps({"success": True}), 200
