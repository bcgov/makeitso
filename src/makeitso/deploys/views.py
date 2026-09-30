import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import redirect, render_template, request, url_for
from flask.views import MethodView

from makeitso.auth.decorators import requires_auth
from makeitso.deploys.controller import Controller
from makeitso.deploys.forms import NewDeployForm
from makeitso.extensions import db
from makeitso.models.deploy import Deploy


class DeployView(MethodView):
    @requires_auth
    def get(self, stack_id: int, deploy_id: int):
        deploy = db.first_or_404(
            sa.select(Deploy)
            .options(so.selectinload(Deploy.commit))
            .where(Deploy.id == deploy_id, Deploy.stack_id == stack_id)
        )

        job = Controller.get_job(commit_sha=deploy.commit.commit_sha)
        if request.headers.get("HX-Request"):
            return render_template(
                "deploys/_job_status.html", stack_id=stack_id, deploy_id=deploy_id, job=job
            )
        return render_template(
            "deploys/detail.html", stack_id=stack_id, deploy_id=deploy_id, job=job
        )


class NewDeployView(MethodView):
    @requires_auth
    def get(self, stack_id: int, commit_sha: str):
        return render_template("deploys/new.html", commit_sha=commit_sha, form=NewDeployForm())

    @requires_auth
    def post(self, stack_id: int, commit_sha: str):
        deploy = Controller.start_deploy(stack_id=stack_id, commit_sha=commit_sha)
        return redirect(url_for("stacks.deploys.detail", stack_id=stack_id, deploy_id=deploy.id))
