# -*- coding: utf-8 -*-

import re

from itertools import chain
from flask import Blueprint, render_template, redirect, url_for, session,\
                  current_app, request, g
from wtforms import SelectField
from .utils import session_keys_needed, send_email, get_api, router_db_get_entry,\
                  router_db_has_entry, router_db_list
from .models import db, IPRequest, EmailForm


wizard = Blueprint('wizard', __name__)


@wizard.route('/wizard/config/<token>')
def wizard_get_config(token):
    r = IPRequest.query.filter_by(token=token).one()
    if not r.verified:
        raise Exception('Request has not been verified yet')

    ips = {'mesh':[], 'hna':[]}
    for ip in r.ips:
        if ip.endswith('/32'):
            ips['mesh'].append(ip.replace('/32', ''))
        else:
            ips['hna'].append(ip)
    router_db = current_app.config['ROUTER_DB']
    base_url = current_app.config['FIRMWARE_BASE_URL']
    router = router_db_get_entry(router_db, r.router_id, base_url)
                
    return render_template('show_config.html', ips=ips, router=router)


@wizard.route('/')
@wizard.route('/wizard/routers/<path:router_id>')
def wizard_select_router(router_id = None):
    if router_db_has_entry(current_app.config['ROUTER_DB'], router_id):
        session['router_id'] = router_id
        return redirect(url_for('.wizard_form'))
    routers = router_db_list(current_app.config['ROUTER_DB'])
    return render_template('select_router.html', routers=routers)


@wizard.route('/wizard/form', methods=['GET', 'POST'])
@session_keys_needed(['router_id'], '.wizard_select_router')
def wizard_form():
    # add location type field dynamically (values are set in config)
    prefix_defaults = current_app.config['PREFIX_DEFAULTS']
    choices = [(k,k) for k in prefix_defaults.keys()]
    setattr(EmailForm, 'location_type', SelectField('Ort', choices=choices))

    form = EmailForm()
    if form.validate_on_submit():
        session['email'] = form.email.data
        session['hostname'] = form.hostname.data
        session['prefix_len'] = prefix_defaults[form.location_type.data]
        return redirect(url_for('.wizard_send_email'))

    router_db = current_app.config['ROUTER_DB']
    router = router_db_get_entry(router_db, session['router_id'])
    return render_template('form.html', form = form, router = router)


@wizard.route('/wizard/email_sent')
@session_keys_needed(['router_id'], '.wizard_select_router')
@session_keys_needed(['email', 'hostname', 'prefix_len'], '.wizard_form')
def wizard_send_email():
    # add new request to database
    router_db = current_app.config['ROUTER_DB']
    r = IPRequest(session['hostname'], session['email'], session['router_id'])
    db.session.add(r)
    db.session.commit()

    # allocate mesh IPs
    router = router_db_get_entry(router_db, session['router_id'])
    ip_mesh_num = 2 if router['dualband'] else 1
    get_api().allocate_ips(current_app.config['API_POOL_MESH'], r.id, r.email,
        r.hostname, ip_mesh_num)

    # allocate HNA network
    get_api().allocate_ips(current_app.config['API_POOL_HNA'], r.id, r.email,
        r.hostname, prefix_len = session['prefix_len'])

    url = url_for(".wizard_activate", request_id=r.id,
                  signed_token=r.gen_signed_token(), _external=True)
    send_email(session['email'], r.hostname, router, url)

    for k in ('email', 'router_id'):
        del session[k]

    return render_template('waiting_for_confirmation.html')


@wizard.route('/wizard/activate/<int:request_id>/<signed_token>')
def wizard_activate(request_id, signed_token):
    r = IPRequest.query.get(request_id)
    if not r.verified:
        if not r.verify_signed_token(signed_token, timeout = 3600):
            raise Exception("Invalid Token")

        get_api().activate_ips(r.id)
        r.verified = True

        db.session.add(r)
        db.session.commit()

    return redirect(url_for('.wizard_get_config', token = r.token))
