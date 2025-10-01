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
    # Seguros e riscos marítimos
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
        
        # Tenta encontrar conteúdo principal - MAIS SELETORES
        content_selectors = [
            'article', '.post-content', '.entry-content', 
            '.noticia-conteudo', '.content', '.main-content',
            '.news-content', '.materia-conteudo', '.texto-noticia',
            '.conteudo-noticia', '.news-body', '.article-body'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_elements = soup.select(selector)
            if content_elements:
                content_element = content_elements[0]
                break
        
        if content_element:
            text = content_element.get_text()
        else:
            # Fallback: pega todo o texto mas tenta limpar
            main_selectors = ['main', '#content', '.content-main']
            for selector in main_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    text = main_element.get_text()
                    break
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
                            summary = summarize_text(summary, sentences_count=1)
                        
                        articles.append({
                            'title': title,
                            'link': link,
                            'summary': summary[:400],
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
    """Coleta notícias via scraping direto com seletores específicos"""
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
            
            # SELETORES ESPECÍFICOS POR SITE
            if "portosenavios" in site:
                links = soup.select('.entry-title a, h2 a, .post-title a, .news-item a')
            elif "gov.br" in site:
                links = soup.select('a[href*="noticias"], .noticia-titulo a, h3 a, .titulo-noticia a, .list-item a')
            elif "marinha.mil.br" in site:
                links = soup.select('a[href*="noticia"], .news-item a, h2 a, .item-title a, .titulo a')
            elif "agenciabrasil" in site:
                links = soup.select('a[href*="/noticia/"], .news-item a, h2 a, .title a')
            elif "migalhas" in site:
                links = soup.select('a[href*="/migalhas-maritimas/"], .title a, h2 a, h3 a')
            else:
                links = soup.select('a[href*="noticia"], .news-item a, h2 a, .title a')
            
            print(f"[SCRAPE] Encontrados {len(links)} links em {site}")
            
            for link in links[:15]:  # Limita a 15 por site
                try:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    if not href or not title or len(title) < 10:
                        continue
                    
                    # Constrói URL completa se for relativa
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = urlparse(site).scheme + "://" + urlparse(site).netloc + href
                        else:
                            href = site.rstrip('/') + '/' + href.lstrip('/')
                    
                    # Verifica relevância com keywords mais amplas
                    title_lower = title.lower()
                    if any(keyword in title_lower for keyword in GENERIC_MARITIME_KEYWORDS):
                        # Extrai conteúdo
                        content = get_article_text(href, session)
                        
                        # Cria resumo
                        if len(content) > 100 and content != "Conteúdo não disponível para resumo.":
                            summary = summarize_text(content, sentences_count=1)  # Apenas 1 frase
                        else:
                            summary = content
                        
                        articles.append({
                            'title': clean_text(title),
                            'link': href,
                            'summary': summary[:400],  # Limita mais
                            'source': urlparse(site).netloc,
                            'type': 'scrape'
                        })
                        
                        time.sleep(0.5)  # Delay menor entre requisições
                        
                except Exception as e:
                    print(f"[SCRAPE ITEM ERROR] {href}: {e}")
                    continue
                    
            print(f"[SCRAPE] ✅ {len(articles)} artigos coletados de {site}")
            
        except Exception as e:
            print(f"[SCRAPE ERROR] {site}: {e}")
            continue
    
    print(f"✅ Total SCRAPE coletado: {len(articles)}")
    return articles