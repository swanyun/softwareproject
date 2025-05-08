import requests
from bs4 import BeautifulSoup
import pandas as pd
import jieba
import pymysql
from collections import defaultdict
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# ------------------- 配置参数 -------------------
CONFIG = {
    "JD_URL": "https://search.jd.com/Search?keyword=WIFI6路由器",
    "TMALL_URL": "https://list.tmall.com/search_product.htm?q=WIFI6路由器",
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "DB_CONFIG": {
        "host": "localhost",
        "user": "your_username",
        "password": "your_password",
        "database": "router_db",
        "charset": "utf8mb4"
    },
    # 自定义关键词库（优点/缺点）
    "POSITIVE_KEYWORDS": {"信号强", "速度快", "稳定", "穿墙好", "覆盖广", "易设置", "颜值高"},
    "NEGATIVE_KEYWORDS": {"断流", "发热", "信号差", "速度慢", "难设置", "性价比低", "不稳定"}
}


# ------------------- 数据采集模块 -------------------
def crawl_jd_data():
    """爬取京东WIFI6路由器数据"""
    headers = {"User-Agent": CONFIG["USER_AGENT"]}
    response = requests.get(CONFIG["JD_URL"], headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("li", class_="gl-item")
    data = []
    for product in products:
        try:
            name = product.find("div", class_="p-name").a.em.get_text(strip=True)
            price = float(product.find("div", class_="p-price").i.get_text(strip=True))
            reviews = [review.get_text(strip=True) for review in product.find_all("div", class_="p-commit")]
            data.append({"platform": "JD", "name": name, "price": price, "reviews": reviews})
        except Exception as e:
            print(f"京东数据解析失败：{e}")
    return data


def crawl_tmall_data():
    """爬取天猫WIFI6路由器数据（需适配天猫网页结构）"""
    # 此处需根据天猫实际HTML结构编写解析逻辑，示例略
    return []


# ------------------- 数据清洗模块 -------------------
def clean_data(raw_data):
    """清洗数据：去除重复、格式化价格、提取WIFI版本"""
    df = pd.DataFrame(raw_data)
    # 去除重复产品（按名称去重）
    df = df.drop_duplicates(subset="name", keep="first")
    # 过滤无评价的产品
    df = df[df["reviews"].apply(len) >= 0]
    # 提取WIFI版本（示例：从名称中匹配"WIFI6"或"AX"）
    df["wifi_version"] = df["name"].apply(lambda x: "WIFI6" if "WIFI6" in x or "AX" in x else "未知")
    return df


# ------------------- 文本解析模块 -------------------
def analyze_reviews(df):
    """分析评价：提取优缺点标签和情感得分"""
    # 加载自定义分词词典
    jieba.load_userdict("router_terms.txt")  # 自定义词典文件需包含"断流""穿墙"等术语

    def process_review(reviews):
        positive_tags = defaultdict(int)
        negative_tags = defaultdict(int)
        sentiment_scores = []
        for review in reviews:
            # 分词
            words = jieba.lcut(review)
            # 匹配关键词
            for word in words:
                if word in CONFIG["POSITIVE_KEYWORDS"]:
                    positive_tags[word] += 1
                elif word in CONFIG["NEGATIVE_KEYWORDS"]:
                    negative_tags[word] += 1
            # 情感分析（简化示例，实际可使用更复杂模型）
            sentiment = sum(1 for word in words if word in CONFIG["POSITIVE_KEYWORDS"]) - sum(
                1 for word in words if word in CONFIG["NEGATIVE_KEYWORDS"])
            sentiment_scores.append(sentiment)
        # 提取TOP2优缺点标签
        top_positive = [k for k, v in sorted(positive_tags.items(), key=lambda x: -x[1])[:2]]
        top_negative = [k for k, v in sorted(negative_tags.items(), key=lambda x: -x[1])[:2]]
        return {
            "positive_tags": ",".join(top_positive),
            "negative_tags": ",".join(top_negative),
            "sentiment_score": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        }

    df[["positive_tags", "negative_tags", "sentiment_score"]] = df["reviews"].apply(process_review).apply(pd.Series)
    return df


# ------------------- 数据存储模块 -------------------
def save_to_database(df):
    """将数据存入MySQL"""
    conn = pymysql.connect(**CONFIG["DB_CONFIG"])
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO router_evaluation (product_name, price, wifi_version, positive_tags, negative_tags, sentiment_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE price=VALUES(price), sentiment_score=VALUES(sentiment_score)
    """
    for _, row in df.iterrows():
        params = (
            row["name"],
            row["price"],
            row["wifi_version"],
            row["positive_tags"],
            row["negative_tags"],
            row["sentiment_score"]
        )
        cursor.execute(insert_sql, params)
    conn.commit()
    conn.close()


# ------------------- 可视化模块 -------------------
def visualize_data(df):
    """生成分析图表"""
    # 1. 情感得分柱状图
    plt.figure(figsize=(12, 6))
    plt.bar(df["name"], df["sentiment_score"], color="skyblue")
    plt.title("路由器情感得分对比")
    plt.xlabel("产品名称")
    plt.ylabel("情感得分（越高越好）")
    plt.xticks(rotation=45, ha="right")
    plt.show()

    # 2. 优点词云图
    all_positive_tags = " ".join(df["positive_tags"].str.split(",").explode().tolist())
    wordcloud = WordCloud(font_path="simhei.ttf", width=800, height=400).generate(all_positive_tags)
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.title("高频优点关键词云")
    plt.show()


# ------------------- 主流程 -------------------
if __name__ == "__main__":
    # 1. 数据采集
    jd_data = crawl_jd_data()
    tmall_data = crawl_tmall_data()
    raw_data = jd_data + tmall_data  # 合并多平台数据

    # 2. 数据清洗
    cleaned_df = clean_data(raw_data)

    # 3. 文本解析与优缺点提取
    analyzed_df = analyze_reviews(cleaned_df)

    # 4. 数据存储
    save_to_database(analyzed_df)

    # 5. 可视化
    visualize_data(analyzed_df)