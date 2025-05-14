from flask import Flask, render_template, request, abort, url_for
import random
from datetime import datetime, timedelta

app = Flask(__name__)


# --- 数据生成 ---
def generate_data(num_items=10):
    items = []
    base_names = ["探索者", "领航者", "守护者", "创新者", "先锋者", "梦想家", "开拓者", "智慧星", "动力核", "光影梭"]
    adjectives = ["超级", "迷你", "专业版", "青春版", "旗舰", "经典款", "升级版", "智能", "环保", "限量"]
    brands = ["未来科技", "先锋电子", "创新工坊", "梦想智造", "极速动力"]
    categories = ["智能设备", "高效工具", "生活助手", "创意配件", "专业装备"]
    colors = ["深空灰", "月光银", "星际蓝", "熔岩红", "森林绿", "曜石黑"]
    materials = ["航空铝合金", "碳纤维复合材料", "高强度聚碳酸酯", "亲肤硅胶", "强化玻璃"]

    used_names = set()
    # item_ids = {} # 这个变量在后续代码中没有被有效使用，可以考虑移除或正确使用

    for i in range(num_items):
        item_id = f"item_{i + 1:03d}"
        while True:
            name_part1 = random.choice(base_names)
            name_part2 = random.choice(adjectives)
            name = f"{name_part1}{name_part2} {random.randint(10, 99)}"
            if name not in used_names:
                used_names.add(name)
                # item_ids[name] = item_id # 如果 ITEM_ID_MAP 未被使用，这行也可以注释掉
                break

        price = random.randint(500, 10000)
        spec_score = round(random.uniform(6.0, 9.9), 1)
        review_score = round(random.uniform(3.5, 5.0), 1)

        # 详细数据
        brand = random.choice(brands)
        category = random.choice(categories)
        release_date = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
        dimensions = f"{random.randint(5, 20)}cm x {random.randint(3, 15)}cm x {random.randint(1, 5)}cm"
        weight = f"{random.randint(100, 2000)}g"
        color_options = random.sample(colors, k=random.randint(2, 4))
        material = random.choice(materials)

        base_features = [
            "超长续航电池", "高清显示屏", "快速充电技术", "AI智能助手", "多重安全防护",
            "人体工学设计", "防水防尘", "轻巧便携", "高速数据传输", "模块化扩展"
        ]
        features = random.sample(base_features, k=random.randint(3, 5))

        description = (
            f"隆重推出 {name}，一款由 {brand} 精心打造的{category}。它采用了先进的{material}材质，"
            f"结合了{', '.join(features[:2])}等尖端技术。无论是日常使用还是专业场景，"
            f"{name} 都能提供无与伦比的体验。现在就拥有它，开启您的全新数字生活！"
            f"我们致力于提供最优质的产品和服务，{name} 经过严格的质量检测，确保耐用性和可靠性。"
            f"提供多种颜色选择：{', '.join(color_options)}。"
        )
        stock_status = random.choice(["库存充足", "少量库存", "预售中", "暂时缺货"])

        good_reviews = [
            f"{name}真是太棒了，性能超出预期！尤其是{random.choice(features)}功能，非常实用。",
            "物超所值，强烈推荐购买。",
            f"设计精美，手感一流。{material}材质感觉很高档。",
            "客服服务态度很好，物流也很快。",
            f"用了几天了，非常满意，功能齐全。特别是{random.choice(colors)}颜色，太好看了！"
        ]
        bad_reviews = [
            f"{name}的{random.choice(features)}功能有时不太稳定，希望能改进。",
            "包装有点简陋，差点以为是二手货。",
            "价格略高，期待后续有优惠。",
            "说明书不够详细，上手有点困难。",
            f"电池续航一般，官方宣称的超长续航有点夸张了，需要一天一充。"
        ]

        items.append({
            "id": item_id,
            "name": name,
            "price": price,
            "spec_score": spec_score,
            "review_score": review_score,
            "brand": brand,
            "category": category,
            "release_date": release_date,
            "dimensions": dimensions,
            "weight": weight,
            "color_options": color_options,
            "material": material,
            "features": features,
            "description": description,
            "stock_status": stock_status,
            "good_reviews": random.sample(good_reviews, k=min(5, len(good_reviews))),
            "bad_reviews": random.sample(bad_reviews, k=min(5, len(bad_reviews)))
        })
    # generate_data 现在只返回 items 列表，因为 item_ids (以及 ITEM_ID_MAP) 似乎没有被使用
    return items


ITEM_DATA = generate_data(10)  # generate_data 现在只返回一个值
ITEMS_BY_ID = {item['id']: item for item in ITEM_DATA}


@app.route('/')
def index():  # 这是保留的第一个 index 函数
    item_names = [item['name'] for item in ITEM_DATA]
    prices = [item['price'] for item in ITEM_DATA]
    spec_scores = [item['spec_score'] for item in ITEM_DATA]
    review_scores = [item['review_score'] for item in ITEM_DATA]

    sort_by = request.args.get('sort_by', 'spec_score')  # 默认按规格评分排序

    # 为排行榜中的项目添加详情页链接
    items_for_ranking = [{**item, 'detail_url': url_for('item_detail', item_id=item['id'])} for item in ITEM_DATA]

    if sort_by == 'review_score':
        ranked_items = sorted(items_for_ranking, key=lambda x: x['review_score'], reverse=True)
        current_sort_criteria = "评论评分"
    elif sort_by == 'price_asc':
        ranked_items = sorted(items_for_ranking, key=lambda x: x['price'])
        current_sort_criteria = "价格 (低到高)"
    elif sort_by == 'price_desc':
        ranked_items = sorted(items_for_ranking, key=lambda x: x['price'], reverse=True)
        current_sort_criteria = "价格 (高到低)"
    else:  # 默认或spec_score
        ranked_items = sorted(items_for_ranking, key=lambda x: x['spec_score'], reverse=True)
        current_sort_criteria = "规格评分"
        sort_by = 'spec_score'  # 确保默认值正确传递

    return render_template('index.html',
                           item_names=item_names,
                           prices=prices,
                           spec_scores=spec_scores,
                           review_scores=review_scores,
                           ranked_items=ranked_items,
                           current_sort_criteria=current_sort_criteria,
                           current_sort_key=sort_by,
                           all_items_json=ITEM_DATA  # 传递所有数据给JS，用于图表或未来的动态更新
                           )


# 新的路由，用于展示商品详情页A (这个函数需要被定义)
@app.route('/item/<item_id>')
def item_detail(item_id):
    item = ITEMS_BY_ID.get(item_id)
    if not item:
        abort(404)  # 如果找不到项目，返回404错误

    back_url = url_for('index')  # 固定返回主页

    return render_template('item_detail.html', item=item, back_url=back_url)


# 第二个 index 函数已被删除

if __name__ == '__main__':
    # 监听所有公共 IP 地址，端口号 8888
    app.run(host='0.0.0.0', port=8888, debug=True)