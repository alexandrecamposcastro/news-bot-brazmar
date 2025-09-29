from app import app
from scheduler import scheduler
import threading
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def iniciar_sistema():
    """Inicia todo o sistema Brazmar"""
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA BRAZMAR NEWS BOT")
    print("=" * 60)
    
    # Verifica configuração
    if os.getenv("GEMINI_API_KEY"):
        print("✅ Gemini API configurada")
    else:
        print("⚠️ Gemini API não configurada - usando apenas ML")
    
    # Cria diretórios necessários
    os.makedirs("database", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    # Inicia agendador em background
    scheduler.iniciar()
    print("✅ Agendador iniciado")
    
    # Inicia servidor web
    print("🌐 Servidor web iniciado: http://localhost:5000")
    print("📊 Dashboard disponível para a equipe")
    print("⏰ Agendamentos ativos: 09:00, 12:00, 15:00, 17:00")
    print("💡 Pressione Ctrl+C para parar")
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    iniciar_sistema()