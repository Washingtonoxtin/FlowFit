from app import create_app, db
from app.models import Usuario, Cliente, Pagamento
from app.utils import criar_usuario_admin_inicial, inicializar_dados
import os

app = create_app()

if __name__ == '__main__':
    print("📦 Iniciando app.py via Docker CMD...")
    with app.app_context():
        db.create_all()
        criar_usuario_admin_inicial()
        # inicializar_dados()  # Descomente se quiser dados de exemplo

    print("🚀 Sistema da Academia iniciado!")
    print("📱 Acesse: http://localhost:5000")
    
    print("🚀 Flask prestes a iniciar...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(os.getenv('FLASK_DEBUG', '0') == '1')
    )
