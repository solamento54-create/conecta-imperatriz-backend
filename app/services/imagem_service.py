"""
Serviço de processamento de imagens.
- Valida formato e tamanho
- Comprime fotos grandes (1920px max)
- Gera thumbnail para listagens
- Remove dados EXIF (privacidade do cidadão)
"""
import io
from typing import Tuple
from PIL import Image, ImageOps
from fastapi import HTTPException, status
from app.core.config import settings


FORMATOS_ACEITOS = {"JPEG", "PNG", "WEBP", "HEIC"}
EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


class ProcessadorImagem:
    """Processa imagens: valida, comprime e gera thumbnails."""

    @staticmethod
    def validar_arquivo(conteudo: bytes, nome_arquivo: str) -> None:
        """
        Valida formato e tamanho. Lança HTTPException se inválido.
        """
        # Verificar tamanho
        tamanho_mb = len(conteudo) / (1024 * 1024)
        if tamanho_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande ({tamanho_mb:.1f}MB). "
                       f"Máximo: {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

        # Verificar extensão
        extensao = nome_arquivo.lower().rsplit(".", 1)[-1] if "." in nome_arquivo else ""
        if f".{extensao}" not in EXTENSOES_VALIDAS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensão não permitida. Aceito: {', '.join(EXTENSOES_VALIDAS)}"
            )

        # Verificar conteúdo é imagem válida (não basta a extensão)
        try:
            img = Image.open(io.BytesIO(conteudo))
            img.verify()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo não é uma imagem válida"
            )

    @staticmethod
    def processar(conteudo: bytes) -> Tuple[bytes, bytes, dict]:
        """
        Processa imagem: comprime + gera thumbnail.
        Retorna (imagem_otimizada, thumbnail, metadata).

        - Remove EXIF (privacidade — câmeras gravam localização GPS no arquivo!)
        - Corrige rotação automaticamente
        - Redimensiona se maior que IMAGEM_MAX_LARGURA
        - Converte tudo para JPEG (menor que PNG)
        """
        img = Image.open(io.BytesIO(conteudo))

        # ── Corrigir rotação automaticamente (EXIF Orientation) ─
        img = ImageOps.exif_transpose(img)

        # ── Converter para RGB (remove canal alfa se PNG) ───────
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        largura_original, altura_original = img.size

        # ── Redimensionar se maior que o limite ────────────────
        if img.width > settings.IMAGEM_MAX_LARGURA:
            proporcao = settings.IMAGEM_MAX_LARGURA / img.width
            nova_altura = int(img.height * proporcao)
            img = img.resize(
                (settings.IMAGEM_MAX_LARGURA, nova_altura),
                Image.Resampling.LANCZOS
            )

        # ── Salvar versão otimizada (sem EXIF) ─────────────────
        buffer_principal = io.BytesIO()
        img.save(
            buffer_principal,
            format="JPEG",
            quality=settings.IMAGEM_QUALIDADE,
            optimize=True,
            progressive=True,
        )
        imagem_otimizada = buffer_principal.getvalue()

        # ── Gerar thumbnail (mantém proporção) ─────────────────
        thumb = img.copy()
        thumb.thumbnail(
            (settings.THUMBNAIL_LARGURA, settings.THUMBNAIL_LARGURA),
            Image.Resampling.LANCZOS
        )
        buffer_thumb = io.BytesIO()
        thumb.save(
            buffer_thumb,
            format="JPEG",
            quality=75,
            optimize=True,
        )
        thumbnail = buffer_thumb.getvalue()

        metadata = {
            "largura_original": largura_original,
            "altura_original": altura_original,
            "largura_final": img.width,
            "altura_final": img.height,
            "tamanho_kb": len(imagem_otimizada) // 1024,
            "thumbnail_kb": len(thumbnail) // 1024,
        }

        return imagem_otimizada, thumbnail, metadata
