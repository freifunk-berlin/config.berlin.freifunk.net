# -*- coding: utf-8 -*-

import string
from random import choice
from functools import wraps
from itertools import chain
from flask import session, redirect, url_for, render_template
from flask.ext.mail import Message
from .exts import mail


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
