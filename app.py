from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smt-jig-secret'

# Khởi tạo SocketIO
socketio = SocketIO(app)

# Route chính
@app.route('/')
def index():
    return render_template('index.html')

# Sự kiện khi client kết nối
@socketio.on('connect')
def handle_connect():
    print('Client connected')

# Sự kiện khi client ngắt kết nối
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Sự kiện test
@socketio.on('test_event')
def handle_test_event(data):
    print('Received from client:', data)
    emit('broadcast_message', {'message': data['message']}, broadcast=True)

# Chạy app
if __name__ == '__main__':
    print("SMT JIG Web 起動中...")

    # Render cung cấp PORT qua biến môi trường
    port = int(os.environ.get("PORT", 5000))

    socketio.run(app, host='0.0.0.0', port=port)
