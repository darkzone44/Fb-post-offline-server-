from flask import Flask, render_template_string, request
import requests
import threading
import time

app = Flask(__name__)

LOGS = []

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>REAL FB Message Sender</title>
<style>
body {
    background: url('https://i.ibb.co/gS2j0yW/neon-bg.jpg');
    background-size: cover;
    font-family: Arial;
    color: #00ffea;
    text-align: center;
}
.box {
    width: 80%;
    margin: auto;
    padding: 20px;
    border: 2px solid #00ffff;
    border-radius: 10px;
    backdrop-filter: blur(10px);
}
input, textarea {
    width: 90%;
    padding: 10px;
    margin: 10px;
    border-radius: 8px;
}
button {
    background: #00ffff;
    padding: 10px 30px;
    border: 0;
    font-size: 18px;
    border-radius: 10px;
}
#logs {
    width: 90%;
    height: 250px;
    background: black;
    color: #00ff00;
    padding: 10px;
    overflow-y: scroll;
    margin-top: 20px;
}
</style>
</head>
<body>

<h1>REAL Facebook Message Sender</h1>

<div class="box">
<h2>Cookies</h2>
<textarea id="cookies" placeholder="Paste Cookies Here"></textarea>

<h2>1. Inbox Message</h2>
<input id="uid" placeholder="User ID">
<textarea id="msg1" placeholder="Message"></textarea>

<h2>2. Group Message</h2>
<input id="thread" placeholder="Group Thread ID">
<textarea id="msg2" placeholder="Message"></textarea>

<button onclick="sendInbox()">Send Inbox</button>
<button onclick="sendGroup()">Send Group</button>

<h2>Live Logs</h2>
<div id="logs"></div>
</div>

<script>
function log(t){
    document.getElementById("logs").innerHTML += t + "<br>";
}

function sendInbox(){
    fetch("/send_inbox", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            cookies:document.getElementById("cookies").value,
            uid:document.getElementById("uid").value,
            msg:document.getElementById("msg1").value
        })
    })
    .then(r=>r.text())
    .then(t=>log(t));
}

function sendGroup(){
    fetch("/send_group", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            cookies:document.getElementById("cookies").value,
            thread:document.getElementById("thread").value,
            msg:document.getElementById("msg2").value
        })
    })
    .then(r=>r.text())
    .then(t=>log(t));
}

setInterval(()=>{
    fetch("/logs")
    .then(r=>r.text())
    .then(t=>{
        document.getElementById("logs").innerHTML = t;
    });
},2000);
</script>

</body>
</html>
"""

def add_log(t):
    LOGS.append(t)
    print(t)

def send_real_message(cookies_raw, uid_or_thread, message, inbox=True):
    try:
        cookies = {}
        for x in cookies_raw.split(";"):
            if "=" in x:
                k,v = x.strip().split("=",1)
                cookies[k]=v

        url = "https://graph.facebook.com/v15.0/me/messages"

        data = {
            "recipient":{
                "id": uid_or_thread
            },
            "message":{
                "text": message
            }
        }

        add_log("Sending...")
        r = requests.post(url, cookies=cookies, json=data)

        if r.status_code == 200:
            add_log("✔ Sent Successfully!")
        else:
            add_log("✖ Failed: " + r.text)

    except Exception as e:
        add_log("Error: " + str(e))


@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/send_inbox", methods=["POST"])
def send_inbox():
    d = request.json
    threading.Thread(target=send_real_message, args=(d["cookies"], d["uid"], d["msg"], True)).start()
    return "Inbox Sending Started..."

@app.route("/send_group", methods=["POST"])
def send_group():
    d = request.json
    threading.Thread(target=send_real_message, args=(d["cookies"], d["thread"], d["msg"], False)).start()
    return "Group Sending Started..."

@app.route("/logs")
def logs():
    return "<br>".join(LOGS[-50:])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
  
