import re

def summarize_text(text, sentences_count=2):
    """Resumo simples em português sem dependências externas"""
    if not text or len(text) < 50:
        return text[:300]
    
    try:
        # Divide o texto em frases usando pontuação portuguesa
        sentences = re.split(r'[.!?]+', text)
        
        # Limpa e filtra frases
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Frases com mais de 10 caracteres
                clean_sentences.append(sentence)
        
        # Se não encontrou frases boas, usa abordagem diferente
        if not clean_sentences:
            words = text.split()
            if len(words) > 30:
                return " ".join(words[:30]) + "..."
            else:
                return text
        
        # Pega as primeiras frases que fazem sentido
        if len(clean_sentences) <= sentences_count:
            summary = " ".join(clean_sentences)
        else:
            summary = " ".join(clean_sentences[:sentences_count])
        
        # Garante que não está muito curto
        if len(summary) < 50:
            words = text.split()
            summary = " ".join(words[:30]) + "..."
        
        return summary[:500]  # Limita o tamanho
        
    except Exception as e:
        print(f"[SUMMARY ERROR] {e}")
        # Fallback final - primeiras 300 caracteres
        return text[:300]