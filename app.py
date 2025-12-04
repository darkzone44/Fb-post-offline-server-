from flask import Flask, request, jsonify, render_template_string
import requests
import uuid
import os

app = Flask(__name__)

def convert_cookie_to_string(session_cookies):
    cookie_str = ""
    for cookie in session_cookies:
        cookie_str += cookie['name'] + "=" + cookie['value'] + ";"
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
        'locale': 'en_US',
        'client_country_code': 'US',
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
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()
        
        if 'access_token' in data:
            token = data['access_token']
            cookies = ""
            if 'session_cookies' in data:
                cookies = convert_cookie_to_string(data['session_cookies'])
                with open("fb_pro_data.txt", "w") as f:
                    f.write("Token: " + token + "

Cookie: " + cookies)
            
            return {
                'success': True,
                'message': 'LOGIN SUCCESSFUL!',
                'token': token,
                'cookies': cookies,
                'saved': 'Data fb_pro_data.txt mein save ho gaya.'
            }
            
        elif 'error' in data:
            error_msg = data['error'].get('message', 'Unknown Error')
            error_data = data['error'].get('error_data', '')
            
            reason = error_msg
            if "checkpoint" in error_msg.lower():
                reason = "Account Checkpoint par chala gaya hai. App ya Browser mein login karke verify karein."
            elif "SMS" in str(error_data):
                reason = "2-Factor Authentication lagi hui hai. Yeh tool 2FA bypass nahi kar sakta."
                
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook API Login Tool</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Orbitron', monospace;
            background: linear-gradient(45deg, #1b1035, #000);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .login-box {
            background: rgba(0,0,0,0.9);
            border: 2px solid #00f5ff;
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 0 50px rgba(0,245,255,0.5);
        }
        .banner { text-align: center; margin-bottom: 30px; }
        .neon-title {
            font-size: 28px;
            color: #00f5ff;
            text-shadow: 0 0 10px #00f5ff;
            margin-bottom: 10px;
        }
        .neon-subtitle { color: #00ff88; font-size: 16px; }
        input {
            width: 100%;
            padding: 15px;
            margin-bottom: 20px;
            border: 2px solid #00f5ff;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 16px;
            font-family: 'Orbitron', monospace;
        }
        input:focus { outline: none; box-shadow: 0 0 20px #00f5ff; }
        .note {
            background: rgba(255,165,0,0.2);
            border: 1px solid #ffaa00;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
            color: #ffaa00;
            font-size: 14px;
        }
        .login-btn {
            width: 100%;
            padding: 15px;
            background: transparent;
            border: 2px solid #00f5ff;
            border-radius: 10px;
            color: #00f5ff;
            font-size: 18px;
            font-family: 'Orbitron', monospace;
            cursor: pointer;
            transition: all 0.3s;
        }
        .login-btn:hover {
            background: #00f5ff;
            color: black;
            box-shadow: 0 0 20px #00f5ff;
        }
        .result-box {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }
        .success { 
            background: rgba(0,255,136,0.2); 
            border: 2px solid #00ff88; 
            color: #00ff88;
            display: block;
        }
        .error { 
            background: rgba(255,0,0,0.2); 
            border: 2px solid #ff4444; 
            color: #ff4444;
            display: block;
        }
        textarea {
            width: 100%;
            height: 100px;
            margin-top: 10px;
            background: rgba(0,0,0,0.7);
            border: 1px solid #00f5ff;
            border-radius: 5px;
            color: #00f5ff;
            padding: 10px;
            font-family: monospace;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(0,245,255,0.3);
            border-top: 4px solid #00f5ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="banner">
            <h1 class="neon-title">FACEBOOK API LOGIN TOOL</h1>
            <p class="neon-subtitle">100% Working - Get EAAAA Token & Cookies</p>
        </div>
        
        <form id="loginForm">
            <input type="text" id="email" name="email" placeholder="Enter Email/ID/Number" required>
            <input type="password" id="password" name="password" placeholder="Enter Password" required>
            <div class="note">
                <p>NOTE: 2-Factor Auth (OTP) wale accounts par ye work nahi karega.</p>
                <p>Normal password wale accounts use karein.</p>
            </div>
            <button type="submit" class="login-btn">LOGIN WITH API</button>
        </form>
        
        <div id="result" class="result-box"></div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            var btn = document.querySelector('.login-btn');
            var resultDiv = document.getElementById('result');
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;display:inline-block;vertical-align:middle;margin-left:10px;"></div> Loading...';
            resultDiv.innerHTML = '<div class="spinner"></div><p>API Request bhej raha hoon...</p>';
            resultDiv.className = 'result-box';
            
            var formData = new FormData(e.target);
            
            try {
                var response = await fetch('/login', {
                    method: 'POST',
                    body: formData
                });
                var data = await response.json();
                
                btn.disabled = false;
                btn.innerHTML = 'LOGIN WITH API';
                
                if (data.success) {
                    resultDiv.className = 'result-box success';
                    resultDiv.innerHTML = '<h3>' + data.message + '</h3>' +
                        '<div><strong>Token (EAAAA):</strong><br><textarea readonly>' + data.token + '</textarea></div>' +
                        (data.cookies ? '<div><strong>Cookies:</strong><br><textarea readonly>' + data.cookies + '</textarea></div>' : '') +
                        '<p>' + data.saved + '</p>';
                } else {
                    resultDiv.className = 'result-box error';
                    resultDiv.innerHTML = '<h3>' + data.message + '</h3><p>' + data.reason + '</p>';
                }
            } catch (error) {
                btn.disabled = false;
                btn.innerHTML = 'LOGIN WITH API';
                resultDiv.className = 'result-box error';
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
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Empty input not allowed.'})
    
    result = login_with_api(email, password)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
