from flask import Blueprint
from makeitso.stacks.views.new import NewStackView

bp = Blueprint("stacks", __name__)

bp.add_url_rule("/new", view_func=NewStackView.as_view("new_stack"))
