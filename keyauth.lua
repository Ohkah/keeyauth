--[[
    KeyAuth - Lua Authentication Library

    Exemplo de uso:

    local KeyAuth = require("keyauth")
    local auth = KeyAuth.new("http://localhost:5000", "meu_device_id")

    if auth:validate("minha_chave_aqui") then
        print("Chave válida! Você pode usar o script.")
    else
        print("Chave inválida ou expirada!")
    end
]]

local KeyAuth = {}
KeyAuth.__index = KeyAuth

-- Função para fazer requisições HTTP
local function http_request(url, method, data)
    -- Para Roblox (usando HttpService)
    if game and game:GetService("HttpService") then
        local HttpService = game:GetService("HttpService")

        local headers = {
            ["Content-Type"] = "application/json"
        }

        if method == "GET" then
            return HttpService:GetAsync(url, false, headers)
        else
            return HttpService:PostAsync(url, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false, headers)
        end
    end

    -- Para scripts Lua puros (usando curl ou similar)
    -- Você pode adaptar isso para sua necessidade
    if os and os.execute then
        local cmd
        if method == "GET" then
            cmd = string.format('curl -s "%s"', url)
        else
            local json_data = table.concat({"{"}, "")
            for k, v in pairs(data) do
                json_data = json_data .. string.format('"%s":"%s",', k, v)
            end
            json_data = json_data:sub(1, -2) .. "}"

            cmd = string.format('curl -s -X POST "%s" -H "Content-Type: application/json" -d \'%s\'', url, json_data)
        end

        local handle = io.popen(cmd)
        local result = handle:read("*a")
        handle:close()
        return result
    end

    error("HTTP request method not supported in this Lua environment")
end

-- Função para fazer parse de JSON simples
local function parse_json(json_str)
    -- Para uso simples com KeyAuth
    if json_str:find('"valid"%s*:%s*true') then
        return {valid = true}
    elseif json_str:find('"valid"%s*:%s*false') then
        return {valid = false}
    elseif json_str:find('"error"') then
        return {error = true}
    end
    return {error = true}
end

-- Cria uma nova instância de KeyAuth
function KeyAuth.new(server_url, device_id)
    local self = setmetatable({}, KeyAuth)
    self.server_url = server_url:gsub("/$", "")  -- Remove trailing slash
    self.device_id = device_id or ""
    self.cache = {}
    return self
end

-- Valida uma chave
function KeyAuth:validate(key)
    if not key or key == "" then
        return false, "Chave não fornecida"
    end

    local url = self.server_url .. "/api/validate"

    local data = {
        key = key,
        device_id = self.device_id
    }

    local response
    local success, error_msg = pcall(function()
        response = http_request(url, "POST", data)
    end)

    if not success then
        return false, "Erro de conexão: " .. error_msg
    end

    if response:find('"valid"%s*:%s*true') then
        return true, "Chave válida"
    elseif response:find('"error"') then
        -- Parse a mensagem de erro
        if response:find("expirada") then
            return false, "Chave expirada"
        elseif response:find("desativada") then
            return false, "Chave desativada"
        elseif response:find("dispositivo") then
            return false, "Chave bloqueada para este dispositivo"
        elseif response:find("usos") then
            return false, "Limite de usos atingido"
        else
            return false, "Chave inválida"
        end
    end

    return false, "Erro desconhecido"
end

-- Obtém informações sobre uma chave (sem usar)
function KeyAuth:get_info(key)
    if not key or key == "" then
        return nil, "Chave não fornecida"
    end

    -- Verifica cache (validade de 5 minutos)
    if self.cache[key] then
        local cached = self.cache[key]
        if os.time() - cached.time < 300 then
            return cached.data
        end
    end

    local url = self.server_url .. "/api/key-info/" .. key

    local response
    local success, error_msg = pcall(function()
        response = http_request(url, "GET", {})
    end)

    if not success then
        return nil, "Erro de conexão: " .. error_msg
    end

    if response:find('"is_active"') then
        -- Cache da resposta
        self.cache[key] = {
            data = response,
            time = os.time()
        }
        return response
    end

    return nil, "Erro ao obter informações"
end

-- Gera um ID de dispositivo baseado no hardware
function KeyAuth.generate_device_id()
    -- Para Roblox
    if game then
        return game:GetService("RunService"):IsStudio() and "roblox_studio" or "roblox_game"
    end

    -- Para sistemas Unix/Linux
    if os and os.execute then
        local handle = io.popen("cat /proc/cpuinfo | grep -i 'serial number' | head -1")
        if handle then
            local result = handle:read("*a")
            handle:close()
            if result and result ~= "" then
                return result:match("[%w]+") or "device_" .. tostring(math.random(1, 999999))
            end
        end
    end

    -- Fallback: gera um ID aleatório
    return "device_" .. tostring(math.random(1, 999999))
end

return KeyAuth
