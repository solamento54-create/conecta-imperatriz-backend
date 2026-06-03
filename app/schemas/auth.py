"""Schemas de autenticação."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login (cidadão ou usuário)."""
    email: EmailStr
    senha: str = Field(min_length=6, max_length=100)


class TokenResponse(BaseModel):
    """Resposta do login bem-sucedido."""
    access_token: str
    token_type: str = "bearer"
    tipo: str        # 'cidadao' ou 'usuario'
    nome: str
    perfil: Optional[str] = None  # só para usuários


class RecuperarSenhaRequest(BaseModel):
    email: EmailStr


class ResetarSenhaRequest(BaseModel):
    token: str
    nova_senha: str = Field(min_length=6, max_length=100)
