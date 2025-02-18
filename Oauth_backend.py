import os
import requests
from flask import Flask, request, redirect, jsonify
from pyngrok import ngrok
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

# Start ngrok and generate a public URL
ngrok_tunnel = ngrok.connect(5000)
REDIRECT_URI = f"{ngrok_tunnel.public_url}/slack/oauth/callback"

print(f"🔗 Redirect URI (Use this in Slack settings): {REDIRECT_URI}")

@app.route("/slack/install")
def slack_install():
    """Redirects users to Slack OAuth approval page."""
    slack_auth_url = (
        f"https://slack.com/oauth/v2/authorize?client_id={SLACK_CLIENT_ID}"
        f"&scope=channels:history,chat:write,conversations.read"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return redirect(slack_auth_url)

@app.route("/slack/oauth/callback")
def slack_callback():
    """Handles OAuth callback and exchanges code for bot token."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": SLACK_CLIENT_ID,
            "client_secret": SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )

    slack_data = response.json()
    
    if not slack_data.get("ok"):
        return jsonify({"error": "Failed to get access token", "details": slack_data}), 400

    access_token = slack_data.get("access_token")

    # Store token in a file or env variable
    with open(".slack_token", "w") as f:
        f.write(access_token)

    return jsonify({"message": "Slack App Installed!", "access_token": access_token})

if __name__ == "__main__":
    app.run(port=5000)
