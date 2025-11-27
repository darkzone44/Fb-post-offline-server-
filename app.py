# app.py
# Streamlit UI + Playwright (sync) automation for non-E2EE Messenger threads
# Usage:
#  - pip install -r requirements.txt
#  - python -m playwright install chromium
#  - streamlit run app.py
#
# WARNING: Keep your cookie private. Use only your own account. Don't spam.

import streamlit as st
import threading, time, traceback
from typing import List
from playwright.sync_api import sync_playwright, Page

# -------------------------
# Helpers
# -------------------------
def parse_cookie_string(cookie_str: str):
    out = []
    if not cookie_str:
        return out
    for part in cookie_str.split(';'):
        p = part.strip()
        if not p or '=' not in p:
            continue
        name, val = p.split('=', 1)
        out.append({'name': name.strip(), 'value': val.strip(), 'domain': '.facebook.com', 'path': '/'})
    return out

def append_log(txt: str):
    ts = time.strftime("%H:%M:%S")
    st.session_state['logs'].append(f"[{ts}] {txt}")
    # keep last 500 lines
    if len(st.session_state['logs']) > 500:
        st.session_state['logs'] = st.session_state['logs'][-500:]

# -------------------------
# Worker (Playwright)
# -------------------------
class MessengerWorker:
    def __init__(self, cookie: str, targets: List[str], messages: List[str], delay_ms: int, mode: str, maxsend: int, headless: bool=False, chrome_path: str=None):
        self.cookie = cookie
        self.targets = targets[:]  # list of thread ids / uids
        self.messages = messages[:]
        self.delay_ms = max(300, int(delay_ms))
        self.mode = mode  # single, group, bulk, loop
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
        append_log("Stop requested")

    def _open(self):
        append_log("Starting Playwright...")
        self._pw = sync_playwright().start()
        launch_opts = {"headless": self.headless, "args": ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage']}
        if self.chrome_path:
            launch_opts["executable_path"] = self.chrome_path
            append_log(f"Using CHROME_PATH: {self.chrome_path}")
        try:
            self._browser = self._pw.chromium.launch(**launch_opts)
            self._page = self._browser.new_page()
            append_log("Browser launched")
        except Exception as e:
            raise RuntimeError(f"Playwright launch failed: {e}")

    def _close(self):
        try:
            if self._page: self._page.close()
        except: pass
        try:
            if self._browser: self._browser.close()
        except: pass
        try:
            if self._pw: self._pw.stop()
        except: pass
        append_log("Browser closed")

    def _set_cookies(self):
        cookies = parse_cookie_string(self.cookie)
        if not cookies:
            append_log("No cookies provided")
            return
        try:
            # navigate to origin then add cookies to context
            try:
                self._page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            self._page.context.add_cookies(cookies)
            append_log(f"Applied {len(cookies)} cookies")
        except Exception as e:
            append_log(f"Failed to set cookies: {e}")
            raise

    def _wait_input_sel(self, timeout=8000):
        selectors = [
            'div[contenteditable="true"][role="combobox"]',
            'div[role="textbox"][contenteditable="true"]',
            'div[contenteditable="true"]',
            'textarea'
        ]
        for sel in selectors:
            try:
                self._page.wait_for_selector(sel, timeout=timeout)
                return sel
            except Exception:
                continue
        return None

    def _send_in_thread(self):
        sel = self._wait_input_sel(timeout=8000)
        if not sel:
            raise RuntimeError("Message input not found on this page — check cookie / login / UI.")
        for msg in self.messages:
            if self._stop:
                return
            append_log(f"Typing message preview: {msg[:80] + ('...' if len(msg) > 80 else '')}")
            try:
                # set the content of contenteditable / input
                self._page.evaluate(
                    """(sel, msg) => {
                        const e = document.querySelector(sel);
                        if (!e) return false;
                        if (e.isContentEditable) {
                            e.focus();
                            e.innerHTML = '';
                            e.appendChild(document.createTextNode(msg));
                            e.dispatchEvent(new Event('input', { bubbles: true }));
                        } else if ('value' in e) {
                            e.value = msg;
                            e.dispatchEvent(new Event('input', { bubbles: true }));
                        } else {
                            e.innerText = msg;
                        }
                        return true;
                    }""",
                    sel, msg
                )
                # press Enter
                self._page.keyboard.press("Enter")
            except Exception as e:
                append_log(f"Send error: {e}")
            # small wait
            t_wait = 0.0
            while t_wait < 1.5 and not self._stop:
                time.sleep(0.3); t_wait += 0.3
            self.sent += 1
            st.session_state['sent'] = self.sent
            if self.maxsend > 0 and self.sent >= self.maxsend:
                append_log("Reached maxsend limit")
                return

    def run(self):
        try:
            self._open()
            self._set_cookies()

            # handle modes
            if self.mode in ("single", "group", "loop"):
                if not self.targets:
                    raise RuntimeError("No target provided")
                target = self.targets[0]
                url = f"https://www.messenger.com/t/{target}"
                append_log(f"Opening {url}")
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                if self.mode == "loop":
                    while not self._stop:
                        self._send_in_thread()
                        if self._stop: break
                        append_log(f"Sleeping {self.delay_ms/1000.0:.1f}s")
                        time.sleep(self.delay_ms/1000.0)
                else:
                    self._send_in_thread()

            elif self.mode == "bulk":
                if not self.targets:
                    raise RuntimeError("No targets for bulk")
                for t in self.targets:
                    if self._stop: break
                    url = f"https://www.messenger.com/t/{t}"
                    append_log(f"Opening {url}")
                    self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    self._send_in_thread()

            else:
                raise RuntimeError(f"Unknown mode: {self.mode}")

            append_log("Task finished")
        except Exception as e:
            append_log("ERROR: " + str(e))
            append_log(traceback.format_exc())
        finally:
            try:
                self._close()
            except:
                pass

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Messenger Sender (non-E2EE)", layout="wide")
st.markdown(
    """<style>
    body { background: radial-gradient(circle at 10% 10%, rgba(0,200,255,0.04), transparent 20%), radial-gradient(circle at 90% 90%, rgba(255,100,200,0.02), transparent 20%), #02020a; color:#e6f7ff; }
    .card { background: rgba(255,255,255,0.02); padding:12px; border-radius:10px; box-shadow: 0 6px 22px rgba(0,0,0,0.6); }
    .neon-title{ color:#00ffd1; text-shadow: 0 0 12px rgba(0,255,200,0.18); }
    textarea, input { background: rgba(255,255,255,0.02); color: #e6f7ff; border: 1px solid rgba(255,255,255,0.04); padding:8px; border-radius:6px; }
    </style>""",
    unsafe_allow_html=True
)

st.markdown("<h1 class='neon-title'>💬 Messenger Sender — Non-E2EE (cookie based)</h1>", unsafe_allow_html=True)

if 'logs' not in st.session_state: st.session_state['logs'] = []
if 'sent' not in st.session_state: st.session_state['sent'] = 0
if 'worker' not in st.session_state: st.session_state['worker'] = None
if 'thread_obj' not in st.session_state: st.session_state['thread_obj'] = None

left, right = st.columns([1,1])

with left:
    st.subheader("Inputs")
    cookie = st.text_area("🔑 Facebook cookie (paste full cookie string here)", height=130, help="Example: datr=...; fr=...; c_user=...; xs=...; sb=...")
    mode = st.selectbox("Mode", options=["single", "group", "bulk", "loop"], index=0, help="single: one thread; group: group thread; bulk: multiple targets; loop: keep sending repeatedly")
    if mode in ("single","group","loop"):
        target = st.text_input("Target thread ID / UID (e.g. 61564176744081)", help="Paste the messenger thread id or user id")
        targets = [target] if target else []
    else:
        targets_text = st.text_area("Targets (one ID per line)", height=120, help="For bulk: paste one thread id / uid per line")
        targets = [t.strip() for t in targets_text.splitlines() if t.strip()]

    delay_ms = st.number_input("Delay between cycles (ms)", value=3000, min_value=300, help="Delay used between message cycles (loop) or per message handling")
    maxsend = st.number_input("Max sends (0 = unlimited)", value=0, min_value=0)
    headless = st.checkbox("Headless (no browser window)", value=False)
    chrome_path = st.text_input("Optional CHROME_PATH (leave blank to use Playwright's bundled chromium)", placeholder="/usr/bin/google-chrome-stable")

with right:
    st.subheader("Message & Controls")
    messages_text = st.text_area("Messages (one per line)", height=240)
    messages = [m.strip() for m in messages_text.splitlines() if m.strip()]
    c1, c2 = st.columns(2)
    start = c1.button("🚀 Start")
    stop = c2.button("🛑 Stop")

    st.markdown("**Cookie helper (bookmarklet)** — click to copy. Create a bookmark and paste this as its URL. Open facebook.com and click the bookmark to copy cookie to clipboard.")
    if st.button("Copy cookie bookmarklet"):
        bm = "javascript:(()=>{try{navigator.clipboard.writeText(document.cookie);alert('Cookie copied');}catch(e){prompt('Copy cookie',document.cookie);}})()"
        st.code(bm, language='javascript')

st.markdown("---")
st.subheader("Live logs / console")
st.text_area("Logs", value="\n".join(st.session_state['logs']), height=360, key="logs_area", disabled=True)
st.metric("Sent", st.session_state['sent'])

# Start / Stop handling
if start:
    if not cookie or not targets or not messages:
        st.error("Please provide cookie, target(s) and at least one message.")
    else:
        if st.session_state.get('worker') is not None:
            st.warning("Worker already running. Stop it first.")
        else:
            worker = MessengerWorker(cookie=cookie, targets=targets, messages=messages, delay_ms=delay_ms, mode=mode, maxsend=maxsend, headless=headless, chrome_path=chrome_path or None)
            st.session_state['worker'] = worker
            def runner():
                append_log("Worker thread starting...")
                worker.run()
                append_log("Worker finished.")
                st.session_state['worker'] = None
            t = threading.Thread(target=runner, daemon=True)
            st.session_state['thread_obj'] = t
            t.start()
            st.success("Worker started — watch logs for progress.")

if stop:
    if st.session_state.get('worker'):
        st.session_state['worker'].stop()
        st.success("Stop requested.")
    else:
        st.info("No worker running.")
            
