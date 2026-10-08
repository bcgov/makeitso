from tests.factories import StackFactory


class TestHealthz:
    def test_ok(self, client):
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json == {"status": "ok"}


class TestIndex:
    def test_logged_out_hides_stacks(self, client):
        stack = StackFactory.create_sync()

        response = client.get("/")

        assert response.status_code == 200
        assert b"Log in with GitHub" in response.data
        assert stack.repository.encode() not in response.data

    def test_logged_in_lists_stacks(self, client, login):
        stack = StackFactory.create_sync()
        login()

        response = client.get("/")

        assert response.status_code == 200
        assert f"{stack.organization}/{stack.repository}".encode() in response.data
