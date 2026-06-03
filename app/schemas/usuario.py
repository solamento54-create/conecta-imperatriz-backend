"""Schemas de Usuário (funcionários)."""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional
from validate_docbr import CPF
from app.models.enums import PerfilUsuario


class UsuarioCreate(BaseModel):
    """Cadastro de novo funcionário (somente admin pode fazer)."""
    cpf: str = Field(min_length=11, max_length=14)
    nome_completo: str = Field(min_length=3, max_length=150)
    email: EmailStr
    telefone: Optional[str] = Field(default=None, max_length=20)
    cargo: Optional[str] = Field(default=None, max_length=100)
    senha: str = Field(min_length=6, max_length=100)
    perfil: PerfilUsuario
    secretaria_id: Optional[int] = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        cpf = CPF()
        if not cpf.validate(v):
            raise ValueError("CPF inválido")
        return cpf.mask(v.replace(".", "").replace("-", ""))

    @model_validator(mode="after")
    def validar_perfil_secretaria(self):
        """Perfil 'secretaria' OBRIGA secretaria_id. Admin/Fiscal proíbe."""
        if self.perfil == PerfilUsuario.SECRETARIA and not self.secretaria_id:
            raise ValueError("Perfil 'secretaria' exige secretaria_id")
        if self.perfil in (PerfilUsuario.ADMIN, PerfilUsuario.FISCAL) and self.secretaria_id:
            raise ValueError(f"Perfil '{self.perfil.value}' não pode ter secretaria_id")
        return self


class UsuarioUpdate(BaseModel):
    """Atualização de usuário."""
    nome_completo: Optional[str] = Field(default=None, min_length=3, max_length=150)
    telefone: Optional[str] = Field(default=None, max_length=20)
    cargo: Optional[str] = Field(default=None, max_length=100)
    ativo: Optional[bool] = None


class UsuarioResponse(BaseModel):
    id: int
    cpf: str
    nome_completo: str
    email: str
    telefone: Optional[str]
    cargo: Optional[str]
    perfil: PerfilUsuario
    secretaria_id: Optional[int]
    ativo: bool
    criado_em: datetime
    ultimo_login: Optional[datetime]

    class Config:
        from_attributes = True
