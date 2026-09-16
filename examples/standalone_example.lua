#!/usr/bin/env lua
--[[
    Exemplo de uso da KeyAuth em um Script Lua Puro (standalone)

    Requisitos:
    - Lua 5.1 ou superior
    - curl instalado (para requisições HTTP)
]]

-- Importa a biblioteca
local KeyAuth = require("keyauth")

-- Configuração
local SERVER_URL = "http://seu-servidor.com:5000"
local DEVICE_ID = KeyAuth.generate_device_id()

print("=== KeyAuth - Exemplo Standalone ===")
print("Device ID: " .. DEVICE_ID)
print("")

-- Cria instância
local auth = KeyAuth.new(SERVER_URL, DEVICE_ID)

-- Função principal
local function main()
    -- Lê a chave da entrada padrão
    io.write("Digite sua chave de autenticação: ")
    local key = io.read()

    if key == "" then
        print("Nenhuma chave fornecida!")
        return false
    end

    -- Valida a chave
    print("Validando...")
    local is_valid, message = auth:validate(key)

    print("")
    if is_valid then
        print("✓ SUCESSO!")
        print("Mensagem: " .. message)
        print("")
        return true
    else
        print("✗ FALHA!")
        print("Motivo: " .. message)
        print("")
        return false
    end
end

-- Função alternativa: Validar diretamente uma chave
local function validate_key_directly(key)
    print("Validando chave: " .. key)

    local is_valid, message = auth:validate(key)

    if is_valid then
        print("✓ Chave válida: " .. message)
        return true
    else
        print("✗ Chave inválida: " .. message)
        return false
    end
end

-- Função para testar a conexão
local function test_connection()
    print("Testando conexão com servidor...")
    print("Servidor: " .. SERVER_URL)

    local is_valid, message = auth:validate("test_key_invalid")

    -- Se recebemos uma resposta (mesmo que negativa), a conexão está OK
    if message and message ~= "" then
        print("✓ Conexão estabelecida!")
        return true
    else
        print("✗ Erro ao conectar")
        return false
    end
end

-- Executa o programa
if test_connection() then
    if main() then
        os.exit(0)  -- Sucesso
    else
        os.exit(1)  -- Falha
    end
else
    print("Não foi possível conectar ao servidor")
    os.exit(2)
end
