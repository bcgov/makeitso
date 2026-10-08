from authlib.integrations.base_client import OAuthError
from flask import Blueprint, current_app, flash, redirect, render_template, session, url_for

from makeitso.extensions import oauth

bp = Blueprint("auth", __name__)


@bp.errorhandler(OAuthError)
def handle_oauth_error(error):
    return render_template("main/error.html", error_message=error.description)


@bp.route("/authorize")
def authorize():
    """
    Callback redirect for OAuth flow
    """

    token = oauth.github.authorize_access_token()
    session["token"] = token

    response = oauth.github.get("user")
    response.raise_for_status()

    user_info = response.json()

    org = current_app.config["GITHUB_ORG"]
    team = current_app.config["GITHUB_TEAM"]
    if not _is_team_member(org, team, user_info["login"]):
        session.clear()
        flash(f"You need to be a member of the {org}/{team} GitHub team to log in", "danger")
        return redirect("/")

    session["user"] = user_info

    return redirect("/")


def _is_team_member(org: str | None, team: str | None, username: str) -> bool:
    # Fail closed if the team isn't configured
    if not org or not team:
        return False

    response = oauth.github.get(f"orgs/{org}/teams/{team}/memberships/{username}")
    # 404 means not a member, or the token can't see the team
    if response.status_code != 200:
        return False

    # Pending invites don't count
    return response.json().get("state") == "active"


@bp.route("/login")
def login():
    scheme = "https" if current_app.config["SESSION_COOKIE_SECURE"] else "http"
    return oauth.github.authorize_redirect(
        redirect_uri=url_for("auth.authorize", _external=True, _scheme=scheme)
    )


# POST with the CSRF token, so another site can't log users out with a link or an <img>
@bp.post("/logout")
def logout():
    """
    Logging out **from this app only**
    This will not log the user out of GitHub itself.
    """
    session.clear()
    return redirect("/")
