import hashlib
import hmac
import json

from flask import Blueprint, abort, current_app, request

from makeitso.extensions import csrf, db
from makeitso.models.stack import Stack
from makeitso.stacks.tasks import enqueue_sync

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
    sync_stacks(payload, ref.removeprefix("refs/heads/"), "Push")


def handle_completed_check_suite(payload):
    # Could be removed once a handle_completed_check_run() updates single check statuses
    branch = payload.get("check_suite", {}).get("head_branch")
    sync_stacks(payload, branch, "Check suite completed")


def sync_stacks(payload, branch, reason):
    """Queue a sync for every active stack on this repo and branch"""
    repo_full_name = payload.get("repository", {}).get("full_name")
    org, _, repo = repo_full_name.partition("/")
    matching_stacks = db.session.scalars(
        Stack.active().where(
            Stack.organization == org, Stack.repository == repo, Stack.branch == branch
        )
    )
    for s in matching_stacks:
        current_app.logger.info(
            "%s on %s/%s, syncing stack %s", reason, repo_full_name, branch, s.id
        )
        enqueue_sync(s.id, followup=True)


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

    if event_type == "check_suite":
        status = payload.get("check_suite", {}).get("status")
        current_app.logger.info("Received check_suite webhook with status %s", status)
        if status == "completed":
            handle_completed_check_suite(payload)

    return json.dumps({"success": True}), 200
