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

from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, PositiveInt, ValidationError, model_validator

from makeitso.engage.errors import EngageConfigError

CONFIG_FILE = "engage.yaml"


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


def parse_config(text: str) -> EngageConfig:
    try:
        # safe_load only builds plain data; yaml.load could run code from the file
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise EngageConfigError(f"{CONFIG_FILE} is not valid YAML: {exc}") from exc
    try:
        # An empty file loads as None
        return EngageConfig.model_validate({} if data is None else data)
    except ValidationError as exc:
        raise EngageConfigError(_describe(exc)) from exc


def _describe(exc: ValidationError) -> str:
    """Pydantic's errors as one readable line, e.g. "deploy.timeout: Input should be ..." """
    problems = []
    for error in exc.errors():
        where = ".".join(str(part) for part in error["loc"]) or "top level"
        message = "unknown setting" if error["type"] == "extra_forbidden" else error["msg"]
        problems.append(f"{where}: {message}")
    return f"Invalid {CONFIG_FILE}: " + "; ".join(problems)
