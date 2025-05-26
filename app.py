from flask import Flask, render_template, request, redirect, url_for, session, flash
import configparser
import base64
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

config = configparser.ConfigParser()
config.read('config.ini')

ENCODED_PASSWORD = config['auth']['password']
SERVER_URL = config['server']['url']
BEARER_TOKEN = config['server']['token']


def check_password(input_password):
    decoded = base64.b64decode(ENCODED_PASSWORD).decode()
    return input_password == decoded


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if check_password(request.form['password']):
            session['logged_in'] = True
            return redirect(url_for('form'))
        else:
            flash('Falsches Passwort!')
    return render_template('login.html')


@app.route('/form', methods=['GET', 'POST'])
def form():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        severity = request.form['severity']
        notification = request.form['notification']
        data = {"severity": severity, "notification": notification}

        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(SERVER_URL, json=data, headers=headers)
        try:
            result = response.json()
        except ValueError:
            result = {"error": "Ungültige Serverantwort"}

        return render_template('form.html', result=result)

    return render_template('form.html')


if __name__ == '__main__':
    app.run(debug=True)
