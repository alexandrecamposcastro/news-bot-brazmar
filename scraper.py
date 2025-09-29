import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from deep_translator import GoogleTranslator
translator = GoogleTranslator(source='pt', target='en')  # Config global para PT → EN

# Resumização (importa de processor)
from processor import summarize_text

# Keywords genéricas (local)
GENERIC_MARITIME_KEYWORDS = ["porto", "navio", "marítimo", "shipping", "carga", "terminal", "logística", "offshore", "regulamentação", "marinha", "antaq"]

from sources import RSS_FEEDS, SCRAPE_SITES

def create_session_with_retries(max_retries=3):
    session = requests.Session()
    retry_strategy = Retry(total=max_retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504, 10054])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_selenium_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_with_selenium(url):
    driver = None
    try:
        print(f"[SELENIUM] Extraindo {url}...")
        driver = get_selenium_driver()
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        full_text = driver.find_element(By.TAG_NAME, "body").text
        full_text = ' '.join(full_text.split())[:3000]
        return full_text
    except Exception as e:
        print(f"[SELENIUM ERROR] {url}: {e}")
        return "Texto não disponível."
    finally:
        if driver:
            driver.quit()

def translate_to_english(text):
    """Traduz texto para inglês usando deep-translator (Google)."""
    if not text or len(text) < 10:
        return text
    try:
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"[TRANSLATE ERROR]: {e} - Mantendo texto original.")
        return text  # Fallback para PT se falhar

def get_article_text(url, session, use_selenium=False):
    if use_selenium:
        full_text = extract_with_selenium(url)
    else:
        headers = {'User -Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        try:
            response = session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            full_text = soup.get_text().strip()
            if len(full_text) < 50:
                return "Short summary available in the link."
            lines = (line.strip() for line in full_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            full_text = ' '.join(chunk for chunk in chunks if chunk)
            full_text = full_text[:2000]
        except Exception as e:
            print(f"[TEXT ERROR] {url}: {e}")
            full_text = "Summary not available."
    return full_text

def fetch_rss():
    articles = []
    session = create_session_with_retries()
    for url in RSS_FEEDS:
        try:
            print(f"[RSS] Processando {url}...")
            feed = feedparser.parse(url)
            added = 0
            for entry in feed.entries[:20]:
                title_lower = entry.title.lower()
                if any(kw in title_lower for kw in GENERIC_MARITIME_KEYWORDS):
                    summary_pt = entry.get('summary', '') or entry.get('description', '') or f"Leia mais sobre {entry.title}."
                    # Traduz título e summary
                    title_en = translate_to_english(entry.title)
                    summary_en = translate_to_english(summary_pt)
                    # Resumiza em EN se longo
                    if len(summary_en) > 200:
                        summary_en = summarize_text(summary_en, sentences_count=2)
                    # Pós-processa para menos ambiguidade: Adiciona contexto chave se vago
                    if len(summary_en.split()) < 20:  # Se muito curto/ambíguo
                        summary_en += f" Related to {title_en} in Brazilian ports."
                    articles.append({
                        'title': title_en,  # Título em EN
                        'link': entry.link,
                        'summary': summary_en[:300],
                        'source': urlparse(url).netloc
                    })
                    added += 1
            print(f"[RSS] {len(feed.entries) if 'entries' in feed else 0} itens, {added} coletados em {url}.")
        except Exception as e:
            print(f"[RSS ERROR] {url}: {e}")
    print(f"✅ Total RSS: {len(articles)}")
    return articles

def fetch_scrape():
    articles = []
    session = create_session_with_retries()
    for site in SCRAPE_SITES:
        try:
            print(f"[SCRAPE] Processando {site}...")
            response = session.get(site, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            if "portosenavios" in site:
                news_items = soup.select('.entry-title a, .post a, h2 a')
            elif "gov.br" in site:
                news_items = soup.select('a[href*="/noticias/"], h3 a, .noticia a')
            else:
                news_items = soup.select('.post a, .news a, h2 a')
            
            added = 0
            for item in news_items[:30]:
                href = item.get('href', '')
                if not href or 'javascript:' in href: continue
                if not href.startswith('http'):
                    href = site.rstrip('/') + '/' + href.lstrip('/')
                title_pt = item.get_text(strip=True)
                if not title_pt: continue
                title_lower = title_pt.lower()
                if any(kw in title_lower for kw in GENERIC_MARITIME_KEYWORDS):
                    use_selenium = "gov.br" in href
                    full_text_pt = get_article_text(href, session, use_selenium=use_selenium)
                    
                    # Traduz full_text para EN
                    full_text_en = translate_to_english(full_text_pt)
                    # Resumiza em EN
                    summary_en = summarize_text(full_text_en, sentences_count=3) if len(full_text_en) > 100 else full_text_en
                    # Pós-processa: Se ambíguo (curto/genérico), adiciona termos chave traduzidos
                    key_terms = ["lease", "terminal", "safety", "port", "regulation", "risk"]  # EN equivalents
                    if len(summary_en.split()) < 25 or "agency" in summary_en.lower() and "details" not in summary_en.lower():
                        summary_en += f" Key aspects: {', '.join([t for t in key_terms if any(term in full_text_en.lower() for term in [t.lower(), translate_to_english(t).lower()])][:3])}."
                    summary_en = summary_en[:400]
                    
                    # Traduz título
                    title_en = translate_to_english(title_pt)
                    
                    articles.append({
                        'title': title_en,
                        'link': href,
                        'summary': summary_en,
                        'source': urlparse(site).netloc
                    })
                    added += 1
                    time.sleep(3 if use_selenium else 1)
            print(f"[SCRAPE] {len(news_items)} itens, {added} coletados em {site}.")
        except Exception as e:
            print(f"[SCRAPE ERROR] {site}: {e}")
    print(f"✅ Total SCRAPE: {len(articles)}")
    return articles