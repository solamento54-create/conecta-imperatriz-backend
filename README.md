# Conecta Imperatriz — Backend API

API REST em **FastAPI + PostgreSQL** para o sistema de denúncias municipais da Prefeitura de Imperatriz/MA.

## 📦 O que tem nesta API

- ✅ Autenticação JWT (cidadão e funcionários da prefeitura)
- ✅ Cadastro de cidadãos com validação de CPF
- ✅ Criação de denúncias com geolocalização
- ✅ Detecção automática de duplicatas por raio (50m)
- ✅ Sistema de apoios (+1 urgência)
- ✅ Cálculo automático de urgência (baixa → crítica)
- ✅ Histórico de auditoria de mudanças
- ✅ Filtro automático por secretaria (perfil "secretaria" só vê o que é dele)
- ✅ Gestão de usuários, secretarias, categorias e equipes
- ✅ Dashboard com KPIs e estatísticas
- ✅ Documentação automática (Swagger UI)

## 🚀 Como rodar localmente

### 1. Pré-requisitos
- Python 3.11+
- PostgreSQL 15+ rodando

### 2. Crie o banco e rode o SQL da Etapa 1
```bash
psql -U postgres -c "CREATE DATABASE conecta_imperatriz;"
psql -U postgres -d conecta_imperatriz -f conecta-imperatriz.sql
```

### 3. Configure o ambiente Python
```bash
cd backend

# Criar virtualenv
python3 -m venv venv
source venv/bin/activate           # Linux/Mac
# venv\Scripts\activate            # Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar variáveis de ambiente
cp .env.example .env
# Edite .env com sua DATABASE_URL e JWT_SECRET_KEY
```

### 4. Rode a API
```bash
uvicorn app.main:app --reload
```

A API estará em `http://localhost:8000`.

## 📚 Documentação interativa

Acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Os dois mostram TODOS os endpoints com exemplos prontos para testar.

## 🗂️ Estrutura

```
backend/
├── app/
│   ├── core/             # config, banco, segurança, dependências
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py   # bcrypt + JWT
│   │   └── deps.py       # validação de token e permissões
│   ├── models/           # 10 tabelas SQLAlchemy
│   ├── schemas/          # validação Pydantic (entrada/saída)
│   ├── routers/          # endpoints organizados
│   │   ├── auth.py       # login e cadastro
│   │   ├── ocorrencias.py
│   │   ├── usuarios.py
│   │   ├── catalogos.py  # secretarias, categorias, equipes
│   │   └── relatorios.py
│   └── main.py           # ponto de entrada
├── requirements.txt
├── .env.example
└── README.md
```

## 🔐 Perfis e permissões

| Perfil | Pode fazer |
|--------|-----------|
| **admin** | Tudo: gerenciar usuários, secretarias, categorias, ver/editar todas as ocorrências |
| **fiscal** | Ver e editar todas as ocorrências (campo) |
| **secretaria** | Ver e editar SOMENTE ocorrências da própria secretaria |
| **cidadão** | Criar/listar/apoiar suas próprias denúncias |

## 🔑 Exemplos de uso

### Cadastrar cidadão (público)
```http
POST /api/v1/auth/cadastrar-cidadao
Content-Type: application/json

{
  "cpf": "123.456.789-09",
  "nome_completo": "Maria Silva",
  "email": "maria@email.com",
  "telefone": "(99) 99999-1234",
  "senha": "senha123",
  "aceite_lgpd": true
}
```

### Login do cidadão
```http
POST /api/v1/auth/login-cidadao
Content-Type: application/json

{ "email": "maria@email.com", "senha": "senha123" }
```

Resposta:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "tipo": "cidadao",
  "nome": "Maria Silva"
}
```

### Verificar duplicata antes de criar denúncia
```http
POST /api/v1/ocorrencias/check-duplicata
Authorization: Bearer SEU_TOKEN

{
  "categoria_id": 1,
  "latitude": -5.5268,
  "longitude": -47.4677,
  "raio_metros": 50
}
```

### Criar nova ocorrência
```http
POST /api/v1/ocorrencias
Authorization: Bearer SEU_TOKEN

{
  "categoria_id": 1,
  "descricao": "Buraco grande na frente do mercado",
  "endereco": "Rua Principal, 100, Centro",
  "bairro": "Centro",
  "latitude": -5.5268,
  "longitude": -47.4677
}
```

### Apoiar denúncia existente
```http
POST /api/v1/ocorrencias/42/apoiar
Authorization: Bearer SEU_TOKEN
```

### Listar ocorrências (painel)
```http
GET /api/v1/ocorrencias?status=analise&urgencia=critica&limit=20
Authorization: Bearer TOKEN_FUNCIONARIO
```

### Dashboard
```http
GET /api/v1/relatorios/dashboard
Authorization: Bearer TOKEN_FUNCIONARIO
```

## 🛡️ Segurança

- ✅ Senhas com hash **bcrypt** (nunca em texto)
- ✅ Tokens **JWT** com expiração (24h)
- ✅ CORS configurável por ambiente
- ✅ Validação de CPF, e-mail, coordenadas
- ✅ CHECK constraint no banco para integridade de perfil
- ✅ Soft-delete (desativação) em vez de DELETE
- ✅ Auditoria de mudanças (histórico_status)

## 📈 Próximas etapas

- **Etapa 3**: Storage de fotos (AWS S3 ou local)
- **Etapa 4**: Refinar autenticação (refresh tokens, recuperação de senha por e-mail)
- **Etapa 5**: Conectar o painel web (HTML atual) a essa API
- **Etapa 6**: Painel separado para perfil "secretaria"
- **Etapa 7**: App mobile (React Native ou Flutter)

## 📞 Suporte

Para dúvidas, abra uma issue ou contate o time de desenvolvimento.

---

**Conecta Imperatriz** · Prefeitura de Imperatriz/MA · 2026
