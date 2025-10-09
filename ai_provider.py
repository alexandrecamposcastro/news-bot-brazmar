import os
import random
import re
import json
from datetime import datetime

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import together
    TOGETHER_AVAILABLE = True
except ImportError:
    TOGETHER_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class MultiAIProvider:
    def __init__(self):
        self.setup_providers()
        self.current_provider = None
        print(f"✅ Sistema Multi-IA inicializado com {len(self.providers)} provedores")
        
    def setup_providers(self):
        """Configura todos os provedores de IA"""
        self.providers = {}
        
        # Groq (PRINCIPAL)
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and GROQ_AVAILABLE:
            try:
                self.providers['groq'] = {
                    'client': Groq(api_key=groq_key),
                    'models': ['llama3-70b-8192', 'mixtral-8x7b-32768'],
                    'type': 'groq'
                }
                print("  ✅ Groq configurado")
            except Exception as e:
                print(f"  ❌ Groq falhou: {e}")
        
        # Together AI
        together_key = os.getenv('TOGETHER_API_KEY') 
        if together_key and TOGETHER_AVAILABLE:
            try:
                together.api_key = together_key
                self.providers['together'] = {
                    'client': together,
                    'models': ['meta-llama/Llama-3-70b-chat-hf', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
                    'type': 'together'
                }
                print("  ✅ Together AI configurado")
            except Exception as e:
                print(f"  ❌ Together AI falhou: {e}")
        
        # OpenAI (Azure)
        openai_key = os.getenv('AZURE_OPENAI_KEY')
        if openai_key and OPENAI_AVAILABLE:
            try:
                azure_endpoint = os.getenv('AZURE_ENDPOINT')
                if azure_endpoint:
                    self.providers['azure'] = {
                        'client': openai.AzureOpenAI(
                            api_key=openai_key,
                            api_version="2023-12-01-preview",
                            azure_endpoint=azure_endpoint
                        ),
                        'models': ['gpt-4'],
                        'type': 'azure'
                    }
                    print("  ✅ Azure OpenAI configurado")
            except Exception as e:
                print(f"  ❌ Azure OpenAI falhou: {e}")
    
    def get_available_provider(self):
        """Retorna um provedor disponível"""
        if not self.providers:
            return None
            
        # Tenta o último provedor usado primeiro
        if self.current_provider and self.current_provider in self.providers:
            return self.current_provider
        
        # Escolhe randomicamente entre os disponíveis
        available = list(self.providers.keys())
        return random.choice(available) if available else None
    
    def analyze_article(self, title, summary):
        """Analisa artigo usando qualquer IA disponível"""
        provider_name = self.get_available_provider()
        
        if not provider_name:
            print("❌ Nenhum provedor de IA disponível - usando fallback")
            return self.get_fallback_response()
        
        try:
            provider = self.providers[provider_name]
            self.current_provider = provider_name
            
            prompt = f"""
            ANALISAR para BRAZMAR MARINE SERVICES (seguros marítimos, consultoria portuária no Brasil):

            TÍTULO: {title}
            RESUMO: {summary}

            CRITÉRIOS ESTRITOS - A notícia deve ser sobre:
            ✅ Seguros marítimos, sinistros navais, avarias
            ✅ Portos brasileiros (Itaqui, Pecém, Suape, Santos, etc.)
            ✅ ANTAQ, Marinha do Brasil, regulamentação portuária
            ✅ Acidentes/incidentes em portos ou navios
            ✅ Operações de cabotagem, navegação interior
            ✅ Região Norte/Nordeste do Brasil

            ❌ REJEITAR se for sobre:
            ❌ Turismo, cruzeiros, pesca esportiva
            ❌ Notícias internacionais
            ❌ Entretenimento, cultura, eventos
            ❌ Assuntos gerais sem ligação direta com operações marítimas

            Esta notícia é RELEVANTE para seguros marítimos ou operações portuárias da BRAZMAR?

            Responda APENAS com JSON:
            {{
                "relevante": true/false,
                "confianca": 0-100,
                "motivo": "explicação específica",
                "urgencia": "BAIXA/MEDIA/ALTA"
            }}
            """
            
            print(f"  🤖 Usando {provider_name.upper()} para análise...")
            
            if provider['type'] == 'groq':
                return self._call_groq(provider, prompt)
            elif provider['type'] == 'together':
                return self._call_together(provider, prompt)
            elif provider['type'] == 'azure':
                return self._call_azure(provider, prompt)
                
        except Exception as e:
            print(f"❌ Erro com {provider_name}: {e}")
            # Remove provedor problemático e tenta outro
            if provider_name in self.providers:
                del self.providers[provider_name]
                print(f"  🔄 Removido {provider_name} - tentando próximo provedor")
            return self.analyze_article(title, summary)  # Recursão com próximo provedor
    
    def _call_groq(self, provider, prompt):
        """Chama API Groq"""
        response = provider['client'].chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=random.choice(provider['models']),
            temperature=0.1,
            max_tokens=500
        )
        return self.parse_response(response.choices[0].message.content)
    
    def _call_together(self, provider, prompt):
        """Chama API Together"""
        response = provider['client'].Complete.create(
            prompt=prompt,
            model=random.choice(provider['models']),
            max_tokens=500,
            temperature=0.1,
            stop=["```"]
        )
        return self.parse_response(response['output']['choices'][0]['text'])
    
    def _call_azure(self, provider, prompt):
        """Chama Azure OpenAI"""
        response = provider['client'].chat.completions.create(
            model=random.choice(provider['models']),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        return self.parse_response(response.choices[0].message.content)
    
    def parse_response(self, response_text):
        """Parse da resposta da IA"""
        try:
            cleaned = re.sub(r'```json|```', '', response_text).strip()
            json_match = re.search(r'\{[^}]*\}', cleaned, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Valida campos obrigatórios
                if 'relevante' in result and 'confianca' in result:
                    return result
        except Exception as e:
            print(f"❌ Erro parse IA: {e}")
        
        return self.get_fallback_response()
    
    def get_fallback_response(self):
        """Resposta fallback se todas as IAs falharem"""
        return {
            "relevante": True,  # No fallback, deixa passar
            "confianca": 50,
            "motivo": "Análise automática - sistema de fallback",
            "urgencia": "MEDIA"
        }

# Instância global
ai_provider = MultiAIProvider()