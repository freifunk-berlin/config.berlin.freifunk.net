# coding: utf-8
from flask import current_app
from app.wizard import get_api
from tables import metadata as db_metadata, t_usr, t_ip
from sqlalchemy import create_engine
from app.nipap import NipapApi
from ipaddress import IPv4Network, collapse_addresses
from pynipap import NipapDuplicateError

def import_db(db_user, db_pass, db_host, db_name):
    # init and connect to legacy db
    db_uri = 'postgresql://%s:%s@%s/%s' % (db_user, db_pass, db_host, db_name)
    db_engine = create_engine(db_uri, convert_unicode=True)
    db_metadata.bind = db_engine
    db_con = db_engine.connect()

    users = t_usr.select().execute().fetchall()
    for user in users:
        print("\n\n%s <%s>..." % (user[1], user[3])),
        rows = t_ip.select(t_ip.c.user_id == user[0]).execute().fetchall()
        networks = [IPv4Network(unicode(r[1])) for r in rows]
        collapsed = [c.compressed for c in collapse_addresses(networks)]
        for c in collapsed:
            pool = current_app.config['API_POOL_LEGACY']
            try: 
                get_api().create_prefix_by_prefix(c, user[1], user[3], pool)
            except NipapDuplicateError:
                pass

        print("\t%s saved." % ",".join(collapsed))

