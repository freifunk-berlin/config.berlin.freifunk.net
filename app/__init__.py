# -*- coding: utf-8 -*-

from flask import Flask, render_template
from .wizard import wizard
from .exts import db, mail, migrate
from .expert import expert
from .summary import summary
from .main import main


def create_app(config=None):
    """Creates the Flask app."""
    app = Flask(__name__)

    configure_app(app)
    configure_extensions(app)
    configure_error_handlers(app)

    for blueprint in [main, wizard, expert, summary]:
        app.register_blueprint(blueprint)

    return app


def configure_app(app):
    # http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('../default.cfg')
    app.config.from_pyfile('../config.cfg', silent=True)

    # http://flask.pocoo.org/docs/0.10/errorhandling/
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(app.config['LOG_FILE_PATH'])
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
            '[in %(pathname)s:%(lineno)d]'))
        app.logger.addHandler(file_handler)


def configure_extensions(app):
    # flask-sqlalchemy
    db.init_app(app)

    # flask-mail
    mail.init_app(app)

    # flask-migrate
    migrate.init_app(app, db)


def configure_error_handlers(app):
    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def errorhandler(e):
        return render_template('error.html', error=e), e.code
