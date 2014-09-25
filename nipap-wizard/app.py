from flask import Flask, render_template
from config import supported_devices

app = Flask(__name__)

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/routers')
def step_routers():
    return render_template('routers.html', routers=supported_devices)

@app.route('/<router>/form')
def step_form(router):
    return render_template('form.html')

@app.route('/verify', methods=['POST'])
def step_verify():
    return render_template('verify.html')

@app.route('/')
def index():
    return render_template('welcome.html')

if __name__ == '__main__':
    app.run(port = 5001, debug = True)
