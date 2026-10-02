# deploys

Starting a deploy from the web app and running it on a background worker.
The repo's engage file decides what runs; see [engage](../engage/README.md) for how the file is
picked for a stack's environment.

## Files

- `views.py`: the pages: deploying a commit, a deploy's live log, the list of deploys.
- `tasks.py`: queueing a deploy (web side) and running it (worker side).
- `helpers.py`, `queries.py`: small helpers and database lookups shared across the module.

## How a deploy runs

Deploys always run on a background worker. Whatever starts one (today, the Deploy button) saves
the deploy and puts a job on the `deploys` Redis queue, and a worker picks it up. Syncs have
their own queue and worker, so a long deploy and a batch of syncs never wait on each other.

1. **Deploy page.** Reads the engage file at the chosen commit through the GitHub API, without
   checking anything out. Shows the commits since the last successful deploy, the review
   checklist, and anything blocking the deploy. An invalid engage file is shown on the page and
   blocks the deploy.
2. **Deploy button.** Checks everything again, since things may have changed:
   - no other deploy running on the stack
   - the engage file is still valid
   - every checklist item is ticked
   - the stack isn't locked and no check failed, except the ones in `ci.allow_failures`
3. **Queued.** The deploy is saved as in progress, then queued. The database allows only one
   in-progress deploy per stack, so a double-click ends up on the deploy that's already running.
4. **Worker.**
   1. Fetches only that commit into a folder of its own, so deploys never share files.
   2. Reads the engage file again, this time from the checkout.
   3. Runs `deploy.file` from the checkout, stopped after `deploy.timeout` seconds.
   4. Saves the result and deletes the folder, even if something crashed.
5. **Live log.** The worker saves the output to the database about once a second. The deploy
   page polls for the text added since its last request, and stops once the deploy has ended.

## What the script gets

Only these environment variables, nothing else from the worker:

| Variable | Value |
|---|---|
| Stack env vars | From the stack's settings page |
| `ENVIRONMENT` | The stack's environment, e.g. `dev` |
| `COMMIT_SHA` | The commit being deployed |
| `STACK_ORG`, `STACK_REPO` | The GitHub repo |
| `WORKDIR` | The checkout folder |
| `PATH`, `HOME`, `PYTHONUNBUFFERED` | So tools work and output isn't buffered |

The built-in ones are set last, so a stack's env vars can't override them. The script uses these
to know where to deploy; this repo's own `deploy.sh`, for example, needs `NAMESPACE_PREFIX` set as
a stack env var and deploys to `$NAMESPACE_PREFIX-tools`.

## How a deploy ends

- **Succeeded / Failed**: the script's exit code (0 or not).
- **Timed Out**: past the limit, the script and everything it started (`helm`, `oc`, ...) are
  asked to stop, then killed after a grace period.
- **Aborted**: someone stopped the job from the queue's own tools.
- **Lost worker**: a deploy whose worker died never records its result. Opening the deploy
  checks the queue, and marks it Failed if the job is gone or its worker stopped responding.

## Emergency mode

Adding `?emergency=1` to the deploy page lets failed checks through, but not a lock. Deploys that
actually skipped failed checks are marked as such.