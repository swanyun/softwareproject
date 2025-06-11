import json
import os
import csv
import random
from collections import defaultdict, Counter
import jieba
import jieba.posseg as psg
import pandas as pd
import re

# 定义特征词典
feature_categories = {
    '信号': ['信号', '穿墙', '覆盖', '强度', '接收'],
    '性能': ['速度', '带宽', '传输', '延迟', '丢包', '卡顿'],
    '稳定性': ['稳定', '断流', '掉线', '重启', '波动'],
    '操作': ['设置', '界面', 'APP', '管理', '配置', '固件'],
    '硬件': ['外观', '材质', '接口', '天线', '散热', '发热', '温度'],
    '服务': ['售后', '保修', '客服', '咨询', '回复'],
    '性价比': ['价格', '划算', '优惠', '赠品', '价值']
}

# 加载停用词表
def load_stopwords(filepath='stopwords.txt'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return set([line.strip() for line in f])
    except:
        return set()

stopwords = load_stopwords()

# 分词函数
def seg_text(text, use_stopwords=True, use_pos=False):
    min_word_length = 1
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

# 文本清洗函数
def clean_text(text):
    if not isinstance(text, str):
        return ""
    emoji_pattern = re.compile(
        r"[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF" "]+",
        flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'[^\u4e00-\u9fa5，。！？、；："' "'" "’‘（）《》【】]", '', text)
    text = re.sub(r'[a-zA-Z0-9]', '', text)
    text = re.sub(r'\s+', '', text)
    return text.strip()

# 特征提取函数
def extract_features(segmented_text, pos_tags):
    features = defaultdict(list)
    for word, pos in pos_tags:
        if pos.startswith(('n', 'v')):
            for category, keywords in feature_categories.items():
                if word in keywords:
                    features[category].append(word)
                    break
            else:
                if pos.startswith('n'):
                    features['其他'].append(word)
    return dict(features)

# 生成分析报告函数
def generate_analysis_report(df):
    report = {
        '优点': defaultdict(list),
        '缺点': defaultdict(list),
        'statistics': {
            '总评论数': len(df),
            '正面评论数': len(df[df['sentiment_label'] == '正面']),
            '负面评论数': len(df[df['sentiment_label'] == '负面'])
        }
    }

    positive_df = df[df['sentiment_label'] == '正面']
    for _, row in positive_df.iterrows():
        for category, words in row['features'].items():
            report['优点'][category].extend(words)

    negative_df = df[df['sentiment_label'] == '负面']
    for _, row in negative_df.iterrows():
        for category, words in row['features'].items():
            report['缺点'][category].extend(words)

    for aspect in ['优点', '缺点']:
        for category in report[aspect]:
            counter = Counter(report[aspect][category])
            report[aspect][category] = [{"特征词": word, "出现次数": count} for word, count in counter.most_common(5)]
    return report

# 指标打分函数
def evaluate_product_features_by_category(report):
    evaluation = {category: 3 for category in feature_categories.keys()}
    for category in evaluation.keys():
        positive_word_freq = report['优点'].get(category, [])
        negative_word_freq = report['缺点'].get(category, [])
        positive_total = sum(item["出现次数"] for item in positive_word_freq)
        negative_total = sum(item["出现次数"] for item in negative_word_freq)
        if positive_total + negative_total == 0:
            score = 5  # 避免除零错误
        else:
            score = (positive_total - negative_total) / (positive_total + negative_total)
            score = max(1, min(10, score * 9.4))
        evaluation[category] = score
    return evaluation

# 加载情感词典
def load_sentiment_dict(positive_path='positive.txt', negative_path='negative.txt'):
    with open(positive_path, 'r', encoding='utf-8') as f:
        positive_words = set([line.strip() for line in f if line.strip()])
    with open(negative_path, 'r', encoding='utf-8') as f:
        negative_words = set([line.strip() for line in f if line.strip()])
    return positive_words, negative_words

positive_set, negative_set = load_sentiment_dict()

def process_files_in_folder(folder_path, keyword_csv_path, score_csv_path, reviews_csv_path):
    # 修改1: 使用utf-8-sig编码解决Excel乱码问题
    with open(keyword_csv_path, 'w', newline='', encoding='utf-8-sig') as kcsv, \
            open(score_csv_path, 'w', newline='', encoding='utf-8-sig') as scsv, \
            open(reviews_csv_path, 'w', newline='', encoding='utf-8-sig', errors='replace') as rcsv:

        # 初始化CSV写入器
        kwriter = csv.writer(kcsv)
        swriter = csv.writer(scsv)
        rwriter = csv.writer(rcsv, quoting=csv.QUOTE_MINIMAL)

        # 写入表头
        kwriter.writerow(['id'] + [f'关键词{i // 2 + 1}' if i % 2 == 0 else f'频率{i // 2 + 1}' for i in range(100)])
        swriter.writerow(['id'] + list(feature_categories.keys()))
        rwriter.writerow(['product_id', 'pos1', 'pos2', 'pos3', 'neg1', 'neg2', 'neg3'])

        # 遍历JSON文件
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                product_id = os.path.splitext(filename)[0]

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reviews = json.load(f)
                    df = pd.DataFrame(reviews)

                    # 数据预处理
                    df = df.drop_duplicates(subset=['name', '评论'])
                    df = df.dropna(subset=['评论'])
                    df['cleaned_content'] = df['评论'].apply(clean_text)
                    df = df[df['cleaned_content'].str.len() > 0]

                    # 特征提取
                    df['segmented'] = df['cleaned_content'].apply(
                        lambda x: seg_text(x, use_stopwords=True, use_pos=False))
                    df['segmented_pos'] = df['cleaned_content'].apply(
                        lambda x: seg_text(x, use_stopwords=True, use_pos=True))
                    df['features'] = df['segmented_pos'].apply(lambda x: extract_features([w[0] for w in x], x))

                    # 情感分析
                    def sentiment_analyzer(word_list):
                        positive_count = sum(1 for word in word_list if word in positive_set)
                        negative_count = sum(1 for word in word_list if word in negative_set)
                        if positive_count > negative_count:
                            return '正面', positive_count, negative_count
                        elif negative_count > positive_count:
                            return '负面', positive_count, negative_count
                        else:
                            return '中性', positive_count, negative_count

                    sentiment_results = df['segmented'].apply(
                        lambda x: pd.Series(sentiment_analyzer(x),
                                            index=['sentiment_label', 'positive_count', 'negative_count'])
                    )
                    df = pd.concat([df, sentiment_results], axis=1)

                    # 随机抽取评论（新增核心功能）
                    def sample_comments(reviews, num=3):
                        if len(reviews) >= num:
                            return random.sample(reviews, num)
                        elif len(reviews) > 0:
                            return list(reviews) + ['暂无'] * (num - len(reviews))
                        else:
                            return ['暂无'] * num

                    pos_comments = sample_comments(df[df['sentiment_label'] == '正面']['评论'].tolist())
                    neg_comments = sample_comments(df[df['sentiment_label'] == '负面']['评论'].tolist())

                    # 写入评论数据
                    rwriter.writerow([product_id] + pos_comments + neg_comments)

                    # 关键词处理（改进格式）
                    all_words = [word for sublist in df['segmented'] for word in sublist]
                    word_counter = Counter(all_words)

                    # 生成关键词-频率对
                    keyword_freq_pairs = []
                    for word, freq in word_counter.most_common(50):
                        if word not in ['路由器', '款']:
                            keyword_freq_pairs.extend([word, freq])

                    # 填充到50个关键词
                    while len(keyword_freq_pairs) < 100:  # 50对关键词+频率
                        keyword_freq_pairs.extend(['暂无', 0])

                    kwriter.writerow([product_id] + keyword_freq_pairs[:100])

                    # 生成评分
                    analysis_report = generate_analysis_report(df)
                    product_scores = evaluate_product_features_by_category(analysis_report)
                    swriter.writerow([product_id] + list(product_scores.values()))

                    print(f"成功处理：{product_id}")

                except Exception as e:
                    print(f"处理文件 {filename} 时出错: {str(e)}")

# 运行参数设置
if __name__ == "__main__":
    process_files_in_folder(
        folder_path='jd',
        keyword_csv_path='keywords.csv',
        score_csv_path='scores.csv',
        reviews_csv_path='sampled_reviews.csv'
    )
    print("所有文件处理完成")

    # 打印 sampled_reviews.csv 文件内容（用于验证）
    try:
        # 修改2: 使用utf-8-sig编码读取文件
        with open('sampled_reviews.csv', 'r', encoding='utf-8-sig') as f:
            print("sampled_reviews.csv 文件内容：")
            print(f.read())
    except Exception as e:
        print(f"读取 sampled_reviews.csv 文件时出错：{str(e)}")