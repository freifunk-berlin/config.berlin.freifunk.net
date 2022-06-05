# coding: utf-8
from flask import current_app
from app.wizard import get_api
from .tables import metadata as db_metadata, t_usr, t_ip
from sqlalchemy import create_engine
from app.nipap import NipapApi
from ipaddress import IPv4Network, collapse_addresses
from pynipap import NipapDuplicateError


def legacy_import(db_user, db_pass, db_host, db_name):
    # init and connect to legacy db
    db_uri = 'postgresql://%s:%s@%s/%s' % (db_user, db_pass, db_host, db_name)
    db_engine = create_engine(db_uri, convert_unicode=True)
    db_metadata.bind = db_engine
    db_con = db_engine.connect()

    users = t_usr.select().execute().fetchall()
    users_len = len(users)
    for i, user in enumerate(users):
        print(("\n\n[%d/%d] %s <%s>..." % (i, users_len, user[1], user[3])))
        rows = t_ip.select(t_ip.c.user_id == user[0]).execute().fetchall()
        networks = [IPv4Network(str(r[1])) for r in rows]
        collapsed = [c.compressed for c in collapse_addresses(networks)]
        for c in collapsed:
            pool = current_app.config['API_POOL_LEGACY']
            try:
                data = {
                    'description': user[1],
                    'tags': ['legacy', 'imported']
                }
                get_api().create_prefix_by_cidr(c, user[3], pool, data)

                print(("\t* %s saved." % c))
            except NipapDuplicateError:
                print(("\t* %s already exists." % c))


def legacy_get_mails(db_user, db_pass, db_host, db_name):
    # init and connect to legacy db
    db_uri = 'postgresql://%s:%s@%s/%s' % (db_user, db_pass, db_host, db_name)
    db_engine = create_engine(db_uri, convert_unicode=True)
    db_metadata.bind = db_engine
    db_con = db_engine.connect()

    # retrieves all emails
    users = t_usr.select().execute().fetchall()
    return (user[3] for user in users)
