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


class NipapApi:
    def __init__(self, app_id, api_user, api_pass, api_host):
        self.api = Api(app_id)
        self.api.connect('http://%s:%s@%s' % (api_user, api_pass, api_host))

    def allocate_ips(self, pool, request_id, num, prefix_len = None, prefix_type='reservation'):
        ips = []
        data = {'external_key' : request_id}
        for i in range(num):
            p = self.api.create_prefix_from_pool(pool, prefix_type, prefix_len,
                    data=data)
            ips.append(p)

        return ips

    def activate_ips(self, request_id):
        for p in self.api.get_prefixes_by_key(request_id):
            p.type = 'assignment'
            p.save()

    def get_prefixes_by_id(self, prefix_id):
        prefixes = self.api.get_prefixes_by_key(prefix_id)
        return [p.prefix for p in prefixes]
