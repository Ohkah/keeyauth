# ⚡ Quick Start - Comece em 5 Minutos

Guia rápido para começar a usar o KeyAuth.

## 🐳 Com Docker (Recomendado)

### Passo 1: Preparar

```bash
cd /caminho/para/keyauth
cp .env.example .env
```

### Passo 2: Iniciar

```bash
docker-compose up -d
```

### Passo 3: Acessar

Abra: **http://localhost:5000**

### Passo 4: Criar Conta

1. Clique em "Registrar"
2. Digite um usuário e senha
3. Clique em "Registrar"

### Passo 5: Criar Chave

1. Clique em "Nova Chave"
2. Preencha:
   - Nome: `Meu Script`
   - Expiração: (deixe vazio)
   - Limite de Usos: (deixe vazio)
   - Device Lock: (deixe vazio)
3. Clique em "Criar Chave"
4. **Copie a chave gerada** (você não verá novamente!)

### Passo 6: Usar em Lua

```lua
local KeyAuth = require("keyauth")

local auth = KeyAuth.new("http://localhost:5000", "meu_device_id")

if auth:validate("sua_chave_aqui") then
    print("✓ Autenticado!")
else
    print("✗ Chave inválida")
end
```

---

## 🖥️ Sem Docker (Local)

### Passo 1: Preparar

```bash
# Instalar Python e MySQL
sudo apt install python3 python3-pip mysql-server

# Clonar projeto
git clone seu-repositorio keyauth
cd keyauth

# Ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Edite .env com suas credenciais MySQL
```

### Passo 2: Preparar MySQL

```bash
sudo mysql -u root -p

CREATE DATABASE keyauth;
CREATE USER 'keyauth'@'localhost' IDENTIFIED BY 'sua_senha';
GRANT ALL ON keyauth.* TO 'keyauth'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Passo 3: Executar

```bash
python3 app.py
```

### Passo 4: Acessar

Abra: **http://localhost:5000**

---

## 🎯 Próximas Etapas

### Criar Diferentes Tipos de Chaves

**Chave com Expiração:**
- Nome: `Script Teste`
- Expiração: `7` dias
- Limite: deixe vazio

**Chave com Limite de Usos:**
- Nome: `Script Trial`
- Expiração: deixe vazio
- Limite: `10` usos

**Chave Bloqueada por Dispositivo:**
- Nome: `Script Principal`
- Device Lock: `computador_principal`
- Usuário deve passar o mesmo device_id

### Verificar Chaves

Vá para "Chaves" para:
- Ver todas as suas chaves
- Copiar chave
- Ver número de usos
- Ativar/Desativar
- Deletar

---

## 📚 Exemplos Práticos

### Roblox Script

```lua
-- Coloque em ServerStorage
local KeyAuth = require(game.ServerStorage.keyauth)

-- Gera device ID único
local device_id = KeyAuth.generate_device_id()

local auth = KeyAuth.new(
    "http://seu-servidor.com:5000",
    device_id
)

-- Valida na inicialização
if not auth:validate("key_sua_chave_aqui") then
    script:Destroy()  -- Encerra se inválida
    return
end

print("✓ Script autorizado")
-- Seu código aqui
```

### Script Lua Puro

```lua
#!/usr/bin/env lua

local KeyAuth = require("keyauth")
local auth = KeyAuth.new("http://localhost:5000", "meu_pc")

-- Valida
local valid, msg = auth:validate("key_sua_chave_aqui")

if valid then
    print("Acesso concedido!")
else
    print("Erro: " .. msg)
    os.exit(1)
end
```

### Verificar Info Sem Usar

```lua
-- Vê info sem contar como um uso
local info = auth:get_info("key_sua_chave_aqui")

if info then
    print("Status: ", info)
else
    print("Chave não encontrada")
end
```

---

## 🔑 Parar e Reiniciar

### Docker

```bash
# Parar
docker-compose down

# Reiniciar
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Python

```bash
# Ctrl+C para parar
# Depois:
python3 app.py
```

---

## ❌ Problemas Comuns

| Problema | Solução |
|----------|---------|
| "Porta 5000 em uso" | `sudo lsof -i :5000` e mate o processo |
| "Erro de conexão MySQL" | Verifique se MySQL está rodando e credenciais estão certas |
| "Página em branco" | Limpe cache do navegador (Ctrl+Shift+Delete) |
| "Chave não valida" | Copie a chave novamente, sem espaços extras |

---

## 🚀 Deploy em Produção

Quando pronto, veja [DEPLOY.md](DEPLOY.md) para instruções completas.

---

## 💡 Dicas

1. **Copie a chave imediatamente** - Você não a verá novamente
2. **Use device_id** - Aumente a segurança
3. **Backup chaves** - Anote as importantes
4. **Monitore uso** - Veja em "Chaves" → última utilização
5. **Teste antes** - Valide a chave localmente primeiro

---

**Pronto para começar!** 🎉

Qualquer dúvida, veja a documentação completa em [README.md](README.md) e [API.md](API.md).
