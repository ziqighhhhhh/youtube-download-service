import pytest
from pydantic import ValidationError

from schemas.all import RechargeRequest, TaskSubmit, UserRegister


def test_register_password_has_minimum_length():
    with pytest.raises(ValidationError):
        UserRegister(email="user@example.com", password="short")


def test_task_url_must_be_http_youtube_url():
    with pytest.raises(ValidationError):
        TaskSubmit(url="file:///etc/passwd")

    with pytest.raises(ValidationError):
        TaskSubmit(url="https://example.com/watch?v=abc")

    valid = TaskSubmit(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert str(valid.url).startswith("https://www.youtube.com/")


def test_recharge_amount_must_be_positive():
    with pytest.raises(ValidationError):
        RechargeRequest(amount=-1)
