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
    update_return_date
)

# ============================
# ROUTES
# ============================
@app.route("/")
def home():
    return render_template("index.html")

# GET JIG LIST BY CATEGORY
@app.route("/api/jigs")
def api_jigs():
    category = request.args.get("category")
    items = get_jigs_by_category(category)
    return jsonify({
        "category": category,
        "category_name": CATEGORY_SHEETS[category],
        "items": items
    })

# BORROW FINAL
@app.route("/api/borrow-final", methods=["POST"])
def api_borrow_final():
    data = request.json
    jig_list = data["jigs"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    results = []

    for jig_id in jig_list:
        category, row, row_data = find_jig(jig_id)
        if category:
            update_status(category, row, "貸出中")
            update_user(category, row, "WEB_USER")
            update_borrow_date(category, row, start_date)
            update_return_date(category, row, end_date)
            results.append(f"{jig_id} を貸出しました。")

    return jsonify({"results": results})

# RETURNABLE LIST
@app.route("/api/returnable")
def api_returnable():
    items = get_returnable_rows()
    return jsonify({"items": items})

# RETURN FINAL
@app.route("/api/return-final", methods=["POST"])
def api_return_final():
    data = request.json
    jig_list = data["jigs"]
    return_date = data["return_date"]

    results = []

    for jig_id in jig_list:
        category, row, row_data = find_jig(jig_id)
        if category:
            update_status(category, row, "在庫")
            update_user(category, row, "")
            update_return_date(category, row, return_date)
            results.append(f"{jig_id} を返却しました。")

    return jsonify({"results": results})

# STATUS LIST
@app.route("/api/status")
def api_status():
    items = []
    for category, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()
        for row in values[1:]:
            items.append({
                "id": row[0],
                "desc": row[1],
                "status": row[2],
                "user": row[3],
                "borrow": row[6],
                "return": row[7]
            })
    return jsonify({"items": items})

# MAIN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
