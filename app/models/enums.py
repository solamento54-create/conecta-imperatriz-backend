"""
Enums usados no sistema Conecta Imperatriz.
Versão expandida com TODOS os enums necessários.
"""
from enum import Enum


class PerfilUsuario(str, Enum):
    """Perfis de usuário."""
    ADMIN = "admin"
    FISCAL = "fiscal"
    SECRETARIA = "secretaria"


class StatusOcorrencia(str, Enum):
    """Status do ciclo de vida."""
    NOVA = "nova"
    ANALISE = "analise"
    EM_ANALISE = "analise"
    TRIAGEM = "triagem"
    EM_EXECUCAO = "em_execucao"
    EXECUCAO = "em_execucao"
    EM_ANDAMENTO = "em_execucao"
    RESOLVIDA = "resolvida"
    CONCLUIDA = "resolvida"
    REJEITADA = "rejeitada"
    CANCELADA = "rejeitada"


class UrgenciaOcorrencia(str, Enum):
    """Nível de urgência."""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class TipoFoto(str, Enum):
    """Tipo da foto."""
    INICIAL = "inicial"
    EXECUCAO = "execucao"
    EM_EXECUCAO = "execucao"
    RESOLVIDA = "resolvida"
    CONCLUIDA = "resolvida"


class PlataformaPush(str, Enum):
    """Plataforma do dispositivo push."""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class CanalNotificacao(str, Enum):
    """Canal de envio da notificação."""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    SISTEMA = "sistema"


class TipoNotificacao(str, Enum):
    """Tipo de evento da notificação."""
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
