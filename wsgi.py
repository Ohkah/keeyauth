# wsgi.py
from app import app, init_db

# Inicializa o banco de dados quando a aplicação inicia
try:
    init_db()
except Exception as e:
    print(f"⚠️ Aviso ao inicializar banco: {e}")

if __name__ == '__main__':
    app.run()