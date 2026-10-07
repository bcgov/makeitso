from flask import Blueprint, render_template

from makeitso.auth.decorators import requires_auth
from makeitso.monitor.monitor import get_queues_data

bp = Blueprint("monitor", __name__)


@bp.get("/")
@requires_auth
def index():
    return render_template("monitor/index.html", queue_data=get_queues_data())


@bp.get("/queues-data")
@requires_auth
def queues_partial():
    return render_template("monitor/_queues.html", queue_data=get_queues_data())
