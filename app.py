from flask import Flask
from routes.whatsapp_routes import whatsapp_bp
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo.env
load_dotenv()

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)
    
    # Registra o Blueprint para as rotas do WhatsApp
    app.register_blueprint(whatsapp_bp, url_prefix="/whatsapp")

    @app.route("/")
    def index():
        return "Servidor do Chatbot está no ar!"

    return app

if __name__ == "__main__":
    app = create_app()
    # O Gunicorn será usado em produção, mas para desenvolvimento local,
    # o app.run() é suficiente.
    app.run(host="0.0.0.0", port=5000, debug=True)