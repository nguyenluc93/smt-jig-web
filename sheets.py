import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------------------------
# GOOGLE SHEETS LOGIN
# ---------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Đọc file JSON local, không dùng ENV
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)

# ---------------------------
# SHEET CONFIG
# ---------------------------

SHEET_ID = "16VAlFUV_r41rBwW7TqUWMNMmHjKB8EX6l7ef9PZL5Hw"

JIG_TABS = [
    "ヘッドOH用",
    "移設/新規納品用",
    "その他交換用"
]

CONSUMABLES_TAB = "消耗品管理"
LOG_TAB = "ログ"
COMMENT_TAB = "comment"

cons_sheet = client.open_by_key(SHEET_ID).worksheet(CONSUMABLES_TAB)
log_sheet = client.open_by_key(SHEET_ID).worksheet(LOG_TAB)
comment_sheet = client.open_by_key(SHEET_ID).worksheet(COMMENT_TAB)


# ---------------------------
# FIND JIG
# ---------------------------

def find_jig(jig_id):
    for tab in JIG_TABS:
        ws = client.open_by_key(SHEET_ID).worksheet(tab)
        data = ws.get_all_records()
        for idx, row in enumerate(data, start=2):
            if row["JIG番号"] == jig_id:
                return ws, idx, row
    return None, None, None


# ---------------------------
# GET JIG LIST
# ---------------------------

def get_jig_list(category):
    items = []
    for tab in JIG_TABS:
        ws = client.open_by_key(SHEET_ID).worksheet(tab)
        data = ws.get_all_records()
        for row in data:
            if row["状態"] == "在庫":
                items.append({
                    "id": row["JIG番号"],
                    "desc": row["説明"]
                })
    return items


# ---------------------------
# GET RETURNABLE LIST
# ---------------------------

def get_returnable_list():
    items = []
    for tab in JIG_TABS:
        ws = client.open_by_key(SHEET_ID).worksheet(tab)
        data = ws.get_all_records()
        for row in data:
            if row["状態"] == "貸出中":
                items.append({
                    "id": row["JIG番号"],
                    "desc": row["説明"],
                    "user": row["使用者"]
                })
    return items


# ---------------------------
# WRITE BORROW
# ---------------------------

def write_borrow(jig, start_date, end_date, user):
    ws, idx, row = find_jig(jig)
    if ws is None:
        return

    ws.update_cell(idx, 3, "貸出中")
    ws.update_cell(idx, 4, user)
    ws.update_cell(idx, 6, start_date)
    ws.update_cell(idx, 7, start_date)
    ws.update_cell(idx, 8, end_date)

    log_sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        jig,
        user,
        start_date,
        "",
        "BORROW"
    ])


# ---------------------------
# WRITE RETURN
# ---------------------------

def write_return(jig, return_date):
    ws, idx, row = find_jig(jig)
    if ws is None:
        return ""

    user = row["使用者"]

    ws.update_cell(idx, 3, "在庫")
    ws.update_cell(idx, 4, "")
    ws.update_cell(idx, 8, return_date)

    log_sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        jig,
        user,
        row["借出日"],
        return_date,
        "RETURN"
    ])

    return user


# ---------------------------
# WRITE COMMENT
# ---------------------------

def write_comment(user, content):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comment_sheet.append_row([
        now,     # 入力日
        user,    # 担当者
        content  # 内容
    ])
