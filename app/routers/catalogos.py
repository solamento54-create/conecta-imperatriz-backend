"""
Endpoints dos catálogos: Secretarias, Categorias, Equipes.
- GET é público (necessário pro app listar opções)
- POST/PATCH/DELETE exigem admin
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.secretaria import Secretaria
from app.models.categoria import Categoria
from app.models.equipe import Equipe
from app.models.usuario import Usuario
from app.schemas.secretaria import SecretariaCreate, SecretariaUpdate, SecretariaResponse
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse
from app.schemas.equipe import EquipeCreate, EquipeUpdate, EquipeResponse


# ════════════════════════════════════════════════════════════
#  SECRETARIAS
# ════════════════════════════════════════════════════════════
router_secretarias = APIRouter(prefix="/secretarias", tags=["Secretarias"])


@router_secretarias.get("", response_model=List[SecretariaResponse])
def listar_secretarias(
    apenas_ativas: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Secretaria)
    if apenas_ativas:
        query = query.filter(Secretaria.ativo == True)
    return query.order_by(Secretaria.nome).all()


@router_secretarias.post("", response_model=SecretariaResponse, status_code=status.HTTP_201_CREATED)
def criar_secretaria(
    dados: SecretariaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    if db.query(Secretaria).filter(Secretaria.slug == dados.slug).first():
        raise HTTPException(409, "Slug já existe")
    nova = Secretaria(**dados.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router_secretarias.patch("/{id}", response_model=SecretariaResponse)
def atualizar_secretaria(
    id: int,
    dados: SecretariaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    s = db.query(Secretaria).filter(Secretaria.id == id).first()
    if not s:
        raise HTTPException(404, "Secretaria não encontrada")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


# ════════════════════════════════════════════════════════════
#  CATEGORIAS
# ════════════════════════════════════════════════════════════
router_categorias = APIRouter(prefix="/categorias", tags=["Categorias"])


@router_categorias.get("", response_model=List[CategoriaResponse])
def listar_categorias(
    secretaria_id: int = None,
    apenas_ativas: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Categoria)
    if apenas_ativas:
        query = query.filter(Categoria.ativo == True)
    if secretaria_id:
        query = query.filter(Categoria.secretaria_id == secretaria_id)
    return query.order_by(Categoria.nome).all()


@router_categorias.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    if db.query(Categoria).filter(Categoria.slug == dados.slug).first():
        raise HTTPException(409, "Slug já existe")
    if not db.query(Secretaria).filter(Secretaria.id == dados.secretaria_id).first():
        raise HTTPException(404, "Secretaria não encontrada")
    nova = Categoria(**dados.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router_categorias.patch("/{id}", response_model=CategoriaResponse)
def atualizar_categoria(
    id: int,
    dados: CategoriaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    c = db.query(Categoria).filter(Categoria.id == id).first()
    if not c:
        raise HTTPException(404, "Categoria não encontrada")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


# ════════════════════════════════════════════════════════════
#  EQUIPES
# ════════════════════════════════════════════════════════════
router_equipes = APIRouter(prefix="/equipes", tags=["Equipes"])


@router_equipes.get("", response_model=List[EquipeResponse])
def listar_equipes(
    secretaria_id: int = None,
    apenas_ativas: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Equipe)
    if apenas_ativas:
        query = query.filter(Equipe.ativo == True)
    if secretaria_id:
        query = query.filter(Equipe.secretaria_id == secretaria_id)
    return query.order_by(Equipe.nome).all()


@router_equipes.post("", response_model=EquipeResponse, status_code=status.HTTP_201_CREATED)
def criar_equipe(
    dados: EquipeCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    if not db.query(Secretaria).filter(Secretaria.id == dados.secretaria_id).first():
        raise HTTPException(404, "Secretaria não encontrada")
    nova = Equipe(**dados.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router_equipes.patch("/{id}", response_model=EquipeResponse)
def atualizar_equipe(
    id: int,
    dados: EquipeUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    e = db.query(Equipe).filter(Equipe.id == id).first()
    if not e:
        raise HTTPException(404, "Equipe não encontrada")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return e
