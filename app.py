# app.py
import streamlit as st
import threading, time, traceback
from typing import List, Dict
from playwright.sync_api import sync_playwright, Browser, Page

# ------------------------
# Helpers
# ------------------------
def parse_cookie_string(cookie_str: str):
    out = []
    for part in cookie_str.split(';'):
        p = part.strip()
        if not p or '=' not in p:
            continue
        name, val = p.split('=',1)
        out.append({'name': name.strip(), 'value': val.strip(), 'domain': '.facebook.com', 'path': '/'})
    return out

def log_status(msg: str):
    ts = time.strftime('%H:%M:%S')
    st.session_state['logs'].append(f"[{ts}] {msg}")
    if len(st.session_state['logs']) > 500:
        st.session_state['logs'] = st.session_state['logs'][-500:]

# ------------------------
# Worker
# ------------------------
class MessengerWorker:
    def __init__(self, cookie, targets, messages, delay_ms, mode, maxsend, headless=False, chrome_path=None):
        self.cookie = cookie
        self.targets = targets[:]  # thread ids
        self.messages = messages[:]
        self.delay_ms = max(300, int(delay_ms))
        self.mode = mode
        self.maxsend = int(maxsend)
        self.headless = bool(headless)
        self.chrome_path = chrome_path or None
        self._stop = False
        self.sent = 0
        self._pw = None
        self._browser = None
        self._page = None

    def stop(self):
        self._stop = True
        log_status("Stop requested by user")

    def _open(self):
        self._pw = sync_playwright().start()
        launch_args = {"headless": self.headless, "args": ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage']}
        if self.chrome_path:
            launch_args["executable_path"] = self.chrome_path
        self._browser = self._pw.chromium.launch(**launch_args)
        self._page = self._browser.new_page()

    def _close(self):
        try:
            if self._page: self._page.close()
            if self._browser: self._browser.close()
            if self._pw: self._pw.stop()
        except:
            pass

    def _set_cookies(self):
        cookies = parse_cookie_string(self.cookie)
        if not cookies:
            log_status("No cookies provided")
            return
        try:
            self._page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        try:
            self._page.context.add_cookies(cookies)
            log_status(f"Set {len(cookies)} cookies")
        except Exception as e:
            log_status(f"Failed to set cookies: {e}")

    def _wait_input(self, timeout_ms=8000):
        selectors = [
            'div[contenteditable="true"][role="combobox"]',
            'div[role="textbox"][contenteditable="true"]',
            'div[contenteditable="true"]',
            'textarea'
        ]
        for s in selectors:
            try:
                self._page.wait_for_selector(s, timeout=timeout_ms)
                return s
            except Exception:
                continue
        return None

    def _send_in_thread(self):
        sel = self._wait_input()
        if not sel:
            raise RuntimeError("Message input not found. Check login / UI.")
        for msg in self.messages:
            if self._stop:
                return
            log_status("Typing message (preview): " + (msg[:80] + ("..." if len(msg)>80 else "")))
            try:
                self._page.evaluate("""(sel, msg) => {
                    const e = document.querySelector(sel);
                    if (!e) return false;
                    if (e.isContentEditable) { e.focus(); e.innerHTML=''; e.appendChild(document.createTextNode(msg)); e.dispatchEvent(new Event('input',{bubbles:true})); }
                    else if ('value' in e) { e.value = msg; e.dispatchEvent(new Event('input',{bubbles:true})); }
                    else { e.innerText = msg; }
                    return true;
                }""", sel, msg)
                self._page.keyboard.press("Enter")
            except Exception as e:
                log_status("Send error: " + str(e))
            wait = 0
            while wait < 1.5 and not self._stop:
                time.sleep(0.3); wait += 0.3
            self.sent += 1
            st.session_state['sent'] = self.sent
            if self.maxsend > 0 and self.sent >= self.maxsend:
                log_status("Reached maxsend limit")
                return

    def run(self):
        try:
            log_status("Launching browser...")
            self._open()
            log_status("Applying cookies...")
            self._set_cookies()
            if self.mode in ("single","group","loop"):
                target = self.targets[0]
                url = f"https://www.messenger.com/t/{target}"
                log_status("Opening: " + url)
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                if self.mode == "loop":
                    while not self._stop:
                        self._send_in_thread()
                        if self._stop: break
                        log_status(f"Sleeping {(self.delay_ms/1000):.1f}s before next loop")
                        time.sleep(self.delay_ms/1000)
                else:
                    self._send_in_thread()
            elif self.mode == "bulk":
                for t in self.targets:
                    if self._stop: break
                    url = f"https://www.messenger.com/t/{t}"
                    log_status("Opening: " + url)
                    self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    self._send_in_thread()
            else:
                raise RuntimeError("Unknown mode")
            log_status("Task finished")
        except Exception as e:
            log_status("ERROR: " + str(e))
            log_status(traceback.format_exc())
        finally:
            try: self._close()
            except: pass
            log_status("Browser closed")

# ------------------------
# Streamlit UI
# ------------------------
st.set_page_config(page_title="Messenger Sender", layout="wide")
st.markdown("""<style>
body { background: radial-gradient(circle at 10% 10%, rgba(0,200,255,0.06), transparent 20%), radial-gradient(circle at 90% 90%, rgba(255,100,200,0.03), transparent 20%), #05060a; }
.section { background: rgba(255,255,255,0.02); border-radius:12px; padding:12px; }
.neon { box-shadow: 0 0 18px rgba(0,255,200,0.08); }
</style>""", unsafe_allow_html=True)

st.title("💬 Messenger Sender — Non-E2EE (cookie based)")
cols = st.columns([1,1])
if 'logs' not in st.session_state: st.session_state['logs'] = []
if 'sent' not in st.session_state: st.session_state['sent'] = 0
if 'worker' not in st.session_state: st.session_state['worker'] = None
if 'thread_obj' not in st.session_state: st.session_state['thread_obj'] = None

with cols[0]:
    st.subheader("Inputs")
    cookie = st.text_area("Facebook cookie (paste full cookie string)", height=120)
    mode = st.selectbox("Mode", options=["single","group","bulk","loop"], index=0)
    if mode in ("single","group","loop"):
        target = st.text_input("Target thread ID / UID (e.g. 61564176744081)")
        targets = [target] if target else []
    else:
        targets_text = st.text_area("Targets (one per line)")
        targets = [t.strip() for t in targets_text.splitlines() if t.strip()]
    delay_ms = st.number_input("Delay between cycles (ms)", value=3000, min_value=300)
    maxsend = st.number_input("Max sends (0=unlimited)", value=0, min_value=0)
    headless = st.checkbox("Headless (no browser window)", value=False)
    chrome_path = st.text_input("Optional CHROME_PATH (leave blank to use Playwright's chromium)")

with cols[1]:
    st.subheader("Messages & Controls")
    messages_text = st.text_area("Messages (one per line)", height=200)
    messages = [m.strip() for m in messages_text.splitlines() if m.strip()]
    start = st.button("Start")
    stop = st.button("Stop")
    st.markdown("**Cookie helper bookmarklet** — click to copy and create a bookmark (open facebook.com then click it to copy cookies).")
    if st.button("Copy bookmarklet"):
        bm = "javascript:(()=>{try{navigator.clipboard.writeText(document.cookie);alert('Cookie copied');}catch(e){prompt('Copy cookie',document.cookie);}})()"
        st.write("Bookmarklet code:"); st.code(bm)

st.markdown("---")
st.subheader("Logs / Live Console")
st.text_area("Logs", value="\\n".join(st.session_state['logs']), height=300, key='logs_box', disabled=True)
st.metric("Sent", st.session_state['sent'])

# Start/Stop handling
if start:
    if not cookie or not targets or not messages:
        st.error("Provide cookie, target(s) and messages before starting.")
    else:
        if st.session_state['worker'] is not None:
            st.warning("A worker is already running. Stop it first.")
        else:
            worker = MessengerWorker(cookie=cookie, targets=targets, messages=messages, delay_ms=delay_ms, mode=mode, maxsend=maxsend, headless=headless, chrome_path=chrome_path or None)
            st.session_state['worker'] = worker
            def runner():
                log_status("Worker thread starting...")
                worker.run()
                log_status("Worker thread terminated.")
                st.session_state['worker'] = None
            t = threading.Thread(target=runner, daemon=True)
            st.session_state['thread_obj'] = t
            t.start()
            st.success("Worker started. Watch logs for progress.")
if stop:
    if st.session_state.get('worker'):
        st.session_state['worker'].stop()
        st.success("Stop requested.")
    else:
        st.info("No worker running.")
    
