# -*- coding: utf-8 -*-

from flask import Blueprint, url_for, render_template
from prettytable import PrettyTable
from utils import ip_request_for_email, send_email
from forms import SummaryForm

summary = Blueprint('summary', __name__)

@summary.route('/summary', methods=['GET', 'POST'])
def summary_index():
    form = SummaryForm()
    if form.validate_on_submit():
        table = PrettyTable()
        email = form.email.data
        requests = ip_request_for_email(email).all()
        table.add_column(u'Name', map(lambda x: x.name, requests))
        table.add_column(u'IPs', map(lambda x: ', '.join(x.ips), requests))
        table.add_column(u'Vom', map(lambda x: x.created_at.strftime('%d.%m.%Y'), requests))
        table.add_column(u'Bestätigt', map(lambda x: x.verified, requests))
        table.add_column(u'Löschen', ['[D%d]' % x for x in range(len(requests))])
        table.add_column(u'Kontakt', ['[M%d]' % x for x in range(len(requests))])

        dellinks = []
        contactlinks = []
        for r in requests:
            url = url_for("main.config_destroy", request_id=r.id,
                          signed_token=r.token_destroy, _external=True)
            dellinks.append(url)
            url = url_for("main.contact_mail", request_id=r.id,
                          signed_token=r.token_contactmail, _external=True)
            contactlinks.append(url)

        subject = '[Freifunk Berlin] IP-Auflistung'
        data = {'table' : table, 'dellinks' : dellinks, 'contactlinks' : contactlinks, 'email': email}
        send_email(email, subject, 'summary/email.txt', data)
        return render_template('summary/success.html', email = email)

    return render_template('summary/form.html', form = form)
