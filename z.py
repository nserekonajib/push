from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK with your service account
cred = credentials.Certificate("n.json")
firebase_admin.initialize_app(cred)

# In-memory store (or use database in production)
user_tokens = {}

@app.route("/register-token", methods=["POST"])
def register_token():
    data = request.json
    user = data.get("user")
    token = data.get("token")

    if not user or not token:
        return jsonify({"error": "Missing user or token"}), 400

    user_tokens[user] = token
    return jsonify({"message": "Token registered successfully"})

@app.route("/send-notification", methods=["POST"])
def send_notification():
    data = request.json
    user = data.get("user")
    title = data.get("title", "Hello!")
    body = data.get("body", "You have a new message 💌")

    token = user_tokens.get(user)
    if not token:
        return jsonify({"error": "No token found for user"}), 404

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        webpush=messaging.WebpushConfig(
            notification={
                "icon": "n.jpeg",
                "click_action": "https://your-app.com"
            }
        )
    )

    response = messaging.send(message)
    return jsonify({"message_id": response})


