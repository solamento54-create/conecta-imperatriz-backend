"""
Enums usados no sistema Conecta Imperatriz.
"""
from enum import Enum

class PerfilUsuario(str, Enum):
    ADMIN = "admin"
    FISCAL = "fiscal"
    SECRETARIA = "secretaria"

class StatusOcorrencia(str, Enum):
    NOVA = "nova"
    ANALISE = "analise"
    EM_ANALISE = "analise"
    TRIAGEM = "triagem"
    EM_EXECUCAO = "execucao"
    EXECUCAO = "execucao"
    EM_ANDAMENTO = "execucao"
    RESOLVIDA = "resolvida"
    CONCLUIDA = "resolvida"
    REJEITADA = "rejeitada"
    CANCELADA = "rejeitada"

class UrgenciaOcorrencia(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class TipoFoto(str, Enum):
    INICIAL = "inicial"
    EXECUCAO = "execucao"
    EM_EXECUCAO = "execucao"
    RESOLVIDA = "resolvida"
    CONCLUIDA = "resolvida"

class PlataformaPush(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"

class CanalNotificacao(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    SISTEMA = "sistema"

class TipoNotificacao(str, Enum):
    STATUS = "status"
    APOIO = "apoio"
    MARCO = "marco"
    SISTEMA = "sistema"
    GERAL = "geral"

# Aliases pra compatibilidade
StatusDenuncia = StatusOcorrencia
UrgenciaDenuncia = UrgenciaOcorrencia
PerfilFuncionario = PerfilUsuario
TipoUsuario = PerfilUsuario
CanalNotif = CanalNotificacao
TipoNotif = TipoNotificacao
