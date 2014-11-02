# -*- coding: utf-8 -*-

from wtforms import SelectField
from flask import Blueprint, render_template, redirect, url_for, current_app,\
                  request, flash
from .models import IPRequest, ExpertForm, DestroyForm
from .utils import form_process, send_email


expert = Blueprint('expert', __name__)


@expert.route('/expert/destroy/<int:request_id>/<signed_token>', methods=['GET', 'POST'])
def expert_destroy(request_id, signed_token):
    form = DestroyForm(request_id=request_id, token=signed_token)
    r = IPRequest.query.get(request_id)
    if form.validate_on_submit():
        r.destroy(form.token.data)
        flash(u'Adressen erfolgreich gelöscht!')
        return redirect(url_for('.expert_form'))

    url = url_for('.expert_destroy', request_id = r.id, signed_token = signed_token)
    return render_template('wizard/destroy_form.html', request = r, form = form, url =  url)


@expert.route('/expert/activate/<int:request_id>/<signed_token>')
def expert_activate(request_id, signed_token):
    r = IPRequest.query.get(request_id)
    if not r.verified:
        r.activate(signed_token)
        url = url_for(".expert_destroy", request_id=r.id,
                      signed_token=r.token_destroy, _external=True)
        subject = "[Freifunk Berlin] IPs - %s" % r.name
        send_email(r.email, subject, 'expert/email_config.txt', {'request' : r,
            'url':url})
        flash(u'IP-Adressen aktiviert. Check your inbox!')

    return redirect(url_for('.expert_form', token = r.token))


@expert.route('/expert/form', methods=['GET', 'POST'])
def expert_form():
    prefix_max  = current_app.config['EXPERT_MAX_PREFIX']
    prefixes = range(prefix_max, 33)
    choices = [(str(k),k) for k in prefixes]
    setattr(ExpertForm, 'prefix', SelectField(u'Präfix', choices=choices))

    form = ExpertForm()
    if form.validate_on_submit():
        r = form_process(form.name.data, form.email.data, form.prefix.data)
        url = url_for(".expert_activate", request_id=r.id,
                      signed_token=r.token_activation, _external=True)
        subject = "[Freifunk Berlin] Aktivierung - %s" % r.name
        send_email(r.email, subject, "activation.txt", {'url':url})
        flash(u'Aktivierungsmail versendet!')

    return render_template('expert/form.html', form=form)
