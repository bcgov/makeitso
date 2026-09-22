from flask import Blueprint, render_template

# A blueprint groups related routes; create_app() registers it on the app.
bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("main/index.html")
