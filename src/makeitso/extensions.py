import os

from authlib.integrations.flask_client import OAuth
from flask_bootstrap import Bootstrap5
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from makeitso.redis_queue import RedisQueue

bootstrap = Bootstrap5()
db = SQLAlchemy()
migrate = Migrate()
rq = RedisQueue()

oauth = OAuth()
oauth.register(
    "github",
    client_id=os.environ.get("GITHUB_APP_CLIENT_ID"),
    client_secret=os.environ.get("GITHUB_APP_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "openid email profile"},
)
