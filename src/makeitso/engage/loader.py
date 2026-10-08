from collections.abc import Callable
from pathlib import Path

from makeitso.engage.config import EngageConfig, config_files, parse_config
from makeitso.github import GitHubRepo


def load_config(repo: GitHubRepo, ref: str, environment: str) -> tuple[EngageConfig, str | None]:
    """The stack's config at `ref`, read through the GitHub API"""
    return _find_config(environment, lambda name: repo.file_content(name, ref))


def read_config(folder: Path, environment: str) -> tuple[EngageConfig, str | None]:
    """The config from a checked-out repo, e.g. a deploy's folder"""

    def read(name: str) -> str | None:
        path = folder / name
        return path.read_text() if path.is_file() else None

    return _find_config(environment, read)


def _find_config(
    environment: str, read: Callable[[str], str | None]
) -> tuple[EngageConfig, str | None]:
    """engage.<environment>.yaml if the repo has it, else engage.yaml, else the defaults.
    `read` returns a file's text, or None if it's missing.
    Returns the config and the file it came from (None: defaults).
    An invalid file raises EngageConfigError"""
    for name in config_files(environment):
        text = read(name)
        if text is not None:
            return parse_config(text, name), name
    return EngageConfig(), None
