from flask import Flask, render_template, request, abort, url_for
import random
from datetime import datetime, timedelta
import mysql.connector
import decimal
import math

# 确保这里的 name 是 '__main__' 的字符串形式
app = Flask(__name__)

# --- 数据库配置 ---
# 请确保您的数据库信息正确无误
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'YDS190410',  # 请替换为您的数据库密码
    'database': 'program_structure_web',
}


# --- 辅助函数：生成评论占位符 ---
def generate_review_placeholders(item_name):
    """为商品名称生成随机的好评和差评占位符"""
    good_reviews_templates = [
        f"{item_name} 很好用，超出预期！", "值得购买。", f"设计不错。",
        "物流很快。", f"用了几天，非常满意。"
    ]
    bad_reviews_templates = [
        f"{item_name} 的某个小地方可以改进。", "包装一般。",
        "价格有点高。", "说明书可以更详细些。"
    ]
    return {
        "good_reviews": random.sample(good_reviews_templates, k=min(2, len(good_reviews_templates))),
        "bad_reviews": random.sample(bad_reviews_templates, k=min(2, len(bad_reviews_templates)))
    }


# --- 核心函数：从数据库获取并处理数据 ---
def fetch_data_from_db():
    """连接数据库，查询所有商品数据，并进行处理和计算"""

    # ---【新增】定义一个清理函数，移除所有控制字符 ---
    def clean_string(s):
        if s is None:
            return None
        # 移除换行、回车、制表符等，并去除首尾空格
        # 使用 repr() 来处理更复杂的控制字符，然后去掉首尾的单引号
        return str(s).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()

    items = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT
            wf.product_id, wf.title, wf.price, wf.sales, wf.shop_name,
            wf.pos1, wf.pos2, wf.pos3, wf.neg1, wf.neg2, wf.neg3,
            wf.signal_score, wf.performance, wf.stability, wf.usability,
            wf.hardware, wf.service, wf.cost_effectiveness,
            wi.*
        FROM 
            wifi_final AS wf
        LEFT JOIN 
            wifi_intro AS wi ON wf.product_id = wi.product_id
        """
        cursor.execute(query)
        db_items = cursor.fetchall()

        for row in db_items:
            item_id = row.get('product_id')
            if not item_id:
                continue

            # ---【核心修改】对所有可能包含控制字符的文本字段进行清理 ---
            item_name_cleaned = clean_string(row.get('title'))
            review_placeholders = generate_review_placeholders(item_name_cleaned)

            db_reviews_list = [
                row.get('pos1'), row.get('pos2'), row.get('pos3'),
                row.get('neg1'), row.get('neg2'), row.get('neg3')
            ]
            actual_db_reviews = [clean_string(review) for review in db_reviews_list if review and clean_string(review)]

            # 分数计算
            spec_scores_to_sum = [
                row.get('signal_score'), row.get('performance'), row.get('stability'),
                row.get('usability'), row.get('hardware'),
            ]
            review_scores_to_sum = [row.get('service'), row.get('cost_effectiveness')]

            valid_review_scores = [float(s) for s in review_scores_to_sum if s is not None]
            review_score_avg = sum(valid_review_scores) / len(valid_review_scores) if valid_review_scores else 0.0

            valid_spec_scores = [float(s) for s in spec_scores_to_sum if s is not None]
            spec_score_avg = sum(valid_spec_scores) / len(valid_spec_scores) if valid_spec_scores else 0.0

            # 数据清洗
            try:
                price_str = row.get('price')
                price = float(''.join(filter(lambda x: x.isdigit() or x == '.', str(price_str)))) if price_str else 0.0
            except (ValueError, TypeError):
                price = 0.0

            db_features_list = []
            if row.get('无线协议') and row.get('无线协议') not in ['无', None, '']:
                db_features_list.append(f"无线协议: {clean_string(row.get('无线协议'))}")
            if row.get('防火墙') and row.get('防火墙') not in ['不支持防火墙', '无', None, '']:
                db_features_list.append(f"防火墙: {clean_string(row.get('防火墙'))}")

            category_cleaned = clean_string(row.get('类型')) if clean_string(row.get('类型')) else clean_string(
                row.get('类别'))

            # 将所有需要展示的字段都添加到字典中
            items.append({
                # 基本信息
                "id": item_id,
                "name": item_name_cleaned,
                "price": price,
                "spec_score": round(spec_score_avg, 2),
                "review_score": round(review_score_avg, 2),
                "brand": clean_string(row.get('品牌')),
                "category": category_cleaned,
                "model": clean_string(row.get('型号')),
                "release_date": clean_string(row.get('上市时间')),

                # 物理规格
                "dimensions": clean_string(row.get('产品尺寸')),
                "weight": row.get('产品净重（kg）'),
                "material": clean_string(row.get('机身材质')),
                "cooling_method": clean_string(row.get('散热方式')),

                # 端口信息
                "lan_output": clean_string(row.get('LAN输出口')),
                "wan_input": clean_string(row.get('WAN接入口')),
                "lan_ports_count": row.get('LAN口数量'),
                "wan_ports_count": row.get('Wan口数量'),
                "lan_port_type": clean_string(row.get('LAN口类型')),
                "wan_port_type": clean_string(row.get('WAN口类型')),
                "other_ports": clean_string(row.get('其他端口')),
                "has_usb": clean_string(row.get('是否带USB')),

                # 无线性能
                "wireless_protocol": clean_string(row.get('无线协议')),
                "wireless_rate": clean_string(row.get('无线速率')),
                "frequency_band": clean_string(row.get('适用频段')),
                "antenna": clean_string(row.get('天线')),
                "fem_amplifier": clean_string(row.get('FEM信号放大器')),
                "supports_mesh": clean_string(row.get('是否支持Mesh')),

                # 软件与服务
                "vpn_support": clean_string(row.get('企业VPN')),
                "firewall_support": clean_string(row.get('防火墙')),
                "app_control": clean_string(row.get('APP控制')),
                "behavior_management": clean_string(row.get('上网行为管理')),

                # 其他
                "applicable_area": clean_string(row.get('适用面积')),
                "capacity": clean_string(row.get('总带机量')),
                "power_supply": clean_string(row.get('供电方式')),
                "packaging_list": clean_string(row.get('packaging_list')),

                # 评论数据
                "db_reviews": actual_db_reviews,
                "good_reviews": review_placeholders['good_reviews'],
                "bad_reviews": review_placeholders['bad_reviews'],

                # 保留原始特性列表以防万一
                "features": db_features_list[:5],
            })

    except mysql.connector.Error as err:
        print(f"连接MySQL或获取数据时出错: {err}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

    return items


# --- 数据加载 ---
ITEM_DATA = fetch_data_from_db()
ITEMS_BY_ID = {item['id']: item for item in ITEM_DATA}


# --- Flask 路由 ---
@app.route('/')
def index():
    """主页路由，处理数据显示、排序和图表生成"""
    if not ITEM_DATA:
        return render_template('index.html',
                               ranked_items=[], current_sort_criteria="数据加载失败",
                               current_sort_key='spec_score', all_items_json="[]",
                               top_spec_chart_data={"labels": [], "scores": []},
                               top_review_chart_data={"labels": [], "scores": []},
                               price_distribution_chart_data={"labels": [], "counts": []},
                               error_message="无法从数据库加载商品数据，请检查后台服务和数据库连接。",
                               ranking_title="项目排行榜"
                               )

    # --- 图表数据生成 ---
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

    price_ranges_config = [
        (0, 29.99, "¥0-¥29"), (30, 59.99, "¥30-¥59"), (60, 99.99, "¥60-¥99"),
        (100, 149.99, "¥100-¥149"), (150, 199.99, "¥150-¥199"), (200, 249.99, "¥200-¥249"),
        (250, 299.99, "¥250-¥299"), (300, 399.99, "¥300-¥399"), (400, 499.99, "¥400-¥499"),
        (500, 699.99, "¥500-¥699"), (700, 999.99, "¥700-¥999"), (1000, 1499.99, "¥1000-¥1499"),
        (1500, 1999.99, "¥1500-¥1999"), (2000, 2499.99, "¥2000-¥2499"), (2500, 2999.99, "¥2500-¥2999"),
        (3000, 3999.99, "¥3000-¥3999"), (4000, float('inf'), "¥4000+")
    ]
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

    # --- 排序逻辑 ---
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
    """商品详情页路由"""
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        abort(404)
    back_url = url_for('index')
    return render_template('item_detail.html', item=item, back_url=back_url)


# --- 应用启动 ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)