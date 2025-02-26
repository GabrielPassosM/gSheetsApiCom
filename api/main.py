import base64
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


load_dotenv()


app = FastAPI(
    title="My communicator for the google sheets API",
    version="1.0.0"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CREDENTIALS_DICT = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": base64.b64decode(os.getenv("GOOGLE_PRIVATE_KEY_BASE64")).decode(),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
}

CREDENTIALS = Credentials.from_service_account_info(CREDENTIALS_DICT, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(CREDENTIALS)


@app.get("/")
def read_root():
    return {"message": "Hello, broski!"}


@app.post("/add-row/{sheet_id}/{add_timestamp}", status_code=200)
@limiter.limit("10/minute")
def add_row(
    request: Request,  # DONT remove - used by the limiter
    sheet_id: str,
    add_timestamp: bool,
    row_info: dict,
) -> None:
    sheet = gc.open_by_key(sheet_id).sheet1
    row_info = list(row_info.values())
    if add_timestamp:
        row_info.append(str(datetime.now(timezone.utc)))
    sheet.append_row(row_info)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
