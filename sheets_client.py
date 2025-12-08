import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# TODO: Update this after you have your Sheet ID
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

def get_service():
    """
    Creates a Google Sheets API client using the service account.
    """
    creds = Credentials.from_service_account_file(
        "creds/sa.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    return service


def read_watchlist():

    service = get_service()

    result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="Watchlist!A2:C"
    ).execute()               # 2) call the API

    rows = result.get("values", [])  # 3) safely get the rows list
    return rows

def write_demo_value(value: str):
    """
    Writes a single value into cell D2 of the Watchlist sheet.
    This is just for testing that writes work.
    """
    service = get_service()

    range_name = "Watchlist!D2"  # column D, row 2
    body = {
        "values": [[value]]  # 2D array: list of rows, each row is a list of cells
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()

    return result


def write_watchlist_update(
    row_index: int,
    current_price,
    previous_close,
    day_change_pct,
    ai_summary: str,
    timestamp: str,
):
    """
    Writes metrics + AI summary into columns D–H for a given row in the Watchlist sheet.

    row_index is the actual sheet row number (2 = first data row).

    D = CurrentPrice
    E = PreviousClose
    F = DayChangePct
    G = AI_Summary
    H = LastUpdated
    """
    service = get_service()

    range_name = f"Watchlist!D{row_index}:H{row_index}"
    body = {
        "values": [[current_price, previous_close, day_change_pct, ai_summary, timestamp]]
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body,
    ).execute()

    return result

    # TODO: create a result = service.spreadsheets().values().get(...)
    # TODO: return the rows
