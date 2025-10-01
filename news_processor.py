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
import time

class NewsProcessorCompleto:
    def __init__(self):
        self.model_file = "relevance_model.pkl"
        self.vectorizer_file = "vectorizer.pkl" 
        self.feedback_file = "feedback.csv"
        self.data_file = "database/news_database.json"
        
        # KEYWORDS ESPECÍFICAS BRAZMAR MARINE SERVICES
        self.KEYWORDS = [
            # Seguros marítimos e riscos
            "seguro marítimo", "sinistro naval", "avaria", "indenização marítima",
            "risco marítimo", "seguradora marítima", "apólice marítima", "seguro de carga",
            
            # Portos brasileiros específicos
            "porto de Itaqui", "porto do Pecém", "porto de Suape", "porto de Santos",
            "porto de Paranaguá", "porto de Rio Grande", "porto de São Luís", "porto de Fortaleza",
            
            # Regulamentação e órgãos
            "ANTAQ", "Marinha do Brasil", "DPC", "Capitania dos Portos", "Marinha",
            "regulamentação portuária", "normativa portuária", "legislação marítima",
            
            # Operações portuárias
            "cabotagem", "navegação interior", "hidrovia", "transporte aquaviário",
            "terminal portuário", "movimentação portuária", "operações portuárias", "carga marítima",
            
            # Regiões de atuação
            "Maranhão", "Ceará", "Amapá", "Pará", "Nordeste", "Norte",
            "São Luís", "Fortaleza", "Macapá", "Belém",
            
            # Acidentes e incidentes
            "acidente naval", "naufrágio", "colisão naval", "incidente portuário",
            "acidente portuário", "avaria em navio", "navio", "porto", "marítimo"
        ]
        
        self.NEGATIVE_KEYWORDS = [
            "global", "internacional", "EUA", "China", "Europa", "Ásia",
            "cruzeiro", "turismo", "pesca esportiva", "iate", "veleiro",
            "histórico", "antigo", "cultural", "festival", "entretenimento"
        ]
        
        self.setup_gemini()
        self.setup_ml_system()
    
    def setup_gemini(self):
        """Configura Gemini com tratamento de erro robusto"""
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            print("❌ GEMINI_API_KEY não encontrada nas variáveis de ambiente")
            self.gemini_enabled = False
            return

        try:
            print("🔑 Configurando Gemini...")
            genai.configure(api_key=api_key)
            
            # Tenta o modelo que você quer usar - Gemini 2.5 Pro
            try:
                self.model = genai.GenerativeModel('gemini-2.5-pro')
                print("✅ Gemini 2.5 Pro configurado com sucesso")
                self.gemini_enabled = True
                return
            except Exception as model_error:
                print(f"❌ Erro com Gemini 2.5 Pro: {model_error}")
                # Fallback para outros modelos
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    print("✅ Fallback para Gemini 1.5 Flash")
                    self.gemini_enabled = True
                except Exception as fallback_error:
                    print(f"❌ Fallback também falhou: {fallback_error}")
                    self.gemini_enabled = False
                    
        except Exception as e:
            print(f"❌ Erro crítico na configuração do Gemini: {e}")
            self.gemini_enabled = False
    
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
            
            # Debug do filtro
            score = self.debug_filtro(artigo)
            
            # Filtro automático
            relevante_auto = score >= 1
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
    
    def debug_filtro(self, artigo):
        """Debug detalhado do filtro"""
        combined_text = (artigo['title'] + " " + artigo['summary']).lower()
        
        keywords_encontradas = [kw for kw in self.KEYWORDS if kw.lower() in combined_text]
        negative_encontradas = [nkw for nkw in self.NEGATIVE_KEYWORDS if nkw.lower() in combined_text]
        
        score = len(keywords_encontradas) - len(negative_encontradas)*2
        
        print(f"   🔍 DEBUG FILTRO:")
        print(f"   📰 Título: {artigo['title'][:60]}...")
        print(f"   ✅ Keywords: {keywords_encontradas}")
        print(f"   ❌ Negative: {negative_encontradas}")
        print(f"   📊 Score: {score}")
        
        return score
    
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
        """Filtro ESPECÍFICO para BRAZMAR MARINE SERVICES"""
        if not self.gemini_enabled or not hasattr(self, 'model'):
            print("   ⚠️ Gemini não disponível para análise")
            return True  # Permite que o artigo passe se Gemini não estiver disponível
        
        try:
            prompt = f"""
            ANALISAR para BRAZMAR MARINE SERVICES (seguros marítimos, consultoria portuária no Brasil):

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

            Esta notícia é RELEVANTE para seguros marítimos ou operações portuárias da BRAZMAR?

            Responda APENAS com JSON:
            {{
                "relevante": true/false,
                "confianca": 0-100,
                "motivo": "explicação específica",
                "urgencia": "BAIXA/MEDIA/ALTA"
            }}
            """
            
            # Configuração de segurança
            generation_config = {
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 500,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
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
            print(f"   ❌ Erro Gemini na análise: {e}")
            # Em caso de erro, permite que o artigo passe
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