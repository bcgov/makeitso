import sqlalchemy as sa
from flask import flash, redirect, render_template, url_for
from flask.views import MethodView

from makeitso.auth.decorators import requires_auth
from makeitso.extensions import db
from makeitso.models.stack import Stack
from makeitso.models.stack_env_var import StackEnvVar
from makeitso.stacks.forms import EnvVarForm, LockForm


class StackSettingsView(MethodView):
    """The stack's lock and its env vars, passed to its deploy script"""

    @requires_auth
    def get(self, stack_id: int):
        stack = Stack.active_or_404(stack_id)
        return _render(stack, _lock_form(stack), _env_var_form())

    @requires_auth
    def post(self, stack_id: int):
        """Add an env var, or change its value if the key already exists"""
        stack = Stack.active_or_404(stack_id)
        form = _env_var_form()
        if not form.validate_on_submit():
            # Back to the page with the errors and what was typed
            return _render(stack, _lock_form(stack), form)
        existing = db.session.scalar(
            sa.select(StackEnvVar).where(
                StackEnvVar.stack_id == stack.id, StackEnvVar.key == form.key.data
            )
        )
        if existing is not None:
            existing.value = form.value.data
        else:
            db.session.add(StackEnvVar(stack_id=stack.id, key=form.key.data, value=form.value.data))
        db.session.commit()
        return redirect(url_for("stacks.settings", stack_id=stack.id))


class StackLockView(MethodView):
    """A lock stops new deploys; a deploy that's already running isn't affected"""

    @requires_auth
    def post(self, stack_id: int):
        stack = Stack.active_or_404(stack_id)
        form = _lock_form(stack)
        if not form.validate_on_submit():
            return _render(stack, form, _env_var_form())
        stack.locked = form.locked.data
        stack.lock_reason = form.lock_reason.data if stack.locked else None
        db.session.commit()
        flash("Stack locked" if stack.locked else "Stack unlocked", "success")
        return redirect(url_for("stacks.settings", stack_id=stack.id))


class DeleteEnvVarView(MethodView):
    @requires_auth
    def post(self, stack_id: int, env_var_id: int):
        stack = Stack.active_or_404(stack_id)
        env_var = db.first_or_404(
            sa.select(StackEnvVar).where(
                StackEnvVar.id == env_var_id, StackEnvVar.stack_id == stack.id
            )
        )
        db.session.delete(env_var)
        db.session.commit()
        return redirect(url_for("stacks.settings", stack_id=stack.id))


def _lock_form(stack: Stack) -> LockForm:
    # Filled from the stack, unless the form was just posted
    return LockForm(obj=stack, prefix="lock")


def _env_var_form() -> EnvVarForm:
    return EnvVarForm(prefix="env")


def _render(stack: Stack, lock_form: LockForm, env_var_form: EnvVarForm) -> str:
    env_vars = db.session.scalars(
        sa.select(StackEnvVar).where(StackEnvVar.stack_id == stack.id).order_by(StackEnvVar.key)
    ).all()
    return render_template(
        "stacks/settings.html",
        stack=stack,
        env_vars=env_vars,
        lock_form=lock_form,
        env_var_form=env_var_form,
    )
