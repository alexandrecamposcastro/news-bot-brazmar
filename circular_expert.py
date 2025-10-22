import google.generativeai as genai
import os
import json
from datetime import datetime

class BrazmarCircularExpert:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise Exception("❌ GEMINI_API_KEY não configurada")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        self.expert_profile = """
        VOCÊ É ESPECIALISTA EM CIRCULARES DA BRAZMAR MARINE SERVICES

        ⚓ PERFIL BRAZMAR:
        - Apoio marítimo e portuário EXCLUSIVAMENTE NORTE/NORDESTE
        - Portos: Itaqui (MA), Pecém (CE), Suape (PE), São Luís, Fortaleza
        - Clientes: Londres, Xangai, Nova York (executivos internacionais)

        📋 FOCO ABSOLUTO: 
        - Apenas operações nos portos do Norte/Nordeste
        - Apenas impactos operacionais reais
        - Linguagem profissional para executivos

        🎯 PÚBLICO ALVO:
        - Seguradoras em Londres
        - Trading companies em Xangai  
        - Investidores em Nova York
        """

    def generate_circular(self, noticias_relevantes):
        """Gera circular profissional - adaptado para notícias sem link"""
        if not noticias_relevantes:
            return "📭 SEM NOTÍCIAS RELEVANTES HOJE - Nada a reportar para o Norte/Nordeste"

        # Agrupa notícias por tipo
        noticias_gemini = [n for n in noticias_relevantes if n.get('type') == 'gemini_active_search']
        noticias_tradicionais = [n for n in noticias_relevantes if n.get('type') != 'gemini_active_search']
    
        prompt = f"""
        {self.expert_profile}

        📊 RESUMO DAS NOTÍCIAS:
        - Notícias encontradas ativamente: {len(noticias_gemini)}
        - Notícias de fontes tradicionais: {len(noticias_tradicionais)}
        - Total: {len(noticias_relevantes)} notícias relevantes

        NOTÍCIAS RELEVANTES DO DIA (APENAS NORTE/NORDESTE):
        {json.dumps(noticias_relevantes, ensure_ascii=False, indent=2)}

        CRIE UMA CIRCULAR PROFISSIONAL:

        BRAZMAR MARINE SERVICES - CIRCULAR DIÁRIA
        Data: {datetime.now().strftime("%d/%m/%Y")}
        Fontes: {len(noticias_gemini)} buscas ativas + {len(noticias_tradicionais)} fontes tradicionais

        🚨 RESUMO EXECUTIVO:
        [Destaque os 3 pontos MAIS IMPORTANTES do dia]

        📊 IMPACTOS OPERACIONAIS:
        • [Lista de impactos REAIS nas operações da Brazmar]

        🎯 RECOMENDAÇÕES PARA CLIENTES:
        • [Ações práticas para seguradoras/trading companies]

        📰 DESTAQUES POR PORTO/REGIÃO:
        [Resumo organizado por localização geográfica]

        ⚠️  ALERTAS E RISCOS:
        • [Riscos específicos identificados]

        Use linguagem concisa e profissional. Foco em INFORMAÇÃO ACIONÁVEL.
        Destaque especialmente as notícias encontradas via busca ativa.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Erro gerando circular: {e}"