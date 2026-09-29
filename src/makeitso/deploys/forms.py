from flask_wtf import FlaskForm
from github import GithubException
from wtforms import Field, StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError

from makeitso.extensions import db
from makeitso.github import GitHubRepo, client_for_current_user
from makeitso.models.stack import Stack


class NewDeployForm(FlaskForm):
    submit = SubmitField("Create Deploy")
