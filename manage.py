# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand
from app import create_app
from app.exts import db

app = create_app()

manager = Manager(app)
manager.add_command('db', MigrateCommand)

@manager.command
def resetdb():
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    manager.run()
