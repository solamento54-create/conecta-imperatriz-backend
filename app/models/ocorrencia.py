"""Modelo Ocorrencia — tabela central do sistema."""
from sqlalchemy import (
    Column, BigInteger, String, Text, DateTime, Date, ForeignKey,
    Numeric, Integer, Enum as SQLEnum, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import StatusOcorrencia, UrgenciaOcorrencia

class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id = Column(BigInteger, primary_key=True, index=True)
    protocolo = Column(String(20), unique=True, nullable=False, index=True)

    # Relacionamentos
    cidadao_id = Column(BigInteger, ForeignKey("cidadaos.id"), nullable=False)
    categoria_id = Column(BigInteger, ForeignKey("categorias.id"), nullable=False)
    secretaria_id = Column(BigInteger, ForeignKey("secretarias.id"))
    equipe_id = Column(BigInteger, ForeignKey("equipes.id"))

    # Conteúdo
    titulo = Column(String(200))
    descricao = Column(Text, nullable=False)

    # Localização
    endereco = Column(String(300), nullable=False)
    bairro = Column(String(100), index=True)
    cep = Column(String(10))
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)

    # Status e prioridade
    status = Column(
        SQLEnum(StatusOcorrencia, name="status_ocorrencia", values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=StatusOcorrencia.ANALISE, index=True
    )
    urgencia = Column(
        SQLEnum(UrgenciaOcorrencia, name="urgencia_ocorrencia", values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=UrgenciaOcorrencia.BAIXA, index=True
    )

    contador_apoios = Column(Integer, nullable=False, default=0)

    # Resolução
    previsao_resolucao = Column(Date)
    data_resolucao = Column(DateTime(timezone=True))
    motivo_rejeicao = Column(Text)
    observacao_interna = Column(Text)

    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    cidadao = relationship("Cidadao", back_populates="ocorrencias")
    categoria = relationship("Categoria", back_populates="ocorrencias")
    secretaria = relationship("Secretaria", back_populates="ocorrencias")
    equipe = relationship("Equipe", back_populates="ocorrencias")
    fotos = relationship("Foto", back_populates="ocorrencia", cascade="all, delete-orphan")
    historico = relationship("HistoricoStatus", back_populates="ocorrencia", cascade="all, delete-orphan")
    apoios = relationship("ApoioDuplicata", back_populates="ocorrencia", cascade="all, delete-orphan")
    notificacoes = relationship("Notificacao", back_populates="ocorrencia")

    # Índice geográfico para busca de duplicatas próximas
    __table_args__ = (
        Index("idx_ocorrencias_geo", "latitude", "longitude"),
    )
