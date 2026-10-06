# webhooks

Receives GitHub's webhooks, so stacks find out about new commits and finished checks without
waiting for the background sync.

- Every request is checked against `GITHUB_WEBHOOK_SECRET`; a bad or missing signature is
  rejected.
- A push to a stack's branch, or a finished check suite on it, queues a sync for that stack
  (see [stacks](../stacks/README.md)). Continuous deploy runs after the sync.

## Testing locally

The GitHub CLI can forward a repo's webhooks to the local app:

```
gh webhook forward --repo=bcgov/makeitso \
  --events=push,check_suite \
  --url=http://localhost:8000/webhooks/webhook-receiver \
  --secret <the secret passed to the app in GITHUB_WEBHOOK_SECRET>
```
