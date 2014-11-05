# -*- coding: utf-8 -*-

import re

from itertools import chain
from flask import Blueprint, render_template, redirect, url_for, current_app,\
                  request, g
from werkzeug.exceptions import BadRequest
from wtforms import SelectField
from .utils import request_create, send_email, get_api,\
                   router_db_get_entry, router_db_has_entry, router_db_list
from .models import IPRequest, EmailForm, DestroyForm, ip_request_get
from .exts import db


wizard = Blueprint('wizard', __name__)


@wizard.route('/wizard/config/<int:request_id>/<signed_token>')
def wizard_get_config(request_id, signed_token):
    r = ip_request_get(request_id)
    if r.viewable(signed_token) or not r.verified:
        raise BadRequest(u"Eintrag wurde bisher noch nicht aktiviert!")

    return render_template('wizard/show_config.html', ips=r.ips_pretty, router=r.router)


@wizard.route('/wizard/routers')
@wizard.route('/wizard/routers/<path:router_id>')
def wizard_select_router(router_id = None):
    router_db = current_app.config['ROUTER_DB']
    if router_db_has_entry(router_db, router_id):
        return redirect(url_for('.wizard_form', router_id = router_id))

    routers = router_db_list(router_db)
    return render_template('wizard/select_router.html', routers=routers)


@wizard.route('/wizard/forms/<path:router_id>', methods=['GET', 'POST'])
def wizard_form(router_id):
    router_db = current_app.config['ROUTER_DB']
    router = router_db_get_entry(router_db, router_id)

    # add location type field dynamically (values are set in config)
    prefix_defaults = current_app.config['PREFIX_DEFAULTS']
    choices = [(k,k) for k in prefix_defaults.keys()]
    setattr(EmailForm, 'location_type', SelectField('Ort', choices=choices))

    form = EmailForm()
    if form.validate_on_submit():
        # mesh ips - 3 for dualband (2x wifi + 1x lan) else 2
        mesh_num = 3 if router['dualband'] else 2
        pool_mesh = current_app.config['API_POOL_MESH']
        prefixes_mesh = [(pool_mesh, 32)]*mesh_num

        # hna network
        pool_hna = current_app.config['API_POOL_HNA']
        prefixes_hna = [(pool_hna, prefix_defaults[form.location_type.data])]

        r = request_create(form.hostname.data, form.email.data,
                prefixes_mesh + prefixes_hna, [], router_id = router_id)

        try:
            url = url_for(".wizard_activate", request_id=r.id,
                          signed_token=r.token_activation, _external=True)
            subject = "[Freifunk Berlin] Aktivierung - %s" % r.name
            data = { 'name': r.name, 'router': r.router['name'], 'url': url }
            send_email(r.email, subject, "activation.txt", data)
        except:
            # if send_mail fails we delete the already saved request
            db.session.delete(r)
            db.session.commit()
            raise

        return render_template('confirmation.html')

    return render_template('wizard/form.html', form = form, router = router)


@wizard.route('/wizard/activate/<int:request_id>/<signed_token>')
def wizard_activate(request_id, signed_token):
    r = ip_request_get(request_id)
    if not r.verified:
        r.activate(signed_token)
        url = url_for(".wizard_destroy", request_id=r.id,
                      signed_token=r.token_destroy, _external=True)
        subject = "[Freifunk Berlin] Konfiguration - %s" % r.name
        send_email(r.email, subject, 'wizard/email_config.txt', {'request' : r,
            'url':url})

    return redirect(url_for('.wizard_get_config', request_id=r.id, signed_token = r.token_config))


@wizard.route('/wizard/destroy/<int:request_id>/<signed_token>', methods=['GET', 'POST'])
def wizard_destroy(request_id, signed_token):
    r = ip_request_get(request_id)
    form = DestroyForm(request_id=request_id, token=signed_token)
    if form.validate_on_submit():
        r.destroy(form.token.data)
        return render_template('wizard/destroy_success.html', name = r.name)

    url = url_for('.wizard_destroy', request_id = r.id, signed_token = signed_token)
    return render_template('wizard/destroy_form.html', request = r, form = form, url =  url)
