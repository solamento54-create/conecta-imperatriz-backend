"""Modelo Foto — imagens de ocorrências."""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import TipoFoto


class Foto(Base):
    __tablename__ = "fotos"

    id = Column(BigInteger, primary_key=True, index=True)
    ocorrencia_id = Column(BigInteger, ForeignKey("ocorrencias.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    tipo = Column(SQLEnum(TipoFoto, name="tipo_foto"), nullable=False, default=TipoFoto.INICIAL)
    tamanho_kb = Column(Integer)
    enviado_por_tipo = Column(String(20))   # 'cidadao' ou 'usuario'
    enviado_por_id = Column(BigInteger)
    data_envio = Column(DateTime(timezone=True), server_default=func.now())

    ocorrencia = relationship("Ocorrencia", back_populates="fotos")
