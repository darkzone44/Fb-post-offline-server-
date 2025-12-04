# app.py
# Render-ready Flask UI that provides big neon-styled input boxes for:
# - Pasting or uploading fbstate.json (or "apostate.json" as user wrote)
# - Admin ID
# - Command prefix
# - Group chat (thread) ID
# - Neon color picker and large layout
#
# Behavior:
# - Saves uploaded/pasted fbstate JSON to `fbstate.json` in the working directory
# - Saves configuration to `config.json` (admin_id, prefix, thread_id, neon_color)
# - Shows success message and provides a button to view/download saved files
# - Designed to be dropped into your bot project folder. Your bot should read fbstate.json and config.json.
#
# Files to add alongside this file for Render:
# requirements.txt content (create file):
# Flask==2.3.2
# gunicorn==20.1.0
#
# Procfile (create file):
# web: gunicorn app:app --bind 0.0.0.0:$PORT
#
# How to use:
# 1) Put this app.py inside your bot project root (next to your bot code).
# 2) Deploy to Render as a Web Service (Python). Render will run the Procfile by default.
# 3) In your bot code, load `fbstate.json` and `config.json` from the working directory.
#
# NOTE: This UI intentionally DOES NOT start or run your bot process. It only writes the files your
# bot expects. Keep your bot code as-is; it should read fbstate.json and config.json when starting.

from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8 MB limit for upload
UPLOAD_FOLDER = os.path.abspath('.')
ALLOWED_EXTENSIONS = {'json'}

HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bot Controller — Paste fbstate.json</title>
  <style>
    /* Basic reset */
    *{box-sizing:border-box;margin:0;padding:0}
    html,body{height:100%}
    body{font-family:Inter,system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; background:#06060a; color:#e6eef8; display:flex; align-items:center; justify-content:center; padding:30px}

    /* Big container */
    .wrap{width:100%;max-width:1100px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border-radius:18px; padding:36px; box-shadow:0 12px 40px rgba(0,0,0,0.7); border:1px solid rgba(255,255,255,0.03)}

    h1{font-size:34px;margin-bottom:8px; letter-spacing:1px}
    p.lead{margin-bottom:20px; color:#bcd3ff}

    .grid{display:grid;grid-template-columns:1fr 420px;gap:24px}

    /* Left column - main form */
    .card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:22px; border-radius:12px; border:1px solid rgba(255,255,255,0.02)}

    label{display:block;font-weight:600;margin-bottom:8px}
    input[type=text], textarea, select{width:100%;padding:14px;border-radius:12px;border:1px solid rgba(255,255,255,0.06);background:rgba(0,0,0,0.25);color:inherit;font-size:16px}
    textarea{min-height:260px;resize:vertical;font-family:monospace}
    .row{display:flex;gap:12px}
    .row > *{flex:1}

    .big-btn{display:inline-block;padding:14px 20px;border-radius:12px;font-weight:700;border:none;cursor:pointer;font-size:16px}

    /* Neon effect box */
    .neon-wrap{padding:18px;border-radius:12px;text-align:center;background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.005));border:1px solid rgba(255,255,255,0.02)}
    .neon-title{font-size:20px;font-weight:800; margin-bottom:10px}
    .neon-box{display:inline-block;padding:10px 18px;border-radius:10px; font-weight:800; font-size:18px; box-shadow:0 0 30px var(--neon), inset 0 0 60px rgba(255,255,255,0.02)}

    /* right column preview */
    .right{position:relative}
    .preview{padding:14px;border-radius:12px;background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.005)); border:1px solid rgba(255,255,255,0.02)}
    .file-list{margin-top:12px}

    footer{margin-top:18px;color:#9fb3ff;font-size:14px}

    /* responsive */
    @media (max-width:980px){.grid{grid-template-columns:1fr}}

    /* subtle animated background lines */
    .bg-lines{position:absolute;left:-60px;top:-60px;right:-60px;bottom:-60px;background-image:linear-gradient(90deg, rgba(255,255,255,0.01) 1px, transparent 1px);background-size:40px 40px;opacity:0.08;transform:rotate(8deg);border-radius:20px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="grid">
      <div>
        <h1>YK TRICKS INDIA — Bot Control Panel</h1>
        <p class="lead">Paste your fbstate.json (or upload), set admin ID, command prefix & group thread ID. Click Save to write files your bot can read.</p>

        <div class="card">
          <form method="post" action="/save" enctype="multipart/form-data">
            <label for="fbstate">Paste fbstate.json (or upload file below)</label>
            <textarea id="fbstate" name="fbstate" placeholder='Paste fbstate.json content here (large textarea)'></textarea>

            <label for="file" style="margin-top:12px">Or upload fbstate.json file</label>
            <input type="file" id="file" name="file" accept="application/json">

            <div style="height:12px"></div>

            <label>Admin ID</label>
            <input type="text" name="admin_id" placeholder="Admin user ID (numeric)">

            <label style="margin-top:12px">Command prefix</label>
            <input type="text" name="prefix" placeholder="e.g. / or ! or ." value="/">

            <label style="margin-top:12px">Group Thread ID</label>
            <input type="text" name="thread_id" placeholder="Thread ID where bot will run">

            <label style="margin-top:12px">Neon color (choose)</label>
            <div class="row">
              <input type="text" id="neon_color" name="neon_color" placeholder="#00ff99 or "" for default" value="#00ff99">
              <input type="color" id="color_picker" value="#00ff99" oninput="document.getElementById('neon_color').value=this.value">
            </div>

            <div style="height:18px"></div>

            <button class="big-btn" style="background:linear-gradient(90deg,var(--neon),#6f9cff); color:black;" type="submit">Save configuration</button>
            <a href="/files" class="big-btn" style="margin-left:10px;background:transparent;color:#a9d3ff;border:1px solid rgba(255,255,255,0.06);">View files</a>
          </form>

          <div style="margin-top:18px;display:flex;gap:12px;align-items:center">
            <div class="neon-wrap" style="flex:1">
              <div class="neon-title">Live Preview</div>
              <div class="neon-box" id="neon_preview">Neon: <span id="neon_text">/</span></div>
            </div>
            <div style="width:120px;text-align:center;color:#bcd3ff">Status<br><strong id="status">Idle</strong></div>
          </div>

        </div>

        <footer>Tip: Deploy this file with your bot project. Bot must read <code>fbstate.json</code> and <code>config.json</code>.</footer>
      </div>

      <div class="right">
        <div class="bg-lines"></div>
        <div class="preview card">
          <h3 style="margin-bottom:8px">Saved files</h3>
          <div class="file-list">
            <ul id="files_ul">
              <!-- Filled by server -->
            </ul>
          </div>

          <div style="margin-top:14px">
            <a href="/download/fbstate.json" class="big-btn" style="background:#ffffff11">Download fbstate.json</a>
            <a href="/download/config.json" class="big-btn" style="margin-left:8px;background:#ffffff11">Download config.json</a>
          </div>

          <div style="margin-top:18px;color:#9fb3ff">Want more UI changes? Tell me the exact color or animation and I'll update.</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // live neon color wiring
    function setNeon(color){
      document.documentElement.style.setProperty('--neon', color);
      document.getElementById('neon_preview').style.boxShadow = '0 0 25px '+color+', inset 0 0 50px rgba(255,255,255,0.02)';
    }
    document.getElementById('color_picker').addEventListener('input', function(e){ setNeon(e.target.value); document.getElementById('neon_text').innerText = document.getElementById('prefix')?.value || document.querySelector('input[name=prefix]')?.value || '/'; });

    // fill file list from server
    fetch('/list').then(r=>r.json()).then(j=>{
      const ul = document.getElementById('files_ul');
      ul.innerHTML='';
      (j.files||[]).forEach(f=>{ const li=document.createElement('li'); li.innerText=f; ul.appendChild(li); })
    })

    // preview prefix
    const prefixInput = document.querySelector('input[name=prefix]');
    if(prefixInput){ prefixInput.addEventListener('input', ()=>{ document.getElementById('neon_text').innerText = prefixInput.value || '/'; }) }

    // initialize neon
    setNeon(document.getElementById('color_picker').value);
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
    # Read textarea content
    fbstate_text = request.form.get('fbstate', '').strip()
    admin_id = request.form.get('admin_id', '').strip()
    prefix = request.form.get('prefix', '/').strip()
    thread_id = request.form.get('thread_id', '').strip()
    neon_color = request.form.get('neon_color', '#00ff99').strip()

    # File upload (optional)
    file = request.files.get('file')
    saved_fbstate_path = None

    # Try save uploaded file first if present
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        dest = os.path.join(UPLOAD_FOLDER, 'fbstate.json')
        file.save(dest)
        saved_fbstate_path = dest
    elif fbstate_text:
        # attempt to parse as JSON (best-effort). If invalid, still write it as text.
        try:
            parsed = json.loads(fbstate_text)
            with open(os.path.join(UPLOAD_FOLDER, 'fbstate.json'), 'w', encoding='utf-8') as f:
                json.dump(parsed, f, indent=2)
            saved_fbstate_path = os.path.join(UPLOAD_FOLDER, 'fbstate.json')
        except Exception:
            # write raw text
            with open(os.path.join(UPLOAD_FOLDER, 'fbstate.json'), 'w', encoding='utf-8') as f:
                f.write(fbstate_text)
            saved_fbstate_path = os.path.join(UPLOAD_FOLDER, 'fbstate.json')

    # Save config
    config = {
        'admin_id': admin_id,
        'prefix': prefix,
        'thread_id': thread_id,
        'neon_color': neon_color
    }
    with open(os.path.join(UPLOAD_FOLDER, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return redirect(url_for('index'))


@app.route('/list')
def list_files():
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
    return ("Not found", 404)


if __name__ == '__main__':
    # When testing locally
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
