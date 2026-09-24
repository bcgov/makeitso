from authlib.integrations.flask_client import OAuth
from flask_bootstrap import Bootstrap5
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from makeitso.redis_queue import RedisQueue

bootstrap = Bootstrap5()
db = SQLAlchemy()
migrate = Migrate()
job_queue = RedisQueue()

oauth = OAuth()
# Client ID and secret are read from app.config (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)
oauth.register(
    "github",
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "openid email profile"},
)
