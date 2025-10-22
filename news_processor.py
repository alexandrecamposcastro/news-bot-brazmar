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

# Importar providers novos
from gemini_provider import gemini_provider
from circular_expert import circular_expert
from database_hybrid import db
from history_manager import history_manager

class NewsProcessorCompleto:
    def __init__(self):
        self.model_file = "relevance_model.pkl"
        self.data_file = "database/news_database.json"
        
        # KEYWORDS ESPECÍFICAS NORTE/NORDESTE
        self.REGIAO_KEYWORDS = [
            'norte', 'nordeste', 'maranhão', 'ceará', 'piauí', 'bahia', 
            'pernambuco', 'alagoas', 'sergipe', 'paraíba', 'rio grande do norte',
            'amapá', 'pará', 'amazonas', 'rondônia', 'acre', 'roraima', 'tocantins',
            'itaqui', 'pecem', 'suape', 'são luís', 'fortaleza', 'belém', 'macapá',
            'manaus', 'recife', 'salvador', 'natal', 'joão pessoa'
        ]
        
        self.setup_ml_system()

    def setup_ml_system(self):
        """Sistema ML opcional"""
        try:
            if os.path.exists(self.model_file):
                self.ml_model = joblib.load(self.model_file)
                print("✅ Modelo ML carregado")
            else:
                self.ml_model = None
                print("🔧 ML será treinado quando houver dados")
        except:
            self.ml_model = None

    def executar_coleta_completa(self):
        """Processamento COMPLETO com BUSCA ATIVA do Gemini"""
        print("🚀 INICIANDO COLETA BRAZMAR - BUSCA ATIVA + FILTRAGEM")
    
        todas_noticias = []
    
        try:
            # 🎯 FASE 1: BUSCA ATIVA DO GEMINI
            print("🔍 INICIANDO BUSCA ATIVA DO GEMINI...")
            noticias_gemini = gemini_provider.buscar_noticias_ativas()
            print(f"🎯 Gemini encontrou {len(noticias_gemini)} notícias ativamente")
        
            # Converte notícias do Gemini para o formato padrão
            for noticia in noticias_gemini:
                noticia['link'] = f"gemini_search_{hash(noticia['title'])}"
                noticia['summary'] = noticia.get('summary', 'Busca ativa Gemini')
                todas_noticias.append(noticia)
        
            # 🎯 FASE 2: COLETA TRADICIONAL (RSS + Scrape)
            from scraper import fetch_rss, fetch_scrape
            artigos_rss = fetch_rss()
            artigos_scrape = fetch_scrape()
            todas_noticias.extend(artigos_rss + artigos_scrape)
        
            print(f"📰 Total coletado: {len(todas_noticias)} notícias (Gemini: {len(noticias_gemini)} + Tradicional: {len(artigos_rss + artigos_scrape)})")
        
        except Exception as e:
            print(f"❌ Erro na coleta: {e}")
            return []

        # PRÉ-FILTRO RIGOROSO
        artigos_pre_filtrados = self.pre_filtro_rigoroso(todas_noticias)
        print(f"🔍 Pré-filtro: {len(todas_noticias)} → {len(artigos_pre_filtrados)}")

        # FILTRAGEM GEMINI
        artigos_relevantes = self.filtrar_com_gemini(artigos_pre_filtrados)
        print(f"✅ Filtro Gemini: {len(artigos_relevantes)} notícias relevantes")

        # GERA CIRCULAR
        if artigos_relevantes:
            circular = circular_expert.generate_circular(artigos_relevantes)
            self.salvar_circular(circular)
            print("📨 CIRCULAR GERADA COM SUCESSO!")

        # Salva resultados
        self.salvar_no_database(artigos_relevantes)
    
        return artigos_relevantes

    def executar_coleta_completa(self):
        """Processamento COMPLETO - SEM PRÉ-FILTRO"""
        print("🚀 INICIANDO COLETA BRAZMAR - GEMINI 100% RESPONSÁVEL")
        
        todas_noticias = []
        
        try:
            # 🎯 FASE 1: BUSCA ATIVA DO GEMINI (DEVERIA ESTAR FUNCIONANDO)
            print("🔍 INICIANDO BUSCA ATIVA DO GEMINI...")
            noticias_gemini = gemini_provider.buscar_noticias_ativas()
            print(f"🎯 Gemini encontrou {len(noticias_gemini)} notícias ativamente")
            
            # Converte notícias do Gemini para o formato padrão
            for noticia in noticias_gemini:
                noticia['link'] = f"gemini_search_{hash(noticia['title'])}"
                noticia['summary'] = noticia.get('summary', 'Busca ativa Gemini')
                noticia['type'] = 'gemini_active_search'
                todas_noticias.append(noticia)
            
            # 🎯 FASE 2: COLETA TRADICIONAL 
            from scraper import fetch_rss, fetch_scrape
            artigos_rss = fetch_rss()
            artigos_scrape = fetch_scrape()
            todas_noticias.extend(artigos_rss + artigos_scrape)
            
            print(f"📰 Total coletado: {len(todas_noticias)} notícias")
            print(f"   - Busca ativa Gemini: {len(noticias_gemini)}")
            print(f"   - Fontes tradicionais: {len(artigos_rss + artigos_scrape)}")
            
        except Exception as e:
            print(f"❌ Erro na coleta: {e}")
            return []

        # 🎯 FASE 3: FILTRAGEM 100% GEMINI (SEM PRÉ-FILTRO)
        print("🔍 INICIANDO FILTRAGEM 100% GEMINI...")
        artigos_relevantes = self.filtrar_com_gemini(todas_noticias)
        print(f"✅ Filtro Gemini: {len(artigos_relevantes)} notícias relevantes")

        # GERA CIRCULAR
        if artigos_relevantes:
            circular = circular_expert.generate_circular(artigos_relevantes)
            self.salvar_circular(circular)
            print("📨 CIRCULAR GERADA COM SUCESSO!")

        # Salva resultados
        self.salvar_no_database(artigos_relevantes)
        
        return artigos_relevantes

    def filtrar_com_gemini(self, artigos):
        """Usa Gemini APENAS para os artigos pré-filtrados"""
        artigos_relevantes = []
        
        for i, artigo in enumerate(artigos):
            print(f"🔍 Gemini analisando {i+1}/{len(artigos)}: {artigo['title'][:50]}...")
            
            analysis = gemini_provider.analyze_article(artigo['title'], artigo.get('summary', ''))
            
            if analysis.get('relevante', False):
                # Adiciona metadados da análise
                artigo.update({
                    'processed_at': datetime.now().isoformat(),
                    'collection_date': datetime.now().strftime("%Y-%m-%d"),
                    'confianca': analysis.get('confianca', 0),
                    'urgencia': analysis.get('urgencia', 'MEDIA'),
                    'ia_analysis': analysis
                })
                artigos_relevantes.append(artigo)
                print(f"   ✅ Aprovado ({analysis.get('confianca', 0)}% confiança)")
            else:
                print(f"   ❌ Rejeitado: {analysis.get('motivo', 'N/A')}")
        
        return artigos_relevantes

    def salvar_circular(self, circular):
        """Salva circular em arquivo"""
        try:
            os.makedirs("circulars", exist_ok=True)
            data = datetime.now().strftime("%Y-%m-%d")
            filename = f"circulars/brazmar_circular_{data}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(circular)
            
            print(f"💾 Circular salva: {filename}")
        except Exception as e:
            print(f"❌ Erro salvando circular: {e}")

    def salvar_no_database(self, artigos):
        """Salva artigos no database"""
        os.makedirs("database", exist_ok=True)
        
        # Salva no JSON
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"articles": [], "stats": {}}

        # Adiciona novos (evita duplicatas)
        titulos_existentes = {a['title'] for a in data['articles']}
        novos = 0
        
        for artigo in artigos:
            if artigo['title'] not in titulos_existentes:
                data['articles'].append(artigo)
                novos += 1
                # Adiciona ao histórico
                history_manager.add_to_history(artigo)

        # Mantém só últimos 200
        data['articles'] = data['articles'][-200:]
        
        # Atualiza stats
        hoje = datetime.now().strftime("%Y-%m-%d")
        artigos_hoje = [a for a in data['articles'] if a.get('collection_date') == hoje]
        
        data['stats'] = {
            "total_articles": len(data['articles']),
            "today_articles": len(artigos_hoje),
            "last_updated": datetime.now().isoformat()
        }

        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Salva no banco também
        for artigo in artigos:
            db.save_article(artigo)

        print(f"💾 Database: {novos} novos artigos salvos")

# Instância global
news_processor = NewsProcessorCompleto()