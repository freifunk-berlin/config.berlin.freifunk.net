# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_mail import Mail

mail = Mail()

from flask_migrate import Migrate

migrate = Migrate()
