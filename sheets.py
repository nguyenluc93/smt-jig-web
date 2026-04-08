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
