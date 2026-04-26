import gspread
from google.oauth2.service_account import Credentials
import os
import json

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

def get_sheet_client():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)

def get_properties(sheet_id: str, query: str = "") -> str:
    client = get_sheet_client()
    sh = client.open_by_key(sheet_id)
    worksheet = sh.worksheet("ობიექტები")
    records = worksheet.get_all_records()

    available = [r for r in records if r.get("სტატუსი") == "ხელმისაწვდომი"]

    query_lower = query.lower()
    location_keywords = [
        "ვაკე", "საბურთალო", "ისანი", "გლდანი",
        "დიდუბე", "მთაწმინდა", "ნაძალადევი", "სამგორი"
    ]
    for loc in location_keywords:
        if loc in query_lower:
            filtered = [
                r for r in available
                if loc in str(r.get("ადგილმდებარეობა", "")).lower()
            ]
            if filtered:
                available = filtered
            break

    for num in ["1", "2", "3", "4", "5"]:
        if f"{num} ოთახ" in query_lower or f"{num}-ოთახ" in query_lower:
            filtered = [r for r in available if str(r.get("ოთახები", "")) == num]
            if filtered:
                available = filtered
            break

    if not available:
        return "ამ კრიტერიუმებით ხელმისაწვდომი ობიექტი არ მოიძებნა"

    result = []
    for r in available:
        result.append(
            f"ID:{r['ID']} | {r['სახელი']} | {r['ტიპი']} | "