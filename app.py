import streamlit as st
import requests
from google_play_scraper import search
import pandas as pd

# 页面基础配置
st.set_page_config(page_title="全球手游市场雷达", layout="wide")
st.title("🎮 全球手游市场情报工具")

# 侧边栏配置区
with st.sidebar:
    st.header("⚙️ 搜索配置")
    
    # 模式选择
    mode = st.radio(
        "选择查询模式",
        ["关键词搜索排名", "热门下载榜 (Free)", "畅销收入榜 (Grossing)", "最新上架 (New)"]
    )
    
    st.divider()
    
    target_kw = st.text_input("🎯 输入关键词", "block blast")
    country = st.selectbox("🌍 目标市场", ["us", "cn", "jp", "kr", "gb", "tw"], index=0)
    limit = st.slider("🔢 抓取数量", 10, 200, 50)

# --- 核心处理函数 ---

def fetch_ios(mode, kw, cc, n):
    # 根据模式选择不同的 App Store 接口
    if mode == "关键词搜索排名":
        url = f"https://itunes.apple.com/search?term={kw}&entity=software&country={cc}&limit={n}"
    elif mode == "热门下载榜 (Free)":
        url = f"https://itunes.apple.com/{cc}/rss/topfreeapplications/limit={n}/json"
    elif mode == "畅销收入榜 (Grossing)":
        url = f"https://itunes.apple.com/{cc}/rss/topgrossingapplications/limit={n}/json"
    else: # 最新上架
        url = f"https://itunes.apple.com/{cc}/rss/newapplications/limit={n}/json"
        
    try:
        res = requests.get(url, timeout=10).json()
        data = []
        
        # 处理搜索接口返回的格式
        if "results" in res:
            for i, item in enumerate(res['results']):
                data.append({
                    "排名": i + 1,
                    "应用名称": item.get('trackName'),
                    "开发者": item.get('artistName'),
                    "评分": item.get('averageUserRating'),
                    "链接": item.get('trackViewUrl')
                })
        # 处理 RSS 榜单接口返回的格式
        else:
            entries = res.get('feed', {}).get('entry', [])
            for i, item in enumerate(entries):
                data.append({
                    "排名": i + 1,
                    "应用名称": item.get('im:name', {}).get('label'),
                    "开发者": item.get('im:artist', {}).get('label'),
                    "分类": item.get('category', {}).get('attributes', {}).get('label'),
                    "链接": item.get('id', {}).get('label')
                })
        return data
    except:
        return []

def fetch_gp(mode, kw, cc, n):
    # Google Play 开源库主要支持搜索，榜单抓取受限
    # 这里我们通过关键词搜索模拟，如果是榜单模式，我们增加 "new" 或 "top" 关键词权重
    search_kw = kw
    if mode == "最新上架 (New)":
        search_kw = f"new {kw}"
    elif mode == "畅销收入榜 (Grossing)":
        search_kw = f"top {kw}"
        
    try:
        res = search(search_kw, lang="en", country=cc, n_hits=n)
        return [{
            "排名": i + 1, 
            "应用名称": item.get('title'), 
            "开发者": item.get('developer'), 
            "评分": item.get('score'), 
            "链接": f"https://play.google.com/store/apps/details?id={item.get('appId')}"
        } for i, item in enumerate(res)]
    except:
        return []

# --- 执行区 ---

if st.button("🚀 开始检索数据", type="primary"):
    st.subheader(f"📍 当前模式：{mode} ({country.upper()})")
    
    t1, t2 = st.tabs(["🍎 iOS (App Store)", "🤖 Android (Google Play)"])
    
    with st.spinner('正在同步全球数据，请稍候...'):
        ios_data = fetch_ios(mode, target_kw, country, limit)
        gp_data = fetch_gp(mode, target_kw, country, limit)
        
        with t1:
            if ios_data:
                df_ios = pd.DataFrame(ios_data)
                # 如果是榜单模式，过滤出包含关键词的游戏
                if mode != "关键词搜索排名":
                    df_ios = df_ios[df_ios['应用名称'].str.contains(target_kw, case=False, na=False)]
                
                st.dataframe(df_ios, use_container_width=True, hide_index=True)
                st.download_button("下载 iOS 报表", df_ios.to_csv(index=False).encode('utf-8-sig'), "ios_data.csv")
            else:
                st.info("在该模式下未找到匹配的 iOS 应用。")

        with t2:
            if gp_data:
                df_gp = pd.DataFrame(gp_data)
                st.dataframe(df_gp, use_container_width=True, hide_index=True)
                st.download_button("下载 Android 报表", df_gp.to_csv(index=False).encode('utf-8-sig'), "gp_data.csv")
            else:
                st.info("未找到匹配的 Android 应用。")

st.divider()
st.caption("提示：iOS 的畅销榜和下载榜是实时 RSS 数据；Android 端目前通过搜索算法模拟相关排名。")
