from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import re

def summarize_text(text, sentences_count=2):
    """SEU função original de resumo"""
    if not text or len(text) < 50:
        return text[:300]
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("portuguese"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(sentence) for sentence in summary)
    except Exception as e:
        print(f"[SUMY ERROR]: {e}")
        sentences = re.split(r'[.!?]+', text)
        return " ".join(sentences[:sentences_count])[:300]