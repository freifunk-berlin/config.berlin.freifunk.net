# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand
from app import create_app
from app.exts import db
from scripts.legacy_importer import import_db

app = create_app()

manager = Manager(app)
manager.add_command('db', MigrateCommand)

@manager.command
def resetdb():
    db.drop_all()
    db.create_all()

@manager.command
@manager.option('-u', '--user', help='database user')
@manager.option('-p', '--passwort', help='database passwort')
@manager.option('-h', '--host', help='database host (including port)')
@manager.option('-d', '--database', help='database name')
def import_legacy(user, password, host, database):
    import_db(user, password, host, database)

if __name__ == '__main__':
    manager.run()
