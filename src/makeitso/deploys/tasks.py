import os
import shutil
import signal
import subprocess
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from flask import current_app
from rq import Queue
from rq.job import Job, JobStatus

from makeitso.deploys.queries import last_successful_deploy
from makeitso.engage import EngageConfig, parse_config
from makeitso.engage.config import config_files
from makeitso.extensions import db, job_queue
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy, DeployStatus
from makeitso.models.stack import Stack

# Durations in this file use time.monotonic(), which can't jump when the system clock changes

# Seconds allowed for the checkout; the deploy script's own limit is deploy.timeout in engage.yaml
CHECKOUT_TIMEOUT = 2 * 60
# Seconds between saves of new output
SAVE_EVERY = 1
# After SIGTERM, seconds to wait before SIGKILL; long, since the script may be rolling back
DEPLOY_TIMEOUT = 1800
# A running job with no worker heartbeat for this long, lost its worker
HEARTBEAT_LIMIT = timedelta(minutes=2)


def _job_id(deploy_id: int) -> str:
    return f"deploy-{deploy_id}"


# --- Starting a deploy (web request) ---


def start_deploy(
    stack: Stack,
    commit: Commit,
    timeout: int,
    deployed_by: str | None,
    bypass: bool = False,
) -> Deploy:
    """Save a deploy and queue it for the worker. `timeout` is engage.yaml's deploy.timeout;
    `deployed_by` is a GitHub login (None for continuous deploys)"""
    last = last_successful_deploy(stack.id)
    deploy = Deploy(
        stack_id=stack.id,
        commit_id=commit.id,
        # Saved now, so the range stays the same after later deploys
        since_commit_id=last.commit_id if last else None,
        status=DeployStatus.IN_PROGRESS,
        output="",
        deployed_with_bypass=bypass,
        deployed_by=deployed_by,
    )
    db.session.add(deploy)
    db.session.commit()
    job_queue.queue.enqueue(
        run_deploy,
        deploy.id,
        job_id=_job_id(deploy.id),
        # The Deploy row keeps status and output, so the job isn't needed afterward
        result_ttl=0,
        # Our worst case (both steps, each with its grace) + 60s slack, so our timeouts fire first
        job_timeout=CHECKOUT_TIMEOUT + timeout + 2 * DEPLOY_TIMEOUT + 60,
    )
    return deploy


def fail_if_lost(deploy: Deploy) -> None:
    """A deploy whose job ended without finishing it (killed worker, RQ's stop or cancel) never
    records its result; record it here so the stack isn't blocked"""
    if deploy.status is not DeployStatus.IN_PROGRESS:
        return
    job = job_queue.queue.fetch_job(_job_id(deploy.id))
    status = job.get_status() if job is not None else None
    # Someone stopped it with RQ's own tools: that's an abort, not a failure
    if status in (JobStatus.STOPPED, JobStatus.CANCELED):
        _finish(deploy, DeployStatus.ABORTED, "\nThe job was stopped from RQ\n")
    elif job is None or status is JobStatus.FAILED or _worker_gone(job):
        _finish(
            deploy,
            DeployStatus.FAILED,
            "\nThe worker stopped before the deploy finished\n",
        )


def signal_job(deploy: Deploy, signal: Literal["cancel", "interrupt"]) -> None:
    """Ask a running deploy's watcher to stop it: cancel lets it clean up, interrupt kills it"""
    if deploy.status is not DeployStatus.IN_PROGRESS:
        raise ValueError("Cannot signal a deploy that is not running")

    job = job_queue.queue.fetch_job(_job_id(deploy.id))
    if job is None:
        raise ValueError("Cannot signal a deploy with no associated job")

    job.meta["signal"] = signal
    job.save_meta()


def requested_signal(deploy: Deploy) -> str | None:
    """The stop signal sent to a running deploy, if any"""
    if deploy.status is not DeployStatus.IN_PROGRESS:
        return None
    job = job_queue.queue.fetch_job(_job_id(deploy.id))
    return job.meta.get("signal") if job else None


def _finish(deploy: Deploy, status: DeployStatus, message: str) -> None:
    deploy.status = status
    deploy.ended_at = datetime.now(UTC)
    deploy.output += message
    db.session.commit()


def _worker_gone(job: Job) -> bool:
    """A running job's worker updates its heartbeat every 30s; RQ itself only notices a dead
    worker when another worker cleans up, which can be much later or never"""
    if job.get_status() != JobStatus.STARTED or job.last_heartbeat is None:
        return False
    return datetime.now(UTC) - job.last_heartbeat > HEARTBEAT_LIMIT


# --- Running a deploy (worker) ---


class _Log:
    """Collects the output and saves it to the deploy about once a second"""

    def __init__(self, deploy: Deploy) -> None:
        self.deploy = deploy
        self.parts: list[str] = []
        self.last_save = time.monotonic()

    def write(self, text: str) -> None:
        self.parts.append(text)
        if time.monotonic() - self.last_save >= SAVE_EVERY:
            self.save()

    def save(self) -> None:
        self.deploy.output = "".join(self.parts)
        db.session.commit()
        self.last_save = time.monotonic()


def run_deploy(deploy_id: int) -> None:
    """Background job: check out the deploy's commit, read its engage.yaml, run its deploy script"""
    deploy = db.session.get_one(Deploy, deploy_id)
    # Each deploy gets its own folder, so deploys never share files
    workdir = Path(current_app.config["DEPLOY_WORKSPACE"]) / f"deploy-{deploy.id}"
    log = _Log(deploy)
    try:
        # Each step blocks until it ends and returns its DeployStatus
        deploy.status = _run(deploy, workdir, log)
        # Show the outcome at the end of the log, where the user is looking
        if deploy.status is not DeployStatus.SUCCEEDED:
            log.write(f"\n{deploy.status.value}\n")
    except Exception as exc:
        # A crash in our own code: put the error in the log, then let RQ record it too
        log.write(f"\n{exc}\n")
        deploy.status = DeployStatus.FAILED
        raise
    finally:
        # Runs whatever happened above, so the deploy never stays half-finished
        deploy.ended_at = datetime.now(UTC)
        log.save()
        shutil.rmtree(workdir, ignore_errors=True)


def _run(deploy: Deploy, workdir: Path, log: _Log) -> DeployStatus:
    """Check out the commit, then run the deploy script that its engage.yaml names"""
    env = _script_env(deploy, workdir)
    job_id = _job_id(deploy.id)
    status = _stream(["bash", "bin/checkout.sh"], env, log, CHECKOUT_TIMEOUT, job_id)
    if status is not DeployStatus.SUCCEEDED:
        return status
    config, name = _read_config(workdir, deploy.stack.environment)
    log.write(f"\nSettings from {name}\n" if name else "\nNo engage.yaml, using the defaults\n")
    log.write(f"\n$ bash {config.deploy.file}  (timeout {config.deploy.timeout}s)\n")
    # Run from the checkout, so the script's relative paths work
    return _stream(
        ["bash", config.deploy.file],
        env,
        log,
        config.deploy.timeout,
        job_id,
        cwd=workdir,
    )


def _read_config(workdir: Path, environment: str) -> tuple[EngageConfig, str | None]:
    """engage.<environment>.yaml from the checkout, else engage.yaml, else the defaults.
    Returns the config and the file it came from"""
    for name in config_files(environment):
        path = workdir / name
        if path.is_file():
            # An invalid file raises EngageConfigError; run_deploy puts its message in the log
            return parse_config(path.read_text(), name), name
    return EngageConfig(), None


def _stream(
    args: list[str],
    env: dict[str, str],
    log: _Log,
    timeout: int,
    job_id: str,
    cwd: Path | None = None,
) -> DeployStatus:
    """Run a command, write each output line to the log, and return how it ended"""
    # `with` closes the output pipe and waits for the exit code when the block ends
    with subprocess.Popen(
        args,
        env=env,
        cwd=cwd,
        # Read the output here instead of printing it in the worker's terminal
        stdout=subprocess.PIPE,
        # Errors go into the same stream, so they land in the log in the right order
        stderr=subprocess.STDOUT,
        # Lines as text instead of bytes
        text=True,
        # Its own process group, so stopping it also stops what it started (helm, oc, ...)
        start_new_session=True,
    ) as proc:
        assert proc.stdout is not None  # Just to make typing happy

        # Starts the timeout clock in the background
        stopped = _watch(proc, timeout, job_id)
        # Each line arrives as soon as the command prints it; the loop ends when the command exits
        for line in proc.stdout:
            log.write(line)
    # The watcher stopped it: that result wins over the exit code
    if "status" in stopped:
        return stopped["status"]
    # Exit code 0 means success, anything else is a failure
    return DeployStatus.SUCCEEDED if proc.returncode == 0 else DeployStatus.FAILED


def _watch(proc: subprocess.Popen, timeout: int, job_id: str) -> dict[str, DeployStatus]:
    """Stops the command on timeout or cancel: SIGTERM, then SIGKILL if it's still running.
    On interrupt, SIGKILL right away.
    Returns a dict that gets a "status" once it stopped the command"""
    stopped: dict[str, DeployStatus] = {}
    deadline = time.monotonic() + timeout

    def send(sig: signal.Signals) -> None:
        # To the whole process group, so child processes stop too
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            # Already exited between our check and the signal
            pass

    def watch(queue: Queue) -> None:
        termed_at = None
        # poll() is None while the command is still running
        while proc.poll() is None:
            time.sleep(1)

            try:
                job = queue.fetch_job(job_id)
                sig = job.meta.get("signal") if job else None
            except Exception:
                sig = None
            match sig:
                case "cancel":
                    stopped["status"] = DeployStatus.CANCELLED
                case "interrupt":
                    stopped["status"] = DeployStatus.INTERRUPTED
                    send(signal.SIGKILL)
                    continue
                case _:
                    if time.monotonic() < deadline:
                        continue
                    stopped["status"] = DeployStatus.TIMED_OUT

            if termed_at is None:
                # First, ask it to stop, so the script can clean up.
                # For helm upgrade commands, this can trigger a long rollback.
                termed_at = time.monotonic()
                send(signal.SIGTERM)
            elif time.monotonic() - termed_at > DEPLOY_TIMEOUT:
                # Still running after the grace period: force it
                send(signal.SIGKILL)

    # Reading the output blocks, so a thread keeps the time
    # daemon=True: Python doesn't wait for it on exit, so if our code crashes,
    # the watcher can't keep the job alive;
    # cutting it off is harmless, it only sends signals and never writes to the DB
    threading.Thread(target=watch, daemon=True, args=[job_queue.queue]).start()
    return stopped


# List of environment variables passed to the task
JOB_ENV_ALLOWLIST = [
    "KUBERNETES_SERVICE_PORT_HTTPS",
    "KUBERNETES_SERVICE_PORT",
    "KUBERNETES_PORT_443_TCP",
    "KUBERNETES_PORT_443_TCP_PROTO",
    "KUBERNETES_PORT_443_TCP_ADDR",
    "KUBERNETES_SERVICE_HOST",
    "KUBERNETES_PORT",
    "KUBERNETES_PORT_443_TCP_PORT",
    "HELM_CONFIG_HOME",
    "HELM_CACHE_HOME",
    "HELM_DATA_HOME",
    "PATH",
    "HOME",
]


def _script_env(deploy: Deploy, workdir: Path) -> dict[str, str]:
    """Only what the script needs"""
    # The stack's own env vars, from the settings page
    env = {var.key: var.value for var in deploy.stack.stack_env_vars}

    # Set last, so a stack's env vars can't override these
    env.update(
        {
            **{var: os.environ.get(var) for var in JOB_ENV_ALLOWLIST},
            "WORKDIR": str(workdir),
            "COMMIT_SHA": deploy.commit.commit_sha,
            "STACK_ORG": deploy.stack.organization,
            "STACK_REPO": deploy.stack.repository,
            "ENVIRONMENT": deploy.stack.environment,
            # Python tools print right away instead of buffering, so the log stays live
            "PYTHONUNBUFFERED": "1",
        }
    )
    return env
