"""
Endpoints de Relatórios e Dashboard.
"""
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.core.database import get_db
from app.core.deps import require_qualquer_usuario
from app.models.ocorrencia import Ocorrencia
from app.models.secretaria import Secretaria
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.models.enums import StatusOcorrencia, UrgenciaOcorrencia, PerfilUsuario


router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/dashboard")
def kpis_dashboard(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    """KPIs principais do dashboard (números do topo)."""
    query = db.query(Ocorrencia)

    # Filtro automático para perfil secretaria
    if usuario.perfil == PerfilUsuario.SECRETARIA:
        query = query.filter(Ocorrencia.secretaria_id == usuario.secretaria_id)

    total = query.count()
    em_analise = query.filter(Ocorrencia.status == StatusOcorrencia.ANALISE).count()
    em_execucao = query.filter(Ocorrencia.status == StatusOcorrencia.EXECUCAO).count()
    resolvidas = query.filter(Ocorrencia.status == StatusOcorrencia.RESOLVIDA).count()
    criticas = query.filter(Ocorrencia.urgencia == UrgenciaOcorrencia.CRITICA).count()

    # Últimos 30 dias
    trinta_dias = datetime.now(timezone.utc) - timedelta(days=30)
    novas_30d = query.filter(Ocorrencia.criado_em >= trinta_dias).count()

    return {
        "total": total,
        "em_analise": em_analise,
        "em_execucao": em_execucao,
        "resolvidas": resolvidas,
        "criticas": criticas,
        "novas_ultimos_30_dias": novas_30d,
    }


@router.get("/por-secretaria")
def ocorrencias_por_secretaria(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_qualquer_usuario),
):
    """Contagem agrupada por secretaria."""
    resultado = db.query(
        Secretaria.id,
        Secretaria.nome,
        Secretaria.cor,
        func.count(Ocorrencia.id).label("total"),
        func.sum(case((Ocorrencia.status == StatusOcorrencia.ANALISE, 1), else_=0)).label("em_analise"),
        func.sum(case((Ocorrencia.status == StatusOcorrencia.EXECUCAO, 1), else_=0)).label("em_execucao"),
        func.sum(case((Ocorrencia.status == StatusOcorrencia.RESOLVIDA, 1), else_=0)).label("resolvidas"),
    ).outerjoin(Ocorrencia, Ocorrencia.secretaria_id == Secretaria.id)\
     .group_by(Secretaria.id, Secretaria.nome, Secretaria.cor)\
     .order_by(Secretaria.nome).all()

    return [
        {
            "secretaria_id": r.id,
            "nome": r.nome,
            "cor": r.cor,
            "total": r.total or 0,
            "em_analise": r.em_analise or 0,
            "em_execucao": r.em_execucao or 0,
            "resolvidas": r.resolvidas or 0,
        }
        for r in resultado
    ]


@router.get("/por-categoria")
def ocorrencias_por_categoria(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_qualquer_usuario),
):
    """Contagem agrupada por categoria (tipo de problema)."""
    resultado = db.query(
        Categoria.id,
        Categoria.nome,
        Categoria.icone,
        Categoria.cor,
        func.count(Ocorrencia.id).label("total"),
    ).outerjoin(Ocorrencia, Ocorrencia.categoria_id == Categoria.id)\
     .group_by(Categoria.id, Categoria.nome, Categoria.icone, Categoria.cor)\
     .order_by(func.count(Ocorrencia.id).desc()).all()

    return [
        {
            "categoria_id": r.id,
            "nome": r.nome,
            "icone": r.icone,
            "cor": r.cor,
            "total": r.total or 0,
        }
        for r in resultado
    ]


@router.get("/evolucao-mensal")
def evolucao_mensal(
    meses: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_qualquer_usuario),
):
    """Ocorrências criadas por mês (últimos N meses)."""
    inicio = datetime.now(timezone.utc) - timedelta(days=meses * 30)

    query = db.query(
        func.date_trunc("month", Ocorrencia.criado_em).label("mes"),
        func.count(Ocorrencia.id).label("total"),
        func.sum(case((Ocorrencia.status == StatusOcorrencia.RESOLVIDA, 1), else_=0)).label("resolvidas"),
    ).filter(Ocorrencia.criado_em >= inicio)

    if usuario.perfil == PerfilUsuario.SECRETARIA:
        query = query.filter(Ocorrencia.secretaria_id == usuario.secretaria_id)

    resultado = query.group_by("mes").order_by("mes").all()

    return [
        {
            "mes": r.mes.strftime("%Y-%m"),
            "total": r.total or 0,
            "resolvidas": r.resolvidas or 0,
        }
        for r in resultado
    ]
