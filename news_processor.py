import google.generativeai as genai
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os
import json
import re
from datetime import datetime

class NewsProcessorCompleto:
    def __init__(self):
        self.model_file = "relevance_model.pkl"
        self.vectorizer_file = "vectorizer.pkl" 
        self.feedback_file = "feedback.csv"
        self.data_file = "database/news_database.json"
        
        # Keywords ajustadas para português
        self.KEYWORDS = [
            # Seguros marítimos e riscos
            "seguro marítimo", "sinistro naval", "avaria", "indenização marítima",
            "risco marítimo", "seguradora marítima", "apólice marítima",
        
            # Portos brasileiros específicos
            "porto de Itaqui", "porto do Pecém", "porto de Suape", "porto de Santos",
            "porto de Paranaguá", "porto de Rio Grande", "porto de São Luís",
        
            # Regulamentação e órgãos
            "ANTAQ", "Marinha do Brasil", "DPC", "Capitania dos Portos",
            "regulamentação portuária", "normativa portuária", "legislação marítima",
        
            # Operações portuárias
            "cabotagem", "navegação interior", "hidrovia", "transporte aquaviário",
            "terminal portuário", "movimentação portuária", "operações portuárias",
        
            # Regiões de atuação
            "Maranhão", "Ceará", "Amapá", "Pará", "Nordeste", "Norte",
            "São Luís", "Fortaleza", "Macapá", "Belém",
        
            # Acidentes e incidentes
            "acidente naval", "naufrágio", "colisão naval", "incidente portuário",
            "acidente portuário", "avaria em navio"
        ]
        
        self.NEGATIVE_KEYWORDS = [
            "global", "internacional", "EUA", "China", "Europa", "Ásia",
            "cruzeiro", "turismo", "pesca esportiva", "iate", "veleiro",
            "histórico", "antigo", "cultural", "festival", "entretenimento"
        ]
        
        self.setup_gemini()
        self.setup_ml_system()
    
    def setup_gemini(self):
        """Configura Gemini"""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "sua_chave_gemini_aqui":
            try:
                genai.configure(api_key=api_key)
                self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
                self.gemini_enabled = True
                print("✅ Gemini Configurado")
            except Exception as e:
                print(f"❌ Erro configurando Gemini: {e}")
                self.gemini_enabled = False
        else:
            self.gemini_enabled = False
            print("⚠️ Gemini não configurado - usando apenas filtros básicos")
    
    def setup_ml_system(self):
        """Sistema de ML"""
        self.ml_model, self.ml_vectorizer = self.load_ml_model()
        if self.ml_model is None:
            print("🔧 Modelo ML será treinado quando houver feedback suficiente")
    
    def executar_coleta_completa(self):
        """Executa processamento COMPLETO"""
        print("🚀 INICIANDO PROCESSAMENTO COMPLETO BRAZMAR")
        
        try:
            from scraper import fetch_rss, fetch_scrape
            artigos_rss = fetch_rss()
            artigos_scrape = fetch_scrape()
            artigos = artigos_rss + artigos_scrape
            print(f"📰 {len(artigos)} notícias coletadas inicialmente")
        except Exception as e:
            print(f"❌ Erro na coleta: {e}")
            return []
        
        # Pré-processamento
        artigos_processados = self.preprocessar_artigos(artigos)
        
        # Filtragem
        artigos_relevantes = self.filtrar_artigos(artigos_processados)
        print(f"✅ {len(artigos_relevantes)} notícias relevantes encontradas")
        
        # Salvar no database
        self.salvar_no_database(artigos_relevantes)
        
        return artigos_relevantes
    
    def preprocessar_artigos(self, artigos):
        """Pré-processamento dos artigos"""
        artigos_processados = []
        
        for artigo in artigos:
            processed_artigo = artigo.copy()
            
            # Garante campos obrigatórios
            processed_artigo['title'] = processed_artigo.get('title', 'Sem Título').strip()
            processed_artigo['summary'] = processed_artigo.get('summary', '').strip()
            processed_artigo['source'] = processed_artigo.get('source', 'Unknown').strip()
            
            # Limpeza básica
            processed_artigo['summary'] = re.sub(r'http\S+', '', processed_artigo['summary'])
            processed_artigo['summary'] = ' '.join(processed_artigo['summary'].split())
            
            # Se summary muito curto, usa título
            if len(processed_artigo['summary']) < 20:
                processed_artigo['summary'] = processed_artigo['title']
            
            artigos_processados.append(processed_artigo)
        
        return artigos_processados
    
    def filtrar_artigos(self, artigos):
        """Filtragem HÍBRIDA (ML + Gemini)"""
        artigos_relevantes = []
        
        for i, artigo in enumerate(artigos):
            print(f"🔍 Analisando {i+1}/{len(artigos)}: {artigo['title'][:50]}...")
            
            # Filtro automático
            relevante_auto = self.filtro_automatico(artigo)
            if not relevante_auto:
                print("   ❌ Rejeitado pelo filtro automático")
                continue
            
            # Filtro ML (se disponível)
            if self.ml_model is not None:
                relevante_ml = self.filtrar_por_ml(artigo)
                if not relevante_ml:
                    print("   ❌ Rejeitado pelo ML")
                    continue
            
            # Gemini (se disponível)
            if self.gemini_enabled:
                relevante_gemini = self.filtrar_por_gemini(artigo)
                if not relevante_gemini:
                    print("   ❌ Rejeitado pelo Gemini")
                    continue
                else:
                    print("   ✅ Aprovado pelo Gemini")
            else:
                print("   ✅ Aprovado pelos filtros básicos")
            
            # Adiciona metadados
            artigo['processed_at'] = datetime.now().isoformat()
            artigo['collection_date'] = datetime.now().strftime("%Y-%m-%d")
            artigo['ai_analyzed'] = self.gemini_enabled
            
            # Define urgência padrão se não definida pelo Gemini
            if 'urgencia' not in artigo:
                artigo['urgencia'] = 'MEDIA'
            if 'confianca' not in artigo:
                artigo['confianca'] = 70
                
            artigos_relevantes.append(artigo)
        
        return artigos_relevantes
    
    def filtro_automatico(self, artigo):
        """Filtro automático por keywords"""
        combined_text = (artigo['title'] + " " + artigo['summary']).lower()
        score = sum(1 for kw in self.KEYWORDS if kw.lower() in combined_text)
        
        # Penaliza por negative keywords
        negative_score = sum(1 for nkw in self.NEGATIVE_KEYWORDS if nkw.lower() in combined_text)
        score -= negative_score * 2
        
        print(f"   🔧 Score automático: {score}")
        return score >= 2  # Reduzido o threshold para capturar mais notícias
    
    def filtrar_por_ml(self, artigo):
        """Filtro por Machine Learning"""
        if self.ml_model is None or self.ml_vectorizer is None:
            return True
        
        try:
            combined_text = artigo['title'] + " " + artigo['summary']
            features = self.ml_vectorizer.transform([combined_text])
            prediction = self.ml_model.predict(features)[0]
            probability = self.ml_model.predict_proba(features)[0][1]
            
            print(f"   🤖 ML - Predição: {prediction}, Probabilidade: {probability:.2f}")
            return prediction == 1 and probability > 0.5
            
        except Exception as e:
            print(f"   ❌ Erro ML: {e}")
            return True
    
    def filtrar_por_gemini(self, artigo):
        """Filtro por Gemini AI"""
        try:
            prompt = f"""
            ANALISAR para BRAZMAR MARINE SERVICES (seguros marítimos, consultoria portuária):

            TÍTULO: {artigo['title']}
            RESUMO: {artigo['summary']}

            CRITÉRIOS ESTRITOS - A notícia deve ser sobre:
            ✅ Seguros marítimos, sinistros navais, avarias
            ✅ Portos brasileiros (Itaqui, Pecém, Suape, Santos, etc.)
            ✅ ANTAQ, Marinha do Brasil, regulamentação portuária
            ✅ Acidentes/incidentes em portos ou navios
            ✅ Operações de cabotagem, navegação interior
            ✅ Região Norte/Nordeste do Brasil

            ❌ REJEITAR se for sobre:
            ❌ Turismo, cruzeiros, pesca esportiva
            ❌ Notícias internacionais
            ❌ Entretenimento, cultura, eventos
            ❌ Assuntos gerais sem ligação direta com operações marítimas

            Responda APENAS com JSON:
            {{
                "relevante": true/false,
                "confianca": 0-100,
                "motivo": "explicação específica",
                "urgencia": "BAIXA/MEDIA/ALTA"
            }}
            """
            
            response = self.model_flash.generate_content(prompt)
            analysis = self.parse_resposta_gemini(response.text)
            
            if analysis.get('relevante', False):
                artigo['gemini_analysis'] = analysis
                artigo['confianca'] = analysis.get('confianca', 0)
                artigo['urgencia'] = analysis.get('urgencia', 'BAIXA')
                print(f"   ✅ Gemini - Confiança: {analysis.get('confianca', 0)}%")
                return True
            else:
                print(f"   ❌ Gemini - Motivo: {analysis.get('motivo', 'N/A')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erro Gemini: {e}")
            return True
    
    def parse_resposta_gemini(self, response_text):
        """Parse da resposta do Gemini"""
        try:
            cleaned = re.sub(r'```json|```', '', response_text).strip()
            json_match = re.search(r'\{[^}]*\}', cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"   ❌ Erro parse Gemini: {e}")
        
        return {"relevante": False, "confianca": 0, "motivo": "Erro na análise", "urgencia": "BAIXA"}
    
    def load_ml_model(self):
        """Carrega modelo ML"""
        if os.path.exists(self.model_file) and os.path.exists(self.vectorizer_file):
            try:
                model = joblib.load(self.model_file)
                vectorizer = joblib.load(self.vectorizer_file)
                print("✅ Modelo ML carregado do cache")
                return model, vectorizer
            except Exception as e:
                print(f"❌ Erro carregando ML: {e}")
        return None, None
    
    def train_ml_model(self):
        """Treina modelo ML com feedback"""
        if not os.path.exists(self.feedback_file) or os.path.getsize(self.feedback_file) < 50:
            print("📊 CSV de feedback vazio ou insuficiente")
            return None, None
        
        try:
            df = pd.read_csv(self.feedback_file)
            
            if 'relevant' not in df.columns or len(df) < 5:
                print("⚠️ Dados insuficientes para treinar ML")
                return None, None
            
            df['text'] = df['title'].fillna('') + " " + df['summary'].fillna('')
            texts = df['text'].tolist()
            labels = df['relevant'].astype(bool).tolist()
            
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=500, stop_words='portuguese')),
                ('clf', LogisticRegression())
            ])
            
            pipeline.fit(texts, labels)
            joblib.dump(pipeline.named_steps['clf'], self.model_file)
            joblib.dump(pipeline.named_steps['tfidf'], self.vectorizer_file)
            print("✅ Modelo ML treinado com feedback")
            return pipeline.named_steps['clf'], pipeline.named_steps['tfidf']
            
        except Exception as e:
            print(f"❌ Erro treinamento ML: {e}")
            return None, None
    
    def salvar_no_database(self, artigos):
        """Salva artigos no database JSON"""
        os.makedirs("database", exist_ok=True)
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"articles": [], "stats": {}}
        
        # Adiciona novos artigos (evita duplicatas)
        titulos_existentes = {a['title'] for a in data['articles']}
        novos = 0
        
        for artigo in artigos:
            if artigo['title'] not in titulos_existentes:
                data['articles'].append(artigo)
                novos += 1
        
        # Mantém apenas últimos 200 artigos
        data['articles'] = data['articles'][-200:]
        
        # Atualiza estatísticas
        hoje = datetime.now().strftime("%Y-%m-%d")
        artigos_hoje = [a for a in data['articles'] if a.get('collection_date') == hoje]
        
        data['stats'] = {
            "total_articles": len(data['articles']),
            "today_articles": len(artigos_hoje),
            "last_updated": datetime.now().isoformat()
        }
        
        data['last_updated'] = datetime.now().isoformat()
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Database atualizado: {novos} novos artigos (total: {len(data['articles'])})")