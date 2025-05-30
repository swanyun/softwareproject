from DrissionPage import ChromiumPage, ChromiumOptions
import time
import json
import csv
import os
from DrissionPage._units.actions import Actions
import random
# 常量配置
CSV_INPUT = 'jdnew_products.csv'  # 存储商品 ID 的 CSV 文件      # 存储评论的目录
COOKIE_PATH = 'jd11yy.json'
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SAVE_DIR = r'C:\Users\MI\PycharmProjects\pythonProject2\jd'

def setup_browser():
    co = ChromiumOptions()
    co.set_browser_path(CHROME_PATH)
    return ChromiumPage(co)

def read_product_ids(path):
    ids = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        print("字段名列表：", reader.fieldnames)  # 帮助调试
        for row in reader:
            product_id = row.get('商品ID')
            if product_id:
                ids.append(product_id.strip())
    return ids


def get_comments(page, product_id):
    url = f'https://item.jd.com/{product_id}.html'
    all_comments = []
    try:
        page.get(url)
        time.sleep(random.uniform(0.5, 0.8))  # ✅ 随机等待 1-3 秒
        page.listen.start('client.action')
        page.ele('css:.all-btn .arrow').click()
        ac = Actions(page)

        for page1 in range(1, 50):
            r = page.listen.wait()
            jd_data = r.response.body
            print(jd_data)
            comment_list = jd_data.get('result', {}).get('floors', [])[2].get('data', [])
            comments = extract_comments(comment_list)
            all_comments.extend(comments)
            tab = page.ele('css:div._rateListContainer_1ygkr_45')
            ac.scroll(delta_y=4000, on_ele=tab)

            time.sleep(random.uniform(1, 3))

        return all_comments
    except Exception as e:
        print(f"[{product_id}] 抓取评论失败：{e}")
        return all_comments

def extract_comments(comment_list):
    comments = []
    for item in comment_list:
        info = item.get('commentInfo', {})
        comments.append({
            'name': info.get('userNickName', ''),
            '评分': info.get('commentScore', ''),
            '产品': info.get('productSpecifications', ''),
            '日期': info.get('commentDate', ''),
            '评论': info.get('commentData', '')
        })
    return comments

def save_to_json(data, product_id):
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f'{product_id}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[{product_id}] 已保存 JSON 到 {path}")

def save_to_csv(data, product_id):
    if not data:
        print(f"[{product_id}] 无评论数据，跳过保存 CSV")
        return

    filtered_data = [
        row for row in data
        if any(str(v).strip() for v in row.values())
    ]

    if not filtered_data:
        print(f"[{product_id}] 所有评论为空，跳过保存 CSV")
        return

    # 替换评论中的换行符
    for row in filtered_data:
        if '评论' in row and isinstance(row['评论'], str):
            row['评论'] = row['评论'].replace('\n', ' ').replace('\r', ' ')

    keys = filtered_data[0].keys()
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f'{product_id}.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(filtered_data)
    print(f"[{product_id}] 已保存 CSV 到 {path}")

def main():
    product_ids = read_product_ids(CSV_INPUT)
    page = setup_browser()
    print(f"读取到商品ID数量：{len(product_ids)}")

    for product_id in product_ids:
        json_path = os.path.join(SAVE_DIR, f'{product_id}.json')
        csv_path = os.path.join(SAVE_DIR, f'{product_id}.csv')

        if os.path.exists(json_path) or os.path.exists(csv_path):
            print(f"[{product_id}] 已存在 JSON 或 CSV 文件，跳过该商品")
            continue

        print(f'\n正在爬取商品 {product_id} 的评论...')
        comments = get_comments(page, product_id)
        if comments:
            save_to_json(comments, product_id)
            save_to_csv(comments, product_id)
        else:
            print(f"[{product_id}] 没有抓到任何评论")

if __name__ == '__main__':
    main()
