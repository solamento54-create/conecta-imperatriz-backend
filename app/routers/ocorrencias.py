"""
Endpoints de Ocorrências (núcleo do sistema).

Endpoints públicos para o cidadão:
- POST   /ocorrencias                — criar nova denúncia
- POST   /ocorrencias/check-duplicata — verificar se já existe similar
- POST   /ocorrencias/{id}/apoiar    — dar +1 em ocorrência existente
- GET    /ocorrencias/minhas         — listar minhas ocorrências
- GET    /ocorrencias/{id}           — detalhes da ocorrência

Endpoints internos (painel):
- GET    /ocorrencias                — listar todas (com filtros)
- PATCH  /ocorrencias/{id}           — atualizar status/secretaria/equipe
"""
from datetime import datetime, timezone, date
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.deps import (
    get_current_cidadao,
    get_current_usuario,
    require_qualquer_usuario,
)
from app.models.ocorrencia import Ocorrencia
from app.models.cidadao import Cidadao
from app.models.usuario import Usuario
from app.models.categoria import Categoria
from app.models.apoio_duplicata import ApoioDuplicata
from app.models.historico_status import HistoricoStatus
from app.models.enums import StatusOcorrencia, PerfilUsuario, UrgenciaOcorrencia
from app.schemas.ocorrencia import (
    OcorrenciaCreate,
    OcorrenciaUpdate,
    OcorrenciaResponse,
    OcorrenciaCompleta,
    DuplicataCheckRequest,
    DuplicataCheckResponse,
)


router = APIRouter(prefix="/ocorrencias", tags=["Ocorrências"])


# ────────────────────────────────────────────────────────────
#  Função utilitária: distância entre 2 coords (em metros)
# ────────────────────────────────────────────────────────────
def distancia_haversine(lat1, lon1, lat2, lon2) -> float:
    """Calcula distância entre dois pontos GPS em metros (fórmula Haversine)."""
    R = 6371000  # raio da Terra em metros
    phi1, phi2 = radians(float(lat1)), radians(float(lat2))
    dphi = radians(float(lat2) - float(lat1))
    dlambda = radians(float(lon2) - float(lon1))
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def calcular_urgencia(apoios: int) -> UrgenciaOcorrencia:
    """0-1 = baixa | 2-4 = media | 5-9 = alta | 10+ = critica."""
    if apoios <= 1:
        return UrgenciaOcorrencia.BAIXA
    elif apoios <= 4:
        return UrgenciaOcorrencia.MEDIA
    elif apoios <= 9:
        return UrgenciaOcorrencia.ALTA
    return UrgenciaOcorrencia.CRITICA


def gerar_protocolo(db: Session) -> str:
    """Gera protocolo '2026-0001' baseado no ano e contagem."""
    ano = datetime.now().year
    total = db.query(Ocorrencia).filter(
        Ocorrencia.criado_em >= datetime(ano, 1, 1, tzinfo=timezone.utc)
    ).count()
    return f"{ano}-{(total + 1):04d}"


# ════════════════════════════════════════════════════════════
#  ENDPOINTS PÚBLICOS (cidadão)
# ════════════════════════════════════════════════════════════

@router.post(
    "/check-duplicata",
    response_model=DuplicataCheckResponse,
    summary="Verifica se já existe ocorrência similar perto"
)
def verificar_duplicata(
    dados: DuplicataCheckRequest,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_current_cidadao),
):
    """
    Antes de criar uma nova ocorrência, o app verifica se já existe uma
    da MESMA CATEGORIA num raio de N metros. Se sim, oferece apoiar a existente.
    """
    # Busca ocorrências ativas (não resolvidas/rejeitadas) da mesma categoria
    candidatas = db.query(Ocorrencia).filter(
        Ocorrencia.categoria_id == dados.categoria_id,
        Ocorrencia.status.in_([StatusOcorrencia.ANALISE, StatusOcorrencia.EXECUCAO]),
    ).all()

    mais_proxima: Optional[Ocorrencia] = None
    menor_distancia: float = float("inf")

    for oc in candidatas:
        dist = distancia_haversine(
            dados.latitude, dados.longitude,
            oc.latitude, oc.longitude
        )
        if dist <= dados.raio_metros and dist < menor_distancia:
            mais_proxima = oc
            menor_distancia = dist

    if mais_proxima:
        return DuplicataCheckResponse(
            encontrada=True,
            ocorrencia=mais_proxima,
            distancia_metros=round(menor_distancia, 2)
        )
    return DuplicataCheckResponse(encontrada=False)


@router.post(
    "",
    response_model=OcorrenciaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova denúncia (cidadão)"
)
def criar_ocorrencia(
    dados: OcorrenciaCreate,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_current_cidadao),
):
    """Cria uma nova denúncia. Cidadão precisa estar autenticado."""
    # Pega a secretaria padrão da categoria
    categoria = db.query(Categoria).filter(Categoria.id == dados.categoria_id).first()
    if not categoria:
        raise HTTPException(404, "Categoria não encontrada")

    nova = Ocorrencia(
        protocolo=gerar_protocolo(db),
        cidadao_id=cidadao.id,
        categoria_id=dados.categoria_id,
        secretaria_id=categoria.secretaria_id,
        titulo=dados.titulo,
        descricao=dados.descricao,
        endereco=dados.endereco,
        bairro=dados.bairro,
        cep=dados.cep,
        latitude=dados.latitude,
        longitude=dados.longitude,
        status=StatusOcorrencia.ANALISE,
        urgencia=UrgenciaOcorrencia.BAIXA,
        contador_apoios=0,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router.post(
    "/{ocorrencia_id}/apoiar",
    summary="Apoiar denúncia existente (+1 urgência)"
)
def apoiar_ocorrencia(
    ocorrencia_id: int,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_current_cidadao),
):
    """
    Cidadão dá '+1' numa ocorrência. Aumenta o contador_apoios e recalcula urgência.
    Mesmo cidadão não pode apoiar 2x a mesma ocorrência.
    """
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if not ocorrencia:
        raise HTTPException(404, "Ocorrência não encontrada")

    if ocorrencia.cidadao_id == cidadao.id:
        raise HTTPException(400, "Você não pode apoiar sua própria denúncia")

    # Verifica se já apoiou
    apoio_existente = db.query(ApoioDuplicata).filter(
        ApoioDuplicata.ocorrencia_id == ocorrencia_id,
        ApoioDuplicata.cidadao_id == cidadao.id
    ).first()

    if apoio_existente:
        raise HTTPException(409, "Você já apoiou essa denúncia")

    # Registra apoio
    novo_apoio = ApoioDuplicata(
        ocorrencia_id=ocorrencia_id,
        cidadao_id=cidadao.id,
    )
    db.add(novo_apoio)

    # Atualiza contador e urgência
    ocorrencia.contador_apoios += 1
    ocorrencia.urgencia = calcular_urgencia(ocorrencia.contador_apoios)

    db.commit()
    db.refresh(ocorrencia)

    return {
        "mensagem": "Apoio registrado com sucesso",
        "total_apoios": ocorrencia.contador_apoios,
        "urgencia": ocorrencia.urgencia.value,
    }


@router.get(
    "/minhas",
    response_model=List[OcorrenciaResponse],
    summary="Listar minhas denúncias (cidadão)"
)
def listar_minhas_ocorrencias(
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_current_cidadao),
):
    return db.query(Ocorrencia)\
        .filter(Ocorrencia.cidadao_id == cidadao.id)\
        .order_by(Ocorrencia.criado_em.desc())\
        .all()


# ════════════════════════════════════════════════════════════
#  ENDPOINTS DO PAINEL (funcionários)
# ════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=List[OcorrenciaCompleta],
    summary="Listar ocorrências (painel)"
)
def listar_ocorrencias(
    status_filtro: Optional[StatusOcorrencia] = Query(None, alias="status"),
    secretaria_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    urgencia: Optional[UrgenciaOcorrencia] = None,
    bairro: Optional[str] = None,
    busca: Optional[str] = Query(None, description="Busca por protocolo ou descrição"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    """
    Lista ocorrências com filtros. Usuário de perfil 'secretaria'
    vê SOMENTE as ocorrências da sua secretaria.
    """
    query = db.query(Ocorrencia).options(
        joinedload(Ocorrencia.cidadao),
        joinedload(Ocorrencia.categoria),
        joinedload(Ocorrencia.secretaria),
        joinedload(Ocorrencia.equipe),
        joinedload(Ocorrencia.fotos),
    )

    # Filtro automático por secretaria (perfil secretaria)
    if usuario.perfil == PerfilUsuario.SECRETARIA:
        query = query.filter(Ocorrencia.secretaria_id == usuario.secretaria_id)
    elif secretaria_id:
        query = query.filter(Ocorrencia.secretaria_id == secretaria_id)

    if status_filtro:
        query = query.filter(Ocorrencia.status == status_filtro)
    if categoria_id:
        query = query.filter(Ocorrencia.categoria_id == categoria_id)
    if urgencia:
        query = query.filter(Ocorrencia.urgencia == urgencia)
    if bairro:
        query = query.filter(Ocorrencia.bairro.ilike(f"%{bairro}%"))
    if busca:
        query = query.filter(
            or_(
                Ocorrencia.protocolo.ilike(f"%{busca}%"),
                Ocorrencia.descricao.ilike(f"%{busca}%"),
            )
        )

    resultados = query.order_by(Ocorrencia.criado_em.desc())\
        .limit(limit).offset(offset).all()

    # Monta resposta enriquecida
    return [
        OcorrenciaCompleta(
            **{c.name: getattr(o, c.name) for c in Ocorrencia.__table__.columns},
            cidadao_nome=o.cidadao.nome_completo if o.cidadao else None,
            cidadao_telefone=o.cidadao.telefone if o.cidadao else None,
            categoria_nome=o.categoria.nome if o.categoria else None,
            categoria_icone=o.categoria.icone if o.categoria else None,
            secretaria_nome=o.secretaria.nome if o.secretaria else None,
            equipe_nome=o.equipe.nome if o.equipe else None,
            fotos_urls=[f.url for f in o.fotos],
        )
        for o in resultados
    ]


@router.get(
    "/{ocorrencia_id}",
    response_model=OcorrenciaCompleta,
    summary="Detalhes da ocorrência"
)
def obter_ocorrencia(
    ocorrencia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    o = db.query(Ocorrencia).options(
        joinedload(Ocorrencia.cidadao),
        joinedload(Ocorrencia.categoria),
        joinedload(Ocorrencia.secretaria),
        joinedload(Ocorrencia.equipe),
        joinedload(Ocorrencia.fotos),
    ).filter(Ocorrencia.id == ocorrencia_id).first()

    if not o:
        raise HTTPException(404, "Ocorrência não encontrada")

    # Secretaria só vê o que é dela
    if usuario.perfil == PerfilUsuario.SECRETARIA:
        if o.secretaria_id != usuario.secretaria_id:
            raise HTTPException(403, "Você não tem acesso a esta ocorrência")

    return OcorrenciaCompleta(
        **{c.name: getattr(o, c.name) for c in Ocorrencia.__table__.columns},
        cidadao_nome=o.cidadao.nome_completo if o.cidadao else None,
        cidadao_telefone=o.cidadao.telefone if o.cidadao else None,
        categoria_nome=o.categoria.nome if o.categoria else None,
        categoria_icone=o.categoria.icone if o.categoria else None,
        secretaria_nome=o.secretaria.nome if o.secretaria else None,
        equipe_nome=o.equipe.nome if o.equipe else None,
        fotos_urls=[f.url for f in o.fotos],
    )


@router.patch(
    "/{ocorrencia_id}",
    response_model=OcorrenciaResponse,
    summary="Atualizar ocorrência (painel)"
)
async def atualizar_ocorrencia(
    ocorrencia_id: int,
    dados: OcorrenciaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    """
    Atualiza status, secretaria, equipe ou observações.
    Registra mudança no histórico de auditoria.
    Envia notificação push ao cidadão quando o status muda.
    """
    o = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if not o:
        raise HTTPException(404, "Ocorrência não encontrada")

    # Secretaria só pode mexer no que é dela
    if usuario.perfil == PerfilUsuario.SECRETARIA:
        if o.secretaria_id != usuario.secretaria_id:
            raise HTTPException(403, "Você não tem acesso a esta ocorrência")

    # Captura estado anterior para o histórico
    status_anterior = o.status
    secretaria_anterior = o.secretaria_id
    equipe_anterior = o.equipe_id

    # Aplica mudanças
    dados_dict = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_dict.items():
        setattr(o, campo, valor)

    # Se status foi para 'resolvida', registra data
    if dados.status == StatusOcorrencia.RESOLVIDA and status_anterior != StatusOcorrencia.RESOLVIDA:
        o.data_resolucao = datetime.now(timezone.utc)

    # Registra histórico (se houve mudança de status)
    houve_mudanca_status = dados.status and dados.status != status_anterior
    if houve_mudanca_status:
        historico = HistoricoStatus(
            ocorrencia_id=o.id,
            usuario_id=usuario.id,
            status_anterior=status_anterior,
            status_novo=dados.status,
            secretaria_anterior_id=secretaria_anterior,
            secretaria_nova_id=dados.secretaria_id or secretaria_anterior,
            equipe_anterior_id=equipe_anterior,
            equipe_nova_id=dados.equipe_id or equipe_anterior,
            observacao=dados.observacao_interna,
        )
        db.add(historico)

    db.commit()
    db.refresh(o)

    # 🔔 Envia notificação push ao cidadão (após commit, em try para nunca quebrar a request)
    if houve_mudanca_status:
        try:
            from app.services.push_service import PushService
            await PushService.notificar_mudanca_status(
                db=db,
                ocorrencia=o,
                status_anterior=str(status_anterior.value if hasattr(status_anterior, "value") else status_anterior),
                status_novo=str(dados.status.value if hasattr(dados.status, "value") else dados.status),
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erro ao enviar push: {e}")

    return o
