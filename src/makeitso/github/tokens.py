from flask import current_app, session
from github import Auth, Github

from makeitso.github.errors import GitHubError

PER_PAGE = 100


def github_client(token: str) -> Github:
    return Github(auth=Auth.Token(token), per_page=PER_PAGE, timeout=10, lazy=True)


def client_for_current_user() -> Github:
    token = (session.get("token") or {}).get("access_token")
    if not token:
        raise GitHubError("Not logged in with GitHub")
    return github_client(token)


def client_for_server() -> Github:
    """A client for code without a logged-in user, like background jobs"""
    token = current_app.config["GITHUB_TOKEN"]
    if not token:
        raise GitHubError("GITHUB_TOKEN is not set")
    return github_client(token)
