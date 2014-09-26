# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, session,\
                  current_app, request, g
from utils import session_key_needed, send_email, allocate_ips
from models import db, EmailForm


wizard = Blueprint('api', __name__)

@wizard.route('/config')
def wizard_get_config():
    return render_template('config.html')

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
    form = EmailForm()
    if form.validate_on_submit():
        session['email'] = form.email.data
        return redirect(url_for('.wizard_send_email'))
    router_db = current_app.config['ROUTER_DB']
    router = router_db[session['router_id']]
    return render_template('email_form.html', form = form, router = router)

@wizard.route('/wizard/email_sent')
@session_key_needed('router_id', '.wizard_select_router')
@session_key_needed('email', '.wizard_get_email')
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
                              num = 1)
    }

    send_email(api_params, session['email'], router, ips)

    for k in ('email', 'router_id'):
        del session[k]

    return render_template('waiting_for_confirmation.html')


@wizard.route('/')
def index():
    return render_template('welcome.html')

@wizard.errorhandler(403)
@wizard.errorhandler(404)
def errorhandler(e):
    return render_template('error.html', error=e), e.code
