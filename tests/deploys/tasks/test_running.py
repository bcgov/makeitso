import os
import time

import pytest

from makeitso.deploys import tasks
from makeitso.deploys.tasks import (
    _Log,
    _script_env,
    _stream,
    run_deploy,
    signal_job,
)
from makeitso.extensions import db
from makeitso.models.deploy import DeployStatus
from makeitso.models.stack_env_var import StackEnvVar
from tests.factories import start_running_deploy


class TestStream:
    """Runs real bash commands; the watcher checks for timeouts and signals once a second"""

    @staticmethod
    def _run_bash(deploy, script: str, timeout: int = 30) -> DeployStatus:
        """Run a bash script through _stream and save its output to the deploy"""
        log = _Log(deploy)
        env = {"PATH": os.environ["PATH"]}
        status = _stream(["bash", "-c", script], env, log, timeout, f"deploy-{deploy.id}")
        log.save()
        return status

    def test_success_logs_every_line(self):
        deploy = start_running_deploy()

        status = self._run_bash(deploy, "echo one; echo two >&2; echo three")

        assert status is DeployStatus.SUCCEEDED
        assert deploy.output == "one\ntwo\nthree\n"

    def test_failure(self):
        assert self._run_bash(start_running_deploy(), "exit 1") is DeployStatus.FAILED

    def test_timeout(self):
        status = self._run_bash(start_running_deploy(), "sleep 30", timeout=1)

        assert status is DeployStatus.TIMED_OUT

    def test_cancel(self):
        deploy = start_running_deploy()
        signal_job(deploy, "cancel")

        assert self._run_bash(deploy, "sleep 30") is DeployStatus.CANCELLED

    def test_interrupt_kills_right_away(self):
        deploy = start_running_deploy()
        signal_job(deploy, "interrupt")

        # Ignores SIGTERM, so only SIGKILL stops it
        assert self._run_bash(deploy, "trap '' TERM; sleep 30") is DeployStatus.INTERRUPTED

    def test_kills_after_grace_period(self, monkeypatch):
        # One second instead of 30 minutes between SIGTERM and SIGKILL
        monkeypatch.setattr(tasks, "DEPLOY_TIMEOUT", 1)

        # Ignores SIGTERM, like a stuck script; only SIGKILL stops it
        status = self._run_bash(start_running_deploy(), "trap '' TERM; sleep 30", timeout=1)

        assert status is DeployStatus.TIMED_OUT

    def test_stops_child_processes(self):
        deploy = start_running_deploy()

        # The background sleep is a child process; it prints its pid, then bash waits for it
        self._run_bash(deploy, "sleep 30 >/dev/null & echo $!; wait", timeout=1)

        child = int(deploy.output.strip())
        # It may take a moment to disappear after the signal
        for _ in range(20):
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                return
            time.sleep(0.1)
        pytest.fail("The child process is still running")


class TestLog:
    def test_saves_while_running(self, monkeypatch):
        # Save on every write instead of once a second
        monkeypatch.setattr(tasks, "SAVE_EVERY", 0)
        deploy = start_running_deploy()

        _Log(deploy).write("cloning\n")

        # Read back from the database, so the page polling the log would see it
        db.session.expire(deploy)
        assert deploy.output == "cloning\n"

    def test_waits_between_saves(self):
        deploy = start_running_deploy()

        _Log(deploy).write("cloning\n")

        db.session.expire(deploy)
        assert deploy.output == ""


class TestScriptEnv:
    def test_passes_only_what_the_script_needs(self, tmp_path, monkeypatch):
        deploy = start_running_deploy()
        monkeypatch.setenv("SECRET_KEY", "worker-secret")
        db.session.add_all(
            [
                StackEnvVar(stack_id=deploy.stack_id, key="NAMESPACE_PREFIX", value="abc123"),
                # Can't replace the commit being deployed
                StackEnvVar(stack_id=deploy.stack_id, key="COMMIT_SHA", value="not-this"),
            ]
        )
        db.session.commit()

        env = _script_env(deploy, tmp_path)

        assert env["NAMESPACE_PREFIX"] == "abc123"
        assert env["COMMIT_SHA"] == deploy.commit.commit_sha
        assert env["ENVIRONMENT"] == "dev"
        assert env["WORKDIR"] == str(tmp_path)
        assert "SECRET_KEY" not in env


class TestRunDeploy:
    """The checkout (a git fetch from GitHub) is faked; the deploy script runs for real"""

    @pytest.fixture(autouse=True)
    def workspace(self, app, tmp_path, monkeypatch):
        monkeypatch.setitem(app.config, "DEPLOY_WORKSPACE", str(tmp_path))
        return tmp_path

    # Replaces the checkout with writing the given files into the deploy's folder
    @pytest.fixture
    def fake_checkout(self, monkeypatch):
        real_stream = tasks._stream

        def fake_checkout(
            files: dict[str, str] | None = None,
            error: Exception | None = None,
            status: DeployStatus = DeployStatus.SUCCEEDED,
        ):
            def stream(args, env, log, timeout, job_id, cwd=None):
                if args != ["bash", "bin/checkout.sh"]:
                    return real_stream(args, env, log, timeout, job_id, cwd)
                os.makedirs(env["WORKDIR"])
                if error:
                    raise error
                for name, text in (files or {}).items():
                    with open(os.path.join(env["WORKDIR"], name), "w") as file:
                        file.write(text)
                return status

            monkeypatch.setattr(tasks, "_stream", stream)

        return fake_checkout

    def test_success(self, workspace, fake_checkout):
        deploy = start_running_deploy()
        fake_checkout({"deploy.sh": "echo deploying $ENVIRONMENT"})

        run_deploy(deploy.id)

        assert deploy.status is DeployStatus.SUCCEEDED
        assert deploy.ended_at is not None
        assert "deploying dev" in deploy.output
        assert not (workspace / f"deploy-{deploy.id}").exists()

    def test_uses_engage_yaml(self, fake_checkout):
        deploy = start_running_deploy()
        fake_checkout({"engage.yaml": "deploy:\n  file: ship.sh\n", "ship.sh": "echo shipping"})

        run_deploy(deploy.id)

        assert deploy.status is DeployStatus.SUCCEEDED
        assert "Settings from engage.yaml" in deploy.output
        assert "shipping" in deploy.output

    def test_failure_ends_log_with_status(self, fake_checkout):
        deploy = start_running_deploy()
        fake_checkout({"deploy.sh": "echo oops; exit 3"})

        run_deploy(deploy.id)

        assert deploy.status is DeployStatus.FAILED
        assert deploy.output.endswith("\nFailed\n")

    def test_checkout_fails(self, fake_checkout):
        deploy = start_running_deploy()
        fake_checkout({"deploy.sh": "echo deploying"}, status=DeployStatus.FAILED)

        run_deploy(deploy.id)

        # Stops after the checkout: the script never runs
        assert deploy.status is DeployStatus.FAILED
        assert "deploying" not in deploy.output

    def test_crash(self, workspace, fake_checkout):
        deploy = start_running_deploy()
        fake_checkout(error=RuntimeError("boom"))

        # Re-raised, so RQ records the job as failed too
        with pytest.raises(RuntimeError, match="boom"):
            run_deploy(deploy.id)

        assert deploy.status is DeployStatus.FAILED
        assert deploy.ended_at is not None
        assert "boom" in deploy.output
        assert not (workspace / f"deploy-{deploy.id}").exists()
