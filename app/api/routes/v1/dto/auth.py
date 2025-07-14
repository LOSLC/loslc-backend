from pydantic import BaseModel, EmailStr


class RegisterRequestDTO(BaseModel):
    username: str
    email: EmailStr
    password: str
    password_confirm: str
    name: str


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str


class UserResponseDTO(BaseModel):
    id: str
    username: str
    email: str
    name: str

    class Config:
        from_attributes = True


class AccountVerificationDTO(BaseModel):
    token: str
    session_id: str


class LoginVerificationDTO(BaseModel):
    token: str
    session_id: str
