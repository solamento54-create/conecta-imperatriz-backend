"""Modelo Usuario - funcionários da prefeitura (admin/fiscal/secretaria)."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import PerfilUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(200), nullable=False)
    cpf = Column(String(11), nullable=True)
    telefone = Column(String(20), nullable=True)
    
    # Usa o tipo ENUM correto do banco (perfil_usuario com valores em minúsculo)
    perfil = Column(
        PgEnum(
            "admin", "fiscal", "secretaria",
            name="perfil_usuario",
            create_type=False,
        ),
        nullable=False,
    )
    
    secretaria_id = Column(Integer, ForeignKey("secretarias.id"), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
    
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    secretaria = relationship("Secretaria", back_populates="usuarios", foreign_keys=[secretaria_id])
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', perfil='{self.perfil}')>"
