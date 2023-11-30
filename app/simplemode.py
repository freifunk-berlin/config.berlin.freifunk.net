from flask import Blueprint, render_template, url_for, current_app
from wtforms import SelectField
from .utils import request_create, send_email, activate_and_redirect
from .forms import EmailForm
from .exts import db

simplemode = Blueprint('simplemode', __name__)

@simplemode.route('/simplemode/activate/<int:request_id>/<signed_token>')
def simplemode_activate(request_id, signed_token):
    template = 'simplemode/email.txt'
    return activate_and_redirect(template, request_id, signed_token)


@simplemode.route('/simplemode', methods=['GET', 'POST'])
def simplemode_form():
    # add location type field dynamically (values are set in config)
    prefix_defaults = current_app.config['PREFIX_DEFAULTS']
    choices = [(k, k) for k in list(prefix_defaults.keys())]
    setattr(EmailForm, 'location_type', SelectField('Ort', choices=choices))

    form = EmailForm()
    if form.validate_on_submit():
        mesh_num = 3
        pool_mesh = current_app.config['API_POOL_MESH']
        prefixes_mesh = [(pool_mesh, 32)] * mesh_num

        # hna network
        pool_hna = current_app.config['API_POOL_HNA']
        prefixes_hna = [(pool_hna, prefix_defaults[form.location_type.data])]

        r = request_create(form.hostname.data, form.email.data,
                           prefixes_mesh + prefixes_hna, [])

        try:
            url = url_for(".simplemode_activate", request_id=r.id,
                          signed_token=r.token_activation, _external=True)
            subject = "[Freifunk Berlin] Aktivierung - %s" % r.name
            data = {'name': r.name, 'url': url}
            send_email(r.email, subject, "activation.txt", data)
        except:
            # if send_mail fails we delete the already saved request
            db.session.delete(r)
            db.session.commit()
            raise

        return render_template('confirmation.html')

    return render_template('simplemode/form.html', form=form)
