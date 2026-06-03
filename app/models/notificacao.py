"""Modelo Notificacao."""
from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import CanalNotificacao


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(BigInteger, primary_key=True, index=True)
    cidadao_id = Column(BigInteger, ForeignKey("cidadaos.id", ondelete="CASCADE"), nullable=False)
    ocorrencia_id = Column(BigInteger, ForeignKey("ocorrencias.id", ondelete="CASCADE"))

    titulo = Column(String(150), nullable=False)
    mensagem = Column(Text, nullable=False)
    canal = Column(SQLEnum(CanalNotificacao, name="canal_notificacao"), nullable=False, default=CanalNotificacao.PUSH)
    lida = Column(Boolean, nullable=False, default=False, index=True)
    data_envio = Column(DateTime(timezone=True), server_default=func.now())
    data_leitura = Column(DateTime(timezone=True))

    cidadao = relationship("Cidadao", back_populates="notificacoes")
    ocorrencia = relationship("Ocorrencia", back_populates="notificacoes")
