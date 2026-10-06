The Github CLI lets us forward webhooks locally:

```
gh webhook forward --repo=bcgov/makeitso --events=push,pull_request --url=http://localhost:8000/webhooks/webhook-receiver --secret <the secret passed to the app in GITHUB_WEBHOOK_SECRET>
```
