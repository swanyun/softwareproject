from flask import Flask, render_template, request, abort, url_for
import random
from datetime import datetime, timedelta
import mysql.connector
import decimal
import math

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'YDS190410',
    'database': 'program_structure_web',
}


# ... (generate_review_placeholders 和 fetch_data_from_db 函数保持不变) ...
def generate_review_placeholders(item_name):
    good_reviews_templates = [
        f"{item_name} 很好用，超出预期！", "值得购买。", f"设计不错。",
        "物流很快。", f"用了几天，非常满意。"]
    bad_reviews_templates = [
        f"{item_name} 的某个小地方可以改进。", "包装一般。",
        "价格有点高。", "说明书可以更详细些。"]
    return {
        "good_reviews": random.sample(good_reviews_templates, k=min(2, len(good_reviews_templates))),
        "bad_reviews": random.sample(bad_reviews_templates, k=min(2, len(bad_reviews_templates)))
    }


def fetch_data_from_db():
    items = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                product_id, title, price, `品牌`, `类型`, `类别`, 
                `上市时间`, `产品尺寸`, `产品净重（kg）`, `机身材质`, `包装清单`,
                `散热方式`, `企业VPN`, `LAN输出口`, `天线`, `WAN接入口`, `无线协议`,
                `AP管理`, `上网行为管理`, `LAN口类型`, `无线速率`, `VPN类型`, `防火墙`,
                `LAN口数量`, `适用频段`, `是否带USB`, `FEM信号放大器`, `是否支持Mesh`,
                `游戏加速`, `供电方式`
            FROM itemlist
        """
        cursor.execute(query)
        db_items = cursor.fetchall()

        for row in db_items:
            item_id = row.get('product_id')
            item_name = row.get('title')
            review_placeholders = generate_review_placeholders(item_name)
            try:
                price_str = row.get('price')
                price = float(''.join(filter(lambda x: x.isdigit() or x == '.', str(price_str)))) if price_str else 0.0
            except (ValueError, TypeError):
                price = 0.0
            spec_score = round(random.uniform(6.0, 9.9), 1)
            review_score = round(random.uniform(3.5, 5.0), 1)
            db_features_list = []
            if row.get('无线协议') and row.get('无线协议') not in ['无', None, '']: db_features_list.append(
                f"无线协议: {row.get('无线协议')}")
            if row.get('防火墙') and row.get('防火墙') not in ['不支持防火墙', '无', None, '']: db_features_list.append(
                f"防火墙: {row.get('防火墙')}")
            category = row.get('类型') if row.get('类型') and row.get('类型') not in ['无', None, ''] else row.get(
                '类别')
            items.append({
                "id": item_id, "name": item_name, "price": price,
                "spec_score": spec_score, "review_score": review_score,
                "brand": row.get('品牌'), "category": category,
                "release_date": row.get('上市时间'), "dimensions": row.get('产品尺寸'),
                "weight": row.get('产品净重（kg）'), "material": row.get('机身材质'),
                "features": db_features_list[:5],
                "good_reviews": review_placeholders['good_reviews'],
                "bad_reviews": review_placeholders['bad_reviews'],
                "product_id_detail": row.get('product_id'), "packaging_list": row.get('包装清单'),
                "lan_output": row.get('LAN输出口'), "antenna": row.get('天线'),
                "wan_input": row.get('WAN接入口'), "power_supply": row.get('供电方式'),
                "lan_ports_count": row.get('LAN口数量'), "vpn_support": row.get('企业VPN'),
            })
    except mysql.connector.Error as err:
        print(f"连接MySQL或获取数据时出错: {err}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals() and cursor: cursor.close()
            conn.close()
    return items


ITEM_DATA = fetch_data_from_db()
ITEMS_BY_ID = {item['id']: item for item in ITEM_DATA}


@app.route('/')
def index():
    if not ITEM_DATA:
        return render_template('index.html',
                               ranked_items=[], current_sort_criteria="数据加载失败",
                               current_sort_key='spec_score', all_items_json="[]",
                               top_spec_chart_data={"labels": [], "scores": []},
                               top_review_chart_data={"labels": [], "scores": []},
                               price_distribution_chart_data={"labels": [], "counts": []},
                               error_message="无法从数据库加载商品数据。",
                               ranking_title="项目排行榜")

    top_spec_items = sorted(ITEM_DATA, key=lambda x: x.get('spec_score', 0), reverse=True)[:10]
    top_spec_chart_data = {
        "labels": [item.get('name', 'N/A')[:20] + '...' if item.get('name') and len(
            item.get('name', 'N/A')) > 20 else item.get('name', 'N/A') for item in top_spec_items],
        "scores": [item.get('spec_score', 0) for item in top_spec_items]
    }

    top_review_items = sorted(ITEM_DATA, key=lambda x: x.get('review_score', 0), reverse=True)[:10]
    top_review_chart_data = {
        "labels": [item.get('name', 'N/A')[:20] + '...' if item.get('name') and len(
            item.get('name', 'N/A')) > 20 else item.get('name', 'N/A') for item in top_review_items],
        "scores": [item.get('review_score', 0) for item in top_review_items]
    }

    # --- REVERTED PRICE RANGES to previous version (50 step, then larger) ---
    price_ranges_config = [
        (0, 29.99, "¥0-¥29"), (30, 59.99, "¥30-¥59"),  # Adjusted first two for finer grain at low end
        (60, 99.99, "¥60-¥99"), (100, 149.99, "¥100-¥149"),
        (150, 199.99, "¥150-¥199"), (200, 249.99, "¥200-¥249"),
        (250, 299.99, "¥250-¥299"), (300, 399.99, "¥300-¥399"),
        (400, 499.99, "¥400-¥499"), (500, 699.99, "¥500-¥699"),
        (700, 999.99, "¥700-¥999"), (1000, 1499.99, "¥1000-¥1499"),
        (1500, 1999.99, "¥1500-¥1999"), (2000, 2499.99, "¥2000-¥2499"),
        (2500, 2999.99, "¥2500-¥2999"), (3000, 3999.99, "¥3000-¥3999"),
        (4000, float('inf'), "¥4000+")
    ]
    # --- END OF REVERTED PRICE RANGES ---

    price_range_labels = [config[2] for config in price_ranges_config]
    price_distribution_counts = [0] * len(price_ranges_config)
    for item in ITEM_DATA:
        price = item.get('price')
        if price is None: continue
        for i, (low, high, _) in enumerate(price_ranges_config):
            if low <= price <= high:
                price_distribution_counts[i] += 1
                break
    price_distribution_chart_data = {
        "labels": price_range_labels,
        "counts": price_distribution_counts
    }

    sort_by = request.args.get('sort_by', 'spec_score')
    items_for_ranking_full = [{**item, 'detail_url': url_for('item_detail', item_id=item['id'])} for item in ITEM_DATA]

    if sort_by == 'review_score':
        sorted_full_list = sorted(items_for_ranking_full, key=lambda x: x.get('review_score', 0), reverse=True)
        current_sort_criteria = "评论评分"
    elif sort_by == 'price_asc':
        sorted_full_list = sorted(items_for_ranking_full, key=lambda x: x.get('price', float('inf')))
        current_sort_criteria = "价格 (低到高)"
    elif sort_by == 'price_desc':
        sorted_full_list = sorted(items_for_ranking_full, key=lambda x: x.get('price', float('-inf')), reverse=True)
        current_sort_criteria = "价格 (高到低)"
    elif sort_by == 'name_asc':
        sorted_full_list = sorted(items_for_ranking_full, key=lambda x: x.get('name', '').lower())
        current_sort_criteria = "名称 (A-Z)"
    elif sort_by == 'name_desc':
        sorted_full_list = sorted(items_for_ranking_full, key=lambda x: x.get('name', '').lower(), reverse=True)
        current_sort_criteria = "名称 (Z-A)"
    else:
        sorted_full_list = sorted(items_for_ranking_full, key=lambda x: x.get('spec_score', 0), reverse=True)
        current_sort_criteria = "规格评分"
        sort_by = 'spec_score'

    ranked_items = sorted_full_list[:50]
    ranking_title = "项目排行榜 (Top 50)"

    return render_template('index.html',
                           ranked_items=ranked_items,
                           current_sort_criteria=current_sort_criteria,
                           current_sort_key=sort_by,
                           all_items_json=ITEM_DATA,
                           top_spec_chart_data=top_spec_chart_data,
                           top_review_chart_data=top_review_chart_data,
                           price_distribution_chart_data=price_distribution_chart_data,
                           ranking_title=ranking_title
                           )


@app.route('/item/<item_id>')
def item_detail(item_id):
    item = ITEMS_BY_ID.get(item_id)
    if not item: abort(404)
    back_url = url_for('index')
    return render_template('item_detail.html', item=item, back_url=back_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)