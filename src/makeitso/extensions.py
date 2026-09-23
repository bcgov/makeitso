from flask_bootstrap import Bootstrap5
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from makeitso.redis_queue import RedisQueue

bootstrap = Bootstrap5()
db = SQLAlchemy()
migrate = Migrate()
rq = RedisQueue()
