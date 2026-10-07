from flask import Blueprint, current_app, render_template

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import job_queue
from makeitso.monitor.monitor import get_queue_data

bp = Blueprint("monitor", __name__)


@bp.get("/")
@requires_auth
def index():

    queue_data = [
        get_queue_data(job_queue.syncs),
        get_queue_data(job_queue.deploys),
    ]

    return render_template("monitor/index.html", queue_data=queue_data)
