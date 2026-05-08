from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import decode_token, is_token_blacklisted
from app.exceptions import UnauthorizedError


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("無效的授權標頭")

    token = authorization[7:]

    if await is_token_blacklisted(token):
        raise UnauthorizedError("Token 已失效")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("無效或過期的 Token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedError("使用者不存在或已停用")

    # Token version 檢查:密碼變更時 user.token_version 會 +1,所有舊 token 立刻失效
    token_tv = int(payload.get("tv", 0))
    if token_tv != int(user.token_version or 0):
        raise UnauthorizedError("Token 已失效,請重新登入")

    return user
