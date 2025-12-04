# app.py - SAME BIG NEON GAMING DESIGN + START/STOP + LIVE LOGS 🔥💎
# Previous bada choda design wapas + new bot controls

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

# Bot status simulation
bot_status = {
    "running": False,
    "logs": [],
    "active_users": 0,
    "thread": None,
}

def bot_simulator():
    while bot_status["running"]:
        time.sleep(3)
        log = f"[{time.strftime('%H:%M:%S')}] Bot active | Users: {bot_status['active_users']}"
        bot_status['logs'].append(log)
        if len(bot_status['logs']) > 50:
            bot_status['logs'].pop(0)
        bot_status['active_users'] = (bot_status['active_users'] + 1) % 12

HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>🚀 YK TRICKS INDIA — ULTIMATE BOT PANEL 🔥</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --neon-primary: #00ff88;
      --neon-secondary: #ff00ff;
      --neon-blue: #00ddff;
      --neon-purple: #ff44ff;
      --neon-glow: 0 0 40px var(--neon-primary), 0 0 80px var(--neon-primary), 0 0 120px var(--neon-primary);
      --bg-glow: 0 0 60px rgba(0,255,136,0.3);
    }

    *{box-sizing:border-box;margin:0;padding:0}
    html,body{height:100vh;overflow:hidden}
    body{
      font-family:'Orbitron', monospace;
      background: radial-gradient(ellipse at center, #0a0a1a 0%, #000000 70%);
      color:#00ff88;
      position:relative;
      overflow:hidden;
      animation: bgPulse 8s ease-in-out infinite alternate;
    }

    /* EPIC BACKGROUND ANIMATIONS */
    body::before {
      content:'';
      position:fixed;
      top:0;left:0;right:0;bottom:0;
      background: 
        radial-gradient(circle at 20% 80%, rgba(120,119,198,0.3) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255,119,198,0.3) 0%, transparent 50%),
        radial-gradient(circle at 40% 40%, rgba(120,219,255,0.2) 0%, transparent 50%);
      animation: rotate 20s linear infinite;
      z-index:0;
    }

    body::after {
      content:'';
      position:fixed;
      inset:0;
      background-image:
        linear-gradient(90deg, transparent 49%, rgba(255,255,255,0.013) 50%, transparent 51%),
        linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
        linear-gradient(90deg, transparent 49%, rgba(0,255,136,0.03) 50%, transparent 51%);
      background-size: 60px 60px, 60px 60px, 30px 30px;
      animation: gridMove 60s linear infinite;
      z-index:0;
    }

    @keyframes bgPulse {0%,100%{filter: brightness(1) contrast(1);} 50%{filter: brightness(1.1) contrast(1.2);}}
    @keyframes rotate {to{transform:rotate(360deg);}}
    @keyframes gridMove {0%{transform:translateX(0) translateY(0);} 100%{transform:translateX(-60px) translateY(-60px);}}
    @keyframes neonPulse {0%,100%{text-shadow:var(--neon-glow);} 50%{text-shadow:0 0 60px var(--neon-primary),0 0 120px var(--neon-primary),0 0 180px var(--neon-primary), inset 0 0 40px var(--neon-primary);}}
    @keyframes float {0%,100%{transform:translateY(0px);} 50%{transform:translateY(-15px);}}
    @keyframes glowPulse {0%,100%{box-shadow:var(--neon-glow);} 50%{box-shadow:0 0 60px var(--neon-primary),0 0 120px var(--neon-primary),0 0 200px var(--neon-primary);}}
    @keyframes scanline {0%{opacity:0.1;} 50%{opacity:0.4;} 100%{opacity:0.1;}}

    /* MAIN CONTAINER - BADA CHODA */
    .wrap{
      width:100vw;height:100vh;
      display:flex;align-items:center;justify-content:center;
      padding:40px;
      position:relative;z-index:10;
      backdrop-filter: blur(20px);
    }

    .panel{
      width:100%;max-width:1600px;height:95vh;
      background: rgba(10,10,25,0.9);
      border:2px solid transparent;
      border-radius:30px;
      padding:50px;
      box-shadow: 
        var(--bg-glow),
        inset 0 0 100px rgba(0,255,136,0.05),
        0 0 200px rgba(0,255,136,0.1);
      border-image: linear-gradient(45deg, var(--neon-primary), var(--neon-secondary), var(--neon-blue)) 1;
      animation: float 6s ease-in-out infinite, glowPulse 3s ease-in-out infinite alternate;
      overflow-y:auto;
      display:grid;
      grid-template-rows: auto 1fr auto;
      gap:30px;
    }

    /* HEADERS - PREMIUM GAMING STYLE */
    h1{
      font-family:'Exo 2', sans-serif;
      font-size:4.5rem;font-weight:900;
      text-align:center;
      background:linear-gradient(45deg, #00ff88, #44ffaa, #00ddff, #ff44ff);
      background-size:400% 400%;
      -webkit-background-clip:text;
      -webkit-text-fill-color:transparent;
      background-clip:text;
      margin-bottom:10px;
      animation: neonPulse 2s ease-in-out infinite alternate, gradientShift 4s ease infinite;
      text-shadow: var(--neon-glow);
      letter-spacing:3px;
    }

    @keyframes gradientShift {
      0%{background-position:0% 50%;}
      50%{background-position:100% 50%;}
      100%{background-position:0% 50%;}
    }

    h2{font-size:2.2rem;font-weight:800;margin:30px 0 20px;color:#00ff88;text-shadow:0 0 30px currentColor;animation:neonPulse 3s infinite;}

    p.lead{
      font-size:1.3rem;
      text-align:center;
      color:#aaffcc;
      margin-bottom:40px;
      font-weight:500;
      text-shadow:0 0 20px rgba(0,255,136,0.5);
    }

    /* MASSIVE INPUT BOXES */
    .input-section{
      background:rgba(255,255,255,0.03);
      border:2px solid rgba(0,255,136,0.3);
      border-radius:25px;
      padding:35px;
      margin-bottom:30px;
      position:relative;
      overflow:hidden;
      animation: glowPulse 4s ease-in-out infinite alternate;
    }

    .input-section::before{
      content:'';
      position:absolute;
      top:-2px;left:-2px;right:-2px;bottom:-2px;
      background:linear-gradient(45deg, var(--neon-primary), var(--neon-blue), var(--neon-secondary), var(--neon-primary));
      border-radius:23px;
      z-index:-1;
      animation: borderRotate 3s linear infinite;
    }

    @keyframes borderRotate{100%{transform:rotate(360deg);}}

    label{
      display:block;
      font-size:1.4rem;
      font-weight:800;
      color:#00ff88;
      margin-bottom:15px;
      text-shadow:0 0 15px currentColor;
    }

    input[type="text"], input[type="color"], textarea, select{
      width:100%;
      height:80px;
      padding:0 25px;
      font-size:1.6rem;
      font-family:'Orbitron', monospace;
      font-weight:700;
      background:linear-gradient(145deg, rgba(0,0,0,0.8), rgba(10,10,25,0.9));
      border:3px solid transparent;
      border-radius:20px;
      color:#00ff88;
      box-shadow: 
        inset 0 0 30px rgba(0,255,136,0.1),
        var(--neon-glow);
      transition:all 0.3s ease;
      text-shadow:0 0 10px currentColor;
    }

    textarea{height:300px !important;resize:vertical;font-size:1.4rem;line-height:1.6;}

    input:focus, textarea:focus, select:focus{
      outline:none;
      border-image:linear-gradient(45deg, var(--neon-primary), var(--neon-blue)) 1;
      box-shadow: 
        inset 0 0 40px var(--neon-primary),
        0 0 60px var(--neon-primary),
        0 0 100px rgba(0,255,136,0.5);
      transform:scale(1.02);
    }

    /* EPIC BUTTONS */
    .mega-btn{
      display:inline-block;
      padding:25px 50px;
      font-size:1.8rem;
      font-weight:900;
      font-family:'Exo 2', sans-serif;
      border:none;
      border-radius:25px;
      cursor:pointer;
      position:relative;
      overflow:hidden;
      text-transform:uppercase;
      letter-spacing:2px;
      margin:10px;
      min-width:220px;
      height:80px;
      transition:all 0.3s ease;
    }

    .save-btn{
      background:linear-gradient(45deg, var(--neon-primary), var(--neon-blue));
      color:#000;
      box-shadow:var(--neon-glow);
      animation:neonPulse 1.5s infinite;
    }

    .start-btn{
      background:linear-gradient(45deg, #00ff44, #44ff88);
      color:#000;
      box-shadow:0 0 50px #00ff44;
      animation:neonPulse 1s infinite;
    }

    .stop-btn{
      background:linear-gradient(45deg, #ff4444, #ff8888);
      color:#000;
      box-shadow:0 0 50px #ff4444;
      animation:neonPulse 1s infinite;
    }

    .files-btn{
      background:rgba(255,255,255,0.1);
      color:#aaffcc;
      border:2px solid rgba(0,255,136,0.5);
    }

    .mega-btn:hover{
      transform:translateY(-5px) scale(1.05);
      box-shadow:0 0 80px var(--neon-primary), 0 0 150px var(--neon-primary);
    }
    .mega-btn:disabled{opacity:0.4; cursor:not-allowed; transform:none;}

    /* STATUS & LOGS SECTION */
    .status-section{
      background:rgba(0,0,0,0.7);
      border:3px solid transparent;
      border-radius:25px;
      padding:40px;
      text-align:center;
      margin:30px 0;
      position:relative;
      grid-row: 2 / 3;
    }

    .neon-display{
      font-size:6rem;
      font-weight:900;
      padding:30px 60px;
      border-radius:20px;
      display:inline-block;
      margin:20px 0;
      font-family:'Exo 2', sans-serif;
      text-shadow:var(--neon-glow);
      animation:neonPulse 2s infinite;
      background:rgba(255,255,255,0.05);
      border:2px solid rgba(0,255,136,0.3);
    }

    .bot-status{
      font-size:2rem;
      font-weight:900;
      padding:25px;
      background:rgba(0,255,0,0.2);
      border-radius:20px;
      margin:20px 0;
      box-shadow:0 0 40px rgba(0,255,0,0.6);
      animation:glowPulse 2s infinite;
    }

    .bot-stopped{
      background:rgba(255,50,50,0.2) !important;
      box-shadow:0 0 40px rgba(255,50,50,0.6) !important;
    }

    #log_console {
      font-family: 'Orbitron', monospace !important;
      font-size:1.2rem;
      height:250px;
      color:#00ff88;
      background:rgba(0,0,0,0.8);
      border:2px solid rgba(0,255,136,0.4);
      border-radius:20px;
      padding:25px;
      overflow-y:scroll;
      box-shadow:inset 0 0 30px rgba(0,255,136,0.2);
      white-space:pre-wrap;
      text-shadow:0 0 5px currentColor;
      margin-top:20px;
    }

    #log_console::-webkit-scrollbar {
      width:15px;
    }
    #log_console::-webkit-scrollbar-track {
      background:rgba(0,255,136,0.1);
      border-radius:10px;
    }
    #log_console::-webkit-scrollbar-thumb {
      background:linear-gradient(var(--neon-primary), var(--neon-blue));
      border-radius:10px;
    }

    /* RESPONSIVE */
    @media (max-width:1400px){
      .panel{max-width:1200px;}
      h1{font-size:3.8rem;}
    }
    @media (max-width:768px){
      .panel{padding:25px;height:98vh;}
      h1{font-size:2.8rem;}
      input,textarea{height:65px;font-size:1.3rem;}
      .mega-btn{padding:20px 30px;font-size:1.4rem;min-width:180px;}
      .neon-display{font-size:4rem;}
    }

    .scanline{position:fixed;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent, #00ff88,transparent);animation:scanline 3s linear infinite;z-index:100;}
  </style>
</head>
<body>
  <div class="scanline"></div>
  
  <div class="wrap">
    <div class="panel">
      
      <!-- HEADER -->
      <div style="grid-row:1">
        <h1>🚀 YK TRICKS 🔥</h1>
        <p class="lead">BADA CHODA BOT PANEL — Live Control + Console Logs 💎⚡</p>
      </div>

      <!-- CONFIG FORM -->
      <form method="post" action="/save" enctype="multipart/form-data" style="grid-row:1">
        
        <div class="input-section">
          <h2>📁 FBSTATE.json</h2>
          <label>PASTE fbstate.json (Ctrl+V)</label>
          <textarea name="fbstate" placeholder="Paste complete fbstate.json here..."></textarea>
          <label style="margin-top:20px;">OR UPLOAD FILE</label>
          <input type="file" name="file" accept=".json" style="height:80px;">
        </div>

        <div class="input-section">
          <h2>⚙️ BOT CONFIG</h2>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:25px;">
            <div>
              <label>👑 ADMIN ID</label>
              <input type="text" name="admin_id" placeholder="Admin User ID">
            </div>
            <div>
              <label>✨ PREFIX</label>
              <input type="text" name="prefix" placeholder="/" value="/">
            </div>
          </div>
          <div style="margin-top:25px;">
            <label>🆔 THREAD ID</label>
            <input type="text" name="thread_id" placeholder="Group Thread ID">
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:25px;margin-top:25px;">
            <div>
              <label>🌈 NEON COLOR</label>
              <input type="color" id="color_picker" value="#00ff88">
            </div>
            <div>
              <label>HEX</label>
              <input type="text" id="neon_color" name="neon_color" value="#00ff88">
            </div>
          </div>
        </div>

        <div style="text-align:center;margin:40px 0;">
          <button class="mega-btn save-btn" type="submit">💾 SAVE</button>
          <button type="button" class="mega-btn start-btn" id="start_btn">▶️ START BOT</button>
          <button type="button" class="mega-btn stop-btn" id="stop_btn" disabled>⏹ STOP BOT</button>
          <a href="/files" class="mega-btn files-btn">📂 FILES</a>
        </div>

      </form>

      <!-- LIVE STATUS & LOGS -->
      <div class="status-section">
        <h3 style="font-size:2rem;margin-bottom:20px;">⚡ LIVE STATUS</h3>
        <div class="neon-display" id="neon_preview">/</div>
        <div class="bot-status" id="bot_status">BOT STOPPED ⏹</div>
        <div id="log_console">Console logs will appear here...
Waiting for bot start...</div>
      </div>

    </div>
  </div>

  <script>
    // LIVE NEON
    function updateNeon(color) {
      document.documentElement.style.setProperty('--neon-primary', color);
      const preview = document.getElementById('neon_preview');
      preview.style.textShadow = `0 0 40px ${color}, 0 0 80px ${color}, 0 0 120px ${color}`;
      preview.style.boxShadow = `0 0 60px ${color}, inset 0 0 50px ${color}`;
    }

    document.getElementById('color_picker').addEventListener('input', e => {
      document.getElementById('neon_color').value = e.target.value;
      updateNeon(e.target.value);
    });

    document.querySelector('input[name="prefix"]').addEventListener('input', e => {
      document.getElementById('neon_preview').textContent = e.target.value || '/';
    });

    // BOT CONTROLS
    const startBtn = document.getElementById('start_btn');
    const stopBtn = document.getElementById('stop_btn');
    const statusDiv = document.getElementById('bot_status');
    const logConsole = document.getElementById('log_console');

    function setStatus(running) {
      if(running) {
        statusDiv.textContent = 'BOT RUNNING 🚀';
        statusDiv.classList.remove('bot-stopped');
        startBtn.disabled = true;
        stopBtn.disabled = false;
      } else {
        statusDiv.textContent = 'BOT STOPPED ⏹';
        statusDiv.classList.add('bot-stopped');
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }
    }

    async function fetchStatus() {
      try {
        const resp = await fetch('/bot_status');
        const data = await resp.json();
        setStatus(data.running);
        logConsole.textContent = data.logs.join('
');
        logConsole.scrollTop = logConsole.scrollHeight;
      } catch(e) {}
    }

    startBtn.onclick = async () => {
      await fetch('/bot_start', {method: 'POST'});
      fetchStatus();
    };

    stopBtn.onclick = async () => {
      await fetch('/bot_stop', {method: 'POST'});
      fetchStatus();
    };

    setInterval(fetchStatus, 2500);
    updateNeon('#00ff88');
    fetchStatus();
  </script>
</body>
</html>
'''

# Flask routes (same as before)
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
            json.loads(fbstate_text)
            with open(os.path.join(UPLOAD_FOLDER, 'fbstate.json'), 'w', encoding='utf-8') as f:
                json.dump(json.loads(fbstate_text), f, indent=2)
        except:
            with open(os.path.join(UPLOAD_FOLDER, 'fbstate.json'), 'w', encoding='utf-8') as f:
                f.write(fbstate_text)

    config = {'admin_id': admin_id, 'prefix': prefix, 'thread_id': thread_id, 'neon_color': neon_color}
    with open(os.path.join(UPLOAD_FOLDER, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    return redirect(url_for('index'))

@app.route('/bot_start', methods=['POST'])
def bot_start():
    if not bot_status["running"]:
        bot_status["running"] = True
        bot_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] 🔥 BOT STARTED SUCCESSFULLY!")
        thread = threading.Thread(target=bot_simulator, daemon=True)
        bot_status["thread"] = thread
        thread.start()
    return jsonify({"status": "started"})

@app.route('/bot_stop', methods=['POST'])
def bot_stop():
    if bot_status["running"]:
        bot_status["running"] = False
        bot_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⏹ BOT STOPPED")
    return jsonify({"status": "stopped"})

@app.route('/bot_status')
def bot_status_route():
    return jsonify({
        "running": bot_status["running"],
        "logs": bot_status["logs"][-30:],
        "active_users": bot_status["active_users"]
    })

@app.route('/files')
def files_page():
    files = [name for name in ('fbstate.json', 'config.json') if os.path.exists(os.path.join(UPLOAD_FOLDER, name))]
    return jsonify({'files': files})

@app.route('/download/<path:filename>')
def download_file(filename):
    safe = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, safe)
    if os.path.exists(path):
        return send_from_directory(UPLOAD_FOLDER, safe, as_attachment=True)
    return ("Not found", 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
