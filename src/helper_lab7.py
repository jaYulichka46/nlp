"""
Допоміжний модуль для Лабораторної роботи 7 (Класифікація українських новин).
Містить функції для навчання baseline-моделей (LogReg, LinearSVC), 
роботи з char-ngrams та специфічні для багатокласової класифікації (OvR) метрики.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score, 
    f1_score, 
    confusion_matrix, 
    precision_recall_curve, 
    classification_report,
    precision_score,
    recall_score
)

def run_logreg_baseline(X_train, y_train, class_weight=None, random_state=42):
    """
    Базовий пайплайн Logistic Regression з ЛР6.
    Використовує sublinear_tf=True.
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2), 
            max_features=25000, 
            sublinear_tf=True
        )),
        ('clf', LogisticRegression(
            random_state=random_state, 
            max_iter=1000, 
            class_weight=class_weight
        ))
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def run_linear_svc(X_train, y_train, use_char_ngrams=False, class_weight=None, random_state=42):
    """
    Пайплайн для LinearSVC.
    Якщо use_char_ngrams=True, об'єднує слова та символи для кращої роботи з морфологією.
    """
    if use_char_ngrams:
        vectorizer = FeatureUnion([
            ('word', TfidfVectorizer(
                analyzer='word', 
                ngram_range=(1, 2), 
                max_features=15000, 
                sublinear_tf=True
            )),
            ('char', TfidfVectorizer(
                analyzer='char_wb', 
                ngram_range=(3, 5), 
                max_features=15000, 
                sublinear_tf=True
            ))
        ])
    else:
        vectorizer = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2), 
            max_features=25000, 
            sublinear_tf=True
        )
        
    pipeline = Pipeline([
        ('features', vectorizer),
        ('clf', LinearSVC(
            C=1.0, 
            random_state=random_state, 
            class_weight=class_weight, 
            max_iter=2000
        ))
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def plot_confusion_matrix(y_true, y_pred, classes, title='Confusion Matrix'):
    """
    Будує теплову карту матриці помилок для багатокласової задачі.
    """
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=classes, yticklabels=classes)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def print_top_features_multiclass(pipeline, model_name, top_n=10):
    """
    Виводить Top ознак для КОЖНОГО класу (специфіка багатокласової класифікації).
    """
    print(f"Top {top_n} Features for: {model_name}\n" + "="*50)
    
    clf = pipeline.named_steps['clf']
    vec_step = 'tfidf' if 'tfidf' in pipeline.named_steps else 'features'
    vectorizer = pipeline.named_steps[vec_step]
    
    # Витягуємо імена ознак
    if type(vectorizer).__name__ == 'FeatureUnion':
        feature_names = []
        for name, transformer in vectorizer.transformer_list:
            names = [f"[{name}] {f}" for f in transformer.get_feature_names_out()]
            feature_names.extend(names)
        feature_names = np.array(feature_names)
    else:
        feature_names = vectorizer.get_feature_names_out()

    classes = clf.classes_
    
    # В багатокласовій класифікації coef_ має форму (n_classes, n_features)
    for i, class_label in enumerate(classes):
        coefs = clf.coef_[i]
        top_positive_idx = np.argsort(coefs)[-top_n:][::-1]
        
        print(f"Найсильніші маркери для рубрики: {class_label}")
        for idx in top_positive_idx:
            print(f"  {feature_names[idx]:<30} (вага: {coefs[idx]:.4f})")
        print("-" * 30)
    print("\n")


# ==========================================
# Функції для One-vs-Rest (PR-крива та пороги)
# ==========================================

def plot_pr_curve_ovr(y_true, y_scores_matrix, classes, target_class):
    """
    Будує PR-криву для одного виділеного класу (One-vs-Rest).
    y_scores_matrix: результат decision_function() розміром (n_samples, n_classes)
    """
    class_idx = list(classes).index(target_class)
    y_scores_target = y_scores_matrix[:, class_idx]
    
    y_true_binary = (y_true == target_class).astype(int)
    precision, recall, _ = precision_recall_curve(y_true_binary, y_scores_target)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, marker='.', label=f'{target_class} vs Rest')
    plt.xlabel(f'Recall (Повнота для "{target_class}")')
    plt.ylabel(f'Precision (Точність для "{target_class}")')
    plt.title(f'PR Curve (One-vs-Rest): {target_class}')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()


def evaluate_ovr_thresholds(y_true, y_scores_matrix, classes, target_class, thresholds=[0.0, -0.5, 0.5]):
    """
    Аналіз порогів для виділеного класу (One-vs-Rest).
    """
    results = []
    class_idx = list(classes).index(target_class)
    y_scores_target = y_scores_matrix[:, class_idx]
    
    y_true_binary = (y_true == target_class).astype(int)
    
    for t in thresholds:
        y_pred_binary = (y_scores_target >= t).astype(int)
        
        acc = accuracy_score(y_true_binary, y_pred_binary)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        
        results.append({
            'Threshold': t,
            'Accuracy (OvR)': acc,
            f'F1 ({target_class})': f1,
            f'Precision ({target_class})': precision,
            f'Recall ({target_class})': recall
        })
        
    return pd.DataFrame(results)