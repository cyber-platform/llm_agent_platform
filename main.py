import threading
from flask import Flask
from auth.credentials import refresh_user_creds
from api.openai.routes import openai_bp
from api.gemini.routes import gemini_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(openai_bp)
app.register_blueprint(gemini_bp)

if __name__ == "__main__":
    # Initialize authentication first
    from auth.credentials import initialize_auth
    if not initialize_auth():
        print("[ERROR] Failed to initialize authentication. Exiting.")
        exit(1)
    
    # Start background refresh thread
    threading.Thread(target=refresh_user_creds, daemon=True).start()
    
    app.run(host='0.0.0.0', port=4000, debug=False)
