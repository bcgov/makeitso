"""Per-repository settings, read from an `engage.yaml` file at the repo's root

Every key is optional; a missing file or key uses the defaults below. Example:

    deploy:
      file: deploy.sh     # script to run, relative to the repo root
      timeout: 1800       # seconds

    review:
      checklist:          # shown before deploying
        - Is it Friday?

    ci:
      allow_failures:     # check names that are shown but don't block a deploy
        - Dependabot
"""

import re
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, PositiveInt, ValidationError, model_validator

from makeitso.engage.errors import EngageConfigError

CONFIG_FILE = "engage.yaml"


def config_files(environment: str) -> list[str]:
    """File names to try, first one found wins: engage.<environment>.yaml, then engage.yaml.
    E.g. engage.prod.yaml for a prod stack"""
    if re.fullmatch(r"[\w-]+", environment):
        return [f"engage.{environment}.yaml", CONFIG_FILE]
    return [CONFIG_FILE]


class _Section(BaseModel):
    # Unknown keys are errors to catch typos; strict means no conversions, so `timeout: "30"` fails
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @model_validator(mode="before")
    @classmethod
    def _skip_empty(cls, data: Any) -> Any:
        # A key with nothing after it, like `deploy:`, uses the default
        if isinstance(data, dict):
            return {key: value for key, value in data.items() if value is not None}
        return data


class DeployConfig(_Section):
    file: str = "deploy.sh"
    timeout: PositiveInt = 1800


class ReviewConfig(_Section):
    checklist: list[str] = []


class CIConfig(_Section):
    allow_failures: list[str] = []


class EngageConfig(_Section):
    deploy: DeployConfig = DeployConfig()
    review: ReviewConfig = ReviewConfig()
    ci: CIConfig = CIConfig()


def parse_config(text: str, file_name: str = CONFIG_FILE) -> EngageConfig:
    """`file_name` is only used in error messages"""
    try:
        # safe_load only builds plain data; yaml.load could run code from the file
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise EngageConfigError(f"{file_name} is not valid YAML: {exc}") from exc
    try:
        # An empty file loads as None
        return EngageConfig.model_validate({} if data is None else data)
    except ValidationError as exc:
        raise EngageConfigError(_describe(exc, file_name)) from exc


def _describe(exc: ValidationError, file_name: str) -> str:
    """Pydantic's errors as one readable line, e.g. "deploy.timeout: Input should be ..." """
    problems = []
    for error in exc.errors():
        where = ".".join(str(part) for part in error["loc"]) or "top level"
        message = "unknown setting" if error["type"] == "extra_forbidden" else error["msg"]
        problems.append(f"{where}: {message}")
    return f"Invalid {file_name}: " + "; ".join(problems)
