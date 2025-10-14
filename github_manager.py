import requests
import base64
import os
from datetime import datetime

class GitHubManager:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo = os.getenv('GITHUB_REPO')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_csv_from_github(self):
        """Pega o CSV do GitHub"""
        try:
            url = f'https://api.github.com/repos/{self.repo}/contents/feedback.csv'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                content = response.json()['content']
                # Decodifica base64
                csv_content = base64.b64decode(content).decode('utf-8')
                return csv_content
            else:
                # Arquivo não existe, cria um novo
                return "title,summary,relevant,timestamp\n"
                
        except Exception as e:
            print(f"❌ Erro pegando CSV do GitHub: {e}")
            return "title,summary,relevant,timestamp\n"
    
    def save_feedback_to_github(self, title, summary, relevant):
        """Salva feedback no GitHub"""
        try:
            # Pega conteúdo atual
            current_content = self.get_csv_from_github()
            
            # Adiciona nova linha
            new_line = f'"{title}","{summary}",{relevant},{datetime.now().isoformat()}\n'
            new_content = current_content + new_line
            
            # Prepara dados para upload
            url = f'https://api.github.com/repos/{self.repo}/contents/feedback.csv'
            
            # Pega SHA do arquivo atual (se existir)
            sha = None
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                sha = response.json()['sha']
            
            # Faz upload
            data = {
                'message': f'Add feedback: {title[:30]}...',
                'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
                'branch': 'main'
            }
            
            if sha:
                data['sha'] = sha
            
            response = requests.put(url, headers=self.headers, json=data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Feedback salvo no GitHub: {title[:30]}...")
                return True
            else:
                print(f"❌ Erro salvando no GitHub: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro salvando feedback no GitHub: {e}")
            return False
    
    def download_csv_for_ml(self):
        """Baixa CSV do GitHub para o ML usar localmente"""
        try:
            csv_content = self.get_csv_from_github()
            
            # Salva localmente para o ML usar
            with open('feedback.csv', 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            print("✅ CSV baixado do GitHub para ML")
            return True
            
        except Exception as e:
            print(f"❌ Erro baixando CSV: {e}")
            return False

# Instância global
github_manager = GitHubManager()