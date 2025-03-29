import base64
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from pydantic import BaseModel, model_validator
from consts import TEST_SHEEET_ID


load_dotenv()


app = FastAPI(title="My communicator for the google sheets API", version="1.0.0")

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

CREDENTIALS = Credentials.from_service_account_info(
    CREDENTIALS_DICT, scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(CREDENTIALS)

SHEETS_ID_PER_ROW_SIZE = {
    3: [
        TEST_SHEEET_ID,
        os.getenv("CORA_SHEET_ID"),
        os.getenv("STELLA_SHEET_ID"),
        os.getenv("GAMALABS_SHEET_ID"),
    ],
}


@dataclass
class AddRowBadRequest(HTTPException):
    status_code: int = 404
    detail: str = "Get out"


class AddRowIn(BaseModel):
    sheet_id: str
    columns: dict

    @model_validator(mode="after")
    def make_validations(self):
        size = len(self.columns)
        if self.sheet_id not in SHEETS_ID_PER_ROW_SIZE.get(size, []):
            raise AddRowBadRequest()

        for value in self.columns.values():
            if not isinstance(value, str) or len(value) > 80:
                raise AddRowBadRequest()

        return self


@app.get("/")
def read_root():
    return {"message": "Hello, broski!"}


@app.post("/add-row/{add_timestamp}", status_code=200)
@limiter.limit("3/minute")
def add_row(
    request: Request,  # DONT remove - used by the limiter
    add_timestamp: bool,
    row_info: AddRowIn,
) -> list[str]:

    row_to_add = list(row_info.columns.values())

    if row_info.sheet_id == TEST_SHEEET_ID:
        return row_to_add

    sheet = gc.open_by_key(row_info.sheet_id).sheet1
    if add_timestamp:
        row_to_add.append(str(datetime.now(timezone.utc)))
    sheet.append_row(row_to_add)

    return row_to_add


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
