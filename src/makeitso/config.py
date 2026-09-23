import os
import urllib.parse

from flask.cli import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key_here")
    BOOTSTRAP_SERVE_LOCAL = True
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    DB_USER = os.environ.get("DB_USER", "postgres")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{urllib.parse.quote(str(os.environ.get('DB_PASSWORD')))}"
        f"@{os.environ.get('DB_HOST', '127.0.0.1')}:{os.environ.get('DB_PORT', '5432')}"
        f"/{os.environ.get('DB_NAME', 'mis')}"
    )
