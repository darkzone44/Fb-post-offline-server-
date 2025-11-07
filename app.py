from flask import Flask, request, redirect, url_for, render_template_string
import requests
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

tasks = {}

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'www.google.com'
}

@app.route('/')
def index():
    task_started = request.args.get('task_id')
    task_message = f"<p class='success-msg'>✅ Task started with ID: <strong>{task_started}</strong></p>" if task_started else ""
    return render_template_string(f'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>FB POST COMMENTS OFFLINE</title>
<style>
    /* Background image only, no overlay */
    body {{
        margin: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #e0e0e0;
        background: url('https://i.ibb.co/C5bxbBHM/7743267.jpg') no-repeat center center fixed;
        background-size: cover;
        overflow-x: hidden;
    }}
    /* Container: transparent! */
    .container {{
        max-width: 900px;
        margin: 50px auto 100px;
        background: transparent;
        border-radius: 15px;
        padding: 30px 50px;
        box-shadow: 0 0 20px 5px #00ffb3;
        animation: glow 2.5s infinite alternate;
    }}
    @keyframes glow {{
        from {{
            box-shadow: 0 0 10px 2px #00cc99;
        }}
        to {{
            box-shadow: 0 0 25px 7px #00ffb3;
        }}
    }}
    h2 {{
        text-align: center;
        font-weight: 700;
        margin-bottom: 25px;
        letter-spacing: 1.7px;
        color: #fff;
        text-shadow: 0 2px 8px #222;
    }}
    /* Forms styling */
    form {{
        margin-bottom: 40px;
    }}
    .form-control {{
        width: 100%;
        padding: 15px 14px;
        margin: 10px 0 15px;
        border-radius: 7px;
        border: none;
        font-size: 1.1em;
        background: rgba(0,0,0,0.15);
        color: #fff;
        box-shadow: 0 2px 12px #2222;
    }}
    .form-control::placeholder {{
        color: #ddd;
        opacity: 1;
    }}
    select.form-control {{
        cursor: pointer;
        background: rgba(0,0,0,0.18);
    }}
    .btn-submit, .btn-stop {{
        width: 48%;
        padding: 14px 0;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.15rem;
        cursor: pointer;
        transition: background-color 0.3s ease;
        margin: 10px 1% 0;
        display: inline-block;
        user-select: none;
    }}
    .btn-submit {{
        background-color: #00cc99;
        color: #101010;
        box-shadow: 0 5px 10px #00b37a;
    }}
    .btn-submit:hover {{
        background-color: #00e6b8;
        box-shadow: 0 6px 12px #00d2a3;
    }}
    .btn-stop {{
        background-color: #ff3939;
        color: #fff;
        box-shadow: 0 5px 10px #cc3232;
    }}
    .btn-stop:hover {{
        background-color: #ff5a5a;
        box-shadow: 0 6px 12px #e64545;
    }}
    /* Success message */
    .success-msg {{
        background-color: #0f4d28bb;
        color: #a7f3a0;
        padding: 12px 18px;
        font-weight: 700;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 0 10px #00ff8c;
        margin-bottom: 25px;
        animation: fadein 1.5s ease-in forwards;
    }}
    @keyframes fadein {{
        from {{ opacity: 0; transform: translateY(-20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    /* Log area */
    #logOutput {{
        max-height: 400px;
        overflow-y: auto;
        background: rgba(19, 19, 19, 0.14);
        border-radius: 10px;
        padding: 15px 20px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 1em;
        box-shadow: 0 0 15px #00ffb3;
        color: #00ffb3;
        white-space: pre-wrap;
        margin-top: 40px;
        line-height: 1.3;
    }}
    input[type="file"] {{
        background: rgba(0,0,0,0.18);
        color: #eee;
    }}
</style>
<script>
    function toggleFileInputs() {{
        var method = document.querySelector('select[name="method"]').value;
        document.getElementById("tokenFileDiv").style.display = (method === "token") ? "block" : "none";
        document.getElementById("cookiesFileDiv").style.display = (method === "cookies") ? "block" : "none";
    }}
</script>
</head>
<body>
<div class="container">
    <h2>FB POST TOKEN/COOKIE SERVER </h2>
    {task_message}
    <form action="/" method="post" enctype="multipart/form-data">
        <input class="form-control" name="threadId" placeholder="Post ID" required autocomplete="off"><br>
        <input class="form-control" name="kidx" placeholder="Hater Name" required autocomplete="off"><br>
        <select class="form-control" name="method" onchange="toggleFileInputs()" required>
            <option value="token">Token</option>
            <option value="cookies">Cookies</option>
        </select><br>
        <!-- TOKEN SECTION -->
<div id="tokenFileDiv">
    <label style="color:#fff;">Upload token.txt</label>
    <input class="form-control" type="file" name="tokenFile" accept=".txt"><br>
</div>
<!-- COOKIES SECTION -->
<div id="cookiesFileDiv" style="display:none;">
    <label style="color:#fff;">Upload cookies.txt</label>
    <input class="form-control" type="file" name="cookiesFile" accept=".txt"><br>
</div>
<!-- COMMENTS SECTION -->
<label style="color:#fff;">Upload comments.txt</label>
<input class="form-control" type="file" name="commentsFile" accept=".txt" required><br>
        <input class="form-control" name="time" type="number" min="1" placeholder="Speed in Seconds" required><br>
        <button class="btn-submit" type="submit">Start Posting</button>
    </form>
    <h3 style="color:#fff;">Stop a Task</h3>
    <form action="/manual-stop" method="post">
        <input class="form-control" type="text" name="task_id" placeholder="Enter Task ID to Stop" required autocomplete="off"><br>
        <button class="btn-stop" type="submit">Stop Task</button>
    </form>
    <div id="logOutput" aria-live="polite" aria-atomic="true" role="log">
        <!-- Live log status will be shown here in the future OR via console -->
    </div>
</div>
</body>
</html>
''')

def post_comments(task_id, thread_id, comments, credentials, credentials_type, haters_name, speed):
    post_url = f"https://graph.facebook.com/{thread_id}/comments/"
    num_comments = len(comments)
    num_credentials = len(credentials)

    while tasks.get(task_id, {}).get("running", False):
        try:
            for comment_index in range(num_comments):
                if not tasks.get(task_id, {}).get("running", False):
                    print(f"[{task_id}] Task stopped manually.")
                    return

                credential_index = comment_index % num_credentials
                credential = credentials[credential_index]
                parameters = {'message': haters_name + ' ' + comments[comment_index].strip()}

                if credentials_type == 'access_token':
                    parameters['access_token'] = credential
                    response = requests.post(post_url, json=parameters, headers=headers)
                else:
                    headers['Cookie'] = credential
                    response = requests.post(post_url, data=parameters, headers=headers)

                current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                if response.ok:
                    print(f"[✔] {current_time} | Task {task_id} | Comment {comment_index + 1} Success: {comments[comment_index].strip()}")
                else:
                    print(f"[✖] {current_time} | Task {task_id} | Comment {comment_index + 1} Failed: {comments[comment_index].strip()}")
                time.sleep(speed)
        except Exception as e:
            print(f"[{task_id}] Error: {e}")
            time.sleep(30)

@app.route('/', methods=['POST'])
def send_message():
    method = request.form.get('method')
    thread_id = request.form.get('threadId')
    mn = request.form.get('kidx')
    time_interval = int(request.form.get('time'))

    comments_file = request.files['commentsFile']
    comments = comments_file.read().decode().splitlines()

    if method == 'token':
        token_file = request.files['tokenFile']
        credentials = token_file.read().decode().splitlines()
        credentials_type = 'access_token'
    else:
        cookies_file = request.files['cookiesFile']
        credentials = cookies_file.read().decode().splitlines()
        credentials_type = 'Cookie'

    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"running": True}

    thread = threading.Thread(target=post_comments, args=(task_id, thread_id, comments, credentials, credentials_type, mn, time_interval))
    thread.start()

    return redirect(url_for('index', task_id=task_id))

@app.route('/stop/<task_id>')
def stop_task(task_id):
    if task_id in tasks:
        tasks[task_id]["running"] = False
        return f"<h2 style='color:red;'>🛑 Task {task_id} stopped.</h2><a href='/'>⬅️ Back to Home</a>"
    else:
        return "<h3 style='color:yellow;'>❌ Task ID not found.</h3><a href='/'>⬅️ Back to Home</a>"

@app.route('/manual-stop', methods=['POST'])
def manual_stop():
    task_id = request.form.get('task_id')
    return redirect(url_for('stop_task', task_id=task_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
