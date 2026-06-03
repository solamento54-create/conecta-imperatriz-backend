"""
Conexão com o banco PostgreSQL via SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings


# ── Engine: a "conexão" com o banco ──────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,    # testa conexão antes de usar
    pool_size=10,          # 10 conexões abertas
    max_overflow=20,       # mais 20 em caso de pico
    echo=settings.APP_DEBUG,  # mostra SQL no terminal em dev
)

# ── SessionLocal: cria sessões para cada request ─────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base: todos os modelos herdam dela ───────────────────────
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency do FastAPI para injetar sessão de banco nos endpoints.
    Garante que a sessão é fechada ao final, mesmo se der erro.

    Uso:
        @router.get("/algo")
        def listar(db: Session = Depends(get_db)):
            return db.query(Modelo).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
