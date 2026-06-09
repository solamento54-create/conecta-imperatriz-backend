"""
Serviço de Storage de arquivos.
"""
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status
from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str: ...
    @abstractmethod
    def delete(self, caminho: str) -> bool: ...
    @abstractmethod
    def url_publica(self, caminho: str) -> str: ...


class LocalStorage(StorageBackend):
    def __init__(self):
        self.diretorio = Path(settings.UPLOAD_DIR).resolve()
        self.diretorio.mkdir(parents=True, exist_ok=True)
        self.base_url = settings.PUBLIC_BASE_URL.rstrip("/")

    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str:
        arquivo = self.diretorio / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)
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


class SupabaseStorage(StorageBackend):
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("STORAGE_MODE=supabase requer SUPABASE_URL e SUPABASE_KEY")
        self.url = settings.SUPABASE_URL.rstrip("/")
        self.key = settings.SUPABASE_KEY
        self.bucket = settings.SUPABASE_BUCKET
        self.headers = {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
        }
        self._garantir_bucket()

    def _garantir_bucket(self):
        try:
            import requests
            r = requests.get(
                f"{self.url}/storage/v1/bucket/{self.bucket}",
                headers=self.headers, timeout=10
            )
            if r.status_code == 404:
                requests.post(
                    f"{self.url}/storage/v1/bucket",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json={"id": self.bucket, "name": self.bucket, "public": True},
                    timeout=10
                )
        except Exception as e:
            print(f"⚠️  Aviso bucket: {e}")

    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str:
        import requests
        r = requests.post(
            f"{self.url}/storage/v1/object/{self.bucket}/{caminho}",
            headers={**self.headers, "Content-Type": content_type, "x-upsert": "true"},
            data=conteudo, timeout=30
        )
        if r.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha no upload: {r.text}"
            )
        return self.url_publica(caminho)

    def delete(self, caminho: str) -> bool:
        import requests
        try:
            requests.delete(
                f"{self.url}/storage/v1/object/{self.bucket}/{caminho}",
                headers=self.headers, timeout=10
            )
            return True
        except Exception:
            return False

    def url_publica(self, caminho: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{caminho}"


_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_MODE == "supabase":
            _storage_instance = SupabaseStorage()
        elif settings.STORAGE_MODE == "local":
            _storage_instance = LocalStorage()
        else:
            raise ValueError(f"STORAGE_MODE inválido: '{settings.STORAGE_MODE}'")
    return _storage_instance


def gerar_caminho_foto(ocorrencia_id: int, tipo: str, sufixo: str = "") -> str:
    agora = datetime.now()
    identificador = uuid.uuid4().hex[:8]
    nome = f"{tipo}-{identificador}{sufixo}.jpg"
    return f"{agora.year}/{agora.month:02d}/ocorrencia-{ocorrencia_id}/{nome}"


def gerar_caminho_thumbnail(caminho_original: str) -> str:
    base, ext = os.path.splitext(caminho_original)
    return f"{base}-thumb{ext}"
