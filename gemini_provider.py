import os
import google.generativeai as genai
import json
import re
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup

class GeminiProvider:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise Exception("❌ GEMINI_API_KEY não configurada")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.last_request_time = 0
        self.min_interval = 7
        self.request_count = 0
        self.reset_time = time.time()
        
        print("✅ Gemini Provider configurado - 8 RPM máximo")

    def _rate_limit(self):
        """Garante que não estoura os limites"""
        now = time.time()
        
        if now - self.reset_time >= 60:
            self.request_count = 0
            self.reset_time = now
        
        if self.request_count >= 8:
            sleep_time = 60 - (now - self.reset_time)
            if sleep_time > 0:
                print(f"⏳ Rate limit: aguardando {sleep_time:.1f}s")
                time.sleep(sleep_time)
            self.request_count = 0
            self.reset_time = time.time()
        
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_request_time = time.time()
        self.request_count += 1

    def analyze_article(self, title, summary):
        """Analisa com critérios MUITO rigorosos - APENAS Norte/Nordeste"""
        self._rate_limit()
        
        prompt = f"""
        VOCÊ É FILTRO DA BRAZMAR MARINE SERVICES - APENAS NORTE/NORDESTE

        REGRA ABSOLUTA: SÓ NOTÍCIAS DO NORTE/NORDESTE BRASILEIRO

        ✅ ACEITAR SOMENTE SE MENCIONAR EXPLICITAMENTE:
        - Maranhão, Ceará, Piauí, Bahia, Pernambuco, Alagoas, Sergipe, Paraíba, Rio Grande do Norte, Amapá, Pará, Amazonas, Rondônia, Acre, Roraima, Tocantins
        - Porto de Itaqui, Pecém, Suape, São Luís, Fortaleza, Belém, Macapá, Manaus, Recife, Salvador, Natal
        - Região Norte, Região Nordeste

        ❌ REJEITAR TUDO QUE FOR:
        - Santos, Rio de Janeiro, São Paulo, Sul, Sudeste
        - Qualquer porto/região fora do Norte/Nordeste
        - Notícias genéricas sem localização específica

        TÍTULO: {title}
        RESUMO: {summary}

        Esta notícia é ESPECIFICAMENTE sobre a REGIÃO NORTE/NORDESTE brasileira?

        Responda APENAS com JSON:
        {{
            "relevante": true/false,
            "confianca": 0-100,
            "motivo": "explicação CURTA",
            "urgencia": "BAIXA/MEDIA/ALTA"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"❌ Erro Gemini: {e}")
            return self._get_fallback_response()

    def buscar_noticias_ativas(self):
        """🎯 NOVO: BUSCA ATIVA DE NOTÍCIAS COM GEMINI"""
        self._rate_limit()
        
        prompt = """
        VOCÊ É CAÇADOR DE NOTÍCIAS DA BRAZMAR MARINE SERVICES

        SUA MISSÃO: ENCONTRAR NOTÍCIAS ESPECÍFICAS para a Brazmar Marine Services

        🎯 FOCO ABSOLUTO: NORTE E NORDESTE DO BRASIL

        🔍 BUSQUE NOTÍCIAS SOBRE:
        - Operações nos portos: Itaqui (MA), Pecém (CE), Suape (PE), São Luís, Fortaleza, Belém, Macapá
        - Apoio marítimo a plataformas de petróleo no Norte/Nordeste
        - Movimentação portuária na região Norte/Nordeste
        - Incidentes/acidentes marítimos nos portos da Brazmar
        - Novas regulamentações da ANTAQ/Marinha para a região
        - Clima/condições operacionais nos portos do Norte/Nordeste

        📋 FORMATO DA RESPOSTA:
        Forneça uma LISTA de notícias RECENTES e RELEVANTES com:
        - Título real da notícia
        - Fonte/veículo onde pode ser encontrada
        - Breve descrição do conteúdo
        - Data aproximada da notícia

        Exemplo:
        1. "Porto de Itaqui bate recorde de movimentação de grãos" - Jornal O Estado do MA - Movimentação de soja no porto aumentou 15% - Outubro 2025
        2. "Marinha autoriza novas operações offshore no Ceará" - Site da Marinha - Liberada perfuração em nova área da Bacia do Ceará - Outubro 2025

        Liste pelo menos 8-10 notícias RECENTES e RELEVANTES.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_busca_ativa(response.text)
        except Exception as e:
            print(f"❌ Erro na busca ativa: {e}")
            return []

    def _parse_busca_ativa(self, response_text):
        """Converte a busca ativa em notícias estruturadas"""
        noticias = []
        linhas = response_text.split('\n')
        
        for linha in linhas:
            linha = linha.strip()
            # Procura por padrões de notícias (números, títulos, fontes)
            if re.match(r'^\d+[\.\)]', linha) and any(keyword in linha.lower() for keyword in ['porto', 'marinha', 'operacao', 'navio', 'petroleo']):
                # Extrai informações básicas
                partes = re.split(r' - ', linha)
                if len(partes) >= 3:
                    titulo = partes[0].replace('"', '').strip()
                    # Remove o número do início se existir
                    titulo = re.sub(r'^\d+[\.\)]\s*', '', titulo)
                    
                    fonte = partes[1].strip()
                    descricao = partes[2].strip()
                    
                    noticias.append({
                        'title': titulo,
                        'source': fonte,
                        'summary': descricao,
                        'type': 'gemini_active_search',
                        'search_timestamp': datetime.now().isoformat()
                    })
        
        return noticias[:10]  # Limita a 10 notícias

    def _parse_response(self, response_text):
        """Parse da resposta do Gemini"""
        try:
            cleaned = re.sub(r'```json|```', '', response_text).strip()
            json_match = re.search(r'\{[^}]+\}', cleaned, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                if 'relevante' in result:
                    return result
        except Exception as e:
            print(f"❌ Erro parse: {e}")
        
        return self._get_fallback_response()

    def _get_fallback_response(self):
        """Fallback SUPER RESTRITIVO"""
        return {
            "relevante": False,
            "confianca": 10,
            "motivo": "Análise falhou - conservador",
            "urgencia": "BAIXA"
        }

# Instância global
gemini_provider = GeminiProvider()