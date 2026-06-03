"""
Dependencies do FastAPI para autenticação e autorização.
Usadas nos endpoints com Depends() para garantir que o usuário está logado
e tem o perfil correto.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.cidadao import Cidadao
from app.models.enums import PerfilUsuario


# OAuth2 scheme — onde o cliente envia o token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login-usuario")


# ────────────────────────────────────────────────────────────
#  Validação de token e busca do usuário/cidadão atual
# ────────────────────────────────────────────────────────────

def get_current_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """Decodifica e valida o JWT. Retorna o payload."""
    payload = decodificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_cidadao(
    payload: dict = Depends(get_current_payload),
    db: Session = Depends(get_db),
) -> Cidadao:
    """Retorna o cidadão logado a partir do token."""
    if payload.get("tipo") != "cidadao":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta rota é exclusiva para cidadãos"
        )

    cidadao_id = payload.get("sub")
    cidadao = db.query(Cidadao).filter(Cidadao.id == int(cidadao_id)).first()

    if not cidadao or not cidadao.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cidadão não encontrado ou inativo"
        )
    return cidadao


def get_current_usuario(
    payload: dict = Depends(get_current_payload),
    db: Session = Depends(get_db),
) -> Usuario:
    """Retorna o usuário (funcionário) logado a partir do token."""
    if payload.get("tipo") != "usuario":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta rota é exclusiva para funcionários da prefeitura"
        )

    usuario_id = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )
    return usuario


# ────────────────────────────────────────────────────────────
#  Autorização por perfil (camadas)
# ────────────────────────────────────────────────────────────

def require_admin(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
    """Exige perfil ADMIN."""
    if usuario.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return usuario


def require_admin_ou_fiscal(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
    """Exige perfil ADMIN ou FISCAL."""
    if usuario.perfil not in (PerfilUsuario.ADMIN, PerfilUsuario.FISCAL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores ou fiscais"
        )
    return usuario


def require_qualquer_usuario(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
    """Qualquer usuário logado (admin/fiscal/secretaria)."""
    return usuario
