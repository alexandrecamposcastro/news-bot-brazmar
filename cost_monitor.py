import os
import requests
import time
from datetime import datetime

class CostProtection:
    def __init__(self):
        self.railway_token = os.getenv('RAILWAY_TOKEN')
        self.max_monthly_cost = 4.50  # ABAIXO dos $5 free!
        self.shutdown_url = None
    
    def get_current_cost(self):
        """Verifica custo atual via Railway API"""
        try:
            headers = {'Authorization': f'Bearer {self.railway_token}'}
            response = requests.get('https://backboard.railway.app/graphql/v2', 
                                  headers=headers)
            
            # Railway API retorna custo atual
            data = response.json()
            current_cost = data.get('data', {}).get('me', {}).get('currentSpending', 0)
            
            print(f"💰 Custo atual: ${current_cost}")
            return current_cost
            
        except Exception as e:
            print(f"❌ Erro verificando custo: {e}")
            return 0
    
    def emergency_shutdown(self):
        """DESLIGA TUDO se custo passar de $4.50"""
        print("🚨 EMERGÊNCIA: Desligando serviços para evitar cobrança!")
        
        # Para todos os serviços Railway
        if self.shutdown_url:
            requests.delete(self.shutdown_url)
        
        # Mata o processo atual
        os._exit(1)
    
    def start_cost_monitor(self):
        """Inicia monitoramento 24/7"""
        print("🛡️ Iniciando proteção contra cobranças...")
        
        while True:
            current_cost = self.get_current_cost()
            
            if current_cost >= self.max_monthly_cost:
                print(f"🚨 ALERTA: Custo ${current_cost} >= ${self.max_monthly_cost}")
                self.emergency_shutdown()
            
            # Verifica a cada 6 horas
            time.sleep(21600)

# Inicia automaticamente
if __name__ == "__main__":
    protector = CostProtection()
    protector.start_cost_monitor()