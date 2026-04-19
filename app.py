from flask import Flask, request, render_template_string, session
from ceasar_cypher import encrypt, decrypt, rot13, vigenere
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = 'caesar123'

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>CLASSIFIED CHANNEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        html, body {
            height: 100%;
            background: #000;
        }

        body {
            font-family: 'Share Tech Mono', monospace;
            color: #00ff41;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100%;
        }

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
            z-index: 100;
        }

        .container {
            width: 100%;
            max-width: 700px;
            display: flex;
            flex-direction: column;
            border-left: 1px solid #00ff41;
            border-right: 1px solid #00ff41;
            box-shadow: 0 0 20px #00ff41, inset 0 0 20px rgba(0,255,65,0.05);
            padding: 12px;
            flex: 1;
        }

        .header {
            text-align: center;
            border-bottom: 1px solid #00ff41;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }

        .header h1 {
            font-size: 1.1rem;
            letter-spacing: 3px;
            color: #00ff41;
            text-shadow: 0 0 10px #00ff41;
        }

        .header p {
            font-size: 0.75rem;
            color: #005f1a;
            letter-spacing: 2px;
            margin-top: 4px;
        }

        .panic-setup {
            text-align: center;
            padding: 20px;
            border: 1px dashed #00ff41;
            margin-bottom: 10px;
        }

        .panic-setup p {
            font-size: 0.9rem;
            margin-bottom: 12px;
            letter-spacing: 2px;
        }

        .panic-setup input {
            background: #000;
            border: 1px solid #00ff41;
            color: #00ff41;
            font-family: 'Share Tech Mono', monospace;
            padding: 10px;
            width: 100%;
            text-align: center;
            font-size: 1rem;
            margin-bottom: 10px;
        }

        .panic-setup button {
            background: #00ff41;
            color: #000;
            border: none;
            padding: 10px 16px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: bold;
            cursor: pointer;
            font-size: 1rem;
            width: 100%;
        }

        .chat-history {
            flex: 1;
            overflow-y: auto;
            padding: 10px 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 200px;
        }

        .chat-history::-webkit-scrollbar { width: 4px; }
        .chat-history::-webkit-scrollbar-track { background: #000; }
        .chat-history::-webkit-scrollbar-thumb { background: #00ff41; }

        .bubble-row {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .bubble-row.agent { align-items: flex-end; }
        .bubble-row.hq { align-items: flex-start; }

        .label {
            font-size: 0.75rem;
            color: #005f1a;
            letter-spacing: 2px;
            padding: 0 8px;
        }

        .bubble {
            max-width: 85%;
            padding: 10px 14px;
            font-size: 1rem;
            line-height: 1.5;
            word-break: break-word;
        }

        .bubble.agent {
            background: rgba(0,255,65,0.1);
            border: 1px solid #00ff41;
            color: #00ff41;
        }

        .bubble.hq {
            background: rgba(0,255,65,0.05);
            border: 1px solid #005f1a;
            color: #00cc33;
        }

        .panic-active .bubble {
            color: #ff0000 !important;
            border-color: #ff0000 !important;
            text-shadow: 0 0 8px #ff0000;
        }

        .panic-banner {
            text-align: center;
            color: #ff0000;
            font-size: 0.85rem;
            letter-spacing: 2px;
            padding: 8px;
            border: 1px solid #ff0000;
            margin-bottom: 8px;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .controls {
            border-top: 1px solid #00ff41;
            padding-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-bottom: 16px;
        }

        .section-label {
            font-size: 0.7rem;
            color: #005f1a;
            letter-spacing: 3px;
            margin-bottom: 4px;
        }

        .cipher-row {
            display: flex;
            gap: 6px;
        }

        .cipher-btn {
            flex: 1;
            padding: 12px 4px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.85rem;
            letter-spacing: 1px;
            cursor: pointer;
            border: 1px solid #005f1a;
            background: #000;
            color: #005f1a;
        }

        .cipher-btn.active {
            border-color: #00ff41;
            color: #00ff41;
            background: rgba(0,255,65,0.1);
            text-shadow: 0 0 8px #00ff41;
        }

        .shift-row {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
            color: #005f1a;
            letter-spacing: 2px;
        }

        .shift-row input[type="number"] {
            background: #000;
            border: 1px solid #00ff41;
            color: #00ff41;
            font-family: 'Share Tech Mono', monospace;
            padding: 8px;
            width: 70px;
            text-align: center;
            font-size: 1rem;
        }

        .shift-row input[type="text"] {
            background: #000;
            border: 1px solid #00ff41;
            color: #00ff41;
            font-family: 'Share Tech Mono', monospace;
            padding: 8px;
            width: 140px;
            text-align: center;
            font-size: 1rem;
        }

        .toggle-row {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .toggle-btn {
            flex: 1;
            min-width: 70px;
            padding: 12px 4px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.8rem;
            letter-spacing: 1px;
            cursor: pointer;
            border: 1px solid #005f1a;
            background: #000;
            color: #005f1a;
        }

        .toggle-btn.active {
            border-color: #00ff41;
            color: #00ff41;
            background: rgba(0,255,65,0.1);
            text-shadow: 0 0 8px #00ff41;
        }

        .input-row {
            display: flex;
            gap: 8px;
        }

        .input-row input {
            flex: 1;
            background: #000;
            border: 1px solid #00ff41;
            color: #00ff41;
            font-family: 'Share Tech Mono', monospace;
            padding: 14px 10px;
            font-size: 1rem;
            outline: none;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .input-row input::placeholder { color: #005f1a; }

        .transmit-btn {
            background: #00ff41;
            color: #000;
            border: none;
            padding: 14px 16px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: bold;
            letter-spacing: 1px;
            cursor: pointer;
            font-size: 0.9rem;
            -webkit-appearance: none;
            border-radius: 0;
        }

        .transmit-btn:active { background: #00cc33; }
    </style>
</head>
<body>
<div class="scanline"></div>
<div class="container {% if panic %}panic-active{% endif %}">
    <div class="header">
        <h1>[ CLASSIFIED CHANNEL 7 ]</h1>
        <p>SECURE TRANSMISSION PROTOCOL ACTIVE</p>
    </div>

    {% if not panic_word %}
    <div class="panic-setup">
        <p>ESTABLISH PANIC WORD TO BEGIN</p>
        <form method="POST">
            <input type="text" name="panic_word" placeholder="ENTER PANIC WORD" autocomplete="off">
            <button type="submit" name="action" value="set_panic">CONFIRM</button>
        </form>
    </div>
    {% else %}

    {% if panic %}
    <div class="panic-banner">⚠ SECURITY PROTOCOL ACTIVE — ALL TRANSMISSIONS ENCRYPTED ⚠</div>
    {% endif %}

    <div class="chat-history">
        {% for msg in history %}
        <div class="bubble-row {{ msg.sender }}">
            <div class="label">{{ '> AGENT' if msg.sender == 'agent' else '< HQ' }}</div>
            <div class="bubble {{ msg.sender }}">{{ msg.text }}</div>
        </div>
        {% endfor %}
    </div>

    <div class="controls">
        <div>
            <div class="section-label">— CIPHER TYPE —</div>
            <div class="cipher-row">
                <button class="cipher-btn {% if cipher == 'caesar' %}active{% endif %}" onclick="setCipher('caesar')">CAESAR</button>
                <button class="cipher-btn {% if cipher == 'rot13' %}active{% endif %}" onclick="setCipher('rot13')">ROT13</button>
                <button class="cipher-btn {% if cipher == 'vigenere' %}active{% endif %}" onclick="setCipher('vigenere')">VIGENÈRE</button>
            </div>
        </div>

        <div id="shiftRow" class="shift-row">
            SHIFT:
            <input type="number" id="shift" min="1" max="25" value="{{ shift }}">
        </div>

        <div id="keywordRow" class="shift-row" style="display:none;">
            KEYWORD:
            <input type="text" id="keyword" maxlength="20" placeholder="ENTER KEY" value="{{ keyword }}">
        </div>

        <div>
            <div class="section-label">— MODE —</div>
            <div class="toggle-row">
                <button class="toggle-btn {% if mode == 'plain' %}active{% endif %}" onclick="setMode('plain')">💬 PLAIN</button>
                <button class="toggle-btn {% if mode == 'encrypt' %}active{% endif %}" onclick="setMode('encrypt')">🔒 ENCRYPT</button>
                <button class="toggle-btn {% if mode == 'decrypt' %}active{% endif %}" onclick="setMode('decrypt')">🔓 DECRYPT</button>
                <button class="toggle-btn {% if mode == 'ai' %}active{% endif %}" onclick="setMode('ai')">🤖 ASK HQ</button>
            </div>
        </div>

        <form method="POST" id="mainForm">
            <input type="hidden" name="action" value="send">
            <input type="hidden" name="mode" id="modeInput" value="{{ mode }}">
            <input type="hidden" name="shift" id="shiftInput" value="{{ shift }}">
            <input type="hidden" name="cipher" id="cipherInput" value="{{ cipher }}">
            <input type="hidden" name="keyword" id="keywordInput" value="{{ keyword }}">
            <div class="input-row">
                <input type="text" name="message" placeholder="ENTER TRANSMISSION..." autocomplete="off">
                <button type="submit" class="transmit-btn">SEND</button>
            </div>
        </form>
    </div>
    {% endif %}
</div>

<script>
    function setMode(mode) {
        document.getElementById('modeInput').value = mode;
        document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
    }

    function setCipher(cipher) {
        document.getElementById('cipherInput').value = cipher;
        document.querySelectorAll('.cipher-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');

        if (cipher === 'vigenere') {
            document.getElementById('shiftRow').style.display = 'none';
            document.getElementById('keywordRow').style.display = 'flex';
        } else if (cipher === 'rot13') {
            document.getElementById('shiftRow').style.display = 'none';
            document.getElementById('keywordRow').style.display = 'none';
        } else {
            document.getElementById('shiftRow').style.display = 'flex';
            document.getElementById('keywordRow').style.display = 'none';
        }
    }

    document.getElementById('shift')?.addEventListener('change', function() {
        document.getElementById('shiftInput').value = this.value;
    });

    document.getElementById('keyword')?.addEventListener('input', function() {
        document.getElementById('keywordInput').value = this.value;
    });

    setCipher("{{ cipher }}");

    const chat = document.querySelector('.chat-history');
    if (chat) chat.scrollTop = chat.scrollHeight;
</script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'history' not in session:
        session['history'] = []
    if 'panic' not in session:
        session['panic'] = False
    if 'panic_word' not in session:
        session['panic_word'] = ''
    if 'shift' not in session:
        session['shift'] = 3
    if 'mode' not in session:
        session['mode'] = 'plain'
    if 'cipher' not in session:
        session['cipher'] = 'caesar'
    if 'keyword' not in session:
        session['keyword'] = 'KEY'

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'set_panic':
            panic_word = request.form.get('panic_word', '').strip().lower()
            session['panic_word'] = panic_word
            session['history'] = [{
                'sender': 'hq',
                'text': 'PANIC WORD SET. CHANNEL SECURE. BEGIN TRANSMISSION.'
            }]

        elif action == 'send':
            message = request.form.get('message', '').strip()
            mode = request.form.get('mode', 'plain')
            shift = int(request.form.get('shift', 3))
            cipher = request.form.get('cipher', 'caesar')
            keyword = request.form.get('keyword', 'KEY').strip() or 'KEY'

            session['shift'] = shift
            session['mode'] = mode
            session['cipher'] = cipher
            session['keyword'] = keyword

            if not message:
                return render_template_string(HTML, **session)

            # Panic word toggle
            if message.lower() == session['panic_word'].lower():
                session['panic'] = not session['panic']
                status = 'ACTIVATED' if session['panic'] else 'DEACTIVATED'
                history = session['history']
                history.append({'sender': 'hq', 'text': f'⚠ SECURITY PROTOCOL {status} ⚠'})
                session['history'] = history
                session.modified = True
                return render_template_string(HTML, **session)

            def run_cipher(text, enc=True):
                if cipher == 'rot13':
                    return rot13(text)
                elif cipher == 'vigenere':
                    return vigenere(text, keyword, encrypt=enc)
                else:
                    return encrypt(text, shift) if enc else decrypt(text, shift)

            history = session['history']

            # Agent bubble — encrypt display if panic active
            display_msg = run_cipher(message) if session['panic'] else message
            history.append({'sender': 'agent', 'text': display_msg})

            # HQ response
            if mode == 'plain':
                response_text = message

            elif mode == 'encrypt':
                result = run_cipher(message)
                response_text = f'ENCRYPTED: {result}'

            elif mode == 'decrypt':
                result = run_cipher(message, enc=False)
                response_text = f'DECRYPTED: {result}'

            elif mode == 'ai':
                try:
                    ai_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=message
                    )
                    response_text = ai_response.text.strip()
                except Exception as e:
                    response_text = f'TRANSMISSION ERROR: {str(e)}'

            # Encrypt HQ response if panic active
            if session['panic']:
                response_text = run_cipher(response_text)

            history.append({'sender': 'hq', 'text': response_text})
            session['history'] = history
            session.modified = True

    return render_template_string(HTML,
        history=session['history'],
        panic=session['panic'],
        panic_word=session['panic_word'],
        shift=session['shift'],
        mode=session['mode'],
        cipher=session['cipher'],
        keyword=session['keyword']
    )

if __name__ == '__main__':
    app.run(debug=True)