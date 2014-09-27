# -*- coding: utf-8 -*-

import re

from itertools import chain
from flask import Blueprint, render_template, redirect, url_for, session,\
                  current_app, request, g
from wtforms import SelectField
from utils import session_key_needed, send_email, allocate_ips, activate_ips
from models import db, IPRequest, EmailForm


wizard = Blueprint('api', __name__)


@wizard.route('/config/<token>')
def wizard_get_config(token):
    r = IPRequest.query.filter_by(token=token).one()
    if not r.verified:
        return redirect(url_for('.index'))

    ips = r.ips.split(' ')
    ips = {'mesh':[], 'hna':[]}
    for ip in r.ips.split(' '):
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
@session_key_needed('router_id', '.wizard_select_router')
def wizard_get_email():
    choices = []
    prefix_defaults = current_app.config['PREFIX_DEFAULTS']
    for k in prefix_defaults.keys():
        #choices.append((re.sub('[\W_]+', '', k), k)
        choices.append((k,k))
    setattr(EmailForm, 'location_type', SelectField('Ort', choices=choices))

    form = EmailForm()

    if form.validate_on_submit():
        session['email'] = form.email.data
        session['prefix_len'] = prefix_defaults[form.location_type.data]
        return redirect(url_for('.wizard_send_email'))
    router_db = current_app.config['ROUTER_DB']
    router = router_db[session['router_id']]
    return render_template('email_form.html', form = form, router = router)


@wizard.route('/wizard/email_sent')
@session_key_needed('router_id', '.wizard_select_router')
@session_key_needed('email', '.wizard_get_email')
@session_key_needed('prefix_len', '.wizard_get_email')
def wizard_send_email():
    router_db = current_app.config['ROUTER_DB']
    router_id = session['router_id']
    router = {'id': router_id, 'data': router_db[router_id]}

    api_params = (current_app.config['APP_ID'], current_app.config['API_USER'],
            current_app.config['API_PASS'], current_app.config['API_HOST'])
    ip_mesh_num = 2 if router['data']['dualband'] else 1
    ips = {
        'mesh' : allocate_ips(*api_params,
                              pool = current_app.config['API_POOL_MESH'],
                              num = ip_mesh_num),
        'hna' : allocate_ips(*api_params,
                              pool = current_app.config['API_POOL_HNA'],
                              num = 1,
                              prefix_len = session['prefix_len'])
    }

    ips = list(chain(*ips.values()))
    ips_str = " ".join(ips)
    r = IPRequest(session['email'], ips_str, router_id)
    db.session.add(r)
    db.session.commit()

    url = url_for(".wizard_activate", request_id=r.id,
                  signed_token=r.gen_signed_token(), _external=True)
    send_email(api_params, session['email'], router, ips, url)

    for k in ('email', 'router_id'):
        del session[k]

    return render_template('waiting_for_confirmation.html')


@wizard.route('/wizard/activate/<int:request_id>/<signed_token>')
def wizard_activate(request_id, signed_token):
    r = IPRequest.query.get(request_id)
    if not r.verify_signed_token(signed_token, timeout = 3600):
        raise Exception("Invalid Token")

    activate_ips(current_app.config['APP_ID'], current_app.config['API_USER'],
            current_app.config['API_PASS'], current_app.config['API_HOST'],
            r.ips.split(" ")
    )

    r.verified = True
    db.session.add(r)
    db.session.commit()

    return redirect(url_for('.wizard_get_config', token = r.token))


@wizard.route('/')
def index():
    return render_template('welcome.html')


@wizard.errorhandler(403)
@wizard.errorhandler(404)
def errorhandler(e):
    return render_template('error.html', error=e), e.code
