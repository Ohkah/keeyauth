from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import jwt
import bcrypt
import MySQLdb
from functools import wraps
import secrets
import json
from hashlib import sha256

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configuração do banco de dados
# Railway fornece essas variáveis automaticamente quando você adiciona MySQL
# Mas também tentamos as variáveis customizadas para compatibilidade
DB_HOST = os.getenv('MYSQL_HOST') or os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('MYSQL_USER') or os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('MYSQL_DATABASE') or os.getenv('DB_NAME', 'keyauth')
DB_PORT = int(os.getenv('MYSQL_PORT', 3306))

def get_db():
    """Conecta ao banco de dados MySQL"""
    try:
        # Tenta conectar usando TCP/IP (melhor para Railway)
        return MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4',
            use_unicode=True,
            autocommit=False
        )
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        raise

def init_db():
    """Inicializa o banco de dados com as tabelas"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Tabela de administradores
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabela de chaves
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INT AUTO_INCREMENT PRIMARY KEY,
            key_string VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            expires_at DATETIME DEFAULT NULL,
            device_lock VARCHAR(255) DEFAULT NULL,
            max_uses INT DEFAULT NULL,
            uses INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME DEFAULT NULL,
            admin_id INT,
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
        """)

        # Tabela de uso das chaves
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS key_usage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            key_id INT NOT NULL,
            device_id VARCHAR(255),
            ip_address VARCHAR(45),
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (key_id) REFERENCES keys(id)
        )
        """)

        db.commit()
        cursor.close()
        db.close()
        print("✓ Banco de dados inicializado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao inicializar banco: {e}")
        raise

def generate_key():
    """Gera uma chave aleatória formatada"""
    return f"key_{secrets.token_hex(16).upper()}"

def hash_password(password):
    """Hash a senha com bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hash):
    """Verifica se a senha corresponde ao hash"""
    return bcrypt.checkpw(password.encode(), hash.encode())

def login_required(f):
    """Decorator para proteger rotas que precisam de login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============== ROTAS DE AUTENTICAÇÃO ==============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login do administrador"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400

        try:
            db = get_db()
            cursor = db.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
            admin = cursor.fetchone()
            cursor.close()
            db.close()

            if admin and verify_password(password, admin['password_hash']):
                session['user_id'] = admin['id']
                session['username'] = admin['username']
                return jsonify({'success': True}), 200
            else:
                return jsonify({'error': 'Usuário ou senha inválidos'}), 401
        except Exception as e:
            return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    """Registra um novo administrador (apenas primeira vez)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        # Verifica se existe algum admin
        cursor.execute("SELECT COUNT(*) as count FROM admins")
        exists = cursor.fetchone()[0] > 0

        if exists and 'user_id' not in session:
            cursor.close()
            db.close()
            return jsonify({'error': 'Registro não permitido'}), 403

        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        db.commit()
        admin_id = cursor.lastrowid
        cursor.close()
        db.close()

        session['user_id'] = admin_id
        session['username'] = username

        return jsonify({'success': True}), 201
    except MySQLdb.IntegrityError:
        return jsonify({'error': 'Usuário já existe'}), 409
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

@app.route('/logout')
def logout():
    """Logout do administrador"""
    session.clear()
    return redirect(url_for('login'))

# ============== ROTAS DO PAINEL ==============

@app.route('/')
@login_required
def dashboard():
    """Painel de controle principal"""
    return render_template('index.html')

# ============== API DE CHAVES ==============

@app.route('/api/keys', methods=['GET'])
@login_required
def get_keys():
    """Lista todas as chaves do administrador"""
    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("""
            SELECT id, key_string, name, expires_at, device_lock, max_uses, uses,
                   is_active, created_at, last_used
            FROM keys
            WHERE admin_id = %s
            ORDER BY created_at DESC
        """, (session['user_id'],))

        keys = cursor.fetchall()
        cursor.close()
        db.close()

        # Converte datas para strings
        for key in keys:
            key['expires_at'] = key['expires_at'].isoformat() if key['expires_at'] else None
            key['created_at'] = key['created_at'].isoformat() if key['created_at'] else None
            key['last_used'] = key['last_used'].isoformat() if key['last_used'] else None

        return jsonify(keys)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar chaves: {str(e)}'}), 500

@app.route('/api/keys', methods=['POST'])
@login_required
def create_key():
    """Cria uma nova chave"""
    data = request.get_json()

    name = data.get('name')
    expires_in_days = data.get('expires_in_days')  # None = nunca expira
    device_lock = data.get('device_lock')  # None = qualquer dispositivo
    max_uses = data.get('max_uses')  # None = ilimitado

    if not name:
        return jsonify({'error': 'Nome da chave é obrigatório'}), 400

    key_string = generate_key()
    expires_at = None

    if expires_in_days and expires_in_days > 0:
        expires_at = datetime.now() + timedelta(days=expires_in_days)

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO keys (key_string, name, expires_at, device_lock, max_uses, admin_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (key_string, name, expires_at, device_lock, max_uses, session['user_id']))

        db.commit()
        key_id = cursor.lastrowid
        cursor.close()
        db.close()

        return jsonify({
            'id': key_id,
            'key_string': key_string,
            'name': name,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'device_lock': device_lock,
            'max_uses': max_uses,
            'uses': 0,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': f'Erro ao criar chave: {str(e)}'}), 500

@app.route('/api/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_key(key_id):
    """Deleta uma chave"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Verifica se a chave pertence ao admin
        cursor.execute("SELECT admin_id FROM keys WHERE id = %s", (key_id,))
        result = cursor.fetchone()

        if not result or result[0] != session['user_id']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave não encontrada'}), 404

        cursor.execute("DELETE FROM key_usage WHERE key_id = %s", (key_id,))
        cursor.execute("DELETE FROM keys WHERE id = %s", (key_id,))
        db.commit()
        cursor.close()
        db.close()

        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao deletar chave: {str(e)}'}), 500

@app.route('/api/keys/<int:key_id>/toggle', methods=['POST'])
@login_required
def toggle_key(key_id):
    """Ativa/desativa uma chave"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Verifica se a chave pertence ao admin
        cursor.execute("SELECT admin_id, is_active FROM keys WHERE id = %s", (key_id,))
        result = cursor.fetchone()

        if not result or result[0] != session['user_id']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave não encontrada'}), 404

        new_status = not result[1]
        cursor.execute("UPDATE keys SET is_active = %s WHERE id = %s", (new_status, key_id))
        db.commit()
        cursor.close()
        db.close()

        return jsonify({'success': True, 'is_active': new_status}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao atualizar chave: {str(e)}'}), 500

# ============== API DE VALIDAÇÃO (PÚBLICA) ==============

@app.route('/api/validate', methods=['POST'])
def validate_key():
    """Valida uma chave (pode ser acessado de qualquer lugar)"""
    data = request.get_json()
    key_string = data.get('key')
    device_id = data.get('device_id')  # Opcional, para device lock

    if not key_string:
        return jsonify({'error': 'Chave é obrigatória'}), 400

    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)

        # Busca a chave
        cursor.execute("""
            SELECT id, name, expires_at, device_lock, max_uses, uses, is_active
            FROM keys
            WHERE key_string = %s
        """, (key_string,))

        key = cursor.fetchone()

        if not key:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave inválida'}), 401

        # Verifica se está ativa
        if not key['is_active']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave desativada'}), 401

        # Verifica expiração
        if key['expires_at'] and datetime.now() > key['expires_at']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave expirada'}), 401

        # Verifica device lock
        if key['device_lock'] and device_id:
            if key['device_lock'] != device_id:
                cursor.close()
                db.close()
                return jsonify({'error': 'Chave bloqueada para este dispositivo'}), 401

        # Verifica limite de usos
        if key['max_uses'] and key['uses'] >= key['max_uses']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Limite de usos atingido'}), 401

        # Registra o uso
        ip_address = request.remote_addr
        cursor.execute("""
            INSERT INTO key_usage (key_id, device_id, ip_address)
            VALUES (%s, %s, %s)
        """, (key['id'], device_id, ip_address))

        # Atualiza o contador de usos
        new_uses = key['uses'] + 1
        cursor.execute("""
            UPDATE keys SET uses = %s, last_used = NOW() WHERE id = %s
        """, (new_uses, key['id']))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            'valid': True,
            'name': key['name'],
            'remaining_uses': key['max_uses'] - new_uses if key['max_uses'] else None
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao validar chave: {str(e)}'}), 500

@app.route('/api/key-info/<key_string>', methods=['GET'])
def get_key_info(key_string):
    """Retorna informações sobre uma chave sem usar (verificação pública)"""
    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("""
            SELECT name, expires_at, max_uses, uses, is_active
            FROM keys
            WHERE key_string = %s
        """, (key_string,))

        key = cursor.fetchone()
        cursor.close()
        db.close()

        if not key:
            return jsonify({'error': 'Chave não encontrada'}), 404

        return jsonify({
            'name': key['name'],
            'expires_at': key['expires_at'].isoformat() if key['expires_at'] else None,
            'max_uses': key['max_uses'],
            'uses': key['uses'],
            'is_active': key['is_active'],
            'remaining_uses': key['max_uses'] - key['uses'] if key['max_uses'] else None
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar informações: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """Trata erro 404"""
    return jsonify({'error': 'Não encontrado'}), 404

@app.errorhandler(500)
def server_error(error):
    """Trata erro 500"""
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    # Inicializa o banco de dados
    try:
        init_db()
    except Exception as e:
        print(f"Aviso: Não foi possível inicializar o banco: {e}")

    # Inicia a aplicação
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
