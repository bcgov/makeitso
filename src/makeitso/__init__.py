import os

from flask import Flask

from makeitso.config import configs
from makeitso.extensions import bootstrap, db, migrate, oauth, rq


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("MAKEITSO_ENV")
    if config_name not in configs:
        raise RuntimeError(f"MAKEITSO_ENV must be one of {list(configs)}, got {config_name!r}")

    app = Flask(__name__)
    app.config.from_object(configs[config_name])

    if not app.config["SECRET_KEY"]:
        raise RuntimeError(f"SECRET_KEY is not set (MAKEITSO_ENV={config_name})")

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
