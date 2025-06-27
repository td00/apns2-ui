from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import configparser
import base64
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Konfiguration laden
config = configparser.ConfigParser()
config.read('config.ini')

# Zugangsdaten aus config.ini
ENCODED_PASSWORD = config['auth']['password']
SERVER_URL = config['server']['url']
BEARER_TOKEN = config['server']['token']

SERVER2_URL = config['server2']['url']
BEARER_TOKEN2 = config['server2']['token']

API_TOKEN = config['api']['token']

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

    result = {"responses": []}

    if request.method == 'POST':
        severity = request.form['severity']
        notification_title = request.form['notification_title']
        notification_text = request.form['notification_text']
        selected_platforms = request.form.getlist('platform')

        data = {
            "severity": severity,
            "notification_title": notification_title,
            "notification_text": notification_text
        }

        if 'apple' in selected_platforms:
            headers = {
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(SERVER_URL, json=data, headers=headers)
                response_data = response.json()
            except ValueError:
                response_data = {"error": "Ungültige Serverantwort"}
            except Exception as e:
                response_data = {"error": str(e)}

            result["responses"].append({
                "platform": "Apple",
                "response": response_data
            })

        if 'android' in selected_platforms:
            headers = {
                "Authorization": f"Bearer {BEARER_TOKEN2}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(SERVER2_URL, json=data, headers=headers)
                response_data = response.json()
            except ValueError:
                response_data = {"error": "Ungültige Serverantwort"}
            except Exception as e:
                response_data = {"error": str(e)}

            result["responses"].append({
                "platform": "Android",
                "response": response_data
            })

        return render_template('form.html', result=result)

    return render_template('form.html')


@app.route('/api/notify', methods=['POST'])
def api_notify():
    # Authorization prüfen
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Kein gültiger Authorization Header"}), 401

    token = auth_header.split(' ')[1]
    if token != API_TOKEN:
        return jsonify({"error": "Ungültiger Token"}), 403

    # JSON einlesen und validieren
    try:
        payload = request.get_json()
        message = payload['message']
        platform = message['platform']
        title = message['title']
        text = message['message']
    except (TypeError, KeyError):
        return jsonify({"error": "Ungültige JSON-Struktur"}), 400

    data = {
        "severity": "info",
        "notification_title": title,
        "notification_text": text
    }

    result = {"responses": []}

    if platform in ['all', 'apple']:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(SERVER_URL, json=data, headers=headers)
            response_data = response.json()
        except ValueError:
            response_data = {"error": "Ungültige Serverantwort"}
        except Exception as e:
            response_data = {"error": str(e)}

        result["responses"].append({
            "platform": "Apple",
            "response": response_data
        })

    if platform in ['all', 'android']:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN2}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(SERVER2_URL, json=data, headers=headers)
            response_data = response.json()
        except ValueError:
            response_data = {"error": "Ungültige Serverantwort"}
        except Exception as e:
            response_data = {"error": str(e)}

        result["responses"].append({
            "platform": "Android",
            "response": response_data
        })

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)