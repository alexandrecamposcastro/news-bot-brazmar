import os
import json
import csv
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# Configuração de porta para produção
PORT = int(os.environ.get('PORT', 5000))

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variáveis de ambiente carregadas")
except Exception as e:
    print(f"⚠️  Aviso: Não foi possível carregar .env: {e}")

class BrazmarDashboard:
    def __init__(self):
        self.data_file = "database/news_database.json"
        self.feedback_file = "feedback.csv"
        self.ensure_database()
    
    def ensure_database(self):
        """Garante que os arquivos de database existem"""
        os.makedirs("database", exist_ok=True)
        
        # Database de notícias
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "articles": [],
                    "last_updated": None,
                    "stats": {
                        "total_articles": 0,
                        "today_articles": 0
                    }
                }, f, indent=2, ensure_ascii=False)
        
        # Arquivo de feedback
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["title", "summary", "relevant"])
    
    def get_dashboard_data(self):
        """Obtém dados para o dashboard"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"articles": [], "stats": {}}
        
        # Artigos de hoje
        hoje = datetime.now().strftime("%Y-%m-%d")
        artigos_hoje = [
            artigo for artigo in data.get("articles", [])
            if artigo.get("collection_date", "").startswith(hoje)
        ]
        
        # Estatísticas
        stats = data.get("stats", {})
        
        return {
            "artigos_hoje": artigos_hoje,
            "total_artigos": len(artigos_hoje),
            "alta_prioridade": len([a for a in artigos_hoje if a.get('urgencia') == 'ALTA']),
            "media_prioridade": len([a for a in artigos_hoje if a.get('urgencia') == 'MEDIA']),
            "baixa_prioridade": len([a for a in artigos_hoje if a.get('urgencia') == 'BAIXA']),
            "ultima_atualizacao": stats.get('last_updated', 'Nunca'),
            "total_geral": stats.get('total_articles', 0)
        }

dashboard = BrazmarDashboard()

# ROTAS DA APLICAÇÃO
@app.route('/')
def index():
    """Dashboard principal"""
    data = dashboard.get_dashboard_data()
    return render_template('dashboard.html', **data)

@app.route('/api/noticias')
def api_noticias():
    """API para notícias (JSON)"""
    data = dashboard.get_dashboard_data()
    return jsonify(data)

@app.route('/api/atualizar', methods=['POST'])
def api_atualizar():
    """Força atualização manual"""
    try:
        # Import aqui para evitar dependência circular
        from news_processor import NewsProcessorCompleto
        processor = NewsProcessorCompleto()
        artigos = processor.executar_coleta_completa()
        
        return jsonify({
            "status": "success", 
            "message": f"Atualização concluída: {len(artigos)} notícias",
            "artigos_processados": len(artigos)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/feedback', methods=['POST'])
def receber_feedback():
    """Sistema de feedback - recebe 👍/👎"""
    try:
        data = request.json
        title = data.get('title', '')
        summary = data.get('summary', '')
        relevant = data.get('relevant', False)
        
        print(f"📝 Recebendo feedback: {title[:50]}... - Relevante: {relevant}")
        
        # SALVA NO FEEDBACK.CSV
        with open('feedback.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([title, summary, relevant])
        
        # Re-treina o modelo ML com novo feedback
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            processor.train_ml_model()
        except Exception as e:
            print(f"⚠️  Não foi possível retreinar modelo: {e}")
        
        return jsonify({'status': 'success', 'message': 'Feedback salvo'})
        
    except Exception as e:
        print(f"❌ Erro no feedback: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/estatisticas')
def api_estatisticas():
    """Estatísticas do sistema"""
    try:
        # Estatísticas de feedback
        feedback_stats = {"total": 0, "relevantes": 0, "irrelevantes": 0}
        if os.path.exists('feedback.csv'):
            with open('feedback.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    feedback_stats["total"] += 1
                    if row.get('relevant', '').lower() == 'true':
                        feedback_stats["relevantes"] += 1
                    else:
                        feedback_stats["irrelevantes"] += 1
        
        # Estatísticas do modelo
        model_exists = os.path.exists("relevance_model.pkl")
        
        return jsonify({
            "feedback": feedback_stats,
            "modelo_treinado": model_exists,
            "gemini_habilitado": os.getenv("GEMINI_API_KEY") is not None
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("🚀 Brazmar News Bot - PRODUÇÃO")
    print(f"🔑 Gemini: {'✅ Habilitado' if os.getenv('GEMINI_API_KEY') else '❌ Desabilitado'}")
    print(f"🌐 Servidor rodando na porta: {PORT}")
    
    # ✅ Configuração correta para produção
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    
    
    # Inicia agendador se disponível
    try:
        from scheduler import scheduler
        scheduler.iniciar()
        print("✅ Agendador iniciado")
    except Exception as e:
        print(f"⚠️  Agendador não disponível: {e}")