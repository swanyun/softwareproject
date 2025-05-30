import os
import time
import csv
from playwright.sync_api import sync_playwright

CTX_STORAGE = "jd1.json"


def extract_product_info(item):
    product_id = item.get_attribute("data-sku") or "无ID"
    title_elem = item.query_selector(".p-name em")
    title = title_elem.inner_text().strip() if title_elem else "无标题"
    price_elem = item.query_selector(".p-price i")
    price = price_elem.inner_text().strip() if price_elem else "无价格"
    sales_elem = item.query_selector(".p-commit strong a")
    sales = sales_elem.inner_text().strip() if sales_elem else "无销量"
    shop_elem = item.query_selector(".p-shop a.hd-shopname")
    shop = shop_elem.inner_text().strip() if shop_elem else "无店铺"

    return {
        "商品ID": product_id,
        "标题": title,
        "价格": price,
        "销量": sales,
        "店铺名": shop,
    }


def main():
    search_url = "https://search.jd.com/Search?keyword=无线千兆路由器"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = None

        # 登录处理
        if os.path.exists(CTX_STORAGE):
            print("加载已保存的登录状态...")
            context = browser.new_context(storage_state=CTX_STORAGE)
        else:
            print("首次运行，请手动登录京东账户...")
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://passport.jd.com/new/login.aspx")
            print("请手动扫码或输入账号密码登录...")
            input("登录完成后请按回车继续...")
            context.storage_state(path=CTX_STORAGE)
            print("登录状态已保存。")
            page.close()

        # 打开搜索页面
        page = context.new_page()
        page.goto(search_url, wait_until="load")

        time.sleep(5)  # 等页面加载（可根据网速调整）
        all_results = []

        for page_index in range(100):  # 爬取3页
            print(f"开始爬取第 {page_index + 1} 页")


            page.wait_for_selector(".gl-item", timeout=15000)
            items = page.query_selector_all(".gl-item")
            print(f"找到 {len(items)} 个商品")

            for item in items:
                info = extract_product_info(item)
                print(info)
                all_results.append(info)

             # 模拟右方向键翻页
            print("按右方向键翻页...")
            page.keyboard.press("ArrowRight")
            time.sleep(3)  # 等待页面跳转（点击后的加载）

            # 刷新页面
            page.reload()
            try:
                page.wait_for_selector(".gl-item", timeout=30000)
                time.sleep(2)  # 页面动画加载
            except Exception as e:
                print(f"第 {i + 1} 页后加载超时: {e}")
                break


        browser.close()

        # 保存CSV
        if all_results:
            keys = all_results[0].keys()
            with open('jd_products.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(all_results)

            print("数据已保存到 jd_products.csv")


if __name__ == "__main__":
    main()
