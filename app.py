# app.py - Clean but visually pleasant design with subtle dark gradients and distinct colors
# No heavy animation, just smooth layering of dark backgrounds + distinct input/button colors
# Color-coded inputs and legends for clarity, neat subtle backgrounds 

from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
UPLOAD_FOLDER = os.path.abspath('.')
ALLOWED_EXTENSIONS = {'json'}

bot_status = {
    "running": False,
    "logs": [],
    "active_users": 0,
    "thread": None,
}

def bot_simulator():
    while bot_status["running"]:
        time.sleep(3)
        log = f"[{time.strftime('%H:%M:%S')}] Bot is active | Users: {bot_status['active_users']}"
        bot_status['logs'].append(log)
        if len(bot_status['logs']) > 50:
            bot_status['logs'].pop(0)
        bot_status['active_users'] = (bot_status['active_users'] + 1) % 10

HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>YK TRICKS INDIA — Stylish Bot Panel</title>
  <style>
    /* Base resets and font */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    html, body {
      height: 100vh;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #121417, #242b38);
      color: #e0e0e0;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 30px 0;
      overflow-y: auto;
    }
    .container {
      background: #1e2233;
      border-radius: 16px;
      width: 100%;
      max-width: 1200px;
      box-shadow: 0 10px 30px rgba(10,14,25,0.7);
      padding: 40px 50px;
      display: flex;
      flex-direction: column;
      gap: 30px;
    }
    h1 {
      font-size: 3rem;
      font-weight: 700;
      text-align: center;
      color: #f0f0f0;
      margin-bottom: 5px;
      user-select:none;
    }
    p.lead {
      text-align: center;
      font-size: 1.15rem;
      color: #bbc6df;
      user-select:none;
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 30px;
    }
    label {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 8px;
      display: block;
    }
    textarea, input[type=text], input[type=color], input[type=file] {
      width: 100%;
      border-radius: 10px;
      padding: 18px 22px;
      font-size: 1.2rem;
      background: white;
      border: none;
      box-shadow: inset 0 0 10px rgba(0,0,0,0.2);
      font-weight: 600;
      color: #111;
      font-family: monospace, monospace;
      resize: vertical;
      transition: box-shadow 0.3s ease, background 0.3s ease;
      user-select: text;
    }
    textarea {
      min-height: 260px;
    }
    textarea:focus, input:focus {
      outline: none;
      background: #e9f0ff;
      box-shadow: 0 0 10px #3f83f8;
    }
    .row {
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }
    .row > * {
      flex: 1;
      min-width: 200px;
    }
    .buttons-row {
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
      justify-content: center;
      margin-top: 15px;
    }
    button, a.button-link {
      flex: 1 1 190px;
      font-weight: 700;
      font-size: 1.3rem;
      padding: 18px 35px;
      border-radius: 12px;
      cursor: pointer;
      border: none;
      color: #fff;
      transition: background-color 0.3s ease;
      user-select:none;
      text-align: center;
      box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    button:disabled {
      background-color: #888;
      cursor: not-allowed;
      box-shadow: none;
    }
    .save-btn {
      background-color: #0077ff;
      box-shadow: 0 0 18px #3399ff;
    }
    .save-btn:hover:not(:disabled) {
      background-color: #005fcc;
      box-shadow: 0 0 28px #0066ff;
    }
    .start-btn {
      background-color: #2ca02c;
      box-shadow: 0 0 18px #48d048;
    }
    .start-btn:hover:not(:disabled) {
      background-color: #238423;
      box-shadow: 0 0 28px #2ecc40;
    }
    .stop-btn {
      background-color: #d93a3a;
      box-shadow: 0 0 18px #e06060;
    }
    .stop-btn:hover:not(:disabled) {
      background-color: #b63131;
      box-shadow: 0 0 28px #ff5252;
    }
    a.button-link {
      background-color: #444;
      box-shadow: 0 0 18px #666;
      color: #eee;
      text-decoration: none;
      display: inline-block;
      vertical-align: middle;
    }
    a.button-link:hover {
      background-color: #666;
      box-shadow: 0 0 28px #777;
    }
    /* Status and logs */
    .status-section {
      background: #2b3049;
      border-radius: 14px;
      padding: 25px 30px;
      display: flex;
      flex-direction: column;
      gap: 15px;
      height: 320px;
      color: #d8dcff;
      font-weight: 600;
      box-shadow: inset 0 0 15px rgba(80,100,160,0.3);
    }
    #bot_status {
      font-size: 1.8rem;
    }
    #bot_status.running {
      color: #55cc55;
    }
    #bot_status.stopped {
      color: #cc5555;
    }
    #log_console {
      flex-grow: 1;
      background: #e8ebf8;
      color: #222;
      border-radius: 10px;
      padding: 10px 15px;
      font-family: monospace;
      font-size: 1rem;
      overflow-y: scroll;
      white-space: pre-wrap;
      user-select: text;
      box-shadow: inset 0 0 8px rgba(0,0,0,0.1);
    }
    /* Responsive */
    @media (max-width: 940px) {
      .container {
        padding: 30px 35px;
      }
      h1 {
        font-size: 2.4rem;
      }
      textarea, input[type=text], input[type=color], input[type=file] {
        font-size: 1rem;
        padding: 14px 18px;
      }
      button, a.button-link {
        font-size: 1.1rem;
        padding: 16px 25px;
      }
      #bot_status {
        font-size: 1.4rem;
      }
      .status-section {
        height: 270px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>YK TRICKS INDIA — Stylish Bot Panel</h1>
    <p class="lead">Paste or upload fbstate.json. Configure your bot. Use Start/Stop buttons and watch live logs & status.</p>

    <form method="post" action="/save" enctype="multipart/form-data" autocomplete="off">
      <label for="fbstate">Paste fbstate.json (text area)</label>
      <textarea name="fbstate" id="fbstate" placeholder="Paste your fbstate.json content here..."></textarea>

      <label for="file">Or upload fbstate.json file</label>
      <input type="file" id="file" name="file" accept="application/json" />

      <div class="row">
        <div>
          <label for="admin_id">Admin ID</label>
          <input type="text" name="admin_id" id="admin_id" placeholder="Enter Admin User ID" />
        </div>
        <div>
          <label for="prefix">Command Prefix</label>
          <input type="text" name="prefix" id="prefix" placeholder="/" value="/" />
        </div>
      </div>

      <label for="thread_id">Group Thread ID</label>
      <input type="text" name="thread_id" id="thread_id" placeholder="Group or Thread ID" />

      <div class="row">
        <div>
          <label for="color_picker">Neon Color Picker</label>
          <input type="color" id="color_picker" value="#00aaee" />
        </div>
        <div>
          <label for="neon_color">Neon Color HEX Code</label>
          <input type="text" name="neon_color" id="neon_color" value="#00aaee" placeholder="#00aaee" />
        </div>
      </div>

      <div class="buttons-row">
        <button type="submit" class="save-btn">Save Config</button>
        <button type="button" id="start_btn" class="start-btn">Start Bot</button>
        <button type="button" id="stop_btn" class="stop-btn" disabled>Stop Bot</button>
        <a href="/files" class="button-link" target="_blank">View Files</a>
      </div>
    </form>

    <div class="status-section">
      <div id="bot_status" class="stopped">Status: Stopped</div>
      <textarea id="log_console" readonly>Console logs will appear here… Waiting for bot start.</textarea>
    </div>
  </div>

  <script>
    const colorInput = document.getElementById('color_picker');
    const colorHexInput = document.getElementById('neon_color');
    colorInput.addEventListener('input', () => {
      colorHexInput.value = colorInput.value;
    });
    colorHexInput.addEventListener('input', () => {
      if(/^#[0-9a-fA-F]{6}$/.test(colorHexInput.value)) {
        colorInput.value = colorHexInput.value;
      }
    });

    const startBtn = document.getElementById('start_btn');
    const stopBtn = document.getElementById('stop_btn');
    const statusDiv = document.getElementById('bot_status');
    const logConsole = document.getElementById('log_console');

    function updateStatus(running) {
      if (running) {
        statusDiv.textContent = "Status: Running";
        statusDiv.classList.remove('stopped');
        statusDiv.classList.add('running');
        startBtn.disabled = true;
        stopBtn.disabled = false;
      } else {
        statusDiv.textContent = "Status: Stopped";
        statusDiv.classList.add('stopped');
        statusDiv.classList.remove('running');
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }
    }

    async function refreshStatus() {
      try {
        const res = await fetch('/bot_status');
        if(res.ok) {
          const data = await res.json();
          updateStatus(data.running);
          logConsole.value = data.logs.join("
");
          logConsole.scrollTop = logConsole.scrollHeight;
        }
      } catch {}
    }

    startBtn.onclick = async () => {
      await fetch('/bot_start', {method: 'POST'});
      refreshStatus();
    };

    stopBtn.onclick = async () => {
      await fetch('/bot_stop', {method: 'POST'});
      refreshStatus();
    };

    setInterval(refreshStatus, 3000);
    refreshStatus();
  </script>
</body>
</html>
'''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/save', methods=['POST'])
def save():
    fbstate_text = request.form.get('fbstate', '').strip()
    admin_id = request.form.get('admin_id', '').strip()
    prefix = request.form.get('prefix', '/').strip()
    thread_id = request.form.get('thread_id', '').strip()
    neon_color = request.form.get('neon_color', '#00aaee').strip()

    file = request.files.get('file')
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        dest = os.path.join(UPLOAD_FOLDER, 'fbstate.json')
        file.save(dest)
    elif fbstate_text:
        try:
            parsed = json.loads(fbstate_text)
            with open(os.path.join(UPLOAD_FOLDER, 'fbstate.json'), 'w', encoding='utf-8') as f:
                json.dump(parsed, f, indent=2)
        except Exception:
            with open(os.path.join(UPLOAD_FOLDER, 'fbstate.json'), 'w', encoding='utf-8') as f:
                f.write(fbstate_text)

    config = {
        'admin_id': admin_id,
        'prefix': prefix,
        'thread_id': thread_id,
        'neon_color': neon_color
    }
    with open(os.path.join(UPLOAD_FOLDER, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    return redirect(url_for('index'))

@app.route('/bot_start', methods=['POST'])
def bot_start():
    if not bot_status["running"]:
        bot_status["running"] = True
        bot_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] Bot started")
        thread = threading.Thread(target=bot_simulator, daemon=True)
        bot_status["thread"] = thread
        thread.start()
    return jsonify({"status": "started"})

@app.route('/bot_stop', methods=['POST'])
def bot_stop():
    if bot_status["running"]:
        bot_status["running"] = False
        bot_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] Bot stopped")
    return jsonify({"status": "stopped"})

@app.route('/bot_status')
def bot_status_route():
    return jsonify({
        "running": bot_status["running"],
        "logs": bot_status["logs"][-40:],
        "active_users": bot_status["active_users"],
    })

@app.route('/files')
def files_page():
    files = []
    for name in ('fbstate.json', 'config.json'):
        if os.path.exists(os.path.join(UPLOAD_FOLDER, name)):
            files.append(name)
    return jsonify({'files': files})

@app.route('/download/<path:filename>')
def download_file(filename):
    safe = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, safe)
    if os.path.exists(path):
        return send_from_directory(UPLOAD_FOLDER, safe, as_attachment=True)
    return ("File not found", 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
