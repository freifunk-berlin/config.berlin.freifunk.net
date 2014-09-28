# -*- coding: utf-8 -*-

import re

from itertools import chain
from flask import Blueprint, render_template, redirect, url_for, session,\
                  current_app, request, g
from wtforms import SelectField
from utils import session_keys_needed, send_email
from nipap import NipapApi
from models import db, IPRequest, EmailForm


wizard = Blueprint('wizard', __name__)


@wizard.before_request
def init_api():
    g.api = NipapApi(current_app.config['APP_ID'])
    uri = 'http://%s:%s@%s' % (current_app.config['API_USER'],
              current_app.config['API_PASS'], current_app.config['API_HOST'])
    g.api.connect(uri)


@wizard.route('/wizard/config/<token>')
def wizard_get_config(token):
    r = IPRequest.query.filter_by(token=token).one()
    if not r.verified:
        raise Exception('Request has not been verified yet')

    ips = {'mesh':[], 'hna':[]}
    for ip in g.api.get_prefixes_for_id(r.id):
        if ip.endswith('/32'):
            ips['mesh'].append(ip.replace('/32', ''))
        else:
            ips['hna'].append(ip)
    router = current_app.config['ROUTER_DB'][r.router_id]
    firmware = "/".join([current_app.config['FIRMWARE_BASE_URL'],
                    router['target']
                ])
                
    return render_template('show_config.html', ips=ips, firmware=firmware, router=router)


@wizard.route('/wizard/routers')
def wizard_select_router():
    router_db = current_app.config['ROUTER_DB']
    router_id = request.args.get('id', None)
    if router_id is not None and router_id in router_db:
        session['router_id'] = router_id
        return redirect(url_for('.wizard_get_email'))
    return render_template('select_router.html', routers=router_db)


@wizard.route('/wizard/contact', methods=['GET', 'POST'])
@session_keys_needed(['router_id'], '.wizard_select_router')
def wizard_get_email():
    # add location type field dynamically (values are set in config)
    prefix_defaults = current_app.config['PREFIX_DEFAULTS']
    choices = [(k,k) for k in prefix_defaults.keys()]
    setattr(EmailForm, 'location_type', SelectField('Ort', choices=choices))

    form = EmailForm()
    if form.validate_on_submit():
        session['email'] = form.email.data
        session['prefix_len'] = prefix_defaults[form.location_type.data]
        return redirect(url_for('.wizard_send_email'))

    router = current_app.config['ROUTER_DB'][session['router_id']]
    return render_template('email_form.html', form = form, router = router)


@wizard.route('/wizard/email_sent')
@session_keys_needed(['router_id'], '.wizard_select_router')
@session_keys_needed(['email', 'prefix_len'], '.wizard_get_email')
def wizard_send_email():
    # add new request to database
    data = current_app.config['ROUTER_DB'][session['router_id']]
    router = {'id': session['router_id'], 'data': data}
    r = IPRequest(session['email'], session['router_id'])
    db.session.add(r)
    db.session.commit()

    # allocate mesh IPs
    ip_mesh_num = 2 if router['data']['dualband'] else 1
    g.api.allocate_ips(current_app.config['API_POOL_MESH'], r.id, r.email,
        ip_mesh_num)

    # allocate HNA network
    g.api.allocate_ips(current_app.config['API_POOL_HNA'], r.id, r.email,
        prefix_len = session['prefix_len'])

    ips = g.api.get_prefixes_for_id(r.id)
    url = url_for(".wizard_activate", request_id=r.id,
                  signed_token=r.gen_signed_token(ips), _external=True)
    send_email(session['email'], router, ips, url)

    for k in ('email', 'router_id'):
        del session[k]

    return render_template('waiting_for_confirmation.html')


@wizard.route('/wizard/activate/<int:request_id>/<signed_token>')
def wizard_activate(request_id, signed_token):
    r = IPRequest.query.get(request_id)
    ips = g.api.get_prefixes_for_id(r.id)
    if not r.verify_signed_token(ips, signed_token, timeout = 3600):
        raise Exception("Invalid Token")

    g.api.activate_ips(r.id)
    r.verified = True

    db.session.add(r)
    db.session.commit()

    return redirect(url_for('.wizard_get_config', token = r.token))


@wizard.route('/')
def index():
    return render_template('welcome.html')
