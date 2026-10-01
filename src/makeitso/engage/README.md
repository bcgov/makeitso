# engage

Parses `engage.yaml`, the per-repository config file that tells makeitso how to deploy a repo.

## The file

Lives at the root of the deployed repo. Every setting is optional; anything missing uses the
default, and a repo without the file gets all defaults.

```yaml
deploy:
  file: deploy.sh
  timeout: 1800

review:
  checklist:
    - Is it Friday?
    - Did you tell the team?

ci:
  allow_failures:
    - "Dependabot"
    - "test-code / yarn-audit"
    - "Happo (cas-registration)"
```

| Setting | Type | Default | Meaning |
|---|---|---|---|
| `deploy.file` | text | `deploy.sh` | Script to run, relative to the repo root |
| `deploy.timeout` | whole number > 0 | `1800` | Seconds before the deploy is stopped |
| `review.checklist` | list of text | `[]` | Items to confirm before deploying |
| `ci.allow_failures` | list of text | `[]` | Check names that are shown but don't block a deploy |

## One file per environment

A repo can have a file per stack environment:
`engage.prod.yaml` is used by the `prod` stack, and stacks without their own file use `engage.yaml`.
The first file found is used as a whole; files aren't merged.

## Validation

Anything present but wrong is an error, with a message pointing at the setting:

- unknown keys, so typos don't go unnoticed (`ci.allow_failure: unknown setting`)
- wrong types, with no conversion: `timeout: "30"` or `timeout: yes` is rejected
- values out of range (`deploy.timeout: Input should be greater than 0`)
- invalid YAML

All of these raise `EngageConfigError`.

## Usage

```python
from makeitso.engage import EngageConfigError, parse_config

try:
    config = parse_config(text)
except EngageConfigError as exc:
    ...  # show str(exc)

config.deploy.timeout
config.ci.allow_failures
```

The result is read-only.
