from flask import Blueprint

from makeitso.deploys.views import DeployListView, DeployLogView, DeployView, NewDeployView

bp = Blueprint("deploys", __name__)

bp.add_url_rule("/", view_func=DeployListView.as_view("list"))
bp.add_url_rule("/new/<commit_sha>", view_func=NewDeployView.as_view("new"))
bp.add_url_rule("/<int:deploy_id>", view_func=DeployView.as_view("detail"))
bp.add_url_rule("/<int:deploy_id>/log", view_func=DeployLogView.as_view("log"))
