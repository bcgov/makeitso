from unittest.mock import MagicMock, patch

from makeitso.extensions import db
from makeitso.models.stack import Stack


def test_new(logged_in_client):
    response = logged_in_client.get("/stacks/new")
    assert response.status_code == 200

    assert b"New stack" in response.data
    assert b"Create stack" in response.data


def test_new_create(
    logged_in_client,
):
    with (
        patch("makeitso.stacks.views.new.enqueue_sync") as mock_enqueue_sync,
        patch("flask_wtf.form.FlaskForm.validate_on_submit") as mock_validate,
    ):
        mock_validate.return_value = True

        data = {
            "organization": "test-org",
            "repository": "test-repo",
            "branch": "test-branch",
            "environment": "testing-test",
            "continuous_deploy": False,
        }

        response = logged_in_client.post("/stacks/new", data=data)

        new_stack: Stack = db.session.execute(
            db.select(Stack).filter_by(repository="test-repo")
        ).scalar_one()

        Stack.repository

        assert response.status_code == 302
        assert response.headers["Location"] == f"/stacks/{new_stack.id}"
