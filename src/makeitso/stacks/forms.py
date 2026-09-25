from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class NewStackForm(FlaskForm):
    org = StringField("Github organization", validators=[DataRequired()])
    repo = StringField("Github repository name", validators=[DataRequired()])
    branch = StringField("Git branch to track", validators=[DataRequired()])

    environment = StringField("Environment", validators=[DataRequired()])

    submit = SubmitField("Create Stack")
