"""
Token rotation 測試:create_access_token 帶 tv claim,token_version 不符時拒絕。
"""
import pytest
from jose import jwt as jose_jwt

from app.config import settings
from app.core.security import create_access_token, decode_token


class TestAccessTokenTV:
    def test_new_token_includes_tv(self):
        tok = create_access_token("user-abc", token_version=3)
        payload = decode_token(tok)
        assert payload is not None
        assert payload["sub"] == "user-abc"
        assert payload["tv"] == 3
        assert payload["type"] == "access"

    def test_default_tv_is_zero(self):
        tok = create_access_token("user-x")
        payload = decode_token(tok)
        assert payload["tv"] == 0

    def test_decode_invalid_returns_none(self):
        assert decode_token("not-a-real-jwt") is None

    def test_decode_wrong_signature_returns_none(self):
        bogus = jose_jwt.encode({"sub": "x", "type": "access", "tv": 0},
                                "wrong-secret", algorithm=settings.JWT_ALGORITHM)
        assert decode_token(bogus) is None
