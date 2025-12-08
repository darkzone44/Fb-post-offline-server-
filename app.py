from flask import Flask, request, jsonify, render_template_string
import requests
import uuid
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'fb-login-tool-2025-super-secure-key'

def convert_cookie_to_string(session_cookies):
    cookie_str = ""
    for cookie in session_cookies:
        cookie_str += cookie['name'] + "=" + cookie['value'] + "; "
    return cookie_str.strip()

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
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        data = response.json()
        
        if 'access_token' in data:
            data['success'] = True
            # Save to file
            result = {
                'email': email,
                'access_token': data.get('access_token'),
                'cookies': convert_cookie_to_string(data.get('session_cookies', [])),
                'timestamp': datetime.now().isoformat()
            }
            with open('fb_pro_data.txt', 'w') as f:
                f.write(json.dumps(result, indent=2))
            data['saved'] = True
        elif 'errors' in data:
            data['success'] = False
            data['type'] = 'auth_error'
        else:
            data['success'] = False
            data['type'] = 'unknown'
            
        return data
        
    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'Timeout - Slow network', 'type': 'network'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': str(e), 'type': 'network'}
    except json.JSONDecodeError:
        return {'success': False, 'message': 'Invalid response from Facebook', 'type': 'parse'}
    except Exception as e:
        return {'success': False, 'message': str(e), 'type': 'unknown'}

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    result = None
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            message = "Email aur Password dono daalo bhai! 😅"
        else:
            result = login_with_api(email, password)
            if result.get('success'):
                message = "🎉 SUCCESS! fb_pro_data.txt file mein save ho gaya!"
            elif result.get('type') == 'network':
                message = "🌐 Network issue - Internet check karo!"
            else:
                message = f"❌ Error: {result.get('message', 'Unknown error')}"
    
    HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB Login Tool - 100% Working 🔥</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #e0e0e0;
        }
        .container {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            text-align: center;
            color: #fff;
            margin-bottom: 10px;
            font-weight: 700;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #a0a0a0;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .input-group {
            position: relative;
            margin-bottom: 20px;
        }
        input {
            width: 100%;
            padding: 16px 20px 16px 50px;
            background: rgba(255,255,255,0.08);
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        input:focus {
            outline: none;
            border-color: #4267b2;
            background: rgba(255,255,255,0.12);
            box-shadow: 0 0 20px rgba(66,103,178,0.3);
        }
        input::placeholder { color: #888; }
        .input-icon {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: #888;
            font-size: 18px;
        }
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #4267b2, #365899);
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
            box-shadow: 0 10px 25px rgba(66,103,178,0.4);
        }
        .btn:active { transform: translateY(0); }
        .message {
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: 500;
            text-align: center;
            animation: slideIn 0.3s ease;
        }
        .success { background: rgba(34,197,94,0.2); border: 1px solid #22c55e; color: #22c55e; }
        .error { background: rgba(239,68,68,0.2); border: 1px solid #ef4444; color: #ef4444; }
        .loading { 
            display: none; 
            text-align: center; 
            padding: 20px;
            color: #60a5fa;
        }
        .spinner {
            border: 3px solid rgba(96,165,250,0.3);
            border-top: 3px solid #60a5fa;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .file-info {
            background: rgba(59,130,246,0.1);
            border: 1px solid rgba(59,130,246,0.3);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            font-size: 14px;
        }
        @media (max-width: 480px) {
            .container { padding: 30px 20px; margin: 10px; }
            h1 { font-size: 24px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><i class="fab fa-facebook"></i> FB Login Tool</h1>
        <p class="subtitle">Email/Password se Token + Cookies Generate karo 🔥</p>
        
        <form method="POST" id="loginForm">
            <div class="input-group">
                <i class="fas fa-envelope input-icon"></i>
                <input type="email" name="email" placeholder="Email ID ya Phone Number" required>
            </div>
            <div class="input-group">
                <i class="fas fa-lock input-icon"></i>
                <input type="password" name="password" placeholder="Password" required>
            </div>
            <button type="submit" class="btn" id="submitBtn">
                <i class="fas fa-rocket"></i> Generate Token & Cookies
            </button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>Facebook se data le rahe hain... Thoda wait karo 🚀</div>
        </div>
        
        {% if message %}
        <div class="message {{ 'success' if 'SUCCESS' in message else 'error' }}">{{ message }}</div>
        {% endif %}
        
        {% if result and result.success %}
        <div class="file-info">
            <i class="fas fa-file-alt"></i> 
            <strong>fb_pro_data.txt</strong> file ban gayi! 
            Token + Cookies save ho gaye ✅
        </div>
        {% endif %}
        
        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #888;">
            <p>Local: python app.py → localhost:5000</p>
            <p>Deploy: Render.com/Heroku ready ✅</p>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').onsubmit = function() {
            document.getElementById('submitBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('submitBtn').disabled = true;
        };
    </script>
</body>
</html>
    '''
    
    return render_template_string(HTML_TEMPLATE, message=message, result=result)

@app.route('/clear', methods=['POST'])
def clear_data():
    try:
        if os.path.exists('fb_pro_data.txt'):
            os.remove('fb_pro_data.txt')
        return jsonify({'success': True, 'message': 'Data cleared! 🚀'})
    except:
        return jsonify({'success': False, 'message': 'Clear failed!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 FB Login Tool starting on port", port)
    print("📱 Local: http://localhost:" + str(port))
    print("🌐 Deploy: Render.com ready!")
    app.run(host='0.0.0.0', port=port, debug=False)
