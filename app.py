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

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variáveis de ambiente carregadas")
except Exception as e:
    print(f"⚠️  Aviso dotenv: {e}")

class BrazmarDashboard:
    def __init__(self):
        self.data_file = "database/news_database.json"
        self.feedback_file = "feedback.csv"
        self.ensure_database()
    
    def ensure_database(self):
        """Garante que os arquivos de database existem"""
        try:
            os.makedirs("database", exist_ok=True)
            
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
            
            if not os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["title", "summary", "relevant"])
                    
            print("✅ Database inicializado")
        except Exception as e:
            print(f"❌ Erro inicializando database: {e}")
    
    def get_dashboard_data(self):
        """Obtém dados para o dashboard"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Erro carregando database: {e}")
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

# Instância global do dashboard
dashboard = BrazmarDashboard()

# ROTAS DA APLICAÇÃO
@app.route('/')
def index():
    """Dashboard principal"""
    try:
        data = dashboard.get_dashboard_data()
        return render_template('dashboard.html', **data)
    except Exception as e:
        return f"Erro carregando dashboard: {e}", 500

@app.route('/api/noticias')
def api_noticias():
    """API para notícias (JSON)"""
    try:
        data = dashboard.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/atualizar', methods=['POST'])
def api_atualizar():
    """Força atualização manual"""
    try:
        from news_processor import NewsProcessorCompleto
        processor = NewsProcessorCompleto()
        artigos = processor.executar_coleta_completa()
        
        return jsonify({
            "status": "success", 
            "message": f"Atualização concluída: {len(artigos)} notícias processadas",
            "artigos_processados": len(artigos)
        })
    except Exception as e:
        print(f"❌ Erro na atualização: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def receber_feedback():
    """Sistema de feedback"""
    try:
        data = request.json
        title = data.get('title', '')
        summary = data.get('summary', '')
        relevant = data.get('relevant', False)
        
        print(f"📝 Feedback: {title[:50]}... - Relevante: {relevant}")
        
        with open('feedback.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([title, summary, relevant])
        
        return jsonify({'status': 'success', 'message': 'Feedback salvo'})
        
    except Exception as e:
        print(f"❌ Erro no feedback: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/estatisticas')
def api_estatisticas():
    """Estatísticas do sistema"""
    try:
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
        
        model_exists = os.path.exists("relevance_model.pkl")
        
        return jsonify({
            "feedback": feedback_stats,
            "modelo_treinado": model_exists,
            "gemini_habilitado": bool(os.getenv("GEMINI_API_KEY"))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check para Render.com"""
    return jsonify({
        "status": "healthy", 
        "service": "Brazmar News Bot",
        "timestamp": datetime.now().isoformat()
    })

def iniciar_sistema():
    """Inicia todo o sistema"""
    print("=" * 50)
    print("🚀 BRAZMAR NEWS BOT - INICIANDO")
    print("=" * 50)
    print(f"🔑 Gemini: {'✅' if os.getenv('GEMINI_API_KEY') else '❌'}")
    print(f"🌐 Porta: {PORT}")
    
    # Inicia agendador
    try:
        from scheduler import scheduler
        scheduler.iniciar()
        print("✅ Agendador iniciado")
    except Exception as e:
        print(f"⚠️  Erro no agendador: {e}")

if __name__ == '__main__':
    iniciar_sistema()
    app.run(host='0.0.0.0', port=PORT, debug=False)