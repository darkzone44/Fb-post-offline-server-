# app.py - Enhanced with START/STOP buttons + LIVE console logs + BOT STATUS display
# Same neon big style, removed fancy fonts, simple bold system font for easier reading

from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
UPLOAD_FOLDER = os.path.abspath('.')
ALLOWED_EXTENSIONS = {'json'}

# Global bot status simulation
bot_status = {
    "running": False,
    "logs": [],
    "active_users": 0,
    "thread": None,
}

def bot_simulator():
    """Background bot simulation generating logs and updating active user count."""
    while bot_status["running"]:
        time.sleep(3)
        # Simulate log entry
        log = f"[{time.strftime('%H:%M:%S')}] Bot running smoothly, active users: {bot_status['active_users'] + 1}"
        bot_status['logs'].append(log)
        # Keep logs under 50 entries
        if len(bot_status['logs']) > 50:
            bot_status['logs'].pop(0)
        # Simulate active users increment and decrement
        bot_status['active_users'] = (bot_status['active_users'] + 1) % 10


HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YK TRICKS INDIA — BOT CONTROL + LIVE STATUS</title>
  <style>
    :root {
      --neon-primary: #00ff88;
      --bg-dark: #0a0a15;
    }

    *{box-sizing:border-box;margin:0;padding:0}
    html,body{height:100vh; background: var(--bg-dark); color:#00ff88; font-family: system-ui, monospace, sans-serif; font-weight: bold; display:flex; justify-content:center; align-items:center; padding:30px;}
    body {overflow:hidden;}

    .wrap {
      width: 100vw; max-width: 1200px; height: 95vh;
      background: rgba(0,0,0,0.85);
      border-radius: 20px;
      padding: 40px;
      box-shadow: 0 0 40px var(--neon-primary);
      display: flex; flex-direction: column;
    }

    h1 {
      font-size: 3.5rem;
      margin-bottom: 10px;
      text-align: center;
      text-shadow:
        0 0 20px var(--neon-primary),
        0 0 40px var(--neon-primary),
        0 0 60px var(--neon-primary);
    }

    p.lead {
      font-size: 1.2rem;
      margin-bottom: 28px;
      text-align: center;
      color: #55ffaaaa;
    }

    form {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 25px;
      overflow-y: auto;
    }

    label {
      font-size: 1.3rem;
      margin-bottom: 6px;
      display: block;
    }

    textarea, input[type=text], input[type=color], input[type=file] {
      width: 100%;
      border-radius: 16px;
      padding: 20px;
      font-size: 1.3rem;
      color: #00ff88;
      background: #011100;
      border: 3px solid transparent;
      box-shadow:
        inset 0 0 20px #00ff88aa;
      font-weight: bold;
      font-family: monospace;
      resize: vertical;
      transition: all 0.3s ease;
    }

    textarea {
      min-height: 280px;
    }

    textarea:focus, input:focus {
      outline: none;
      border-color: var(--neon-primary);
      box-shadow:
        0 0 30px var(--neon-primary),
        inset 0 0 40px var(--neon-primary);
      background: #002200;
      color:#aaffaa;
      transform: scale(1.02);
    }

    .row {
      display: flex;
      gap: 15px;
      flex-wrap: wrap;
    }

    .row > * {
      flex: 1;
      min-width: 200px;
    }

    .big-btn {
      height: 75px;
      font-size: 1.7rem;
      font-weight: 900;
      cursor: pointer;
      border-radius: 25px;
      border: none;
      background: linear-gradient(45deg, #00ff88, #00cc66);
      color: #001100;
      text-shadow: 0 0 10px #00ff88;
      box-shadow:
        0 0 30px #00ff88;
      transition: transform 0.2s, box-shadow 0.3s;
      flex: 1;
      user-select:none;
    }
    .big-btn:hover:not(:disabled) {
      transform: scale(1.08);
      box-shadow:
        0 0 70px #00ff88,
        0 0 120px #00ff88;
    }
    .big-btn:disabled {
      cursor: not-allowed;
      opacity: 0.5;
    }

    .buttons-row {
      display: flex;
      gap: 30px;
      margin-top: 12px;
    }

    /* Live preview + status */
    .section {
      background: #012200aa;
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 0 30px #00ff80bb inset;
    }

    .neon-preview {
      font-size: 5rem;
      font-weight: 900;
      text-align: center;
      margin: 10px 0 25px;
      text-shadow:
        0 0 40px var(--neon-primary),
        0 0 80px var(--neon-primary),
        0 0 120px var(--neon-primary);
    }

    .status {
      font-size: 1.6rem;
      font-weight: 900;
      padding: 15px;
      background: #001400;
      border-radius: 15px;
      box-shadow:
        0 0 20px #00ff88;
      color: #aaffaa;
      user-select:none;
      text-align: center;
      margin-bottom: 30px;
    }

    /* Logs container */
    #log_console {
      font-family: monospace !important;
      font-size: 1.1rem;
      height: 230px;
      color: #00ff88;
      background: #001200;
      border-radius: 15px;
      padding: 15px;
      overflow-y: scroll;
      box-shadow: inset 0 0 20px #00ff88;
      white-space: pre-wrap;
      user-select: text;
    }

    /* Scrollbar stylings */
    #log_console::-webkit-scrollbar {
      width: 12px;
    }
    #log_console::-webkit-scrollbar-track {
      background: #001100;
      border-radius: 8px;
    }
    #log_console::-webkit-scrollbar-thumb {
      background: #00cc55;
      border-radius: 8px;
    }

    @media (max-width: 850px) {
      h1 { font-size: 2.7rem; }
      textarea, input[type=text], input[type=color] { height: 65px; font-size: 1.1rem; }
      .big-btn { height: 60px; font-size: 1.3rem; }
      .neon-preview { font-size: 3.5rem; }
      #log_console { height: 160px; font-size: 0.9rem; }
    }
  </style>
</head>
<body>
  <div class="wrap">

    <h1>YK TRICKS INDIA — BOT CONTROL PANEL</h1>
    <p class="lead">Paste fbstate.json or upload. Configure. Start/Stop bot. Watch live logs and status.</p>

    <form method="post" action="/save" enctype="multipart/form-data" id="config_form" autocomplete="off">

      <div class="section">
        <label for="fbstate">Paste fbstate.json content</label>
        <textarea id="fbstate" name="fbstate" placeholder="Paste fbstate.json here..."></textarea>

        <label style="margin-top:20px;">Or upload fbstate.json file</label>
        <input type="file" id="file" name="file" accept="application/json">

        <div class="row" style="margin-top:25px;">
          <div>
            <label>Admin ID</label>
            <input type="text" name="admin_id" placeholder="Enter Admin User ID" autocomplete="off">
          </div>
          <div>
            <label>Command Prefix</label>
            <input type="text" name="prefix" placeholder="/" value="/" autocomplete="off">
          </div>
        </div>

        <label style="margin-top:20px;">Group Thread ID</label>
        <input type="text" name="thread_id" placeholder="Group Thread ID" autocomplete="off">

        <div class="row" style="margin-top:20px;">
          <div>
            <label>Neon color picker</label>
            <input type="color" id="color_picker" value="#00ff88" autocomplete="off">
          </div>
          <div>
            <label>Neon color hex</label>
            <input type="text" id="neon_color" name="neon_color" value="#00ff88" placeholder="#00ff88" autocomplete="off">
          </div>
        </div>

        <div class="buttons-row" style="margin-top:35px;">
          <button type="submit" class="big-btn" id="save_btn">💾 Save Config</button>
          <button type="button" class="big-btn" id="start_btn" style="background:#22aa22; color:black;">▶️ Start Bot</button>
          <button type="button" class="big-btn" id="stop_btn" style="background:#bb2222; color:black;" disabled>⏹ Stop Bot</button>
          <a href="/files" target="_blank" class="big-btn" style="background:#004466;">📂 View Files</a>
        </div>
      </div>

      <div class="section" style="margin-top:30px;">
        <div class="neon-preview" id="neon_preview">/</div>
        <div class="status" id="bot_status">Status: <strong>Stopped</strong></div>
        <label>Console Logs:</label>
        <div id="log_console" tabindex="0" aria-label="Bot console logs"></div>
      </div>
    </form>
  </div>

  <script>
    // Neon color sync & preview
    function updateNeon(color) {
      document.documentElement.style.setProperty('--neon-primary', color);
      const preview = document.getElementById('neon_preview');
      preview.style.textShadow = `0 0 40px ${color}, 0 0 80px ${color}, 0 0 120px ${color}`;
      preview.style.boxShadow = `0 0 60px ${color}, inset 0 0 50px ${color}`;
    }
    const colorPicker = document.getElementById('color_picker');
    const neonColor = document.getElementById('neon_color');
    colorPicker.addEventListener('input', e => {
      neonColor.value = e.target.value;
      updateNeon(neonColor.value);
    });
    neonColor.addEventListener('input', e => {
      if(/^#[0-9a-f]{6}$/i.test(e.target.value)){
        colorPicker.value = e.target.value;
        updateNeon(e.target.value);
      }
    });

    // Prefix live preview
    const prefixInput = document.querySelector('input[name="prefix"]');
    prefixInput.addEventListener('input', () => {
      document.getElementById('neon_preview').textContent = prefixInput.value || '/';
    });

    updateNeon(colorPicker.value);

    // Bot buttons logic
    const startBtn = document.getElementById('start_btn');
    const stopBtn = document.getElementById('stop_btn');
    const statusElem = document.getElementById('bot_status');
    const logConsole = document.getElementById('log_console');

    function setStatus(running) {
      statusElem.innerHTML = 'Status: <strong>' + (running ? 'Running 🚀' : 'Stopped ⏹') + '</strong>';
      startBtn.disabled = running;
      stopBtn.disabled = !running;
    }

    async function fetchStatus() {
      const resp = await fetch('/bot_status');
      if(resp.ok){
        const data = await resp.json();
        setStatus(data.running);
        logConsole.textContent = data.logs.join('
');
        logConsole.scrollTop = logConsole.scrollHeight;
      }
    }

    // Start Bot
    startBtn.onclick = async () => {
      startBtn.disabled = true;
      await fetch('/bot_start', {method: 'POST'});
      setStatus(true);
    };

    // Stop Bot
    stopBtn.onclick = async () => {
      stopBtn.disabled = true;
      await fetch('/bot_stop', {method: 'POST'});
      setStatus(false);
    };

    // Periodic log & status refresh (every 2.5 sec)
    setInterval(fetchStatus, 2500);
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
        bot_status["active_users"] = 0
        bot_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] Bot started.")
        # Start background thread
        thread = threading.Thread(target=bot_simulator, daemon=True)
        bot_status["thread"] = thread
        thread.start()
    return jsonify({"status": "started"})

@app.route('/bot_stop', methods=['POST'])
def bot_stop():
    if bot_status["running"]:
        bot_status["running"] = False
        bot_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] Bot stopped.")
    return jsonify({"status": "stopped"})

@app.route('/bot_status')
def bot_current_status():
    return jsonify({
        "running": bot_status["running"],
        "logs": bot_status["logs"][-40:],  # last 40 logs
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
