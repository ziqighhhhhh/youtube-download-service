import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from services import billing_service, cookie_service


class Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class Db:
    def __init__(self, result=None):
        self.result = result
        self.committed = False

    def query(self, model):
        return Query(self.result)

    def commit(self):
        self.committed = True


class User:
    id = 1
    cookie_text = "old"
    cookie_updated_at = None


def test_save_cookie_does_not_store_plaintext_in_db(monkeypatch):
    user = User()
    temp_dir = Path("data") / f"youtube-download-service-tests-{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cookie_service, "USERS_DIR", temp_dir)

    try:
        assert cookie_service.save_cookie(Db(user), 1, "sensitive-cookie")

        assert user.cookie_text is None
        assert (temp_dir / "1" / "cookies.txt").read_text(encoding="utf-8") == "sensitive-cookie"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_add_balance_rejects_negative_amount():
    with pytest.raises(ValueError, match="greater than 0"):
        billing_service.add_balance(Db(), 1, -1)
