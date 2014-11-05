# -*- coding: utf-8 -*-

import string
from random import choice
from functools import wraps
from itertools import chain
from flask import redirect, url_for, render_template, g, current_app
from flask.ext.mail import Message
from .nipap import NipapApi
from .exts import mail


def get_api():
    api = getattr(g, '_api', None)
    if api is None:
        api = g._api = NipapApi(current_app.config['APP_ID'])
        uri = 'http://%s:%s@%s' % (current_app.config['API_USER'],
                  current_app.config['API_PASS'], current_app.config['API_HOST'])
        g._api.connect(uri)

    return api


def request_create(name, email, prefixes_v4, prefixes_v6, router_id = None):
    """Process the data gathered from the input form, by performing all steps
       needed to assign enough ips for the router model of the user. """

    from .models import db, IPRequest
    try:
        # add new request to database
        r = IPRequest(name, email, router_id)
        db.session.add(r)
        db.session.commit()

        # allocate IPs in NIPAP
        if prefixes_v4:
            for (pool, prefix_len) in prefixes_v4:
                get_api().allocate_ips(pool, r.id, r.email, name, prefix_len, 4)

        if prefixes_v6:
            for (pool, prefix_len) in prefixes_v6:
                get_api().allocate_ips(pool, r.id, r.email, name, prefix_len, 6)

    except:
        db.session.rollback()
        raise
    finally:
        db.session.close()

    return r


def gen_random_hash(length):
    digits = string.ascii_letters + string.digits
    return ''.join(choice(digits) for x in range(length))



def send_email(recipient, subject, template, data):
    body = render_template(template, **data)
    msg = Message(subject, sender=current_app.config['MAIL_FROM'],
              recipients=[recipient], body = body)
    return mail.send(msg)


def _get_firmwares_for_router(base_url, data):
    firmware_id = data['id']
    if 'firmware_no_suffix' in data and data['firmware_no_suffix']:
        firmware_id = firmware_id[:-1]

    prefix =  "%s/openwrt-%s-%s" % (data['target'], '-'.join(firmware_id), data['fs'])
    return dict([(x, "%s/%s-%s.bin" % (base_url, prefix, x)) for x in ['sysupgrade', 'factory']])


def router_db_get_entry(router_db, router_id, base_url = None):
    if router_id is None:
        return None

    cursor = router_db
    data = dict([(k,v) for k,v in cursor.items() if k != 'entries'])
    keys = router_id.split('/')
    for n in keys:
        cursor = cursor['entries'][n]

        # merge data
        for k,v in cursor.items():
            if k != 'entries':
                data[k] = v

    data['target'] = keys[0]
    data['id'] = keys
    data['firmwares'] = _get_firmwares_for_router(base_url, data)

    return data


def router_db_has_entry(router_db, router_id):
    try:
        return router_db_get_entry(router_db, router_id)
    except KeyError:
        return False


def router_db_list(router_db):
    for target, subtargets  in sorted(router_db['entries'].items()):
        for subtarget, profiles in sorted(subtargets['entries'].items()):
            for profile, entries in sorted(profiles['entries'].items()):
                for device, data in sorted(entries['entries'].items()):
                    name = "%s/%s/%s/%s" % (target, subtarget, profile, device)
                    yield (name, data)
