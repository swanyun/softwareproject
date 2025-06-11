import json
from collections import defaultdict
import jieba
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re #正则表达式
import jieba.posseg as psg #中文分词和词性标注
from collections import Counter


import warnings

from pyecharts.charts import WordCloud

warnings.filterwarnings("ignore")


import os
file_path='jd/4772588.json'
with open(file_path, 'r', encoding='utf-8') as f:
    reviews = json.load(f)  # reviews 是 Python list

# 转换为DataFrame
df = pd.DataFrame(reviews)  # df 是 Pandas DataFrame

# 正确用法：对DataFrame操作
print("数据维度:", df.shape)  # 显示(行数, 列数)
print("\n前5行数据:")
print(df.head())  # 显示前5行
#去重
# 假设我们要基于'rateContent'和'userNick'去重
df = df.drop_duplicates(subset=['name', '评论'])
# 检查去重后的数据
print("\n去重后数据维度:", df.shape)
print("\n去重后前5行数据:")
print(df.head())

# 提取评论内容
content = df['评论']
print("\n评论内容数量:", len(content))

# 3. 数据清洗
# 3.1 去除空评论
df = df.dropna(subset=['评论'])

# 3.2 去除无意义评论
meaningless_comments = ["此用户没有填写评价", "评价方未及时评价"]
df = df[~df['评论'].isin(meaningless_comments)]


# 3.3 定义文本清洗函数
def clean_text(text):
    if not isinstance(text, str):
        return ""

    # 去除表情符号
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    # 保留中文和中文标点
    text = re.sub(r'[^\u4e00-\u9fa5，。！？、；："\'（）《》【】]', '', text)

    # 去除数字和字母
    text = re.sub(r'[a-zA-Z0-9]', '', text)

    # 去除多余空格和特殊空白字符
    text = re.sub(r'\s+', '', text)

    return text.strip()


# 应用清洗函数
df['cleaned_content'] = df['评论'].apply(clean_text)

# 3.4 去除清洗后为空的评论
df = df[df['cleaned_content'].str.len() > 0]

# 4. 结果展示
print("\n清洗后数据维度:", df.shape)
print("\n清洗后数据示例:")
print(df[['评论', 'cleaned_content']].head(10).to_string(index=False))

# 5. 提取评论内容
content = df['cleaned_content']
print("\n有效评论内容数量:", len(content))




# 3. 中文分词处理
# 加载停用词表（需准备或使用默认）
def load_stopwords(filepath='stopwords.txt'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return set([line.strip() for line in f])
    except:
        return set()

stopwords = load_stopwords()

# 分词函数
# 修改后的分词函数（更清晰的过滤逻辑）
def seg_text(text, use_stopwords=True, use_pos=False):
    # 允许单独控制长度过滤
    min_word_length = 1 # 原为2

    if use_pos:
        words = psg.cut(text)
        if use_stopwords:
            return [(w.word, w.flag) for w in words
                    if w.word not in stopwords
                    and len(w.word) >= min_word_length]
        return [(w.word, w.flag) for w in words
                if len(w.word) >= min_word_length]
    else:
        words = jieba.cut(text)
        if use_stopwords:
            return [w for w in words
                    if w not in stopwords
                    and len(w) >= min_word_length]
        return [w for w in words
                if len(w) >= min_word_length]

# 添加分词结果列
print("\n正在进行分词处理...")
df['segmented'] = df['cleaned_content'].apply(lambda x: seg_text(x, use_stopwords=True, use_pos=False))
df['segmented_pos'] = df['cleaned_content'].apply(lambda x: seg_text(x, use_stopwords=True, use_pos=True))

# 4. 分词结果分析
# 词频统计
all_words = [word for sublist in df['segmented'] for word in sublist]
word_freq = Counter(all_words)
print("\n最常出现的40个词语:")
print(word_freq.most_common(40))

# 5. 结果展示
print("\n完整处理后的数据示例:")
print(df[['cleaned_content', 'segmented', 'segmented_pos']].head(5).to_string(index=False))



# 6. 去除不包含名词的评论
def contains_noun(pos_list):
    # 检查是否包含名词（词性为 "n" 或 "ns" 等）
    for word, pos in pos_list:
        if pos.startswith('n'):  # 包含名词
            return True
    return False

# 应用过滤函数
df = df[df['segmented_pos'].apply(contains_noun)]

# 7. 结果展示
print("\n去除不包含名词的评论后数据维度:", df.shape)
print("\n去除不包含名词的评论后数据示例:")
print(df[['cleaned_content', 'segmented', 'segmented_pos']].head(5).to_string(index=False))




# 1. 存储分词结果到 JSON 文件
# 准备分词结果数据
segmented_data = df[['cleaned_content', 'segmented']].to_dict(orient='records')

# 写入 JSON 文件
with open('segmented_comments.json', 'w', encoding='utf-8') as f:
    json.dump(segmented_data, f, ensure_ascii=False, indent=4)

print("分词结果已存储到 'segmented_comments.json' 文件中。")

# 2. 存储高频词到 JSON 文件
# 获取高频词数据
high_frequency_words = word_freq.most_common(40)  # 获取前 40 个高频词
high_frequency_words_dict = dict(high_frequency_words)  # 转换为字典

# 写入 JSON 文件
with open('high_frequency_words.json', 'w', encoding='utf-8') as f:
    json.dump(high_frequency_words_dict, f, ensure_ascii=False, indent=4)

print("高频词已存储到 'high_frequency_words.json' 文件中。")


# ========== 情感分析 ==========
# 1. 加载情感词典
def load_sentiment_dict(positive_path='positive.txt', negative_path='negative.txt'):
    with open(positive_path, 'r', encoding='utf-8') as f:
        positive_words = set([line.strip() for line in f if line.strip()])

    with open(negative_path, 'r', encoding='utf-8') as f:
        negative_words = set([line.strip() for line in f if line.strip()])

    return positive_words, negative_words


positive_set, negative_set = load_sentiment_dict()


# 2. 定义情感分析函数
def sentiment_analyzer(word_list):
    positive_count = sum(1 for word in word_list if word in positive_set)
    negative_count = sum(1 for word in word_list if word in negative_set)

    # 情感判断逻辑
    if positive_count > negative_count:
        return '正面', positive_count, negative_count
    elif negative_count > positive_count:
        return '负面', positive_count, negative_count
    else:
        return '中性', positive_count, negative_count


# 3. 应用情感分析
print("\n正在进行情感标注...")
sentiment_results = df['segmented'].apply(
    lambda x: pd.Series(sentiment_analyzer(x),
                        index=['sentiment_label', 'positive_count', 'negative_count'])
)
df = pd.concat([df, sentiment_results], axis=1)

# 4. 结果验证
print("\n情感分布统计:")
print(df['sentiment_label'].value_counts())

print("\n情感分析示例（正面）:")
print(
    df[df['sentiment_label'] == '正面'][['cleaned_content', 'segmented', 'sentiment_label']].sample(3, random_state=1))

print("\n情感分析示例（负面）:")
print(
    df[df['sentiment_label'] == '负面'][['cleaned_content', 'segmented', 'sentiment_label']].sample(3, random_state=1))

# 5. 存储情感分析结果
sentiment_data = df[['cleaned_content', 'segmented', 'sentiment_label', 'positive_count', 'negative_count']].to_dict(
    orient='records')
with open('sentiment_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(sentiment_data, f, ensure_ascii=False, indent=4)
print("\n情感分析结果已存储到 sentiment_analysis.json")

# 6. 可视化展示（可选）
plt.figure(figsize=(10, 6))
sns.countplot(x='sentiment_label', data=df, order=['正面', '中性', '负面'])
plt.title('评论情感分布')
plt.savefig('sentiment_distribution.png')
plt.show()

# ========== 1. 准备特征词典 ==========
# 定义路由器核心特征类别（可根据具体商品调整）
feature_categories = {
    '信号': ['信号', '穿墙', '覆盖', '强度', '接收'],
    '性能': ['速度', '带宽', '传输', '延迟', '丢包', '卡顿'],
    '稳定性': ['稳定', '断流', '掉线', '重启', '波动'],
    '操作': ['设置', '界面', 'APP', '管理', '配置', '固件'],
    '硬件': ['外观', '材质', '接口', '天线', '散热', '发热', '温度'],
    '服务': ['售后', '保修', '客服', '咨询', '回复'],
    '性价比': ['价格', '划算', '优惠', '赠品', '价值']
}


# ========== 2. 定义特征提取函数 ==========
def extract_features(segmented_text, pos_tags):
    """
    提取技术特征词和修饰词组合
    返回格式：{特征类别: [特征词]}
    """
    features = defaultdict(list)

    # 组合词性规则：名词/动词 + 形容词/副词
    for word, pos in pos_tags:
        # 筛选特征词性（名词、动词）
        if pos.startswith(('n', 'v')):
            # 匹配预定义特征类别
            for category, keywords in feature_categories.items():
                if word in keywords:
                    features[category].append(word)
                    break
            else:  # 未匹配到预定义类别的通用处理
                if pos.startswith('n'):
                    features['其他'].append(word)
    return dict(features)


# 应用特征提取
print("\n正在提取产品特征...")
df['features'] = df['segmented_pos'].apply(
    lambda x: extract_features([w[0] for w in x], x)
)


# ========== 3. 生成优缺点报告 ==========
def generate_analysis_report(df):
    # 初始化报告结构
    report = {
        '优点': defaultdict(list),
        '缺点': defaultdict(list),
        'statistics': {
            '总评论数': len(df),
            '正面评论数': len(df[df['sentiment_label'] == '正面']),
            '负面评论数': len(df[df['sentiment_label'] == '负面'])
        }
    }

    # 分析正面评价
    positive_df = df[df['sentiment_label'] == '正面']
    for _, row in positive_df.iterrows():
        for category, words in row['features'].items():
            report['优点'][category].extend(words)

    # 分析负面评价
    negative_df = df[df['sentiment_label'] == '负面']
    for _, row in negative_df.iterrows():
        for category, words in row['features'].items():
            report['缺点'][category].extend(words)

    # 统计词频并排序
    for aspect in ['优点', '缺点']:
        for category in report[aspect]:
            counter = Counter(report[aspect][category])
            report[aspect][category] = [
                {"特征词": word, "出现次数": count}
                for word, count in counter.most_common(5)
            ]

    return report


# 生成报告
analysis_report = generate_analysis_report(df)

# ========== 4. 结构化存储 ==========
with open('product_analysis_report.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_report, f, ensure_ascii=False, indent=4)
print("产品分析报告已保存到 product_analysis_report.json")

import math

# 生成分析报告
analysis_report = generate_analysis_report(df)

# 定义针对各个指标的打分函数
def evaluate_product_features_by_category(report):
    # 初始化各个指标的分数
    evaluation = {
        '信号': 3,
        '性能': 3,
        '稳定性': 3,
        '操作': 3,
        '硬件': 3,
        '服务': 3,
        '性价比': 3
    }

    # 遍历优缺点，对每个指标进行打分
    for category in evaluation.keys():
        # 获取该类别在优缺点中的所有特征词频率
        positive_word_freq = report['优点'].get(category, [])
        negative_word_freq = report['缺点'].get(category, [])

        # 计算正面和负面特征词的总出现次数
        positive_total = sum(item["出现次数"] for item in positive_word_freq)
        negative_total = sum(item["出现次数"] for item in negative_word_freq)

        # 计算基于（好评 - 差评）/5 的分数
        score = (positive_total - negative_total) / 5

        # 确保分数在1-5的范围内，并向上取整
        score = max(1, min(5, score))
        score = math.ceil(score)  # 向上取整

        evaluation[category] = score

    return evaluation

# 执行各个指标的打分
product_feature_scores = evaluate_product_features_by_category(analysis_report)

# 结果展示
print("\n产品各指标评价结果:")
for category, score in product_feature_scores.items():
    print(f"{category}: {score}/5")

# 将评价结果存入报告
analysis_report['feature_scores'] = product_feature_scores

# 保存更新后的报告
with open('product_analysis_report.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_report, f, ensure_ascii=False, indent=4)
print("\n更新后的产品分析报告已保存到 product_analysis_report.json")








