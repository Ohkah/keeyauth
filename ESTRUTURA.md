# 📂 Estrutura do Projeto KeyAuth

Visão geral da organização dos arquivos.

```
keyauth-system/
│
├── 📄 README.md                    ← LEIA PRIMEIRO - Documentação principal
├── 📄 QUICKSTART.md                ← Guia rápido (5 minutos)
├── 📄 API.md                       ← Documentação técnica da API
├── 📄 DEPLOY.md                    ← Instruções de deployment
├── 📄 ESTRUTURA.md                 ← Este arquivo
│
├── 🐍 app.py                       ← Aplicação Flask principal
├── 📋 requirements.txt             ← Dependências Python
├── .env.example                    ← Exemplo de variáveis de ambiente
│
├── 🐳 Dockerfile                   ← Imagem Docker
├── 🐳 docker-compose.yml          ← Orquestração dos containers
│
├── 🚀 setup.sh                     ← Script de setup automático
│
├── 🌐 nginx.conf.example           ← Configuração Nginx para produção
│
├── 📁 templates/
│   ├── login.html                  ← Página de login
│   └── index.html                  ← Painel de controle (dashboard)
│
├── 📁 examples/
│   ├── roblox_example.lua         ← Exemplo para scripts Roblox
│   └── standalone_example.lua      ← Exemplo para Lua puro
│
└── 📁 keyauth.lua                  ← Biblioteca Lua para validação
```

## 📝 Descrição dos Arquivos

### Documentação
- **README.md**: Documentação completa do projeto
- **QUICKSTART.md**: Guia rápido para começar em 5 minutos
- **API.md**: Referência técnica de todos os endpoints
- **DEPLOY.md**: Instruções detalhadas para colocar em produção
- **ESTRUTURA.md**: Este arquivo

### Backend
- **app.py**: Aplicação Flask com:
  - Autenticação de administrador
  - API de validação de chaves
  - Painel de controle
  - Gerenciamento do banco de dados

### Frontend
- **templates/login.html**: Tela de login e registro
- **templates/index.html**: Painel completo com:
  - Dashboard com estatísticas
  - Gerenciamento de chaves
  - Criação de novas chaves
  - Interface responsiva

### Bibliotecas
- **keyauth.lua**: Biblioteca Lua para validar chaves
  - Compatível com Roblox
  - Compatível com Lua puro
  - Suporte a cache
  - Geração de device ID

### Configuração
- **requirements.txt**: Dependências Python (Flask, MySQL, etc)
- **.env.example**: Template de variáveis de ambiente
- **docker-compose.yml**: Define serviços (Flask + MySQL)
- **Dockerfile**: Imagem Docker para a aplicação
- **nginx.conf.example**: Configuração do servidor web

### Exemplos
- **examples/roblox_example.lua**: Como usar em scripts Roblox
- **examples/standalone_example.lua**: Como usar em Lua puro

### Scripts
- **setup.sh**: Automatiza setup local ou Docker

---

## 🔄 Fluxo de Funcionamento

### 1. Admin (Você)
```
Browser → http://localhost:5000
         ↓
    Login/Register (templates/login.html)
         ↓
    Painel de Controle (templates/index.html)
         ↓
    app.py processa (criar/deletar/listar chaves)
         ↓
    MySQL armazena dados
```

### 2. Usuário Final (Cliente)
```
Script Lua → keyauth.lua
           ↓
    POST /api/validate → app.py
           ↓
    Validação no MySQL
           ↓
    Response: {valid: true/false, ...}
           ↓
    Script continua ou para
```

---

## 🔌 Endpoints da API

Todos em `app.py`:

**Públicos (sem login):**
- `POST /api/validate` - Valida uma chave
- `GET /api/key-info/{key}` - Info da chave (sem usar)

**Privados (requer login):**
- `GET /api/keys` - Lista chaves do admin
- `POST /api/keys` - Cria nova chave
- `DELETE /api/keys/{id}` - Deleta chave
- `POST /api/keys/{id}/toggle` - Ativa/desativa chave

**Autenticação:**
- `POST /login` - Login do admin
- `POST /register` - Registra primeiro admin
- `GET /logout` - Logout

---

## 📊 Banco de Dados (MySQL)

Tabelas criadas automaticamente:

**admins**
```sql
id: INT (auto_increment)
username: VARCHAR(255) UNIQUE
password_hash: VARCHAR(255)
created_at: TIMESTAMP
```

**keys**
```sql
id: INT (auto_increment)
key_string: VARCHAR(255) UNIQUE
name: VARCHAR(255)
expires_at: DATETIME (NULL = nunca expira)
device_lock: VARCHAR(255) (NULL = qualquer dispositivo)
max_uses: INT (NULL = ilimitado)
uses: INT
is_active: BOOLEAN
created_at: TIMESTAMP
last_used: DATETIME
admin_id: INT (FK → admins)
```

**key_usage**
```sql
id: INT (auto_increment)
key_id: INT (FK → keys)
device_id: VARCHAR(255)
ip_address: VARCHAR(45)
validated_at: TIMESTAMP
```

---

## 🚀 Ciclo de Vida de uma Chave

1. **Criação** (Painel)
   - Admin preenche form em `index.html`
   - POST `/api/keys` chamado
   - `app.py` insere em MySQL
   - Chave gerada: `key_XXXXX...`

2. **Compartilhamento**
   - Admin copia a chave
   - Compartilha com usuário

3. **Uso** (Script Lua)
   - Script importa `keyauth.lua`
   - Chama `auth:validate(key)`
   - POST `/api/validate` → `app.py`
   - MySQL valida expiration, device_lock, max_uses
   - Registra uso em `key_usage`
   - Retorna sucesso/erro

4. **Gerenciamento**
   - Admin vê estatísticas no dashboard
   - Pode desativar, deletar, ou ver último uso

---

## 🔐 Segurança

**Senhas**
- Hash com bcrypt
- Nunca armazenadas em plain text

**Chaves**
- Geradas com `secrets.token_hex(16)`
- Formatadas: `key_XXXXX...`
- Nunca exibidas novamente após criação

**Sessões**
- Flask sessions com SECRET_KEY
- Cookies seguros
- Logout limpa sessão

**API**
- Validação de input
- Device lock optional
- Rate limiting (recomendado em produção)

---

## 📈 Escalabilidade

**Atual (Desenvolvimento)**
- SQLite possível, mas MySQL recomendado
- 1 worker Flask

**Produção (Docker)**
- 4 workers Gunicorn
- MySQL 8.0
- Nginx proxy reverso

**Escalado**
- Redis para cache
- Load balancer
- Múltiplas instâncias
- CDN para static files

---

## 🛠️ Para Desenvolvedores

### Adicionar Novo Endpoint

1. Em `app.py`, adicione:
```python
@app.route('/api/novo-endpoint', methods=['GET'])
@login_required  # Se precisar autenticação
def novo_endpoint():
    # Seu código aqui
    return jsonify({'resultado': 'sucesso'})
```

2. Teste com cURL:
```bash
curl http://localhost:5000/api/novo-endpoint
```

### Modificar Banco de Dados

1. Em `init_db()`, altere `CREATE TABLE`
2. Delete dados antigos: `docker-compose down -v`
3. Reinicie: `docker-compose up -d`

### Alterar Interface

1. Edite `templates/index.html` ou `login.html`
2. F5 no navegador (Ctrl+Shift+R força)
3. Veja resultado em tempo real

---

## 📦 Dependências Principais

| Pacote | Função |
|--------|--------|
| Flask | Framework web |
| Flask-MySQLdb | Conexão com MySQL |
| PyJWT | JWT tokens (opcional) |
| bcrypt | Hash de senhas |
| python-dotenv | Variáveis de ambiente |
| gunicorn | Servidor WSGI (produção) |

---

## 🌐 Variáveis de Ambiente

```env
DB_HOST=localhost       # Host do MySQL
DB_USER=root           # Usuário MySQL
DB_PASSWORD=           # Senha MySQL
DB_NAME=keyauth        # Nome da database

SECRET_KEY=abc123...   # Segredo para sessões
FLASK_ENV=production   # development ou production
DEBUG=False            # Desabilitar em produção
```

---

## 📞 Estrutura de Suporte

Para diferentes problemas:

1. **"Como começar?"** → QUICKSTART.md
2. **"Como usar a API?"** → API.md
3. **"Como fazer deploy?"** → DEPLOY.md
4. **"Como funciona tudo?"** → README.md + arquivos comentados
5. **"Qual arquivo está onde?"** → ESTRUTURA.md (este arquivo)

---

**Qualquer dúvida, comece pelo README.md!** 📚
