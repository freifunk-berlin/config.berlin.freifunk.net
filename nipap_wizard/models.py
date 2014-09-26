# -*- coding: utf-8 -*-

from flask import current_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import Email, AnyOf
from itsdangerous import URLSafeTimedSerializer
from .exts import db
from utils import gen_random_hash

class IPRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    ips = db.Column(db.String(120))
    router_id = db.Column(db.String(120))
    verified = db.Column(db.Boolean(), default=False)
    token  = db.Column(db.String(128), unique=True)

    def __init__(self, email, ips, router_id):
        self.email = email
        self.ips = ips
        self.router_id = router_id
        self.token = gen_random_hash(32)


    def verify_signed_token(self, signed_token, timeout = 3600):
        secret = current_app.config['SECRET_KEY']
        serializer = URLSafeTimedSerializer(secret, self.ips)
        return self.token == serializer.loads(signed_token, max_age=timeout)

    def gen_signed_token(self):
        secret = current_app.config['SECRET_KEY']
        serializer = URLSafeTimedSerializer(secret, self.ips)
        return serializer.dumps(self.token)

    def __repr__(self):
        return '<IPRequest %r>' % self.email


error_msg = u'Falsch. Wie heisst die Hauptstadt Deutschlands?'
v = AnyOf(('Berlin', 'berlin'), message=error_msg)
class EmailForm(Form):
    email = StringField('Email', validators=[Email()])
    captcha = StringField('Captcha', validators=[v])
