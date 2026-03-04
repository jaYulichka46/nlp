import stanza

def get_stanza_pipeline(use_gpu=False):
    """
    Завантажує та ініціалізує пайплайн 
    Stanza для української мови.
    """
    stanza.download('uk', processors='tokenize,pos,lemma')
    nlp = stanza.Pipeline('uk', processors='tokenize,pos,lemma', use_gpu=use_gpu, verbose=False)
    return nlp

def extract_ling_features(text: str, nlp_pipeline) -> dict:
    """
    Обробляє текст через Stanza та повертає 
    лематизований текст і послідовність POS-тегів.
    """
    if not isinstance(text, str) or not text.strip():
        return {"lemma_text": "", "pos_seq": ""}
        
    doc = nlp_pipeline(text)
    
    lemmas = []
    pos_tags = []
    
    for sentence in doc.sentences:
        for word in sentence.words:
            lemma = word.lemma if word.lemma else word.text
            lemmas.append(lemma)
            pos_tags.append(word.upos)
            
    return {
        "lemma_text": " ".join(lemmas),
        "pos_seq": " ".join(pos_tags)
    }

if __name__ == "__main__":
    sample_text = "Бійці ЗСУ знищили ворожий танк."
    nlp = get_stanza_pipeline()
    res = extract_ling_features(sample_text, nlp)
    
    print(f"Оригінал: {sample_text}")
    print(f"Леми: {res['lemma_text']}")
    print(f"POS-теги: {res['pos_seq']}")