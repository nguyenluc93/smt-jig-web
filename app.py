from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import logging

# ---------------------------
# ENABLE FULL DEBUG LOGGING
# ---------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from sheets import (
    get_jig_list,
    write_borrow,
    get_returnable_list,
    write_return,
    write_comment
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def menu():
    logger.debug("Menu page loaded")
    return render_template("menu.html")


@app.route("/borrow")
def borrow():
    logger.debug("Borrow page loaded")
    return render_template("borrow.html")


@app.route("/return")
def return_page():
    logger.debug("Return page loaded")
    return render_template("return.html")


@app.route("/consumables")
def consumables():
    logger.debug("Consumables page loaded")
    return render_template("consumables.html")


@app.route("/comment")
def comment():
    logger.debug("Comment page loaded")
    return render_template("comment.html")


# ---------------------------
# API ENDPOINTS
# ---------------------------

@app.route("/api/get_jigs", methods=["GET"])
def api_get_jigs():
    try:
        category = request.args.get("category", "")
        logger.debug(f"API get_jigs called with category={category}")
        items = get_jig_list(category)
        return jsonify({"status": "ok", "items": items})
    except Exception as e:
        logger.exception("Error in /api/get_jigs")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/borrow", methods=["POST"])
def api_borrow():
    try:
        data = request.json
        logger.debug(f"API borrow called with data={data}")
        write_borrow(
            data["jig"],
            data["start_date"],
            data["end_date"],
            data["user"]
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.exception("Error in /api/borrow")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/get_returnable", methods=["GET"])
def api_get_returnable():
    try:
        logger.debug("API get_returnable called")
        items = get_returnable_list()
        return jsonify({"status": "ok", "items": items})
    except Exception as e:
        logger.exception("Error in /api/get_returnable")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/return", methods=["POST"])
def api_return():
    try:
        data = request.json
        logger.debug(f"API return called with data={data}")
        user = write_return(data["jig"], data["return_date"])
        return jsonify({"status": "ok", "user": user})
    except Exception as e:
        logger.exception("Error in /api/return")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/comment", methods=["POST"])
def api_comment():
    try:
        data = request.json
        logger.debug(f"API comment called with data={data}")
        write_comment(data["user"], data["content"])
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.exception("Error in /api/comment")
        return jsonify({"status": "error", "message": str(e)})


# ---------------------------
# RUN APP
# ---------------------------

if __name__ == "__main__":
    logger.debug("Starting Flask server with SocketIO")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
