"""Schemas de Ocorrência."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from app.models.enums import StatusOcorrencia, UrgenciaOcorrencia


class OcorrenciaCreate(BaseModel):
    """Cidadão cria uma denúncia pelo app."""
    categoria_id: int
    titulo: Optional[str] = Field(default=None, max_length=200)
    descricao: str = Field(min_length=10, max_length=2000)
    endereco: str = Field(min_length=5, max_length=300)
    bairro: Optional[str] = Field(default=None, max_length=100)
    cep: Optional[str] = Field(default=None, max_length=10)
    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)


class OcorrenciaUpdate(BaseModel):
    """Atualização pelo painel da prefeitura."""
    status: Optional[StatusOcorrencia] = None
    secretaria_id: Optional[int] = None
    equipe_id: Optional[int] = None
    previsao_resolucao: Optional[date] = None
    motivo_rejeicao: Optional[str] = None
    observacao_interna: Optional[str] = None


class OcorrenciaResponse(BaseModel):
    """Resposta completa da ocorrência."""
    id: int
    protocolo: str
    cidadao_id: int
    categoria_id: int
    secretaria_id: Optional[int]
    equipe_id: Optional[int]
    titulo: Optional[str]
    descricao: str
    endereco: str
    bairro: Optional[str]
    cep: Optional[str]
    latitude: Decimal
    longitude: Decimal
    status: StatusOcorrencia
    urgencia: UrgenciaOcorrencia
    contador_apoios: int
    previsao_resolucao: Optional[date]
    data_resolucao: Optional[datetime]
    motivo_rejeicao: Optional[str]
    observacao_interna: Optional[str]
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class OcorrenciaCompleta(OcorrenciaResponse):
    """Ocorrência com dados relacionados (para o painel)."""
    cidadao_nome: Optional[str] = None
    cidadao_telefone: Optional[str] = None
    categoria_nome: Optional[str] = None
    categoria_icone: Optional[str] = None
    secretaria_nome: Optional[str] = None
    equipe_nome: Optional[str] = None
    fotos_urls: List[str] = []


class DuplicataCheckRequest(BaseModel):
    """Verifica se já existe ocorrência similar perto."""
    categoria_id: int
    latitude: Decimal
    longitude: Decimal
    raio_metros: int = Field(default=50, ge=10, le=500)


class DuplicataCheckResponse(BaseModel):
    encontrada: bool
    ocorrencia: Optional[OcorrenciaResponse] = None
    distancia_metros: Optional[float] = None
