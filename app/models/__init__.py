"""
Modelos SQLAlchemy do Conecta Imperatriz.
Importar tudo aqui é importante para o Alembic detectar as tabelas.
"""
from app.models.secretaria import Secretaria
from app.models.categoria import Categoria
from app.models.equipe import Equipe
from app.models.cidadao import Cidadao
from app.models.usuario import Usuario
from app.models.ocorrencia import Ocorrencia
from app.models.foto import Foto
from app.models.historico_status import HistoricoStatus
from app.models.apoio_duplicata import ApoioDuplicata
from app.models.notificacao import Notificacao
from app.models.dispositivo_push import DispositivoPush

__all__ = [
    "Secretaria",
    "Categoria",
    "Equipe",
    "Cidadao",
    "Usuario",
    "Ocorrencia",
    "Foto",
    "HistoricoStatus",
    "ApoioDuplicata",
    "Notificacao",
    "DispositivoPush",
]
