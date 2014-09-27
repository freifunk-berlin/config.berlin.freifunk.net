# -*- coding: utf-8 -*-

from flask import Flask
from .wizard import wizard
from .exts import db, mail, migrate
from .wizard import wizard

def create_app(config=None):
    """Creates the Flask app."""
    app = Flask(__name__)

    configure_app(app)
    configure_extensions(app)

    for blueprint in [wizard]:
        app.register_blueprint(blueprint)

    return app


def configure_app(app):
    # http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('../default.cfg')
    app.config.from_pyfile('../config.cfg', silent=True)


def configure_extensions(app):
    # flask-sqlalchemy
    db.init_app(app)

    # flask-mail
    mail.init_app(app)

    # flask-migrate
    migrate.init_app(app, db)

