"""Schemas de Secretaria."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SecretariaCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    descricao: Optional[str] = None
    email_contato: Optional[EmailStr] = None
    telefone: Optional[str] = Field(default=None, max_length=20)
    icone: Optional[str] = Field(default=None, max_length=50)
    cor: Optional[str] = Field(default="#0D2CBC", max_length=7)


class SecretariaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descricao: Optional[str] = None
    email_contato: Optional[EmailStr] = None
    telefone: Optional[str] = None
    icone: Optional[str] = None
    cor: Optional[str] = None
    ativo: Optional[bool] = None


class SecretariaResponse(BaseModel):
    id: int
    nome: str
    slug: str
    descricao: Optional[str]
    email_contato: Optional[str]
    telefone: Optional[str]
    icone: Optional[str]
    cor: Optional[str]
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
