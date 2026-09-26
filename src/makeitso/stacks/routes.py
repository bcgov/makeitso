from flask import Blueprint

from makeitso.stacks.views.delete import DeleteStackView
from makeitso.stacks.views.detail import StackCommitsView, StackDetailView
from makeitso.stacks.views.new import NewStackView

bp = Blueprint("stacks", __name__)

bp.add_url_rule("/new", view_func=NewStackView.as_view("new_stack"))
bp.add_url_rule("/<int:stack_id>", view_func=StackDetailView.as_view("detail"))
bp.add_url_rule("/<int:stack_id>/commits", view_func=StackCommitsView.as_view("commits"))
bp.add_url_rule("/<int:stack_id>/delete", view_func=DeleteStackView.as_view("delete"))
