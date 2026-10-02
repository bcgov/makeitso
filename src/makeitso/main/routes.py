from flask import Blueprint, render_template, session

from makeitso.deploys.queries import current_deploy, last_successful_deploy, previous_deploys
from makeitso.extensions import db
from makeitso.models.stack import Stack

# A blueprint groups related routes; create_app() registers it on the app.
bp = Blueprint("main", __name__)


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}


# Public so logging out lands here instead of bouncing straight back through GitHub login
@bp.get("/")
def index():
    # Logged-out users only see the login button, so skip the queries
    if not session.get("user"):
        return render_template("main/index.html")

    stacks = db.session.scalars(Stack.active().order_by(Stack.repository, Stack.environment)).all()
    # Each stack's state for the list: a running deploy, the latest finished one, and what's live
    states = {
        stack.id: {
            "running": current_deploy(stack.id),
            "latest": next(iter(previous_deploys(stack.id, limit=1)), None),
            "live": last_successful_deploy(stack.id),
        }
        for stack in stacks
    }
    return render_template("main/index.html", stacks=stacks, states=states)
