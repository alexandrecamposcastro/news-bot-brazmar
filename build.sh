#!/bin/bash
echo "🚀 Iniciando build do Brazmar News Bot..."
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
echo "✅ Build concluído com sucesso!"