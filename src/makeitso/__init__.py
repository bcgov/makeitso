import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

from makeitso.extensions import bootstrap

db = SQLAlchemy()
migrate = Migrate()

def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config["BOOTSTRAP_SERVE_LOCAL"] = True

    bootstrap.init_app(app)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    
    from makeitso import models

    from makeitso.auth import bp as auth_bp
    from makeitso.deploys import bp as deploys_bp
    from makeitso.main import bp as main_bp
    from makeitso.stacks import bp as stacks_bp

    app.register_blueprint(main_bp)
