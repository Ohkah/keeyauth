# 📡 Documentação da API KeyAuth

Guia completo para integrar a API KeyAuth em suas aplicações.

## 🔗 Base URL

```
http://seu-servidor.com:5000
```

## 🔐 Autenticação

A maioria dos endpoints públicos não requer autenticação. Os endpoints privados (gerenciamento de chaves) usam sessão.

## 📝 Endpoints

### 1. Validar Chave

Valida se uma chave é válida e registra o uso.

**Endpoint:** `POST /api/validate`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "key": "key_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "device_id": "computador_123"
}
```

**Parâmetros:**
- `key` (string, obrigatório): A chave a ser validada
- `device_id` (string, opcional): ID do dispositivo para device lock

**Response (200 - Sucesso):**
```json
{
  "valid": true,
  "name": "My Script v1.0",
  "remaining_uses": 950
}
```

**Response (401 - Inválida/Expirada):**
```json
{
  "error": "Chave expirada"
}
```

**Possíveis Erros:**
- `"Chave inválida"` - Chave não existe
- `"Chave desativada"` - Administrador desativou
- `"Chave expirada"` - Data de expiração passou
- `"Chave bloqueada para este dispositivo"` - Device lock ativo
- `"Limite de usos atingido"` - Max uses foi alcançado

**Exemplo cURL:**
```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "key": "key_abcdef123456",
    "device_id": "meu_pc_123"
  }'
```

**Exemplo Python:**
```python
import requests

response = requests.post(
    "http://localhost:5000/api/validate",
    json={
        "key": "key_abcdef123456",
        "device_id": "meu_pc_123"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Chave válida: {data['name']}")
    print(f"Usos restantes: {data['remaining_uses']}")
else:
    error = response.json()
    print(f"Erro: {error['error']}")
```

### 2. Obter Informações da Chave

Obtém informações sobre uma chave **sem contar como um uso**.

**Endpoint:** `GET /api/key-info/{key_string}`

**Response (200):**
```json
{
  "name": "My Script v1.0",
  "expires_at": "2025-12-31T23:59:59",
  "max_uses": 1000,
  "uses": 50,
  "is_active": true,
  "remaining_uses": 950
}
```

**Response (404):**
```json
{
  "error": "Chave não encontrada"
}
```

**Parâmetros:**
- `expires_at`: Data de expiração (null = nunca expira)
- `max_uses`: Limite de usos (null = ilimitado)
- `uses`: Número de vezes já usada
- `is_active`: Se está ativa
- `remaining_uses`: Usos restantes (null = ilimitado)

**Exemplo cURL:**
```bash
curl http://localhost:5000/api/key-info/key_abcdef123456
```

### 3. Login

Faz login como administrador.

**Endpoint:** `POST /login`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

**Response (200 - Sucesso):**
```json
{
  "success": true
}
```

**Response (401 - Erro):**
```json
{
  "error": "Usuário ou senha inválidos"
}
```

### 4. Registrar

Cria uma nova conta de administrador (apenas na primeira vez).

**Endpoint:** `POST /register`

**Request Body:**
```json
{
  "username": "novo_usuario",
  "password": "senha_segura"
}
```

**Response (201 - Criado):**
```json
{
  "success": true
}
```

**Response (409 - Já existe):**
```json
{
  "error": "Usuário já existe"
}
```

### 5. Logout

Faz logout do administrador.

**Endpoint:** `GET /logout`

**Response:** Redireciona para `/login`

### 6. Listar Chaves (Admin)

Lista todas as chaves do administrador logado.

**Endpoint:** `GET /api/keys`

**Requer autenticação:** Sim

**Response (200):**
```json
[
  {
    "id": 1,
    "key_string": "key_abcdef123456",
    "name": "My Script v1.0",
    "expires_at": "2025-12-31T23:59:59",
    "device_lock": null,
    "max_uses": 1000,
    "uses": 50,
    "is_active": true,
    "created_at": "2024-01-01T10:00:00",
    "last_used": "2024-09-16T15:30:00"
  }
]
```

### 7. Criar Chave (Admin)

Cria uma nova chave.

**Endpoint:** `POST /api/keys`

**Requer autenticação:** Sim

**Request Body:**
```json
{
  "name": "My Script v1.0",
  "expires_in_days": 30,
  "max_uses": 1000,
  "device_lock": null
}
```

**Parâmetros:**
- `name` (string, obrigatório): Nome descritivo da chave
- `expires_in_days` (number, opcional): Dias até expirar (null = nunca)
- `max_uses` (number, opcional): Limite de usos (null = ilimitado)
- `device_lock` (string, opcional): ID do dispositivo (null = qualquer)

**Response (201 - Criada):**
```json
{
  "id": 1,
  "key_string": "key_abcdef123456",
  "name": "My Script v1.0",
  "expires_at": "2025-12-31T23:59:59",
  "device_lock": null,
  "max_uses": 1000,
  "uses": 0,
  "is_active": true,
  "created_at": "2024-01-01T10:00:00"
}
```

### 8. Deletar Chave (Admin)

Deleta uma chave.

**Endpoint:** `DELETE /api/keys/{id}`

**Requer autenticação:** Sim

**Response (200):**
```json
{
  "success": true
}
```

### 9. Ativar/Desativar Chave (Admin)

Alterna o status de uma chave.

**Endpoint:** `POST /api/keys/{id}/toggle`

**Requer autenticação:** Sim

**Response (200):**
```json
{
  "success": true,
  "is_active": false
}
```

## 🔄 Fluxo de Uso Típico

### 1. Usuário usa um script:

```
Cliente → POST /api/validate → Servidor
Servidor valida e registra o uso
Cliente ← JSON com sucesso/erro
```

### 2. Verificar antes de usar:

```
Cliente → GET /api/key-info/{key} → Servidor
Servidor retorna info sem contar uso
Cliente ← JSON com informações
```

### 3. Admin criar chave:

```
Admin → Login
Admin → POST /api/keys (com parametros)
Admin ← Chave criada
Admin → Compartilha chave com usuário
```

## 🌍 Exemplos Completos

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:5000';

// Validar chave
async function validateKey(key, deviceId) {
  try {
    const response = await axios.post(`${API_URL}/api/validate`, {
      key: key,
      device_id: deviceId
    });
    
    console.log('✓ Chave válida');
    console.log('Nome:', response.data.name);
    console.log('Usos restantes:', response.data.remaining_uses);
    return true;
  } catch (error) {
    console.log('✗ Erro:', error.response.data.error);
    return false;
  }
}

// Obter info sem usar
async function getKeyInfo(key) {
  try {
    const response = await axios.get(`${API_URL}/api/key-info/${key}`);
    console.log(response.data);
    return response.data;
  } catch (error) {
    console.log('Chave não encontrada');
    return null;
  }
}

validateKey('key_abc123', 'meu_pc');
```

### Python

```python
import requests

API_URL = 'http://localhost:5000'

def validate_key(key, device_id=None):
    response = requests.post(
        f'{API_URL}/api/validate',
        json={
            'key': key,
            'device_id': device_id
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Válida: {data['name']}")
        print(f"Restante: {data.get('remaining_uses', 'ilimitado')}")
        return True
    else:
        print(f"✗ Erro: {response.json()['error']}")
        return False

validate_key('key_abc123', 'meu_pc')
```

### Lua (Roblox)

```lua
local KeyAuth = require(game.ServerStorage.keyauth)
local auth = KeyAuth.new('http://localhost:5000', 'meu_device_id')

if auth:validate('key_abc123') then
    print('✓ Chave válida!')
else
    print('✗ Chave inválida!')
end
```

## 🛡️ Boas Práticas de Segurança

1. **Use HTTPS em produção** - Configure SSL/TLS
2. **Não expõe as chaves** - Guarde em variáveis de ambiente
3. **Valide a resposta** - Sempre verifique o status HTTP
4. **Implemente retry** - Para falhas de conexão
5. **Cache inteligente** - Use `/api/key-info` para cache local
6. **Logs de auditoria** - Monitore acessos suspeitos

## ⚙️ Limitações e Quotas

- **Rate limiting:** 100 requisições por minuto (por IP)
- **Timeout:** 30 segundos
- **Max payload:** 10KB

## 📊 Statuscode HTTP

| Código | Significado |
|--------|------------|
| 200 | Sucesso |
| 201 | Recurso criado |
| 400 | Requisição inválida |
| 401 | Não autorizado |
| 404 | Não encontrado |
| 409 | Conflito |
| 500 | Erro do servidor |

---

**Última atualização:** 2024
