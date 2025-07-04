import asyncio
import logging
import random
import os
import sys
from telethon import TelegramClient, events
import requests
from threading import Thread

class BotMonitor:
    def __init__(self, api_id, api_hash, control_bot_token, control_chat_id):
        self.api_id = api_id
        self.api_hash = api_hash
        self.control_bot_token = control_bot_token
        self.control_chat_id = control_chat_id
        self.clients = []
        self.is_running = False
        self.logs = []
        self.bot_tokens = []
        
    def add_log(self, message):
        self.logs.append(message)
        if len(self.logs) > 100:  # Keep last 100 logs
            self.logs.pop(0)
            
    async def event_handler(self, event):
        try:
            await event.get_chat()
            chatid = event.chat_id
            name = event.sender.username if event.sender.username else str(event.sender_id)
            self.add_log(f'New message from chat id: {str(chatid)}')

            if event.raw_text and len(event.raw_text.strip()) < 10:
                self.add_log(f'Message too short, skipping: "{event.raw_text.strip()}"')
                return

            if event.voice:
                self.add_log('Processing voice message...')
                urlll = f'https://api.telegram.org/bot{self.control_bot_token}/sendmessage?chat_id={self.control_chat_id}&text=VOICE FROM : @{name}'
                voice = await event.download_media(file='voice')
                urll = f'https://api.telegram.org/bot{self.control_bot_token}/sendvoice?chat_id={self.control_chat_id}'
                files = {'voice': open(voice, 'rb')}
                requests.post(urlll)
                requests.post(urll, files=files)
                self.add_log(f'Forwarded voice message from: @{name}')

            elif event.document:
                self.add_log('Processing document...')
                urlll = f'https://api.telegram.org/bot{self.control_bot_token}/sendmessage?chat_id={self.control_chat_id}&text=FILE FROM : @{name}'
                media = await event.download_media(file='file')
                urll = f'https://api.telegram.org/bot{self.control_bot_token}/senddocument?chat_id={self.control_chat_id}'
                files = {'document': open(media, 'rb')}
                requests.post(urlll)
                requests.post(urll, files=files)
                self.add_log(f'Forwarded document from: @{name}')

            elif event.media and hasattr(event.media, 'photo'):
                self.add_log('Processing photo...')
                urlll = f'https://api.telegram.org/bot{self.control_bot_token}/sendmessage?chat_id={self.control_chat_id}&text=PHOTO FROM : @{name}'
                photo = await event.download_media()
                urll = f'https://api.telegram.org/bot{self.control_bot_token}/sendphoto?chat_id={self.control_chat_id}'
                files = {'photo': open(photo, 'rb')}
                requests.post(urlll)
                requests.post(urll, files=files)
                self.add_log(f'Forwarded photo from: @{name}')

            elif event.raw_text in ['ㅤ', '.', '/start', 'Hashtag : ma9souda', 'ID Message:']:
                self.add_log('Ignored system message')
            else:
                text = event.raw_text
                cleaned_text = text.replace('#', '').replace('&', '')
                urll = f'https://api.telegram.org/bot{self.control_bot_token}/sendmessage?chat_id={self.control_chat_id}&text=FROM BOT : @{name}\n\n{cleaned_text}'
                requests.post(urll)
                self.add_log(f'Forwarded message from: @{name}')

        except Exception as e:
            self.add_log(f'Error: {str(e)}')

    async def start_bots(self):
        self.is_running = True
        self.add_log("Starting bot monitoring...")
        
        for token in self.bot_tokens:
            try:
                session_file = f'session_{token}.session'
                client = TelegramClient(session_file, self.api_id, self.api_hash)
                self.clients.append(client)
                await client.start(bot_token=token)
                client.add_event_handler(self.event_handler, events.NewMessage)
                self.add_log(f'Bot started with token: {token[:10]}...')
            except Exception as e:
                self.add_log(f'Failed to start bot: {str(e)}')
                continue

        self.add_log("All bots started successfully")
        while self.is_running:
            await asyncio.sleep(1)

    async def stop_bots(self):
        self.is_running = False
        self.add_log("Stopping all bots...")
        for client in self.clients:
            try:
                await client.disconnect()
            except:
                pass
        self.clients = []
        self.add_log("All bots stopped")

    def load_tokens(self, file_content):
        self.bot_tokens = [x.strip() for x in file_content.split('\n') if x.strip()]
        self.add_log(f'Loaded {len(self.bot_tokens)} bot tokens')
