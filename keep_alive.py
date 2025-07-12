from flask import Flask
import threading
import logging

# Setup logging for Flask
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>EMS Training Bot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #e74c3c; }
                .status { color: #27ae60; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚁 EMS Training Discord Bot</h1>
                <p class="status">✅ Bot is online and running</p>
                <p>This bot provides comprehensive EMS flight training features including:</p>
                <ul>
                    <li>🚨 Emergency alert detection and response</li>
                    <li>🧠 AI-powered help system</li>
                    <li>📁 Document management</li>
                    <li>🛫 Mission logging</li>
                    <li>⏰ Scheduled reminders</li>
                    <li>🎖️ Rank management</li>
                </ul>
                <p><strong>Last updated:</strong> Bot startup</p>
            </div>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'EMS Training Bot'}

def keep_alive():
    """Start Flask server in a separate thread"""
    def run():
        app.run(host='0.0.0.0', port=5000, debug=False)
    
    server = threading.Thread(target=run)
    server.daemon = True
    server.start()
    print("Keep-alive server started on port 5000")
