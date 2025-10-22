import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self):
        self.history_file = "database/news_history.json"
        self.ensure_history_file()
    
    def ensure_history_file(self):
        """Garante que o arquivo de histórico existe"""
        try:
            os.makedirs("database", exist_ok=True)
            if not os.path.exists(self.history_file):
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "news_history": [],
                        "last_updated": None,
                        "total_news": 0
                    }, f, indent=2, ensure_ascii=False)
                print("✅ Arquivo de histórico criado")
        except Exception as e:
            print(f"❌ Erro criando histórico: {e}")
    
    def add_to_history(self, article):
        """Adiciona notícia ao histórico"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verifica se já existe (evita duplicatas)
            existing_links = {a.get('link', '') for a in data['news_history']}
            if article.get('link', '') in existing_links:
                return False
            
            # Adiciona metadados
            article_with_meta = article.copy()
            article_with_meta['added_to_history'] = datetime.now().isoformat()
            article_with_meta['history_id'] = len(data['news_history']) + 1
            
            data['news_history'].append(article_with_meta)
            data['last_updated'] = datetime.now().isoformat()
            data['total_news'] = len(data['news_history'])
            
            # Mantém apenas últimos 1000 registros
            if len(data['news_history']) > 1000:
                data['news_history'] = data['news_history'][-1000:]
                data['total_news'] = 1000
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"📚 Notícia adicionada ao histórico: {article.get('title', '')[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Erro adicionando ao histórico: {e}")
            return False
    
    def get_recent_history(self, limit=100):
        """Pega histórico recente"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Retorna as mais recentes primeiro
            recent = sorted(data['news_history'], 
                          key=lambda x: x.get('added_to_history', ''), 
                          reverse=True)[:limit]
            return recent
        except Exception as e:
            print(f"❌ Erro lendo histórico: {e}")
            return []
    
    def search_history(self, query):
        """Busca no histórico por palavra-chave"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            query = query.lower()
            results = []
            
            for article in data['news_history']:
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                source = article.get('source', '').lower()
                
                if (query in title or query in summary or query in source):
                    results.append(article)
            
            return results[:50]  # Limita resultados
            
        except Exception as e:
            print(f"❌ Erro buscando histórico: {e}")
            return []
    
    def get_stats(self):
        """Estatísticas do histórico"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "total_news": data.get('total_news', 0),
                "last_updated": data.get('last_updated', 'Nunca'),
                "recent_added": len(data.get('news_history', []))
            }
        except:
            return {"total_news": 0, "last_updated": "Nunca", "recent_added": 0}


history_manager = HistoryManager()