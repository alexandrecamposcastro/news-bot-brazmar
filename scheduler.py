import schedule
import time
import threading
from datetime import datetime

class BrazmarScheduler:
    def __init__(self):
        self.processor = None
        self.running = True
        
    def agendar_tarefas(self):
        """Agenda todas as tarefas automáticas"""
        
        # 🕘 09:00 - Análise completa do dia
        schedule.every().day.at("09:00").do(self.tarefa_analise_completa)
        
        # 🕛 12:00 - Atualização do meio-dia
        schedule.every().day.at("12:00").do(self.tarefa_atualizacao_rapida)
        
        # 🕔 17:00 - Resumo executivo
        schedule.every().day.at("17:00").do(self.tarefa_resumo_executivo)
        
        print("⏰ AGENDADOR BRAZMAR CONFIGURADO:")
        print("   🕘 09:00 - Análise completa (início do dia)")
        print("   🕛 12:00 - Atualização rápida (meio-dia)")
        print("   🕔 17:00 - Resumo executivo (fim do dia)")
    
    def tarefa_analise_completa(self):
        """Tarefa das 09:00 - Análise completa"""
        print(f"\n🎯 EXECUTANDO ANÁLISE COMPLETA - {datetime.now()}")
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            artigos = processor.executar_coleta_completa()
            print(f"✅ Análise completa concluída: {len(artigos)} notícias")
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
    
    def tarefa_atualizacao_rapida(self):
        """Tarefas rápidas de atualização"""
        print(f"\n⚡ ATUALIZAÇÃO RÁPIDA - {datetime.now()}")
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            artigos = processor.executar_coleta_completa()
            print(f"✅ Atualização rápida concluída: {len(artigos)} notícias")
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
    
    def tarefa_resumo_executivo(self):
        """Tarefa das 17:00 - Resumo do dia"""
        print(f"\n📊 RESUMO EXECUTIVO - {datetime.now()}")
        try:
            from news_processor import NewsProcessorCompleto
            processor = NewsProcessorCompleto()
            artigos = processor.executar_coleta_completa()
            
            # Gera relatório resumido
            altas = len([a for a in artigos if a.get('urgencia') == 'ALTA'])
            print(f"📈 RESUMO: {len(artigos)} notícias totais, {altas} de alta urgência")
            
        except Exception as e:
            print(f"❌ Erro no resumo: {e}")
    
    def iniciar(self):
        """Inicia o agendador em thread separada"""
        self.agendar_tarefas()
        
        def rodar_agendador():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
        
        thread = threading.Thread(target=rodar_agendador, daemon=True)
        thread.start()
        print("🚀 Agendador iniciado em background")
    
    def parar(self):
        """Para o agendador"""
        self.running = False
        print("🛑 Agendador parado")

# Instância global para importação
scheduler = BrazmarScheduler()

# Opcional: Execução direta para testes
if __name__ == '__main__':
    print("🔧 Executando scheduler em modo standalone...")
    scheduler.iniciar()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.parar()