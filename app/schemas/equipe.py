"""Schemas de Equipe."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class EquipeCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    responsavel_nome: str = Field(min_length=3, max_length=150)
    responsavel_telefone: Optional[str] = Field(default=None, max_length=20)
    responsavel_email: Optional[EmailStr] = None
    secretaria_id: int


class EquipeUpdate(BaseModel):
    nome: Optional[str] = None
    responsavel_nome: Optional[str] = None
    responsavel_telefone: Optional[str] = None
    responsavel_email: Optional[EmailStr] = None
    secretaria_id: Optional[int] = None
    ativo: Optional[bool] = None


class EquipeResponse(BaseModel):
    id: int
    nome: str
    responsavel_nome: str
    responsavel_telefone: Optional[str]
    responsavel_email: Optional[str]
    secretaria_id: int
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
