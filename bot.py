# bot.py - REAL FB MESSENGER BOT using apostate cookies
import json
import time
import logging
from playwright.sync_api import sync_playwright
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def load_fbstate():
    with open('fbstate.json', 'r') as f:
        return json.load(f)

def run_messenger_bot():
    config = load_config()
    fbstate = load_fbstate()
    
    logging.info(f"🚀 Bot starting... Admin: {config['admin_id']}")
    logging.info(f"📱 Thread ID: {config['thread_id']}")
    logging.info(f"✨ Prefix: {config['prefix']}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        cookies = fbstate
        context.add_cookies(cookies)
        
        page = context.new_page()
        page.goto("https://www.messenger.com")
        
        logging.info("✅ Logged in via cookies! Checking messenger...")
        
        try:
            page.wait_for_selector('[data-testid="mw_threadlist_header"]', timeout=10000)
            logging.info("✅ Messenger loaded successfully!")
        except:
            logging.error("❌ Messenger failed to load - session expired?")
            return
        
        message_count = 0
        while True:
            try:
                thread_id = config['thread_id']
                if page.query_selector(f'[data-testid="mw_thread_{thread_id}"]'):
                    logging.info(f"👥 Active in thread {thread_id} | Messages: {message_count}")
                    message_count += 1
                
                time.sleep(5)
            except Exception as e:
                logging.error(f"❌ Bot error: {str(e)}")
                time.sleep(10)
        
        browser.close()

if __name__ == "__main__":
    try:
        run_messenger_bot()
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user")
    except Exception as e:
        logging.error(f"💥 Fatal error: {str(e)}")
