"""
Schemas Pydantic para registro e gerenciamento de dispositivos push.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DispositivoPushRegistrar(BaseModel):
    """Cidadão registra (ou re-registra) seu token Expo Push."""
    expo_token: str = Field(..., min_length=10, max_length=200,
                             description="Token no formato ExponentPushToken[xxxxx]")
    plataforma: Optional[str] = Field(None, max_length=20, description="'android' ou 'ios'")
    modelo:     Optional[str] = Field(None, max_length=100, description="Modelo do aparelho")


class DispositivoPushResposta(BaseModel):
    id:           int
    expo_token:   str
    plataforma:   Optional[str]
    modelo:       Optional[str]
    ativo:        bool
    criado_em:    datetime

    model_config = {"from_attributes": True}


class NotificacaoResposta(BaseModel):
    id:            int
    titulo:        str
    mensagem:      str
    canal:         str
    enviada:       bool
    lida:          bool
    ocorrencia_id: Optional[int] = None
    data_envio:    Optional[datetime] = None
    lida_em:       Optional[datetime] = None
    criado_em:     datetime

    model_config = {"from_attributes": True}
