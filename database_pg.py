import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

class PostgreSQLDatabase:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.init_database()
    
    def get_connection(self):
        """Cria conexão com PostgreSQL"""
        return psycopg2.connect(self.db_url, sslmode='require')
    
    def init_database(self):
        """Inicializa tabelas no PostgreSQL"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabela de feedback
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    relevant BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de artigos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE,
                    summary TEXT,
                    source TEXT,
                    urgency TEXT,
                    confidence INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de configurações do sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ PostgreSQL inicializado com sucesso")
        except Exception as e:
            print(f"❌ Erro inicializando PostgreSQL: {e}")
    
    def save_feedback(self, title, summary, relevant):
        """Salva feedback no PostgreSQL"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO feedback (title, summary, relevant)
                VALUES (%s, %s, %s)
            ''', (title, summary, relevant))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"💾 Feedback salvo no PostgreSQL: {title[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Erro salvando feedback: {e}")
            return False
    
    def get_feedback_stats(self):
        """Obtém estatísticas do feedback"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM feedback')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM feedback WHERE relevant = TRUE')
            relevantes = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM feedback WHERE relevant = FALSE')
            irrelevantes = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                "total": total,
                "relevantes": relevantes,
                "irrelevantes": irrelevantes
            }
        except Exception as e:
            print(f"❌ Erro obtendo stats: {e}")
            return {"total": 0, "relevantes": 0, "irrelevantes": 0}
    
    def save_article(self, article):
        """Salva artigo no PostgreSQL"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO articles (title, link, summary, source, urgency, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING
            ''', (
                article['title'],
                article['link'],
                article['summary'],
                article['source'],
                article.get('urgencia', 'MEDIA'),
                article.get('confianca', 70)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro salvando artigo: {e}")
            return False
    
    def get_recent_articles(self, limit=50):
        """Obtém artigos recentes do PostgreSQL"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, link, summary, source, urgency, confidence, created_at
                FROM articles 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (limit,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'title': row[0],
                    'link': row[1],
                    'summary': row[2],
                    'source': row[3],
                    'urgencia': row[4],
                    'confianca': row[5],
                    'created_at': row[6].isoformat() if row[6] else None
                })
            
            cursor.close()
            conn.close()
            return articles
        except Exception as e:
            print(f"❌ Erro obtendo artigos: {e}")
            return []

# Instância global
db = PostgreSQLDatabase()