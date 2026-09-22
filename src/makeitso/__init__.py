from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from makeitso.auth import bp as auth_bp
    from makeitso.deploys import bp as deploys_bp
    from makeitso.main import bp as main_bp
    from makeitso.stacks import bp as stacks_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(stacks_bp, url_prefix="/stacks")
    app.register_blueprint(deploys_bp, url_prefix="/deploys")

    return app
