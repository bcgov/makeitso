from flask import Blueprint

from makeitso.deploys.views import DeployView

bp = Blueprint("deploys", __name__)

bp.add_url_rule("/<int:deploy_id>", view_func=DeployView.as_view("detail"))
