import pytest
from fakeredis import FakeRedis
from rq import Queue

from makeitso import create_app
from makeitso.extensions import db
from makeitso.redis_queue import QUEUE_NAMES


# One app and one set of tables for the whole test run.
# A request context (not just an app context), so tests can build URLs with url_for
@pytest.fixture(scope="session")
def app():
    app = create_app("pytest")
    with app.test_request_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# Empty every table after each test, so tests don't see each other's rows
@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    db.session.rollback()
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


# An empty in-memory Redis for each test, so no test reaches a real one
@pytest.fixture(autouse=True)
def fake_redis(app, monkeypatch):
    connection = FakeRedis()
    queues = {name: Queue(name, connection=connection) for name in QUEUE_NAMES}
    monkeypatch.setitem(app.extensions, "rq_queues", queues)
    return connection


# Log the test client in as a GitHub user: login() or login("someone")
@pytest.fixture
def login(client):
    def login(user: str = "octocat") -> None:
        with client.session_transaction() as session:
            session["user"] = {"login": user, "avatar_url": ""}
            session["token"] = {"access_token": "test-token"}

    return login
