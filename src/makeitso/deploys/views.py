from flask import render_template, request
from flask.views import MethodView
from makeitso.deploys.controller import Controller
from makeitso.deploys.forms import NewDeployForm

import sqlalchemy as sa
import sqlalchemy.orm as so

from makeitso.extensions import db
from makeitso.models.deploy import Deploy


class DeployView(MethodView):

    def get(self, stack_id: int, deploy_id: int):
        if request.headers.get("HX-Request"):
            commit = db.session.scalar(
                sa.select(Deploy)
                .options(so.selectinload(Deploy.commit))
                .filter_by(id=deploy_id)
            ).commit

            job = Controller.get_job(commit_sha=commit.commit_sha)
            return render_template("deploys/_job_status.html", job=job)

        return render_template("deploys/detail.html", deploy_id=deploy_id)


class NewDeployView(MethodView):

    def get(self, stack_id: int, commit_sha: str):
        return render_template(
            "deploys/new.html", commit_sha=commit_sha, form=NewDeployForm()
        )

    def post(self, stack_id: int, commit_sha: str):
        deploy = Controller.start_deploy(commit_sha=commit_sha)
        # Job controller stuff
        return render_template("deploys/detail.html", deploy_id=deploy.id)
