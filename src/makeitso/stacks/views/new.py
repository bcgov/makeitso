from flask import redirect, render_template
from flask.views import MethodView
from makeitso.auth.decorators import requires_auth
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
            # Handle form submission for creating a new stack
            print("yay!")
            return redirect("/")

        print("noooooo")
        return render_template("stacks/new.html", title="New Stack", form=self.form)
