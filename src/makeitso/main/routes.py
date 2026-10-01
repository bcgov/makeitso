from flask import Blueprint, render_template

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
    stacks = db.session.scalars(Stack.active()).all()
    return render_template("main/index.html", stacks=stacks)
