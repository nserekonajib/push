from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, messaging
import logging
import traceback

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

# --- Firebase Admin SDK Initialization ---
try:
    cred = credentials.Certificate("n.json")  # Your Firebase service account JSON
    firebase_admin.initialize_app(cred)
    logging.info("Firebase Admin SDK initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Firebase Admin SDK: {e}")
    raise e

# --- In-Memory Store for FCM Tokens (Replace with DB in Production) ---
user_tokens = {}

# --- Register Device Token ---
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

# --- Send Notification to One User ---
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

# --- Broadcast Notification to All Registered Devices ---
@app.route("/broadcast", methods=["POST"])
def broadcast():
    data = request.get_json(force=True)
    title = data.get("title", "🔔 New Notification")
    body = data.get("body", "This is a message to all devices.")

    results = []
    for user, token in user_tokens.items():
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
            results.append({user: response})
            logging.info(f"Broadcast sent to {user}: {response}")
        except Exception as e:
            results.append({user: str(e)})
            logging.error(f"Broadcast failed for {user}: {e}")
            logging.error(traceback.format_exc())

    return jsonify({"results": results}), 200

# --- Optional Root Endpoint ---
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Push Notification Server is running"}), 200


