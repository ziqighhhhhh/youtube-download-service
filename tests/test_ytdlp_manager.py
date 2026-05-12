import asyncio
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from services.ytdlp_manager import YtDlpError, YtDlpManager


def test_count_from_playlist_json():
    payload = b'{"entries":[{"id":"1"},{"id":"2"}]}'

    assert YtDlpManager._count_from_json(payload) == 2


def test_count_from_single_video_json():
    payload = b'{"id":"abc","title":"video"}'

    assert YtDlpManager._count_from_json(payload) == 1


def test_count_from_empty_json_returns_none():
    assert YtDlpManager._count_from_json(b"NA") is None


def test_temp_cookie_file_writes_plaintext_and_deletes():
    created = []
    temp_dir = Path("data") / f"youtube-download-service-ytdlp-tests-{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        with YtDlpManager._temporary_cookie_file("cookie=value", temp_dir) as path:
            created.append(path)
            assert path.exists()
            assert path.read_text(encoding="utf-8") == "cookie=value"

        assert not created[0].exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_video_count_raises_on_ytdlp_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout=b"", stderr=b"ERROR: login required")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(YtDlpError, match="login required"):
        asyncio.run(YtDlpManager().get_video_count("https://www.youtube.com/watch?v=x"))


def test_get_video_count_uses_cookies(monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args[0], 0, stdout=b'{"entries":[{"id":"1"},{"id":"2"},{"id":"3"}]}', stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    count = asyncio.run(
        YtDlpManager().get_video_count(
            "https://www.youtube.com/playlist?list=abc",
            cookie_text="cookie=value",
        )
    )

    assert count == 3
    assert "--cookies" in calls[0][0]
