from functools import wraps

from flask import redirect, session, url_for


def requires_auth(view):
    """
    Decorator requiring authentication for a view
    """

    @wraps(view)
    def decorated(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return decorated
