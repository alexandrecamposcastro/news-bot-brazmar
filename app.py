import os
import json
import csv
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time
import schedule

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# Configuração de porta para Railway
PORT = int(os.environ.get('PORT', 10000))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variáveis de ambiente carregadas")
except Exception as e:
    print(f"⚠️  Aviso dotenv: {e}")

# Importar database PostgreSQL
from database_pg import db

class BrazmarDashboard:
    def __init__(self):
        self.data_file = "database/news_database.json"
        self.ensure_database()
    
    def ensure_database(self):
        """Garante que os arquivos necessários existem"""
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
                    
            print("✅ Database inicializado")
        except Exception as e:
            print(f"❌ Erro inicializando database: {e}")
    
    def get_dashboard_data(self):
        """Obtém dados para o dashboard - Agora com PostgreSQL"""
        try:
            # Tenta pegar artigos do PostgreSQL primeiro
            artigos_recentes = db.get_recent_articles(50)
            
            if artigos_recentes:
                # Usa artigos do PostgreSQL
                hoje = datetime.now().strftime("%Y-%m-%d")
                artigos_hoje = [
                    artigo for artigo in artigos_recentes
                    if artigo.get('created_at', '').startswith(hoje)
                ]
                
                return {
                    "artigos_hoje": artigos_hoje,
                    "total_artigos": len(artigos_hoje),
                    "alta_prioridade": len([a for a in artigos_hoje if a.get('urgencia') == 'ALTA']),
                    "media_prioridade": len([a for a in artigos_hoje if a.get('urgencia') == 'MEDIA']),
                    "baixa_prioridade": len([a for a in artigos_hoje if a.get('urgencia') == 'BAIXA']),
                    "ultima_atualizacao": datetime.now().isoformat(),
                    "total_geral": len(artigos_recentes)
                }
            else:
                # Fallback para JSON local
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                hoje = datetime.now().strftime("%Y-%m-%d")
                artigos_hoje = [
                    artigo for artigo in data.get("articles", [])
                    if artigo.get("collection_date", "").startswith(hoje)
                ]
                
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
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Erro carregando database: {e}")
            return {
                "artigos_hoje": [], 
                "total_artigos": 0,
                "alta_prioridade": 0,
                "media_prioridade": 0,
                "baixa_prioridade": 0,
                "ultima_atualizacao": "Nunca",
                "total_geral": 0
            }

class BrazmarScheduler:
    def __init__(self):
        self.running = True
        
    def executar_coleta_imediata(self):
        """Executa coleta IMEDIATA ao iniciar"""
        print(f"\n🎯 EXECUTANDO COLETA IMEDIATA - {datetime.now()}")
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            artigos = processor.executar_coleta_completa()
            print(f"✅ Coleta imediata concluída: {len(artigos)} notícias")
            return artigos
        except Exception as e:
            print(f"❌ Erro na coleta imediata: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def agendar_tarefas(self):
        """Agenda todas as tarefas automáticas"""
        
        # 🎯 COLETA IMEDIATA ao iniciar
        self.executar_coleta_imediata()
        
        # 🕘 09:00 - Análise completa do dia
        schedule.every().day.at("09:00").do(self.tarefa_analise_completa)
        
        # 🕛 12:00 - Atualização do meio-dia
        schedule.every().day.at("12:00").do(self.tarefa_atualizacao_rapida)
        
        # 🕒 15:00 - Atualização da tarde
        schedule.every().day.at("15:00").do(self.tarefa_atualizacao_rapida)
        
        # 🕔 17:00 - Resumo executivo
        schedule.every().day.at("17:00").do(self.tarefa_resumo_executivo)
        
        print("⏰ AGENDADOR CONFIGURADO:")
        print("   🎯 COLETA IMEDIATA (ao iniciar)")
        print("   🕘 09:00 - Análise completa")
        print("   🕛 12:00 - Atualização rápida")
        print("   🕒 15:00 - Atualização rápida") 
        print("   🕔 17:00 - Resumo executivo")
    
    def tarefa_analise_completa(self):
        """Tarefa das 09:00 - Análise completa"""
        print(f"\n🎯 EXECUTANDO ANÁLISE COMPLETA - {datetime.now()}")
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            artigos = processor.executar_coleta_completa()
            print(f"✅ Análise completa: {len(artigos)} notícias")
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
    
    def tarefa_atualizacao_rapida(self):
        """Tarefas rápidas de atualização"""
        print(f"\n⚡ ATUALIZAÇÃO RÁPIDA - {datetime.now()}")
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            artigos = processor.executar_coleta_completa()
            print(f"✅ Atualização rápida: {len(artigos)} notícias")
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
    
    def tarefa_resumo_executivo(self):
        """Tarefa das 17:00 - Resumo do dia"""
        print(f"\n📊 RESUMO EXECUTIVO - {datetime.now()}")
        try:
            # Usa o dashboard para pegar estatísticas
            data = dashboard.get_dashboard_data()
            altas = data.get('alta_prioridade', 0)
            total = data.get('total_artigos', 0)
            print(f"📈 RESUMO: {total} notícias totais, {altas} de alta urgência")
        except Exception as e:
            print(f"❌ Erro no resumo: {e}")
    
    def iniciar(self):
        """Inicia o agendador em thread separada"""
        def rodar_agendador():
            self.agendar_tarefas()
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
        
        thread = threading.Thread(target=rodar_agendador, daemon=True)
        thread.start()
        print("🚀 Agendador iniciado em background")
    
    def parar(self):
        """Para o agendador"""
        self.running = False
        print("🛑 Agendador parado")

# Instâncias globais
dashboard = BrazmarDashboard()
scheduler = BrazmarScheduler()

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
    """Sistema de feedback com PostgreSQL"""
    try:
        data = request.json
        title = data.get('title', '')
        summary = data.get('summary', '')
        relevant = data.get('relevant', False)
        
        print(f"📝 Feedback: {title[:50]}... - Relevante: {relevant}")
        
        # Salva no PostgreSQL
        success = db.save_feedback(title, summary, relevant)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Feedback salvo no banco'})
        else:
            return jsonify({'status': 'error', 'message': 'Erro ao salvar feedback'}), 500
        
    except Exception as e:
        print(f"❌ Erro no feedback: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/estatisticas')
def api_estatisticas():
    """Estatísticas do sistema com PostgreSQL"""
    try:
        feedback_stats = db.get_feedback_stats()
        
        # Verifica se modelo ML existe
        model_exists = os.path.exists("relevance_model.pkl")
        
        return jsonify({
            "feedback": feedback_stats,
            "modelo_treinado": model_exists,
            "gemini_habilitado": bool(os.getenv("GEMINI_API_KEY")),
            "banco_dados": "✅ PostgreSQL",
            "plataforma": "Railway"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check para Railway"""
    try:
        # Testa conexão com PostgreSQL
        stats = db.get_feedback_stats()
        
        return jsonify({
            "status": "healthy", 
            "service": "Brazmar News Bot",
            "timestamp": datetime.now().isoformat(),
            "database": "✅ PostgreSQL conectado",
            "feedback_count": stats["total"]
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 500

# INICIALIZAÇÃO DO SISTEMA
print("=" * 60)
print("🚀 BRAZMAR NEWS BOT - INICIANDO NO RAILWAY")
print("=" * 60)
print(f"🔑 Gemini: {'✅ CONFIGURADO' if os.getenv('GEMINI_API_KEY') else '❌ NÃO CONFIGURADO'}")
print(f"🗄️  Database: PostgreSQL")
print(f"🌐 Porta: {PORT}")

# Inicia agendador IMEDIATAMENTE
try:
    scheduler.iniciar()
    print("✅ Agendador iniciado com COLETA IMEDIATA")
except Exception as e:
    print(f"❌ ERRO no agendador: {e}")
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    # Inicia servidor web
    app.run(host='0.0.0.0', port=PORT, debug=False)