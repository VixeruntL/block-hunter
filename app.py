import streamlit as st
import requests
from google_play_scraper import search
import pandas as pd
from datetime import datetime

# 页面基础配置
st.set_page_config(page_title="全球手游搜索雷达", layout="wide", page_icon="🔍")

st.title("🌐 全球应用商店实时搜索工具")
st.caption("支持任何品类、任何关键词的 Top 结果抓取 (iOS & Android)")

# 侧边栏：通用配置
with st.sidebar:
    st.header("⚙️ 搜索设置")
    target_keyword = st.text_input("🎯 输入关键词", "block blast")
    country_code = st.selectbox("🌍 选择国家/地区代码", ["us", "cn", "jp", "kr", "gb", "de", "fr"], index=0)
    limit_val = st.slider("🔢 抓取数量", 10, 200, 50)
    st.divider()
    st.info("提示：此工具将直接返回商店当前搜索排序下的前 N 个结果。")

# 核心功能：iOS 抓取
def fetch_ios_data(kw, cc, limit):
    # App Store API
    url = f"https://itunes.apple.com/search?term={kw}&entity=software&country={cc}&limit={limit}"
    try:
        res = requests.get(url, timeout=15).json()
        results = res.get('results', [])
        data = []
        for i, item in enumerate(results):
            data.append({
                "排名": i + 1,
                "应用名称": item.get('trackName'),
                "开发者": item.get('artistName'),
                "主分类": item.get('primaryGenreName'),
                "评分": round(item.get('averageUserRating', 0), 1),
                "链接": item.get('trackViewUrl')
            })
        return data
    except Exception as e:
        st.error(f"iOS 抓取失败: {e}")
        return []

# 核心功能：Android 抓取
def fetch_gp_data(kw, cc, limit):
    try:
        # Google Play 抓取
        results = search(kw, lang="en", country=cc, n_hits=limit)
        data = []
        for i, item in enumerate(results):
            data.append({
                "排名": i + 1,
                "应用名称": item.get('title'),
                "开发者": item.get('developer'),
                "评分": round(item.get('score', 0), 1),
                "包名/ID": item.get('appId'),
                "链接": f"https://play.google.com/store/apps/details?id={item.get('appId')}"
            })
        return data
    except Exception as e:
        st.error(f"Android 抓取失败: {e}")
        return []

# 主界面：点击按钮开始
if st.button("🚀 开始全球全量检索", type="primary"):
    if not target_keyword:
        st.warning("请先输入关键词！")
    else:
        t1, t2 = st.tabs(["🍎 App Store (iOS)", "🤖 Google Play (Android)"])
        
        with st.spinner(f'正在检索 "{target_keyword}" 的实时数据...'):
            ios_list = fetch_ios_data(target_keyword, country_code, limit_val)
            gp_list = fetch_gp_data(target_keyword, country_code, limit_val)
            
            # 展示 iOS 数据
            with t1:
                if ios_list:
                    df_ios = pd.DataFrame(ios_list)
                    st.success(f"iOS 结果: 找到 {len(df_ios)} 条")
                    st.dataframe(df_ios, column_config={"链接": st.column_config.LinkColumn("跳转链接")}, use_container_width=True, hide_index=True)
                    # 导出按钮
                    csv_ios = df_ios.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 导出 iOS
