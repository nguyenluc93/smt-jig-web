from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

app = Flask(__name__)

# ============================
# GOOGLE SHEETS SETUP
# ============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)

SPREADSHEET_NAME = "JIG_management"
book = client.open(SPREADSHEET_NAME)

CATEGORY_SHEETS = {
    "HEAD": "ヘッドOH用",
    "MOVE": "移設/新規納品用",
    "LINEAR": "その他交換用"
}

# ============================
# IMPORT SHEETS LOGIC
# ============================
from sheets import (
    find_jig,
    get_jigs_by_category,
    get_returnable_rows,
    update_status,
    update_user,
    update_borrow_date,
    update_return_date,
    get_consumables,
    update_consumable_stock,
    log_consumable,
    log_history,
    get_logs
)

# ============================
# ROUTES (PAGES)
# ============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/return")
def return_page():
    return render_template("return.html")

@app.route("/consumables")
def consumables_page():
    return render_template("consumables.html")

@app.route("/logs")
def logs_page():
    return render_template("logs.html")

# ============================
# API: JIG LIST BY CATEGORY (BORROW)
# ============================
@app.route("/api/jigs")
def api_jigs():
    category = request.args.get("category", "HEAD")
    items = get_jigs_by_category(category)
    return jsonify({
        "category": category,
        "category_name": CATEGORY_SHEETS[category],
        "items": items
    })

# ============================
# API: BORROW FINAL
# ============================
@app.route("/api/borrow-final", methods=["POST"])
def api_borrow_final():
    data = request.json
    jig_list = data["jigs"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    user = data["user"]

    results = []

    for jig_id in jig_list:
        category, row, row_data = find_jig(jig_id)
        if category:
            update_status(category, row, "貸出中")
            update_user(category, row, user)
            update_borrow_date(category, row, start_date)
            update_return_date(category, row, end_date)

            # log lịch sử mượn
            log_history(jig_id, user, start_date, end_date)

            results.append(f"{jig_id} を貸出しました。")

    return jsonify({"results": results})

# ============================
# API: RETURNABLE LIST
# ============================
@app.route("/api/returnable")
def api_returnable():
    items = get_returnable_rows()
    return jsonify({"items": items})

# ============================
# API: RETURN FINAL
# ============================
@app.route("/api/return-final", methods=["POST"])
def api_return_final():
    data = request.json
    jig_list = data["jigs"]
    return_date = data["return_date"]

    results = []
    borrow_info = {}

    for jig_id in jig_list:
        category, row, row_data = find_jig(jig_id)
        if category:
            # row_data: [id, desc, status, user, borrow_date, return_date, ...]
            user = row_data[3]
            borrow_date = row_data[4]

            borrow_info[jig_id] = {
                "user": user,
                "borrow_date": borrow_date,
                "return_date": return_date
            }

            update_status(category, row, "在庫")
            update_user(category, row, "")
            update_return_date(category, row, return_date)

            # log lịch sử trả
            log_history(jig_id, user, borrow_date, return_date)

            results.append(f"{jig_id} を返却しました。")

    consumables = get_consumables()

    return jsonify({
        "results": results,
        "consumables": consumables,
        "borrow_info": borrow_info
    })

# ============================
# API: CONSUMABLES LIST
# ============================
@app.route("/api/consumables")
def api_consumables():
    return jsonify({"items": get_consumables()})

# ============================
# API: CONSUMABLES FINAL
# (CHỈ CẬP NHẬT SHEET 消耗品 + LOG TIÊU HAO RIÊNG)
# ============================
@app.route("/api/consumables-final", methods=["POST"])
def api_consumables_final():
    data = request.json
    user = data["user"]
    jig_id = data["jig"]
    items = data["items"]

    for item in items:
        name = item["name"]
        qty = int(item["qty"])

        # cập nhật tồn kho tiêu hao
        update_consumable_stock(name, qty)
        # log tiêu hao riêng (không liên quan ログ履歴)
        log_consumable(name, qty, user, jig_id)

    return jsonify({"status": "ok"})

# ============================
# API: LOGS (LỊCH SỬ MƯỢN/TRẢ)
# ============================
@app.route("/api/logs")
def api_logs():
    items = get_logs()
    return jsonify({"items": items})

# ============================
# MAIN
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
