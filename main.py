from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure secret key
socketio = SocketIO(app)

active_users = {}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    username = request.args.get('username')
    if not username or username in active_users.values():
        emit('username_taken', {}, room=request.sid)
        disconnect(request.sid)
        return

    active_users[request.sid] = username
    emit('update_user_list', list(active_users.values()), broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_users:
        del active_users[request.sid]
        emit('update_user_list', list(active_users.values()), broadcast=True)


@socketio.on('message')
def handle_message(msg):
    send(msg, broadcast=True)


@socketio.on('private_message')
def handle_private_message(data):
    recipient_session_id = None
    for session_id, username in active_users.items():
        if username == data['recipient']:
            recipient_session_id = session_id
            break
    if recipient_session_id:
        emit('private_message', data['msg'], room=recipient_session_id)


@socketio.on('boot_user')
def boot_user(data):
    initiator_username = active_users.get(request.sid)
    target_username = data.get("target_username")
    
    if initiator_username != "Server":
        emit('action_denied', {'error': "You don't have permission to boot users."}, room=request.sid)
        return
    
    target_sid = None
    for sid, username in active_users.items():
        if username == target_username:
            target_sid = sid
            break
    
    if not target_sid:
        emit('action_failed', {'error': f"User '{target_username}' not found."}, room=request.sid)
        return
    
    disconnect(target_sid)
    del active_users[target_sid]
    
    emit('update_user_list', list(active_users.values()), broadcast=True)
    
    emit('action_success', {'message': f"User '{target_username}' has been booted."}, room=request.sid)



if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
