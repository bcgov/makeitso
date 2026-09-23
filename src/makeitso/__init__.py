from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config
from makeitso import redis_queue
from makeitso.config import Config
from makeitso.extensions import bootstrap

db = SQLAlchemy()
migrate = Migrate()


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    bootstrap.init_app(app)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    redis_queue.init_app(app)

    from makeitso import models  # noqa: F401  (registers the models with SQLAlchemy)
    from makeitso.auth import bp as auth_bp
    from makeitso.deploys import bp as deploys_bp
    from makeitso.main import bp as main_bp
    from makeitso.stacks import bp as stacks_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(stacks_bp, url_prefix="/stacks")
    app.register_blueprint(deploys_bp, url_prefix="/deploys")

    return app
