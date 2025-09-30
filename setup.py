import nltk
import os

print("📥 Configurando NLTK...")
try:
    nltk.download('punkt')
    nltk.download('punkt_tab')
    print("✅ NLTK configurado com sucesso!")
except Exception as e:
    print(f"⚠️ Erro NLTK: {e}")

print("📁 Criando diretórios...")
os.makedirs("database", exist_ok=True)
os.makedirs("templates", exist_ok=True)
print("✅ Diretórios criados!")