import requests
import uuid
import json
import os
import sys
from flask import Flask, request, jsonify, render_template_string

def clear():
    os.system('clear')

def banner():
    print("""\u001B[1;32m
=============================================
   FACEBOOK API LOGIN TOOL (100% WORKING)
   (Get EAAAA Token & Cookies via API)
=============================================\u001B[0m""")

def convert_cookie_to_string(session_cookies):
    # API se milne wali cookies ko string banata hai
    cookie_str = ""
    for cookie in session_cookies:
        cookie_str += f"{cookie['name']}={cookie['value']};"
    return cookie_str

def login_with_api(email, password):
    # Yeh wo API URL hai jo Facebook ki purani Android Apps use karti hain
    url = "https://b-graph.facebook.com/auth/login"
    
    # Fake Device ID generate karna taake FB ko shaq na ho
    adid = str(uuid.uuid4())
    device_id = str(uuid.uuid4())
    
    # Official Facebook Android App ke parameters
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
        'locale': 'en_US',
        'client_country_code': 'US',
        'method': 'auth.login',
        'fb_api_req_friendly_name': 'authenticate',
        'fb_api_caller_class': 'com.facebook.account.login.protocol.Fb4aAuthHandler',
        'api_key': '882a8490361da98702bf97a021ddc14d', # Official FB API Key
        'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32' # Generic App Token
    }
    
    # Official User Agent (Bohot Zaroori hai)
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
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()
        
        # === SUCCESS CASE ===
        if 'access_token' in data:
            token = data['access_token']
            cookies = ""
            if 'session_cookies' in data:
                cookies = convert_cookie_to_string(data['session_cookies'])
                # Save to file
                with open("fb_pro_data.txt", "w") as f:
                    f.write(f"Token: {token}

Cookie: {cookies}")
            
            return {
                'success': True,
                'message': 'LOGIN SUCCESSFUL!',
                'token': token,
                'cookies': cookies,
                'saved': 'Data fb_pro_data.txt mein save ho gaya.'
            }
            
        # === ERROR CASES ===
        elif 'error' in data:
            error_msg = data['error'].get('message', 'Unknown Error')
            error_data = data['error'].get('error_data', '')
            
            reason = error_msg
            if "checkpoint" in error_msg.lower():
                reason = "Account Checkpoint par chala gaya hai.
App ya Browser mein login karke verify karein."
            elif "SMS" in str(error_data):
                reason = "2-Factor Authentication lagi hui hai.
Yeh tool 2FA bypass nahi kar sakta."
            else:
                reason = error_msg
                
            return {
                'success': False,
                'message': 'LOGIN FAILED!',
                'reason': reason
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': 'Internet Error!',
            'reason': str(e)
        }

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook API Login Tool</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Orbitron', monospace;
            background: radial-gradient(ellipse at bottom, #1b1035 0%, #000 70%);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        .container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 2rem;
            position: relative;
        }
        .glow-bg {
            position: absolute;
            border-radius: 50%;
            filter: blur(100px);
            opacity: 0.3;
            animation: glowPulse 4s ease-in-out infinite alternate;
            background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff88);
        }
        .glow2 { width: 400px; height: 400px; top: 10%; left: 10%; animation-delay: 0s; }
        .glow3 { width: 600px; height: 600px; bottom: 10%; right: 10%; animation-delay: 2s; }
        .login-box {
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(20px);
            border: 2px solid rgba(0, 245, 255, 0.3);
            border-radius: 30px;
            padding: 4rem;
            width: 100%;
            max-width: 600px;
            box-shadow: 0 0 50px rgba(0, 245, 255, 0.3), inset 0 0 50px rgba(0, 0, 0, 0.5);
            position: relative;
            animation: slideIn 1s ease-out;
        }
        .banner { text-align: center; margin-bottom: 3rem; }
        .neon-title {
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 40px #ff00ff;
            animation: neonFlicker 2s infinite alternate;
            margin-bottom: 1rem;
        }
        .neon-subtitle {
            font-size: 1.2rem;
            color: #00ff88;
            text-shadow: 0 0 10px #00ff88;
        }
        .input-group {
            position: relative;
            margin-bottom: 2.5rem;
        }
        input {
            width: 100%;
            padding: 1.5rem 2rem;
            font-size: 1.2rem;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(0, 245, 255, 0.3);
            border-radius: 20px;
            color: #fff;
            font-family: 'Orbitron', monospace;
            backdrop-filter: blur(10px);
            transition: all 0.4s ease;
        }
        input:focus {
            outline: none;
            border-color: #00f5ff;
            box-shadow: 0 0 20px rgba(0, 245, 255, 0.5), inset 0 0 20px rgba(0, 245, 255, 0.1);
            transform: scale(1.02);
        }
        .input-glow {
            position: absolute;
            top: -2px; left: -2px; right: -2px; bottom: -2px;
            background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff88);
            border-radius: 20px;
            z-index: -1;
            opacity: 0;
            transition: opacity 0.4s ease;
        }
        .input-group:focus-within .input-glow { opacity: 1; }
        .note {
            background: rgba(255, 165, 0, 0.1);
            border: 1px solid rgba(255, 165, 0, 0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2.5rem;
            text-align: center;
        }
        .note p {
            color: #ffaa00;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        .login-btn {
            width: 100%;
            padding: 1.5rem;
            font-size: 1.3rem;
            font-weight: 700;
            background: transparent;
            border: 3px solid transparent;
            border-radius: 25px;
            color: #00f5ff;
            font-family: 'Orbitron', monospace;
            text-transform: uppercase;
            letter-spacing: 2px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.4s ease;
        }
        .login-btn::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.3), transparent);
            transition: left 0.6s;
        }
        .login-btn:hover::before { left: 100%; }
        .login-btn .btn-glow {
            position: absolute;
            top: -3px; left: -3px; right: -3px; bottom: -3px;
            background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff88);
            border-radius: 25px;
            z-index: -1;
            filter: blur(10px);
            opacity: 0.7;
        }
        .login-btn:hover {
            border-color: #00f5ff;
            box-shadow: 0 0 30px rgba(0, 245, 255, 0.6), 0 0 60px rgba(255, 0, 255, 0.4), 0 0 100px rgba(0, 255, 136, 0.3);
            transform: translateY(-3px);
        }
        .login-btn.loading { pointer-events: none; }
        .result-box {
            margin-top: 2rem;
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.5s ease;
        }
        .result-box.show {
            opacity: 1;
            transform: translateY(0);
        }
        .success {
            background: rgba(0, 255, 136, 0.2);
            border: 2px solid #00ff88;
            color: #00ff88;
        }
        .error {
            background: rgba(255, 0, 0, 0.2);
            border: 2px solid #ff4444;
            color: #ff4444;
        }
        .token-box, .cookie-box {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 1rem;
            margin: 1rem 0;
            text-align: left;
        }
        textarea {
            width: 100%;
            height: 100px;
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid rgba(0, 245, 255, 0.5);
            border-radius: 10px;
            color: #00f5ff;
            font-family: monospace;
            padding: 1rem;
            resize: vertical;
        }
        .spinner {
            width: 40px; height: 40px;
            border: 4px solid rgba(0, 245, 255, 0.3);
            border-top: 4px solid #00f5ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes glowPulse {
            0% { opacity: 0.3; transform: scale(1); }
            100% { opacity: 0.6; transform: scale(1.1); }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(50px) scale(0.9); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes neonFlicker {
            0%, 18%, 22%, 25%, 53%, 57%, 100% { text-shadow: 0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 40px #ff00ff; }
            20%, 24%, 55% { text-shadow: none; }
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .login-box { padding: 2rem; margin: 1rem; }
            .neon-title { font-size: 2rem; }
            input { padding: 1.2rem 1.5rem; font-size: 1.1rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glow-bg glow2"></div>
        <div class="glow-bg glow3"></div>
        
        <div class="login-box">
            <div class="banner">
                <h1 class="neon-title">FACEBOOK API LOGIN TOOL</h1>
                <p class="neon-subtitle">100% Working - Get EAAAA Token & Cookies</p>
            </div>
            
            <form id="loginForm">
                <div class="input-group">
                    <input type="text" id="email" name="email" placeholder="Enter Email/ID/Number" required>
                    <div class="input-glow"></div>
                </div>
                
                <div class="input-group">
                    <input type="password" id="password" name="password" placeholder="Enter Password" required>
                    <div class="input-glow"></div>
                </div>
                
                <div class="note">
                    <p>NOTE: 2-Factor Auth (OTP) wale accounts par ye work nahi karega.</p>
                    <p>Normal password wale accounts use karein.</p>
                </div>
                
                <button type="submit" class="login-btn">
                    <span class="btn-text">LOGIN WITH API</span>
                    <span class="btn-glow"></span>
                </button>
            </form>
            
            <div id="result" class="result-box"></div>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.querySelector('.login-btn');
            const resultDiv = document.getElementById('result');
            
            btn.classList.add('loading');
            resultDiv.classList.remove('success', 'error', 'show');
            resultDiv.innerHTML = '<div class="spinner"></div><p>API Request bhej raha hoon...</p>';
            resultDiv.classList.add('show');
            
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                btn.classList.remove('loading');
                resultDiv.classList.remove('show');
                
                setTimeout(() => {
                    if (data.success) {
                        resultDiv.classList.add('success', 'show');
                        resultDiv.innerHTML = `
                            <h3>${data.message}</h3>
                            <div class="token-box">
                                <strong>Token (EAAAA):</strong><br>
                                <textarea readonly>${data.token}</textarea>
                            </div>
                            ${data.cookies ? `
                            <div class="cookie-box">
                                <strong>Cookies:</strong><br>
                                <textarea readonly>${data.cookies}</textarea>
                            </div>` : ''}
                            <p>${data.saved}</p>
                        `;
                    } else {
                        resultDiv.classList.add('error', 'show');
                        resultDiv.innerHTML = `<h3>${data.message}</h3><p>${data.reason}</p>`;
                    }
                }, 500);
                
            } catch (error) {
                btn.classList.remove('loading');
                resultDiv.classList.add('error', 'show');
                resultDiv.innerHTML = '<h3>Network Error!</h3>';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Empty input not allowed.'})
        
    result = login_with_api(email, password)
    return jsonify(result)

def main():
    clear()
    banner()
    
    print("
[NOTE] 2-Factor Auth (OTP) wale accounts par ye work nahi karega.")
    print("       Normal password wale accounts use karein.
")
    print("       Flask Web Server: http://localhost:5000")
    print("       Ya Termux/Android me: http://0.0.0.0:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
