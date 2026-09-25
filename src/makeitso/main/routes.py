from flask import Blueprint, render_template, request
from redis.exceptions import ConnectionError as RedisConnectionError
from rq.exceptions import NoSuchJobError
from rq.job import Job

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import job_queue, db
from makeitso.main.jobs import run_deployment
from makeitso.models.stack import Stack

# A blueprint groups related routes; create_app() registers it on the app.
bp = Blueprint("main", __name__)


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}


# Public so logging out lands here instead of bouncing straight back through GitHub login
@bp.get("/")
def index():
    stacks = db.session.query(Stack).all()
    return render_template("main/index.html", stacks=stacks)


# Queues the example job and returns its status fragment right away
@bp.post("/partials/example-job")
@requires_auth
def enqueue_example_job():
    commit_sha = request.form.get("commit_sha")
    stack = db.session.query(Stack).filter_by(repository="makeitso").first()

    try:
        job = Job.fetch(commit_sha, connection=job_queue.queue.connection)
    except NoSuchJobError:
        job = job_queue.queue.enqueue(
            run_deployment, commit_sha, stack, job_id=commit_sha
        )
    except RedisConnectionError:
        return render_template("main/_job_status.html", job=None)
    return render_template("main/_job_status.html", job=job)


# Polled by HTMX to refresh the job's status until it finishes
@bp.get("/partials/example-job/<job_id>")
@requires_auth
def example_job_status(job_id: str):
    # Load the job's latest state from Redis by its ID
    job = Job.fetch(job_id, connection=job_queue.queue.connection)
    return render_template("main/_job_status.html", job=job)
