"""Modelo ApoioDuplicata — quando cidadão dá '+1' em ocorrência existente."""
from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ApoioDuplicata(Base):
    __tablename__ = "apoios_duplicata"

    id = Column(BigInteger, primary_key=True, index=True)
    ocorrencia_id = Column(BigInteger, ForeignKey("ocorrencias.id", ondelete="CASCADE"), nullable=False)
    cidadao_id = Column(BigInteger, ForeignKey("cidadaos.id", ondelete="CASCADE"), nullable=False)
    data_apoio = Column(DateTime(timezone=True), server_default=func.now())

    # Garante que mesmo cidadão não apoia 2x a mesma ocorrência
    __table_args__ = (
        UniqueConstraint("ocorrencia_id", "cidadao_id", name="uq_apoio_unico"),
    )

    ocorrencia = relationship("Ocorrencia", back_populates="apoios")
    cidadao = relationship("Cidadao", back_populates="apoios")
