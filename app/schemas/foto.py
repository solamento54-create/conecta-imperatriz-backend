"""Schemas de Foto."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import TipoFoto


class FotoResponse(BaseModel):
    id: int
    ocorrencia_id: int
    url: str
    thumbnail_url: Optional[str]
    tipo: TipoFoto
    tamanho_kb: Optional[int]
    enviado_por_tipo: Optional[str]
    enviado_por_id: Optional[int]
    data_envio: datetime

    model_config = ConfigDict(from_attributes=True)


class FotoUploadResponse(BaseModel):
    """Resposta após upload bem-sucedido."""
    id: int
    url: str
    thumbnail_url: Optional[str]
    tipo: TipoFoto
    tamanho_kb: int
    mensagem: str = "Foto enviada com sucesso"
