from flask import Flask, render_template, request, jsonify
from sheets import (
    get_jig_list,
    get_returnable_list,
    write_borrow,
    write_return,
    write_consumables,
    get_logs,
    write_comment,   # ⬅️ mới thêm
    get_consumables  # nếu bạn đã tách riêng, giữ lại
)

app = Flask(__name__)

# ---------------------------
# ROUTES (HTML PAGES)
# ---------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/borrow")
def borrow_page():
    return render_template("borrow.html")

@app.route("/return")
def return_page():
    return render_template("return.html")

@app.route("/consumables")
def consumables_page():
    return render_template("consumables.html")

@app.route("/logs")
def logs_page():
    return render_template("logs.html")

@app.route("/comment")
def comment_page():
    return render_template("comment.html")


# ---------------------------
# API ENDPOINTS
# ---------------------------

@app.route("/api/jigs")
def api_jigs():
    category = request.args.get("category", "")
    items = get_jig_list(category)
    return jsonify({"items": items})


@app.route("/api/returnable")
def api_returnable():
    items = get_returnable_list()
    return jsonify({"items": items})


@app.route("/api/borrow-final", methods=["POST"])
def api_borrow_final():
    data = request.get_json()
    jigs = data["jigs"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    user = data["user"]

    for jig in jigs:
        write_borrow(jig, start_date, end_date, user)

    return jsonify({"status": "ok"})


@app.route("/api/return-final", methods=["POST"])
def api_return_final():
    data = request.get_json()
    jigs = data["jigs"]
    return_date = data["return_date"]

    borrow_info = {}
    for jig in jigs:
        user = write_return(jig, return_date)
        borrow_info[jig] = {"user": user}

    return jsonify({
        "status": "ok",
        "borrow_info": borrow_info
    })


@app.route("/api/consumables")
def api_consumables():
    items = get_consumables()
    return jsonify({"items": items})


@app.route("/api/consumables-final", methods=["POST"])
def api_consumables_final():
    data = request.get_json()
    jig = data["jig"]
    user = data["user"]
    items = data["items"]

    if len(items) > 0:
        write_consumables(jig, user, items)

    return jsonify({"status": "ok"})


@app.route("/api/logs")
def api_logs():
    items = get_logs()
    return jsonify({"items": items})


@app.route("/api/comment", methods=["POST"])
def api_comment():
    data = request.get_json()
    user = data["user"]
    content = data["content"]

    write_comment(user, content)
    return jsonify({"status": "ok"})


# ---------------------------
# RUN
# ---------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
