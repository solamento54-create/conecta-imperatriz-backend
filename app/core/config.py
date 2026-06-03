"""
Configurações centrais da aplicação.
Lê as variáveis de ambiente do arquivo .env automaticamente.
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings carregadas do .env via Pydantic."""

    # ── App ─────────────────────────────────────────────────
    APP_NAME: str = "Conecta Imperatriz API"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "1.0.0"

    # ── Servidor ────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Banco de Dados ──────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/conecta_imperatriz"
    )

    # ── JWT ─────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="troque-em-producao-por-uma-chave-grande-e-aleatoria"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    # ── CORS ────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:5500,null"

    # ── Storage ─────────────────────────────────────────────
    STORAGE_MODE: str = "local"     # 'local' ou 'supabase'

    # Local
    UPLOAD_DIR: str = "./uploads"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Supabase
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_BUCKET: str = "conecta-imperatriz-fotos"

    # Limites
    MAX_UPLOAD_SIZE_MB: int = 10
    IMAGEM_MAX_LARGURA: int = 1920
    IMAGEM_QUALIDADE: int = 85
    THUMBNAIL_LARGURA: int = 400

    # ── AWS S3 (legado/opcional) ────────────────────────────
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_S3_BUCKET: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Converte a string ALLOWED_ORIGINS em lista."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


# Singleton — uma instância usada em todo o app
settings = Settings()
