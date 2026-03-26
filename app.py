import streamlit as st
import requests
from google_play_scraper import search
import pandas as pd

# 页面基础配置
st.set_page_config(page_title="Block排名调研", layout="wide")
st.title("📊 Block 关键词排名调研 (Top 200)")

# 侧边栏
st.sidebar.header("🔍 搜索配置")
target_keyword = st.sidebar.text_input("输入关键词", "block blast")
country_code = st.sidebar.selectbox("选择市场", ["us", "gb", "jp", "kr", "cn"], index=0)
limit_val = st.sidebar.slider("抓取数量", 20, 200, 100)

def fetch_ios(kw, cc, limit):
    url = f"https://itunes.apple.com/search?term={kw}&entity=software&country={cc}&limit={limit}"
    try:
        res = requests.get(url, timeout=15).json()
        results = res.get('results', [])
        return [{"排名": i+1, "游戏名称": item.get('trackName'), "开发者": item.get('artistName'), "评分": item.get('averageUserRating'), "链接": item.get('trackViewUrl')} for i, item in enumerate(results)]
    except:
        return []

def fetch_gp(kw, cc, limit):
    try:
        results = search(kw, lang="en", country=cc, n_hits=limit)
        return [{"排名": i+1, "游戏名称": item.get('title'), "开发者": item.get('developer'), "评分": item.get('score'), "链接": f"https://play.google.com/store/apps/details?id={item.get('appId')}"} for i, item in enumerate(results)]
    except:
        return []

# 主执行逻辑
if st.button("🚀 开始扫描排名", type="primary"):
    t1, t2 = st.tabs(["🍎 iOS 排行", "🤖 Android 排行"])
    
    with st.spinner('正在同步双端数据...'):
        ios_data = fetch_ios(target_keyword, country_code, limit_val)
        gp_data = fetch_gp(target_keyword, country_code, limit_val)
        
        with t1:
            if ios_data:
                st.dataframe(pd.DataFrame(ios_data), use_container_width=True, hide_index=True)
            else:
                st.warning("未找到 iOS 数据")
                
        with t2:
            if gp_data:
                st.dataframe(pd.DataFrame(gp_data), use_container_width=True, hide_index=True)
            else:
                st.warning("未找到 Android 数据")

st.info("💡 如果数据刷不出来，请检查关键词是否包含特殊符号，或尝试切换市场。")
