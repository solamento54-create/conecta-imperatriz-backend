"""
Modelo: DispositivoPush — token Expo Push de cada celular do cidadão.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DispositivoPush(Base):
    __tablename__ = "dispositivos_push"

    id          = Column(Integer, primary_key=True, index=True)
    cidadao_id  = Column(Integer, ForeignKey("cidadaos.id", ondelete="CASCADE"), nullable=False, index=True)
    expo_token  = Column(String, nullable=False, unique=True)
    plataforma  = Column(String(20))      # 'android' | 'ios'
    modelo      = Column(String(100))
    ativo       = Column(Boolean, default=True, index=True)
    criado_em   = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_uso  = Column(DateTime(timezone=True), server_default=func.now())

    cidadao = relationship("Cidadao", backref="dispositivos_push")

    __table_args__ = (
        UniqueConstraint("expo_token", name="uq_dispositivo_token"),
    )
