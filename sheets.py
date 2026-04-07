# sheets.py
import os
import pickle
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime

# ============================
# GOOGLE LOGIN
# ============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_client():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return gspread.authorize(creds)


client = get_gsheet_client()

# ============================
# CONFIG
# ============================
SHEET_ID = "16VAlFUV_r41rBwW7TqUWMNMmHjKB8EX6l7ef9PZL5Hw"
book = client.open_by_key(SHEET_ID)

CATEGORY_SHEETS = {
    "HEAD": "ヘッドOH用",
    "LINEAR": "その他交換用",
    "MOVE": "移設/新規納品用",
}

CONSUMABLE_SHEET = "消耗品管理"

# Column index
COL_JIG = 1
COL_DESC = 2
COL_STATUS = 3
COL_USER = 4
COL_NOTE = 5
COL_RESERVE_DATE = 6
COL_BORROW_DATE = 7
COL_RETURN_DATE = 8


# ============================
# HELPER FUNCTIONS
# ============================
def find_jig(jig_id):
    """
    Tìm JIG trong tất cả category.
    Trả về (category, row, row_data) hoặc (None, None, None)
    """
    for category, sheet_name in CATEGORY_SHEETS.items():
        ws = book.worksheet(sheet_name)
        values = ws.get_all_values()

        for idx, row in enumerate(values[1:], start=2):
            if row[COL_JIG - 1] == jig_id:
                return category, idx, row

    return None, None, None


def today():
    return datetime.now().strftime("%Y/%m/%d")


# ============================
# BORROW
# ============================
def borrow_jig(jig_id, qty):
    category, row, row_data = find_jig(jig_id)

    if not category:
        return False, f"JIG ID {jig_id} は存在しません。"

    status = row_data[COL_STATUS - 1]

    if status == "貸出中":
        return False, f"JIG {jig_id} は既に貸出中です。"

    # Update status
    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_STATUS, "貸出中")
    ws.update_cell(row, COL_USER, "WEB USER")
    ws.update_cell(row, COL_BORROW_DATE, today())
    ws.update_cell(row, COL_RETURN_DATE, "")
    ws.update_cell(row, COL_RESERVE_DATE, "")

    return True, (
        f"【JIG 借用 完了】\n"
        f"JIG ID: {jig_id}\n"
        f"数量: {qty}\n"
        f"借用日: {today()}"
    )


# ============================
# RETURN
# ============================
def return_jig(jig_id, qty):
    category, row, row_data = find_jig(jig_id)

    if not category:
        return False, f"JIG ID {jig_id} は存在しません。"

    status = row_data[COL_STATUS - 1]

    if status != "貸出中":
        return False, f"JIG {jig_id} は貸出中ではありません。"

    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_STATUS, "在庫")
    ws.update_cell(row, COL_USER, "")
    ws.update_cell(row, COL_RETURN_DATE, today())

    return True, (
        f"【JIG 返却 完了】\n"
        f"JIG ID: {jig_id}\n"
        f"返却数量: {qty}\n"
        f"返却日: {today()}"
    )


# ============================
# RESERVE
# ============================
def reserve_jig(jig_id, qty):
    category, row, row_data = find_jig(jig_id)

    if not category:
        return False, f"JIG ID {jig_id} は存在しません。"

    status = row_data[COL_STATUS - 1]

    if status == "貸出中":
        return False, f"JIG {jig_id} は貸出中のため予約できません。"

    ws = book.worksheet(CATEGORY_SHEETS[category])
    ws.update_cell(row, COL_STATUS, "予約")
    ws.update_cell(row, COL_USER, "WEB USER")
    ws.update_cell(row, COL_RESERVE_DATE, today())

    return True, (
        f"【JIG 予約 完了】\n"
        f"JIG ID: {jig_id}\n"
        f"数量: {qty}\n"
        f"予約日: {today()}"
    )


# ============================
# CONSUMABLES (giữ nguyên)
# ============================
def get_consumables():
    ws = book.worksheet(CONSUMABLE_SHEET)
    values = ws.get_all_values()

    results = []
    for idx, row in enumerate(values[1:], start=2):
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
    ws = book.worksheet(CONSUMABLE_SHEET)
    ws.update_cell(row, 2, new_stock)
