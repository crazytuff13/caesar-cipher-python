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

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>CLASSIFIED CHANNEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        :root { --green: #00ff41; --green-dim: #005f1a; --green-glow: rgba(0,255,65,0.1); --red: #ff0000; --bg: #000; }
        html, body { height: 100%; background: var(--bg); font-family: 'Share Tech Mono', monospace; color: var(--green); }
        .scanline { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: repeating-linear-gradient(0deg, rgba(0,0,0,0.03) 0px, rgba(0,0,0,0.03) 1px, transparent 1px, transparent 2px); pointer-events: none; z-index: 999; }
        .auth-screen { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }
        .auth-box { width: 100%; max-width: 400px; border: 1px solid var(--green); box-shadow: 0 0 30px var(--green), inset 0 0 30px var(--green-glow); padding: 30px 24px; display: flex; flex-direction: column; gap: 16px; }
        .auth-title { text-align: center; font-size: 1.3rem; letter-spacing: 4px; text-shadow: 0 0 15px var(--green); }
        .auth-subtitle { text-align: center; font-size: 0.75rem; color: var(--green-dim); letter-spacing: 3px; }
        .auth-tabs { display: flex; gap: 8px; }
        .auth-tab { flex: 1; padding: 10px; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem; letter-spacing: 2px; cursor: pointer; border: 1px solid var(--green-dim); background: var(--bg); color: var(--green-dim); }
        .auth-tab.active { border-color: var(--green); color: var(--green); background: var(--green-glow); text-shadow: 0 0 8px var(--green); }
        .auth-input { background: var(--bg); border: 1px solid var(--green); color: var(--green); font-family: 'Share Tech Mono', monospace; padding: 12px; font-size: 1rem; width: 100%; outline: none; -webkit-appearance: none; border-radius: 0; }
        .auth-input::placeholder { color: var(--green-dim); }
        .auth-btn { background: var(--green); color: var(--bg); border: none; padding: 14px; font-family: 'Share Tech Mono', monospace; font-weight: bold; font-size: 1rem; letter-spacing: 3px; cursor: pointer; width: 100%; -webkit-appearance: none; border-radius: 0; }
        .auth-error { color: var(--red); font-size: 0.85rem; letter-spacing: 2px; text-align: center; border: 1px solid var(--red); padding: 8px; }
        .app { display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 220px; min-width: 220px; border-right: 1px solid var(--green); display: flex; flex-direction: column; background: #000; transition: transform 0.3s ease; }
        .sidebar-header { padding: 14px 12px; border-bottom: 1px solid var(--green); display: flex; flex-direction: column; gap: 4px; }
        .sidebar-title { font-size: 0.8rem; letter-spacing: 3px; color: var(--green); text-shadow: 0 0 8px var(--green); }
        .user-badge { font-size: 0.7rem; color: var(--green-dim); letter-spacing: 2px; }
        .new-room-btn { margin: 10px; padding: 10px; background: var(--green-glow); border: 1px solid var(--green); color: var(--green); font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; letter-spacing: 2px; cursor: pointer; text-align: center; }
        .rooms-list { flex: 1; overflow-y: auto; padding: 4px 0; }
        .room-item { padding: 12px; font-size: 0.85rem; cursor: pointer; border-left: 3px solid transparent; color: var(--green-dim); border-bottom: 1px solid rgba(0,255,65,0.05); }
        .room-item:hover { background: var(--green-glow); color: var(--green); }
        .room-item.active { border-left-color: var(--green); color: var(--green); background: var(--green-glow); }
        .room-name { font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .room-meta { font-size: 0.65rem; color: var(--green-dim); margin-top: 2px; }
        .sidebar-footer { padding: 10px; border-top: 1px solid var(--green); }
        .logout-btn { width: 100%; padding: 8px; background: transparent; border: 1px solid var(--green-dim); color: var(--green-dim); font-family: 'Share Tech Mono', monospace; font-size: 0.75rem; letter-spacing: 2px; cursor: pointer; }
        .logout-btn:hover { border-color: var(--red); color: var(--red); }
        .chat-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .chat-header { padding: 12px 16px; border-bottom: 1px solid var(--green); display: flex; align-items: center; justify-content: space-between; }
        .chat-header-left { display: flex; align-items: center; gap: 10px; }
        .menu-btn { display: none; background: transparent; border: 1px solid var(--green); color: var(--green); font-family: 'Share Tech Mono', monospace; padding: 6px 10px; cursor: pointer; font-size: 1rem; }
        .room-title { font-size: 1rem; letter-spacing: 3px; text-shadow: 0 0 8px var(--green); }
        .refresh-btn { font-size: 0.75rem; color: var(--green); letter-spacing: 2px; cursor: pointer; border: 1px solid var(--green-dim); padding: 6px 12px; background: transparent; font-family: 'Share Tech Mono', monospace; }
        .refresh-btn:hover { border-color: var(--green); background: var(--green-glow); }
        .panic-banner { text-align: center; color: var(--red); font-size: 0.8rem; letter-spacing: 2px; padding: 6px; border-bottom: 1px solid var(--red); animation: blink 1s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
        .messages::-webkit-scrollbar { width: 4px; }
        .messages::-webkit-scrollbar-thumb { background: var(--green); }
        .msg-row { display: flex; flex-direction: column; gap: 3px; }
        .msg-row.mine { align-items: flex-end; }
        .msg-row.theirs { align-items: flex-start; }
        .msg-row.system { align-items: center; }
        .msg-meta { font-size: 0.7rem; color: var(--green-dim); letter-spacing: 1px; padding: 0 8px; }
        .msg-bubble { max-width: 80%; padding: 10px 14px; font-size: 0.95rem; line-height: 1.5; word-break: break-word; }
        .msg-bubble.mine { background: var(--green-glow); border: 1px solid var(--green); color: var(--green); }
        .msg-bubble.theirs { background: rgba(0,255,65,0.03); border: 1px solid var(--green-dim); color: #00cc33; }
        .msg-bubble.system { border: 1px dashed var(--green-dim); color: var(--green-dim); font-size: 0.8rem; letter-spacing: 2px; text-align: center; }
        .msg-bubble.encrypted { color: var(--red) !important; border-color: var(--red) !important; text-shadow: 0 0 6px var(--red); }
        .no-room { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--green-dim); gap: 16px; font-size: 0.9rem; letter-spacing: 3px; }
        .no-room-icon { font-size: 3rem; opacity: 0.3; }
        .controls { border-top: 1px solid var(--green); padding: 10px 12px; display: flex; flex-direction: column; gap: 10px; }
        .control-row { display: flex; gap: 8px; }
        .ctrl-btn { flex: 1; padding: 12px 4px; font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; letter-spacing: 1px; cursor: pointer; border: 1px solid var(--green-dim); background: var(--bg); color: var(--green-dim); -webkit-appearance: none; border-radius: 0; }
        .ctrl-btn.active { border-color: var(--green); color: var(--green); background: var(--green-glow); text-shadow: 0 0 6px var(--green); }
        .ctrl-btn.locked { border-color: var(--red); color: var(--red); background: rgba(255,0,0,0.1); text-shadow: 0 0 6px var(--red); }
        .input-row { display: flex; gap: 8px; }
        .msg-input { flex: 1; background: var(--bg); border: 1px solid var(--green); color: var(--green); font-family: 'Share Tech Mono', monospace; padding: 12px 10px; font-size: 1rem; outline: none; -webkit-appearance: none; border-radius: 0; }
        .msg-input::placeholder { color: var(--green-dim); }
        .send-btn { background: var(--green); color: var(--bg); border: none; padding: 12px 16px; font-family: 'Share Tech Mono', monospace; font-weight: bold; font-size: 0.9rem; cursor: pointer; -webkit-appearance: none; border-radius: 0; }
        .send-btn:active { background: #00cc33; }
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 500; align-items: center; justify-content: center; padding: 20px; }
        .modal-overlay.open { display: flex; }
        .modal { width: 100%; max-width: 380px; border: 1px solid var(--green); box-shadow: 0 0 30px var(--green); background: #000; padding: 24px; display: flex; flex-direction: column; gap: 14px; }
        .modal-title { font-size: 1rem; letter-spacing: 3px; text-shadow: 0 0 8px var(--green); text-align: center; }
        .modal input { background: var(--bg); border: 1px solid var(--green); color: var(--green); font-family: 'Share Tech Mono', monospace; padding: 10px; font-size: 1rem; width: 100%; outline: none; -webkit-appearance: none; border-radius: 0; }
        .modal input::placeholder { color: var(--green-dim); }
        .modal-btns { display: flex; gap: 8px; }
        .modal-confirm { flex: 1; background: var(--green); color: var(--bg); border: none; padding: 12px; font-family: 'Share Tech Mono', monospace; font-weight: bold; font-size: 0.9rem; cursor: pointer; }
        .modal-cancel { flex: 1; background: transparent; color: var(--green-dim); border: 1px solid var(--green-dim); padding: 12px; font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; cursor: pointer; }
        .cipher-options { display: flex; flex-direction: column; gap: 8px; }
        .cipher-option { padding: 14px; font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; letter-spacing: 2px; cursor: pointer; border: 1px solid var(--green-dim); background: var(--bg); color: var(--green-dim); text-align: center; }
        .cipher-option:hover { border-color: var(--green); color: var(--green); background: var(--green-glow); }
        .cipher-option.active { border-color: var(--green); color: var(--green); background: var(--green-glow); text-shadow: 0 0 6px var(--green); }
        .keyword-input { background: var(--bg); border: 1px solid var(--green); color: var(--green); font-family: 'Share Tech Mono', monospace; padding: 10px; font-size: 1rem; width: 100%; outline: none; -webkit-appearance: none; border-radius: 0; margin-top: 4px; }
        .keyword-input::placeholder { color: var(--green-dim); }
        @media (max-width: 600px) {
            .sidebar { position: fixed; top: 0; left: 0; height: 100%; z-index: 200; transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .menu-btn { display: block; }
            .sidebar-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 199; }
            .sidebar-overlay.open { display: block; }
        }
    </style>
</head>
<body>
<div class="scanline"></div>

{% if not logged_in %}
<div class="auth-screen">
    <div class="auth-box">
        <div class="auth-title">[ CLASSIFIED CHANNEL 7 ]</div>
        <div class="auth-subtitle">SECURE TRANSMISSION NETWORK</div>
        <div class="auth-tabs">
            <button class="auth-tab active" id="loginTab" onclick="switchTab('login')">LOGIN</button>
            <button class="auth-tab" id="registerTab" onclick="switchTab('register')">REGISTER</button>
        </div>
        {% if error %}<div class="auth-error">WARNING: {{ error }}</div>{% endif %}
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
<div class="app">
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="closeSidebar()"></div>
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-title">[ CHANNELS ]</div>
            <div class="user-badge">AGENT: {{ username }}</div>
        </div>
        <button class="new-room-btn" onclick="openNewRoomModal()">+ NEW CHANNEL</button>
        <div class="rooms-list">
            {% for room in rooms %}
            <div class="room-item {% if current_room and current_room.id == room.id %}active{% endif %}" onclick="joinRoom({{ room.id }})">
                <div class="room-name"># {{ room.name }}</div>
                <div class="room-meta">BY {{ room.creator or 'UNKNOWN' }}</div>
            </div>
            {% endfor %}
        </div>
        <div class="sidebar-footer">
            <form method="POST">
                <input type="hidden" name="auth_action" value="logout">
                <button class="logout-btn" type="submit">DISCONNECT</button>
            </form>
        </div>
    </div>

    <div class="chat-area">
        {% if current_room %}
        <div class="chat-header">
            <div class="chat-header-left">
                <button class="menu-btn" onclick="openSidebar()">CHANNELS</button>
                <div class="room-title"># {{ current_room.name }}</div>
            </div>
            <button class="refresh-btn" onclick="location.reload()">⟳ REFRESH</button>
        </div>
        {% if encrypted_mode %}
        <div class="panic-banner">🔒 ENCRYPTED MODE ACTIVE</div>
        {% endif %}
        <div class="messages" id="messages">
            {% for msg in messages %}
            <div class="msg-row {% if msg.username == username %}mine{% elif msg.username == 'SYSTEM' %}system{% else %}theirs{% endif %}">
                {% if msg.username != 'SYSTEM' %}<div class="msg-meta">{{ msg.username }} - {{ msg.created_at }}</div>{% endif %}
                <div class="msg-bubble {% if msg.username == username %}mine{% elif msg.username == 'SYSTEM' %}system{% else %}theirs{% endif %} {% if msg.is_encrypted %}encrypted{% endif %}">{{ msg.content }}</div>
            </div>
            {% endfor %}
        </div>
        <div class="controls">
            <div class="control-row">
                <button class="ctrl-btn active" id="cipherBtn" onclick="openCipherModal()">🔐 {{ cipher|upper }}</button>
                <button class="ctrl-btn {% if encrypted_mode %}locked{% endif %}" id="lockBtn" onclick="toggleLock()">{% if encrypted_mode %}🔒 ENCRYPTED{% else %}🔓 PLAIN{% endif %}</button>
                <button class="ctrl-btn {% if mode == 'ai' %}active{% endif %}" id="aiBtn" onclick="toggleAI()">🤖 ASK HQ</button>
            </div>
            <form method="POST" action="/send_message" id="msgForm">
                <input type="hidden" name="room_id" value="{{ current_room.id }}">
                <input type="hidden" name="mode" id="modeInput" value="{{ mode }}">
                <input type="hidden" name="cipher" id="cipherInput" value="{{ cipher }}">
                <input type="hidden" name="shift" id="shiftInput" value="{{ shift }}">
                <input type="hidden" name="keyword" id="keywordInput" value="{{ keyword }}">
                <input type="hidden" name="encrypted_mode" id="encryptedModeInput" value="{{ 'true' if encrypted_mode else 'false' }}">
                <div class="input-row">
                    <input class="msg-input" type="text" name="message" id="msgInput" placeholder="ENTER TRANSMISSION..." autocomplete="off">
                    <button class="send-btn" type="submit">SEND</button>
                </div>
            </form>
        </div>
        {% else %}
        <button class="menu-btn" style="display:block;margin:12px;" onclick="openSidebar()">CHANNELS</button>
        <div class="no-room">
            <div class="no-room-icon">X</div>
            <div>SELECT A CHANNEL</div>
            <div style="font-size:0.75rem;">OR CREATE A NEW ONE</div>
        </div>
        {% endif %}
    </div>
</div>

<!-- NEW ROOM MODAL -->
<div class="modal-overlay" id="newRoomModal">
    <div class="modal">
        <div class="modal-title">[ NEW CHANNEL ]</div>
        <form method="POST" action="/create_room_form">
            <input type="text" name="name" id="newRoomName" placeholder="CHANNEL CODENAME" autocomplete="off" maxlength="30">
            <div class="modal-btns" style="margin-top:14px;">
                <button class="modal-cancel" type="button" onclick="closeNewRoomModal()">CANCEL</button>
                <button class="modal-confirm" type="submit">CREATE</button>
            </div>
        </form>
    </div>
</div>

<!-- CIPHER MODAL -->
<div class="modal-overlay" id="cipherModal">
    <div class="modal">
        <div class="modal-title">[ SELECT CIPHER ]</div>
        <div class="cipher-options">
            <button class="cipher-option {% if cipher == 'caesar' %}active{% endif %}" onclick="selectCipher('caesar')">CAESAR — NUMBER SHIFT</button>
            <button class="cipher-option {% if cipher == 'rot13' %}active{% endif %}" onclick="selectCipher('rot13')">ROT13 — FIXED SHIFT 13</button>
            <button class="cipher-option {% if cipher == 'vigenere' %}active{% endif %}" onclick="selectCipher('vigenere')">VIGENERE — KEYWORD</button>
        </div>
        <div id="shiftSection" style="display:{% if cipher == 'caesar' %}block{% else %}none{% endif %};">
            <div style="font-size:0.75rem;color:var(--green-dim);letter-spacing:2px;margin-bottom:6px;">SHIFT (1-25):</div>
            <input class="keyword-input" type="number" id="shiftPicker" min="1" max="25" value="{{ shift }}">
        </div>
        <div id="keywordSection" style="display:{% if cipher == 'vigenere' %}block{% else %}none{% endif %};">
            <div style="font-size:0.75rem;color:var(--green-dim);letter-spacing:2px;margin-bottom:6px;">KEYWORD:</div>
            <input class="keyword-input" type="text" id="keywordPicker" maxlength="20" placeholder="ENTER KEYWORD" value="{{ keyword }}">
        </div>
        <button class="modal-confirm" onclick="closeCipherModal()">CONFIRM</button>
    </div>
</div>

<script>
    let currentMode = "{{ mode }}";
    let currentCipher = "{{ cipher }}";
    let currentShift = {{ shift }};
    let currentKeyword = "{{ keyword }}";
    let encryptedMode = {{ 'true' if encrypted_mode else 'false' }};

    function toggleLock() {
        encryptedMode = !encryptedMode;
        document.getElementById('encryptedModeInput').value = encryptedMode ? 'true' : 'false';
        const btn = document.getElementById('lockBtn');
        if (encryptedMode) {
            btn.textContent = '🔒 ENCRYPTED';
            btn.classList.add('locked');
            btn.classList.remove('active');
        } else {
            btn.textContent = '🔓 PLAIN';
            btn.classList.remove('locked');
        }
    }

    function toggleAI() {
        if (currentMode === 'ai') {
            currentMode = 'plain';
            document.getElementById('aiBtn').classList.remove('active');
        } else {
            currentMode = 'ai';
            document.getElementById('aiBtn').classList.add('active');
        }
        document.getElementById('modeInput').value = currentMode;
    }

    function openCipherModal() { document.getElementById('cipherModal').classList.add('open'); }
    function closeCipherModal() {
        currentShift = parseInt(document.getElementById('shiftPicker').value) || 3;
        currentKeyword = document.getElementById('keywordPicker').value || 'KEY';
        document.getElementById('shiftInput').value = currentShift;
        document.getElementById('keywordInput').value = currentKeyword;
        document.getElementById('cipherInput').value = currentCipher;
        document.getElementById('cipherBtn').textContent = '🔐 ' + currentCipher.toUpperCase();
        document.getElementById('cipherModal').classList.remove('open');
    }

    function selectCipher(cipher) {
        currentCipher = cipher;
        document.querySelectorAll('.cipher-option').forEach(function(b) { b.classList.remove('active'); });
        event.target.classList.add('active');
        document.getElementById('shiftSection').style.display = cipher === 'caesar' ? 'block' : 'none';
        document.getElementById('keywordSection').style.display = cipher === 'vigenere' ? 'block' : 'none';
    }

    function joinRoom(roomId) {
        window.location.href = '/?room=' + roomId;
        closeSidebar();
    }

    function openNewRoomModal() { document.getElementById('newRoomModal').classList.add('open'); }
    function closeNewRoomModal() { document.getElementById('newRoomModal').classList.remove('open'); }
    function openSidebar() {
        document.getElementById('sidebar').classList.add('open');
        document.getElementById('sidebarOverlay').classList.add('open');
    }
    function closeSidebar() {
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('sidebarOverlay').classList.remove('open');
    }

    const messages = document.getElementById('messages');
    if (messages) messages.scrollTop = messages.scrollHeight;
</script>
{% endif %}
</body>
</html>'''


@app.route('/', methods=['GET', 'POST'])
def index():
    error = None

    if request.method == 'POST':
        auth_action = request.form.get('auth_action')

        if auth_action == 'logout':
            session.clear()
            return redirect(url_for('index'))

        if auth_action == 'register':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if len(username) < 3:
                error = 'CODENAME MUST BE 3+ CHARACTERS'
            elif len(password) < 4:
                error = 'ACCESS CODE MUST BE 4+ CHARACTERS'
            else:
                success = create_user(username, password)
                if success:
                    user = verify_user(username, password)
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    return redirect(url_for('index'))
                else:
                    error = 'CODENAME ALREADY IN USE'

        elif auth_action == 'login':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            user = verify_user(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                error = 'INVALID CREDENTIALS - ACCESS DENIED'

    if 'user_id' not in session:
        return render_template_string(HTML, logged_in=False, error=error)

    rooms = get_all_rooms()
    room_id = request.args.get('room', type=int)
    current_room = get_room(room_id) if room_id else None
    messages = get_messages(room_id) if room_id else []

    return render_template_string(HTML,
        logged_in=True,
        username=session['username'],
        rooms=rooms,
        current_room=current_room,
        messages=messages,
        encrypted_mode=session.get('encrypted_mode', False),
        mode=session.get('mode', 'plain'),
        cipher=session.get('cipher', 'caesar'),
        shift=session.get('shift', 3),
        keyword=session.get('keyword', 'KEY')
    )


@app.route('/create_room_form', methods=['POST'])
def create_room_form():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    name = request.form.get('name', '').strip().upper()
    if not name:
        return redirect(url_for('index'))
    room_id = create_room(name, session['user_id'])
    if room_id:
        return redirect('/?room=' + str(room_id))
    return redirect(url_for('index'))


@app.route('/send_message', methods=['POST'])
def send_message_route():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    room_id = request.form.get('room_id', type=int)
    message = request.form.get('message', '').strip()
    mode = request.form.get('mode', 'plain')
    cipher = request.form.get('cipher', 'caesar')
    shift = int(request.form.get('shift', 3))
    keyword = request.form.get('keyword', 'KEY').strip() or 'KEY'
    encrypted_mode = request.form.get('encrypted_mode') == 'true'

    session['mode'] = mode
    session['cipher'] = cipher
    session['shift'] = shift
    session['keyword'] = keyword
    session['encrypted_mode'] = encrypted_mode

    if not message or not room_id:
        return redirect('/?room=' + str(room_id))

    def run_cipher(text, enc=True):
        if cipher == 'rot13':
            return rot13(text)
        elif cipher == 'vigenere':
            return vigenere(text, keyword, encrypt=enc)
        else:
            return encrypt(text, shift) if enc else decrypt(text, shift)

    is_encrypted = False

    if mode == 'ai':
        try:
            ai_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=message
            )
            content = ai_response.text.strip()
        except Exception as e:
            content = 'TRANSMISSION ERROR: ' + str(e)
        sender = 'HQ'
    else:
        content = message
        sender = session['username']

    if encrypted_mode:
        content = run_cipher(content)
        is_encrypted = True

    save_message(room_id, session['user_id'], sender, content, is_encrypted)

    return redirect('/?room=' + str(room_id))


@socketio.on('join')
def on_join(data):
    room_id = str(data['room_id'])
    username = data['username']
    join_room(room_id)
    emit('user_joined', {'msg': username + ' JOINED THE CHANNEL'}, to=room_id)


if __name__ == '__main__':
    socketio.run(app, debug=True)
