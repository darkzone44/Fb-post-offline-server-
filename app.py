import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

st.markdown(
    """
    <style>
        .main {background-color: #111;}
        div.stButton > button {
            background-color: #172b4d; color: #00FF00; border-radius: 10px; font-size: 16px; font-weight: bold;
            border: 2px solid #60f34a; box-shadow: 0 0 10px #1aff06;
        }
        .console { background: #000211; border-radius: 8px; box-shadow: 0 0 10px #39ff14;
            font-family: monospace; color: #39ff14; padding: 12px; margin-top: 14px; min-height:180px;}
        .neon-label { font-size:22px; color:#00ffa3; font-family:monospace; margin-bottom:5px; }
        .config-box {background: #0a2127; border-radius: 10px; box-shadow: 0 0 10px #19fbffb3; padding: 15px; margin: 8px 0;}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="neon-label">SYSTEM CONSOLE <span style="color:#0f0">● ACTIVE</span></div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="config-box"><b>Your Configuration</b></div>', unsafe_allow_html=True)
    fb_user = st.text_input("Facebook Username/Email")
    fb_pass = st.text_input("Facebook Password", type="password")
    chat_id = st.text_input("Conversation ID (eg. 61564176744081)")
    delay = st.slider("Delay seconds", 5,60,12)
    msg = st.text_area("Enter Message")

st.markdown('<div class="config-box"><b>Automation Control</b></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
run_bot = col1.button("▶ START E2EE")
stop_bot = col2.button("■ STOP E2EE")

console = st.empty()

def send_e2ee_message(fb_user, fb_pass, chat_id, msg, delay, console):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-data-dir=chrome-profile')
    driver = webdriver.Chrome(options=chrome_options)

    logs = []
    try:
        logs.append("[AUTO] Opening Facebook login page...")
        driver.get("https://www.facebook.com/login/")
        time.sleep(4)

        logs.append("[AUTO] Logging in as user...")
        driver.find_element(By.ID, "email").send_keys(fb_user)
        driver.find_element(By.ID, "pass").send_keys(fb_pass)
        driver.find_element(By.NAME, "login").click()
        time.sleep(8)

        url = f"https://www.facebook.com/messages/t/{chat_id}"
        logs.append(f"[AUTO] Navigating to: {url} ...")
        driver.get(url)
        time.sleep(5)

        selectors = [
            (By.CSS_SELECTOR, "div[role='textbox']"),
            (By.CSS_SELECTOR, "div[aria-label='Message']"),
            (By.CSS_SELECTOR, "div[contenteditable='true']"),
            (By.XPATH, "//div[@role='textbox']"),
        ]
        input_box = None
        for by, pattern in selectors:
            try:
                input_box = driver.find_element(by, pattern)
                break
            except Exception:
                logs.append(f"[AUTO] Selector failed: {pattern}")
                continue

        if not input_box:
            logs.append("[ERROR] Message input not found! FB layout update ho sakta hai.")
            driver.quit()
            # Fixed log join
            console.markdown('<div class="console">' + "
".join(logs) + '</div>', unsafe_allow_html=True)
            return

        input_box.click()
        input_box.send_keys(msg)
        time.sleep(1)
        input_box.send_keys(Keys.RETURN)
        logs.append(f"[AUTO] Message sent: {msg}")
        time.sleep(delay)
        driver.quit()
        logs.append("[AUTO] Browser closed.")

    except Exception as e:
        logs.append(f"[ERROR] {str(e)}")
        driver.quit()

    # Fixed log join
    console.markdown('<div class="console">' + "
".join(logs) + '</div>', unsafe_allow_html=True)

if run_bot and fb_user and fb_pass and chat_id and msg:
    console.markdown('<div class="console">[AUTO] Automation starting...</div>', unsafe_allow_html=True)
    send_e2ee_message(fb_user, fb_pass, chat_id, msg, delay, console)

if stop_bot:
    console.markdown('<div class="console">[AUTO] Automation stopped.</div>', unsafe_allow_html=True)
