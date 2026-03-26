import streamlit as st
import requests
from google_play_scraper import search
import pandas as pd

st.set_page_config(page_title="Block 关键词竞品调研", layout="wide")
st.title("📊 Block 关键词搜索排名 Top 200 (iOS & Android)")

# 侧边栏设置
st.sidebar.header("🔍 搜索配置")
target_keyword = st.sidebar.text_input("目标关键词", "block blast")
country = st.sidebar.selectbox("目标市场", ["us", "gb", "jp", "kr", "cn"], index=0)
limit_count = st.sidebar.slider("抓取数量 (最大200)", 20, 200, 100)

def get_ios_top_200(keyword, country, limit):
    # App Store 搜索 API 默认最大返回 200 条
    url = f"https://itunes.apple.com/search?term={keyword}&entity=software&country={country}&limit={limit}"
    try:
        res = requests.get(url, timeout=15).json()
        results = res.get('results', [])
        data = []
        for i, item in enumerate(results):
            data.append({
                "排名": i + 1,
                "游戏名称": item.get('trackName'),
                "开发者": item.get('artistName'),
                "评分": round(item.get('averageUserRating', 0), 1),
                "评分数": item.get('userRatingCount', 0),
                "链接": item.get('trackViewUrl')
            })
        return data
    except:
        return []

def get_gp_top_200(keyword, country, limit):
    try:
        # google-play-scraper 的 search 方法支持 n_hits 参数
        # 注意：Google Play 搜索结果受算法限制，有时即便设为200也只能返回 100-150 条左右
        results = search(
            keyword,
            lang="en", # 语言统一用英文
            country=country,
            n_hits=limit
        )
        data = []
        for i, item in enumerate(results):
            data.append({
                "排名": i + 1,
                "游戏名称": item.get('title'),
                "开发者": item.get('developer'),
                "评分": round(item.get('score', 0), 1),
                "应用ID": item.get('appId'),
                "链接": f"https://play.google.com/store/apps/details?id={item.get('appId')}"
            })
        return data
    except:
        return []

# 主逻辑
if st.button("🚀 开始扫描 Top 200", type="primary"):
    tab1, tab2 = st.tabs(["🍎 App Store (iOS)", "🤖 Google Play (Android)"])
    
    with st.spinner(f'正在检索 "{target_keyword}" 在 {country.upper()} 市场的排名...'):
        # 抓取数据
        ios_list = get_ios_top_200(target_keyword, country, limit_count)
        gp_list = get_gp_top_200(target_keyword, country, limit_count)
        
        with tab1:
            if ios_list:
                df_ios = pd.DataFrame(ios_list)
                st.success(f"已找到 {len(df_ios)} 款 iOS 产品")
                st.dataframe(df_ios, column_config={"链接": st.column_config.LinkColumn()}, use_container_width=True, hide_index=True)
                csv_ios = df_ios.to_csv(index=False).encode('utf-8')
                st.download_button("📥 下载 iOS 排名报告", data=csv_ios, file_name=f
