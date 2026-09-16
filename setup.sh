#!/bin/bash

echo "╔════════════════════════════════════════════════════╗"
echo "║     KeyAuth - Sistema de Autenticação de Chaves   ║"
echo "║                  Setup Script                      ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Verifica se Docker está instalado
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✓ Docker encontrado!"
    echo ""
    echo "Escolha uma opção:"
    echo "1) Rodar com Docker Compose (Recomendado)"
    echo "2) Setup Local (sem Docker)"
    read -p "Opção: " option

    if [ "$option" = "1" ]; then
        echo ""
        echo "🐳 Preparando Docker Compose..."

        # Copia .env.example se não existir
        if [ ! -f .env ]; then
            cp .env.example .env
            echo "✓ Arquivo .env criado"
            echo "  ⚠️  Edite .env com suas configurações de banco de dados"
        fi

        echo ""
        echo "Iniciando serviços..."
        docker-compose up -d

        echo ""
        echo "✓ Serviços iniciados!"
        echo ""
        echo "📍 Acesse: http://localhost:5000"
        echo ""
        echo "Próximos passos:"
        echo "1. Acesse http://localhost:5000"
        echo "2. Clique em 'Registrar' para criar sua conta de admin"
        echo "3. Faça login e comece a criar chaves!"
        echo ""
        echo "Para ver os logs:"
        echo "  docker-compose logs -f keyauth"
        echo ""
        echo "Para parar os serviços:"
        echo "  docker-compose down"
        exit 0
    fi
fi

# Setup Local
echo ""
echo "🛠️  Preparando Setup Local..."
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 não encontrado!"
    echo "Instale Python 3 em https://www.python.org/downloads/"
    exit 1
fi
echo "✓ Python 3 encontrado: $(python3 --version)"

# Verifica MySQL
if ! command -v mysql &> /dev/null; then
    echo ""
    echo "⚠️  MySQL não encontrado!"
    echo "Instale MySQL:"
    echo "  Ubuntu/Debian: sudo apt-get install mysql-server"
    echo "  macOS: brew install mysql-server"
    echo "  Windows: https://dev.mysql.com/downloads/"
    echo ""
    read -p "Deseja continuar sem MySQL? (n/s): " continue_mysql
    if [ "$continue_mysql" != "s" ]; then
        exit 1
    fi
else
    echo "✓ MySQL encontrado: $(mysql --version)"
fi

echo ""
echo "Instalando dependências Python..."
python3 -m pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependências instaladas"
else
    echo "✗ Erro ao instalar dependências"
    exit 1
fi

# Copia .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Arquivo .env criado"
    echo ""
    echo "⚠️  Edite .env com suas configurações:"
    echo "  DB_HOST=localhost"
    echo "  DB_USER=root"
    echo "  DB_PASSWORD=sua_senha"
    echo "  DB_NAME=keyauth"
fi

echo ""
echo "✓ Setup concluído!"
echo ""
echo "Para iniciar a aplicação:"
echo "  python3 app.py"
echo ""
echo "Depois acesse: http://localhost:5000"
