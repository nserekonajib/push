from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, messaging
import logging

app = Flask(__name__)

# Configure CORS - adjust origins as needed for production
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Firebase Admin SDK (make sure n.json is your service account key)
cred = credentials.Certificate("n.json")
firebase_admin.initialize_app(cred)

# In-memory token store (replace with persistent DB in prod)
user_tokens: dict[str, str] = {}

# Setup logger
logging.basicConfig(level=logging.INFO)


@app.route("/register-token", methods=["POST"])
def register_token():
    data = request.get_json(force=True)
    user = data.get("user")
    token = data.get("token")

    if not user or not token:
        return jsonify({"error": "Missing 'user' or 'token' in request body"}), 400

    user_tokens[user] = token
    logging.info(f"Registered token for user '{user}': {token}")
    return jsonify({"message": "Token registered successfully"}), 200


@app.route("/send-notification", methods=["POST"])
def send_notification():
    data = request.get_json(force=True)
    user = data.get("user")
    title = data.get("title", "Hello!")
    body = data.get("body", "You have a new message 💌")

    if not user:
        return jsonify({"error": "Missing 'user' in request body"}), 400

    token = user_tokens.get(user)
    if not token:
        return jsonify({"error": f"No token found for user '{user}'"}), 404

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        webpush=messaging.WebpushConfig(
            notification={
                "icon": "https://your-domain.com/path-to-icon.png",  # Use absolute URL to icon
                "click_action": "https://your-domain.com/dashboard"  # Your app URL on click
            }
        )
    )

    try:
        response = messaging.send(message)
        logging.info(f"Sent notification to user '{user}', message_id: {response}")
        return jsonify({"message_id": response}), 200
    except Exception as e:
        logging.error(f"Error sending notification to user '{user}': {e}")
        return jsonify({"error": "Failed to send notification", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
