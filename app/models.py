# -*- coding: utf-8 -*-

from datetime import datetime
from flask import current_app
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import Email, AnyOf, Length
from itsdangerous import URLSafeTimedSerializer
from .exts import db
from .utils import gen_random_hash, router_db_get_entry
from .wizard import get_api

class IPRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    hostname = db.Column(db.String(120), unique=True)
    router_id = db.Column(db.String(120))
    verified = db.Column(db.Boolean(), default=False)
    token  = db.Column(db.String(128), unique=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)

    def __init__(self, hostname, email, router_id):
        self.hostname = hostname
        self.email = email
        self.router_id = router_id
        self.token = gen_random_hash(32)


    def verify_signed_token(self, signed_token, timeout = 3600):
        secret = current_app.config['SECRET_KEY']
        serializer = URLSafeTimedSerializer(secret, " ".join(self.ips))
        return self.token == serializer.loads(signed_token, max_age=timeout)

    def gen_signed_token(self):
        secret = current_app.config['SECRET_KEY']
        serializer = URLSafeTimedSerializer(secret, " ".join(self.ips))
        return serializer.dumps(self.token)

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


error_msg = u'Falsch. Wie heisst die Hauptstadt Deutschlands?'
v = AnyOf(('Berlin', 'berlin'), message=error_msg)
class EmailForm(Form):
    email = StringField('Email', validators=[Email()])
    hostname = StringField('Name', validators=[Length(4,32)])
    captcha = StringField('Captcha', validators=[v])

    @validates('hostname')
    def validate_hostname(self, field):
        r = IPRequest.query.filter_by(hostname=field.data).count()
        if r > 0:
            raise ValueError('Standortname bereits vergeben.')
        return field
