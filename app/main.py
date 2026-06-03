"""
═══════════════════════════════════════════════════════════════
  Conecta Imperatriz — API REST
  Backend FastAPI para sistema de denúncias municipais
═══════════════════════════════════════════════════════════════
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import auth, ocorrencias, usuarios, catalogos, relatorios, fotos, push


# ────────────────────────────────────────────────────────────
#  Lifespan: executado ao iniciar e ao desligar a API
# ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📦 Ambiente: {settings.APP_ENV}")
    print(f"🗄️  Banco: {settings.DATABASE_URL.split('@')[-1]}")
    yield
    # Shutdown
    print("👋 Encerrando API...")


# ────────────────────────────────────────────────────────────
#  Instância FastAPI
# ────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    # Conecta Imperatriz 🏛️

    API REST do sistema de denúncias municipais da Prefeitura de Imperatriz/MA.

    ## Estrutura

    **Para cidadãos (app mobile):**
    - 📱 Cadastro e login de cidadãos
    - 📸 Criar denúncias com foto e localização GPS
    - 👥 Apoiar denúncias existentes (aumenta urgência)
    - 📊 Acompanhar status das próprias denúncias

    **Para funcionários (painel web):**
    - 🔐 Login com 3 perfis: Admin, Fiscal, Responsável de Secretaria
    - 📋 Listar e filtrar ocorrências
    - ⚙️ Atualizar status, atribuir secretaria/equipe
    - 📈 Dashboard com KPIs e gráficos
    - 👤 Gestão de usuários (somente Admin)

    ## Autenticação

    Use o endpoint `/auth/login-usuario` ou `/auth/login-cidadao` para obter um token JWT.
    Inclua-o no header de requisições autenticadas: `Authorization: Bearer SEU_TOKEN`
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",       # Swagger
    redoc_url="/redoc",     # ReDoc (alternativa)
    lifespan=lifespan,
)


# ────────────────────────────────────────────────────────────
#  CORS — permite chamadas do painel web e app
# ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────────────────────────
#  Endpoints raiz
# ────────────────────────────────────────────────────────────
@app.get("/", tags=["Status"])
def root():
    return {
        "api": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "status": "online",
        "documentacao": "/docs",
    }


@app.get("/health", tags=["Status"])
def health_check():
    """Verificação de saúde da API."""
    return {"status": "healthy"}


# ────────────────────────────────────────────────────────────
#  Routers (todos com prefix /api/v1)
# ────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(ocorrencias.router, prefix=API_PREFIX)
app.include_router(fotos.router, prefix=API_PREFIX)
app.include_router(usuarios.router, prefix=API_PREFIX)
app.include_router(catalogos.router_secretarias, prefix=API_PREFIX)
app.include_router(catalogos.router_categorias, prefix=API_PREFIX)
app.include_router(catalogos.router_equipes, prefix=API_PREFIX)
app.include_router(relatorios.router, prefix=API_PREFIX)
app.include_router(push.router, prefix=API_PREFIX)


# ────────────────────────────────────────────────────────────
#  Servir uploads localmente (modo 'local' apenas)
# ────────────────────────────────────────────────────────────
if settings.STORAGE_MODE == "local":
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
    print(f"📁 Storage local ativo: servindo de {upload_dir}")


# ────────────────────────────────────────────────────────────
#  Handler de erros genérico
# ────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def excecao_generica(request, exc: Exception):
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "tipo": type(exc).__name__}
    )


# ────────────────────────────────────────────────────────────
#  Permite rodar com: python -m app.main
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_DEBUG,
    )
