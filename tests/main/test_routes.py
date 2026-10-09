from tests.factories import StackFactory


class TestNavbar:
    def test_logged_in_shows_account_menu(self, client):
        with client.session_transaction() as session:
            session["user"] = {
                "login": "octocat",
                "name": "Mona Lisa",
                "avatar_url": "https://avatars.example/octocat",
                "html_url": "https://github.com/octocat",
            }

        response = client.get("/")

        assert b'src="https://avatars.example/octocat"' in response.data
        assert b"Mona Lisa" in response.data
        assert b'href="https://github.com/octocat"' in response.data
        assert b"@octocat" in response.data
        assert b'action="/logout"' in response.data

    def test_logged_out_has_no_account_menu(self, client):
        response = client.get("/")

        assert b"Account menu" not in response.data
        assert b'action="/logout"' not in response.data


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
