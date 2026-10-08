from pathlib import Path


def test_production_image_copies_canon_resources():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "COPY resources ./resources" in dockerfile
    assert "run_black_office:application" in dockerfile
