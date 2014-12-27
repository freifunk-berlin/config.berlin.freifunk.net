# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, url_for
from .forms import DestroyForm
from .utils import ip_request_get


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/config/<int:request_id>/<signed_token>')
def config_show(request_id, signed_token):
    r = ip_request_get(request_id)
    if r.viewable(signed_token) or not r.verified:
        raise BadRequest(u"Eintrag wurde bisher noch nicht aktiviert!")

    return render_template('config.html', name=r.name, ips=r.ips_pretty,
                                          router=r.router)


@main.route('/destroy/<int:request_id>/<signed_token>', methods=['GET', 'POST'])
def config_destroy(request_id, signed_token):
    r = ip_request_get(request_id)
    form = DestroyForm(request_id=request_id, token=signed_token)
    if form.validate_on_submit():
        r.destroy(form.token.data)
        return render_template('destroy_success.html', name = r.name)

    url = url_for('.config_destroy', request_id = r.id, signed_token = signed_token)
    return render_template('destroy_form.html', request = r, form = form, url =  url)
