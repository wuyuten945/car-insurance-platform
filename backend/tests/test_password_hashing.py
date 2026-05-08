"""
密碼雜湊 + 透明 bcrypt 升級測試。
"""
import pytest

from app.core.admin_auth import hash_password, verify_password, needs_rehash
from app.services.auth_service import _hash_password, _verify_password
from app.services.auth_service import needs_rehash as svc_needs_rehash


class TestAdminPasswordHashing:
    def test_new_hash_is_bcrypt(self):
        h = hash_password("hello1234")
        assert h.startswith("$2"), "新雜湊應為 bcrypt 格式"
        assert len(h) > 50, "bcrypt 雜湊長度應該夠長"

    def test_verify_new_bcrypt(self):
        h = hash_password("hello1234")
        assert verify_password("hello1234", h) is True
        assert verify_password("wrong", h) is False

    def test_verify_legacy_sha256(self):
        """舊 'salt:digest' 格式必須仍可驗證。"""
        import hashlib
        salt = "abcd1234abcd1234"
        digest = hashlib.sha256((salt + "hello1234").encode()).hexdigest()
        legacy_hash = f"{salt}:{digest}"
        assert verify_password("hello1234", legacy_hash) is True
        assert verify_password("wrong", legacy_hash) is False

    def test_needs_rehash_legacy(self):
        legacy_hash = "abcd:" + "0" * 64
        assert needs_rehash(legacy_hash) is True

    def test_needs_rehash_bcrypt_no(self):
        h = hash_password("hello1234")
        assert needs_rehash(h) is False


class TestCustomerPasswordHashing:
    def test_new_hash_is_bcrypt(self):
        h = _hash_password("hello1234")
        assert h.startswith("$2")

    def test_verify_legacy_dollarsign(self):
        """客戶舊格式是 'salt$digest' (dollar sign)。"""
        import hashlib
        salt = "abcd1234abcd1234"
        digest = hashlib.sha256((salt + "hello1234").encode()).hexdigest()
        legacy = f"{salt}${digest}"
        assert _verify_password("hello1234", legacy) is True
        assert _verify_password("wrong", legacy) is False

    def test_needs_rehash_works_for_customer_format(self):
        legacy = "abcd$" + "0" * 64
        assert svc_needs_rehash(legacy) is True
        assert svc_needs_rehash(_hash_password("x")) is False

    def test_empty_hash_rejected(self):
        assert _verify_password("anything", "") is False
        assert _verify_password("anything", None) is False
