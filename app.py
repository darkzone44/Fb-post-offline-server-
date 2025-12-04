# app.py - Minimal clean black design, no heavy animation, simple smooth UI
# Suitable for low-performance or distraction-free use, focus on clarity & usability

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
        log = f"[{time.strftime('%H:%M:%S')}] Bot is running, active users: {bot_status['active_users']}"
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
  <title>YK TRICKS INDIA - Clean Bot Panel</title>
  <style>
    /* Basic reset and smooth fonts */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    html, body {
      height: 100vh;
      background-color: #000000;
      color: #e0e0e0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      font-weight: 600;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;
      overflow: hidden;
    }
    body {
      overflow-y: auto;
    }
    .container {
      background-color: #121212;
      border-radius: 12px;
      width: 100%;
      max-width: 1100px;
      padding: 30px 40px;
      box-shadow: 0 0 10px #222;
    }
    h1 {
      font-size: 2.8rem;
      margin-bottom: 15px;
      color: #f5f5f5;
      text-align: center;
    }
    p.lead {
      text-align: center;
      font-size: 1.1rem;
      margin-bottom: 30px;
      color: #bbb;
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 25px;
    }
    label {
      font-size: 1.1rem;
      margin-bottom: 6px;
      color: #ccc;
      display: block;
    }
    textarea, input[type=text], input[type=color], input[type=file] {
      width: 100%;
      border-radius: 8px;
      padding: 18px 20px;
      font-size: 1.2rem;
      background-color: #222222;
      border: 1.5px solid #444444;
      color: #f0f0f0;
      resize: vertical;
      font-family: monospace, Consolas, monospace;
      transition: border-color 0.3s ease;
    }
    textarea {
      min-height: 220px;
    }
    textarea:focus, input:focus {
      outline: none;
      border-color: #007acc;
      background-color: #1a1a1a;
    }
    .row {
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }
    .row > * {
      flex: 1;
      min-width: 150px;
    }
    .buttons-row {
      display: flex;
      gap: 20px;
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    button, a.button-link {
      font-weight: 700;
      font-size: 1.3rem;
      padding: 18px 35px;
      border-radius: 10px;
      text-decoration: none;
      cursor: pointer;
      border: none;
      color: #fff;
      background-color: #007acc;
      transition: background-color 0.3s ease;
      user-select: none;
      flex: 1 1 180px;
      text-align: center;
    }
    button:disabled {
      background-color: #444;
      cursor: not-allowed;
    }
    button:hover:not(:disabled), a.button-link:hover {
      background-color: #005a9e;
    }
    a.button-link {
      background-color: #444444;
    }
    /* Status and log area */
    .status-section {
      background-color: #1f1f1f;
      border-radius: 12px;
      padding: 20px;
      margin-top: 35px;
      height: 320px;
      display: flex;
      flex-direction: column;
    }
    #bot_status {
      font-size: 1.7rem;
      font-weight: 700;
      color: #33cc33;
      margin-bottom: 17px;
      user-select:none;
    }
    #bot_status.stopped {
      color: #cc3333;
    }
    #log_console {
      flex-grow: 1;
      background-color: #121212;
      border-radius: 10px;
      padding: 15px;
      font-family: monospace;
      font-size: 1rem;
      color: #d0d0d0;
      overflow-y: auto;
      white-space: pre-wrap;
      user-select: text;
      border: 1px solid #333;
    }
    /* Responsive */
    @media (max-width: 920px) {
      .container {
        padding: 25px 30px;
      }
      h1 {
        font-size: 2.2rem;
      }
      textarea, input[type=text], input[type=color], input[type=file] {
        font-size: 1rem;
        padding: 14px 16px;
      }
      button, a.button-link {
        font-size: 1.1rem;
        padding: 14px 25px;
      }
      #bot_status {
        font-size: 1.3rem;
      }
      .status-section {
        height: 280px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>YK TRICKS INDIA — BOT CONTROL PANEL</h1>
    <p class="lead">Paste fbstate.json or upload it. Configure your bot and control start/stop. View live logs & status.</p>

    <form method="post" action="/save" enctype="multipart/form-data" autocomplete="off">
      <label for="fbstate">Paste fbstate.json content</label>
      <textarea id="fbstate" name="fbstate" placeholder="Paste your fbstate.json content here..."></textarea>

      <label for="file">Or upload fbstate.json file</label>
      <input type="file" id="file" name="file" accept="application/json">

      <div class="row">
        <div>
          <label for="admin_id">Admin ID</label>
          <input type="text" id="admin_id" name="admin_id" placeholder="Enter Admin User ID" autocomplete="off" />
        </div>
        <div>
          <label for="prefix">Command Prefix</label>
          <input type="text" id="prefix" name="prefix" placeholder="/" value="/" autocomplete="off" />
        </div>
      </div>

      <label for="thread_id">Group Thread ID</label>
      <input type="text" id="thread_id" name="thread_id" placeholder="Group / Thread ID" autocomplete="off" />

      <div class="row">
        <div>
          <label for="color_picker">Pick Neon Color</label>
          <input type="color" id="color_picker" value="#00ff88" />
        </div>
        <div>
          <label for="neon_color">Neon Color HEX</label>
          <input type="text" id="neon_color" name="neon_color" value="#00ff88" placeholder="#00ff88" autocomplete="off" />
        </div>
      </div>

      <div class="buttons-row">
        <button type="submit" id="save_btn">Save Config</button>
        <button type="button" id="start_btn" style="background-color:#228822;">Start Bot</button>
        <button type="button" id="stop_btn" disabled style="background-color:#882222;">Stop Bot</button>
        <a href="/files" target="_blank" class="button-link">View Files</a>
      </div>
    </form>

    <div class="status-section">
      <div id="bot_status" class="stopped">Status: Stopped</div>
      <textarea id="log_console" readonly>Console logs will appear here... Waiting for bot to start.</textarea>
    </div>
  </div>

  <script>
    const colorPicker = document.getElementById('color_picker');
    const neonColor = document.getElementById('neon_color');
    colorPicker.addEventListener('input', e => {
      neonColor.value = e.target.value;
    });
    neonColor.addEventListener('input', e => {
      if(/^#[0-9a-f]{6}$/i.test(e.target.value)) {
        colorPicker.value = e.target.value;
      }
    });

    const startBtn = document.getElementById('start_btn');
    const stopBtn = document.getElementById('stop_btn');
    const statusDiv = document.getElementById('bot_status');
    const logConsole = document.getElementById('log_console');

    function setStatus(running) {
      if(running) {
        statusDiv.textContent = 'Status: Running';
        statusDiv.classList.remove('stopped');
        startBtn.disabled = true;
        stopBtn.disabled = false;
      } else {
        statusDiv.textContent = 'Status: Stopped';
        statusDiv.classList.add('stopped');
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }
    }

    async function fetchStatus() {
      try {
        const resp = await fetch('/bot_status');
        if(resp.ok) {
          const data = await resp.json();
          setStatus(data.running);
          logConsole.value = data.logs.join('
');
          logConsole.scrollTop = logConsole.scrollHeight;
        }
      } catch(e){}
    }

    startBtn.onclick = async () => {
      await fetch('/bot_start', {method: 'POST'});
      fetchStatus();
    };
    stopBtn.onclick = async () => {
      await fetch('/bot_stop', {method: 'POST'});
      fetchStatus();
    };

    setInterval(fetchStatus, 3000);
    fetchStatus();
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
    neon_color = request.form.get('neon_color', '#00ff88').strip()

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
