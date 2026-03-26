import streamlit as st
import requests
from google_play_scraper import search, app as gp_app
from datetime import datetime, timedelta
import pandas as pd

# 设置网页标题和布局
st.set_page_config(page_title="Block游戏监控器", layout="wide")
st.title("🧩 Block类新品游戏雷达 (Google Play & App Store)")

# 侧边栏设置面板
st.sidebar.header("⚙️ 监控设置")
keywords_input = st.sidebar.text_area("监控关键词 (用逗号分隔)", "block blast, block puzzle, wood block")
days_limit = st.sidebar.slider("查询过去几天的上架产品？", 1, 14, 3)
country = st.sidebar.selectbox("目标市场", ["us", "jp", "kr", "tw", "cn"], index=0)

# 处理用户输入的关键词
keywords = [k.strip() for k in keywords_input.split(',')]

def fetch_app_store(keywords, days_limit, country):
    new_apps = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_limit)
    for keyword in keywords:
        url = f"https://itunes.apple.com/search?term={keyword}&entity=software&country={country}&limit=50"
        try:
            response = requests.get(url, timeout=10).json()
            for result in response.get('results', []):
                release_date_str = result.get('releaseDate')
                if release_date_str:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    if release_date >= cutoff_date:
                        new_apps.append({
                            "平台": "🍎 App Store",
                            "游戏名称": result.get('trackName'),
                            "开发者": result.get('artistName'),
                            "上架日期": release_date.strftime("%Y-%m-%d"),
                            "链接": result.get('trackViewUrl')
                        })
        except Exception as e:
            continue
    return new_apps

def fetch_google_play(keywords, days_limit, country):
    new_apps = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_limit)
    for keyword in keywords:
        try:
            results = search(keyword, lang="en", country=country)
            for result in results[:20]: # 取前20名以加快速度
                app_id = result['appId']
                try:
                    details = gp_app(app_id, lang='en', country=country)
                    released_str = details.get('released')
                    if released_str:
                        release_date = datetime.strptime(released_str, "%b %d, %Y")
                        if release_date >= cutoff_date:
                            new_apps.append({
                                "平台": "🤖 Google Play",
                                "游戏名称": details.get('title'),
                                "开发者": details.get('developer'),
                                "上架日期": release_date.strftime("%Y-%m-%d"),
                                "链接": f"https://play.google.com/store/apps/details?id={app_id}"
                            })
                except Exception:
                    continue
        except Exception:
            continue
    return new_apps

# 主界面运行按钮
if st.button("🚀 开始扫描新品", type="primary"):
    with st.spinner('正在全网搜寻最新上架的 Block 游戏，这可能需要几十秒钟...'):
        ios_data = fetch_app_store(keywords, days_limit, country)
        gp_data = fetch_google_play(keywords, days_limit, country)
        
        all_data = ios_data + gp_data
        
        # 数据去重（基于游戏名称）
        unique_apps = []
        seen_names = set()
        for item in all_data:
            if item['游戏名称'] not in seen_names:
                unique_apps.append(item)
                seen_names.add(item['游戏名称'])

        if unique_apps:
            st.success(f"扫描完成！共发现 {len(unique_apps)} 款近期上架的新游戏。")
            # 将结果转为数据表展示
            df = pd.DataFrame(unique_apps)
            # 将链接转为可点击的HTML格式
            st.dataframe(
                df,
                column_config={
                    "链接": st.column_config.LinkColumn("应用商店链接")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning(f"在过去 {days_limit} 天内，没有发现符合条件的新游戏。你可以尝试扩大时间范围或更换关键词。")