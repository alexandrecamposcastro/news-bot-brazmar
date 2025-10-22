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
        """Gera circular profissional"""
        if not noticias_relevantes:
            return "📭 SEM NOTÍCIAS RELEVANTES HOJE - Nada a reportar para o Norte/Nordeste"

        prompt = f"""
        {self.expert_profile}

        NOTÍCIAS RELEVANTES DO DIA (APENAS NORTE/NORDESTE):
        {json.dumps(noticias_relevantes, ensure_ascii=False, indent=2)}

        CRIE UMA CIRCULAR PROFISSIONAL:

        BRAZMAR MARINE SERVICES - CIRCULAR DIÁRIA
        Data: {datetime.now().strftime("%d/%m/%Y")}

        🚨 RESUMO EXECUTIVO (1-2 frases):
        [Destaque o MAIS IMPORTANTE]

        📊 IMPACTOS OPERACIONAIS:
        • [Lista de impactos REAIS nas operações]

        🎯 RECOMENDAÇÕES:
        • [Ações práticas para clientes]

        📰 SITUAÇÃO POR PORTO:
        [Resumo por porto/região]

        ⚠️  ALERTAS:
        • [Riscos específicos identificados]

        Use linguagem concisa e profissional. Foco em INFORMAÇÃO ACIONÁVEL.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Erro gerando circular: {e}"

# ✅✅✅ CORRIGIDO: Instância com nome CORRETO
circular_expert = BrazmarCircularExpert()