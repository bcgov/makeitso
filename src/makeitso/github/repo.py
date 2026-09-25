import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Self

from github import Github, UnknownObjectException
from github.Commit import Commit

from makeitso.github.types import GitHubCheck, GitHubCommit

# Imported for type checkers only; importing at runtime would be circular
if TYPE_CHECKING:
    from makeitso.models.stack import Stack

COMMIT_LIMIT = 10

# Check states that make a commit's overall state "failure" or "pending"; anything else counts as ok
FAILED_STATES = {"failure", "cancelled", "timed_out"}
PENDING_STATES = {"pending", "queued", "in_progress", "waiting", "requested", "action_required"}

# First line of a GitHub merge commit, e.g. "Merge pull request #12 from org/branch"
MERGE_HEADLINE = re.compile(r"^Merge pull request #(\d+) from ")


class GitHubRepo:
    def __init__(self, client: Github, repository: str) -> None:
        # the client is lazy, so this makes no request yet
        self.repo = client.get_repo(repository)

    @classmethod
    def for_stack(cls, client: Github, stack: Stack) -> Self:
        return cls(client, f"{stack.organization}/{stack.repository}")

    def exists(self) -> bool:
        """False if the repository doesn't exist or the token can't see it"""
        try:
            # The repo is lazy; update() makes the request
            self.repo.update()
        except UnknownObjectException:
            return False
        return True

    def has_branch(self, branch: str) -> bool:
        try:
            self.repo.get_branch(branch)
        except UnknownObjectException:
            return False
        return True

    def commits(self, branch: str) -> list[GitHubCommit]:
        """The latest commits that landed on `branch`, the newest first

        GitHub lists every commit reachable from the branch, including the ones inside each
        merged pull request. We only want what landed on the branch itself, so we start at
        the newest commit and keep following its *first* parent:

            M2 (merge of PR #2) --first parent--> M1 (merge of PR #1) --> ...
             \\--second parent--> commits inside PR #2 (skipped)
        """
        # the newest PER_PAGE commits, enough to walk back through
        page = self.repo.get_commits(sha=branch).get_page(0)
        by_sha = {commit.sha: commit for commit in page}

        found: list[GitHubCommit] = []
        commit = page[0] if page else None
        while commit is not None and len(found) < COMMIT_LIMIT:
            found.append(_to_commit(commit))
            # Step to the first parent; stop if it's outside the fetched page
            commit = by_sha.get(commit.parents[0].sha) if commit.parents else None
        return found

    def checks(self, sha: str) -> list[GitHubCheck]:
        """CI results for one commit"""
        commit = self.repo.get_commit(sha)
        return [
            GitHubCheck(
                name=run.name,
                # A finished run has a conclusion (success, failure, ...); otherwise use its status
                state=run.conclusion or run.status,
                # GitHub's API allows a null URL; store "" so one check can't fail the sync
                url=run.html_url or "",
            )
            for run in commit.get_check_runs()
        ]


def _to_commit(commit: Commit) -> GitHubCommit:
    """Turn a PyGithub commit into our own GitHubCommit"""
    # commit.commit is the underlying git commit, with the message, name and dates
    author = commit.author
    title, pull_request_number = _title_and_pull_request(commit.commit.message)
    return GitHubCommit(
        sha=commit.sha,
        message=title,
        url=commit.html_url,
        committed_at=commit.commit.committer.date,
        pull_request_number=pull_request_number,
        author_name=commit.commit.author.name,
        author_login=author.login if author else None,
        author_avatar_url=author.avatar_url if author else None,
        author_url=author.html_url if author else None,
    )


def _title_and_pull_request(message: str) -> tuple[str, int | None]:
    """The title to show for a commit and its PR number

    "Merge pull request #12 from org/branch\\n\\nFix the thing" -> ("Fix the thing", 12)
    "Fix typo in README" -> ("Fix typo in README", None)
    """
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    headline = lines[0] if lines else ""
    if match := MERGE_HEADLINE.match(headline):
        return (lines[1] if len(lines) > 1 else headline), int(match.group(1))
    return headline, None


def overall_state(check_states: Iterable[str]) -> str | None:
    """One state for a commit's status icon: failure, pending or success; None if no checks"""
    states = set(check_states)
    if not states:
        return None
    # `&` is set intersection: true if any state is also in the given set
    if states & FAILED_STATES:
        return "failure"
    if states & PENDING_STATES:
        return "pending"
    return "success"
