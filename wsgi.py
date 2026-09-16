from app import app, init_db

# Inicializa o banco de dados quando a aplicação inicia
try:
    init_db()
    print("✓ Banco de dados inicializado via wsgi.py")
except Exception as e:
    print(f"⚠️ Aviso ao inicializar banco: {e}")

if __name__ == '__main__':
    app.run()
