# -*- coding: utf-8 -*-

from datetime import datetime
from flask import current_app
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from sqlalchemy.orm import validates
from flask_wtf import Form
from wtforms import StringField, HiddenField, SelectField, BooleanField
from wtforms.validators import Email, AnyOf, Length, Required
from itsdangerous import URLSafeTimedSerializer
from .exts import db
from .utils import gen_random_hash, router_db_get_entry
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


captcha_validator = AnyOf(('Berlin', 'berlin'),
        message=u'Falsch. Wie heisst die Hauptstadt Deutschlands?')
class EmailForm(Form):
    email = StringField('Email', validators=[Email()])
    hostname = StringField('Name', validators=[Length(4,32)])
    captcha = StringField('Captcha', validators=[captcha_validator])

    @validates('hostname')
    def validate_hostname(self, field):
        r = IPRequest.query.filter_by(name=field.data).count()
        if r > 0:
            raise ValueError(u'Standortname bereits vergeben.')
        return field

class DestroyForm(Form):
    email = StringField('Email', validators=[Email()])
    request_id = HiddenField('request_id')
    token = HiddenField('token')

    @validates('email')
    def validate_email(self, field):
        r = IPRequest.query.get(self.request_id.data)
        if r is None:
            raise ValueError(u'Ungültige Anfrage')

        if field.data != r.email:
            raise ValueError(u'Email stimmt nicht überein.')
        return field

class ExpertForm(Form):
    email = StringField('Email', validators=[Email()])
    name = StringField('Name', validators=[Length(4,32)])
    captcha = StringField('Captcha', validators=[captcha_validator])

    @validates('name')
    def validate_name(self, field):
        r = IPRequest.query.filter_by(name=field.data).count()
        if r > 0:
            raise ValueError(u'Name bereits vergeben.')
        return field

class RequiredAny(Required):
    """
    RequiredAny is a WTForm validaotr which makes a field required if
    another field is _not_ set.
    """

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredAny, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if not bool(other_field.data):
            super(RequiredAny, self).__call__(form, field)

def create_select_field(cls, attr, name, placeholder, choices_raw, depends):
    validators = [RequiredAny(depends, u'Bitte mind. eine Auswahl für IPv4 oder IPv6 treffen')]
    choices = [('', placeholder)] + [(unicode(k),k) for k in choices_raw]
    setattr(cls, attr, SelectField(name, choices=choices,
        validators=validators))


def ip_request_get(request_id):
    r = IPRequest.query.get(request_id)
    if r is None:
        raise BadRequest(u"Ungültige ID. Hast du den Eintrag bereits gelöscht?")
    return r
