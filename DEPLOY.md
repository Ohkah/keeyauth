# 🚀 Guia de Deploy do KeyAuth

Instruções passo a passo para colocar KeyAuth em produção.

## 📋 Pré-requisitos

- VPS ou servidor com Linux
- Domínio (ou use IP)
- SSH acesso ao servidor
- Conhecimento básico de Linux

## 🏠 Opção 1: Deploy com Docker (Recomendado)

### 1.1 Configurar o Servidor

```bash
# Conectar ao servidor
ssh usuario@seu-servidor.com

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Adicionar usuário atual ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### 1.2 Clonar o Projeto

```bash
cd /home/usuario
git clone seu-repositorio keyauth
cd keyauth
```

### 1.3 Configurar Variáveis

```bash
cp .env.example .env
nano .env
```

**Edite com:**
```env
DB_HOST=mysql
DB_USER=keyauth
DB_PASSWORD=SenhaForte123!@#
DB_NAME=keyauth
SECRET_KEY=sua_chave_secreta_aleatoria_muito_segura
FLASK_ENV=production
DEBUG=False
```

**Gerar SECRET_KEY segura:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 1.4 Inicie o Docker Compose

```bash
docker-compose up -d

# Verifique os logs
docker-compose logs -f
```

### 1.5 Configurar Nginx

```bash
# Instalar Nginx
sudo apt install nginx -y

# Copiar configuração
sudo cp nginx.conf.example /etc/nginx/sites-available/keyauth
sudo nano /etc/nginx/sites-available/keyauth

# Edite "seu-dominio.com" para seu domínio real

# Ativar site
sudo ln -s /etc/nginx/sites-available/keyauth /etc/nginx/sites-enabled/keyauth

# Remover site padrão
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 1.6 Configurar SSL (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot certonly --nginx -d seu-dominio.com

# Nginx será recarregado automaticamente
```

### 1.7 Configurar Auto-Renovação

```bash
# Certbot renova automaticamente, mas para testar:
sudo certbot renew --dry-run
```

---

## 🖥️ Opção 2: Deploy Manual com Gunicorn

### 2.1 Preparar o Servidor

```bash
# Conectar
ssh usuario@seu-servidor.com

# Atualizar
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install python3 python3-pip python3-venv -y
sudo apt install mysql-server nginx -y

# Configurar MySQL
sudo mysql_secure_installation
```

### 2.2 Clonar Projeto

```bash
cd /home/usuario
git clone seu-repositorio keyauth
cd keyauth

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2.3 Configurar Banco de Dados

```bash
sudo mysql -u root -p

CREATE DATABASE keyauth;
CREATE USER 'keyauth'@'localhost' IDENTIFIED BY 'SenhaForte123!@#';
GRANT ALL PRIVILEGES ON keyauth.* TO 'keyauth'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2.4 Configurar .env

```bash
cp .env.example .env
nano .env
```

```env
DB_HOST=localhost
DB_USER=keyauth
DB_PASSWORD=SenhaForte123!@#
DB_NAME=keyauth
SECRET_KEY=sua_chave_segura
FLASK_ENV=production
DEBUG=False
```

### 2.5 Criar Serviço Systemd

```bash
sudo nano /etc/systemd/system/keyauth.service
```

Cole:
```ini
[Unit]
Description=KeyAuth Application
After=network.target

[Service]
User=usuario
WorkingDirectory=/home/usuario/keyauth
Environment="PATH=/home/usuario/keyauth/venv/bin"
ExecStart=/home/usuario/keyauth/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable keyauth
sudo systemctl start keyauth
sudo systemctl status keyauth
```

### 2.6 Configurar Nginx

```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/keyauth
sudo nano /etc/nginx/sites-available/keyauth

# Edite seu-dominio.com

sudo ln -s /etc/nginx/sites-available/keyauth /etc/nginx/sites-enabled/keyauth
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 2.7 SSL com Let's Encrypt

```bash
sudo certbot certonly --nginx -d seu-dominio.com
```

---

## 🔧 Configuração de Backup Automático

```bash
# Criar script de backup
nano /home/usuario/backup-keyauth.sh
```

Cole:
```bash
#!/bin/bash
BACKUP_DIR="/home/usuario/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="keyauth"
DB_USER="keyauth"
DB_PASSWORD="SenhaForte123!@#"

mkdir -p $BACKUP_DIR

# Backup do banco
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/keyauth_$TIMESTAMP.sql

# Comprimir
gzip $BACKUP_DIR/keyauth_$TIMESTAMP.sql

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "keyauth_*.sql.gz" -mtime +30 -delete

echo "Backup realizado: $BACKUP_DIR/keyauth_$TIMESTAMP.sql.gz"
```

Tornar executável:
```bash
chmod +x /home/usuario/backup-keyauth.sh
```

Agendar com cron:
```bash
crontab -e

# Adicione a linha:
0 2 * * * /home/usuario/backup-keyauth.sh
```

---

## 📊 Monitoramento

### Verificar Status

```bash
# Docker
docker-compose ps
docker-compose logs -f

# Systemd
systemctl status keyauth
journalctl -u keyauth -f

# Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/keyauth_access.log
```

### Verificar Espaço em Disco

```bash
df -h
du -sh /var/lib/mysql
du -sh /home/usuario/keyauth
```

### CPU e Memória

```bash
# Docker
docker stats

# Systemd
top
ps aux | grep gunicorn
```

---

## 🔐 Segurança

### Firewall

```bash
# Ativar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verificar
sudo ufw status
```

### Atualizações de Segurança

```bash
# Ativar atualizações automáticas
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### MySQL Seguro

```bash
# Executado durante instalação
sudo mysql_secure_installation

# Remover usuários padrão
sudo mysql -u root -p
DELETE FROM mysql.user WHERE user='';
FLUSH PRIVILEGES;
```

---

## 🐛 Troubleshooting

### Erro: "Connection refused"

```bash
# Verifique se a aplicação está rodando
docker-compose ps
# ou
systemctl status keyauth

# Reinicie
docker-compose restart
# ou
sudo systemctl restart keyauth
```

### Erro: "Database connection failed"

```bash
# Verifique MySQL
docker-compose logs mysql
# ou
sudo systemctl status mysql

# Teste conexão
mysql -u keyauth -p -h localhost keyauth
```

### Erro: "Certificado SSL inválido"

```bash
# Renovar certificado
sudo certbot renew --force-renewal

# Verificar data de expiração
sudo certbot certificates
```

### Erro: "Nginx proxy error"

```bash
# Verificar configuração Nginx
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/keyauth_error.log

# Reiniciar
sudo systemctl restart nginx
```

### Erro: "Permission denied"

```bash
# Verificar proprietário dos arquivos
ls -la /home/usuario/keyauth

# Corrigir permissões
sudo chown -R usuario:usuario /home/usuario/keyauth

# Para Docker
sudo usermod -aG docker $USER
newgrp docker
```

---

## 📈 Escalar para Produção

### Aumentar Workers Gunicorn

Em `keyauth.service`:
```ini
ExecStart=/home/usuario/keyauth/venv/bin/gunicorn --workers 8 --bind 127.0.0.1:5000 app:app
```

### Cache com Redis

```bash
# Instalar Redis
sudo apt install redis-server

# Usar em app.py
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

### Load Balancing

Use Nginx como load balancer apontando para múltiplas instâncias.

### CDN

Configure CloudFlare ou similar para cache de conteúdo estático.

---

## 📞 Suporte

Logs úteis:
```bash
# Docker Compose
docker-compose logs keyauth
docker-compose logs mysql

# Systemd
journalctl -u keyauth -n 100
journalctl -u mysql -n 100

# Nginx
tail -f /var/log/nginx/keyauth_access.log
tail -f /var/log/nginx/keyauth_error.log

# MySQL
sudo tail -f /var/log/mysql/error.log
```

---

**Seu KeyAuth está pronto para produção!** 🎉
