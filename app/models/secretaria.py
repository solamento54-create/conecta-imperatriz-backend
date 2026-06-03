"""Modelo Secretaria."""
from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Secretaria(Base):
    __tablename__ = "secretarias"

    id = Column(BigInteger, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    descricao = Column(Text)
    email_contato = Column(String(150))
    telefone = Column(String(20))
    icone = Column(String(50))
    cor = Column(String(7), default="#0D2CBC")
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    categorias = relationship("Categoria", back_populates="secretaria")
    equipes = relationship("Equipe", back_populates="secretaria")
    usuarios = relationship("Usuario", back_populates="secretaria")
    ocorrencias = relationship("Ocorrencia", back_populates="secretaria")
