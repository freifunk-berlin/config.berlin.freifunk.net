# -*- coding: utf-8 -*-

from datetime import datetime
from flask import current_app, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from itsdangerous import URLSafeTimedSerializer
from .exts import db
from .utils import gen_random_hash, router_db_get_entry, send_email
from .wizard import get_api

class IPRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    name = db.Column(db.String(120), unique=True)
    router_id = db.Column(db.String(120))
    verified = db.Column(db.Boolean(), default=False)
    token  = db.Column(db.String(128), unique=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)

    def __init__(self, name, email, router_id):
        self.name = name
        self.email = email
        self.router_id = router_id
        self.token = gen_random_hash(32)


    def activate(self, signed_token, timeout = 3600):
        if not self._verify(signed_token, 'activation', timeout):
            raise BadRequest(u"Dein Token ist ungültig oder bereits abgelaufen")

        get_api().activate_ips(self.id)
        self.verified = True

        db.session.add(self)
        db.session.commit()

    def viewable(self, signed_token):
        if not self._verify(signed_token, 'config'):
            raise BadRequest(u"Dein Token ist ungültig")


    def destroy(self, signed_token):
        if not self._verify(signed_token, 'destroy'):
            raise BadRequest(u"Dein Token ist ungültig!")

        get_api().delete_prefixes_by_id(self.id)
        db.session.delete(self)
        db.session.commit()


    def _verify(self, signed_token, salt, timeout = None):
        serializer = URLSafeTimedSerializer(self.token, salt)
        return self.name == serializer.loads(signed_token, max_age=timeout)


    def _gen_signed_token(self, salt):
        serializer = URLSafeTimedSerializer(self.token, salt)
        return serializer.dumps(self.name)


    @property
    def token_activation(self):
        return self._gen_signed_token('activation')

    @property
    def token_config(self):
        return self._gen_signed_token('config')


    @property
    def token_destroy(self):
        return self._gen_signed_token('destroy')


    @property
    def ips(self):
        return get_api().get_prefixes_for_id(self.id)


    @property
    def ips_pretty(self):
        ips = {'mesh':[], 'hna':[]}
        for ip in self.ips:
            if ip.endswith('/32'):
                ips['mesh'].append(ip.replace('/32', ''))
            else:
                ips['hna'].append(ip)
        return ips


    @property
    def router(self):
        router_db = current_app.config['ROUTER_DB']
        base_url = current_app.config['FIRMWARE_BASE_URL']
        return router_db_get_entry(router_db, self.router_id, base_url)


    def __repr__(self):
        return '<IPRequest %r>' % self.email
