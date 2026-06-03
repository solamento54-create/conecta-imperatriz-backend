"""Enums usados em vários modelos."""
import enum


class PerfilUsuario(str, enum.Enum):
    ADMIN = "admin"
    FISCAL = "fiscal"
    SECRETARIA = "secretaria"


class StatusOcorrencia(str, enum.Enum):
    ANALISE = "analise"
    EXECUCAO = "execucao"
    RESOLVIDA = "resolvida"
    REJEITADA = "rejeitada"


class UrgenciaOcorrencia(str, enum.Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class TipoFoto(str, enum.Enum):
    INICIAL = "inicial"
    EM_EXECUCAO = "em_execucao"
    RESOLVIDA = "resolvida"


class CanalNotificacao(str, enum.Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
