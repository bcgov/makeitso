import pytest

from makeitso import create_app
from makeitso.extensions import db


# One app and one set of tables for the whole test run
@pytest.fixture(scope="session")
def app():
    app = create_app("pytest")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(app):
    client = app.test_client()

    with client.session_transaction() as session:
        session["user"] = {"login": "testuser", "avatar_url": ""}

    return client


# Empty every table after each test, so tests don't see each other's rows
@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    db.session.rollback()
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
