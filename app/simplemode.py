from flask import Blueprint, render_template, url_for, current_app
from wtforms import SelectField
from wtforms.validators import DataRequired
from .utils import request_create, send_email, activate_and_redirect
from .forms import EmailForm
from .exts import db

simplemode = Blueprint("simplemode", __name__)


@simplemode.route("/simplemode/activate/<int:request_id>/<signed_token>")
def simplemode_activate(request_id, signed_token):
    template = "simplemode/email.txt"
    return activate_and_redirect(template, request_id, signed_token)


@simplemode.route("/simplemode", methods=["GET", "POST"])
def simplemode_form():

    # add location field dynamically (values are set in config)
    v6pool = current_app.config["API_POOL_IPV6_SIMPLE"]
    v6_choices = [("", "Bitte Stadteil wählen")] + [(k, k) for k in list(v6pool.keys())]

    setattr(
        EmailForm,
        "ipv6_pool",
        SelectField("Stadtteil", choices=v6_choices, validators=[DataRequired()]),
    )
    form = EmailForm()

    if form.validate_on_submit():
        pool_mesh = current_app.config["API_POOL_MESH"]
        prefixes_mesh = [(pool_mesh, 32)] * 3

        # hna network
        pool_hna = current_app.config["API_POOL_HNA"]
        prefixes_hna = [(pool_hna, "27")]

        prefixes_v6 = [(v6pool[form.ipv6_pool.data], None)]

        r = request_create(
            form.hostname.data,
            form.email.data,
            prefixes_mesh + prefixes_hna,
            prefixes_v6,
        )

        try:
            url = url_for(
                ".simplemode_activate",
                request_id=r.id,
                signed_token=r.token_activation,
                _external=True,
            )
            subject = f"[Freifunk Berlin] Aktivierung - {r.name}"
            data = {"name": r.name, "url": url}
            send_email(r.email, subject, "activation.txt", data)
        except Exception as e:
            # if send_mail fails we delete the already saved request
            db.session.delete(r)
            db.session.commit()
            current_app.logger.error(f"Error sending mail!\n {e}")
            raise

        return render_template("confirmation.html")

    return render_template("simplemode/form.html", form=form)
