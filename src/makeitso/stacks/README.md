# stacks

A stack is one repository, one branch and one environment to deploy to, e.g.
`bcgov/makeitso`, `develop`, `dev`. Only one active stack per repo and environment.
Deploys live in [deploys](../deploys/README.md), under a stack.

## Files

- `views/`: the pages: creating a stack, its commit list, its settings, deleting it.
- `forms.py`: the forms on those pages.
- `sync.py`: saves what GitHub returns into the database.
- `tasks.py`: the background sync job, and picking which stacks need one.
- `cli.py`: the `flask stacks sync` command run by the background schedule.

## Sync

Copies the branch's latest commits and their checks from GitHub into the database, so pages
never wait on GitHub.

1. Runs when a stack is created, when someone presses Sync, and in the background (below).
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

## Background sync

Keeps stacks up to date when nobody presses Sync, without hitting GitHub more than needed.

- The `stack-sync` CronJob runs `flask stacks sync` every 10 minutes
  (`stackSync.schedule` in the Helm values). It only queues syncs; the worker does them.
- Only stacks that haven't synced successfully in the last 30 minutes are picked. Each stack
  saves when its last successful sync was, so a manual Sync also resets the clock.
- Each stack also counts its failed syncs in a row. After 5, background syncs skip it (a repo
  that was renamed or lost access), and the stack page says so. Pressing Sync still works,
  and one successful sync resets the count.

## Settings

- **Lock**: stops new deploys, with a reason shown to whoever tries. A running deploy isn't
  affected.
- **Env vars**: passed to the deploy script. See [deploys](../deploys/README.md#what-the-script-gets).

## Delete

The stack is archived instead of deleted, so its deploy history stays. An archived stack frees
its repo and environment for a new stack.
