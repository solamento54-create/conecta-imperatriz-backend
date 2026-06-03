"""
Endpoints de Autenticação.
- POST /auth/login-cidadao   — login do cidadão (app)
- POST /auth/login-usuario   — login do funcionário (painel)
- POST /auth/cadastrar-cidadao — cadastro pelo app
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verificar_senha, criar_access_token
from app.models.cidadao import Cidadao
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.cidadao import CidadaoCreate, CidadaoResponse


router = APIRouter(prefix="/auth", tags=["Autenticação"])


# ────────────────────────────────────────────────────────────
#  CADASTRO DE CIDADÃO (público)
# ────────────────────────────────────────────────────────────
@router.post(
    "/cadastrar-cidadao",
    response_model=CidadaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo cidadão (via app)",
)
def cadastrar_cidadao(
    dados: CidadaoCreate,
    db: Session = Depends(get_db),
):
    """
    Cadastro de cidadão pelo app mobile.
    - CPF e e-mail devem ser únicos.
    - Senha é criptografada com bcrypt antes de salvar.
    - Aceite LGPD é obrigatório.
    """
    # Verifica se CPF já existe
    if db.query(Cidadao).filter(Cidadao.cpf == dados.cpf).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já cadastrado"
        )

    # Verifica se e-mail já existe
    if db.query(Cidadao).filter(Cidadao.email == dados.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado"
        )

    novo_cidadao = Cidadao(
        cpf=dados.cpf,
        nome_completo=dados.nome_completo,
        email=dados.email,
        telefone=dados.telefone,
        senha_hash=hash_password(dados.senha),
        data_nascimento=dados.data_nascimento,
        data_aceite_lgpd=datetime.now(timezone.utc),
        ativo=True,
    )
    db.add(novo_cidadao)
    db.commit()
    db.refresh(novo_cidadao)
    return novo_cidadao


# ────────────────────────────────────────────────────────────
#  LOGIN DE CIDADÃO
# ────────────────────────────────────────────────────────────
@router.post(
    "/login-cidadao",
    response_model=TokenResponse,
    summary="Login do cidadão (app)"
)
def login_cidadao(
    dados: LoginRequest,
    db: Session = Depends(get_db),
):
    """Autentica cidadão e devolve um JWT."""
    cidadao = db.query(Cidadao).filter(Cidadao.email == dados.email).first()

    if not cidadao or not verificar_senha(dados.senha, cidadao.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )

    if not cidadao.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Entre em contato com a ouvidoria."
        )

    # Atualiza último login
    cidadao.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    # Gera token
    token = criar_access_token({
        "sub": str(cidadao.id),
        "tipo": "cidadao",
        "nome": cidadao.nome_completo,
    })

    return TokenResponse(
        access_token=token,
        tipo="cidadao",
        nome=cidadao.nome_completo,
    )


# ────────────────────────────────────────────────────────────
#  LOGIN DE USUÁRIO (FUNCIONÁRIO)
# ────────────────────────────────────────────────────────────
@router.post(
    "/login-usuario",
    response_model=TokenResponse,
    summary="Login de funcionário (painel)"
)
def login_usuario(
    dados: LoginRequest,
    db: Session = Depends(get_db),
):
    """Autentica funcionário da prefeitura e devolve um JWT."""
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Contate o administrador."
        )

    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    token = criar_access_token({
        "sub": str(usuario.id),
        "tipo": "usuario",
        "perfil": usuario.perfil.value,
        "secretaria_id": usuario.secretaria_id,
        "nome": usuario.nome_completo,
    })

    return TokenResponse(
        access_token=token,
        tipo="usuario",
        nome=usuario.nome_completo,
        perfil=usuario.perfil.value,
    )
