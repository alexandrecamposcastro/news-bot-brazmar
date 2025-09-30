import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

# Configuração simplificada - removendo tradução problemática
from processor import summarize_text

# Keywords em português para filtro inicial
GENERIC_MARITIME_KEYWORDS = [
    "porto", "navio", "marítimo", "shipping", "carga", "terminal", 
    "logística", "offshore", "regulamentação", "marinha", "antaq",
    "brasil", "brasileiro", "portos", "marítima", "cabotagem",
    "transporte", "mercante", "exportação", "importação", "alfândega"
]

from sources import RSS_FEEDS, SCRAPE_SITES

def create_session_with_retries(max_retries=3):
    """Cria sessão com retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def clean_text(text):
    """Limpa e formata texto"""
    if not text:
        return ""
    # Remove múltiplos espaços e quebras de linha
    text = re.sub(r'\s+', ' ', text)
    # Remove caracteres especiais problemáticos
    text = re.sub(r'[^\w\s.,!?;-]', '', text)
    return text.strip()

def get_article_text(url, session):
    """Extrai texto do artigo de forma simplificada"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove elementos indesejados
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Tenta encontrar conteúdo principal
        content_selectors = [
            'article', '.post-content', '.entry-content', 
            '.noticia-conteudo', '.content', '.main-content'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if content_element:
            text = content_element.get_text()
        else:
            text = soup.get_text()
        
        # Limpa o texto
        text = clean_text(text)
        
        if len(text) < 100:
            return "Conteúdo não disponível para resumo."
            
        return text[:2500]  # Limita tamanho
        
    except Exception as e:
        print(f"[TEXT ERROR] {url}: {e}")
        return "Erro ao extrair conteúdo."

def fetch_rss():
    """Coleta notícias de feeds RSS"""
    articles = []
    session = create_session_with_retries()
    
    for url in RSS_FEEDS:
        try:
            print(f"[RSS] Processando {url}")
            feed = feedparser.parse(url)
            
            if hasattr(feed, 'entries'):
                for entry in feed.entries[:15]:  # Limita a 15 por feed
                    title = entry.get('title', 'Sem título')
                    link = entry.get('link', '')
                    summary = entry.get('summary', entry.get('description', ''))
                    
                    # Filtro por keywords em português
                    combined_text = (title + " " + summary).lower()
                    
                    if any(keyword in combined_text for keyword in GENERIC_MARITIME_KEYWORDS):
                        # Limpa e formata
                        title = clean_text(title)
                        summary = clean_text(summary)
                        
                        # Resumiza se necessário
                        if len(summary) > 200:
                            summary = summarize_text(summary, sentences_count=2)
                        
                        articles.append({
                            'title': title,
                            'link': link,
                            'summary': summary[:500],
                            'source': urlparse(url).netloc,
                            'type': 'rss'
                        })
                        
                print(f"[RSS] ✅ {len(feed.entries)} entradas processadas de {url}")
                
        except Exception as e:
            print(f"[RSS ERROR] {url}: {e}")
            continue
    
    print(f"✅ Total RSS coletado: {len(articles)}")
    return articles

def fetch_scrape():
    """Coleta notícias via scraping direto"""
    articles = []
    session = create_session_with_retries()
    
    for site in SCRAPE_SITES:
        try:
            print(f"[SCRAPE] Processando {site}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = session.get(site, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Seletores para diferentes sites
            if "portosenavios" in site:
                links = soup.select('.entry-title a, h2 a, .post-title a')
            elif "antaq" in site or "gov.br" in site:
                links = soup.select('a[href*="noticias"], .noticia-titulo a, h3 a')
            else:
                links = soup.select('a[href*="noticia"], .news-item a, h2 a')
            
            for link in links[:10]:  # Limita a 10 por site
                try:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    if not href or not title:
                        continue
                    
                    # Constrói URL completa se for relativa
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = urlparse(site).scheme + "://" + urlparse(site).netloc + href
                        else:
                            href = site.rstrip('/') + '/' + href.lstrip('/')
                    
                    # Verifica relevância
                    if any(keyword in title.lower() for keyword in GENERIC_MARITIME_KEYWORDS):
                        # Extrai conteúdo
                        content = get_article_text(href, session)
                        
                        # Cria resumo
                        if len(content) > 100 and content != "Conteúdo não disponível para resumo.":
                            summary = summarize_text(content, sentences_count=2)
                        else:
                            summary = content
                        
                        articles.append({
                            'title': clean_text(title),
                            'link': href,
                            'summary': summary[:500],
                            'source': urlparse(site).netloc,
                            'type': 'scrape'
                        })
                        
                        time.sleep(1)  # Delay entre requisições
                        
                except Exception as e:
                    print(f"[SCRAPE ITEM ERROR] {href}: {e}")
                    continue
                    
            print(f"[SCRAPE] ✅ {len(links)} links processados de {site}")
            
        except Exception as e:
            print(f"[SCRAPE ERROR] {site}: {e}")
            continue
    
    print(f"✅ Total SCRAPE coletado: {len(articles)}")
    return articles