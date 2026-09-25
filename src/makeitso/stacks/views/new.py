from flask import redirect, render_template
from flask.views import MethodView

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import db
from makeitso.models.stack import Stack
from makeitso.stacks.forms import NewStackForm


class NewStackView(MethodView):
    def __init__(self):
        self.form = NewStackForm()

    @requires_auth
    def get(self):
        return render_template("stacks/new.html", title="New Stack", form=self.form)

    @requires_auth
    def post(self):
        if self.form.validate_on_submit():
            stack = Stack(
                organization=self.form.organization.data,
                repository=self.form.repository.data,
                branch=self.form.branch.data,
                name=self.form.repository.data,
                environment=self.form.environment.data,
            )
            db.session.add(stack)
            db.session.commit()

            return redirect("/")

        return render_template("stacks/new.html", title="New Stack", form=self.form)
