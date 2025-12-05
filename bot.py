# bot.py - YOUR ACTUAL FB BOT CODE
import json
import logging

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Load config
with open('config.json') as f:
    config = json.load(f)

with open('fbstate.json') as f:
    fbstate = json.load(f)

print(f"Bot starting... Admin: {config['admin_id']}, Prefix: {config['prefix']}")
print(f"Thread ID: {config['thread_id']}")

# YOUR FB MESSENGER BOT CODE HERE
# Example loop:
while True:
    print("Bot running... Active in thread", config['thread_id'])
    # Your bot logic
    time.sleep(5)
