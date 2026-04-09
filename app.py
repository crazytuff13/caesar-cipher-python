from flask import Flask, request, render_template_string, session
from ceasar_cypher import encrypt, decrypt

app = Flask(__name__)
app.secret_key = 'caesar123'

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Caesar Cipher</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #eee;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            background: #16213e;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 500px;
        }

        h1 {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 8px;
            color: #e94560;
            letter-spacing: 2px;
        }

        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
            font-size: 0.9rem;
        }

        label {
            display: block;
            margin-bottom: 6px;
            color: #aaa;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #0f3460;
            background: #0f3460;
            color: #fff;
            font-size: 1rem;
            margin-bottom: 20px;
            outline: none;
            transition: border 0.2s;
        }

        input[type="text"]:focus, input[type="number"]:focus {
            border-color: #e94560;
        }

        .buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        button {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            font-weight: bold;
            transition: opacity 0.2s;
        }

        button:hover {
            opacity: 0.85;
        }

        .btn-encrypt {
            background: #e94560;
            color: white;
        }

        .btn-decrypt {
            background: #0f3460;
            color: white;
            border: 1px solid #e94560;
        }

        .btn-undo {
            background: #444;
            color: white;
            flex: 0.5;
        }

        .result {
            background: #0f3460;
            border-left: 4px solid #e94560;
            padding: 16px 20px;
            border-radius: 8px;
            font-size: 1.2rem;
            word-break: break-all;
            letter-spacing: 1px;
        }

        .result-label {
            font-size: 0.75rem;
            color: #e94560;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Caesar Cipher</h1>
        <p class="subtitle">Encrypt and decrypt your messages</p>
        <form method="POST">
            <label>Message</label>
            <input type="text" name="message" value="{{ message }}" placeholder="Enter your message...">

            <label>Shift (1-25)</label>
            <input type="number" name="shift" min="1" max="25" value="{{ shift }}">

            <div class="buttons">
                <button class="btn-encrypt" name="mode" value="e">🔒 Encrypt</button>
                <button class="btn-decrypt" name="mode" value="d">🔓 Decrypt</button>
                {% if previous %}
                    <button class="btn-undo" name="mode" value="undo">↩ Undo</button>
                {% endif %}
            </div>
        </form>

        {% if result %}
        <div class="result-label">Result</div>
        <div class="result">{{ result }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    message = ''
    shift = 3
    previous = session.get('previous', '')

    if request.method == 'POST':
        message = request.form['message']
        shift = int(request.form['shift'])
        mode = request.form['mode']

        if mode == 'undo':
            result = previous
        elif mode == 'e':
            session['previous'] = message
            result = encrypt(message, shift)
        else:
            session['previous'] = message
            result = decrypt(message, shift)

        previous = session.get('previous', '')

    return render_template_string(HTML, result=result, message=message, shift=shift, previous=previous)

if __name__ == '__main__':
    app.run(debug=True)