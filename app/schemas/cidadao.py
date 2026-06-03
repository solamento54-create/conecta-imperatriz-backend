"""Schemas de Cidadão."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, date
from typing import Optional
from validate_docbr import CPF


class CidadaoCreate(BaseModel):
    """Cadastro de novo cidadão pelo app."""
    cpf: str = Field(min_length=11, max_length=14)
    nome_completo: str = Field(min_length=3, max_length=150)
    email: EmailStr
    telefone: str = Field(min_length=10, max_length=20)
    senha: str = Field(min_length=6, max_length=100)
    data_nascimento: Optional[date] = None
    aceite_lgpd: bool = Field(description="Cidadão DEVE aceitar termos LGPD")

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        cpf = CPF()
        if not cpf.validate(v):
            raise ValueError("CPF inválido")
        return cpf.mask(v.replace(".", "").replace("-", ""))

    @field_validator("aceite_lgpd")
    @classmethod
    def validar_aceite(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Aceite dos termos LGPD é obrigatório")
        return v


class CidadaoUpdate(BaseModel):
    """Atualização de dados pelo próprio cidadão."""
    nome_completo: Optional[str] = Field(default=None, min_length=3, max_length=150)
    telefone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    data_nascimento: Optional[date] = None


class CidadaoResponse(BaseModel):
    """Resposta da API (esconde senha_hash, etc)."""
    id: int
    cpf: str
    nome_completo: str
    email: str
    telefone: str
    data_nascimento: Optional[date]
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
