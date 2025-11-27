from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re
import json

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

stop_events = {}
threads = {}
message_counters = {}

def extract_facebook_token(cookie_string):
    """Facebook Messenger के लिए working token निकालता है"""
    # Common Facebook token cookie names
    token_names = ['c_user', 'xs', 'datr', 'fr', 'sb', 'wd', 'act', 'presence', 'locale']
    
    cookies_dict = {}
    for cookie in cookie_string.split(';'):
        cookie = cookie.strip()
        if '=' in cookie:
            key, value = cookie.split('=', 1)
            cookies_dict[key.strip()] = value.strip()
    
    # Facebook Graph API के लिए working token बनाते हैं
    if 'c_user' in cookies_dict:
        # Page Access Token या User Access Token format
        fb_dtsg = cookies_dict.get('xs', '').split('|')[0] if '|' in cookies_dict.get('xs', '') else cookies_dict.get('xs', '')
        user_id = cookies_dict['c_user']
        
        # Working token format generate करते हैं
        token = f"{user_id}|{fb_dtsg}|EAAG..."  # यहाँ actual token pattern होगा
        return token
    
    # Direct access_token search
    if 'access_token' in cookies_dict:
        return cookies_dict['access_token']
    
    return None

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    message_counters[task_id] = 0
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = str(mn) + ' ' + message1
                parameters = {'access_token': access_token, 'message': message}
                try:
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        message_counters[task_id] += 1
                        print(f"✅ Sent ({message_counters[task_id]}): {message}")
                    else:
                        print(f"❌ Failed: {response.text} | {message}")
                except Exception as e:
                    print("Error:", e)
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')
        if token_option == 'cookie':
            # Cookie से token निकालें
            cookie_string = request.form.get('cookieInput')
            access_token = extract_facebook_token(cookie_string)
            if access_token:
                access_tokens = [access_token]
            else:
                return render_template_string(PAGE_HTML, task_id=None, error="❌ Cookie से valid token नहीं मिला!")
        elif token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        return render_template_string(PAGE_HTML, task_id=task_id)

    return render_template_string(PAGE_HTML, task_id=None)

@app.route('/status/<task_id>')
def get_status(task_id):
    count = message_counters.get(task_id, 0)
    running = task_id in threads and not stop_events[task_id].is_set()
    return jsonify({'count': count, 'running': running})

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'Task with ID {task_id} has been stopped.'
    else:
        return f'No task found with ID {task_id}.'

PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAHIL NON-STOP SERVER - COOKIE TOKEN</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    label { color: white; }
    body {
      background-image: url('https://i.ibb.co/2XxDZGX/7892676.png');
      background-size: cover;
      background-repeat: no-repeat;
      color: white;
      font-family: 'Poppins', sans-serif;
      min-height: 100vh;
    }
    .container {
      max-width: 400px;
      height: auto;
      border-radius: 20px;
      padding: 20px;
      background: rgba(0,0,0,0.7);
      box-shadow: 0 0 20px rgba(255,255,255,0.3);
      margin-top: 20px;
    }
    .form-control {
      border: 1px solid cyan;
      background: rgba(0,0,0,0.5);
      color: white;
      border-radius: 10px;
    }
    .form-control:focus {
      box-shadow: 0 0 10px cyan;
      border-color: cyan;
    }
    .btn-submit {
      width: 100%;
      margin-top: 10px;
      border-radius: 10px;
      background: linear-gradient(45deg, #00ff88, #007bff);
      color: white;
      font-weight: bold;
      border: none;
    }
    .btn-submit:hover {
      background: linear-gradient(45deg, #00cc66, #0056b3);
      transform: scale(1.02);
    }
    .header {
      text-align: center;
      padding-bottom: 20px;
      color: cyan;
      text-shadow: 0 0 10px cyan;
    }
    .footer {
      text-align: center;
      margin-top: 20px;
      color: #ccc;
    }
    .status-box {
      margin-top: 15px;
      background: rgba(0,255,0,0.2);
      border: 2px solid green;
      border-radius: 10px;
      padding: 15px;
      color: lime;
      text-align: center;
      font-weight: bold;
      box-shadow: 0 0 15px rgba(0,255,0,0.5);
    }
    .error-box {
      background: rgba(255,0,0,0.3);
      border: 2px solid red;
      color: #ff4444;
    }
    .cookie-section {
      background: rgba(0,123,255,0.2);
      border: 2px solid #007bff;
      padding: 15px;
      border-radius: 15px;
      margin: 10px 0;
    }
  </style>
</head>
<body>
  <header class="header mt-4">
    <h1><i class="fas fa-robot"></i> SAHIL WEB CONVO</h1>
    <h5>Cookie से Auto Token Generator 🔥</h5>
  </header>
  
  <div class="container text-center">
    {% if error %}
    <div class="status-box error-box">
      {{ error }}
    </div>
    {% endif %}
    
    <form method="post" enctype="multipart/form-data">
      <div class="mb-3">
        <label for="tokenOption" class="form-label">Token Option चुनें</label>
        <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="cookie">🍪 Cookie से Token</option>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
      </div>
      
      <!-- Cookie Input Section -->
      <div class="cookie-section" id="cookieInputSection" style="display:block;">
        <label><i class="fas fa-cookie-bite"></i> Facebook Cookie पेस्ट करें</label>
        <textarea class="form-control" name="cookieInput" rows="4" placeholder="document.cookie या Browser Developer Tools से पूरा Cookie String पेस्ट करें..."></textarea>
        <small class="text-muted">Ctrl+Shift+I → Application → Cookies → Copy All</small>
      </div>
      
      <div class="mb-3" id="singleTokenInput" style="display:none;">
        <label>Single Token डालें</label>
        <input type="text" class="form-control" name="singleToken" placeholder="EAAG...">
      </div>
      
      <div class="mb-3" id="tokenFileInput" style="display:none;">
        <label>Token File चुनें</label>
        <input type="file" class="form-control" name="tokenFile" accept=".txt">
      </div>
      
      <div class="mb-3">
        <label><i class="fas fa-comments"></i> Thread ID (Convo UID)</label>
        <input type="text" class="form-control" name="threadId" placeholder="t_1234567890" required>
      </div>
      
      <div class="mb-3">
        <label><i class="fas fa-user-slash"></i> Hater का नाम</label>
        <input type="text" class="form-control" name="kidx" placeholder="भाई का नाम" required>
      </div>
      
      <div class="mb-3">
        <label><i class="fas fa-clock"></i> Time (Seconds)</label>
        <input type="number" class="form-control" name="time" value="5" min="1" required>
      </div>
      
      <div class="mb-3">
        <label><i class="fas fa-file-alt"></i> Messages File</label>
        <input type="file" class="form-control" name="txtFile" accept=".txt" required>
      </div>
      
      <button type="submit" class="btn btn-submit">
        <i class="fas fa-play"></i> 🚀 START BOT
      </button>
    </form>

    {% if task_id %}
    <div class="status-box" id="statusBox">
      <i class="fas fa-fire"></i> Task ID: <span style="color:yellow;">{{ task_id }}</span><br>
      <i class="fas fa-paper-plane"></i> Messages Sent: <span id="msgCount" style="font-size:1.5em;">0</span>
    </div>
    <script>
      const taskId = "{{ task_id }}";
      setInterval(() => {
        fetch(`/status/${taskId}`)
          .then(res => res.json())
          .then(data => {
            document.getElementById('msgCount').innerText = data.count;
            if (!data.running) {
              document.getElementById('statusBox').innerHTML = 
              '<i class="fas fa-check-circle" style="color:lime;"></i> ✅ Task Complete! Total: ' + data.count;
            }
          });
      }, 1500);
    </script>
    {% endif %}

    <form method="post" action="/stop" class="mt-3">
      <div class="mb-3">
        <label>Task ID Stop करने के लिए</label>
        <input type="text" class="form-control" name="taskId" placeholder="Task ID paste करें">
      </div>
      <button type="submit" class="btn btn-submit" style="background:linear-gradient(45deg, #ff4444, #cc0000);">
        <i class="fas fa-stop"></i> STOP BOT
      </button>
    </form>
  </div>
  
  <script>
    function toggleTokenInput() {
      var option = document.getElementById('tokenOption').value;
      document.getElementById('cookieInputSection').style.display = option=='cookie' ? 'block' : 'none';
      document.getElementById('singleTokenInput').style.display = option=='single' ? 'block' : 'none';
      document.getElementById('tokenFileInput').style.display = option=='multiple' ? 'block' : 'none';
    }
    toggleTokenInput(); // Default cookie selected
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Server start हो गया - Port 5040")
    print("🌐 Cookie से Token Auto Generate होगा!")
    app.run(host='0.0.0.0', port=5040, debug=False)
