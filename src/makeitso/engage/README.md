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

## How the file is found

Each stack has an environment (`dev`, `test`, `prod`, ...), set when the stack is created.
The names tried, in order:

1. `engage.<environment>.yaml`
2. `engage.yaml`

The first file found is used as a whole; files aren't merged. If neither exists, every setting
uses its default. An environment name with anything other than letters, digits, `_` or `-` only
tries `engage.yaml`.

For a repo with `engage.yaml` and `engage.prod.yaml`:

| Stack environment | File used |
|---|---|
| `prod` | `engage.prod.yaml` |
| `dev` | `engage.yaml` |

The same rule is used in two places, reading the file in two ways:

- **Through the GitHub API.** Nothing is checked out, so this is quick. Used by the deploy page
  (at the commit being deployed) and by a stack sync (at the branch head, to save
  `ci.allow_failures` for the check icons).
- **From the checkout.** The worker reads the file again after checking out the commit, and uses
  that copy for the actual run.

The deploy page and the deploy log both show which file was used.

## Validation

Anything present but wrong is an error, with a message pointing at the setting:

- unknown keys, so typos don't go unnoticed (`ci.allow_failure: unknown setting`)
- wrong types, with no conversion: `timeout: "30"` or `timeout: yes` is rejected
- values out of range (`deploy.timeout: Input should be greater than 0`)
- invalid YAML

On the deploy page the error is shown and blocks the deploy. If the file only turns out invalid
on the worker, the deploy fails with the error in its log.

## Files

- `config.py`: the settings, their defaults and validation, and which file names to try.
- `loader.py`: finds and reads the file through the GitHub API.
- `errors.py`: the error raised for an invalid file.
