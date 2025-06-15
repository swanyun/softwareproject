# lda_analysis.py
"""
独立LDA主题分析模块
输入：jd文件夹中的JSON评论文件
输出：
  1. lda_keywords.csv - 各产品主题关键词
  2. lda_results/ - 可视化结果目录
"""

import os
import json
import csv
import numpy as np
import pandas as pd
import re
import jieba
import scipy.linalg
if not hasattr(scipy.linalg, 'triu'):
    from scipy.linalg._basic import triu
    scipy.linalg.triu = triu

from gensim import corpora, models
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis

# 复用原有系统的预处理函数
# ----------------------------
def load_stopwords(filepath='stopwords.txt'):
    """加载停用词表"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return set([line.strip() for line in f])
    except:
        return set()

def clean_text(text):
    """文本清洗函数"""
    if not isinstance(text, str):
        return ""
    emoji_pattern = re.compile(
        r"[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF" "]+",
        flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'[^\u4e00-\u9fa5，。！？、；："\'“”‘’（）《》【】]', '', text)
    text = re.sub(r'[a-zA-Z0-9]', '', text)
    text = re.sub(r'\s+', '', text)
    return text.strip()

def seg_text(text, use_stopwords=True, use_pos=False):
    """分词函数"""
    min_word_length = 1
    stopwords = load_stopwords()
    
    if use_pos:
        words = psg.cut(text)
        if use_stopwords:
            return [(w.word, w.flag) for w in words if w.word not in stopwords and len(w.word) >= min_word_length]
        return [(w.word, w.flag) for w in words if len(w.word) >= min_word_length]
    else:
        words = jieba.cut(text)
        if use_stopwords:
            return [w for w in words if w not in stopwords and len(w) >= min_word_length]
        return [w for w in words if len(w) >= min_word_length]

# LDA主题分析核心函数
# ----------------------------
def perform_lda_analysis(reviews, product_id, num_topics=5, num_keywords=10):
    """
    执行LDA主题分析并生成可视化结果
    
    参数:
    reviews - 评论列表
    product_id - 产品ID
    num_topics - 主题数量 (默认5)
    num_keywords - 每个主题的关键词数量 (默认10)
    
    返回:
    topic_keywords - 主题关键词字典
    """
    # 1. 数据预处理
    cleaned_reviews = [clean_text(review) for review in reviews]
    segmented_reviews = [seg_text(text, use_stopwords=True, use_pos=False) 
                         for text in cleaned_reviews]
    
    # 2. 准备语料库
    dictionary = corpora.Dictionary(segmented_reviews)
    corpus = [dictionary.doc2bow(text) for text in segmented_reviews]
    
    # 3. 训练LDA模型
    lda_model = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=42,
        passes=15,
        alpha='auto',
        eta='auto'
    )
    
    # 4. 提取主题关键词
    topic_keywords = {}
    for topic_id in range(num_topics):
        topic_terms = lda_model.show_topic(topic_id, topn=num_keywords)
        keywords = [term[0] for term in topic_terms]
        topic_keywords[f"主题{topic_id+1}"] = keywords
    
    # 5. 创建可视化目录
    output_dir = f"lda_results/{product_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 6. 生成可视化结果
    generate_visualizations(lda_model, corpus, dictionary, segmented_reviews, product_id, output_dir)
    
    return topic_keywords

def generate_visualizations(lda_model, corpus, dictionary, texts, product_id, output_dir):
    """生成LDA分析的可视化结果"""
    num_topics = lda_model.num_topics
    
    # 1. 主题词云
    for topic_id in range(num_topics):
        topic_terms = dict(lda_model.show_topic(topic_id, topn=20))
        wordcloud = WordCloud(
            font_path='SimHei.ttf',  # 使用支持中文的字体
            width=800,
            height=600,
            background_color='white'
        ).generate_from_frequencies(topic_terms)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'产品{product_id} - 主题{topic_id+1}关键词')
        plt.savefig(f'{output_dir}/topic_{topic_id+1}_wordcloud.png', bbox_inches='tight')
        plt.close()
    
    # 2. 主题分布饼图
    topic_dist = np.zeros(num_topics)
    for doc in corpus:
        doc_topics = lda_model.get_document_topics(doc, minimum_probability=0)
        for topic, prob in doc_topics:
            topic_dist[topic] += prob
    
    topic_dist /= len(corpus)
    plt.figure(figsize=(8, 8))
    plt.pie(topic_dist, 
            labels=[f'主题{i+1}' for i in range(num_topics)],
            autopct='%1.1f%%',
            startangle=90)
    plt.title(f'产品{product_id}主题分布')
    plt.savefig(f'{output_dir}/topic_distribution.png')
    plt.close()
    
    # 3. 主题热力图
    topic_matrix = np.zeros((len(corpus), num_topics))
    for i, doc in enumerate(corpus):
        doc_topics = lda_model.get_document_topics(doc, minimum_probability=0)
        for topic, prob in doc_topics:
            topic_matrix[i, topic] = prob
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(topic_matrix[:50], cmap="YlGnBu")  # 只显示前50条评论
    plt.title(f'产品{product_id}评论-主题分布热力图')
    plt.xlabel('主题')
    plt.ylabel('评论序号')
    plt.savefig(f'{output_dir}/topic_heatmap.png')
    plt.close()
    
    # 4. 交互式可视化
    vis_data = gensimvis.prepare(lda_model, corpus, dictionary)
    pyLDAvis.save_html(vis_data, f'{output_dir}/lda_visualization.html')

# 主处理函数
# ----------------------------
def process_jd_folder(folder_path='jd', output_csv='lda_keywords.csv'):
    """
    处理JD文件夹中的所有JSON文件
    
    参数:
    folder_path - 包含JSON评论文件的文件夹路径
    output_csv - 输出CSV文件路径
    """
    # 创建输出目录
    os.makedirs('lda_results', exist_ok=True)
    
    # 准备CSV输出文件
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        # 写入表头: 产品ID + 各主题关键词
        writer.writerow(['产品ID'] + [f'主题{i+1}关键词' for i in range(5)])
        
        # 遍历文件夹中的所有JSON文件
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                product_id = os.path.splitext(filename)[0]
                file_path = os.path.join(folder_path, filename)
                
                try:
                    # 读取JSON文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reviews_data = json.load(f)
                    
                    # 提取评论内容
                    reviews = [item['评论'] for item in reviews_data]
                    
                    # 执行LDA分析
                    topic_keywords = perform_lda_analysis(reviews, product_id)
                    
                    # 写入CSV文件
                    keywords_list = [','.join(kw) for kw in topic_keywords.values()]
                    writer.writerow([product_id] + keywords_list)
                    
                    print(f"成功处理产品: {product_id}")
                    
                except Exception as e:
                    print(f"处理文件 {filename} 时出错: {str(e)}")
    
    print(f"LDA分析完成! 结果保存在: {output_csv}")

# 主函数
if __name__ == "__main__":
    # 设置JD文件夹路径和输出文件
    process_jd_folder(folder_path='jd', output_csv='lda_keywords.csv')