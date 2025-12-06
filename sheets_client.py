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

    # TODO: create a result = service.spreadsheets().values().get(...)
    # TODO: return the rows
