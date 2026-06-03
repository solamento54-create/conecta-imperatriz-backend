"""
Endpoints de gerenciamento de Fotos.

Fluxo:
1. Cidadão cria ocorrência → recebe ocorrencia_id
2. Cidadão faz upload de 1 ou mais fotos para essa ocorrência
3. (Opcional) Fiscal sobe foto 'em_execucao' durante reparo
4. (Opcional) Fiscal sobe foto 'resolvida' ao concluir
"""
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, File, UploadFile, HTTPException,
    Form, status, Path
)
from fastapi.responses import FileResponse
from pathlib import Path as PathLib
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import (
    get_current_cidadao,
    get_current_usuario,
    require_qualquer_usuario,
)
from app.models.foto import Foto
from app.models.ocorrencia import Ocorrencia
from app.models.cidadao import Cidadao
from app.models.usuario import Usuario
from app.models.enums import TipoFoto, PerfilUsuario
from app.schemas.foto import FotoResponse, FotoUploadResponse
from app.services.imagem_service import ProcessadorImagem
from app.services.storage_service import (
    get_storage,
    gerar_caminho_foto,
    gerar_caminho_thumbnail,
)


router = APIRouter(prefix="/fotos", tags=["Fotos"])


# ════════════════════════════════════════════════════════════
#  UPLOAD pelo CIDADÃO (foto inicial da denúncia)
# ════════════════════════════════════════════════════════════
@router.post(
    "/ocorrencias/{ocorrencia_id}/upload-cidadao",
    response_model=FotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cidadão envia foto da denúncia",
)
def upload_foto_cidadao(
    ocorrencia_id: int = Path(...),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_current_cidadao),
):
    """
    Cidadão envia foto vinculada à sua ocorrência.
    - Só pode subir fotos das próprias denúncias
    - Foto é processada (comprimida, EXIF removido, thumbnail gerado)
    - Aceita: JPG, PNG, WEBP, HEIC. Máximo 10MB.
    """
    # Valida ocorrência e propriedade
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if not ocorrencia:
        raise HTTPException(404, "Ocorrência não encontrada")
    if ocorrencia.cidadao_id != cidadao.id:
        raise HTTPException(403, "Você só pode enviar fotos das suas próprias denúncias")

    return _processar_upload(
        db=db,
        arquivo=arquivo,
        ocorrencia=ocorrencia,
        tipo=TipoFoto.INICIAL,
        enviado_por_tipo="cidadao",
        enviado_por_id=cidadao.id,
    )


# ════════════════════════════════════════════════════════════
#  UPLOAD pelo FISCAL/USUÁRIO (foto de execução / resolvida)
# ════════════════════════════════════════════════════════════
@router.post(
    "/ocorrencias/{ocorrencia_id}/upload-usuario",
    response_model=FotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Fiscal/funcionário envia foto (em execução ou resolvida)",
)
def upload_foto_usuario(
    ocorrencia_id: int = Path(...),
    arquivo: UploadFile = File(...),
    tipo: TipoFoto = Form(default=TipoFoto.EM_EXECUCAO),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    """
    Funcionário envia foto de uma ocorrência.
    - Fiscal e admin podem subir foto em qualquer ocorrência
    - Perfil 'secretaria' só pode subir em ocorrências da sua secretaria
    - Tipo: 'em_execucao' ou 'resolvida' (não pode subir 'inicial')
    """
    if tipo == TipoFoto.INICIAL:
        raise HTTPException(
            400,
            "Funcionário não pode subir foto do tipo 'inicial'. "
            "Use 'em_execucao' ou 'resolvida'."
        )

    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if not ocorrencia:
        raise HTTPException(404, "Ocorrência não encontrada")

    # Secretaria só vê o que é dela
    if usuario.perfil == PerfilUsuario.SECRETARIA:
        if ocorrencia.secretaria_id != usuario.secretaria_id:
            raise HTTPException(403, "Você não tem acesso a esta ocorrência")

    return _processar_upload(
        db=db,
        arquivo=arquivo,
        ocorrencia=ocorrencia,
        tipo=tipo,
        enviado_por_tipo="usuario",
        enviado_por_id=usuario.id,
    )


# ════════════════════════════════════════════════════════════
#  LISTAR fotos de uma ocorrência
# ════════════════════════════════════════════════════════════
@router.get(
    "/ocorrencias/{ocorrencia_id}",
    response_model=List[FotoResponse],
    summary="Listar fotos de uma ocorrência",
)
def listar_fotos(
    ocorrencia_id: int,
    tipo: Optional[TipoFoto] = None,
    db: Session = Depends(get_db),
):
    """Lista todas as fotos de uma ocorrência (público — para exibir no app/painel)."""
    query = db.query(Foto).filter(Foto.ocorrencia_id == ocorrencia_id)
    if tipo:
        query = query.filter(Foto.tipo == tipo)
    return query.order_by(Foto.data_envio).all()


# ════════════════════════════════════════════════════════════
#  EXCLUIR foto
# ════════════════════════════════════════════════════════════
@router.delete(
    "/{foto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir foto",
)
def excluir_foto(
    foto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    """
    Exclui uma foto. Regras:
    - Admin e fiscal podem excluir qualquer foto
    - Secretaria só pode excluir fotos das suas ocorrências
    - Foto é apagada do storage E do banco
    """
    foto = db.query(Foto).filter(Foto.id == foto_id).first()
    if not foto:
        raise HTTPException(404, "Foto não encontrada")

    if usuario.perfil == PerfilUsuario.SECRETARIA:
        ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == foto.ocorrencia_id).first()
        if not ocorrencia or ocorrencia.secretaria_id != usuario.secretaria_id:
            raise HTTPException(403, "Você não tem acesso a esta foto")

    storage = get_storage()

    # Extrai caminho relativo da URL (depende do backend)
    caminho_principal = _extrair_caminho_da_url(foto.url)
    caminho_thumb = _extrair_caminho_da_url(foto.thumbnail_url) if foto.thumbnail_url else None

    try:
        if caminho_principal:
            storage.delete(caminho_principal)
        if caminho_thumb:
            storage.delete(caminho_thumb)
    except Exception as e:
        print(f"⚠️  Aviso: falha ao apagar arquivo do storage: {e}")

    db.delete(foto)
    db.commit()


# ════════════════════════════════════════════════════════════
#  Servir arquivos locais (apenas modo 'local')
# ════════════════════════════════════════════════════════════
@router.get(
    "/local/{caminho:path}",
    include_in_schema=False,  # esconde do swagger — é detalhe interno
)
def servir_arquivo_local(caminho: str):
    """
    Endpoint usado APENAS no modo 'local' para servir os arquivos.
    Em produção (Supabase), as URLs apontam direto pro Supabase.
    """
    if settings.STORAGE_MODE != "local":
        raise HTTPException(404, "Endpoint não disponível neste modo")

    diretorio = PathLib(settings.UPLOAD_DIR).resolve()
    arquivo = diretorio / caminho

    # Segurança: garante que o caminho está dentro do diretório
    try:
        arquivo.resolve().relative_to(diretorio)
    except ValueError:
        raise HTTPException(400, "Caminho inválido")

    if not arquivo.exists() or not arquivo.is_file():
        raise HTTPException(404, "Arquivo não encontrado")

    return FileResponse(arquivo)


# ════════════════════════════════════════════════════════════
#  Helpers privados
# ════════════════════════════════════════════════════════════
def _processar_upload(
    db: Session,
    arquivo: UploadFile,
    ocorrencia: Ocorrencia,
    tipo: TipoFoto,
    enviado_por_tipo: str,
    enviado_por_id: int,
) -> FotoUploadResponse:
    """Processa upload: valida, comprime, salva no storage e no banco."""

    # Lê o conteúdo do arquivo
    conteudo = arquivo.file.read()

    # Valida
    ProcessadorImagem.validar_arquivo(conteudo, arquivo.filename or "foto.jpg")

    # Processa (comprime + thumbnail + remove EXIF)
    imagem_otimizada, thumbnail, meta = ProcessadorImagem.processar(conteudo)

    # Gera caminhos
    caminho_principal = gerar_caminho_foto(ocorrencia.id, tipo.value)
    caminho_thumb = gerar_caminho_thumbnail(caminho_principal)

    # Upload para storage
    storage = get_storage()
    url_principal = storage.upload(imagem_otimizada, caminho_principal, "image/jpeg")
    url_thumb = storage.upload(thumbnail, caminho_thumb, "image/jpeg")

    # Salva no banco
    nova_foto = Foto(
        ocorrencia_id=ocorrencia.id,
        url=url_principal,
        thumbnail_url=url_thumb,
        tipo=tipo,
        tamanho_kb=meta["tamanho_kb"],
        enviado_por_tipo=enviado_por_tipo,
        enviado_por_id=enviado_por_id,
    )
    db.add(nova_foto)
    db.commit()
    db.refresh(nova_foto)

    return FotoUploadResponse(
        id=nova_foto.id,
        url=nova_foto.url,
        thumbnail_url=nova_foto.thumbnail_url,
        tipo=nova_foto.tipo,
        tamanho_kb=nova_foto.tamanho_kb,
    )


def _extrair_caminho_da_url(url: str) -> Optional[str]:
    """Tenta extrair o caminho relativo de uma URL de storage."""
    if not url:
        return None

    # Modo local
    if "/uploads/" in url:
        return url.split("/uploads/", 1)[1]

    # Modo Supabase (formato: .../bucket/path/...)
    if settings.SUPABASE_BUCKET and f"/{settings.SUPABASE_BUCKET}/" in url:
        return url.split(f"/{settings.SUPABASE_BUCKET}/", 1)[1]

    return None
