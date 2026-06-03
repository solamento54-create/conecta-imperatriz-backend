"""
Funções de segurança: hash de senha (bcrypt) e tokens JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings


# ── Hash bcrypt (usando o módulo bcrypt diretamente) ─────────

def hash_password(senha_em_texto: str) -> str:
    """
    Gera hash bcrypt da senha. NUNCA salve senha em texto.
    Trunca em 72 bytes (limite do bcrypt).
    """
    senha_bytes = senha_em_texto.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha_bytes, salt).decode("utf-8")


def verificar_senha(senha_em_texto: str, senha_hash: str) -> bool:
    """Compara senha digitada com hash salvo no banco."""
    try:
        senha_bytes = senha_em_texto.encode("utf-8")[:72]
        return bcrypt.checkpw(senha_bytes, senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── JWT (JSON Web Tokens) ────────────────────────────────────

def criar_access_token(
    dados: Dict[str, Any],
    expira_em: Optional[timedelta] = None
) -> str:
    """
    Gera um token JWT.

    O 'dados' tipicamente contém:
        - sub: ID do usuário (subject)
        - tipo: 'cidadao' ou 'usuario'
        - perfil: 'admin', 'fiscal', 'secretaria' (se for usuario)
        - secretaria_id: int (se for usuario de secretaria)
    """
    payload = dados.copy()

    if expira_em is None:
        expira_em = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expira = datetime.now(timezone.utc) + expira_em
    payload.update({"exp": expira, "iat": datetime.now(timezone.utc)})

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def decodificar_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida um token JWT.
    Retorna o payload se válido, None se inválido/expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
