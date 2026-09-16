# 🔐 KeyAuth - Sistema de Autenticação de Chaves

Um sistema robusto e personalizável para gerenciar chaves de autenticação para scripts Lua, similar ao KeyAuth. Perfeito para proteger scripts Roblox, ferramentas e aplicações Lua com validação independente.

## ✨ Características

- ✅ **Geração de Chaves** - Crie chaves aleatórias e seguras
- ⏰ **Expiração Configurável** - Escolha se nunca expira ou defina um prazo
- 🔒 **Device Lock** - Restrinja uma chave a um dispositivo específico
- 📊 **Limite de Usos** - Defina quantas vezes uma chave pode ser usada
- 🎯 **API REST** - Validação de chaves via API HTTP
- 🖥️ **Painel de Controle** - Interface web para gerenciar tudo
- 🚀 **Validação Independente** - As validações funcionam sem seu computador ligado
- 📱 **Responsivo** - Funciona em desktop, tablet e mobile
- 🐳 **Docker** - Deploy fácil com Docker Compose

## 📋 Requisitos

### Para Desenvolvimento Local
- Python 3.8+
- MySQL 5.7+ ou MariaDB
- pip (gerenciador de pacotes Python)

### Para Produção (Recomendado)
- Docker
- Docker Compose

## 🚀 Instalação Rápida

### Opção 1: Docker Compose (Recomendado)

1. Clone ou extraia os arquivos
2. Copie `.env.example` para `.env` e configure:
   ```bash
   cp .env.example .env
   ```
3. Inicie os serviços:
   ```bash
   docker-compose up -d
   ```
4. Acesse em `http://localhost:5000`

### Opção 2: Instalação Local

1. **Instale o MySQL:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mysql-server
   
   # macOS
   brew install mysql-server
   
   # Windows: Download de https://dev.mysql.com/downloads/
   ```

2. **Crie o banco de dados:**
   ```bash
   mysql -u root -p
   CREATE DATABASE keyauth;
   EXIT;
   ```

3. **Instale as dependências Python:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   # Edite .env com suas configurações
   ```

5. **Rode a aplicação:**
   ```bash
   python app.py
   ```

6. **Acesse em `http://localhost:5000`**

## 📚 Como Usar

### 1. Primeiro Login

Ao acessar `http://localhost:5000` pela primeira vez:
- Clique em "Registrar"
- Crie uma conta de administrador
- Faça login

### 2. Criar Chaves

No painel, acesse "Nova Chave" e configure:

**Campos:**
- **Nome da Chave**: Identificação (ex: "My Script v1.0")
- **Expiração**: Dias até expirar (deixe em branco para nunca expirar)
- **Limite de Usos**: Quantas vezes pode ser usada (deixe em branco para ilimitado)
- **Device Lock**: ID do dispositivo (deixe em branco para qualquer dispositivo)

**Exemplos:**
```
Nome: "Script Principal"
Expiração: 30 (dias)
Limite de Usos: 1000
Device Lock: (deixe vazio)
```

```
Nome: "Teste Temporário"
Expiração: 1 (dia)
Limite de Usos: 10
Device Lock: computador_123
```

### 3. Usar em Scripts Lua

#### Para Scripts Roblox:

1. **Coloque `keyauth.lua` em ServerStorage** (ou ReplicatedStorage)

2. **Use em um Script:**
```lua
local KeyAuth = require(game.ServerStorage.keyauth)

local auth = KeyAuth.new("http://seu-servidor.com:5000", KeyAuth.generate_device_id())

if auth:validate("key_XXXXXXXXXXXXXXXX") then
    print("✓ Chave válida!")
    -- Seu código aqui
else
    print("✗ Chave inválida!")
    script:Destroy()
end
```

#### Para Scripts Lua Puro:

1. **Copie `keyauth.lua` para seu projeto**

2. **Use como:**
```lua
local KeyAuth = require("keyauth")

local auth = KeyAuth.new("http://seu-servidor.com:5000", "meu_device_id")

local is_valid, message = auth:validate("key_XXXXXXXXXXXXXXXX")

if is_valid then
    print("Chave válida!")
else
    print("Erro: " .. message)
end
```

#### Para Gerar Device ID Automático:

```lua
local device_id = KeyAuth.generate_device_id()
print("Device ID: " .. device_id)
```

## 🔌 API REST

### Validar Chave

**Endpoint:** `POST /api/validate`

**Request:**
```json
{
  "key": "key_XXXXXXXXXXXXXXXX",
  "device_id": "computador_123"  // Opcional
}
```

**Response (Sucesso):**
```json
{
  "valid": true,
  "name": "My Script",
  "remaining_uses": 950
}
```

**Response (Erro):**
```json
{
  "error": "Chave expirada"
}
```

### Obter Informações da Chave

**Endpoint:** `GET /api/key-info/{key_string}`

**Response:**
```json
{
  "name": "My Script",
  "expires_at": "2025-12-31T23:59:59",
  "max_uses": 1000,
  "uses": 50,
  "is_active": true,
  "remaining_uses": 950
}
```

## 🛠️ Gerenciar Chaves via Painel

### Ver Minhas Chaves
- Acesse a aba "Chaves"
- Veja todas as suas chaves com status, usos e data de última utilização

### Ativar/Desativar Chave
- Clique em "Desativar" ou "Ativar" na linha da chave

### Deletar Chave
- Clique em "Deletar" na linha da chave
- Confirme a exclusão

### Copiar Chave
- Clique em "Copiar" para copiar a chave para a área de transferência

## 📊 Dashboard

Veja estatísticas em tempo real:
- Total de chaves criadas
- Total de validações realizadas
- Quantidade de chaves ativas

## 🚀 Deploy em Produção

### Usando Docker:

1. **Configure um VPS/servidor**

2. **Instale Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

3. **Clone o projeto:**
   ```bash
   git clone seu-repositorio keyauth
   cd keyauth
   ```

4. **Crie o arquivo `.env`:**
   ```bash
   cp .env.example .env
   # Edite com suas configurações
   nano .env
   ```

5. **Inicie:**
   ```bash
   docker-compose up -d
   ```

6. **Configure um proxy reverso (Nginx):**

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

7. **Configure SSL com Let's Encrypt:**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot certonly --nginx -d seu-dominio.com
   ```

## 📝 Variáveis de Ambiente

Crie um arquivo `.env`:

```env
# MySQL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=keyauth

# Flask
SECRET_KEY=gere_uma_chave_aleatoria_muito_segura
FLASK_ENV=production
DEBUG=False
```

**Para gerar uma SECRET_KEY segura:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 🔒 Segurança

- ✅ Senhas com hash bcrypt
- ✅ Sessões protegidas
- ✅ Validação de entrada
- ✅ HTTPS recomendado em produção
- ✅ Logs de uso de chaves

## 🆘 Troubleshooting

### "Erro de conexão ao banco de dados"
- Verifique se MySQL está rodando
- Confirme as credenciais no `.env`
- Verifique se o banco `keyauth` existe

### "Erro 500 ao validar chave"
- Verifique os logs: `docker-compose logs keyauth`
- Confirme que a chave existe
- Verifique a URL do servidor

### "Não consigo conectar ao servidor"
- Verifique se `docker-compose` está rodando: `docker-compose ps`
- Reinicie se necessário: `docker-compose restart`
- Verifique a porta (padrão 5000)

## 📞 Suporte

Para problemas, verifique:
1. Os logs da aplicação
2. A configuração do `.env`
3. A conexão com o MySQL
4. As permissões de firewall

## 📄 Licença

Este projeto é fornecido como está, livre para uso pessoal e comercial.

## 🎯 Próximas Melhorias

- [ ] Autenticação de dois fatores (2FA)
- [ ] Integração com Discord
- [ ] Analytics avançado
- [ ] API com autenticação Bearer
- [ ] Backup automático de banco de dados
- [ ] Suporte multi-idioma

---

**Desenvolvido com ❤️ para proteger seus scripts**
