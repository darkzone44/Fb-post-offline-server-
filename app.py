import requests
import uuid
import os
from flask import Flask, request, jsonify, render_template_string

def clear():
    os.system('clear')

def banner():
    print("\u001B[1;32m=============================================")
    print("   FACEBOOK API LOGIN TOOL (100% WORKING)")
    print("   (Get EAAAA Token & Cookies via API)")
    print("=============================================\u001B[0m")

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

            return {'success': True, 'message': 'LOGIN SUCCESSFUL!', 'token': token, 'cookies': cookies, 'saved': 'Data fb_pro_data.txt mein save ho gaya.'}

        elif 'error' in data:
            error_msg = data['error'].get('message', 'Unknown Error')
            error_data = data['error'].get('error_data', '')

            reason = error_msg
            if "checkpoint" in error_msg.lower():
                reason = "Account Checkpoint par chala gaya hai. App ya Browser mein login karke verify karein."
            elif "SMS" in str(error_data):
                reason = "2-Factor Authentication lagi hui hai. Yeh tool 2FA bypass nahi kar sakta."

            return {'success': False, 'message': 'LOGIN FAILED!', 'reason': reason}

    except Exception as e:
        return {'success': False, 'message': 'Internet Error!', 'reason': str(e)}

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Facebook API Login Tool</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet" />
<style>
  /* Full neon style and large layout CSS here as shared before */
  /* For brevity, please use the CSS given in previous responses */
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
        <input type="text" id="email" name="email" placeholder="Enter Email/ID/Number" required />
        <div class="input-glow"></div>
      </div>
      <div class="input-group">
        <input type="password" id="password" name="password" placeholder="Enter Password" required />
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
    const response = await fetch('/login', { method: 'POST', body: formData });
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
    return render_template_string(HTML_PAGE)

@app.route('/login', methods=['POST'])
def login_route():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Empty input not allowed.'})
    result = login_with_api(email, password)
    return jsonify(result)

if __name__ == '__main__':
    clear()
    banner()
    app.run(host='0.0.0.0', port=5000, debug=True)
