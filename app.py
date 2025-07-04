import streamlit as st
from streamlit.components.v1 import html
import asyncio
from bot_monitor import BotMonitor
import time
import threading
import os

# Custom CSS and JS
def inject_custom_css():
    st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
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
    </style>
    """, unsafe_allow_html=True)

    # Add some animations
    html("""
    <script>
    // Simple animation for buttons
    document.addEventListener('DOMContentLoaded', function() {
        const buttons = document.querySelectorAll('.stButton>button');
        buttons.forEach(button => {
            button.addEventListener('mouseover', function() {
                this.style.transform = 'scale(1.05)';
            });
            button.addEventListener('mouseout', function() {
                this.style.transform = 'scale(1)';
            });
        });
    });
    </script>
    """)

# Login system
def login():
    st.title("🔒 Bot Monitor Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "wolf" and password == "firas":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# Main application
def main_app():
    inject_custom_css()
    
    st.title("🤖 Telegram Bot Monitor")
    st.markdown("---")
    
    # Initialize bot monitor in session state
    if 'bot_monitor' not in st.session_state:
        st.session_state.bot_monitor = None
        st.session_state.monitor_thread = None
    
    # Configuration section
    with st.expander("⚙️ Configuration", expanded=True):
        col1, col2 = st.columns(2)
        api_id = col1.text_input("API ID", value="your_api_id")
        api_hash = col2.text_input("API Hash", value="your_api_hash", type="password")
        
        col1, col2 = st.columns(2)
        control_bot_token = col1.text_input("Control Bot Token", value="your_control_bot_token")
        control_chat_id = col2.text_input("Control Chat ID", value="your_control_chat_id")
        
        uploaded_file = st.file_uploader("📁 Upload Bot Tokens (txt file)", type=["txt"])
        
        if uploaded_file is not None:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.bot_monitor = BotMonitor(
                api_id, api_hash, control_bot_token, control_chat_id
            )
            st.session_state.bot_monitor.load_tokens(file_content)
            st.success(f"Loaded {len(st.session_state.bot_monitor.bot_tokens)} bot tokens")
    
    # Control buttons
    col1, col2 = st.columns(2)
    start_btn = col1.button("🚀 Start Monitoring", key="start")
    stop_btn = col2.button("🛑 Stop Monitoring", key="stop")
    
    if start_btn and st.session_state.bot_monitor:
        if not st.session_state.bot_monitor.is_running:
            def run_async():
                asyncio.run(st.session_state.bot_monitor.start_bots())
            
            st.session_state.monitor_thread = threading.Thread(target=run_async)
            st.session_state.monitor_thread.start()
            st.success("Monitoring started!")
        else:
            st.warning("Monitoring is already running")
    
    if stop_btn and st.session_state.bot_monitor:
        if st.session_state.bot_monitor.is_running:
            asyncio.run(st.session_state.bot_monitor.stop_bots())
            st.success("Monitoring stopped!")
        else:
            st.warning("Monitoring is not running")
    
    # Log display
    st.markdown("## 📜 Activity Log")
    log_container = st.empty()
    
    # Update logs in real-time
    while True:
        if 'bot_monitor' in st.session_state and st.session_state.bot_monitor:
            logs = st.session_state.bot_monitor.logs
            if logs:
                log_html = "<div class='log-table'>"
                for log in logs[-20:]:  # Show last 20 logs
                    log_class = "info-log"
                    if "Success" in log or "Forwarded" in log:
                        log_class = "success-log"
                    elif "Error" in log or "Failed" in log:
                        log_class = "error-log"
                    log_html += f"<div class='log-entry {log_class}'>{log}</div>"
                log_html += "</div>"
                log_container.markdown(log_html, unsafe_allow_html=True)
        time.sleep(1)

# App flow
def app():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if st.session_state.logged_in:
        main_app()
    else:
        login()

if __name__ == "__main__":
    app()
