--[[
    Exemplo de uso da KeyAuth em um Script Roblox
    Cole este código em um LocalScript ou Script do Roblox
]]

-- Importa a biblioteca KeyAuth
local KeyAuth = require(game.ServerStorage.keyauth)  -- Ajuste o caminho conforme necessário

-- Configuração
local SERVER_URL = "http://seu-servidor.com:5000"  -- URL do seu servidor KeyAuth
local DEVICE_ID = KeyAuth.generate_device_id()     -- Gera ID único do dispositivo

-- Cria instância
local auth = KeyAuth.new(SERVER_URL, DEVICE_ID)

-- Função para validar a chave
local function validate_key()
    -- Aqui você pode obter a chave de diferentes formas:
    -- 1. De um arquivo local
    -- 2. De uma variável de ambiente
    -- 3. Pedida ao jogador
    -- 4. Armazenada em DataStore

    local key = "key_XXXXXXXXXXXXXXXX"  -- Substitua pela chave real

    print("Validando chave...")
    local is_valid, message = auth:validate(key)

    if is_valid then
        print("✓ Chave válida!")
        print(message)
        return true
    else
        print("✗ Chave inválida!")
        print("Motivo: " .. message)
        return false
    end
end

-- Função para obter informações sobre a chave
local function get_key_info()
    local key = "key_XXXXXXXXXXXXXXXX"

    local info, error = auth:get_info(key)

    if info then
        print("Informações da chave:")
        print(info)
    else
        print("Erro: " .. error)
    end
end

-- Executa a validação
if validate_key() then
    print("Seu script pode rodar normalmente!")
    -- Seu código aqui
else
    print("Acesso negado!")
    -- Encerrar o script ou mostrar mensagem de erro
    script:Destroy()  -- Destroi o script se usar em Roblox
end
