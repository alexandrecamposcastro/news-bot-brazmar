import os
import json
import csv
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import threading
import time
import schedule

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# Configuração de porta para Render
PORT = int(os.environ.get('PORT', 5000))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variáveis de ambiente carregadas")
except Exception as e:
    print(f"⚠️  Aviso dotenv: {e}")

# Importar database HYBRID e novos providers
from database_hybrid import db
from github_manager import github_manager
from history_manager import history_manager
from gemini_provider import gemini_provider  # ✅ NOVO - substitui ai_provider
from circular_expert import circular_expert  # ✅ NOVO - especialista em circulares

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
        """Obtém dados para o dashboard - Agora com banco híbrido"""
        try:
            # Tenta pegar artigos do banco primeiro
            artigos_recentes = db.get_recent_articles(50)
            
            if artigos_recentes:
                # Usa artigos do banco
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
        """Executa coleta OTIMIZADA ao iniciar"""
        print(f"\n🎯 EXECUTANDO COLETA OTIMIZADA - {datetime.now()}")
        try:
            from news_processor import news_processor  # ✅ Usa instância global otimizada
            artigos = news_processor.executar_coleta_completa()
            print(f"✅ Coleta otimizada concluída: {len(artigos)} notícias relevantes")
            return artigos
        except Exception as e:
            print(f"❌ Erro na coleta otimizada: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def agendar_tarefas(self):
        """Agenda todas as tarefas automáticas"""
        
        # 🎯 COLETA IMEDIATA ao iniciar (OTIMIZADA)
        self.executar_coleta_imediata()
        
        # 🕘 09:00 - Análise completa do dia
        schedule.every().day.at("09:00").do(self.tarefa_analise_completa)
        
        # 🕛 12:00 - Atualização do meio-dia
        schedule.every().day.at("12:00").do(self.tarefa_atualizacao_rapida)
        
        # 🕒 15:00 - Atualização da tarde
        schedule.every().day.at("15:00").do(self.tarefa_atualizacao_rapida)
        
        # 🕔 17:00 - Resumo executivo
        schedule.every().day.at("17:00").do(self.tarefa_resumo_executivo)
        
        print("⏰ AGENDADOR CONFIGURADO (OTIMIZADO):")
        print("   🎯 COLETA IMEDIATA (ao iniciar) - OTIMIZADA")
        print("   🕘 09:00 - Análise completa")
        print("   🕛 12:00 - Atualização rápida")
        print("   🕒 15:00 - Atualização rápida") 
        print("   🕔 17:00 - Resumo executivo")
    
    def tarefa_analise_completa(self):
        """Tarefa das 09:00 - Análise completa OTIMIZADA"""
        print(f"\n🎯 EXECUTANDO ANÁLISE COMPLETA OTIMIZADA - {datetime.now()}")
        try:
            from news_processor import news_processor  # ✅ OTIMIZADO
            artigos = news_processor.executar_coleta_completa()
            print(f"✅ Análise completa OTIMIZADA: {len(artigos)} notícias")
        except Exception as e:
            print(f"❌ Erro na análise OTIMIZADA: {e}")
    
    def tarefa_atualizacao_rapida(self):
        """Tarefas rápidas de atualização OTIMIZADA"""
        print(f"\n⚡ ATUALIZAÇÃO RÁPIDA OTIMIZADA - {datetime.now()}")
        try:
            from news_processor import news_processor  # ✅ OTIMIZADO
            artigos = news_processor.executar_coleta_completa()
            print(f"✅ Atualização rápida OTIMIZADA: {len(artigos)} notícias")
        except Exception as e:
            print(f"❌ Erro na atualização OTIMIZADA: {e}")
    
    def tarefa_resumo_executivo(self):
        """Tarefa das 17:00 - Resumo do dia"""
        print(f"\n📊 RESUMO EXECUTIVO - {datetime.now()}")
        try:
            # Usa o dashboard para pegar estatísticas
            data = dashboard.get_dashboard_data()
            altas = data.get('alta_prioridade', 0)
            total = data.get('total_artigos', 0)
            print(f"📈 RESUMO: {total} notícias totais, {altas} de alta urgência")
            
            # ✅ NOVO: Gera circular final do dia
            if total > 0:
                from news_processor import news_processor
                artigos_recentes = db.get_recent_articles(20)
                circular = circular_expert.generate_circular(artigos_recentes)
                print("📨 CIRCULAR FINAL DO DIA GERADA!")
                
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
        print("🚀 Agendador OTIMIZADO iniciado em background")
    
    def parar(self):
        """Para o agendador"""
        self.running = False
        print("🛑 Agendador parado")

# Instâncias globais
dashboard = BrazmarDashboard()
scheduler = BrazmarScheduler()

def criar_csv_se_nao_existir():
    """Cria o CSV se não existir"""
    if not os.path.exists('feedback.csv'):
        with open('feedback.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['title', 'summary', 'relevant', 'timestamp'])
        print("✅ CSV criado")

def treinar_ml_com_csv():
    """Treina ML usando o CSV"""
    try:
        if not os.path.exists('feedback.csv'):
            print("❌ CSV não encontrado para treinamento")
            return False
            
        # Conta linhas no CSV
        with open('feedback.csv', 'r', encoding='utf-8') as f:
            linhas = sum(1 for line in f)
        
        print(f"📊 Feedbacks no CSV: {linhas - 1}")
        
        if linhas >= 6:  # 1 header + 5 feedbacks
            print("🎯 Treinando ML com CSV...")
            from news_processor import news_processor
            success = news_processor.train_ml_model()
            if success:
                print("✅✅✅ ML treinado com sucesso!")
                return True
            else:
                print("⚠️ ML não foi treinado (erro ou dados insuficientes)")
                return False
        else:
            print(f"⚠️ Feedbacks insuficientes: {linhas - 1}/5")
            return False
            
    except Exception as e:
        print(f"❌ Erro treinamento ML: {e}")
        return False

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
    """Força atualização manual OTIMIZADA"""
    try:
        from news_processor import news_processor  # ✅ OTIMIZADO
        artigos = news_processor.executar_coleta_completa()
        
        return jsonify({
            "status": "success", 
            "message": f"Atualização OTIMIZADA concluída: {len(artigos)} notícias relevantes",
            "artigos_processados": len(artigos)
        })
    except Exception as e:
        print(f"❌ Erro na atualização OTIMIZADA: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ NOVA ROTA: GERAR CIRCULAR EM TEMPO REAL
@app.route('/api/circular', methods=['POST'])
def api_gerar_circular():
    """Gera circular profissional em tempo real"""
    try:
        from news_processor import news_processor
        
        # Busca notícias recentes
        artigos_recentes = db.get_recent_articles(20)
        
        if not artigos_recentes:
            return jsonify({
                "status": "success",
                "circular": "📭 SEM NOTÍCIAS RELEVANTES - Nada a reportar para o Norte/Nordeste",
                "artigos_base": 0
            })
        
        # Gera circular profissional
        circular = circular_expert.generate_circular(artigos_recentes)
        
        return jsonify({
            "status": "success",
            "circular": circular,
            "artigos_base": len(artigos_recentes),
            "gerado_em": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def receber_feedback():
    """Sistema de feedback -> GitHub -> CSV -> ML"""
    try:
        # Verifica se tem dados JSON
        if not request.json:
            return jsonify({'status': 'error', 'message': 'Dados JSON não fornecidos'}), 400
        
        data = request.json
        title = data.get('title', '')
        summary = data.get('summary', '')
        relevant = data.get('relevant', False)
        
        print(f"📝 Recebendo feedback: {title[:50]}... - Relevante: {relevant}")
        
        # Validação básica
        if not title:
            return jsonify({'status': 'error', 'message': 'Título é obrigatório'}), 400
        
        # Garante que CSV existe
        criar_csv_se_nao_existir()
        
        # ✅ SALVA NO CSV
        with open('feedback.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([title, summary, relevant, datetime.now()])
        
        print("✅ Feedback salvo no CSV")
        
        # ✅ TREINA ML COM O CSV
        treinar_ml_com_csv()
        
        return jsonify({
            'status': 'success', 
            'message': 'Feedback salvo e ML atualizado!'
        })
        
    except Exception as e:
        print(f"❌ Erro no feedback: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/treinar-ml', methods=['POST'])
def treinar_ml():
    """Força treinamento do ML"""
    try:
        # Baixa CSV mais recente do GitHub
        if os.getenv("GITHUB_TOKEN"):
            github_manager.download_csv_for_ml()
        success = treinar_ml_com_csv()
        
        if success:
            return jsonify({'status': 'success', 'message': 'ML treinado com sucesso!'})
        else:
            return jsonify({'status': 'error', 'message': 'Erro ao treinar ML'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/estatisticas')
def api_estatisticas():
    """Estatísticas do sistema OTIMIZADO"""
    try:
        feedback_stats = db.get_feedback_stats()
        
        # Verifica se tem CSV de feedback
        csv_count = 0
        if os.path.exists('feedback.csv'):
            with open('feedback.csv', 'r', encoding='utf-8') as f:
                csv_count = sum(1 for line in f) - 1  # Exclui header
        
        # Verifica se modelo ML existe
        model_exists = os.path.exists("relevance_model.pkl")
        
        # Estatísticas do histórico
        history_stats = history_manager.get_stats()
        
        return jsonify({
            "feedback": feedback_stats,
            "feedback_csv": csv_count,
            "modelo_treinado": model_exists,
            "historico": history_stats,
            "gemini_habilitado": bool(os.getenv("GEMINI_API_KEY")),
            "github_configurado": bool(os.getenv("GITHUB_TOKEN")),
            "banco_dados": "✅ PostgreSQL" if db.use_postgres else "✅ SQLite",
            "plataforma": "Render",
            "provedor_ia": "✅ Gemini Flash 2.0",
            "regiao_foco": "🎯 NORTE/NORDESTE BRASIL"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-csv')
def download_csv():
    """Baixa o CSV de feedbacks"""
    try:
        # Baixa CSV mais recente do GitHub primeiro
        if os.getenv("GITHUB_TOKEN"):
            github_manager.download_csv_for_ml()
        return send_file('feedback.csv', as_attachment=True, as_text=False)
    except Exception as e:
        return f"Erro ao baixar CSV: {e}", 404

@app.route('/health')
def health_check():
    """Health check para Render"""
    try:
        # Testa conexão com banco
        stats = db.get_feedback_stats()
        history_stats = history_manager.get_stats()
        
        return jsonify({
            "status": "healthy", 
            "service": "Brazmar News Bot OTIMIZADO",
            "timestamp": datetime.now().isoformat(),
            "database": "✅ Conectado",
            "tipo_banco": "PostgreSQL" if db.use_postgres else "SQLite",
            "github": "✅ Configurado" if os.getenv("GITHUB_TOKEN") else "❌ Não configurado",
            "historico": f"✅ {history_stats['total_news']} notícias",
            "feedback_count": stats["total"],
            "provedor_ia": "✅ Gemini Flash 2.0",
            "regiao_foco": "🎯 NORTE/NORDESTE BRASIL"
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 500

# 🆕 ROTAS DO HISTÓRICO
@app.route('/historico')
def historico():
    """Página do histórico de notícias"""
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BRAZMAR - Histórico de Notícias</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: #f5f5f5; 
                color: #333; 
                line-height: 1.6;
            }
            .header { 
                background: #2c3e50; 
                color: white; 
                padding: 2rem 1rem; 
                text-align: center; 
                margin-bottom: 2rem;
            }
            .header h1 { 
                margin-bottom: 0.5rem; 
                font-size: 2.5rem;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 0 1rem; 
            }
            .controls { 
                background: white; 
                padding: 1.5rem; 
                border-radius: 10px; 
                margin: 2rem 0; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .btn { 
                background: #3498db; 
                color: white; 
                border: none; 
                padding: 0.8rem 1.5rem; 
                border-radius: 6px; 
                cursor: pointer; 
                margin: 0 0.5rem; 
                font-size: 1rem;
                transition: background 0.2s;
                text-decoration: none;
                display: inline-block;
            }
            .btn:hover { background: #2980b9; }
            .btn-success { background: #27ae60; }
            .btn-success:hover { background: #219653; }
            .btn-purple { background: #9b59b6; }
            .btn-purple:hover { background: #8e44ad; }
            .search-box { 
                padding: 0.8rem; 
                border: 1px solid #ddd; 
                border-radius: 6px; 
                width: 300px; 
                font-size: 1rem;
                margin-right: 1rem;
            }
            .stats-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 1.5rem; 
                margin: 2rem 0; 
            }
            .stat-card { 
                background: white; 
                padding: 1.5rem; 
                border-radius: 10px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                text-align: center; 
            }
            .stat-number { 
                font-size: 2.5rem; 
                font-weight: bold; 
                margin: 0.5rem 0; 
                color: #2c3e50;
            }
            .news-list { 
                background: white; 
                border-radius: 10px; 
                padding: 2rem; 
                margin: 2rem 0; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .news-item { 
                padding: 1.5rem; 
                border-bottom: 1px solid #eee; 
                margin-bottom: 1rem; 
                border-radius: 8px;
                transition: background 0.2s;
            }
            .news-item:hover {
                background: #f8f9fa;
            }
            .news-item:last-child { border-bottom: none; }
            .news-title { 
                font-weight: bold; 
                margin-bottom: 0.8rem; 
                color: #2c3e50; 
                font-size: 1.2rem;
            }
            .news-meta { 
                font-size: 0.9rem; 
                color: #666; 
                margin-bottom: 0.8rem; 
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
            }
            .priority-badge { 
                display: inline-block; 
                padding: 0.3rem 0.8rem; 
                border-radius: 20px; 
                color: white; 
                font-size: 0.8rem; 
                font-weight: bold;
            }
            .priority-alta { background: #e74c3c; }
            .priority-media { background: #f39c12; }
            .priority-baixa { background: #27ae60; }
            .loading { 
                text-align: center; 
                padding: 2rem; 
                color: #666; 
            }
            .back-btn {
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Histórico de Notícias</h1>
            <p>BRAZMAR MARINE SERVICES - Todas as notícias processadas</p>
        </div>

        <div class="container">
            <a href="/" class="btn back-btn">← Voltar ao Dashboard</a>

            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div>Total de Notícias</div>
                    <div class="stat-number" id="totalNews">0</div>
                    <div>No histórico</div>
                </div>
                <div class="stat-card">
                    <div>Última Atualização</div>
                    <div class="stat-number" id="lastUpdated">-</div>
                    <div>Do histórico</div>
                </div>
            </div>

            <div class="controls">
                <input type="text" id="searchInput" class="search-box" placeholder="🔍 Buscar por palavra-chave..." />
                <button class="btn" onclick="searchHistory()">Buscar</button>
                <button class="btn btn-success" onclick="loadRecent()">Ver Recentes</button>
                <button class="btn" onclick="clearSearch()">Limpar</button>
            </div>

            <div class="news-list">
                <h2 style="margin-bottom: 1.5rem;" id="resultsTitle">📰 Últimas Notícias no Histórico</h2>
                <div id="historyResults">
                    <div class="loading">Carregando notícias...</div>
                </div>
            </div>
        </div>

        <script>
            function loadStats() {
                fetch('/api/historico/estatisticas')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('totalNews').textContent = data.total_news;
                        document.getElementById('lastUpdated').textContent = 
                            data.last_updated === 'Nunca' ? 'Nunca' : 
                            new Date(data.last_updated).toLocaleDateString('pt-BR');
                    });
            }
            
            function loadRecent() {
                document.getElementById('resultsTitle').textContent = '📰 Últimas Notícias no Histórico';
                document.getElementById('historyResults').innerHTML = '<div class="loading">Carregando...</div>';
                
                fetch('/api/historico/recentes')
                    .then(r => r.json())
                    .then(data => {
                        displayResults(data);
                    })
                    .catch(error => {
                        document.getElementById('historyResults').innerHTML = '<div class="loading">Erro ao carregar</div>';
                    });
            }
            
            function searchHistory() {
                const query = document.getElementById('searchInput').value.trim();
                if (!query) {
                    alert('Digite algo para buscar');
                    return;
                }
                
                document.getElementById('resultsTitle').textContent = `🔍 Resultados para: "${query}"`;
                document.getElementById('historyResults').innerHTML = '<div class="loading">Buscando...</div>';
                
                fetch('/api/historico/buscar?q=' + encodeURIComponent(query))
                    .then(r => r.json())
                    .then(data => {
                        displayResults(data);
                    })
                    .catch(error => {
                        document.getElementById('historyResults').innerHTML = '<div class="loading">Erro na busca</div>';
                    });
            }
            
            function clearSearch() {
                document.getElementById('searchInput').value = '';
                loadRecent();
            }
            
            function displayResults(articles) {
                const container = document.getElementById('historyResults');
                
                if (articles.length === 0) {
                    container.innerHTML = '<div class="loading">Nenhuma notícia encontrada</div>';
                    return;
                }
                
                container.innerHTML = articles.map(article => `
                    <div class="news-item">
                        <div class="news-title">${escapeHtml(article.title || 'Sem título')}</div>
                        <div class="news-meta">
                            ${article.urgencia ? `<span class="priority-badge priority-${article.urgencia.toLowerCase()}">${article.urgencia}</span>` : ''}
                            <span>📅 ${formatDate(article.added_to_history)}</span>
                            <span>📰 ${escapeHtml(article.source || 'Fonte desconhecida')}</span>
                            ${article.confianca ? `<span>🎯 ${article.confianca}% confiança</span>` : ''}
                        </div>
                        <div class="news-summary">${escapeHtml(article.summary || 'Sem resumo')}</div>
                        <div style="margin-top: 0.5rem;">
                            <a href="${article.link}" target="_blank" style="color: #3498db; text-decoration: none;">🔗 Ver notícia original</a>
                        </div>
                    </div>
                `).join('');
            }
            
            function formatDate(dateString) {
                if (!dateString) return 'Data desconhecida';
                try {
                    return new Date(dateString).toLocaleString('pt-BR');
                } catch {
                    return dateString;
                }
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            // Carrega ao abrir a página
            loadStats();
            loadRecent();
            
            // Enter para buscar
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchHistory();
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/historico/recentes')
def api_historico_recentes():
    """API para histórico recente"""
    try:
        recent = history_manager.get_recent_history(100)
        return jsonify(recent)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/historico/buscar')
def api_historico_buscar():
    """API para buscar no histórico"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        results = history_manager.search_history(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/historico/estatisticas')
def api_historico_estatisticas():
    """API para estatísticas do histórico"""
    try:
        stats = history_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# INICIALIZAÇÃO DO SISTEMA OTIMIZADO
print("=" * 60)
print("🚀 BRAZMAR NEWS BOT OTIMIZADO - INICIANDO NO RENDER")
print("=" * 60)
print(f"🔑 Gemini: {'✅ CONFIGURADO' if os.getenv('GEMINI_API_KEY') else '❌ NÃO CONFIGURADO'}")
print(f"🔑 GitHub: {'✅ CONFIGURADO' if os.getenv('GITHUB_TOKEN') else '❌ NÃO CONFIGURADO'}")
print(f"🗄️  Database: {'PostgreSQL' if db.use_postgres else 'SQLite'}")
print(f"🎯 Região Foco: NORTE/NORDESTE BRASIL")
print(f"🤖 Provedor IA: Gemini Flash 2.0")
print(f"📊 Rate Limit: 8 RPM máximo")
print(f"🌐 Porta: {PORT}")

# Garante que CSV existe
criar_csv_se_nao_existir()

# Baixa CSV do GitHub ao iniciar
try:
    if os.getenv("GITHUB_TOKEN"):
        print("📥 Baixando CSV do GitHub...")
        github_manager.download_csv_for_ml()
except Exception as e:
    print(f"⚠️ Erro baixando CSV inicial: {e}")

# Inicia agendador IMEDIATAMENTE
try:
    scheduler.iniciar()
    print("✅ Agendador OTIMIZADO iniciado com COLETA IMEDIATA")
except Exception as e:
    print(f"❌ ERRO no agendador: {e}")
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    # Inicia servidor web
    app.run(host='0.0.0.0', port=PORT, debug=False)