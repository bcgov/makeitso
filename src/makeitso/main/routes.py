from datetime import UTC, datetime

from flask import Blueprint, render_template
from redis.exceptions import ConnectionError as RedisConnectionError
from rq.job import Job

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import job_queue
from makeitso.main.jobs import add_numbers

# A blueprint groups related routes; create_app() registers it on the app.
bp = Blueprint("main", __name__)


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}


@bp.get("/")
def index():
    return render_template("main/index.html")


@bp.get("/partials/server-time")
@requires_auth
def server_time():
    return render_template("main/_server_time.html", now=datetime.now(UTC))


# Queues the example job and returns its status fragment right away
@bp.post("/partials/example-job")
def enqueue_example_job():
    try:
        job = job_queue.queue.enqueue(add_numbers, 2, 3)
    except RedisConnectionError:
        return render_template("main/_job_status.html", job=None)
    return render_template("main/_job_status.html", job=job)


# Polled by HTMX to refresh the job's status until it finishes
@bp.get("/partials/example-job/<job_id>")
def example_job_status(job_id: str):
    # Load the job's latest state from Redis by its ID
    job = Job.fetch(job_id, connection=job_queue.queue.connection)
    return render_template("main/_job_status.html", job=job)
