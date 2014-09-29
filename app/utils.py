# -*- coding: utf-8 -*-

import string
from random import choice
from functools import wraps
from itertools import chain
from flask import session, redirect, url_for, render_template, g, current_app
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


def session_keys_needed(keys, endpoint):
    def session_keys_needed_(f):
        @wraps(f)
        def session_keys_needed__(*args, **kwargs):
            for key in keys:
                if key not in session:
                    return redirect(url_for(endpoint))
            return f(*args, **kwargs)
        return session_keys_needed__
    return session_keys_needed_


def gen_random_hash(length):
    digits = string.ascii_letters + string.digits
    return ''.join(choice(digits) for x in range(length))


def send_email(email, router, ips, url):
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
