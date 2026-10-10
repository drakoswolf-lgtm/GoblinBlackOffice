from werkzeug.test import Client
from werkzeug.wrappers import Response
from app.office.web import application

def test_cinematic_video_sources_available():
    client = Client(application, Response)
    for name in ("gbo-opening-mobile.mp4", "gbo-opening-desktop.mp4"):
        response = client.get("/canon/startup/" + name)
        assert response.status_code == 200, name
        assert response.headers["Content-Type"].startswith("video/mp4")
        assert response.data[4:8] == b"ftyp"
