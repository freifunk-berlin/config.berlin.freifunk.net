# -*- coding: utf-8 -*-

import string
from random import choice
from functools import wraps
from itertools import chain
from flask import session, redirect, url_for, render_template
from flask.ext.mail import Message
from .exts import mail
from nipap import Api


def session_key_needed(key, endpoint):
    def session_key_needed_(f):
        @wraps(f)
        def session_key_needed__(*args, **kwargs):
            if key not in session:
                return redirect(url_for(endpoint))
            return f(*args, **kwargs)
        return session_key_needed__
    return session_key_needed_


def gen_random_hash(length):
    digits = string.ascii_letters + string.digits
    return ''.join(choice(digits) for x in range(length))


def allocate_ips(app_id, api_user, api_pass, api_host, pool, num, prefix_len = None, prefix_type='reservation'):
    api = Api(app_id)
    api.connect('http://%s:%s@%s' % (api_user, api_pass, api_host))

    ips = []
    for i in range(num):
        ips.append(api.create_prefix_from_pool(pool, prefix_type, prefix_len))

    return ips


def activate_ips(app_id, api_user, api_pass, api_host, ips):
    api = Api(app_id)
    api.connect('http://%s:%s@%s' % (api_user, api_pass, api_host))
    success = []
    for ip in ips:
        prefix = api.get_prefix_by_prefix(ip)
        if prefix is not None:
            prefix.type = 'assignment'
            prefix.save()
            success.append(True)
        else:
            success.append(False)

    return success


def send_email(api_params, email, router, ips, url):
    body = render_template('email.txt',
        router = router['data']['name'],
        ips = ips,
        url = url,
        domain = 'ip.berlin.freifunk.net',
    )

    msg = Message("Your confirmation is needed!",
              sender="no-reply@ip.berlin.freifunk.net",
              recipients=[email],
              body = body)
    mail.send(msg)

