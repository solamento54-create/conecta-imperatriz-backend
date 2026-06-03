"""
Router de notificações push e dispositivos.

Endpoints:
  POST   /push/dispositivos                  → Cidadão registra seu token Expo
  DELETE /push/dispositivos/{token}          → Remove um token (logout)
  GET    /push/notificacoes                  → Lista notificações do cidadão
  PATCH  /push/notificacoes/{id}/marcar-lida → Marca notificação como lida
  POST   /push/teste                         → (DEV) Envia push de teste
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.core.deps import get_cidadao_atual
from app.models.dispositivo_push import DispositivoPush
from app.models.notificacao import Notificacao
from app.models.cidadao import Cidadao
from app.schemas.push import (
    DispositivoPushRegistrar,
    DispositivoPushResposta,
    NotificacaoResposta,
)
from app.services.push_service import PushService

router = APIRouter(prefix="/push", tags=["Notificações Push"])


# ─────────────────────────────────────────────────────────────
#  DISPOSITIVOS
# ─────────────────────────────────────────────────────────────

@router.post("/dispositivos", response_model=DispositivoPushResposta,
             summary="Cidadão registra seu token push")
def registrar_dispositivo(
    dados: DispositivoPushRegistrar,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_cidadao_atual),
):
    """
    Chamado pelo app quando o cidadão concede permissão de notificação.
    Se o mesmo token já existe (mesmo celular abriu de novo), atualiza
    o vínculo com o cidadão atual (caso o aparelho tenha trocado de dono).
    """
    existente = db.query(DispositivoPush).filter(
        DispositivoPush.expo_token == dados.expo_token
    ).first()

    if existente:
        existente.cidadao_id = cidadao.id
        existente.plataforma = dados.plataforma or existente.plataforma
        existente.modelo     = dados.modelo or existente.modelo
        existente.ativo      = True
        existente.ultimo_uso = datetime.utcnow()
        db.commit()
        db.refresh(existente)
        return existente

    novo = DispositivoPush(
        cidadao_id = cidadao.id,
        expo_token = dados.expo_token,
        plataforma = dados.plataforma,
        modelo     = dados.modelo,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.delete("/dispositivos/{token:path}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove o token do dispositivo (logout)")
def remover_dispositivo(
    token: str,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_cidadao_atual),
):
    """Chamado pelo app no logout para parar de receber push."""
    disp = db.query(DispositivoPush).filter(
        DispositivoPush.expo_token == token,
        DispositivoPush.cidadao_id == cidadao.id,
    ).first()
    if disp:
        db.delete(disp)
        db.commit()


# ─────────────────────────────────────────────────────────────
#  NOTIFICAÇÕES (histórico no app)
# ─────────────────────────────────────────────────────────────

@router.get("/notificacoes", response_model=List[NotificacaoResposta],
            summary="Lista notificações do cidadão")
def listar_notificacoes(
    apenas_nao_lidas: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_cidadao_atual),
):
    """
    Lista notificações ordenadas da mais recente para a mais antiga.
    Mostra também as não enviadas por push (caso o cidadão não tivesse o app aberto).
    """
    q = db.query(Notificacao).filter(Notificacao.cidadao_id == cidadao.id)
    if apenas_nao_lidas:
        q = q.filter(Notificacao.lida == False)
    return q.order_by(desc(Notificacao.criado_em)).limit(limit).all()


@router.patch("/notificacoes/{notif_id}/marcar-lida", response_model=NotificacaoResposta,
              summary="Marca notificação como lida")
def marcar_lida(
    notif_id: int,
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_cidadao_atual),
):
    notif = db.query(Notificacao).filter(
        Notificacao.id == notif_id,
        Notificacao.cidadao_id == cidadao.id,
    ).first()
    if not notif:
        raise HTTPException(404, "Notificação não encontrada")
    if not notif.lida:
        notif.lida = True
        notif.lida_em = datetime.utcnow()
        db.commit()
    db.refresh(notif)
    return notif


# ─────────────────────────────────────────────────────────────
#  TESTE (útil em dev)
# ─────────────────────────────────────────────────────────────

@router.post("/teste", summary="(DEV) Envia push de teste para o cidadão logado")
async def teste_push(
    db: Session = Depends(get_db),
    cidadao: Cidadao = Depends(get_cidadao_atual),
):
    """
    Endpoint útil para testar se as notificações estão chegando.
    Envia push para todos os dispositivos do cidadão logado.
    """
    n = await PushService.enviar_para_cidadao(
        db=db,
        cidadao_id=cidadao.id,
        titulo="🔔 Notificação de teste",
        corpo="Se você está vendo isso, as notificações estão funcionando!",
        dados_extras={"tipo": "teste"},
    )
    return {"enviadas": n, "mensagem": "Teste enviado" if n > 0 else "Nenhum dispositivo cadastrado"}
