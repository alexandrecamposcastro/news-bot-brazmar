import os
import sqlite3
import json
from datetime import datetime

class HybridDatabase:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.use_postgres = False
        self.init_database()
    
    def init_database(self):
        """Inicializa banco - PostgreSQL com fallback para SQLite"""
        print("🔄 Inicializando banco de dados...")
        
        # Tenta PostgreSQL primeiro
        if self.db_url:
            try:
                import psycopg2
                conn = psycopg2.connect(self.db_url, sslmode='require')
                cursor = conn.cursor()
                
                # Cria tabelas PostgreSQL
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        summary TEXT,
                        relevant BOOLEAN NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
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
                
                conn.commit()
                cursor.close()
                conn.close()
                
                self.use_postgres = True
                print("✅ PostgreSQL configurado com sucesso!")
                return
                
            except Exception as e:
                print(f"❌ PostgreSQL falhou, usando SQLite: {e}")
        
        # Fallback para SQLite
        try:
            os.makedirs("database", exist_ok=True)
            conn = sqlite3.connect("database/brazmar.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    summary TEXT,
                    relevant BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE,
                    summary TEXT,
                    source TEXT,
                    urgency TEXT,
                    confidence INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ SQLite configurado como fallback")
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO: Nenhum banco funcionou: {e}")
    
    def save_feedback(self, title, summary, relevant):
        """Salva feedback de forma robusta"""
        try:
            if self.use_postgres:
                return self._save_postgres(title, summary, relevant)
            else:
                return self._save_sqlite(title, summary, relevant)
        except Exception as e:
            print(f"❌ Erro geral salvando feedback: {e}")
            return False
    
    def _save_postgres(self, title, summary, relevant):
        """Salva no PostgreSQL"""
        import psycopg2
        conn = psycopg2.connect(self.db_url, sslmode='require')
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
    
    def _save_sqlite(self, title, summary, relevant):
        """Salva no SQLite"""
        conn = sqlite3.connect("database/brazmar.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback (title, summary, relevant)
            VALUES (?, ?, ?)
        ''', (title, summary, relevant))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"💾 Feedback salvo no SQLite: {title[:50]}...")
        return True
    
    def get_feedback_stats(self):
        """Obtém estatísticas do feedback"""
        try:
            if self.use_postgres:
                import psycopg2
                conn = psycopg2.connect(self.db_url, sslmode='require')
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM feedback')
                total = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM feedback WHERE relevant = TRUE')
                relevantes = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM feedback WHERE relevant = FALSE')
                irrelevantes = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
            else:
                conn = sqlite3.connect("database/brazmar.db")
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM feedback')
                total = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM feedback WHERE relevant = 1')
                relevantes = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM feedback WHERE relevant = 0')
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
        """Salva artigo no banco"""
        try:
            if self.use_postgres:
                import psycopg2
                conn = psycopg2.connect(self.db_url, sslmode='require')
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
            else:
                conn = sqlite3.connect("database/brazmar.db")
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO articles (title, link, summary, source, urgency, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
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
        """Obtém artigos recentes do banco"""
        try:
            if self.use_postgres:
                import psycopg2
                conn = psycopg2.connect(self.db_url, sslmode='require')
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
            else:
                conn = sqlite3.connect("database/brazmar.db")
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT title, link, summary, source, urgency, confidence, created_at
                    FROM articles 
                    ORDER BY created_at DESC 
                    LIMIT ?
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
                        'created_at': row[6]
                    })
                
                cursor.close()
                conn.close()
            
            return articles
        except Exception as e:
            print(f"❌ Erro obtendo artigos: {e}")
            return []

# Instância global
db = HybridDatabase()