import streamlit as st
import requests
import time
import json

# =============== UI SETUP ===============

page_bg = """
<style>
  body {
    background-image: url('https://i.imgur.com/eY1ZQqW.jpeg');
    background-size: cover;
    background-attachment: fixed;
  }

  .big-title {
    font-size: 40px;
    color: #00ffcc;
    text-shadow: 0px 0px 20px #00fff2;
    text-align: center;
    font-weight: 900;
  }

  .box {
    background: rgba(0,0,0,0.6);
    padding: 20px;
    border-radius: 15px;
    border: 2px solid #00ffc3;
    box-shadow: 0px 0px 15px #00ffe6;
  }

  .logbox {
    background: rgba(0,0,0,0.6);
    padding: 15px;
    border-radius: 10px;
    height: 250px;
    overflow-y: auto;
    border: 1px solid #00ffc8;
    color: #00ffea;
    font-size: 14px;
  }
</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)
st.markdown("<div class='big-title'>🔥 REAL FACEBOOK MESSAGE SENDER (NON-E2EE) 🔥</div>", unsafe_allow_html=True)
st.markdown("### *Group + Inbox दोनों में काम करेगा* 🚀")

st.markdown("<div class='box'>", unsafe_allow_html=True)

cookie_input = st.text_area("👉 अपनी Facebook Cookies Paste करें (c_user, xs, fr, fbl_st आदि)", height=120)
rec_id = st.text_input("👉 Receiver ID / Group Thread ID डालें")
msg = st.text_area("👉 Message लिखें", height=100)

send_btn = st.button("🔥 SEND MESSAGE 🔥")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### 📡 Live Logs")
log_window = st.empty()

# =============== COOKIE PARSER ===============

def cookie_to_dict(raw_cookie):
    cookies = {}
    try:
        parts = raw_cookie.split(";")
        for p in parts:
            if "=" in p:
                key, val = p.strip().split("=", 1)
                cookies[key] = val
        return cookies
    except:
        return None

# =============== MESSAGE SENDER ===============

def send_message(cookies, thread_id, text):
    url = "https://www.facebook.com/api/graphql/"

    payload = {
        "av": cookies.get("c_user"),
        "__aaid": cookies.get("c_user"),
        "batch_name": "MessengerSendMessageMutation",
        "variables": json.dumps({
            "message": {"text": text},
            "client_mutation_id": "1",
            "actor_id": cookies.get("c_user"),
            "recipient_id": thread_id
        }),
        "doc_id": "5301165566584771"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    return requests.post(url, data=payload, cookies=cookies, headers=headers)

# =============== BUTTON CLICK ===============

if send_btn:
    if cookie_input.strip() == "" or rec_id.strip() == "" or msg.strip() == "":
        st.error("❌ सभी बॉक्स भरना जरूरी है!")
    else:
        cookies = cookie_to_dict(cookie_input)

        if not cookies:
            st.error("❌ Cookies गलत हैं!")
        else:
            log_window.write("🔄 Sending message...")
            try:
                res = send_message(cookies, rec_id, msg)

                if "errors" in res.text or res.status_code != 200:
                    log_window.write("❌ Message send failed!")
                    log_window.write(res.text)
                else:
                    log_window.write("✅ Message Sent Successfully!")
                    log_window.write(res.text[:500])

            except Exception as e:
                log_window.write("❌ ERROR:")
                log_window.write(str(e))
                
