from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import Email, AnyOf

db = SQLAlchemy()

class IPRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    nipap_id = db.Column(db.Integer, unique=True)
    active = db.Column(db.Boolean())

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return '<IPRequest %r>' % self.email


error_msg = u'Falsch. Wie heisst die Hauptstadt Deutschlands?'
v = AnyOf(('Berlin', 'berlin'), message=error_msg)
class EmailForm(Form):
    email = StringField('Email', validators=[Email()])
    captcha = StringField('Captcha', validators=[v])
