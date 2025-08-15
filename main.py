import os
from app import app

# Optional: Only run ngrok in development mode
if os.environ.get("USE_NGROK") == "true":
    from pyngrok import ngrok

    port = 5000
    public_url = ngrok.connect(port)
    print(f" * ngrok tunnel: {public_url}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
