"""Modelo Usuario (funcionários da prefeitura)."""
from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, ForeignKey,
    Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import PerfilUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, index=True)
    cpf = Column(String(14), unique=True, nullable=False)
    nome_completo = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    telefone = Column(String(20))
    cargo = Column(String(100))
    senha_hash = Column(String(255), nullable=False)

    # IMPORTANTE: values_callable força o SQLAlchemy a usar os valores
    # do enum (minúsculos: 'admin', 'fiscal', 'secretaria') em vez dos
    # nomes (maiúsculos: 'ADMIN', 'FISCAL', 'SECRETARIA').
    perfil = Column(
        SQLEnum(
            PerfilUsuario,
            name="perfil_usuario",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        nullable=False,
    )

    secretaria_id = Column(BigInteger, ForeignKey("secretarias.id"))
    token_recuperacao = Column(String(255))
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True))

    # Regra: perfil 'secretaria' obriga secretaria_id; admin/fiscal proíbe
    __table_args__ = (
        CheckConstraint(
            "(perfil = 'secretaria' AND secretaria_id IS NOT NULL) OR "
            "(perfil IN ('admin', 'fiscal') AND secretaria_id IS NULL)",
            name="chk_perfil_secretaria"
        ),
    )

    secretaria = relationship("Secretaria", back_populates="usuarios")
    historico_alteracoes = relationship("HistoricoStatus", back_populates="usuario")
