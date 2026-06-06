"""Modelo HistoricoStatus — auditoria de mudanças."""
from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import StatusOcorrencia

class HistoricoStatus(Base):
    __tablename__ = "historico_status"

    id = Column(BigInteger, primary_key=True, index=True)
    ocorrencia_id = Column(BigInteger, ForeignKey("ocorrencias.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id"), nullable=False)
    status_anterior = Column(SQLEnum(StatusOcorrencia, name="status_ocorrencia", values_callable=lambda x: [e.value for e in x]))
    status_novo = Column(SQLEnum(StatusOcorrencia, name="status_ocorrencia", values_callable=lambda x: [e.value for e in x]), nullable=False)
    secretaria_anterior_id = Column(BigInteger, ForeignKey("secretarias.id"))
    secretaria_nova_id = Column(BigInteger, ForeignKey("secretarias.id"))
    equipe_anterior_id = Column(BigInteger, ForeignKey("equipes.id"))
    equipe_nova_id = Column(BigInteger, ForeignKey("equipes.id"))
    observacao = Column(Text)
    data_alteracao = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    ocorrencia = relationship("Ocorrencia", back_populates="historico")
    usuario = relationship("Usuario", back_populates="historico_alteracoes")
