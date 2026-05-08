"""
基本 smoke test:app 能起、health endpoint 正常。
"""


class TestHealth:
    async def test_app_starts(self, client):
        # FastAPI default OpenAPI schema 路徑
        r = await client.get("/openapi.json")
        assert r.status_code == 200
        body = r.json()
        assert "paths" in body

    async def test_unauth_protected_endpoint_rejected(self, client):
        # 沒帶 token 應該得到 401 或 422 (FastAPI Header dependency 缺少時)
        r = await client.get("/api/v1/customers/eligibility")
        assert r.status_code in (401, 422)
