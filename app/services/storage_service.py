"""
Serviço de Storage de arquivos.

Abstração que funciona com dois backends:
- 'local'    → salva em pasta local (desenvolvimento)
- 'supabase' → salva no Supabase Storage (produção)

A escolha vem da variável STORAGE_MODE no .env.
O resto do código não precisa saber qual está ativo.
"""
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status
from app.core.config import settings


# ════════════════════════════════════════════════════════════
#  Interface comum (contrato)
# ════════════════════════════════════════════════════════════
class StorageBackend(ABC):
    """Interface que todo backend de storage deve implementar."""

    @abstractmethod
    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str:
        """Salva arquivo e devolve URL pública."""
        ...

    @abstractmethod
    def delete(self, caminho: str) -> bool:
        """Remove arquivo."""
        ...

    @abstractmethod
    def url_publica(self, caminho: str) -> str:
        """Gera URL pública para acesso ao arquivo."""
        ...


# ════════════════════════════════════════════════════════════
#  Backend LOCAL — desenvolvimento
# ════════════════════════════════════════════════════════════
class LocalStorage(StorageBackend):
    """Storage que salva arquivos numa pasta no servidor."""

    def __init__(self):
        self.diretorio = Path(settings.UPLOAD_DIR).resolve()
        self.diretorio.mkdir(parents=True, exist_ok=True)
        self.base_url = settings.PUBLIC_BASE_URL.rstrip("/")

    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str:
        # Cria subpastas se necessário
        arquivo = self.diretorio / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)

        # Salva o arquivo
        arquivo.write_bytes(conteudo)
        return self.url_publica(caminho)

    def delete(self, caminho: str) -> bool:
        arquivo = self.diretorio / caminho
        if arquivo.exists():
            arquivo.unlink()
            return True
        return False

    def url_publica(self, caminho: str) -> str:
        return f"{self.base_url}/uploads/{caminho}"


# ════════════════════════════════════════════════════════════
#  Backend SUPABASE — produção
# ════════════════════════════════════════════════════════════
class SupabaseStorage(StorageBackend):
    """Storage que salva arquivos no Supabase Storage."""

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "STORAGE_MODE=supabase requer SUPABASE_URL e SUPABASE_KEY no .env"
            )

        # Import tardio para não exigir supabase em dev
        from supabase import create_client

        self.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
        )
        self.bucket = settings.SUPABASE_BUCKET
        self._garantir_bucket()

    def _garantir_bucket(self):
        """Garante que o bucket existe. Cria se não existir."""
        try:
            buckets = self.client.storage.list_buckets()
            nomes = [b.name for b in buckets]
            if self.bucket not in nomes:
                self.client.storage.create_bucket(
                    self.bucket,
                    options={"public": True}  # fotos são públicas para o app exibir
                )
        except Exception as e:
            print(f"⚠️  Aviso: não foi possível verificar bucket '{self.bucket}': {e}")

    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str:
        try:
            self.client.storage.from_(self.bucket).upload(
                path=caminho,
                file=conteudo,
                file_options={
                    "content-type": content_type,
                    "cache-control": "31536000",  # cache de 1 ano (foto não muda)
                    "upsert": "true",  # sobrescreve se já existir
                },
            )
            return self.url_publica(caminho)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha ao enviar foto para storage: {str(e)}"
            )

    def delete(self, caminho: str) -> bool:
        try:
            self.client.storage.from_(self.bucket).remove([caminho])
            return True
        except Exception:
            return False

    def url_publica(self, caminho: str) -> str:
        return self.client.storage.from_(self.bucket).get_public_url(caminho)


# ════════════════════════════════════════════════════════════
#  Factory — instancia o backend correto
# ════════════════════════════════════════════════════════════
_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Retorna a instância de storage configurada (singleton)."""
    global _storage_instance

    if _storage_instance is None:
        if settings.STORAGE_MODE == "supabase":
            _storage_instance = SupabaseStorage()
        elif settings.STORAGE_MODE == "local":
            _storage_instance = LocalStorage()
        else:
            raise ValueError(
                f"STORAGE_MODE inválido: '{settings.STORAGE_MODE}'. "
                f"Use 'local' ou 'supabase'."
            )

    return _storage_instance


# ════════════════════════════════════════════════════════════
#  Helpers — geram caminhos organizados
# ════════════════════════════════════════════════════════════
def gerar_caminho_foto(ocorrencia_id: int, tipo: str, sufixo: str = "") -> str:
    """
    Gera caminho organizado por ano/mês/ocorrência.
    Exemplo: '2026/05/ocorrencia-42/inicial-a3f7b8.jpg'
    """
    agora = datetime.now()
    identificador = uuid.uuid4().hex[:8]
    nome = f"{tipo}-{identificador}{sufixo}.jpg"
    return f"{agora.year}/{agora.month:02d}/ocorrencia-{ocorrencia_id}/{nome}"


def gerar_caminho_thumbnail(caminho_original: str) -> str:
    """Deriva o caminho do thumbnail a partir do caminho original."""
    base, ext = os.path.splitext(caminho_original)
    return f"{base}-thumb{ext}"
