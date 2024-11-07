from flask import request, jsonify
from flask_jwt_extended import decode_token, exceptions as jwt_exceptions, JWTManager
from flask_socketio import SocketIO, join_room, leave_room
import jwt

socketio = SocketIO(cors_allowed_origins="*")
jwt_manager = JWTManager()

connected_users = {}  # Dictionary to map userId to their socket session ID

@socketio.on('connect')
def handle_connect(auth):
    if not auth or 'token' not in auth:
        print("Missing or invalid token")
        return False  # Reject the connection if no token is provided

    token = auth.get('token')
    try:
        # Decode the token manually
        decoded_token = decode_token(token)
        user_identity = decoded_token["sub"]  # Adjust based on your JWT structure
        user_id = int(user_identity["userId"])

        if user_id:
            connected_users[user_id] = request.sid
            join_room(user_id)
            print(f'User {user_id} connected with session ID {request.sid}')
    except Exception:
        print("Token has expired")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    user_id = next((key for key, value in connected_users.items() if value == request.sid), None)
    if user_id:
        connected_users.pop(user_id, None)
        leave_room(user_id)
        print(f'User {user_id} disconnected.')

# Emit notifications to a specific user
def send_notification_to_user(user_id, message):
    if user_id in connected_users:
        socketio.emit('new_notification', {'message': message}, room=user_id)
