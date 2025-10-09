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
import sqlite3

# Importar database e IA
from database_hybrid import db
from ai_provider import ai_provider

class NewsProcessorCompleto:
    def __init__(self):
        self.model_file = "relevance_model.pkl"
        self.vectorizer_file = "vectorizer.pkl" 
        self.data_file = "database/news_database.json"
        
        # KEYWORDS ESPECÍFICAS BRAZMAR MARINE SERVICES
        self.KEYWORDS = [
            # Seguros marítimos e riscos
            "seguro marítimo", "sinistro naval", "avaria", "indenização marítima",
            "risco marítimo", "seguradora marítima", "apólice marítima", "seguro de carga",
            
            # Portos brasileiros específicos
            "porto de itaqui", "porto do pecém", "porto de suape", "porto de santos",
            "porto de paranaguá", "porto de rio grande", "porto de são luís", "porto de fortaleza",
            "porto de belém", "porto de macapá", "porto de manaus",
            
            # Órgãos e regulamentação
            "antaq", "marinha do brasil", "dpc", "capitania dos portos", "marinha",
            "regulamentação portuária", "normativa portuária", "legislação marítima",
            "ibama", "polícia federal", "pf", "agricultura", "defesa agropecuária",
            
            # Operações marítimas
            "cabotagem", "navegação interior", "hidrovia", "transporte aquaviário",
            "terminal portuário", "movimentação portuária", "operações portuárias", 
            "carga marítima", "navio", "embarcação", "transporte de carga",
            
            # Regiões de atuação
            "maranhão", "ceará", "amapá", "pará", "nordeste", "norte",
            "são luís", "fortaleza", "macapá", "belém", "manaus",
            
            # Acidentes e incidentes
            "acidente naval", "naufrágio", "colisão naval", "incidente portuário",
            "acidente portuário", "avaria em navio", "incidente marítimo",
            
            # Novos termos dos sites adicionados
            "transito e transportes", "transporte aquaviario", "migalhas maritimas",
            "diretoria de portos", "comando distrito naval", "agência brasil",
            "polícia federal", "ibama", "ministério agricultura"
        ]
        
        self.NEGATIVE_KEYWORDS = [
            "global", "internacional", "EUA", "China", "Europa", "Ásia",
            "cruzeiro", "turismo", "pesca esportiva", "iate", "veleiro",
            "histórico", "antigo", "cultural", "festival", "entretenimento"
        ]
        
        self.setup_gemini()
        self.setup_ml_system()
    
    def setup_gemini(self):
        """Configura Gemini (opcional)"""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "AIzaSyCamSIYRSrZ9JUHtnVNgLKdkQ42ySYAdNA":
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.gemini_enabled = True
                print("✅ Gemini Configurado (opcional)")
            except Exception as e:
                print(f"❌ Erro configurando Gemini: {e}")
                self.gemini_enabled = False
        else:
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
        """Filtragem HÍBRIDA (ML + Multi-IA)"""
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
            
            # Multi-IA (substitui Gemini)
            relevante_ia = self.filtrar_por_ia(artigo)
            if not relevante_ia:
                print("   ❌ Rejeitado pela IA")
                continue
            else:
                print("   ✅ Aprovado pela IA")
            
            # Adiciona metadados
            artigo['processed_at'] = datetime.now().isoformat()
            artigo['collection_date'] = datetime.now().strftime("%Y-%m-%d")
            artigo['ai_analyzed'] = True
            artigo['ai_provider'] = ai_provider.current_provider
            
            # Define urgência padrão se não definida pela IA
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
    
    def filtrar_por_ia(self, artigo):
        """Filtro usando Multi-IA"""
        try:
            analysis = ai_provider.analyze_article(artigo['title'], artigo['summary'])
            
            if analysis.get('relevante', False):
                artigo['ia_analysis'] = analysis
                artigo['confianca'] = analysis.get('confianca', 0)
                artigo['urgencia'] = analysis.get('urgencia', 'MEDIA')
                artigo['ia_provider'] = ai_provider.current_provider
                print(f"   ✅ {ai_provider.current_provider.upper()} - Confiança: {analysis.get('confianca', 0)}%")
                return True
            else:
                print(f"   ❌ {ai_provider.current_provider.upper()} - Motivo: {analysis.get('motivo', 'N/A')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erro IA: {e}")
            return True  # Em caso de erro, permite passar
    
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
        """Treina modelo ML com feedbacks do CSV"""
        try:
            import pandas as pd
            import csv
            
            # Tenta carregar do CSV
            dados = []
            if os.path.exists("feedback.csv"):
                with open("feedback.csv", 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['title'] and row['relevant']:  # Verifica se não está vazio
                            dados.append({
                                'text': f"{row['title']} {row.get('summary', '')}",
                                'label': row['relevant'].lower() == 'true'
                            })
            
            if len(dados) < 5:
                print("⚠️ Poucos feedbacks para treinar ML (mínimo 5)")
                return None, None
            
            print(f"🎯 Treinando ML com {len(dados)} feedbacks do CSV...")
            
            # Prepara dados
            textos = [item['text'] for item in dados]
            labels = [item['label'] for item in dados]
            
            # Treina modelo
            vectorizer = TfidfVectorizer(max_features=500, stop_words='portuguese')
            X = vectorizer.fit_transform(textos)
            
            model = LogisticRegression()
            model.fit(X, labels)
            
            # Salva modelo
            joblib.dump(model, self.model_file)
            joblib.dump(vectorizer, self.vectorizer_file)
            
            print(f"✅ ML treinado! {sum(labels)} relevantes, {len(labels)-sum(labels)} irrelevantes")
            return model, vectorizer
            
        except Exception as e:
            print(f"❌ Erro treinamento ML: {e}")
            return None, None
    
    def salvar_no_database(self, artigos):
        """Salva artigos no JSON E no banco"""
        os.makedirs("database", exist_ok=True)
        
        # Salva no JSON (backup)
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
        
        # Salva no banco
        salvos_db = 0
        for artigo in artigos:
            if db.save_article(artigo):
                salvos_db += 1
        
        print(f"💾 Database atualizado: {novos} novos artigos (JSON), {salvos_db} no banco")