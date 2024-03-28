# -*- coding: utf-8 -*-

import string
from random import choice
from flask import redirect, url_for, render_template, g, current_app
from flask_mail import Message
from werkzeug.exceptions import BadRequest
from .nipap import NipapApi
from .exts import mail
from sqlalchemy import func


def get_api():
    api = getattr(g, "_api", None)
    if api is None:
        api = g._api = NipapApi(current_app.config["APP_ID"])
        uri = "http://{}:{}@{}".format(
            current_app.config["API_USER"],
            current_app.config["API_PASS"],
            current_app.config["API_HOST"],
        )
        g._api.connect(uri)

    return api


def request_create(name, email, prefixes_v4, prefixes_v6):
    """Process the data gathered from the input form, by performing all steps
    needed to assign enough ips for the router model of the user."""

    from .models import db, IPRequest

    try:
        # add new request to database
        r = IPRequest(name, email)
        db.session.add(r)
        db.session.commit()

        # allocate IPs in NIPAP
        if prefixes_v4:
            for pool, prefix_len in prefixes_v4:
                get_api().allocate_ips(pool, r.id, r.email, name, prefix_len, 4)

        if prefixes_v6:
            for pool, prefix_len in prefixes_v6:
                get_api().allocate_ips(pool, r.id, r.email, name, prefix_len, 6)

    except:
        db.session.rollback()
        raise
    finally:
        db.session.close()

    return r


def gen_random_hash(length):
    digits = string.ascii_letters + string.digits
    return "".join(choice(digits) for x in range(length))


def send_email(recipient, subject, template, data, no_template=False):
    body = render_template(template, **data) if not no_template else template
    msg = Message(
        subject,
        sender=current_app.config["MAIL_FROM"],
        recipients=[recipient],
        body=body,
    )
    return mail.send(msg)


def ip_request_get(request_id):
    from .models import IPRequest

    r = IPRequest.query.get(request_id)
    if r is None:
        raise BadRequest("Ungültige ID. Hast du den Eintrag bereits gelöscht?")
    return r


def ip_request_for_email(email):
    from .models import IPRequest
    r = IPRequest.query.filter(func.lower(IPRequest.email) == func.lower(email), IPRequest.verified == True)
    if r.count() == 0:
        raise BadRequest("Kein Eintrag für diese E-Mail")
    return r


def activate_and_redirect(email_template, request_id, signed_token):
    r = ip_request_get(request_id)
    if not r.verified:
        r.activate(signed_token)
        url_destroy = url_for(
            "main.config_destroy",
            request_id=r.id,
            signed_token=r.token_destroy,
            _external=True,
        )
        url_contactmail = url_for(
            "main.contact_mail",
            request_id=r.id,
            signed_token=r.token_contactmail,
            _external=True,
        )
        subject = "[Freifunk Berlin] IPs - %s" % r.name
        data = {
            "request": r,
            "url_destroy": url_destroy,
            "url_contactmail": url_contactmail,
        }
        send_email(r.email, subject, email_template, data)

    return redirect(
        url_for("main.config_show", request_id=r.id, signed_token=r.token_config)
    )
