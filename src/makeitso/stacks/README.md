# stacks

A stack is one repository, one branch and one environment to deploy to, e.g.
`bcgov/makeitso`, `develop`, `dev`. Only one active stack per repo and environment.
Deploys live in [deploys](../deploys/README.md), under a stack.

## Files

- `views/`: the pages: creating a stack, its commit list, its settings, deleting it.
- `forms.py`: the forms on those pages.
- `sync.py`: saves what GitHub returns into the database.
- `tasks.py`: the background sync job.

## Sync

Copies the branch's latest commits and their checks from GitHub into the database, so pages
never wait on GitHub.

1. Runs when a stack is created and when someone presses Sync.
2. The sync is queued as a background job; a stack never has two syncs at once.
3. The worker, using the server's GitHub token:
   - saves the commits and replaces their checks
     (see [github](../github/README.md) for which commits)
   - reads the engage file at the branch head and saves its `ci.allow_failures` on the stack,
     so the check icons can skip those checks without calling GitHub. An invalid file counts
     every check.
4. The commit list refreshes itself while the sync runs. If the sync fails, its error is shown
   on the stack page until the next sync, or for a day at most. The error is kept on the job in
   Redis, not in the database.

## Settings

- **Lock**: stops new deploys, with a reason shown to whoever tries. A running deploy isn't
  affected.
- **Env vars**: passed to the deploy script. See [deploys](../deploys/README.md#what-the-script-gets).

## Delete

The stack is archived instead of deleted, so its deploy history stays. An archived stack frees
its repo and environment for a new stack.
