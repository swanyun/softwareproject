from DrissionPage import ChromiumPage, ChromiumOptions
import os
import time
import csv

# 常量配置
CSV_INPUT = 'jdnew_products.csv'  # 存储商品 ID 的 CSV 文件
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SAVE_DIR = r'C:\Users\MI\PycharmProjects\pythonProject2\jdgoodshop1'  # 修改为 shop 目录

def setup_browser():
    co = ChromiumOptions()
    co.set_browser_path(CHROME_PATH)


    page = ChromiumPage(co)
    # 伪装 webdriver
    page.run_js("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return page

def read_product_ids(path):
    ids = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_id = row.get('商品ID')
            if product_id:
                ids.append(product_id.strip())
    return ids

def has_been_scraped(product_id):
    txt_path = os.path.join(SAVE_DIR, f'{product_id}.txt')
    return os.path.exists(txt_path)

def remove_after_sale_info(text):
    keyword = '售后保障'
    pos = text.find(keyword)
    if pos != -1:
        return text[:pos].strip()
    return text

def get_product_detail_text(page, product_id):
    url = f'https://item.jd.com/{product_id}.html'
    page.get(url)
    time.sleep(3)  # 等待页面加载

    current_url = page.url
    if current_url == 'https://www.jd.com/?from=pc_item&reason=403':
        print(f"[{product_id}] 跳转到错误页面，可能被限制或商品不存在，跳过。")
        return None

    try:
        # 提取好评率文本
        applause_ele = page.ele('.applause-rate')
        if applause_ele:
            applause_text = applause_ele.text
            applause_text = applause_text.replace('\n', '').strip()
            print(f"[{product_id}] 获取到好评率：{applause_text}")
            return applause_text
        else:
            print(f"[{product_id}] 页面中未找到好评率元素")
            return None
    except Exception as e:
        print(f"[{product_id}] 获取好评率时发生异常: {e}")
        return None



def save_detail_text(text, product_id):
    if not text:
        print(f"[{product_id}] 无详情内容，跳过保存")
        return
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f'{product_id}.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"[{product_id}] 商品详情已保存到 {path}")

def main():
    product_ids = read_product_ids(CSV_INPUT)
    print(f"读取到商品ID数量：{len(product_ids)}")
    page = setup_browser()

    for product_id in product_ids:
        if has_been_scraped(product_id):
            print(f"[{product_id}] 已爬取，跳过")
            continue

        print(f"\n正在爬取商品 {product_id} 的详情...")
        detail_text = get_product_detail_text(page, product_id)
        save_detail_text(detail_text, product_id)

if __name__ == '__main__':
    main()
