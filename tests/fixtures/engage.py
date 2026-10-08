import pytest

from makeitso.github import GitHubRepo


# Files the app reads from a repo through the GitHub API (engage.yaml), served from memory
# No files (so the engage.yaml defaults) unless a test calls engage_yaml("...")
@pytest.fixture(autouse=True)
def engage_yaml(monkeypatch):
    files: dict[str, str] = {}
    monkeypatch.setattr(GitHubRepo, "file_content", lambda repo, path, ref: files.get(path))

    # engage_yaml("deploy:\n  timeout: 60\n") or engage_yaml(text, "engage.prod.yaml")
    def engage_yaml(text: str, name: str = "engage.yaml") -> None:
        files[name] = text

    return engage_yaml
