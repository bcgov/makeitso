# github

Thin wrapper around [PyGithub](https://pygithub.readthedocs.io/) for reading commits and CI checks.
Nothing here touches the database; `stacks/sync.py` takes these results and saves them.

## Files

- `tokens.py`: builds a `Github` client. `client_for_current_user()` uses the logged-in user's
  OAuth token, `client_for_server()` uses `GITHUB_TOKEN` from config (for background jobs).
- `repo.py`: `GitHubRepo`, the calls we make against one repository.
- `types.py`: plain dataclasses (`GitHubCommit`, `GitHubCheck`) so the rest of the app doesn't
  depend on PyGithub objects.
- `errors.py`: `GitHubError`, raised when no token is available.

## How a sync reads GitHub

1. `commits(branch)` fetches the newest 100 commits in a single request, then walks
   **first parents** from the branch head, keeping up to 10 (`COMMIT_LIMIT`).
2. For each of those, `checks(sha)` fetches all check runs (PyGithub follows the pages).

A branch's commit list also contains every commit made inside merged PRs. Following only the
first parent of each merge skips those and leaves what actually landed on the branch, one entry
per PR.

## Decisions

- **State of a check** is `conclusion` if the run finished, otherwise its `status`
  (`queued`, `in_progress`, ...).
- **Overall state** (`overall_state()`): any failed state makes it `failure`, else anything
  unfinished makes it `pending`, else `success`; `None` when there are no checks. The icon
  lists in `templates/stacks/_checks.html` must match `FAILED_STATES` / `PENDING_STATES`.
- **Titles.** For "Merge pull request #N from ..." we show the PR title (the next line) and
  keep N. Squash-merge `(#N)` suffixes are left alone.

## Known gaps

- No fallback to the next page when the first-parent walk leaves the first 100 commits.
- Background jobs use a personal access token; a GitHub App installation token should replace
  it.
- Syncing is manual (Sync button) or on stack creation. Webhooks (`push`, `check_run`) would
  let us refresh only what changed.
