import sqlalchemy as sa

from makeitso.engage import EngageConfig, EngageConfigError
from makeitso.engage.loader import load_config
from makeitso.extensions import db
from makeitso.github import GitHubRepo
from makeitso.models.commit import Commit
from makeitso.models.commit_status import CommitStatus
from makeitso.models.stack import Stack


def sync_commits(stack: Stack, repo: GitHubRepo) -> None:
    """Save the branch's latest commits and their checks from GitHub into the database"""
    existing = {
        commit.commit_sha: commit
        for commit in db.session.scalars(sa.select(Commit).where(Commit.stack_id == stack.id))
    }
    # Oldest first, so new commits get increasing ids in git order (pages sort by id)
    for found in reversed(repo.commits(stack.branch)):
        commit = existing.get(found.sha)
        if commit is None:
            commit = Commit(stack=stack, commit_sha=found.sha)
            db.session.add(commit)
        commit.commit_message = found.message
        commit.pull_request_number = found.pull_request_number
        commit.url = found.url
        commit.committed_at = found.committed_at
        commit.author_name = found.author_name
        commit.author_login = found.author_login
        commit.author_avatar_url = found.author_avatar_url
        commit.author_url = found.author_url

        # Replacing the list deletes the old rows (delete-orphan cascade)
        commit.commit_statuses = [
            CommitStatus(name=check.name, state=check.state, html_url=check.url)
            for check in repo.checks(found.sha)
        ]
    db.session.commit()


def save_allow_failures(stack: Stack, repo: GitHubRepo) -> None:
    """Save the stack's ci.allow_failures from the branch head, for the check icons"""
    try:
        config, _ = load_config(repo, stack.branch, stack.environment)
    except EngageConfigError:
        # An invalid file shows on the deploy page; the icons then count every check
        config = EngageConfig()
    stack.allow_failures = list(config.ci.allow_failures)
    db.session.commit()
