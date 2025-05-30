import os
import glob
import mysql.connector
from mysql.connector import errorcode
import pandas as pd

# —— 一、初始连接配置（不指定 database） ——
db_cfg = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': '123456',
    # 不在这里指定 'database'
    'charset':  'utf8mb4'
}

# 要创建的数据库名
DB_NAME = 'WIFISHOP_database'

# 数据文件目录
#商品详情
txt_dir_path = r"D:\test\wifi_ev\mysql_resource\shop"
#商品好评率
txt_dir_path2 = r"D:\test\wifi_ev\mysql_resource\jdgoodshop1"
#商品介绍
csv_file_path = r"D:\test\wifi_ev\mysql_resource\jd_products.csv"
#keywords
csv_file_path1 = r"D:\test\wifi_ev\mysql_resource\keywords.csv"
#scores
csv_file_path2 = r"D:\test\wifi_ev\mysql_resource\scores.csv"
#sampled_reviews
csv_file_path3 = r"D:\test\wifi_ev\mysql_resource\sampled_reviews.csv"


def get_existing_columns(cursor, table_name):
    """
    从目标表中读取已存在的列名，返回一个集合
    """
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
    return {row[0] for row in cursor.fetchall()}

def connect_db(cfg):
    """
    根据配置连接 MySQL 并返回连接对象
    """
    return mysql.connector.connect(**cfg)




def main():
    # —— 一、连接到 MySQL（不指定数据库） ——
    try:
        conn = mysql.connector.connect(**db_cfg)
        cursor = conn.cursor()
        print("✔ 初始连接成功（未指定数据库）")
    except mysql.connector.Error as err:
        print(f"❌ 连接失败: {err}")
        exit(1)

    # —— 二、创建数据库 if not exists ——
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        print(f"✔ 数据库 `{DB_NAME}` 已创建或已存在")
        cursor.execute(f"USE {DB_NAME};")
    except mysql.connector.Error as err:
        print(f"❌ 创建数据库失败: {err}")
        cursor.close()
        conn.close()
        exit(1)

    # MySQL对应数据库中建表-------------------------------------------------------------------------------------------------------------------

    # —— 创建表 shop_items ——
    create_table_sql_shop_items = """
    CREATE TABLE IF NOT EXISTS `shop_items` (
      `商品编号` VARCHAR(64) PRIMARY KEY,
      `品牌`        VARCHAR(128),
      `散热方式`    VARCHAR(64),
      `类型`        VARCHAR(64),
      `企业VPN`     VARCHAR(64),
      `LAN输出口`   VARCHAR(64),
      `机身材质`    VARCHAR(64),
      `天线`        VARCHAR(64),
      `WAN接入口`   VARCHAR(64),
      `WAN口类型`   VARCHAR(64),
      `其他端口`    VARCHAR(64),
      `总带机量`    VARCHAR(64),
      `适用面积`    VARCHAR(64),
      `无线协议`    VARCHAR(64),
      `AP管理`      VARCHAR(64),
      `上网行为管理` VARCHAR(64),
      `LAN口类型`   VARCHAR(64),
      `无线速率`    VARCHAR(64),
      `VPN类型`     VARCHAR(128),
      `防火墙`      VARCHAR(64),
      `LAN口数量`   VARCHAR(64),
      `适用频段`    VARCHAR(128),
      `产品尺寸`    VARCHAR(128),
      `产品净重（kg）` VARCHAR(64),
      `认证型号`    VARCHAR(64),
      `包装清单`    TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        cursor.execute(create_table_sql_shop_items)
        conn.commit()
        print("✔ 表 `shop_items` 已创建或已存在")
    except mysql.connector.Error as err:
        print(f"❌ 创建表 `shop_items` 失败: {err}")





    # —— 创建表 jdgoodshop1 ——
    create_table_sql_jdgoodshop1 = """
    CREATE TABLE IF NOT EXISTS `jdgoodshop1` (
    `商品编号` VARCHAR(64) PRIMARY KEY,
    `好评率字段` VARCHAR(64)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        cursor.execute(create_table_sql_jdgoodshop1)
        conn.commit()
        print("✔ 表 `jdgoodshop1` 已创建或已存在")
    except mysql.connector.Error as err:
        print(f"❌ 创建表 `jdgoodshop1` 失败: {err}")















    # —— 创建表 jd_products ——
    create_table_sql_jd_products = '''
    CREATE TABLE IF NOT EXISTS `jd_products` (
        product_id VARCHAR(20) PRIMARY KEY,
        title VARCHAR(255),
        price VARCHAR(20),
        sales VARCHAR(20),
        shop_name VARCHAR(40)
    );
    '''
    try:
        cursor.execute(create_table_sql_jd_products)
        conn.commit()
        print("✔ 表 `jd_products` 已创建或已存在")
    except mysql.connector.Error as err:
        print(f"❌ 创建表 `jd_products` 失败: {err}")

    # —— 创建表 keywords ——
    create_table_sql_keywords_frequency = '''
    CREATE TABLE IF NOT EXISTS `keywords_frequency` (
    id VARCHAR(50) PRIMARY KEY ,
    keyword1 VARCHAR(100), frequency1 VARCHAR(20),
keyword2 VARCHAR(100), frequency2 VARCHAR(20),
keyword3 VARCHAR(100), frequency3 VARCHAR(20),
keyword4 VARCHAR(100), frequency4 VARCHAR(20),
keyword5 VARCHAR(100), frequency5 VARCHAR(20),
keyword6 VARCHAR(100), frequency6 VARCHAR(20),
keyword7 VARCHAR(100), frequency7 VARCHAR(20),
keyword8 VARCHAR(100), frequency8 VARCHAR(20),
keyword9 VARCHAR(100), frequency9 VARCHAR(20),
keyword10 VARCHAR(100), frequency10 VARCHAR(20),
keyword11 VARCHAR(100), frequency11 VARCHAR(20),
keyword12 VARCHAR(100), frequency12 VARCHAR(20),
keyword13 VARCHAR(100), frequency13 VARCHAR(20),
keyword14 VARCHAR(100), frequency14 VARCHAR(20),
keyword15 VARCHAR(100), frequency15 VARCHAR(20),
keyword16 VARCHAR(100), frequency16 VARCHAR(20),
keyword17 VARCHAR(100), frequency17 VARCHAR(20),
keyword18 VARCHAR(100), frequency18 VARCHAR(20),
keyword19 VARCHAR(100), frequency19 VARCHAR(20),
keyword20 VARCHAR(100), frequency20 VARCHAR(20),
keyword21 VARCHAR(100), frequency21 VARCHAR(20),
keyword22 VARCHAR(100), frequency22 VARCHAR(20),
keyword23 VARCHAR(100), frequency23 VARCHAR(20),
keyword24 VARCHAR(100), frequency24 VARCHAR(20),
keyword25 VARCHAR(100), frequency25 VARCHAR(20),
keyword26 VARCHAR(100), frequency26 VARCHAR(20),
keyword27 VARCHAR(100), frequency27 VARCHAR(20),
keyword28 VARCHAR(100), frequency28 VARCHAR(20),
keyword29 VARCHAR(100), frequency29 VARCHAR(20),
keyword30 VARCHAR(100), frequency30 VARCHAR(20),
keyword31 VARCHAR(100), frequency31 VARCHAR(20),
keyword32 VARCHAR(100), frequency32 VARCHAR(20),
keyword33 VARCHAR(100), frequency33 VARCHAR(20),
keyword34 VARCHAR(100), frequency34 VARCHAR(20),
keyword35 VARCHAR(100), frequency35 VARCHAR(20),
keyword36 VARCHAR(100), frequency36 VARCHAR(20),
keyword37 VARCHAR(100), frequency37 VARCHAR(20),
keyword38 VARCHAR(100), frequency38 VARCHAR(20),
keyword39 VARCHAR(100), frequency39 VARCHAR(20),
keyword40 VARCHAR(100), frequency40 VARCHAR(20),
keyword41 VARCHAR(100), frequency41 VARCHAR(20),
keyword42 VARCHAR(100), frequency42 VARCHAR(20),
keyword43 VARCHAR(100), frequency43 VARCHAR(20),
keyword44 VARCHAR(100), frequency44 VARCHAR(20),
keyword45 VARCHAR(100), frequency45 VARCHAR(20),
keyword46 VARCHAR(100), frequency46 VARCHAR(20),
keyword47 VARCHAR(100), frequency47 VARCHAR(20),
keyword48 VARCHAR(100), frequency48 VARCHAR(20),
keyword49 VARCHAR(100), frequency49 VARCHAR(20),
keyword50 VARCHAR(100), frequency50 VARCHAR(20)
);
'''
    try:
        cursor.execute(create_table_sql_keywords_frequency)
        conn.commit()
        print("✔ 表 `keywords_frequency` 已创建或已存在")
    except mysql.connector.Error as err:
        print(f"❌ 创建表 `keywords_frequency` 失败: {err}")











    # —— 创建表 scores ——评论关键词（id 为字符串类型）
    create_table_sql_scores = """
    CREATE TABLE IF NOT EXISTS `scores` (
id VARCHAR(50) PRIMARY KEY,
signal_score DOUBLE,
performance DOUBLE,
stability DOUBLE,
usability DOUBLE,
hardware DOUBLE,
service DOUBLE,
cost_effectiveness DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""
    try:
        cursor.execute(create_table_sql_scores)
        conn.commit()
        print("✔ 表 `scores` 已创建或已存在")
    except mysql.connector.Error as err:
        print(f"❌ 创建表 `scores` 失败: {err}")










        # —— 创建表 sample_reviews ——评分表
    create_table_sql_sample_reviews = '''
    CREATE TABLE IF NOT EXISTS `sample_reviews` 
(  
    product_id VARCHAR(50) PRIMARY KEY,
    pos1 VARCHAR(500),
    pos2 VARCHAR(500),
    pos3 VARCHAR(500),
    neg1 VARCHAR(500),
    neg2 VARCHAR(500),
    neg3 VARCHAR(500)
); 
'''
    try:
        cursor.execute(create_table_sql_sample_reviews)
        conn.commit()
        print("✔ 表 `sample_reviews` 已创建或已存在")
    except mysql.connector.Error as err:
        print(f"❌ 创建表 `sample_reviews` 失败: {err}")






    # 读取数据到MySQL-------------------------------------------------------------------------------------------------------------------















    # —— 五、读取txt文件并写入数据库 ——
    # 更新配置，指定刚创建的数据库
    db_cfg['database'] = DB_NAME
    conn = connect_db(db_cfg)
    cursor = conn.cursor()
    table_shop_items = 'shop_items'
    # 预先读取表中已存在的列
    existing_cols_shop_items = get_existing_columns(cursor, table_shop_items)

    # 遍历目录下所有 .txt 文件
    pattern = os.path.join(txt_dir_path, "*.txt")
    for filepath in glob.glob(pattern):
        product_id = os.path.splitext(os.path.basename(filepath))[0]

        # 读取文件并过滤空行
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        # 截取“商品详情”到“质量承诺”之间的属性内容
        try:
            start = lines.index("商品详情") + 1
            end   = lines.index("质量承诺")
            lines = lines[start:end]
        except ValueError:
            print(f"[WARN] 文件 {product_id} 缺少关键标志，跳过")
            continue

        # 将商品编号加入记录，并两两解析属性–值
        record = {"商品编号": product_id}
        i = 0
        while i + 1 < len(lines):
            record[lines[i]]   = lines[i + 1]
            i += 2

        # 动态检查并添加缺失的表字段
        missing = set(record.keys()) - existing_cols_shop_items
        for col in missing:
            sql_add = (
                f"ALTER TABLE `{table_shop_items}` "
                f"ADD COLUMN `{col}` VARCHAR(200) CHARACTER SET utf8mb4;"
            )
            try:
                cursor.execute(sql_add)
                existing_cols_shop_items.add(col)
                print(f"[INFO] 已添加缺失列 `{col}`")
            except mysql.connector.Error as e:
                print(f"[ERROR] 添加列 `{col}` 失败: {e}")

        # 构建 INSERT ... ON DUPLICATE KEY UPDATE 语句
        cols        = list(record.keys())
        placeholders = ",".join(["%s"] * len(cols))
        col_sql     = ",".join(f"`{c}`" for c in cols)
        update_sql  = ",".join(f"`{c}`=VALUES(`{c}`)" for c in cols)

        sql = (
            f"INSERT INTO `{table_shop_items}` ({col_sql}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_sql}"
        )

        # 执行写入或更新
        try:
            cursor.execute(sql, [record[c] for c in cols])
            print(f"[INFO] 商品编号 {product_id} 插入/更新成功")
        except mysql.connector.Error as e:
            print(f"[ERROR] 写入 {product_id} 失败：{e}")

    # 数据目录和表名
    txt_dir_path2 = r"D:\test\wifi_ev\mysql_resource\jdgoodshop1"
    table_jdgoodshop1 = 'jdgoodshop1'

    # 获取已有列（这里假设已有，如果需要动态添加列可参考之前代码）
    # 这里列固定，不做动态添加

    # 遍历目录下所有txt文件
    pattern = os.path.join(txt_dir_path2, "*.txt")

    for filepath in glob.glob(pattern):
        product_id = os.path.splitext(os.path.basename(filepath))[0]

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            print(f"[ERROR] 读取文件 {product_id} 失败: {e}")
            continue

        # 构建插入或更新语句
        insert_sql = f"""
        INSERT INTO `{table_jdgoodshop1}` (`商品编号`, `好评率字段`)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE `好评率字段`=VALUES(`好评率字段`);
        """

        try:
            cursor.execute(insert_sql, (product_id, content))
            conn.commit()
            print(f"[INFO] 商品编号 {product_id} 数据插入/更新成功")
        except mysql.connector.Error as err:
            print(f"[ERROR] 商品编号 {product_id} 写入失败: {err}")


    # —— 读取CSV文件并写入数据库 ——
    table_jd_products = 'jd_products'
    # 加载CSV文件
    try:
        data = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
    else:
        # 插入数据
        insert_query = '''
        INSERT INTO jd_products (product_id, title, price, sales, shop_name)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title),
            price=VALUES(price),
            sales=VALUES(sales),
            shop_name=VALUES(shop_name);
        '''
        # 批量插入数据
        for _, row in data.iterrows():
            values = (str(row['商品ID']), row['标题'], str(row['价格']), row['销量'], row['店铺名'])
            try:
                cursor.execute(insert_query, values)
                conn.commit()
                print(f"插入成功: {row['标题']}")
            except mysql.connector.Error as err:
                print(f"插入失败: {err}")

    table_keywords = 'keywords_frequency'

    try:
        data_keywords = pd.read_csv(csv_file_path1)
        print(f"✔ 成功读取 {csv_file_path1}")
    except Exception as e:
        print(f"❌ 读取 {csv_file_path1} 文件失败: {e}")
    else:
        # 数据库字段名（英文）
        keyword_fields = [f'keyword{i}' for i in range(1, 51)]
        frequency_fields = [f'frequency{i}' for i in range(1, 51)]
        all_fields = ['id'] + keyword_fields + frequency_fields

        fields_sql = ', '.join(all_fields)
        placeholders = ', '.join(['%s'] * len(all_fields))
        update_clause = ', '.join([f"{field}=VALUES({field})" for field in all_fields if field != 'id'])

        insert_sql = f'''
            INSERT INTO {table_keywords} ({fields_sql})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause};
        '''

        values_list = []
        for idx, row in data_keywords.iterrows():
            row_values = []

            # id 字段
            id_val = row.get('id', '')
            if pd.isna(id_val):
                id_val = ''
            row_values.append(str(id_val))

            # 关键词字段，CSV是中文“关键词1”，对应数据库英文keyword1
            for i in range(1, 51):
                kw = row.get(f'关键词{i}', '')
                if pd.isna(kw):
                    kw = ''
                row_values.append(str(kw))

            # 频率字段，CSV是中文“频率1”，对应数据库英文frequency1
            for i in range(1, 51):
                freq = row.get(f'频率{i}', '0')
                if pd.isna(freq):
                    freq = '0'
                try:
                    freq_val = str(int(float(freq)))
                except Exception:
                    freq_val = '0'
                row_values.append(freq_val)

            if idx < 3:
                print(f"第{idx}条插入数据预览:", row_values)

            values_list.append(tuple(row_values))

        try:
            cursor.executemany(insert_sql, values_list)
            conn.commit()
            print(f"✔ 批量插入 {len(values_list)} 条数据成功")
        except mysql.connector.Error as err:
            print(f"❌ 批量插入失败: {err}")









    # —— 读取 scores.csv 并清洗、批量插入 ——
    try:
        data_scores = pd.read_csv(csv_file_path2, dtype=str)  # 所有字段先读为字符串
        print("✔ 成功读取 scores.csv")
    except Exception as e:
        print(f"❌ 读取 scores.csv 文件失败: {e}")
    else:
        # 1. SQL 插入语句
        insert_query_scores = '''
                              INSERT INTO scores (id, signal_score, performance, stability, usability, hardware,
                                                  service, cost_effectiveness)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY \
                              UPDATE \
                                  signal_score = \
                              VALUES (signal_score), performance = \
                              VALUES (performance), stability = \
                              VALUES (stability), usability = \
                              VALUES (usability), hardware = \
                              VALUES (hardware), service = \
                              VALUES (service), cost_effectiveness = \
                              VALUES (cost_effectiveness); \
                              '''

        # 2. 构建插入列表：只对非 id 字段强制转 float
        values_list = []
        for _, row in data_scores.iterrows():
            try:
                id_value = str(row['id']).strip().lstrip("'")  # 保持 id 为字符串
                float_values = []
                for col in row.index:
                    if col != 'id':
                        val = row[col]
                        val = float(str(val).strip().lstrip("'")) if pd.notnull(val) else None
                        float_values.append(val)
                values_list.append((id_value, *float_values))
            except Exception as ex:
                print(f"⚠️ 数据格式错误: id={row.get('id')}, 错误: {ex}")

        # 3. 执行批量插入
        try:
            cursor.executemany(insert_query_scores, values_list)
            conn.commit()
            print(f"✅ 批量插入/更新成功，共 {len(values_list)} 条记录。")
        except mysql.connector.Error as err:
            print(f"❌ 批量插入失败: {err}")

    # —— 读取 sampled_reviews.csv 并写入数据库 ——
    table_sample_reviews = 'sample_reviews'

    # 加载CSV文件
    try:
        data_sample_reviews = pd.read_csv(csv_file_path3)
    except Exception as e:
        print(f"读取 sampled_reviews.csv 文件失败: {e}")
    else:
        # 插入数据
        insert_query_sample_reviews = '''
                                      INSERT INTO sample_reviews (product_id, pos1, pos2, pos3, neg1, neg2, neg3)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY \
                                      UPDATE \
                                          pos1= \
                                      VALUES (pos1), pos2= \
                                      VALUES (pos2), pos3= \
                                      VALUES (pos3), neg1= \
                                      VALUES (neg1), neg2= \
                                      VALUES (neg2), neg3= \
                                      VALUES (neg3); \
                                      '''
        # 批量插入数据
        for _, row in data_sample_reviews.iterrows():
            try:
                values = (
                    str(row['product_id']),
                    str(row.get('pos1', '') if not pd.isna(row.get('pos1', '')) else ''),
                    str(row.get('pos2', '') if not pd.isna(row.get('pos2', '')) else ''),
                    str(row.get('pos3', '') if not pd.isna(row.get('pos3', '')) else ''),
                    str(row.get('neg1', '') if not pd.isna(row.get('neg1', '')) else ''),
                    str(row.get('neg2', '') if not pd.isna(row.get('neg2', '')) else ''),
                    str(row.get('neg3', '') if not pd.isna(row.get('neg3', '')) else '')
                )
                cursor.execute(insert_query_sample_reviews, values)
                conn.commit()
                print(f"插入成功: product_id={row['product_id']}")
            except mysql.connector.Error as err:
                print(f"插入失败: product_id={row.get('product_id')}, 错误: {err}")

    # —— 七、关闭连接 ——
    conn.commit()
    cursor.close()
    conn.close()
    print("所有操作完成，数据库连接已关闭！")

if __name__ == '__main__':
    main()