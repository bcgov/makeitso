from authlib.integrations.flask_client import OAuth
from flask import Blueprint, redirect, session, url_for

from makeitso.extensions import oauth

bp = Blueprint("auth", __name__)


@bp.route("/callback")
def callback():
    """
    Callback redirect for OAuth flow
    """

    token = oauth.github.authorize_access_token()
    response = oauth.github.get("user")
    response.raise_for_status()

    user_info = response.json()
    session["user"] = user_info

    return redirect("/")


@bp.route("/login")
def login():
    return oauth.github.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True)
    )


@bp.route("/logout")
def logout():
    """
    Logging out **from this app only**
    This will not log the user out of GitHub itself.
    """
    session.clear()
    return redirect("/")
