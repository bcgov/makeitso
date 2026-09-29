from flask import render_template
from flask.views import MethodView


class DeployView(MethodView):

    def get(self, stack_id: int, deploy_id: int):
        return render_template("deploys/detail.html", deploy_id=deploy_id)


class NewDeployView(MethodView):

    def get(self, stack_id: int, commit_sha: str):
        return render_template("deploys/new.html", commit_sha=commit_sha)