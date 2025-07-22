from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, messaging
import logging
import traceback

app = Flask(__name__)
CORS(app)  # Adjust origins for production as needed

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate("n.json")  # Your Firebase service account file
    firebase_admin.initialize_app(cred)
    logging.info("Firebase Admin SDK initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Firebase Admin SDK: {e}")
    raise e

# In-memory user tokens store (replace with DB for production)
user_tokens = {}

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
            notification=messaging.WebpushNotification(
                icon="https://your-domain.com/assets/icon.png"
            ),
            fcm_options=messaging.WebpushFCMOptions(
                link="https://your-domain.com/dashboard"
            )
        )
    )

    try:
        response = messaging.send(message)
        logging.info(f"Notification sent to user '{user}', message_id: {response}")
        return jsonify({"message_id": response}), 200
    except Exception as e:
        logging.error(f"Error sending notification to user '{user}': {e}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "Failed to send notification", "details": str(e)}), 500



