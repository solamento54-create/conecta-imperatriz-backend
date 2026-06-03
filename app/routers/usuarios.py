"""
Endpoints de gestão de Usuários (funcionários).
TODOS os endpoints exigem perfil ADMIN.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.core.deps import require_admin
from app.models.usuario import Usuario
from app.models.enums import PerfilUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse


router = APIRouter(prefix="/usuarios", tags=["Usuários (Admin)"])


@router.get("", response_model=List[UsuarioResponse])
def listar_usuarios(
    perfil: Optional[PerfilUsuario] = None,
    secretaria_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    query = db.query(Usuario)
    if perfil:
        query = query.filter(Usuario.perfil == perfil)
    if secretaria_id:
        query = query.filter(Usuario.secretaria_id == secretaria_id)
    if ativo is not None:
        query = query.filter(Usuario.ativo == ativo)
    return query.order_by(Usuario.nome_completo).all()


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    # Unicidade
    if db.query(Usuario).filter(Usuario.cpf == dados.cpf).first():
        raise HTTPException(409, "CPF já cadastrado")
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(409, "E-mail já cadastrado")

    novo = Usuario(
        cpf=dados.cpf,
        nome_completo=dados.nome_completo,
        email=dados.email,
        telefone=dados.telefone,
        cargo=dados.cargo,
        senha_hash=hash_password(dados.senha),
        perfil=dados.perfil,
        secretaria_id=dados.secretaria_id,
        ativo=True,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(404, "Usuário não encontrado")
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(404, "Usuário não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Desativa (soft-delete) um usuário. Não apaga do banco."""
    if usuario_id == admin.id:
        raise HTTPException(400, "Você não pode desativar a si mesmo")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(404, "Usuário não encontrado")

    usuario.ativo = False
    db.commit()
