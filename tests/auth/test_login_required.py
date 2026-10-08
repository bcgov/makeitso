from typing import Any

from flask import url_for
from werkzeug.routing import Rule

# Routes anyone can open; every other route must send logged-out users to the login page
PUBLIC_ENDPOINTS = {
    # Landing page; shows only the login button when logged out
    "main.index",
    # Health checks from OpenShift, which can't log in
    "main.healthz",
    # The login flow itself
    "auth.login",
    "auth.authorize",
    "auth.logout",
    # Called by GitHub, which can't log in; checked by its signature instead
    "webhooks.receive_github_webhook",
    # CSS, JS and images
    "static",
    "bootstrap.static",
}


def _url(rule: Rule) -> str:
    """The rule's URL with a placeholder for each part, e.g. /stacks/1/deploys/1"""
    values: dict[str, Any] = {name: 1 if name.endswith("_id") else "x" for name in rule.arguments}
    return url_for(rule.endpoint, **values)


class TestLoginRequired:
    def test_every_route_requires_login(self, app, client):
        unprotected = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint in PUBLIC_ENDPOINTS:
                continue
            url = _url(rule)
            for method in sorted((rule.methods or set()) - {"HEAD", "OPTIONS"}):
                response = client.open(url, method=method)
                if response.status_code != 302 or response.location != "/login":
                    unprotected.append(f"{method} {url} ({rule.endpoint})")

        assert unprotected == []

    def test_public_endpoints_exist(self, app):
        """Catches a route that was renamed or removed but is still listed as public"""
        endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

        assert PUBLIC_ENDPOINTS - endpoints == set()
