from makeitso.engage.config import EngageConfig, config_files, parse_config
from makeitso.github import GitHubRepo


def load_config(repo: GitHubRepo, ref: str, environment: str) -> tuple[EngageConfig, str | None]:
    """The stack's config at `ref`, read through the GitHub API: engage.<environment>.yaml if the
    repo has it, else engage.yaml. Returns the config and the file it came from (None: defaults)"""
    for name in config_files(environment):
        text = repo.file_content(name, ref)
        if text is not None:
            return parse_config(text, name), name
    return EngageConfig(), None
