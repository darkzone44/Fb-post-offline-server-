# app.py  — Streamlit UI + Selenium messenger sender (real messages)
# Requirements:
#   pip install streamlit selenium chromedriver_autoinstaller
#
# Run:
#   streamlit run app.py
#
# Notes:
#  - Chrome must be installed. chromedriver_autoinstaller will attempt to match driver.
#  - Paste cookie string like: datr=...; fr=...; sb=...; ...
#  - For group or user thread: put the messenger thread id (example: 61564176744081).
#  - Use responsibly.

import streamlit as st
import threading, time, traceback
from queue import Queue, Empty
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Helpers for UI style ----
st.set_page_config(page_title="Messenger Auto Sender", layout="wide")
st.markdown("""
<style>
.box { padding:14px; border-radius:12px; color:#eaf6ff; }
.box-blue{background:linear-gradient(180deg,#001122,#002b4d); border-left:6px solid #00d4ff}
.box-green{background:linear-gradient(180deg,#012012,#003820); border-left:6px solid #00ffa3}
.box-pink{background:linear-gradient(180deg,#2a001d,#4b003f); border-left:6px solid #ff6b6b}
.box-multi{background:linear-gradient(180deg,#121212,#2b2b3a); border-left:6px solid #ffd76b}
.small {font-size:12px; color:rgba(255,255,255,0.8)}
.status {white-space:pre-wrap; font-family:monospace; background:#00000033; padding:8px; border-radius:8px}
</style>
""", unsafe_allow_html=True)

st.title("Messenger — End-to-End Message Sender (Chrome automation)")
st.write("Use responsibly. Only your own account or with permission.")

# layout
col1, col2 = st.columns([1,1])

with col1:
    st.markdown('<div class="box box-blue"><h4>1) Paste Facebook cookie</h4><div class="small">Example: datr=...; fr=...; sb=...; locale=en_GB; ...</div></div>', unsafe_allow_html=True)
    cookie = st.text_area("Facebook cookie (full string)", height=120, placeholder="datr=...; fr=...; sb=...; ...")
    st.markdown('<div style="margin-top:6px" class="small">Need cookie quickly? Click the bookmarklet helper below, create a bookmark with the code and run it on facebook.com to copy cookie to clipboard.</div>', unsafe_allow_html=True)
    if st.button("Copy Cookie Bookmarklet code"):
        code = ("javascript:(()=>{try{const c=document.cookie; navigator.clipboard.writeText(c); alert('Cookie copied to clipboard');}catch(e){prompt('Please copy cookie manually', document.cookie);}})()")
        st.code(code, language='javascript')

    st.markdown("")  # spacer

    st.markdown('<div class="box box-green"><h4>2) Target & Mode</h4></div>', unsafe_allow_html=True)
    mode = st.selectbox("Mode", ["singleUID", "groupThread", "bulk", "autoLoop"], help="singleUID = single user thread, groupThread = one group thread, bulk = multiple thread ids, autoLoop = keep looping messages at delay")
    if mode == "bulk":
        targets = st.text_area("Targets (comma separated thread/UIDs)", placeholder="61564..., 12345..., 67890...")
    else:
        target = st.text_input("Target thread ID / UID (example: 61564176744081)")
    delay_ms = st.number_input("Delay between messages (ms)", min_value=300, value=3000, step=100)
    maxsend = st.number_input("Max messages to send (0 = unlimited for chosen mode)", min_value=0, value=0, step=1)
    headless = st.checkbox("Run Chrome headless (no browser window). Uncheck to watch)", value=False)

with col2:
    st.markdown('<div class="box box-pink"><h4>3) Messages</h4></div>', unsafe_allow_html=True)
    messages_text = st.text_area("Messages (one per line)", height=240, placeholder="Hello\\nThis is an automated message")
    uploaded = st.file_uploader("Or upload .txt file (one message per line)", type=['txt'])
    if uploaded is not None:
        messages_text = uploaded.getvalue().decode('utf-8')

    st.markdown('<div class="box box-multi"><h4>Controls</h4></div>', unsafe_allow_html=True)
    start_btn = st.button("Start")
    stop_btn = st.button("Stop")
    st.markdown("**Status / Logs**")
    status_area = st.empty()
    status_area.text("Idle.")

# --- Backend automation logic ---
RUN_THREAD = None
STOP_EVENT = threading.Event()

def parse_cookie_string(cookie_str):
    parts = cookie_str.split(';')
    cookies = []
    for p in parts:
        p = p.strip()
        if not p: continue
        if '=' not in p: continue
        name, val = p.split('=', 1)
        cookies.append({'name': name.strip(), 'value': val.strip(), 'domain': '.facebook.com', 'path': '/', 'httpOnly': False, 'secure': True})
    return cookies

def find_input_selector(driver, timeout=8):
    selectors = [
        'div[contenteditable="true"][role="combobox"]',
        'div[role="textbox"][contenteditable="true"]',
        'div[contenteditable="true"]',
        'textarea'
    ]
    for sel in selectors:
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            return sel
        except Exception:
            pass
    return None

def get_last_message_text(driver):
    try:
        script = """
        (function(){
          const nodes = Array.from(document.querySelectorAll('div[dir="auto"], span, div')).slice(-40);
          for(let i=nodes.length-1;i>=0;i--){
             const t = nodes[i].innerText || '';
             if(t && t.trim()) return t.trim();
          }
          return '';
        })();
        """
        return driver.execute_script(script)
    except Exception:
        return ""

def send_message_in_page(driver, selector, text):
    # For contenteditable, set innerText then input event; else set value.
    try:
        is_ce = driver.execute_script("const e=document.querySelector(arguments[0]); return !!(e && e.isContentEditable);", selector)
    except Exception:
        is_ce = False
    if is_ce:
        driver.execute_script("""
            const sel = arguments[0], msg = arguments[1];
            const e = document.querySelector(sel);
            if(!e) return false;
            e.focus();
            e.innerHTML = '';
            e.appendChild(document.createTextNode(msg));
            e.dispatchEvent(new Event('input', {bubbles:true}));
            return true;
        """, selector, text)
        # press enter
        el = driver.find_element(By.CSS_SELECTOR, selector)
        el.send_keys(Keys.ENTER)
    else:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            el.clear()
            el.send_keys(text)
            el.send_keys(Keys.ENTER)
        except Exception:
            # fallback: use script to find a textbox and set value & dispatch
            driver.execute_script("""
                const sel = arguments[0], msg = arguments[1];
                const e = document.querySelector(sel);
                if(!e) return false;
                e.value = msg;
                e.dispatchEvent(new Event('input', {bubbles:true}));
                return true;
            """, selector, text)
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                el.send_keys(Keys.ENTER)
            except Exception:
                pass

def messenger_send_loop(params, out_q, stop_event):
    """
    params: dict with cookie, mode, target/targets, messages(list), delay_ms, headless, maxsend
    Writes logs to out_q
    """
    try:
        out_q.put("Installing / matching chromedriver...")
        chromedriver_autoinstaller.install()  # installs matching chromedriver if necessary
        options = webdriver.ChromeOptions()
        # keep some options to make stable
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if params.get("headless"):
            options.add_argument("--headless=new")
        # you can set user-data-dir to keep session, but we use cookies so not needed
        out_q.put("Launching Chrome...")
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        out_q.put("Failed to start Chrome / chromedriver: " + str(e))
        out_q.put(traceback.format_exc())
        return

    try:
        # Set cookies
        cookies = parse_cookie_string(params.get("cookie",""))
        out_q.put(f"Parsed {len(cookies)} cookies.")
        out_q.put("Opening facebook.com to set cookies...")
        try:
            driver.get("https://www.facebook.com")
        except Exception as e:
            out_q.put("Warning: navigation to facebook.com failed initially: " + str(e))

        # add cookies
        for c in cookies:
            try:
                # Selenium requires domain match; ensure domain set
                driver.add_cookie(c)
            except Exception as e:
                out_q.put("Warning: cookie add failed for " + c.get('name','') + " : " + str(e))

        # helper to open messenger thread and send
        def open_and_send_thread(thread_id):
            try:
                url = f"https://www.messenger.com/t/{thread_id}"
                out_q.put("Navigating to " + url)
                driver.get(url)
                # wait for visible input
                sel = find_input_selector(driver, timeout=12)
                if not sel:
                    out_q.put("Message input not found on page. You may not be logged in (cookie invalid) or UI changed.")
                    return False
                out_q.put("Found input selector: " + sel)
                # send messages list
                sent_local = 0
                for text in params['messages']:
                    if stop_event.is_set(): return True
                    out_q.put("Sending: " + (text if len(text)<160 else text[:160]+"..."))
                    send_message_in_page(driver, sel, text)
                    # confirm (short loop)
                    ok = False
                    startt = time.time()
                    while time.time() - startt < 6:
                        last = get_last_message_text(driver)
                        if last and text.strip()[:40] in last:
                            ok = True
                            break
                        time.sleep(0.5)
                    out_q.put("Sent confirmed: " + str(ok))
                    sent_local += 1
                    params['_sent_count'] = params.get('_sent_count',0) + 1
                    if params.get('maxsend') and params.get('_sent_count') >= params.get('maxsend'):
                        out_q.put("Reached maxsend limit.")
                        return True
                    # delay with stop checks
                    waited = 0
                    while waited < params['delay_ms']:
                        if stop_event.is_set(): return True
                        time.sleep(0.25)
                        waited += 250
                return True
            except Exception as e:
                out_q.put("Error in open_and_send_thread: " + str(e))
                out_q.put(traceback.format_exc())
                return False

        # Mode handling
        mode = params['mode']
        out_q.put("Mode: " + mode)
        if mode == "singleUID" or mode == "groupThread":
            tid = params['target']
            open_and_send_thread(tid)
        elif mode == "bulk":
            tlist = params['targets']
            for t in tlist:
                if stop_event.is_set(): break
                open_and_send_thread(t.strip())
        elif mode == "autoLoop":
            target = params['target']
            while not stop_event.is_set():
                ok = open_and_send_thread(target)
                if stop_event.is_set(): break
                # after one round, wait delay_ms (we already wait after each message but add small pause)
                time.sleep(max(1, params['delay_ms']/1000))
        else:
            out_q.put("Unknown mode: " + str(mode))

    except Exception as e:
        out_q.put("Fatal error during run: " + str(e))
        out_q.put(traceback.format_exc())
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        out_q.put("Task finished. Driver closed.")

# Manage thread and queue for logs
log_q = Queue()

def start_background(params):
    global RUN_THREAD, STOP_EVENT, log_q
    STOP_EVENT.clear()
    log_q = Queue()
    RUN_THREAD = threading.Thread(target=messenger_send_loop, args=(params, log_q, STOP_EVENT), daemon=True)
    RUN_THREAD.start()

def stop_background():
    global STOP_EVENT
    STOP_EVENT.set()

# When start button pressed
if start_btn:
    msgs = [m.strip() for m in (messages_text or "").splitlines() if m.strip()]
    if not cookie:
        status_area.text("Please paste your Facebook cookie.")
    elif not msgs:
        status_area.text("Please provide at least one message.")
    else:
        # prepare params
        if mode == "bulk":
            tlist = [t.strip() for t in (targets or "").split(",") if t.strip()]
            if not tlist:
                status_area.text("Provide at least one target for bulk mode.")
            else:
                params = {"cookie": cookie, "mode": mode, "targets": tlist, "messages": msgs, "delay_ms": int(delay_ms), "headless": headless, "maxsend": int(maxsend)}
                status_area.text("Starting background task...")
                start_background(params)
                time.sleep(0.3)
        else:
            tgt = target if 'target' in locals() else ""
            if not tgt:
                status_area.text("Provide target thread/UID.")
            else:
                params = {"cookie": cookie, "mode": mode, "target": tgt, "messages": msgs, "delay_ms": int(delay_ms), "headless": headless, "maxsend": int(maxsend)}
                status_area.text("Starting background task...")
                start_background(params)
                time.sleep(0.3)

# When stop button pressed
if stop_btn:
    stop_background()
    status_area.text("Stop requested...")

# Live log streaming to UI
# show logs while thread running or for 3 seconds after finish
def drain_queue_display(timeout=0.2):
    messages = []
    try:
        while True:
            line = log_q.get_nowait()
            messages.append(line)
    except Empty:
        pass
    if messages:
        prev = status_area.text_area("Logs", value="\n".join(messages), height=300)
        # alternatively update a streaming text
    return messages

# Poll UI for logs
if 'RUN_THREAD' in globals() and RUN_THREAD:
    # if thread alive show logs continuously
    if RUN_THREAD.is_alive():
        # read up to 100 lines quickly
        out_lines = []
        while True:
            try:
                out_lines.append(log_q.get_nowait())
            except Empty:
                break
        if out_lines:
            status_area.text("\n".join(out_lines[-40:]))
        else:
            status_area.text("Running... (no new logs yet)")
    else:
        # thread finished, drain remaining logs
        out_lines = []
        while True:
            try:
                out_lines.append(log_q.get_nowait())
            except Empty:
                break
        if out_lines:
            status_area.text("Finished.\n\n" + "\n".join(out_lines[-80:]))
        else:
            status_area.text("Finished. No logs captured.")
else:
    # no background thread — show nothing or last logs
    # try to drain queue once
    tmp = []
    try:
        while True:
            tmp.append(log_q.get_nowait())
    except Exception:
        pass
    if tmp:
        status_area.text("\n".join(tmp[-80:]))
    else:
        status_area.text("Idle.")

# Simple footer / tips
st.markdown("""
---  
**Tips:**  
- If Chrome/driver fails: ensure Google Chrome is installed on your machine. chromedriver_autoinstaller will fetch matching driver automatically.  
- If you run on a hosted service, you must install Chrome/Chromium in that environment and allow the driver to be installed; otherwise prefer to run locally.  
- Use delays (>=3000 ms) to avoid abuse detection.
""")
