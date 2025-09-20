from flask import Blueprint, render_template, url_for, current_app
from .forms import ExpertForm, create_select_field
from .utils import request_create, send_email, activate_and_redirect
from .exts import db

expert = Blueprint('expert', __name__)


@expert.route('/expert/activate/<int:request_id>/<signed_token>')
def expert_activate(request_id, signed_token):
    template = 'expert/email.txt'
    return activate_and_redirect(template, request_id, signed_token)


@expert.route('/expert/form', methods=['GET', 'POST'])
def expert_form():
    # add select fields dynamically (because they get their data from config)
    ipv4_prefixes = list(range(32, current_app.config['EXPERT_MAX_PREFIX'] - 1, -1))
    create_select_field(ExpertForm, 'ipv4_prefix', 'IPv4-Präfix', 'kein IPv4',
                        ipv4_prefixes, 'ipv6_pool')
    create_select_field(ExpertForm, 'ipv6_pool', 'Wahlkreis', 'kein IPv6',
                        current_app.config['API_POOL_IPV6'], 'ipv4_prefix')


    form = ExpertForm()
    if form.validate_on_submit():
        prefixes_v4 = [(current_app.config['API_POOL_HNA'], int(form.ipv4_prefix.data))] \
            if form.ipv4_prefix.data else []

        prefixes_v6 = [(form.ipv6_pool.data, None)] \
            if form.ipv6_pool.data else []

        r = request_create(form.name.data, form.email.data, prefixes_v4,
                           prefixes_v6)

        try:
            url = url_for(".expert_activate", request_id=r.id,
                          signed_token=r.token_activation, _external=True)
            subject = f"[Freifunk Berlin] Aktivierung - {r.name}"
            send_email(r.email, subject, "activation.txt", {'url': url})

        except:
            # if send_mail fails we delete the already saved request
            db.session.delete(r)
            db.session.commit()
            raise

        return render_template('confirmation.html')

    return render_template('expert/form.html', form=form)
