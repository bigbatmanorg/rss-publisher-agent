from pathlib import Path


def test_upload_ui_uses_shared_asset_api():
    html = (Path(__file__).parents[1] / "static" / "upload" / "index.html").read_text()
    assert "POST" in html
    assert "/api/v1/assets" in html
    assert "asset_id" in html
    assert "sessionStorage" in html
