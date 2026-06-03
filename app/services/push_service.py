"""
Serviço de notificações push via Expo Push API.

A Expo oferece um serviço gratuito e ilimitado de envio de push notifications
que funciona em Android e iOS sem precisar configurar Firebase/APNs separadamente.

Endpoint: https://exp.host/--/api/v2/push/send
Documentação: https://docs.expo.dev/push-notifications/sending-notifications/
"""
import logging
from typing import List, Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.models.dispositivo_push import DispositivoPush
from app.models.notificacao import Notificacao
from app.models.ocorrencia import Ocorrencia

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class PushService:
    """
    Envia notificações push para cidadãos via Expo.
    Salva também na tabela `notificacoes` para histórico no app.
    """

    @staticmethod
    async def enviar_para_cidadao(
        db: Session,
        cidadao_id: int,
        titulo: str,
        corpo: str,
        dados_extras: Optional[Dict[str, Any]] = None,
        ocorrencia_id: Optional[int] = None,
    ) -> int:
        """
        Envia push para TODOS os dispositivos ativos do cidadão.
        Retorna o número de dispositivos para os quais foi enviada.
        """
        # 1. Busca os tokens ativos do cidadão
        dispositivos = (
            db.query(DispositivoPush)
            .filter(and_(
                DispositivoPush.cidadao_id == cidadao_id,
                DispositivoPush.ativo == True,
            ))
            .all()
        )

        # 2. Registra no histórico mesmo se não houver dispositivo
        # (assim o cidadão vê quando abrir o app)
        notif = Notificacao(
            cidadao_id=cidadao_id,
            ocorrencia_id=ocorrencia_id,
            titulo=titulo,
            mensagem=corpo,
            canal="push",
            enviada=len(dispositivos) > 0,
            data_envio=datetime.utcnow() if dispositivos else None,
        )
        db.add(notif)
        db.commit()

        if not dispositivos:
            logger.info(f"Cidadão {cidadao_id} sem dispositivos cadastrados — notificação salva apenas no histórico.")
            return 0

        # 3. Monta mensagens Expo
        mensagens = []
        for d in dispositivos:
            mensagens.append({
                "to": d.expo_token,
                "title": titulo,
                "body": corpo,
                "sound": "default",
                "priority": "high",
                "data": {
                    **(dados_extras or {}),
                    "ocorrencia_id": ocorrencia_id,
                    "notificacao_id": notif.id,
                },
            })

        # 4. Envia em batch para Expo
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    EXPO_PUSH_URL,
                    json=mensagens,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                resultado = response.json()

                # 5. Marca tokens inválidos como inativos
                if "data" in resultado:
                    for i, item in enumerate(resultado["data"]):
                        if item.get("status") == "error":
                            erro = item.get("details", {}).get("error")
                            if erro in ("DeviceNotRegistered", "InvalidCredentials"):
                                dispositivos[i].ativo = False
                                logger.warning(f"Token desativado: {dispositivos[i].expo_token[:30]}... ({erro})")
                    db.commit()

            logger.info(f"Push enviado para {len(dispositivos)} dispositivo(s) do cidadão {cidadao_id}")
            return len(dispositivos)

        except httpx.HTTPError as e:
            logger.error(f"Erro ao enviar push via Expo: {e}")
            return 0
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar push: {e}")
            return 0

    @staticmethod
    async def notificar_mudanca_status(
        db: Session, ocorrencia: Ocorrencia, status_anterior: str, status_novo: str
    ):
        """
        Helper específico para mudança de status — formata título e corpo automaticamente.
        Chamado pelo router de ocorrências quando admin/fiscal/secretaria atualiza status.
        """
        if not ocorrencia.cidadao_id:
            return

        # Texto amigável por status
        status_labels = {
            "analise":   "📋 Em análise",
            "execucao":  "🚧 Em execução",
            "resolvida": "✅ Resolvida",
            "rejeitada": "❌ Rejeitada",
        }
        label_novo = status_labels.get(status_novo, status_novo)

        # Mensagens humanizadas por transição
        if status_novo == "execucao":
            titulo = f"Sua denúncia está em execução! 🚧"
            corpo = f"Protocolo {ocorrencia.protocolo}: equipe da prefeitura iniciou os trabalhos no local."
        elif status_novo == "resolvida":
            titulo = f"Sua denúncia foi resolvida! ✅"
            corpo = f"Protocolo {ocorrencia.protocolo}: problema resolvido. Toque para ver os detalhes."
        elif status_novo == "rejeitada":
            titulo = f"Atualização na sua denúncia"
            corpo = f"Protocolo {ocorrencia.protocolo}: {ocorrencia.motivo_rejeicao or 'Não foi possível processar essa ocorrência.'}"
        else:
            titulo = f"Atualização: {label_novo}"
            corpo = f"Protocolo {ocorrencia.protocolo} agora está {status_labels.get(status_novo, status_novo).lower()}"

        await PushService.enviar_para_cidadao(
            db=db,
            cidadao_id=ocorrencia.cidadao_id,
            titulo=titulo,
            corpo=corpo,
            ocorrencia_id=ocorrencia.id,
            dados_extras={
                "tipo": "mudanca_status",
                "status_anterior": status_anterior,
                "status_novo": status_novo,
                "protocolo": ocorrencia.protocolo,
            },
        )

    @staticmethod
    async def notificar_apoio_recebido(
        db: Session, ocorrencia: Ocorrencia, total_apoios: int
    ):
        """
        Notifica o cidadão original quando sua denúncia recebe um novo apoio.
        Só notifica em marcos importantes (5, 10, 25, 50, 100) para não spammar.
        """
        marcos = {5: "5", 10: "10", 25: "25", 50: "50", 100: "100"}
        if total_apoios not in marcos:
            return

        await PushService.enviar_para_cidadao(
            db=db,
            cidadao_id=ocorrencia.cidadao_id,
            titulo=f"Sua denúncia tem {total_apoios} apoios! 👍",
            corpo=f"Protocolo {ocorrencia.protocolo}: outros cidadãos confirmaram esse problema. A urgência foi aumentada!",
            ocorrencia_id=ocorrencia.id,
            dados_extras={"tipo": "novo_apoio", "total": total_apoios},
        )
