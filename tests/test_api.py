from fastapi.testclient import TestClient
from api.main import app
from consts import TEST_SHEEET_ID


client = TestClient(app)


def test_add_row():
    # success - 200
    data = {
        "sheet_id": TEST_SHEEET_ID,
        "columns": {
            "Name": "aaaa",
            "Email": "aaa@gmail.com",
            "Phone": "99999999",
        },
    }
    response = client.post("/add-row/true", json=data)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # More columns than allowed - 404
    data = {
        "sheet_id": TEST_SHEEET_ID,
        "columns": {
            "Name": "aaaa",
            "Email": "aaa@gmail.com",
            "Phone": "99999999",
            "extraColumn": "value",
        },
    }
    response = client.post("/add-row/true", json=data)
    assert response.status_code == 404
