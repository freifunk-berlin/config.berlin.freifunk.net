# -*- coding: utf-8 -*-

from flask_script import Manager
from flask_migrate import MigrateCommand
from app import create_app
from app.exts import db

# create app
app = create_app()
manager = Manager(app)

# add manager scripts
manager.add_command('db', MigrateCommand)
from scripts import *

if __name__ == '__main__':
    manager.run()
