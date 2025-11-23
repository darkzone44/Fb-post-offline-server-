from flask import Flask, request, render_template_string, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import time
import re
from threading import Thread, Event
import random
import string

app = Flask(__name__)
app.debug = True

### Selenium based token extraction

def extract_token_with_selenium(cookie_string):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://m.facebook.com")
        time.sleep(2)

        # Clear currently set cookies (if any)
        driver.delete_all_cookies()

        # Set provided cookies
        cookies = cookie_string.split(';')
        for c in cookies:
            if '=' in c:
                name, value = c.strip().split('=', 1)
                cookie_dict = {'name': name, 'value': value, 'domain': '.facebook.com'}
                try:
                    driver.add_cookie(cookie_dict)
                except Exception as e:
                    print("Cookie set error:", e)

        driver.refresh()
        time.sleep(5)

        # Try to extract access token from page source
        page_source = driver.page_source
        token_match = re.search(r'"accessToken":"(EAAw+)"', page_source)
        if token_match:
            return token_match.group(1), None

        # Try from window object JS execution (some pages)
        js_token = driver.execute_script("return window.__accessToken || null;")
        if js_token:
            return js_token, None

        return None, "Access token not found"
    finally:
        driver.quit()

### Cookie+fb_dtsg message sending logic

headers_template = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'Referer': 'https://m.facebook.com',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
}
stop_events = {}
threads = {}
message_counters = {}

def get_fb_dtsg(cookie):
    session = requests.Session()
    headers = headers_template.copy()
    headers['Cookie'] = cookie
    r = session.get('https://m.facebook.com', headers=headers)
    if r.status_code != 200:
        print("FB homepage request failed:", r.status_code)
        return None
    match = re.search(r'name="fb_dtsg" value="([^"]+)"', r.text)
    if match:
        return match.group(1)
    else:
        print("fb_dtsg token not found in page")
        return None

def send_messages(cookies_list, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    message_counters[task_id] = 0
    while not stop_event.is_set():
        for cookie in cookies_list:
            if stop_event.is_set():
                break
            fb_dtsg = get_fb_dtsg(cookie)
            if not fb_dtsg:
                print("Skipping this cookie, fb_dtsg not found")
                continue
            headers = headers_template.copy()
            headers['Cookie'] = cookie
            for message1 in messages:
                if stop_event.is_set():
                    break
                api_url = f'https://m.facebook.com/messages/send/?icm=1&refid=12'
                payload = {
                    'ids[0]': thread_id,
                    'message': f"{mn} {message1}",
                    'fb_dtsg': fb_dtsg,
                    'send': 'Send',
                }
                try:
                    response = requests.post(api_url, data=payload, headers=headers)
                    if response.status_code == 200 and ('success' in response.text or '"error"' not in response.text):
                        message_counters[task_id] += 1
                        print(f"✅ Sent ({message_counters[task_id]}): {payload['message']}")
                    else:
                        print(f"❌ Failed ({response.status_code}): {payload['message']}")
                        print("Response Text:", response.text[:200])
                except Exception as e:
                    print("Error sending message:", e)
                time.sleep(time_interval)
        time.sleep(time_interval)

### Flask routes

@app.route('/', methods=['GET', 'POST'])
def home():
    token = None
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        cookie = request.form.get('cookie')

        if action == 'extract_token':
            if cookie:
                token, error = extract_token_with_selenium(cookie.strip())
        elif action == 'send_messages':
            # Start message sender thread
            cookie_option = request.form.get('tokenOption')
            if cookie_option == 'single':
                cookies_list = [request.form.get('singleToken')]
            else:
                token_file = request.files.get('tokenFile')
                if token_file:
                    cookies_list = token_file.read().decode().strip().splitlines()
                else:
                    cookies_list = []

            thread_id = request.form.get('threadId')
            mn = request.form.get('kidx')
            time_interval = int(request.form.get('time'))
            txt_file = request.files.get('txtFile')
            messages = txt_file.read().decode().splitlines() if txt_file else []

            task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            stop_events[task_id] = Event()
            thread = Thread(target=send_messages, args=(cookies_list, thread_id, mn, time_interval, messages, task_id))
            threads[task_id] = thread
            thread.start()
            return render_template_string(PAGE_HTML, token=None, error=None, task_id=task_id)

    return render_template_string(PAGE_HTML, token=token, error=error, task_id=None)

@app.route('/status/<task_id>')
def status(task_id):
    count = message_counters.get(task_id, 0)
    running = task_id in threads and not stop_events[task_id].is_set()
    return jsonify({'count': count, 'running': running})

@app.route('/stop', methods=['POST'])
def stop():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'Task with ID {task_id} has been stopped.'
    else:
        return f'No task found with ID {task_id}.'

### HTML template

PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Facebook Token Extractor and Message Sender</title>
<style>
body { background: #222; color: #eee; font-family: Arial, sans-serif; padding: 20px; }
.container { max-width: 600px; margin: auto; background: #333; padding: 20px; border-radius: 10px; }
label { font-weight: bold; margin-top: 10px; display: block; }
textarea, input, select, button { width: 100%; margin-top: 5px; padding: 10px; border-radius: 5px; border:none; }
button { background: #3b5998; color: white; font-weight: bold; cursor: pointer; }
button:hover { background: #2d4373; }
.status-box { margin-top: 15px; background: #111; padding: 15px; border-radius: 5px; }
</style>
</head>
<body>
<div class="container">
<h2>Facebook Token Extractor & Message Sender</h2>

<h3>1. Extract Access Token (Chromium based)</h3>
<form method="post">
<label>Paste Full Facebook Cookie:</label>
<textarea name="cookie" rows="4" placeholder="c_user=...; xs=...;"></textarea>
<input type="hidden" name="action" value="extract_token" />
<button type="submit">Extract Token</button>
</form>

{% if token %}
<div class="status-box">
<strong>Extracted Access Token:</strong><br/>
<code>{{ token }}</code>
</div>
{% endif %}
{% if error %}
<div class="status-box" style="color:#ff6666;">
<strong>Error:</strong><br/>
{{ error }}
</div>
{% endif %}

<hr />

<h3>2. Send Messages Using Cookies</h3>
<form method="post" enctype="multipart/form-data">
<label>Cookie Input Option:</label>
<select name="tokenOption" id="tokenOption" onchange="toggleCookieInput()">
  <option value="single">Single Cookie String</option>
  <option value="multiple">Cookie File Upload</option>
</select>

<div id="singleCookieDiv" style="margin-top:10px;">
<label>Paste Full Cookie:</label>
<textarea name="singleToken" rows="3" placeholder="c_user=...; xs=...;"></textarea>
</div>
<div id="multipleCookieDiv" style="display:none; margin-top:10px;">
<label>Upload Cookie File (txt):</label>
<input type="file" name="tokenFile" />
</div>

<label>Thread ID:</label>
<input type="text" name="threadId" required />

<label>Your Name Prefix (for messages):</label>
<input type="text" name="kidx" required />

<label>Message Interval (seconds):</label>
<input type="number" name="time" required />

<label>Upload Message Text File (one message per line):</label>
<input type="file" name="txtFile" required />

<input type="hidden" name="action" value="send_messages" />
<button type="submit">Start Sending</button>
</form>

{% if task_id %}
<div class="status-box" id="statusBox">
  <strong>Task ID:</strong> <span id="taskId">{{ task_id }}</span><br/>
  <strong>Messages Sent:</strong> <span id="msgCount">0</span>
</div>
<script>
let taskId = "{{ task_id }}";
let interval = setInterval(() => {
  fetch(`/status/${taskId}`)
    .then(res => res.json())
    .then(data => {
      if (data.running) {
        document.getElementById('msgCount').innerText = data.count;
      } else {
        document.getElementById('statusBox').innerHTML = '<strong>✅ Task Completed!</strong>';
        clearInterval(interval);
      }
    });
}, 2000);
</script>
{% endif %}

<hr />

<h3>3. Stop Sending Task</h3>
<form method="post" action="/stop">
<label>Enter Task ID to Stop:</label>
<input type="text" name="taskId" required />
<button type="submit" style="background:#b22222;">Stop Task</button>
</form>

</div>

<script>
function toggleCookieInput() {
  var val = document.getElementById('tokenOption').value;
  document.getElementById('singleCookieDiv').style.display = val === 'single' ? 'block' : 'none';
  document.getElementById('multipleCookieDiv').style.display = val === 'multiple' ? 'block' : 'none';
}
window.onload = toggleCookieInput;
</script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5040)
