import pandas as pd
from sqlalchemy import create_engine

def deduplicate_columns(columns):
    counts = {}
    new_cols = []
    for col in columns:
        if col not in counts:
            counts[col] = 0
            new_cols.append(col)
        else:
            counts[col] += 1
            new_cols.append(f"{col}.{counts[col]}")
    return new_cols

# 数据库连接字符串（SQLAlchemy）
db_url = "mysql+mysqlconnector://root:123456@localhost/WIFISHOP_database"
engine = create_engine(db_url)

def create_engine_and_save(df, table_name):
    df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
    print(f"✅ 成功保存表：{table_name}")

def main():
    # 1. 读取 WIFI_INTRO
    query_intro = """
    SELECT *
    FROM jd_products AS jp
    RIGHT JOIN shop_items AS si ON jp.product_id = si.`商品编号`
    """
    df_intro = pd.read_sql(query_intro, engine)
    print(f"WIFI_INTRO 数据形状: {df_intro.shape}")
    create_engine_and_save(df_intro, 'wifi_intro')

    # 2. 读取 WIFI_FINAL
    query_final = """
    SELECT *
    FROM jd_products AS jp
    RIGHT JOIN sample_reviews AS sr ON jp.product_id = sr.product_id
    RIGHT JOIN keywords_frequency AS kf ON sr.product_id = kf.id
    RIGHT JOIN scores AS sc ON kf.id = sc.id
    RIGHT JOIN jdgoodshop1 AS js ON sc.id = js.`商品编号`
    """
    df_final = pd.read_sql(query_final, engine)
    print(f"最终数据表形状: {df_final.shape}")

    # 去重列名
    df_final.columns = deduplicate_columns(df_final.columns)

    # 删除重复主键列，只保留 product_id
    right_primary_keys = ['商品编号', '商品编号.1', '商品编号.2', 'id', 'id.1', 'id.2', 'product_id.1', 'product_id.2']
    cols_to_drop = [col for col in df_final.columns if col in right_primary_keys and col != 'product_id']
    df_final.drop(columns=cols_to_drop, inplace=True)

    create_engine_and_save(df_final, 'wifi_final')

if __name__ == "__main__":
    main()
