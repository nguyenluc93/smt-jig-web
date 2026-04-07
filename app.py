from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smt-jig-secret'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("SMT JIG Web 起動中...")
    socketio.run(app, host='0.0.0.0', port=5000)

@socketio.on('test_event')
def handle_test_event(data):
    print('Received from client:', data)
    emit('broadcast_message', {'message': data['message']}, broadcast=True)

