from flask import Flask, request, jsonify, render_template_string
import requests
import uuid
import os
from datetime import datetime

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
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        data = response.json()
        
        if 'access_token' in data:
            token = data['access_token']
            cookies = ""
            if 'session_cookies' in data:
                cookies = convert_cookie_to_string(data['session_cookies'])
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_content = "
=== " + email + " ===
Token: " + token + "
Cookies: " + cookies + "
Time: " + timestamp + "

"
            with open("fb_pro_data.txt", "a") as f:
                f.write(file_content)
            
            return {
                'success': True,
                'token': token,
                'cookies': cookies,
                'message': 'LOGIN SUCCESSFUL! EAAAA Token Generated Successfully.'
            }
        elif 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            if 'checkpoint' in error_msg.lower():
                return {'success': False, 'message': 'Account checkpointed. Verify in Facebook app/browser first.', 'type': 'checkpoint'}
            elif any(x in error_msg.lower() for x in ['sms', '2fa', 'otp']):
                return {'success': False, 'message': '2FA/OTP enabled on this account. Use normal password account.', 'type': '2fa'}
            else:
                return {'success': False, 'message': error_msg, 'type': 'error'}
        else:
            return {'success': False, 'message': 'Invalid API response received.', 'type': 'unknown'}
    except Exception as e:
        return {'success': False, 'message': 'Network error: ' + str(e), 'type': 'network'}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook API Login Tool - Working</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {margin:0;padding:0;box-sizing:border-box;}
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }
        .container {
            width: 100%;
            max-width: 450px;
            padding: 20px;
        }
        .card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo i {
            font-size: 48px;
            color: #4267B2;
            margin-bottom: 10px;
        }
        .logo h1 {
            font-size: 24px;
            font-weight: 700;
            color: #333;
            margin: 0;
        }
        .logo p {
            color: #666;
            font-size: 14px;
            margin: 5px 0 0 0;
        }
        .form-group {
            position: relative;
            margin-bottom: 20px;
        }
        .form-group input {
            width: 100%;
            padding: 15px 20px 15px 45px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }
        .form-group input:focus {
            outline: none;
            border-color: #4267B2;
            box-shadow: 0 0 0 3px rgba(66,103,178,0.1);
            background: white;
        }
        .form-group i {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: #999;
            font-size: 18px;
            transition: 0.3s ease;
        }
        .form-group input:focus + i {
            color: #4267B2;
        }
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #4267B2, #365899);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(66,103,178,0.3);
        }
        .btn.loading {
            pointer-events: none;
            opacity: 0.7;
        }
        .btn.loading:after {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            top: 50%;
            left: 50%;
            margin-left: -10px;
            margin-top: -10px;
            border: 2px solid transparent;
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            transform: scale(0.8);
            opacity: 0;
            transition: all 0.4s ease;
        }
        .result.show {
            transform: scale(1);
            opacity: 1;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .result pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: left;
            font-size: 13px;
            max-height: 200px;
            overflow: auto;
            margin-top: 10px;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .clear-btn {
            width: 100%;
            padding: 12px;
            margin-top: 15px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: 0.3s ease;
        }
        .clear-btn:hover {
            background: #5a6268;
        }
        .note {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            font-size: 13px;
            text-align: center;
        }
        @keyframes spin {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @media (max-width: 480px) {
            .container { padding: 15px; }
            .card { padding: 30px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <i class="fab fa-facebook-f"></i>
                <h1>FB API Login Tool</h1>
                <p>Get EAAAA Token + Cookies</p>
            </div>
            
            <div class="form-group">
                <input type="text" id="email" placeholder="Email / Phone / Username">
                <i class="fas fa-user"></i>
            </div>
            
            <div class="form-group">
                <input type="password" id="password" placeholder="Password">
                <i class="fas fa-lock"></i>
            </div>
            
            <button class="btn" id="loginBtn">
                <i class="fas fa-rocket"></i> Generate Token
            </button>
            
            <div id="result" class="result"></div>
            
            <button class="clear-btn" id="clearBtn" style="display: none;">
                <i class="fas fa-trash"></i> Clear Data File
            </button>
            
            <div class="note">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Important:</strong> 2FA/OTP accounts won't work. Use normal password accounts only. Data saves to fb_pro_data.txt
            </div>
        </div>
    </div>

    <script>
        document.getElementById('loginBtn').onclick = async function() {
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();
            const btn = document.getElementById('loginBtn');
            const result = document.getElementById('result');
            const clearBtn = document.getElementById('clearBtn');
            
            if (!email || !password) {
                showResult('Please enter both email and password!', 'error');
                return;
            }
            
            btn.classList.add('loading');
            btn.innerHTML = '';
            result.classList.remove('show');
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email, password: password})
                });
                
                const data = await response.json();
                
                btn.classList.remove('loading');
                btn.innerHTML = '<i class="fas fa-rocket"></i> Generate Token';
                
                if (data.success) {
                    let html = '<strong>' + data.message + '</strong><br><br><strong>Token:</strong><br><pre>' + data.token + '</pre>';
                    if (data.cookies) {
                        html += '<br><strong>Cookies:</strong><br><pre>' + data.cookies + '</pre>';
                    }
                    showResult(html, 'success');
                    clearBtn.style.display = 'block';
                } else {
                    let type = 'error';
                    if (data.type === 'checkpoint' || data.type === '2fa') {
                        type = 'warning';
                    }
                    showResult(data.message, type);
                }
            } catch (error) {
                btn.classList.remove('loading');
                btn.innerHTML = '<i class="fas fa-rocket"></i> Generate Token';
                showResult('Network error. Please check your connection.', 'error');
            }
        };
        
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = 'result show ' + type;
        }
        
        document.getElementById('clearBtn').onclick = async function() {
            try {
                await fetch('/api/clear');
                document.getElementById('result').classList.remove('show');
                this.style.display = 'none';
                document.getElementById('email').value = '';
                document.getElementById('password').value = '';
                showResult('Data file cleared successfully!', 'success');
            } catch(e) {
                showResult('Error clearing data!', 'error');
            }
        };
        
        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('loginBtn').click();
            }
        });
        
        document.getElementById('email').focus();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required!', 'type': 'empty'})
    
    result = login_with_api(email, password)
    return jsonify(result)

@app.route('/api/clear')
def api_clear():
    try:
        if os.path.exists('fb_pro_data.txt'):
            os.remove('fb_pro_data.txt')
        return jsonify({'success': True, 'message': 'Data cleared successfully!'})
    except:
        return jsonify({'success': False, 'message': 'Failed to clear data!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
