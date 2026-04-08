import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# GOOGLE SHEETS SETUP
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
# FIND JIG
# ============================
def find_jig(jig_id):
    for category, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()
        for idx, row in enumerate(values[1:], start=2):
            if row[0] == jig_id:
                return category, idx, row
    return None, None, None

# ============================
# GET JIGS BY CATEGORY
# ============================
def get_jigs_by_category(category):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    values = ws.get_all_values()

    items = []
    for row in values[1:]:
        items.append({
            "id": row[0],
            "desc": row[1],
            "status": row[2]
        })
    return items

# ============================
# GET RETURNABLE ROWS
# ============================
def get_returnable_rows():
    items = []
    for category, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()
        for idx, row in enumerate(values[1:], start=2):
            if row[2] == "貸出中":
                items.append({
                    "id": row[0],
                    "desc": row[1],
                    "user": row[3],
                    "category": category,
                    "row": idx
                })
    return items

# ============================
# UPDATE FUNCTIONS
# ============================
def update_status(category, row, status):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, 3, status)

def update_user(category, row, user):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, 4, user)

def update_borrow_date(category, row, date):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, 7, date)

def update_return_date(category, row, date):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, 8, date)

# ============================
# CONSUMABLES SHEET
# ============================

CONSUMABLE_SHEET = "消耗品"
CONSUMABLE_LOG_SHEET = "消耗品ログ"

# Get consumables list
def get_consumables():
    ws = book.worksheet(CONSUMABLE_SHEET)
    values = ws.get_all_values()[1:]  # skip header

    items = []
    for row in values:
        name = row[0]
        stock = int(row[1]) if row[1].isdigit() else 0
        items.append({"name": name, "stock": stock})
    return items

# Update consumable stock
def update_consumable_stock(name, used_qty):
    ws = book.worksheet(CONSUMABLE_SHEET)
    values = ws.get_all_values()

    for idx, row in enumerate(values[1:], start=2):
        if row[0] == name:
            current = int(row[1]) if row[1].isdigit() else 0
            ws.update_cell(idx, 2, max(current - used_qty, 0))
            return True
    return False

# Log consumable usage
def log_consumable(name, qty, user, jig_id):
    try:
        ws = book.worksheet(CONSUMABLE_LOG_SHEET)
    except:
        ws = book.add_worksheet(CONSUMABLE_LOG_SHEET, rows=1000, cols=10)
        ws.append_row(["日時", "消耗品", "数量", "ユーザー", "JIG"])

    from datetime import datetime
    now = datetime.now().strftime("%Y/%m/%d %H:%M")

    ws.append_row([now, name, qty, user, jig_id])

