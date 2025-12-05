# app.py - FULL WORKING FB MESSENGER BOT PANEL 
# Real bot start/stop with fbstate.json + config.json integration
# Deploy on Render - saves files + runs your actual FB bot!

from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import threading
import time
import subprocess
import sys
import signal

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
UPLOAD_FOLDER = os.path.abspath('.')
ALLOWED_EXTENSIONS = {'json'}

# Bot process management
bot_process = None
bot_logs = []
bot_status_data = {"running": False, "pid": None, "logs": []}

def tail_bot_logs():
    """Read bot logs in real-time"""
    global bot_logs
    try:
        if bot_process and bot_process.poll() is None:
            # Read last 100 lines from bot output
            log_file = 'bot.log'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    bot_logs = lines[-50:]  # last 50 lines
    except:
        pass

def start_real_bot():
    """Start your actual FB Messenger bot"""
    global bot_process, bot_status_data
    
    if bot_process and bot_process.poll() is None:
        return False
    
    # Check required files exist
    if not os.path.exists('fbstate.json') or not os.path.exists('config.json'):
        bot_status_data["logs"].append("[ERROR] fbstate.json or config.json missing!")
        return False
    
    try:
        # Clear previous logs
        open('bot.log', 'w').close()
        
        # Start your bot (replace with your actual bot command)
        # Option 1: If you have bot.py file
        bot_process = subprocess.Popen(
            [sys.executable, 'bot.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        bot_status_data["running"] = True
        bot_status_data["pid"] = bot_process.pid
        bot_status_data["logs"].append(f"[{time.strftime('%H:%M:%S')}] 🚀 Bot started (PID: {bot_process.pid})")
        
        # Log reader thread
        def log_reader():
            global bot_logs
            for line in iter(bot_process.stdout.readline, ''):
                bot_logs.append(line.strip())
                if len(bot_logs) > 100:
                    bot_logs.pop(0)
        
        threading.Thread(target=log_reader, daemon=True).start()
        
        return True
        
    except Exception as e:
        bot_status_data["logs"].append(f"[ERROR] Failed to start bot: {str(e)}")
        return False

def stop_real_bot():
    """Stop the running bot"""
    global bot_process, bot_status_data
    
    if bot_process and bot_process.poll() is None:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
            bot_status_data["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⏹ Bot stopped (PID: {bot_status_data['pid']})")
        except:
            bot_process.kill()
            bot_status_data["logs"].append(f"[{time.strftime('%H:%M:%S')}] 💥 Bot force killed")
        
        bot_status_data["running"] = False
        bot_status_data["pid"] = None
        bot_process = None

HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>YK TRICKS INDIA — REAL FB BOT PANEL</title>
  <style>
    * {box-sizing:border-box;margin:0;padding:0;}
    html, body {
      height:100vh; background:linear-gradient(135deg, #121417, #242b38);
      color:#e0e0e0; font-family:'Segoe UI',Tahoma,sans-serif;
      display:flex;justify-content:center;align-items:flex-start;padding:30px;
      overflow-y:auto;
    }
    .container {
      background:#1e2233; border-radius:16px; width:100%; max-width:1200px;
      box-shadow:0 10px 30px rgba(10,14,25,0.7); padding:40px 50px;
      display:flex;flex-direction:column;gap:30px;
    }
    h1 {font-size:3rem;font-weight:700;text-align:center;color:#f0f0f0;margin-bottom:5px;}
    p.lead {text-align:center;font-size:1.15rem;color:#bbc6df;}
    form {display:flex;flex-direction:column;gap:30px;}
    label {font-size:1.1rem;font-weight:600;margin-bottom:8px;display:block;}
    textarea, input[type=text], input[type=color], input[type=file] {
      width:100%;border-radius:10px;padding:18px 22px;font-size:1.2rem;
      background:white;border:none;box-shadow:inset 0 0 10px rgba(0,0,0,0.2);
      font-weight:600;color:#111;font-family:monospace;resize:vertical;
      transition:box-shadow 0.3s ease;
    }
    textarea {min-height:260px;}
    textarea:focus, input:focus {outline:none;background:#e9f0ff;box-shadow:0 0 15px #3f83f8;}
    .row {display:flex;gap:20px;flex-wrap:wrap;}
    .row>* {flex:1;min-width:200px;}
    .buttons-row {display:flex;gap:20px;flex-wrap:wrap;justify-content:center;margin-top:15px;}
    button, a.button-link {
      flex:1 1 190px;font-weight:700;font-size:1.3rem;padding:18px 35px;
      border-radius:12px;cursor:pointer;border:none;color:#fff;
      transition:all 0.3s ease;text-align:center;box-shadow:0 5px 15px rgba(0,0,0,0.2);
    }
    button:disabled {background:#888;cursor:not-allowed;box-shadow:none;}
    .save-btn {background:#0077ff;box-shadow:0 0 18px #3399ff;}
    .save-btn:hover:not(:disabled) {background:#005fcc;box-shadow:0 0 28px #0066ff;}
    .start-btn {background:#2ca02c;box-shadow:0 0 18px #48d048;}
    .start-btn:hover:not(:disabled) {background:#238423;box-shadow:0 0 28px #2ecc40;}
    .stop-btn {background:#d93a3a;box-shadow:0 0 18px #e06060;}
    .stop-btn:hover:not(:disabled) {background:#b63131;box-shadow:0 0 28px #ff5252;}
    a.button-link {background:#444;box-shadow:0 0 18px #666;color:#eee;text-decoration:none;}
    a.button-link:hover {background:#666;box-shadow:0 0 28px #777;}
    .status-section {
      background:#2b3049;border-radius:14px;padding:25px 30px;display:flex;
      flex-direction:column;gap:15px;height:350px;color:#d8dcff;font-weight:600;
      box-shadow:inset 0 0 15px rgba(80,100,160,0.3);
    }
    #bot_status {font-size:1.8rem;}
    #bot_status.running {color:#55cc55;}
    #bot_status.stopped {color:#cc5555;}
    #log_console {
      flex-grow:1;background:#e8ebf8;color:#222;border-radius:10px;
      padding:10px 15px;font-family:monospace;font-size:1rem;overflow-y:scroll;
      white-space:pre-wrap;box-shadow:inset 0 0 8px rgba(0,0,0,0.1);
    }
    .file-status {background:#2a3a4a;border-radius:10px;padding:15px;color:#aaccff;}
    @media (max-width:940px) {
      .container {padding:30px 35px;}
      h1 {font-size:2.4rem;}
      textarea, input {font-size:1rem;padding:14px 18px;}
      button, a.button-link {font-size:1.1rem;padding:16px 25px;}
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 YK TRICKS INDIA — REAL FB BOT</h1>
    <p class="lead">Upload fbstate.json → Save Config → Start Real Bot → Watch Live Logs</p>

    <form method="post" action="/save" enctype="multipart/form-data">
      <label>Paste fbstate.json content</label>
      <textarea name="fbstate" placeholder="Paste complete fbstate.json here..."></textarea>

      <label>Upload fbstate.json file</label>
      <input type="file" name="file" accept=".json">

      <div class="row">
        <div><label>Admin ID</label><input type="text" name="admin_id" placeholder="1234567890"></div>
        <div><label>Command Prefix</label><input type="text" name="prefix" value="/" placeholder="!"></div>
      </div>

      <label>Group Thread ID</label>
      <input type="text" name="thread_id" placeholder="123456789012345">

      <div class="row">
        <div><label>Bot Color</label><input type="color" id="color_picker" value="#00aaee"></div>
        <div><label>Color HEX</label><input type="text" name="neon_color" id="neon_color" value="#00aaee"></div>
      </div>

      <div class="buttons-row">
        <button type="submit" class="save-btn">💾 SAVE CONFIG</button>
        <button type="button" id="start_btn" class="start-btn">▶️ START BOT</button>
        <button type="button" id="stop_btn" class="stop-btn" disabled>⏹ STOP BOT</button>
        <a href="/files" class="button-link" target="_blank">📁 FILES</a>
      </div>
    </form>

    <div class="status-section">
      <div id="bot_status" class="stopped">Status: Stopped</div>
      <div id="file_status" class="file-status">
        fbstate.json: <span id="fbstate_check">❌ Missing</span> | 
        config.json: <span id="config_check">❌ Missing</span>
      </div>
      <textarea id="log_console" readonly>Bot logs appear here...
Save config first, then Start Bot</textarea>
    </div>
  </div>

  <script>
    const colorPicker = document.getElementById('color_picker');
    const colorHex = document.getElementById('neon_color');
    colorPicker.oninput = () => colorHex.value = colorPicker.value;
    colorHex.oninput = () => {
      if(/^#[0-9a-fA-F]{6}$/i.test(colorHex.value)) colorPicker.value = colorHex.value;
    };

    const startBtn = document.getElementById('start_btn');
    const stopBtn = document.getElementById('stop_btn');
    const statusDiv = document.getElementById('bot_status');
    const logConsole = document.getElementById('log_console');
    const fbstateCheck = document.getElementById('fbstate_check');
    const configCheck = document.getElementById('config_check');

    function updateStatus(running, pid) {
      if(running) {
        statusDiv.textContent = `Status: Running (PID: ${pid})`;
        statusDiv.className = 'running';
        startBtn.disabled = true;
        stopBtn.disabled = false;
      } else {
        statusDiv.textContent = 'Status: Stopped';
        statusDiv.className = 'stopped';
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }
    }

    async function refreshStatus() {
      try {
        const res = await fetch('/status');
        const data = await res.json();
        updateStatus(data.running, data.pid);
        logConsole.value = data.logs.join('
');
        logConsole.scrollTop = logConsole.scrollHeight;
        
        fbstateCheck.textContent = data.files.fbstate ? '✅ OK' : '❌ Missing';
        fbstateCheck.style.color = data.files.fbstate ? '#55cc55' : '#cc5555';
        configCheck.textContent = data.files.config ? '✅ OK' : '❌ Missing';
        configCheck.style.color = data.files.config ? '#55cc55' : '#cc5555';
      } catch {}
    }

    startBtn.onclick = async () => {
      await fetch('/bot_start', {method:'POST'});
      refreshStatus();
    };
    stopBtn.onclick = async () => {
      await fetch('/bot_stop', {method:'POST'});
      refreshStatus();
    };

    setInterval(refreshStatus, 2000);
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

    # Save fbstate.json
    file = request.files.get('file')
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        dest = os.path.join(UPLOAD_FOLDER, 'fbstate.json')
        file.save(dest)
    elif fbstate_text:
        try:
            parsed = json.loads(fbstate_text)
            with open('fbstate.json', 'w', encoding='utf-8') as f:
                json.dump(parsed, f, indent=2)
        except:
            with open('fbstate.json', 'w', encoding='utf-8') as f:
                f.write(fbstate_text)

    # Save config.json
    config = {'admin_id': admin_id, 'prefix': prefix, 'thread_id': thread_id, 'neon_color': neon_color}
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    global bot_status_data
    tail_bot_logs()
    bot_status_data["logs"] = bot_logs[-50:] + bot_status_data["logs"][-10:]
    
    files = {
        'fbstate': os.path.exists('fbstate.json'),
        'config': os.path.exists('config.json')
    }
    
    return jsonify({
        'running': bot_status_data["running"],
        'pid': bot_status_data["pid"],
        'logs': bot_status_data["logs"],
        'files': files
    })

@app.route('/bot_start', methods=['POST'])
def bot_start():
    if start_real_bot():
        return jsonify({"status": "started"})
    return jsonify({"status": "error"}), 400

@app.route('/bot_stop', methods=['POST'])
def bot_stop():
    stop_real_bot()
    return jsonify({"status": "stopped"})

@app.route('/files')
def files_page():
    files = [name for name in ('fbstate.json', 'config.json', 'bot.log') 
             if os.path.exists(os.path.join(UPLOAD_FOLDER, name))]
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
