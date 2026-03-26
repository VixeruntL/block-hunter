import streamlit as st
import requests
from google_play_scraper import search, app as gp_app
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Block游戏监控器", layout="wide")
st.title("🧩 Block类新品游戏雷达")

# 侧边栏
st.sidebar.header("⚙️ 监控设置")
keywords_input = st.sidebar.text_area("监控关键词 (用逗号分隔)", "block blast, block puzzle, wood block")
days_limit = st.sidebar.slider("查询过去几天的上架产品？", 1, 30, 14) # 扩大到30天更稳妥
country = st.sidebar.selectbox("目标市场", ["us", "jp", "kr", "tw", "cn"], index=0)

keywords = [k.strip() for k in keywords_input.split(',')]

def fetch_app_store(keywords, days_limit, country):
    new_apps = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_limit)
    for keyword in keywords:
        # 增加搜索限额到 100
        url = f"https://itunes.apple.com/search?term={keyword}&entity=software&country={country}&limit=100"
        try:
            response = requests.get(url, timeout=15).json()
            for result in response.get('results', []):
                # 尝试获取发布日期或更新日期
                date_str = result.get('releaseDate') or result.get('currentVersionReleaseDate')
                if date_str:
                    release_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                    if release_date >= cutoff_date:
                        new_apps.append({
                            "平台": "🍎 App Store",
                            "游戏名称": result.get('trackName'),
                            "开发者": result.get('artistName'),
                            "发布日期": release_date.strftime("%Y-%m-%d"),
                            "链接": result.get('trackViewUrl')
                        })
        except: continue
    return new_apps

def fetch_google_play(keywords, days_limit, country):
    new_apps = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_limit)
    for keyword in keywords:
        try:
            # 增加搜索深度
            results = search(keyword, lang="en", country=country)
            for result in results[:40]: 
                app_id = result['appId']
                try:
                    # 抓取详情很耗时且易被封IP，这里先做基础判断
                    details = gp_app(app_id, lang='en', country=country)
                    released_str = details.get('released')
                    if released_str:
                        # 兼容处理 Google Play 的多种日期格式
                        try:
                            release_date = pd.to_datetime(released_str)
                            if release_date >= cutoff_date:
                                new_apps.append({
                                    "平台": "🤖 Google Play",
                                    "游戏名称": details.get('title'),
                                    "开发者": details.get('developer'),
                                    "发布日期": release_date.strftime("%Y-%m-%d"),
                                    "链接": f"https://play.google.com/store/apps/details?id={app_id}"
                                })
                        except: continue
                except: continue
        except: continue
    return new_apps

if st.button("🚀 开始扫描新品", type="primary"):
    if not keywords_input.strip():
        st.error("请输入关键词后再扫描！")
    else:
        with st.spinner('正在深度扫描，请耐心等待约 30 秒...'):
            ios_data = fetch_app_store(keywords, days_limit, country)
            gp_data = fetch_google_play(keywords, days_limit, country)
            
            all_data = ios_data + gp_data
            
            if all_data:
                df = pd.DataFrame(all_data).drop_duplicates(subset=['游戏名称'])
                st.success(f"找到 {len(df)} 款近期上架/更新的游戏！")
                st.dataframe(df, column_config={"链接": st.column_config.LinkColumn()}, use_container_width=True)
            else:
                st.info("💡 搜索反馈：在当前条件下未发现极新品。原因可能是：这些词下的排名前 100 都是老游戏。建议尝试搜更具体的词，如 'Block Blast 2026'。")
