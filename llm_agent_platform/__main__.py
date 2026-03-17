from flask import Flask
from llm_agent_platform.core.logging import setup_logging
from llm_agent_platform.api.openai.routes import openai_bp
from llm_agent_platform.api.gemini.routes import gemini_bp
from llm_agent_platform.api.parity.routes import parity_bp

# Setup logging
logger = setup_logging()

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(openai_bp)
app.register_blueprint(gemini_bp)
app.register_blueprint(parity_bp)

if __name__ == "__main__":
    # Initialize authentication first
    from llm_agent_platform.auth.credentials import initialize_auth
    if not initialize_auth():
        logger.error("[ERROR] Failed to initialize authentication. Exiting.")
        exit(1)

    app.run(host='0.0.0.0', port=4000, debug=False)
