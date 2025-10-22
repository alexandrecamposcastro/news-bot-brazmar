import os
import google.generativeai as genai
import json
import re
from datetime import datetime
import time

class GeminiProvider:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise Exception("❌ GEMINI_API_KEY não configurada")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')  # Seu modelo principal
        self.last_request_time = 0
        self.min_interval = 7  # 7 segundos = ~8 RPM (abaixo do seu limite)
        self.request_count = 0
        self.reset_time = time.time()
        
        print("✅ Gemini Provider configurado - 8 RPM máximo")

    def _rate_limit(self):
        """Garante que não estoura os limites"""
        now = time.time()
        
        # Reset a cada minuto
        if now - self.reset_time >= 60:
            self.request_count = 0
            self.reset_time = now
        
        # Limite de 8 requests por minuto
        if self.request_count >= 8:
            sleep_time = 60 - (now - self.reset_time)
            if sleep_time > 0:
                print(f"⏳ Rate limit: aguardando {sleep_time:.1f}s")
                time.sleep(sleep_time)
            self.request_count = 0
            self.reset_time = time.time()
        
        # Intervalo entre requests
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
            "relevante": False,  # ❌ NÃO DEIXA PASSAR NADA
            "confianca": 10,
            "motivo": "Análise falhou - conservador",
            "urgencia": "BAIXA"
        }

# Instância global
gemini_provider = GeminiProvider()