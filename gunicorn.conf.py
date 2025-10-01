import multiprocessing

# Configurações específicas para Render.com
bind = "0.0.0.0:10000"
workers = 1
worker_class = "sync"
timeout = 300  # Aumenta timeout para 5 minutos
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = False  # IMPORTANTE: False para evitar conflitos