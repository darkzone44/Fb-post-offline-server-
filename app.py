from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re

app = Flask(__name__)
app.debug = True

# common browser-like headers (will be copied and extended per-request)
BASE_HEADERS = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.facebook.com/'
}

stop_events = {}
threads = {}
message_counters = {}

def fetch_fb_dtsg_and_jazoest(cookie):
    """
    Fetch a page (messages thread landing) to extract fb_dtsg and jazoest values
    Returns (fb_dtsg, jazoest, user_id) or (None, None, None) on failure.
    """
    try:
        headers = BASE_HEADERS.copy()
        headers['Cookie'] = cookie
        # Use the mobile messages thread root which usually contains fb_dtsg in page
        r = requests.get("https://www.facebook.com/messages", headers=headers, timeout=12)
        text = r.text

        # fb_dtsg extraction
        fb_dtsg = None
        jazoest = None

        # Try common patterns for fb_dtsg / jazoest (page may vary)
        m = re.search(r'name="fb_dtsg" value="([^"]+)"', text)
        if m:
            fb_dtsg = m.group(1)
        else:
            m = re.search(r'fb_dtsg\\":\\"([^\\"]+)', text)
            if m:
                fb_dtsg = m.group(1)

        m2 = re.search(r'name="jazoest" value="([^"]+)"', text)
        if m2:
            jazoest = m2.group(1)
        else:
            m2 = re.search(r'jazoest\\":\\"([^\\"]+)', text)
            if m2:
                jazoest = m2.group(1)

        # user id (c_user) from cookie if present
        user_id = None
        mu = re.search(r'c_user=(\d+)', cookie)
        if mu:
            user_id = mu.group(1)

        return fb_dtsg, jazoest, user_id
    except Exception as e:
        print("fetch_fb_dtsg error:", e)
        return None, None, None

def send_messages_with_cookie(cookie, thread_id, mn, time_interval, messages, task_id):
    """
    Send messages to given thread using cookie-based web endpoint.
    This tries to mimic browser messenger requests by extracting fb_dtsg and
    posting to a messenger endpoint.
    """
    stop_event = stop_events[task_id]
    message_counters[task_id] = 0

    fb_dtsg, jazoest, user_id = fetch_fb_dtsg_and_jazoest(cookie)
    if not fb_dtsg:
        print("❌ Could not extract fb_dtsg / jazoest from session. Message sending aborted for this cookie.")
        return

    headers = BASE_HEADERS.copy()
    headers['Cookie'] = cookie
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    headers['Referer'] = f'https://www.facebook.com/messages/t/{thread_id}'

    # Sometimes messenger requires an AJAX endpoint with specific query params
    post_url = "https://www.facebook.com/messaging/send/"

    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            message_text = str(mn) + ' ' + message1
            # payload tuned to mimic web messenger posting form fields
            payload = {
                'fb_dtsg': fb_dtsg,
                'jazoest': jazoest or '',
                'body': message_text,
                # include recipient id. For group/conversation threads the format may vary;
                # we include `to` or `ids[]` as a fallback.
                'ids[0]': thread_id,
                'send_time': '',
                # required flags used by FB in some flows
                '__user': user_id or '',
                '__a': '1'
            }

            try:
                r = requests.post(post_url, data=payload, headers=headers, timeout=12)
                # Facebook often returns JSON prefixed with )]}', so be tolerant
                status_ok = False
                text = r.text if r is not None else ''
                if r.status_code == 200:
                    # naive success detection: presence of "client_id" or "success" or status code 200
                    if '"message_id"' in text or '"success":' in text or r.status_code == 200:
                        status_ok = True

                if status_ok:
                    message_counters[task_id] += 1
                    print(f"✅ Sent ({message_counters[task_id]}): {message_text}")
                else:
                    print(f"❌ Failed to send (maybe blocked or changed endpoint). Status: {r.status_code}")
                    # Optional: print short response snippet for debugging
                    snippet = text.replace('\n',' ')[:200]
                    print("   Resp snippet:", snippet)
            except Exception as e:
                print("Error sending message:", e)

            time.sleep(float(time_interval))

def send_messages_with_tokens(access_tokens, thread_id, mn, time_interval, messages, task_id):
    """
    Fallback: if user supplied access_tokens (access_token strings), use Graph API endpoint.
    This part preserves original behavior (requires tokens that are valid and permitted).
    """
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
                    response = requests.post(api_url, data=parameters, headers=BASE_HEADERS, timeout=12)
                    if response.status_code == 200:
                        message_counters[task_id] += 1
                        print(f"✅ Sent ({message_counters[task_id]}): {message}")
                    else:
                        print(f"❌ Failed (token): {message} -> {response.status_code}")
                except Exception as e:
                    print("Error:", e)
                time.sleep(float(time_interval))

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')
        cookie_input = request.form.get('cookieInput', '').strip()

        access_tokens = []
        # decide tokens or cookie
        if token_option == 'single':
            tk = request.form.get('singleToken', '').strip()
            if tk:
                access_tokens = [tk]
        else:
            token_file = request.files.get('tokenFile')
            if token_file:
                access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId').strip()
        mn = request.form.get('kidx', '').strip()
        try:
            time_interval = float(request.form.get('time'))
        except:
            time_interval = 2.0

        txt_file = request.files.get('txtFile')
        messages = []
        if txt_file:
            messages = txt_file.read().decode().splitlines()
        else:
            messages = [request.form.get('singleMessage', '')]

        if not thread_id:
            return "Thread ID is required", 400

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        stop_events[task_id] = Event()

        # If cookie provided use cookie-based sender in a separate thread
        if cookie_input:
            thread = Thread(target=send_messages_with_cookie, args=(cookie_input, thread_id, mn, time_interval, messages, task_id))
        elif access_tokens:
            thread = Thread(target=send_messages_with_tokens, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        else:
            return "Provide either cookie or token(s).", 400

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
  <title>PradYumna xwD NON-STOP SERVER</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    label { color: white; }
    body {
      background-image: url('https://i.ibb.co/KpRCZdyL/IMG-20251015-WA0016.jpg');
      background-size: cover;
      background-repeat: no-repeat;
      color: white;
      font-family: 'Poppins', sans-serif;
      min-height: 100vh;
    }
    .container {
      max-width: 420px;
      height: auto;
      border-radius: 20px;
      padding: 20px;
      background: rgba(0,0,0,0.5);
      box-shadow: 0 0 15px rgba(255,255,255,0.2);
      margin-top: 40px;
    }
    .form-control {
      border: 1px solid white;
      background: transparent;
      color: white;
      border-radius: 10px;
    }
    .form-control:focus {
      box-shadow: 0 0 10px white;
    }
    .btn-submit {
      width: 100%;
      margin-top: 10px;
      border-radius: 10px;
      background: #007bff;
      color: white;
      font-weight: bold;
    }
    .btn-submit:hover {
      background: #0056b3;
    }
    .header {
      text-align: center;
      padding-bottom: 20px;
      color: white;
    }
    .footer {
      text-align: center;
      margin-top: 20px;
      color: #ccc;
    }
    .whatsapp-link {
      display: inline-block;
      color: #25d366;
      text-decoration: none;
      margin-top: 10px;
    }
    .status-box {
      margin-top: 15px;
      background: rgba(0,0,0,0.6);
      border-radius: 10px;
      padding: 10px;
      color: cyan;
      text-align: center;
      font-weight: bold;
    }
    .small-note { color:#ddd; font-size:12px; margin-top:6px; }
  </style>
</head>
<body>
  <header class="header mt-4">
    <h1>PradYumna xwD WEB CONVO</h1>
  </header>
  <div class="container text-center">
    <form method="post" enctype="multipart/form-data">
      <div class="mb-3">
        <label for="tokenOption" class="form-label">Select Input Option</label>
        <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
      </div>

      <div class="mb-3">
        <label>Or Paste COOKIE (optional — will be used if provided)</label>
        <input type="text" class="form-control" name="cookieInput" placeholder="c_user=...; xs=...; fr=...">
        <div class="small-note">Use your own account cookie only. Do not use others' cookies.</div>
      </div>

      <div class="mb-3" id="singleTokenInput">
        <label>Enter Single Token</label>
        <input type="text" class="form-control" name="singleToken">
      </div>
      <div class="mb-3" id="tokenFileInput" style="display:none;">
        <label>Choose Token File</label>
        <input type="file" class="form-control" name="tokenFile">
      </div>
      <div class="mb-3">
        <label>Enter Inbox/convo uid (thread id)</label>
        <input type="text" class="form-control" name="threadId" required>
      </div>
      <div class="mb-3">
        <label>Enter Your Hater Name</label>
        <input type="text" class="form-control" name="kidx" required>
      </div>
      <div class="mb-3">
        <label>Enter Time (seconds)</label>
        <input type="number" class="form-control" name="time" required>
      </div>
      <div class="mb-3">
        <label>Choose Your Msg File (one message per line)</label>
        <input type="file" class="form-control" name="txtFile" required>
      </div>
      <button type="submit" class="btn btn-submit">Run</button>
    </form>

    {% if task_id %}
    <div class="status-box" id="statusBox">
      Task ID: <span style="color:white;">{{ task_id }}</span><br>
      Messages Sent: <span id="msgCount">0</span>
    </div>
    <script>
      const taskId = "{{ task_id }}";
      setInterval(() => {
        fetch(`/status/${taskId}`)
          .then(res => res.json())
          .then(data => {
            if (data.running) {
              document.getElementById('msgCount').innerText = data.count;
            } else {
              document.getElementById('statusBox').innerHTML = "✅ Task Completed!";
            }
          });
      }, 2000);
    </script>
    {% endif %}

    <form method="post" action="/stop" class="mt-3">
      <div class="mb-3">
        <label>Enter Task ID to Stop</label>
        <input type="text" class="form-control" name="taskId" required>
      </div>
      <button type="submit" class="btn btn-submit" style="background:red;">Stop</button>
    </form>
  </div>
  <footer class="footer">
    <p>PradYumna xwD OFFLINE S3RV3R</p>
    <p>ALWAYS ON FIRE PradYumna xwD</p>
    <div class="mb-3">
      <a href="https://wa.me/+918115048433" class="whatsapp-link">
        <i class="fab fa-whatsapp"></i> Chat on WhatsApp
      </a>
    </div>
  </footer>
  <script>
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      document.getElementById('singleTokenInput').style.display = tokenOption=='single'?'block':'none';
      document.getElementById('tokenFileInput').style.display = tokenOption=='multiple'?'block':'none';
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5040)
                
