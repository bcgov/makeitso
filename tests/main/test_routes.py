import pytest

from makeitso.extensions import db
from makeitso.models.stack import Stack


@pytest.fixture
def stack():
    stack = Stack(
        organization="bcgov",
        repository="secret-repo",
        branch="develop",
        name="secret-repo-dev",
        environment="dev",
    )
    db.session.add(stack)
    db.session.commit()
    return stack


def test_healthz(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_index_logged_out_hides_stacks(client, stack):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Log in with GitHub" in response.data
    assert b"secret-repo" not in response.data


def test_index_logged_in_lists_stacks(client, stack):
    with client.session_transaction() as session:
        session["user"] = {"login": "octocat", "avatar_url": ""}

    response = client.get("/")

    assert response.status_code == 200
    assert b"bcgov/secret-repo" in response.data
