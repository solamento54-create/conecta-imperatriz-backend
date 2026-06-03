"""
Enums usados no sistema Conecta Imperatriz.
IMPORTANTE: os valores devem bater EXATAMENTE com os ENUM types do PostgreSQL.
"""
from enum import Enum


class PerfilUsuario(str, Enum):
    """Perfis de usuário do painel (admin/fiscal/secretaria)."""
    ADMIN = "admin"
    FISCAL = "fiscal"
    SECRETARIA = "secretaria"


class StatusOcorrencia(str, Enum):
    """Status do ciclo de vida de uma ocorrência."""
    NOVA = "nova"
    TRIAGEM = "triagem"
    EM_EXECUCAO = "em_execucao"
    RESOLVIDA = "resolvida"
    REJEITADA = "rejeitada"


class UrgenciaOcorrencia(str, Enum):
    """Nível de urgência da ocorrência."""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class TipoFoto(str, Enum):
    """Tipo da foto associada a uma ocorrência."""
    INICIAL = "inicial"
    EXECUCAO = "execucao"
    RESOLVIDA = "resolvida"


class PlataformaPush(str, Enum):
    """Plataforma do dispositivo para push notifications."""
    ANDROID = "android"
    IOS = "ios"
