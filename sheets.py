import gspread
from datetime import datetime

from oauth2client.service_account import ServiceAccountCredentials
import json, os

# dùng chung với app.py: GOOGLE_CREDENTIALS + SPREADSHEET_NAME
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

CONSUMABLE_SHEET = "消耗品"
CONSUMABLE_LOG_SHEET = "消耗品ログ"
LOG_HISTORY_SHEET = "ログ履歴"

# ============================
# JIG HELPERS
# ============================
def find_jig(jig_id):
    """
    Tìm JIG trong các sheet category.
    Trả về: (category_key, row_index, row_values) hoặc (None, None, None)
    """
    for key, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()
        for i, row in enumerate(values[1:], start=2):
            if row[0] == jig_id:
                return key, i, row
    return None, None, None

def get_jigs_by_category(category_key):
    """
    Lấy danh sách JIG có trạng thái '在庫' trong 1 category.
    """
    sheet_name = CATEGORY_SHEETS[category_key]
    ws = book.worksheet(sheet_name)
    values = ws.get_all_values()[1:]

    items = []
    for row in values:
        jig_id = row[0]
        desc = row[1]
        status = row[2]
        if status == "在庫":
            items.append({
                "id": jig_id,
                "desc": desc
            })
    return items

def get_returnable_rows():
    """
    Lấy danh sách JIG đang '貸出中' từ tất cả category.
    """
    items = []
    for key, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()[1:]
        for row in values:
            jig_id = row[0]
            desc = row[1]
            status = row[2]
            user = row[3]
            if status == "貸出中":
                items.append({
                    "id": jig_id,
                    "desc": desc,
                    "user": user,
                    "category": key
                })
    return items

def update_status(category_key, row, status):
    ws = book.worksheet(CATEGORY_SHEETS[category_key])
    ws.update_cell(row, 3, status)  # col C

def update_user(category_key, row, user):
    ws = book.worksheet(CATEGORY_SHEETS[category_key])
    ws.update_cell(row, 4, user)  # col D

def update_borrow_date(category_key, row, date_str):
    ws = book.worksheet(CATEGORY_SHEETS[category_key])
    ws.update_cell(row, 5, date_str)  # col E

def update_return_date(category_key, row, date_str):
    ws = book.worksheet(CATEGORY_SHEETS[category_key])
    ws.update_cell(row, 6, date_str)  # col F

# ============================
# CONSUMABLES
# ============================
def get_consumables():
    """
    Lấy danh sách tiêu hao từ sheet 消耗品.
    Giả định: col A = name, col B = stock
    """
    ws = book.worksheet(CONSUMABLE_SHEET)
    values = ws.get_all_values()[1:]

    items = []
    for row in values:
        name = row[0]
        stock = row[1]
        items.append({
            "name": name,
            "stock": stock
        })
    return items

def update_consumable_stock(name, used_qty):
    """
    Trừ tồn kho trong sheet 消耗品.
    """
    ws = book.worksheet(CONSUMABLE_SHEET)
    values = ws.get_all_values()
    for i, row in enumerate(values[1:], start=2):
        if row[0] == name:
            try:
                current = int(row[1])
            except:
                current = 0
            new_val = current - used_qty
            ws.update_cell(i, 2, new_val)
            break

def log_consumable(name, qty, user, jig_id):
    """
    Ghi log tiêu hao vào sheet 消耗品ログ.
    """
    try:
        ws = book.worksheet(CONSUMABLE_LOG_SHEET)
    except:
        ws = book.add_worksheet(CONSUMABLE_LOG_SHEET, rows=1000, cols=10)
        ws.append_row(["日時", "消耗品", "数量", "ユーザー", "JIG"])

    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    ws.append_row([now, name, qty, user, jig_id])

# ============================
# LOG LỊCH SỬ MƯỢN/TRẢ
# ============================
def log_history(jig, user, borrow_date, return_date):
    """
    Ghi lịch sử mượn/trả vào sheet ログ履歴.
    KHÔNG liên quan đến tiêu hao.
    """
    try:
        ws = book.worksheet(LOG_HISTORY_SHEET)
    except:
        ws = book.add_worksheet(LOG_HISTORY_SHEET, rows=1000, cols=10)
        ws.append_row(["日時", "JIG", "借用者", "借用日", "返却日"])

    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    ws.append_row([now, jig, user, borrow_date, return_date])

def get_logs():
    """
    Lấy toàn bộ lịch sử mượn/trả từ ログ履歴.
    """
    try:
        ws = book.worksheet(LOG_HISTORY_SHEET)
    except:
        return []

    values = ws.get_all_values()[1:]
    items = []
    for row in values:
        items.append({
            "datetime": row[0],
            "jig": row[1],
            "user": row[2],
            "borrow_date": row[3],
            "return_date": row[4]
        })
    return items
