from flask import Flask, render_template, redirect, url_for, session, request, g
from utils import session_key_needed, send_email
from models import db, EmailForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db.init_app(app)

app = Flask(__name__)
app.config.from_pyfile('application.cfg')

router_db = app.config['ROUTER_DB']

@app.route('/config')
def wizard_get_config():
    return render_template('config.html')

@app.route('/wizard/routers')
def wizard_select_router():
    router_id = request.args.get('id', None)
    if router_id is not None and router_id in router_db:
        session['router_id'] = router_id
        return redirect(url_for('wizard_get_email'))
    return render_template('routers.html', routers=router_db)

@app.route('/wizard/email', methods=['GET', 'POST'])
@session_key_needed('router_id', 'wizard_select_router')
def wizard_get_email():
    form = EmailForm()
    if form.validate_on_submit():
        session['email'] = form.email.data
        return redirect(url_for('wizard_send_email'))
    router = router_db[session['router_id']]
    return render_template('form.html', form = form, router = router)

@app.route('/wizard/confirmation')
@session_key_needed('router_id', 'wizard_select_router')
@session_key_needed('email', 'wizard_get_email')
def wizard_send_email():
    api_params = ('nipap_wizard', app.config['API_USER'],
            app.config['API_PASS'], app.config['API_HOST'],
            app.config['API_POOL_MESH'], app.config['API_POOL_HNA'])
    router_id = session['router_id']
    router = {'id': router_id, 'data': router_db[router_id]}
    send_email(api_params, session['email'], router)

    for k in ('email', 'router_id'):
        del session[k]

    return render_template('email.html')


@app.route('/')
def index():
    return render_template('welcome.html')

@app.errorhandler(403)
@app.errorhandler(404)
def errorhandler(e):
    return render_template('error.html', error=e), e.code

if __name__ == '__main__':
    app.run()
