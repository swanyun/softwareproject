import requests
from bs4 import BeautifulSoup
import pandas as pd
import jieba
import pymysql
from collections import defaultdict
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re

# ------------------- 配置参数 -------------------
CONFIG = {
    "JD_URL": "https://search.jd.com/Search?keyword=WIFI6路由器",  # 京东搜索URL
    "TMALL_URL": "https://list.tmall.com/search_product.htm?q=WIFI6路由器",  # 天猫搜索URL
    "USER_AGENT": "Mozilla/5.0 ...",  # 模拟浏览器请求头，防止被反爬
    "DB_CONFIG": {  # 数据库连接配置
        "host": "localhost",
        "user": "your_username",
        "password": "your_password",
        "database": "router_db",
        "charset": "utf8mb4"  # 支持完整中文和表情符号
    },
    "POSITIVE_KEYWORDS": {"信号强", "速度快", "稳定", "穿墙好", "覆盖广", "易设置", "颜值高"},  # 正面评价关键词
    "NEGATIVE_KEYWORDS": {"断流", "发热", "信号差", "速度慢", "难设置", "性价比低", "不稳定"}  # 负面评价关键词
}


# ------------------- 数据采集模块 -------------------
def crawl_jd_data():
    """
    爬取京东平台的WIFI6路由器数据
    :return: 包含产品信息的列表，每个元素为字典
    """
    headers = {"User-Agent": CONFIG["USER_AGENT"]}
    try:
        # 发送HTTP请求获取页面内容
        response = requests.get(CONFIG["JD_URL"], headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("li", class_="gl-item")  # 定位商品列表项

        data = []
        for product in products:
            try:
                # 提取商品名称、价格和评价信息
                name = product.find("div", class_="p-name").a.em.get_text(strip=True)
                price = float(product.find("div", class_="p-price").i.get_text(strip=True))
                reviews = [review.get_text(strip=True) for review in product.find_all("div", class_="p-commit")]
                data.append({
                    "platform": "JD",
                    "name": name,
                    "price": price,
                    "reviews": reviews
                })
            except Exception as e:
                print(f"解析京东商品失败: {e}")
        return data
    except requests.RequestException as e:
        print(f"请求京东页面失败: {e}")
        return []


def crawl_tmall_data():
    """
    爬取天猫平台的WIFI6路由器数据
    :return: 包含产品信息的列表，每个元素为字典
    """
    headers = {"User-Agent": CONFIG["USER_AGENT"]}
    try:
        response = requests.get(CONFIG["TMALL_URL"], headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("div", class_="product-iWrap")  # 定位天猫商品项

        data = []
        for product in products:
            try:
                # 提取商品名称、格式化价格并获取评价
                name = product.find("div", class_="productTitle").a.get_text(strip=True)
                price_text = product.find("p", class_="productPrice").em.get_text(strip=True)
                price = float(re.sub(r'[^\d.]', '', price_text))  # 去除非数字字符
                review_element = product.find("div", class_="productReview")
                reviews = [review_element.span.get_text(strip=True)] if review_element else []

                data.append({
                    "platform": "TMALL",
                    "name": name,
                    "price": price,
                    "reviews": reviews
                })
            except Exception as e:
                print(f"解析天猫商品失败: {e}")
        return data
    except requests.RequestException as e:
        print(f"请求天猫页面失败: {e}")
        return []


# ------------------- 数据清洗模块 -------------------
def clean_data(raw_data):
    """
    清洗原始数据，去除重复项并提取关键信息
    :param raw_data: 爬取的原始数据列表
    :return: 清洗后的DataFrame
    """
    df = pd.DataFrame(raw_data)

    # 数据去重和过滤
    df = df.drop_duplicates(subset="name", keep="first")  # 按名称去重
    df = df[df["reviews"].apply(len) > 0]  # 过滤无评价的产品

    # 提取WIFI版本信息
    def extract_wifi_version(name):
        if "WIFI6E" in name or "WiFi6E" in name:
            return "WIFI6E"
        elif "WIFI6" in name or "WiFi6" in name or "AX" in name:
            return "WIFI6"
        elif "WIFI5" in name or "WiFi5" in name or "AC" in name:
            return "WIFI5"
        else:
            return "未知"

    # 提取无线速率信息
    def extract_speed(name):
        match = re.search(r'(\d+M)', name)  # 正则匹配数字+M的模式
        return match.group(1) if match else "未知"

    df["wifi_version"] = df["name"].apply(extract_wifi_version)
    df["speed"] = df["name"].apply(extract_speed)

    return df


# ------------------- 文本解析模块 -------------------
def analyze_reviews(df):
    """
    分析用户评价，提取优缺点标签并计算情感得分
    :param df: 清洗后的DataFrame
    :return: 添加了分析结果的DataFrame
    """
    # 加载自定义词典，增强分词准确性
    jieba.load_userdict("router_terms.txt")

    def process_review(reviews):
        """
        处理单个产品的评价列表
        :param reviews: 评价文本列表
        :return: 包含优缺点标签和情感得分的字典
        """
        positive_tags = defaultdict(int)  # 优点标签计数器
        negative_tags = defaultdict(int)  # 缺点标签计数器
        sentiment_scores = []  # 存储每条评价的情感得分

        for review in reviews:
            words = jieba.lcut(review)  # 分词处理

            # 统计关键词出现次数
            for word in words:
                if word in CONFIG["POSITIVE_KEYWORDS"]:
                    positive_tags[word] += 1
                elif word in CONFIG["NEGATIVE_KEYWORDS"]:
                    negative_tags[word] += 1

            # 计算情感得分（简单正负词数量差）
            sentiment = sum(1 for word in words if word in CONFIG["POSITIVE_KEYWORDS"]) - \
                        sum(1 for word in words if word in CONFIG["NEGATIVE_KEYWORDS"])
            sentiment_scores.append(sentiment)

        # 提取出现频率最高的前两个优缺点标签
        top_positive = [k for k, v in sorted(positive_tags.items(), key=lambda x: -x[1])[:2]]
        top_negative = [k for k, v in sorted(negative_tags.items(), key=lambda x: -x[1])[:2]]

        return {
            "positive_tags": ",".join(top_positive),  # 转为逗号分隔的字符串
            "negative_tags": ",".join(top_negative),
            "sentiment_score": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        }

    # 对每条记录的评价进行处理，并添加结果列
    df[["positive_tags", "negative_tags", "sentiment_score"]] = df["reviews"].apply(process_review).apply(pd.Series)
    return df


# 其余模块保持不变...
# ------------------- 数据存储模块 -------------------
def save_to_database(df):
    """
    将数据存入MySQL
    :param df: 分析后的DataFrame，包含产品信息、优缺点标签和情感得分
    """
    try:
        # 建立数据库连接
        conn = pymysql.connect(**CONFIG["DB_CONFIG"])
        cursor = conn.cursor()
        # 插入或更新数据的SQL语句
        insert_sql = """
            INSERT INTO router_evaluation (product_name, price, wifi_version, positive_tags, negative_tags, sentiment_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price=VALUES(price), sentiment_score=VALUES(sentiment_score)
        """
        # 遍历DataFrame的每一行
        for _, row in df.iterrows():
            # 提取要插入的数据
            params = (
                row["name"],
                row["price"],
                row["wifi_version"],
                row["positive_tags"],
                row["negative_tags"],
                row["sentiment_score"]
            )
            # 执行SQL插入语句
            cursor.execute(insert_sql, params)
        # 提交事务
        conn.commit()
        # 关闭数据库连接
        conn.close()
    except pymysql.Error as e:
        print(f"数据库操作失败：{e}")


# ------------------- 可视化模块 -------------------
def visualize_data(df):
    """
    生成分析图表
    :param df: 分析后的DataFrame，包含产品信息、优缺点标签和情感得分
    """
    # 1. 情感得分柱状图
    plt.figure(figsize=(12, 6))
    # 绘制情感得分柱状图
    plt.bar(df["name"], df["sentiment_score"], color="skyblue")
    # 设置图表标题
    plt.title("路由器情感得分对比")
    # 设置X轴标签
    plt.xlabel("产品名称")
    # 设置Y轴标签
    plt.ylabel("情感得分（越高越好）")
    # 旋转X轴标签，使其更易阅读
    plt.xticks(rotation=45, ha="right")
    # 显示图表
    plt.show()

    # 2. 优点词云图
    # 将所有优点标签连接成一个字符串
    all_positive_tags = " ".join(df["positive_tags"].str.split(",").explode().tolist())
    # 生成词云对象
    wordcloud = WordCloud(font_path="simhei.ttf", width=800, height=400).generate(all_positive_tags)
    plt.figure(figsize=(12, 6))
    # 显示词云图
    plt.imshow(wordcloud)
    # 隐藏坐标轴
    plt.axis("off")
    # 设置词云图标题
    plt.title("高频优点关键词云")
    # 显示图表
    plt.show()


# ------------------- 主流程 -------------------
if __name__ == "__main__":
    # 1. 数据采集
    jd_data = crawl_jd_data()
    tmall_data = crawl_tmall_data()
    # 合并多平台数据
    raw_data = jd_data + tmall_data

    # 2. 数据清洗
    cleaned_df = clean_data(raw_data)

    # 3. 文本解析与优缺点提取
    analyzed_df = analyze_reviews(cleaned_df)

    # 4. 数据存储
    save_to_database(analyzed_df)

    # 5. 可视化
    visualize_data(analyzed_df)
