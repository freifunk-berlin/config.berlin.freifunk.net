# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, url_for
from werkzeug.exceptions import BadRequest

from .forms import DestroyForm, ContactMailForm
from .utils import ip_request_get, send_email


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/config/<int:request_id>/<signed_token>')
def config_show(request_id, signed_token):
    r = ip_request_get(request_id)
    if r.viewable(signed_token) or not r.verified:
        raise BadRequest("Eintrag wurde bisher noch nicht aktiviert!")

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


@main.route('/contact/<int:request_id>/<signed_token>', methods=['GET', 'POST'])
def contact_mail(request_id, signed_token):
    r = ip_request_get(request_id)
    form = ContactMailForm(request_id=request_id, token=signed_token)
    if form.validate_on_submit():
        try:
            r.sendcontactmail(form.token.data)
            subject = "[Freifunk Berlin] Kontakt per Web - %s" % r.name
            data = {'request' : r, 'text': form.text.data}
            send_email(r.email, subject, "contact_mail.txt", data)
            return render_template('contact_mail_result.html', result = "Mail erfolgreich gesendet." )
        except:
            return render_template('contact_mail_result.html', result = "Senden der Mail fehlgeschlagen." )

    url = url_for('.contact_mail', request_id = r.id, signed_token = signed_token)
    return render_template('contact_mail_form.html', request = r, form = form, url =  url)
