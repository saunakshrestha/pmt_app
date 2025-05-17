from ninja import Schema


class TokenResponse(Schema):
    access: str
    refresh: str

class TokenOnlyResponse(Schema):
    access: str

class TokenInput(Schema):
    email: str
    password: str

class RefreshInput(Schema):
    refresh: str

class VerifyInput(Schema):
    token: str