import threading
import numpy as np
import jieba
import jieba.analyse
from collections import Counter

_model = None
_lock = threading.Lock()
_use_transformer = False


def get_model():
    global _model, _use_transformer
    with _lock:
        if _model is None:
            _model = "jieba"
            _use_transformer = False
            print("使用jieba分词智能匹配")
    return _model


def encode_text(text):
    return None


def _jieba_similarity(text1, text2):
    keywords1 = set(jieba.analyse.extract_tags(text1, topK=20))
    keywords2 = set(jieba.analyse.extract_tags(text2, topK=20))
    
    if not keywords1 or not keywords2:
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))
        stop_words = {'的', '了', '是', '在', '有', '和', '与', '或', '等', '这', '那', 
                      '我', '你', '他', '她', '它', '们', '着', '过', '被', '把', '给',
                      '向', '从', '到', '对', '为', '一', '个', '上', '下', '中', '里',
                      '不', '没', '很', '都', '也', '就', '会', '能', '要', '想', '可',
                      ' ', '\n', '\t', '。', '，', '！', '？', '、', '：', '；'}
        keywords1 = words1 - stop_words
        keywords2 = words2 - stop_words
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    
    jaccard = len(intersection) / len(union) if union else 0.0
    
    tfidf1 = jieba.analyse.extract_tags(text1, topK=10, withWeight=True)
    tfidf2 = jieba.analyse.extract_tags(text2, topK=10, withWeight=True)
    
    weight1 = {k: w for k, w in tfidf1}
    weight2 = {k: w for k, w in tfidf2}
    
    common_keywords = set(weight1.keys()) & set(weight2.keys())
    if common_keywords:
        weighted_match = sum(min(weight1[k], weight2[k]) for k in common_keywords)
        weighted_match = min(1.0, weighted_match)
    else:
        weighted_match = 0.0
    
    similarity = jaccard * 0.5 + weighted_match * 0.5
    
    return similarity


def compute_semantic_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    
    get_model()
    return _jieba_similarity(text1, text2)


def compute_batch_similarity(query_text, text_list):
    if not query_text or not text_list:
        return []
    
    get_model()
    return [_jieba_similarity(query_text, t) for t in text_list]


def extract_keywords(text):
    if not text:
        return []
    
    keywords = jieba.analyse.extract_tags(text, topK=10)
    return list(keywords)
