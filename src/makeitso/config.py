import os
import urllib.parse

from flask.cli import load_dotenv

load_dotenv()


class Config:
    # Production-safe defaults shared by every environment

    SECRET_KEY = os.environ.get("SECRET_KEY")
    # Send the session cookie over HTTPS only
    SESSION_COOKIE_SECURE = True
    # Hide the session cookie from JavaScript
    SESSION_COOKIE_HTTPONLY = True
    # Don't send the session cookie on cross-site requests, except top-level navigation
    SESSION_COOKIE_SAMESITE = "Lax"

    BOOTSTRAP_SERVE_LOCAL = True
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"

    GITHUB_CLIENT_ID = os.environ.get("GITHUB_APP_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_APP_CLIENT_SECRET")

    DB_USER = os.environ.get("DB_USER", "postgres")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{urllib.parse.quote(str(os.environ.get('DB_PASSWORD')))}"
        f"@{os.environ.get('DB_HOST', '127.0.0.1')}:{os.environ.get('DB_PORT', '5432')}"
        f"/{os.environ.get('DB_NAME', 'mis')}"
    )


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev"
    # Local dev runs on plain http


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test"

class LocalConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "local"
    # Local dev runs on plain http
    SESSION_COOKIE_SECURE = False


configs = {
    "prod": ProductionConfig,
    "dev": DevelopmentConfig,
    "test": TestingConfig,
    "local": LocalConfig,
}
