#!/usr/bin/python3

# _*_ coding:utf-8 _*_

# it logs all the requests made to the sserver
# it will be using default HTTP port 80

# HTTP honeypot
# usage: from honeyhttp import runHttp 

from flask import Flask, request, send_from_directory, redirect, url_for
from datetime import datetime
import os
import json
import requests
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

    return send_from_directory('website', 'login.html')

# redirect unauthorized dashboard access
@app.route('/dashboard', methods=['GET'])
def dashboard():
    return redirect('/login')

@app.route('/robots.txt', methods=['GET'])
def robots():
    return send_from_directory('website', 'robots.txt')

# run
def runHttp():
    cert_file = 'certificate/server.crt'
    key_file = 'certificate/server.key'

    # https
    app.run('0.0.0.0',port=443, ssl_context=(cert_file, key_file), debug=False)

if __name__ == '__main__':
    runHttp()
