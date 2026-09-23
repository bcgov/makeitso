from dotenv import load_dotenv
from flask import Flask

from makeitso.config import Config
from makeitso.extensions import bootstrap, db, migrate, oauth, rq


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    rq.init_app(app)
    oauth.init_app(app)

    from makeitso import models  # noqa: F401  (registers the models with SQLAlchemy)
    from makeitso.auth import bp as auth_bp
    from makeitso.deploys import bp as deploys_bp
    from makeitso.main import bp as main_bp
    from makeitso.stacks import bp as stacks_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/")
    app.register_blueprint(stacks_bp, url_prefix="/stacks")
    app.register_blueprint(deploys_bp, url_prefix="/deploys")

    return app
