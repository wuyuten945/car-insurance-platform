from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "資源不存在"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "未授權"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "權限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "請求無效"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class RateLimitError(HTTPException):
    def __init__(self, detail: str = "請求過於頻繁，請稍後再試"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
