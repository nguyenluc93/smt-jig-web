# sheets.py
import os
import pickle
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ============================
# GOOGLE OAUTH LOGIN
# ============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_client():
    creds = None

    # Load token nếu có
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # Nếu chưa có token hoặc token hết hạn
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Lưu token
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return gspread.authorize(creds)


client = get_gsheet_client()

# ============================
# CONFIG
# ============================
SHEET_ID = "16VAlFUV_r41rBwW7TqUWMNMmHjKB8EX6l7ef9PZL5Hw"
book = client.open_by_key(SHEET_ID)

# Map category → sheet name
CATEGORY_SHEETS = {
    "HEAD": "ヘッドOH用",
    "LINEAR": "その他交換用",
    "MOVE": "移設/新規納品用",
}

CONSUMABLE_SHEET = "消耗品管理"

# Cột trong sheet JIG
COL_JIG = 1
COL_DESC = 2
COL_STATUS = 3
COL_USER = 4
COL_NOTE = 5
COL_RESERVE_DATE = 6     # 借出予定日
COL_BORROW_DATE = 7      # 借出日
COL_RETURN_DATE = 8      # 返却予定日


# ============================
# JIG FUNCTIONS
# ============================
def get_jig_rows(category):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    values = ws.get_all_values()

    rows = []
    for idx, row in enumerate(values[1:], start=2):
        jig = row[COL_JIG - 1]
        desc = row[COL_DESC - 1]
        status = row[COL_STATUS - 1]

        # Chỉ hiển thị JIG đang "在庫" hoặc "予約"
        if status != "貸出中":
            rows.append({
                "category": category,
                "row": idx,
                "jig": jig,
                "desc": desc,
                "status": status,
                "user": row[COL_USER - 1],
                "borrow_date": row[COL_BORROW_DATE - 1],
                "return_date": row[COL_RETURN_DATE - 1],
            })
    return rows


def get_returnable_rows():
    rows = []
    for category, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()

        for idx, row in enumerate(values[1:], start=2):
            status = row[COL_STATUS - 1]
            if status == "貸出中":
                rows.append({
                    "category": category,
                    "row": idx,
                    "jig": row[COL_JIG - 1],
                    "desc": row[COL_DESC - 1],
                    "user": row[COL_USER - 1],
                    "borrow_date": row[COL_BORROW_DATE - 1],
                    "return_date": row[COL_RETURN_DATE - 1],
                })
    return rows


# ============================
# UPDATE FUNCTIONS
# ============================
def update_status(category, row, status):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_STATUS, status)

def update_user(category, row, user):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_USER, user)

def update_note(category, row, note):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_NOTE, note)

def update_reserve_date(category, row, date):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_RESERVE_DATE, date)

def update_borrow_date(category, row, date):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_BORROW_DATE, date)

def update_return_date(category, row, date):
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_RETURN_DATE, date)
# ============================
# CONSUMABLE FUNCTIONS (FINAL)
# ============================

def get_consumables():
    """
    Đọc sheet '消耗品管理'
    Trả về list:
    [
        {"row": 2, "name": "パックリーナー(本)", "stock": 4},
        {"row": 3, "name": "インシュロック100(パック)", "stock": 3},
        ...
    ]
    """
    ws = book.worksheet(CONSUMABLE_SHEET)
    values = ws.get_all_values()

    results = []
    for idx, row in enumerate(values[1:], start=2):  # bỏ dòng tiêu đề
        name = row[0].strip()
        qty_raw = row[1].strip()

        try:
            qty = int(qty_raw)
        except:
            qty = 0

        results.append({
            "row": idx,
            "name": name,
            "stock": qty
        })

    return results


def update_consumable_stock(row, new_stock):
    """
    Cập nhật tồn kho tại dòng 'row' cột B (在庫数)
    """
    ws = book.worksheet(CONSUMABLE_SHEET)
    ws.update_cell(row, 2, new_stock)
