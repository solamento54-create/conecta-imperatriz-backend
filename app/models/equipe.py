"""Modelo Equipe."""
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Equipe(Base):
    __tablename__ = "equipes"

    id = Column(BigInteger, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    responsavel_nome = Column(String(150), nullable=False)
    responsavel_telefone = Column(String(20))
    responsavel_email = Column(String(150))
    secretaria_id = Column(BigInteger, ForeignKey("secretarias.id"), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    secretaria = relationship("Secretaria", back_populates="equipes")
    ocorrencias = relationship("Ocorrencia", back_populates="equipe")
