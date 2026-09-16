from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import bcrypt
import MySQLdb
from functools import wraps
import secrets
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configuração do banco de dados usando MYSQL_URL
MYSQL_URL = os.getenv('MYSQL_URL')

if MYSQL_URL:
    parsed = urlparse(MYSQL_URL)
    DB_HOST = parsed.hostname or 'localhost'
    DB_PORT = parsed.port or 3306
    DB_NAME = parsed.path.lstrip('/') or 'railway'

    # A URL pode estar no formato: mysql://password@host ou mysql://user:password@host
    if ':' in (parsed.username or ''):
        # Formato: mysql://user:password@host
        DB_USER = parsed.username.split(':')[0]
        DB_PASSWORD = parsed.username.split(':')[1]
    elif parsed.username:
        # Formato: mysql://password@host (assume user=root)
        DB_USER = 'root'
        DB_PASSWORD = parsed.username
    else:
        DB_USER = 'root'
        DB_PASSWORD = parsed.password or ''
else:
    # Fallback
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'railway'
    DB_PORT = 3306

print(f"[DB Config] Conectando a {DB_HOST}:{DB_PORT}/{DB_NAME} como {DB_USER}")

def get_db():
    """Conecta ao banco de dados MySQL"""
    try:
        conn = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4',
            use_unicode=True,
            autocommit=False
        )
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        raise

def init_db():
    """Inicializa o banco de dados com as tabelas"""
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

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
        print("✓ Banco de dados inicializado")
        return True
    except Exception as e:
        print(f"✗ Erro ao inicializar: {e}")
        return False

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

# ============== ROTA DE INICIALIZAÇÃO ==============

@app.route('/api/init', methods=['GET'])
def initialize():
    """Inicializa o banco de dados"""
    if init_db():
        return jsonify({
            'success': True,
            'message': '✓ Banco de dados inicializado!',
            'user': 'admin',
            'pass': 'admin123'
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Erro ao inicializar'}), 500

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
            print(f"❌ Erro no login: {e}")
            return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    """Registra um novo administrador"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
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
    """Logout"""
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
    expires_in_days = data.get('expires_in_days')
    device_lock = data.get('device_lock')
    max_uses = data.get('max_uses')

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
    """Valida uma chave"""
    data = request.get_json()
    key_string = data.get('key')
    device_id = data.get('device_id')

    if not key_string:
        return jsonify({'error': 'Chave é obrigatória'}), 400

    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
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

        if not key['is_active']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave desativada'}), 401

        if key['expires_at'] and datetime.now() > key['expires_at']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave expirada'}), 401

        if key['device_lock'] and device_id and key['device_lock'] != device_id:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chave bloqueada para este dispositivo'}), 401

        if key['max_uses'] and key['uses'] >= key['max_uses']:
            cursor.close()
            db.close()
            return jsonify({'error': 'Limite de usos atingido'}), 401

        ip_address = request.remote_addr
        cursor.execute("""
            INSERT INTO key_usage (key_id, device_id, ip_address)
            VALUES (%s, %s, %s)
        """, (key['id'], device_id, ip_address))

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
    """Retorna informações sobre uma chave"""
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
    return jsonify({'error': 'Não encontrado'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ Aviso ao inicializar: {e}")

    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
