#!/usr/bin/python3

# _*_ coding:utf-8 _*_

# it logs all the requests made to the sserver
# it will be using default HTTP port 80

# HTTP honeypot
# usage: from honeyhttp import runHttp 

from flask import Flask, request, redirect, url_for, Response
from datetime import datetime
import os
import json
from user_agents import parse

# init
app = Flask(__name__)
HTTP_LOGS = 'Logs/https.log'
GEO_API_URL = "http://ipinfo.io/{ip}"

os.makedirs('Logs', exist_ok=True)

# DRY

def getIP():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    return client_ip

def writedata(log_file,log_data):
    with open(log_file, 'a+') as fh:
        fh.write(json.dumps(log_data) + '\n')

# helper

def get_geo_info(ip):
    try:
        response = requests.get(GEO_API_URL.format(ip=ip))
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {}
    return {}

def parse_user_agent(user_agent_str):
    user_agent = parse(user_agent_str)
    return {
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}",
        "device": user_agent.device.family
    }


# logging requests

'''
{
  "timestamp": "21/12/2024-01:41:05",
  "event": "Login Attempt",
  "client_ip": "192.168.29.222",
  "region": "Unknown",
  "country": "Unknown",
  "location": "Unknown",
  "isp": "Unknown",
  "browser": "Chrome Mobile 131.0.0",
  "os": "Android 10",
  "device": "K",
  "username": "ryuk",
  "password": "find_me_boo"
}
'''

@app.before_request
def log_request():
    client_ip = getIP() # get ip
    geo_info = get_geo_info(client_ip)
    user_agent_info = parse_user_agent(request.headers.get('User-Agent', 'Unknown'))

    log_data = {
        'timestamp': datetime.now().strftime("%d/%m/%Y-%H:%M:%S"),
        'method': request.method,
        'path': request.path,
        'client_ip': client_ip,
        'region': geo_info.get('region', 'Unknown'),
        'country': geo_info.get('country', 'Unknown'),
        'location': geo_info.get('loc', 'Unknown'),
        'isp': geo_info.get('org', 'Unknown'),
        'browser': user_agent_info['browser'],
        'os': user_agent_info['os'],
        'device': user_agent_info['device'],
        'headers': dict(request.headers)
    }

    writedata(HTTP_LOGS,log_data) # dump data

# index page
@app.route('/', methods=['GET'])
def index():
    return redirect('/login', code=302)


# <--- honeypot --->
# handle login attempts
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', 'unknown')
        password = request.form.get('password', 'unknown')
        client_ip = getIP() # get ip

        geo_info = get_geo_info(client_ip)
        user_agent_info = parse_user_agent(request.headers.get('User-Agent', 'Unknown'))

        # Log creds and ip
        log_data = {
            'timestamp': datetime.now().strftime("%d/%m/%Y-%H:%M:%S"),
            'event': 'Login Attempt',
            'client_ip': client_ip,
            'region': geo_info.get('region', 'Unknown'),
            'country': geo_info.get('country', 'Unknown'),
            'location': geo_info.get('loc', 'Unknown'),
            'isp': geo_info.get('org', 'Unknown'),
            'browser': user_agent_info['browser'],
            'os': user_agent_info['os'],
            'device': user_agent_info['device'],
            'username': username,
            'password': password
        }

        writedata(HTTP_LOGS,log_data) # dump data

        return redirect(url_for('login', error="Invalid Login Credentials!"))

    login_page = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container { 
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                max-width: 400px;
                width: 100%;
            }
            .container h2 { text-align: center; }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; }
            .form-group input { width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #ccc; }
            .form-group input[type="submit"] {
                background-color: #007bff;
                color: #fff;
                cursor: pointer;
            }
            .form-group input[type="submit"]:hover {
                background-color: #0056b3;
            }
            #error-msg { color: red; font-weight: bold; text-align: center; }
            .captcha-group { margin-top: 20px; }
            .captcha-group label { font-weight: bold; }
        </style>
    </head>
    <body>
    <div class="container">
        <h2>User Portal</h2>
        <form action="/login" method="post" onsubmit="return validateCaptcha();">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="captcha-group">
                <label id="math-problem"></label><br>
                <input type="text" id="captcha" name="captcha" required placeholder="Enter your answer">
            </div>
            <input type="hidden" name="captcha_answer" id="captcha_answer">
            <div class="form-group">
                <input type="submit" value="Login">
            </div>
            <p id="error-msg"></p>
        </form>
    </div>
    <script>
        function getQueryParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        }

        function displayAndTrimError() {
            const errorMessage = getQueryParam('error');
            if (errorMessage) {
                const errorElement = document.getElementById('error-msg');
                if (errorElement) {
                    errorElement.textContent = decodeURIComponent(errorMessage);
                    errorElement.style.display = 'block';
                }
                const url = new URL(window.location.href);
                url.searchParams.delete('error');
                window.history.replaceState({}, document.title, url.pathname);
            }
        }

        function generateMathProblem() {
            const num1 = Math.floor(Math.random() * 10) + 1;
            const num2 = Math.floor(Math.random() * 10) + 1;
            const isAddition = Math.random() < 0.5;
            const problemLabel = document.getElementById('math-problem');
            const operator = isAddition ? '+' : '-';
            const answer = isAddition ? num1 + num2 : num1 - num2;

            if (problemLabel) {
                problemLabel.textContent = `${num1} ${operator} ${num2} = ?`;
            }
            return answer;
        }

        function validateCaptcha() {
            const userCaptcha = document.getElementById('captcha').value;
            const expectedCaptcha = document.getElementById('captcha_answer').value;

            if (parseInt(userCaptcha, 10) !== parseInt(expectedCaptcha, 10)) {
                alert("Incorrect CAPTCHA. Please try again.");
                return false;
            }
            return true;
        }

        window.addEventListener('DOMContentLoaded', () => {
            displayAndTrimError();
            const captchaAnswer = generateMathProblem();
            const captchaInput = document.getElementById('captcha_answer');
            if (captchaInput) {
                captchaInput.value = captchaAnswer;
            }
        });
    </script>
    </body>
    </html>
    '''
    return login_page
    


# redirect unauthorized dashboard access
@app.route('/dashboard', methods=['GET'])
def dashboard():
    return redirect('/login')

@app.route('/robots.txt', methods=['GET'])
def robots():
    robots_content = '''User-agent: *
Disallow: /login
    '''
    
    return Response(robots_content, content_type="text/plain")

# run
def runHttp():
    cert_file = 'certificate/server.crt'
    key_file = 'certificate/server.key'

    # https
    app.run('0.0.0.0',port=443, ssl_context=(cert_file, key_file), debug=False)

if __name__ == '__main__':
    runHttp()
