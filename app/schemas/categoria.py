"""Schemas de Categoria."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    descricao: Optional[str] = None
    secretaria_id: int
    icone: Optional[str] = Field(default=None, max_length=50)
    cor: Optional[str] = Field(default="#0D2CBC", max_length=7)


class CategoriaUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    secretaria_id: Optional[int] = None
    icone: Optional[str] = None
    cor: Optional[str] = None
    ativo: Optional[bool] = None


class CategoriaResponse(BaseModel):
    id: int
    nome: str
    slug: str
    descricao: Optional[str]
    secretaria_id: int
    icone: Optional[str]
    cor: Optional[str]
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
