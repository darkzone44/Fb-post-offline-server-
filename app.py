# app.py
import streamlit as st
import threading
import time
from typing import List, Dict
import traceback

# Playwright (sync)
from playwright.sync_api import sync_playwright, Browser, Page

# ---------------------------
# Utility functions
# ---------------------------
def parse_cookie_string(cookie_str: str) -> List[Dict]:
    """
    Convert "k=v; k2=v2" into list of cookie dicts usable by Playwright.
    Domain will be set to '.facebook.com' by default.
    """
    out = []
    for part in cookie_str.split(';'):
        p = part.strip()
        if not p:
            continue
        if '=' not in p:
            continue
        name, val = p.split('=', 1)
        out.append({'name': name.strip(), 'value': val.strip(), 'domain': '.facebook.com', 'path': '/'})
    return out

def _set_status(msg: str):
    st.session_state['status_lines'].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    # keep last 200 lines
    st.session_state['status_lines'] = st.session_state['status_lines'][-200:]

# ---------------------------
# Core automation worker
# ---------------------------
class MessengerWorker:
    def __init__(self, cookie: str, targets: List[str], messages: List[str], delay_ms: int, mode: str, maxsend: int, headless=False, chrome_executable: str = None):
        self.cookie = cookie
        self.targets = targets[:]  # list of thread IDs or UIDs
        self.messages = messages[:]
        self.delay_ms = max(300, int(delay_ms))
        self.mode = mode  # 'single', 'group', 'bulk', 'loop'
        self.maxsend = int(maxsend)
        self.headless = bool(headless)
        self.chrome_executable = chrome_executable
        self._stop = False
        self.sent = 0
        self._playwright = None
        self._browser = None
        self._page = None

    def stop(self):
        self._stop = True
        _set_status("Stop requested")

    def _open_browser(self):
        # Launch Playwright Chromium
        self._playwright = sync_playwright().start()
        launch_args = {"headless": self.headless, "args": ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage']}
        if self.chrome_executable:
            launch_args["executable_path"] = self.chrome_executable
        self._browser = self._playwright.chromium.launch(**launch_args)
        self._page = self._browser.new_page()

    def _close_browser(self):
        try:
            if self._page:
                self._page.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

    def _set_cookies(self):
        cookies = parse_cookie_string(self.cookie)
        if cookies:
            # go to facebook origin, then set cookies
            self._page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=30000)
            # Playwright expects cookies as list of dicts without domain starting dot on some installations, but .facebook.com is generally accepted
            try:
                self._page.context.add_cookies(cookies)
                _set_status(f"Set {len(cookies)} cookies")
            except Exception as e:
                _set_status(f"Failed to set cookies: {e}")
        else:
            _set_status("No cookies provided")

    def _wait_for_input_selector(self, page: Page, timeout_ms=10000):
        selectors = [
            'div[contenteditable="true"][role="combobox"]',
            'div[role="textbox"][contenteditable="true"]',
            'div[contenteditable="true"]',
            'textarea'
        ]
        for sel in selectors:
            try:
                page.wait_for_selector(sel, timeout=timeout_ms)
                return sel
            except Exception:
                continue
        return None

    def _send_in_current_thread(self, page: Page) -> None:
        sel = self._wait_for_input_selector(page, timeout_ms=8000)
        if not sel:
            raise RuntimeError("Message input not found on this thread page. Check login / UI changes.")
        for text in self.messages:
            if self._stop:
                return
            _set_status(f"Typing message: {text[:80]}")
            # Use evaluate to set contenteditable text then press Enter
            try:
                page.evaluate(
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
                            // fallback: try to set innerText
                            e.innerText = msg;
                        }
                        return true;
                    }""",
                    sel, text
                )
                page.keyboard.press("Enter")
            except Exception as e:
                _set_status(f"Send attempt error: {e}")
            # confirm attempt by short wait; the robust check is hard because Messenger DOM varies:
            wait_ms = 0
            while wait_ms < 3000 and not self._stop:
                time.sleep(0.3)
                wait_ms += 300
            self.sent += 1
            st.session_state['sent_count'] = self.sent
            if self.maxsend > 0 and self.sent >= self.maxsend:
                _set_status("Reached maxsend limit")
                return

    def run(self):
        try:
            _set_status("Launching browser...")
            self._open_browser()

            _set_status("Applying cookies and opening Messenger...")
            self._set_cookies()

            # Choose mode behavior
            if self.mode == 'single':
                target = self.targets[0]
                url = f"https://www.messenger.com/t/{target}"
                _set_status(f"Opening {url}")
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                self._send_in_current_thread(self._page)

            elif self.mode == 'group':
                # group thread id same as messenger thread
                target = self.targets[0]
                url = f"https://www.messenger.com/t/{target}"
                _set_status(f"Opening group thread {url}")
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                self._send_in_current_thread(self._page)

            elif self.mode == 'bulk':
                # iterate through targets
                for t in self.targets:
                    if self._stop: break
                    url = f"https://www.messenger.com/t/{t}"
                    _set_status(f"Opening target {t}")
                    self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    self._send_in_current_thread(self._page)

            elif self.mode == 'loop':
                target = self.targets[0]
                url = f"https://www.messenger.com/t/{target}"
                _set_status(f"Starting loop on {url}")
                # open once, then loop forever until stopped
                self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
                while not self._stop:
                    self._send_in_current_thread(self._page)
                    if self._stop:
                        break
                    # delay between cycles
                    sleep_secs = max(1, self.delay_ms / 1000.0)
                    _set_status(f"Sleeping {sleep_secs}s before next loop")
                    time.sleep(sleep_secs)
            else:
                raise RuntimeError("Unknown mode")
            _set_status("Task finished")
        except Exception as e:
            _set_status("ERROR: " + str(e))
            _set_status(traceback.format_exc())
        finally:
            try:
                self._close_browser()
            except:
                pass
            _set_status("Browser closed")

# ---------------------------
# Streamlit UI + control
# ---------------------------
st.set_page_config(page_title="E2EE Messenger Sender", layout="wide")
st.title("E2EE Messenger — Cookie-based sender (Use responsibly)")

if 'worker_thread' not in st.session_state: st.session_state['worker_thread'] = None
if 'worker_obj' not in st.session_state: st.session_state['worker_obj'] = None
if 'status_lines' not in st.session_state: st.session_state['status_lines'] = []
if 'sent_count' not in st.session_state: st.session_state['sent_count'] = 0

col1, col2 = st.columns([1,1])
with col1:
    st.subheader("Inputs (cookie, target, messages)")
    cookie = st.text_area("Facebook cookie (paste full cookie string)", height=120, key="cookie_box")
    st.markdown("**Target mode**")
    mode = st.selectbox("Mode", ["single", "group", "bulk", "loop"])
    if mode in ("single", "group", "loop"):
        target = st.text_input("Target thread ID / UID (e.g. 61564176744081)", key="target_input")
        targets = [target] if target else []
    else:
        targets_raw = st.text_area("Targets (one thread/UID per line)", height=120, key="targets_area")
        targets = [t.strip() for t in targets_raw.splitlines() if t.strip()]

    delay = st.number_input("Delay between messages (ms)", value=3000, min_value=300)
    maxsend = st.number_input("Max sends (0 = unlimited)", value=0, min_value=0)
    headless = st.checkbox("Headless (no browser window). For debugging uncheck.", value=False)
    chrome_path = st.text_input("Optional CHROME_PATH (leave blank to use Playwright bundled)", placeholder="/usr/bin/google-chrome-stable")

with col2:
    st.subheader("Message and controls")
    messages_raw = st.text_area("Messages (one per line)", height=220, key="messages_area")
    messages = [m.strip() for m in messages_raw.splitlines() if m.strip()]

    start_btn = st.button("Start")
    stop_btn = st.button("Stop")
    st.markdown("**Cookie helper (bookmarklet)** — click to copy. Create a bookmark in your browser and paste this as URL, open facebook.com and click the bookmark to copy cookies to clipboard.")
    if st.button("Copy cookie-bookmarklet"):
        code = "javascript:(()=>{try{navigator.clipboard.writeText(document.cookie);alert('Cookie copied');}catch(e){prompt('Copy cookie manually',document.cookie);}})()"
        st.experimental_set_query_params()  # no-op but ensures UI update
        st.write("Bookmarklet (copied to clipboard):")
        st.write(code)
        try:
            st.experimental_set_query_params(_bm="copied")  # just a marker
        except:
            pass

st.markdown("---")
st.subheader("Status / Logs")
st.text_area("Logs", value="\n".join(st.session_state['status_lines']), height=220, key="logs_area", disabled=True)
st.metric("Sent count", st.session_state['sent_count'])

# Handle start/stop
if start_btn:
    # simple validation
    if not cookie or not targets or not messages:
        st.error("Provide cookie, target(s) and at least one message.")
    else:
        if st.session_state['worker_thread'] and st.session_state['worker_thread'].is_alive():
            st.warning("A task is already running. Stop it first.")
        else:
            worker = MessengerWorker(cookie=cookie, targets=targets, messages=messages, delay_ms=delay, mode=mode, maxsend=maxsend, headless=headless, chrome_executable=chrome_path or None)
            st.session_state['worker_obj'] = worker
            def _runner():
                _set_status("Starting task...")
                worker.run()
            t = threading.Thread(target=_runner, daemon=True)
            st.session_state['worker_thread'] = t
            t.start()
            st.success("Worker started. Check logs for progress.")

if stop_btn:
    if st.session_state.get('worker_obj'):
        st.session_state['worker_obj'].stop()
        st.success("Stop requested.")
    else:
        st.info("No running worker object found.")
        
