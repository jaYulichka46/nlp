from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation
from sklearn.pipeline import Pipeline

def build_lsa_pipeline(n_components=5, min_df=5, max_df=0.90, stop_words=None, random_state=42):
    pipeline = Pipeline([
        ('vectorizer', TfidfVectorizer(
            max_df=max_df, 
            min_df=min_df, 
            stop_words=stop_words 
        )),
        ('lsa', TruncatedSVD(
            n_components=n_components, 
            random_state=random_state
        ))
    ])
    return pipeline

def build_lda_pipeline(n_components=5, min_df=5, max_df=0.90, stop_words=None, random_state=42):
    pipeline = Pipeline([
        ('vectorizer', CountVectorizer(
            max_df=max_df, 
            min_df=min_df, 
            stop_words=stop_words
        )),
        ('lda', LatentDirichletAllocation(
            n_components=n_components, 
            random_state=random_state,
            learning_method='batch'
        ))
    ])
    return pipeline