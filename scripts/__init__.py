from manage import manager
from app.exts import db
from .legacy_importer import legacy_import, legacy_get_mails
from .cleanup import delete_unconfirmed_requests, delete_orphaned_prefixes
from .mail import get_mail_addresses_for_pools, send_mail_to_pools

@manager.command
def resetdb():
    db.drop_all()
    db.create_all()


@manager.command
@manager.option('-h', '--hours', help='hours after a request should be deleted')
def remove_unconfirmed_requests(hours = 48):
    delete_unconfirmed_requests(int(hours))

@manager.command
def remove_orphaned_prefixes():
    delete_orphaned_prefixes()

@manager.command
@manager.option('-u', '--user', help='database user')
@manager.option('-p', '--passwort', help='database passwort')
@manager.option('-h', '--host', help='database host (including port)')
@manager.option('-d', '--database', help='database name')
def import_legacy(user, password, host, database):
    legacy_import(user, password, host, database)


@manager.command
@manager.option('-u', '--user', help='database user')
@manager.option('-p', '--passwort', help='database passwort')
@manager.option('-h', '--host', help='database host (including port)')
@manager.option('-d', '--database', help='database name')
def get_mails_for_legacy(user, password, host, database):
    for email in legacy_get_mails(user, password, host, database):
        print(email)


@manager.command
@manager.option('-p', '--pools', help='pools separated by coma')
def mail_addresses_for_pools(pools):
    for email in get_mail_addresses_for_pools(pools):
        print(email)


@manager.command
@manager.option('-p', '--pools', help='pools separated by coma')
@manager.option('-s', '--subject', help='subject')
@manager.option('-t', '--template', help='template file')
@manager.option('-d', '--delay', help='delay between emails')
def mail(pools, subject, template_file, delay = 0.5):
    with open(template_file, 'r') as f:
        template = f.read()

    send_mail_to_pools(pools, subject, template, delay)
