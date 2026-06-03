"""
Dependências FastAPI compartilhadas pelos routers.
Inclui: obter usuário do JWT, autorização por perfil, etc.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario
from app.models.cidadao import Cidadao
from app.models.enums import PerfilUsuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login-usuario", auto_error=False)


def _decode_token(token: str) -> dict:
    """Decodifica e valida o JWT. Lança 401 se inválido."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependência: obtém o Usuario (admin/fiscal/secretaria) do JWT."""
    payload = _decode_token(token)
    if payload.get("tipo") != "usuario":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este endpoint é para usuários do painel.",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token sem identificador")
    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(401, "Usuário inativo ou não encontrado")
    return usuario


def get_cidadao_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Cidadao:
    """Dependência: obtém o Cidadao do JWT."""
    payload = _decode_token(token)
    if payload.get("tipo") != "cidadao":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este endpoint é para cidadãos.",
        )
    cidadao_id = payload.get("sub")
    if not cidadao_id:
        raise HTTPException(401, "Token sem identificador")
    cidadao = db.query(Cidadao).filter(Cidadao.id == int(cidadao_id)).first()
    if not cidadao or not cidadao.ativo:
        raise HTTPException(401, "Cidadão inativo ou não encontrado")
    return cidadao


def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Apenas perfil admin pode acessar."""
    if usuario.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(403, "Acesso restrito a administradores")
    return usuario


def require_admin_ou_fiscal(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Admin ou fiscal podem acessar."""
    if usuario.perfil not in (PerfilUsuario.ADMIN, PerfilUsuario.FISCAL):
        raise HTTPException(403, "Acesso restrito a admin ou fiscal")
    return usuario


def require_qualquer_usuario(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Qualquer usuário do painel (admin, fiscal, secretaria) pode acessar."""
    return usuario
