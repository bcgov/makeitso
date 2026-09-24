from authlib.integrations.base_client import OAuthError
from flask import Blueprint, current_app, redirect, render_template, session, url_for

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
    session["user"] = user_info

    return redirect("/")


@bp.route("/login")
def login():
    scheme = "https" if current_app.config["SESSION_COOKIE_SECURE"] else "http"
    return oauth.github.authorize_redirect(
        redirect_uri=url_for("auth.authorize", _external=True, _scheme=scheme)
    )


@bp.route("/logout")
def logout():
    """
    Logging out **from this app only**
    This will not log the user out of GitHub itself.
    """
    session.clear()
    return redirect("/")
