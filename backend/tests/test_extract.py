from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_extract_returns_mock_data() -> None:
    response = client.post(
        '/ledgergut/extract',
        files={'file': ('receipt.jpg', b'image-bytes', 'image/jpeg')},
        data={'claimantName': 'Mog'},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload['draft']['vendor'] == 'Goblin Supply Co.'
    assert payload['draft']['claimantName'] == 'Mog'
    assert payload['draft']['purchaseGroup'] == 'Materials'
    assert len(payload['statusMessages']) == 5
