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
    if mode == "关键词搜索排名":
        url = f"https://itunes.apple.com/search?term={kw}&entity=software&country={cc}&limit={n}"
    elif mode == "热门下载榜 (Free)":
        url = f"https://itunes.apple.com/{cc}/rss/topfreeapplications/limit={n}/json"
    elif mode == "畅销收入榜 (Grossing)":
        url = f"https://itunes.apple.com/{cc}/rss/topgrossingapplications/limit={n}/json"
    else: 
        url = f"https://itunes.apple.com/{cc}/rss/newapplications/limit={n}/json"
        
    try:
        res = requests.get(url, timeout=10).json()
        data = []
        if "results" in res:
            for i, item in enumerate(res['results']):
                data.append({
                    "排名": i + 1,
                    "应用名称": item.get('trackName'),
                    "开发者": item.get('artistName'),
                    "评分": item.get('averageUserRating'),
                    "链接": item.get('trackViewUrl')
                })
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
            "链接": f"
