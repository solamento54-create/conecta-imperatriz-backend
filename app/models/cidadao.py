"""Modelo Cidadão."""
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Cidadao(Base):
    __tablename__ = "cidadaos"

    id = Column(BigInteger, primary_key=True, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome_completo = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    telefone = Column(String(20), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    data_nascimento = Column(Date)
    data_aceite_lgpd = Column(DateTime(timezone=True), nullable=False)
    token_recuperacao = Column(String(255))
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True))

    ocorrencias = relationship("Ocorrencia", back_populates="cidadao")
    apoios = relationship("ApoioDuplicata", back_populates="cidadao")
    notificacoes = relationship("Notificacao", back_populates="cidadao")
