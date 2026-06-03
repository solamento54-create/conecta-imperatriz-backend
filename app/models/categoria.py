"""Modelo Categoria."""
from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(BigInteger, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    descricao = Column(Text)
    secretaria_id = Column(BigInteger, ForeignKey("secretarias.id"), nullable=False)
    icone = Column(String(50))
    cor = Column(String(7), default="#0D2CBC")
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    secretaria = relationship("Secretaria", back_populates="categorias")
    ocorrencias = relationship("Ocorrencia", back_populates="categoria")
