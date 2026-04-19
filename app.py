from flask import Flask, request, render_template_string, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from ceasar_cypher import encrypt, decrypt, rot13, vigenere
from database import init_db, create_user, verify_user, get_user_by_id, create_room, get_all_rooms, get_room, save_message, get_messages
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "classified_key_7")
socketio = SocketIO(app, cors_allowed_origins="*")

init_db()

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>CLASSIFIED CHANNEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --green: #00ff41;
            --green-dim: #005f1a;
            --green-glow: rgba(0,255,65,0.1);
            --red: #ff0000;
            --bg: #000;
            --text: #00ff41;
        }

        html, body {
            height: 100%;
            background: var(--bg);
            font-family: 'Share Tech Mono', monospace;
            color: var(--text);
        }

        /* ── SCANLINE ── */
        .scanline {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0,0,0,0.03) 0px,
                rgba(0,0,0,0.03) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 999;
        }

        /* ── AUTH SCREEN ── */
        .auth-screen {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .auth-box {
            width: 100%;
            max-width: 400px;
            border: 1px solid var(--green);
            box-shadow: 0 0 30px var(--green), inset 0 0 30px var(--green-glow);
            padding: 30px 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .auth-title {
            text-align: center;
            font-size: 1.3rem;
            letter-spacing: 4px;
            text-shadow: 0 0 15px var(--green);
            margin-bottom: 8px;
        }

        .auth-subtitle {
            text-align: center;
            font-size: 0.75rem;
            color: var(--green-dim);
            letter-spacing: 3px;
        }

        .auth-tabs {
            display: flex;
            gap: 8px;
        }

        .auth-tab {
            flex: 1;
            padding: 10px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.85rem;
            letter-spacing: 2px;
            cursor: pointer;
            border: 1px solid var(--green-dim);
            background: var(--bg);
            color: var(--green-dim);
        }

        .auth-tab.active {
            border-color: var(--green);
            color: var(--green);
            background: var(--green-glow);
            text-shadow: 0 0 8px var(--green);
        }

        .auth-input {
            background: var(--bg);
            border: 1px solid var(--green);
            color: var(--green);
            font-family: 'Share Tech Mono', monospace;
            padding: 12px;
            font-size: 1rem;
            width: 100%;
            outline: none;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .auth-input::placeholder { color: var(--green-dim); }

        .auth-btn {
            background: var(--green);
            color: var(--bg);
            border: none;
            padding: 14px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: bold;
            font-size: 1rem;
            letter-spacing: 3px;
            cursor: pointer;
            width: 100%;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .auth-error {
            color: var(--red);
            font-size: 0.85rem;
            letter-spacing: 2px;
            text-align: center;
            border: 1px solid var(--red);
            padding: 8px;
        }

        /* ── MAIN APP LAYOUT ── */
        .app {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* ── SIDEBAR ── */
        .sidebar {
            width: 220px;
            min-width: 220px;
            border-right: 1px solid var(--green);
            display: flex;
            flex-direction: column;
            background: #000;
            transition: transform 0.3s ease;
        }

        .sidebar-header {
            padding: 14px 12px;
            border-bottom: 1px solid var(--green);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .sidebar-title {
            font-size: 0.8rem;
            letter-spacing: 3px;
            color: var(--green);
            text-shadow: 0 0 8px var(--green);
        }

        .user-badge {
            font-size: 0.7rem;
            color: var(--green-dim);
            letter-spacing: 2px;
        }

        .new-room-btn {
            margin: 10px;
            padding: 10px;
            background: var(--green-glow);
            border: 1px solid var(--green);
            color: var(--green);
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.8rem;
            letter-spacing: 2px;
            cursor: pointer;
            text-align: center;
        }

        .rooms-list {
            flex: 1;
            overflow-y: auto;
            padding: 4px 0;
        }

        .room-item {
            padding: 12px;
            font-size: 0.85rem;
            letter-spacing: 1px;
            cursor: pointer;
            border-left: 3px solid transparent;
            color: var(--green-dim);
            border-bottom: 1px solid rgba(0,255,65,0.05);
        }

        .room-item:hover {
            background: var(--green-glow);
            color: var(--green);
        }

        .room-item.active {
            border-left-color: var(--green);
            color: var(--green);
            background: var(--green-glow);
            text-shadow: 0 0 6px var(--green);
        }

        .room-name {
            font-size: 0.85rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .room-meta {
            font-size: 0.65rem;
            color: var(--green-dim);
            margin-top: 2px;
            letter-spacing: 1px;
        }

        .sidebar-footer {
            padding: 10px;
            border-top: 1px solid var(--green);
        }

        .logout-btn {
            width: 100%;
            padding: 8px;
            background: transparent;
            border: 1px solid var(--green-dim);
            color: var(--green-dim);
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.75rem;
            letter-spacing: 2px;
            cursor: pointer;
        }

        .logout-btn:hover {
            border-color: var(--red);
            color: var(--red);
        }

        /* ── CHAT AREA ── */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--green);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .chat-header-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .menu-btn {
            display: none;
            background: transparent;
            border: 1px solid var(--green);
            color: var(--green);
            font-family: 'Share Tech Mono', monospace;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 1rem;
        }

        .room-title {
            font-size: 1rem;
            letter-spacing: 3px;
            text-shadow: 0 0 8px var(--green);
        }

        .online-count {
            font-size: 0.7rem;
            color: var(--green-dim);
            letter-spacing: 2px;
        }

        .panic-banner {
            text-align: center;
            color: var(--red);
            font-size: 0.8rem;
            letter-spacing: 2px;
            padding: 6px;
            border-bottom: 1px solid var(--red);
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .messages::-webkit-scrollbar { width: 4px; }
        .messages::-webkit-scrollbar-track { background: #000; }
        .messages::-webkit-scrollbar-thumb { background: var(--green); }

        .msg-row { display: flex; flex-direction: column; gap: 3px; }
        .msg-row.mine { align-items: flex-end; }
        .msg-row.theirs { align-items: flex-start; }
        .msg-row.system { align-items: center; }

        .msg-meta {
            font-size: 0.7rem;
            color: var(--green-dim);
            letter-spacing: 1px;
            padding: 0 8px;
        }

        .msg-bubble {
            max-width: 80%;
            padding: 10px 14px;
            font-size: 0.95rem;
            line-height: 1.5;
            word-break: break-word;
        }

        .msg-bubble.mine {
            background: var(--green-glow);
            border: 1px solid var(--green);
            color: var(--green);
        }

        .msg-bubble.theirs {
            background: rgba(0,255,65,0.03);
            border: 1px solid var(--green-dim);
            color: #00cc33;
        }

        .msg-bubble.system {
            border: 1px dashed var(--green-dim);
            color: var(--green-dim);
            font-size: 0.8rem;
            letter-spacing: 2px;
            text-align: center;
        }

        .msg-bubble.encrypted {
            color: var(--red) !important;
            border-color: var(--red) !important;
            text-shadow: 0 0 6px var(--red);
        }

        .no-room {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--green-dim);
            gap: 16px;
            font-size: 0.9rem;
            letter-spacing: 3px;
        }

        .no-room-icon {
            font-size: 3rem;
            opacity: 0.3;
        }

        /* ── CONTROLS ── */
        .controls {
            border-top: 1px solid var(--green);
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .section-label {
            font-size: 0.65rem;
            color: var(--green-dim);
            letter-spacing: 3px;
        }

        .btn-row {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .pill-btn {
            flex: 1;
            min-width: 60px;
            padding: 10px 4px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.75rem;
            letter-spacing: 1px;
            cursor: pointer;
            border: 1px solid var(--green-dim);
            background: var(--bg);
            color: var(--green-dim);
            -webkit-appearance: none;
            border-radius: 0;
        }

        .pill-btn.active {
            border-color: var(--green);
            color: var(--green);
            background: var(--green-glow);
            text-shadow: 0 0 6px var(--green);
        }

        .param-row {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.8rem;
            color: var(--green-dim);
            letter-spacing: 2px;
        }

        .param-row input {
            background: var(--bg);
            border: 1px solid var(--green);
            color: var(--green);
            font-family: 'Share Tech Mono', monospace;
            padding: 6px 8px;
            font-size: 0.95rem;
            outline: none;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .param-row input[type="number"] { width: 65px; text-align: center; }
        .param-row input[type="text"] { width: 120px; text-align: center; }

        .input-row {
            display: flex;
            gap: 8px;
        }

        .msg-input {
            flex: 1;
            background: var(--bg);
            border: 1px solid var(--green);
            color: var(--green);
            font-family: 'Share Tech Mono', monospace;
            padding: 12px 10px;
            font-size: 1rem;
            outline: none;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .msg-input::placeholder { color: var(--green-dim); }

        .send-btn {
            background: var(--green);
            color: var(--bg);
            border: none;
            padding: 12px 16px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: bold;
            font-size: 0.9rem;
            letter-spacing: 1px;
            cursor: pointer;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .send-btn:active { background: #00cc33; }

        /* ── MODAL ── */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.85);
            z-index: 500;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .modal-overlay.open { display: flex; }

        .modal {
            width: 100%;
            max-width: 380px;
            border: 1px solid var(--green);
            box-shadow: 0 0 30px var(--green);
            background: #000;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .modal-title {
            font-size: 1rem;
            letter-spacing: 3px;
            text-shadow: 0 0 8px var(--green);
            text-align: center;
        }

        .modal input {
            background: var(--bg);
            border: 1px solid var(--green);
            color: var(--green);
            font-family: 'Share Tech Mono', monospace;
            padding: 10px;
            font-size: 1rem;
            width: 100%;
            outline: none;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .modal input::placeholder { color: var(--green-dim); }

        .modal-btns {
            display: flex;
            gap: 8px;
        }

        .modal-confirm {
            flex: 1;
            background: var(--green);
            color: var(--bg);
            border: none;
            padding: 12px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: bold;
            font-size: 0.9rem;
            cursor: pointer;
        }

        .modal-cancel {
            flex: 1;
            background: transparent;
            color: var(--green-dim);
            border: 1px solid var(--green-dim);
            padding: 12px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.9rem;
            cursor: pointer;
        }

        /* ── MOBILE ── */
        @media (max-width: 600px) {
            .sidebar {
                position: fixed;
                top: 0; left: 0;
                height: 100%;
                z-index: 200;
                transform: translateX(-100%);
            }

            .sidebar.open {
                transform: translateX(0);
            }

            .menu-btn { display: block; }

            .sidebar-overlay {
                display: none;
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 199;
            }

            .sidebar-overlay.open { display: block; }
        }
    </style>
</head>
<body>
<div class="scanline"></div>

{% if not logged_in %}
<!-- AUTH SCREEN -->
<div class="auth-screen">
    <div class="auth-box">
        <div class="auth-title">[ CLASSIFIED CHANNEL 7 ]</div>
        <div class="auth-subtitle">SECURE TRANSMISSION NETWORK</div>

        <div class="auth-tabs">
            <button class="auth-tab active" id="loginTab" onclick="switchTab('login')">LOGIN</button>
            <button class="auth-tab" id="registerTab" onclick="switchTab('register')">REGISTER</button>
        </div>

        {% if error %}
        <div class="auth-error">⚠ {{ error }}</div>
        {% endif %}

        <form method="POST" id="authForm">
            <input type="hidden" name="auth_action" id="authAction" value="login">
            <div style="display:flex;flex-direction:column;gap:10px;">
                <input class="auth-input" type="text" name="username" placeholder="AGENT CODENAME" autocomplete="off" required>
                <input class="auth-input" type="password" name="password" placeholder="ACCESS CODE" required>
                <button class="auth-btn" type="submit">AUTHENTICATE</button>
            </div>
        </form>
    </div>
</div>

<script>
function switchTab(tab) {
    document.getElementById('authAction').value = tab;
    document.getElementById('loginTab').classList.toggle('active', tab === 'login');
    document.getElementById('registerTab').classList.toggle('active', tab === 'register');
    document.querySelector('.auth-btn').textContent = tab === 'login' ? 'AUTHENTICATE' : 'ENLIST';
}
</script>

{% else %}
<!-- MAIN APP -->
<div class="app">
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="closeSidebar()"></div>

    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-title">[ CHANNELS ]</div>
            <div class="user-badge">▶ {{ username }}</div>
        </div>

        <button class="new-room-btn" onclick="openNewRoomModal()">+ NEW CHANNEL</button>

        <div class="rooms-list">
            {% for room in rooms %}
            <div class="room-item {% if current_room and current_room.id == room.id %}active{% endif %}"
                 onclick="joinRoom({{ room.id }}, '{{ room.name }}')">
                <div class="room-name"># {{ room.name }}</div>
                <div class="room-meta">BY {{ room.creator or 'UNKNOWN' }}</div>
            </div>
            {% endfor %}
        </div>

        <div class="sidebar-footer">
            <form method="POST">
                <input type="hidden" name="auth_action" value="logout">
                <button class="logout-btn" type="submit">⏻ DISCONNECT</button>
            </form>
        </div>
    </div>

    <div class="chat-area">
        {% if current_room %}
        <div class="chat-header">
            <div class="chat-header-left">
                <button class="menu-btn" onclick="openSidebar()">☰</button>
                <div class="room-title"># {{ current_room.name }}</div>
            </div>
            <div class="online-count" id="onlineCount">● CONNECTING</div>
        </div>

        {% if panic %}
        <div class="pan