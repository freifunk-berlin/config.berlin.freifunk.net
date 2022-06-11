# -*- coding: utf-8 -*-

from sqlalchemy.orm import validates
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SelectField
from wtforms.validators import Email, AnyOf, Length, DataRequired
from .models import IPRequest

captcha_validator = AnyOf(('Berlin', 'berlin'),
                          message='Falsch. Wie heisst die Hauptstadt Deutschlands?')


class EmailForm(FlaskForm):
    email = StringField('E-Mail', validators=[Email()])
    hostname = StringField('Name', validators=[Length(4, 32)])
    captcha = StringField('Captcha', validators=[captcha_validator])

    @validates('hostname')
    def validate_hostname(self, field):
        r = IPRequest.query.filter_by(name=field.data).count()
        if r > 0:
            raise ValueError('Standortname bereits vergeben.')
        return field


class DestroyForm(FlaskForm):
    email = StringField('E-Mail', validators=[Email()])
    request_id = HiddenField('request_id')
    token = HiddenField('token')

    @validates('email')
    def validate_email(self, field):
        r = IPRequest.query.get(self.request_id.data)
        if r is None:
            raise ValueError('Ungültige Anfrage')

        if field.data != r.email:
            raise ValueError('E-Mail stimmt nicht überein.')
        return field


class ContactMailForm(FlaskForm):
    text = StringField('text')
    request_id = HiddenField('request_id')
    token = HiddenField('token')
    captcha = StringField('Captcha', validators=[captcha_validator])


class ExpertForm(FlaskForm):
    email = StringField('E-Mail', validators=[Email()])
    name = StringField('Name', validators=[Length(4, 32)])
    captcha = StringField('Captcha', validators=[captcha_validator])

    @validates('name')
    def validate_name(self, field):
        r = IPRequest.query.filter_by(name=field.data).count()
        if r > 0:
            raise ValueError('Name bereits vergeben.')
        return field


class SummaryForm(FlaskForm):
    email = StringField('E-Mail', validators=[Email()])

    @validates('email')
    def validate_email(self, field):
        r = IPRequest.query.filter_by(email=field.data)
        if r is None:
            raise ValueError('Ungültige Anfrage')
        return field


class RequiredAny(DataRequired):
    """
    RequiredAny is a WTForm validator which makes a field required if
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
    validators = [RequiredAny(depends, 'Bitte mind. eine Auswahl für IPv4 oder IPv6 treffen')]
    choices = [('', placeholder)] + [(str(k), k) for k in choices_raw]
    setattr(cls, attr, SelectField(name, choices=choices,
                                   validators=validators))
