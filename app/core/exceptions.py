from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "You do not have access to this resource."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "This resource already exists."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidCredentialsException(HTTPException):
    def __init__(self, detail: str = "Incorrect email or password."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UnsupportedFileException(HTTPException):
    def __init__(self, detail: str = "Only PDF files are supported."):
        super().__init__(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail)


class FileTooLargeException(HTTPException):
    def __init__(self, detail: str = "File exceeds the maximum upload size."):
        super().__init__(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)
