from flask import request

from makeitso.models.commit import Commit
from makeitso.models.stack import Stack


def emergency_mode() -> bool:
    """Emergency mode is on for this page (?emergency=1); it lets failed CI checks through"""
    return request.args.get("emergency") == "1"


def checks_failed(commit: Commit, allow_failures: list[str]) -> bool:
    """A check failed that isn't listed in engage.yaml's ci.allow_failures"""
    return commit.checks_state(allow_failures) == "failure"


def deploy_blockers(
    stack: Stack, commit: Commit, allow_failures: list[str], emergency: bool = False
) -> list[str]:
    """Why this commit can't be deployed; empty if it can. A running deploy is checked separately.
    Emergency mode lets failed CI checks through, but not the lock"""
    reasons = []
    if stack.locked:
        reasons.append(f"The stack is locked: {stack.lock_reason}")
    if checks_failed(commit, allow_failures) and not emergency:
        reasons.append("Some checks failed")
    return reasons
