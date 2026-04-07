from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os

# ====== Sheets integration (bạn map vào sheets.py thật) ======
from sheets import borrow_jig, return_jig, reserve_jig  # bạn sẽ tạo 3 hàm này

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smt-jig-secret'

socketio = SocketIO(app)

# session state: sid -> dict
session_states = {}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    sid = getattr(socketio, 'sid', None)  # phòng khi dùng khác driver
    print('Client connected')
    emit('bot_message', {'message': '接続しました。ご用件を選択してください。'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# ========== FLOW ENTRY POINTS (từ quick buttons) ==========

@socketio.on('user_action')
def handle_user_action(data):
    sid = getattr(socketio, 'sid', None)
    action = data.get('action')
    print(f"[USER ACTION] {action}")

    if action == "borrow":
        # start borrow flow
        session_states[sid] = {"flow": "borrow", "step": 1, "data": {}}
        emit('bot_message', {'message': '【JIG 借用】JIG ID を入力してください。'})
    elif action == "return":
        session_states[sid] = {"flow": "return", "step": 1, "data": {}}
        emit('bot_message', {'message': '【JIG 返却】JIG ID を入力してください。'})
    elif action == "reserve":
        session_states[sid] = {"flow": "reserve", "step": 1, "data": {}}
        emit('bot_message', {'message': '【JIG 予約】JIG ID を入力してください。'})
    elif action == "consumables":
        emit('bot_message', {'message': '【消耗品 使用】このフローは後で実装します。'})
    elif action == "status":
        emit('bot_message', {'message': '【状況一覧】このフローは後で実装します。'})
    else:
        emit('bot_message', {'message': '不明な操作です。'})


# ========== TEXT MESSAGE HANDLER (điều khiển toàn bộ flow) ==========

@socketio.on('user_message')
def handle_user_message(data):
    sid = getattr(socketio, 'sid', None)
    text = data.get('text', '').strip()
    print(f"[USER TEXT] {text}")

    state = session_states.get(sid)

    # nếu không có flow đang chạy → coi như chat tự do
    if not state:
        emit('bot_message', {'message': f"受信しました: {text}"})
        return

    flow = state.get("flow")
    step = state.get("step", 1)
    ctx = state.get("data", {})

    # ===== BORROW FLOW =====
    if flow == "borrow":
        if step == 1:
            # nhận JIG ID
            ctx["jig_id"] = text
            state["step"] = 2
            emit('bot_message', {'message': f'JIG ID: {text}\n数量を入力してください。'})
        elif step == 2:
            # nhận quantity
            if not text.isdigit():
                emit('bot_message', {'message': '数量は数字で入力してください。'})
                return
            ctx["qty"] = int(text)
            state["step"] = 3
            emit('bot_message', {
                'message': f'JIG ID: {ctx["jig_id"]}\n数量: {ctx["qty"]}\n\nこの内容で借用しますか？（はい / いいえ）'
            })
        elif step == 3:
            if text in ["はい", "はい。", "はいです", "yes", "Yes"]:
                # gọi Sheets
                success, msg = borrow_jig(ctx["jig_id"], ctx["qty"])
                emit('bot_message', {'message': msg})
                session_states.pop(sid, None)
            else:
                emit('bot_message', {'message': 'キャンセルしました。最初からやり直してください。'})
                session_states.pop(sid, None)

    # ===== RETURN FLOW =====
    elif flow == "return":
        if step == 1:
            ctx["jig_id"] = text
            state["step"] = 2
            emit('bot_message', {
                'message': f'JIG ID: {text}\n返却数量を入力してください。'
            })
        elif step == 2:
            if not text.isdigit():
                emit('bot_message', {'message': '数量は数字で入力してください。'})
                return
            ctx["qty"] = int(text)
            state["step"] = 3
            emit('bot_message', {
                'message': f'JIG ID: {ctx["jig_id"]}\n返却数量: {ctx["qty"]}\n\nこの内容で返却しますか？（はい / いいえ）'
            })
        elif step == 3:
            if text in ["はい", "はい。", "はいです", "yes", "Yes"]:
                success, msg = return_jig(ctx["jig_id"], ctx["qty"])
                emit('bot_message', {'message': msg})
                session_states.pop(sid, None)
            else:
                emit('bot_message', {'message': 'キャンセルしました。最初からやり直してください。'})
                session_states.pop(sid, None)

    # ===== RESERVE FLOW =====
    elif flow == "reserve":
        if step == 1:
            ctx["jig_id"] = text
            state["step"] = 2
            emit('bot_message', {
                'message': f'JIG ID: {text}\n予約数量を入力してください。'
            })
        elif step == 2:
            if not text.isdigit():
                emit('bot_message', {'message': '数量は数字で入力してください。'})
                return
            ctx["qty"] = int(text)
            state["step"] = 3
            emit('bot_message', {
                'message': f'JIG ID: {ctx["jig_id"]}\n予約数量: {ctx["qty"]}\n\nこの内容で予約しますか？（はい / いいえ）'
            })
        elif step == 3:
            if text in ["はい", "はい。", "はいです", "yes", "Yes"]:
                success, msg = reserve_jig(ctx["jig_id"], ctx["qty"])
                emit('bot_message', {'message': msg})
                session_states.pop(sid, None)
            else:
                emit('bot_message', {'message': 'キャンセルしました。最初からやり直してください。'})
                session_states.pop(sid, None)

    # cập nhật lại state
    state["data"] = ctx
    session_states[sid] = state


if __name__ == '__main__':
    print("SMT JIG Web 起動中...")
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
