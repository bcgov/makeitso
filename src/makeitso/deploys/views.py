from flask import render_template
from flask.views import MethodView


class DeployView(MethodView):
    def get(self, stack_id: int, deploy_id: int):
        return render_template("deploys/detail.html", deploy_id=deploy_id)
