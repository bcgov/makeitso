from flask_wtf import FlaskForm
from github import GithubException
from wtforms import BooleanField, Field, StringField, TextAreaField
from wtforms.validators import DataRequired, Regexp, ValidationError

from makeitso.extensions import db
from makeitso.github import GitHubRepo, client_for_current_user
from makeitso.models.stack import Stack


class NewStackForm(FlaskForm):
    organization = StringField(
        "Organization", description="The GitHub user or organization", validators=[DataRequired()]
    )
    repository = StringField(
        "Repository", description="The repository to deploy", validators=[DataRequired()]
    )
    branch = StringField(
        "Branch", description="Commits on this branch can be deployed", validators=[DataRequired()]
    )
    environment = StringField(
        "Environment",
        description="Picks the engage file (e.g. engage.dev.yaml); scripts get it as ENVIRONMENT",
        validators=[DataRequired()],
    )
    continuous_deploy = BooleanField("Enable Continuous Deployment")

    # WTForms runs validate_<field> methods after that field's own validators
    def validate_repository(self, field: Field) -> None:
        # Nothing to check yet if the org is missing
        if self.organization.errors:
            return
        github_repo = self._github_repo()
        try:
            exists = github_repo.exists()
        except GithubException as exc:
            raise ValidationError(
                f"Could not check the repository on GitHub ({exc.status})"
            ) from exc
        if not exists:
            raise ValidationError(f"Repository {self.organization.data}/{field.data} was not found")
        # Save the names as GitHub spells them, so "OrG/FoO" and "oRG/fOo" are the same stack
        self.organization.data = github_repo.owner
        field.data = github_repo.name

    def validate_branch(self, field: Field) -> None:
        if self.organization.errors or self.repository.errors:
            return
        try:
            has_branch = self._github_repo().has_branch(field.data)
        except GithubException as exc:
            raise ValidationError(f"Could not check the branch on GitHub ({exc.status})") from exc
        if not has_branch:
            raise ValidationError(f"Branch {field.data} was not found")

    def validate_environment(self, field: Field) -> None:
        # Needs the repo's names as GitHub spells them, set once the repository check passed
        if self.organization.errors or self.repository.errors:
            return
        existing = db.session.scalar(
            Stack.active().where(
                Stack.organization == self.organization.data,
                Stack.repository == self.repository.data,
                Stack.environment == field.data,
            )
        )
        if existing is not None:
            raise ValidationError(
                f"A stack for {self.organization.data}/{self.repository.data} "
                f"({field.data}) already exists"
            )

    def _github_repo(self) -> GitHubRepo:
        return GitHubRepo(
            client_for_current_user(), f"{self.organization.data}/{self.repository.data}"
        )


def _strip(value: str | None) -> str | None:
    return value.strip() if value else value


class LockForm(FlaskForm):
    locked = BooleanField("Lock this stack")
    lock_reason = TextAreaField(
        "Reason", description="Shown on the stack page. Needed when locking.", filters=[_strip]
    )

    def validate_lock_reason(self, field: Field) -> None:
        if self.locked.data and not field.data:
            raise ValidationError("Give a reason for locking the stack")


class EnvVarForm(FlaskForm):
    key = StringField(
        "Name",
        filters=[_strip],
        validators=[
            DataRequired(),
            # What a shell accepts: letters, digits and _, not starting with a digit
            Regexp(
                r"^[A-Za-z_][A-Za-z0-9_]*$",
                message="Letters, digits and _, not starting with a digit",
            ),
        ],
    )
    value = StringField("Value")
