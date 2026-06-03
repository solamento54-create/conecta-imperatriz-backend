"""
Enums usados no sistema Conecta Imperatriz.
IMPORTANTE: os valores devem bater EXATAMENTE com os ENUM types do PostgreSQL.
"""
from enum import Enum


class PerfilUsuario(str, Enum):
    """Perfis de usuário do painel."""
    ADMIN = "admin"
    FISCAL = "fiscal"
    SECRETARIA = "secretaria"


class StatusOcorrencia(str, Enum):
    """Status do ciclo de vida de uma ocorrência."""
    NOVA = "nova"
    ANALISE = "analise"
    TRIAGEM = "triagem"
    EM_EXECUCAO = "em_execucao"
    EXECUCAO = "em_execucao"
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


# Aliases pra compatibilidade
StatusDenuncia = StatusOcorrencia
UrgenciaDenuncia = UrgenciaOcorrencia
PerfilFuncionario = PerfilUsuario
TipoUsuario = PerfilUsuario
