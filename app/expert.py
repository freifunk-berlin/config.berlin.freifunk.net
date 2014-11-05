# -*- coding: utf-8 -*-

from wtforms import SelectField
from flask import Blueprint, render_template, redirect, url_for, current_app,\
                  request, flash
from werkzeug.exceptions import BadRequest
from .models import IPRequest, ExpertForm, DestroyForm, create_select_field,\
                    ip_request_get
from .utils import request_create, send_email
from .exts import db


expert = Blueprint('expert', __name__)


@expert.route('/expert/destroy/<int:request_id>/<signed_token>', methods=['GET', 'POST'])
def expert_destroy(request_id, signed_token):
    r = ip_request_get(request_id)
    form = DestroyForm(request_id=request_id, token=signed_token)
    if form.validate_on_submit():
        r.destroy(form.token.data)
        flash(u'Adressen erfolgreich gelöscht!')
        return redirect(url_for('.expert_form'))

    url = url_for('.expert_destroy', request_id = r.id, signed_token = signed_token)
    return render_template('wizard/destroy_form.html', request = r, form = form, url =  url)


@expert.route('/expert/activate/<int:request_id>/<signed_token>')
def expert_activate(request_id, signed_token):
    r = ip_request_get(request_id)
    if not r.verified:
        r.activate(signed_token)
        url = url_for(".expert_destroy", request_id=r.id,
                      signed_token=r.token_destroy, _external=True)
        subject = "[Freifunk Berlin] IPs - %s" % r.name
        data = {'request' : r, 'url':url}
        send_email(r.email, subject, 'expert/email_config.txt', data)
        flash(u'IP-Adressen aktiviert. Check your inbox!')

    return redirect(url_for('.expert_form', token = r.token))


@expert.route('/expert/form', methods=['GET', 'POST'])
def expert_form():
    # add select fields dynamically (because they get their data from config)
    ipv4_prefixes = range(32, current_app.config['EXPERT_MAX_PREFIX']-1, -1)
    create_select_field(ExpertForm, 'ipv4_prefix', u'IPv4-Präfix', 'kein IPv4',
            ipv4_prefixes, 'ipv6_pool')
    create_select_field(ExpertForm, 'ipv6_pool', u'Wahlkreis', 'kein IPv6',
            current_app.config['API_POOL_IPV6'], 'ipv4_prefix')

    form = ExpertForm()
    if form.validate_on_submit():
        prefixes_v4 = [(current_app.config['API_POOL_HNA'], int(form.ipv4_prefix.data))]
        prefixes_v6 = [(form.ipv6_pool.data, None)]
        r = request_create(form.name.data, form.email.data, prefixes_v4,
                prefixes_v6)

        try:
            url = url_for(".expert_activate", request_id=r.id,
                          signed_token=r.token_activation, _external=True)
            subject = "[Freifunk Berlin] Aktivierung - %s" % r.name
            send_email(r.email, subject, "activation.txt", {'url':url})

            flash(u'Aktivierungsmail versendet!')

        except:
            # if send_mail fails we delete the already saved request
            db.session.delete(r)
            db.session.commit()
            raise

    return render_template('expert/form.html', form=form)
