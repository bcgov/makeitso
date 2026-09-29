from flask_wtf import FlaskForm
from github import GithubException
from wtforms import Field, StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError

from makeitso.github import GitHubRepo, client_for_current_user


class NewStackForm(FlaskForm):
    organization = StringField("Github organization", validators=[DataRequired()])
    repository = StringField("Github repository name", validators=[DataRequired()])
    branch = StringField("Git branch to track", validators=[DataRequired()])
    environment = StringField("Environment", validators=[DataRequired()])
    submit = SubmitField("Create Stack")

    # WTForms runs validate_<field> methods after that field's own validators
    def validate_repository(self, field: Field) -> None:
        # Nothing to check yet if the org is missing
        if self.organization.errors:
            return
        try:
            exists = self._github_repo().exists()
        except GithubException as exc:
            raise ValidationError(
                f"Could not check the repository on GitHub ({exc.status})"
            ) from exc
        if not exists:
            raise ValidationError(f"Repository {self.organization.data}/{field.data} was not found")

    def validate_branch(self, field: Field) -> None:
        if self.organization.errors or self.repository.errors:
            return
        try:
            has_branch = self._github_repo().has_branch(field.data)
        except GithubException as exc:
            raise ValidationError(f"Could not check the branch on GitHub ({exc.status})") from exc
        if not has_branch:
            raise ValidationError(f"Branch {field.data} was not found")

    def _github_repo(self) -> GitHubRepo:
        return GitHubRepo(
            client_for_current_user(), f"{self.organization.data}/{self.repository.data}"
        )
