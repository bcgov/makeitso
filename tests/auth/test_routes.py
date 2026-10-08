from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.integrations.base_client import OAuthError

USER = {"login": "octocat", "avatar_url": ""}


def _response(status_code, json=None):
    response = MagicMock(status_code=status_code)
    response.json.return_value = json or {}
    return response


class TestLogin:
    def test_asks_github_for_org_access(self, client):
        response = client.get("/login")

        assert response.status_code == 302
        location = urlparse(response.location)
        assert location.netloc == "github.com"
        assert parse_qs(location.query)["scope"] == ["read:user read:org"]


class TestLogout:
    def test_clears_session(self, client, login):
        login()

        response = client.post("/logout")

        assert response.status_code == 302
        assert response.location == "/"
        with client.session_transaction() as session:
            assert "user" not in session
            assert "token" not in session


class TestAuthorize:
    @pytest.fixture(autouse=True)
    def team(self, app, monkeypatch):
        monkeypatch.setitem(app.config, "GITHUB_ORG", "bcgov")
        monkeypatch.setitem(app.config, "GITHUB_TEAM", "makeitso-users")

    # Fakes the GitHub OAuth client: GET /user, then the team membership call
    @pytest.fixture
    def github(self):
        with patch("makeitso.auth.routes.oauth") as oauth:
            oauth.github.authorize_access_token.return_value = {"access_token": "t"}
            yield oauth.github

    @staticmethod
    def _authorize(client, github, membership):
        github.get.side_effect = [_response(200, USER), membership]
        return client.get("/authorize")

    def test_member_logs_in(self, client, github):
        response = self._authorize(client, github, _response(200, {"state": "active"}))

        assert response.status_code == 302
        assert response.location == "/"
        github.get.assert_called_with("orgs/bcgov/teams/makeitso-users/memberships/octocat")
        with client.session_transaction() as session:
            assert session["user"] == USER

    @pytest.mark.parametrize(
        "membership",
        [_response(404), _response(200, {"state": "pending"})],
        ids=["not-a-member", "pending-invite"],
    )
    def test_non_member_is_sent_back_with_a_message(self, client, github, membership):
        response = self._authorize(client, github, membership)

        assert response.status_code == 302
        assert response.location == "/"
        with client.session_transaction() as session:
            assert "user" not in session
            assert "token" not in session

    def test_non_member_sees_message_on_landing_page(self, client, github):
        github.get.side_effect = [_response(200, USER), _response(404)]

        response = client.get("/authorize", follow_redirects=True)

        assert response.request.path == "/"
        assert b"member of the bcgov/makeitso-users GitHub team" in response.data
        assert b"Log in with GitHub" in response.data

    def test_oauth_error_shows_error_page(self, client, github):
        github.authorize_access_token.side_effect = OAuthError(description="bad code")

        response = client.get("/authorize")

        assert b"bad code" in response.data
        with client.session_transaction() as session:
            assert "user" not in session

    def test_denied_when_team_not_configured(self, app, client, github, monkeypatch):
        monkeypatch.setitem(app.config, "GITHUB_TEAM", None)
        github.get.return_value = _response(200, USER)

        response = client.get("/authorize")

        assert response.status_code == 302
        with client.session_transaction() as session:
            assert "user" not in session
        # Never asks GitHub about membership
        assert github.get.call_count == 1
