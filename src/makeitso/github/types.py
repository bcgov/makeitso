from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GitHubCommit:
    sha: str
    message: str
    url: str
    committed_at: datetime
    pull_request_number: int | None
    author_name: str
    author_login: str | None
    author_avatar_url: str | None
    author_url: str | None


@dataclass(frozen=True)
class GitHubCheck:
    name: str
    state: str
    url: str
