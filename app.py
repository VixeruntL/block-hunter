import streamlit as st
import requests
from google_play_scraper import search, app as gp_app
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Block新游监控-专业版", layout="wide")
st.title("🛡️ Block类游戏上架深度监控 (免搜索直达)")

# 侧边栏设置
st.sidebar.header("🎯 监控参数")
target_keyword = st.sidebar.text_input("过滤关键词 (如: block, puzzle, wood)", "block")
days_limit = st.sidebar.slider("监控范围 (过去几天)", 1, 30, 7)
country = st.sidebar.selectbox("监控市场", ["us", "gb", "jp", "kr", "cn"], index=0)

# App Store 逻辑优化：利用 RSS Feed 直接抓取最新上架
def fetch_ios_new_releases(keyword, days, country):
    new_apps = []
    # 抓取 App Store 最新上架的游戏榜单 (New Games RSS)
    url = f"https://itunes.apple.com/{country}/rss/newapplications/limit=100/json"
    try:
        res = requests.get(url, timeout=15).json()
        entries = res.get('feed', {}).get('entry', [])
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        for entry in entries:
            name = entry.get('im:name', {}).get('label', '')
            # 只要名字里包含关键字，就记录
            if keyword.lower() in name.lower():
                # 进一步抓取详情获取精确日期
                app_id = entry.get('id', {}).get('im:bundleId', '')
                new_apps.append({
                    "平台": "🍎 App Store",
                    "游戏名称": name,
                    "开发者": entry.get('im:artist', {}).get('label', '未知'),
                    "发布日期": "近期上架", # RSS流默认为最新
                    "链接": entry.get('id', {}).get('label', '')
                })
    except: pass
    return new_apps

# Google Play 逻辑优化：尝试多重搜索组合，模拟“最新”排序
def fetch_gp_new_releases(keyword, days, country):
    new_apps = []
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    # 尝试搜索关键词的变体，以覆盖更多新游
    search_queries = [f"new {keyword} game", f"{keyword} 2026", keyword]
    
    seen_ids = set()
    for q in search_queries:
        try:
            results = search(q, lang="en", country=country, n_hits=50)
            for r in results:
                app_id = r['appId']
                if app_id in seen_ids: continue
                seen_ids.add(app_id)
                
                try:
                    # 获取详细信息
                    details = gp_app(app_id, lang='en', country=country)
                    rel_date_str = details.get('released')
                    if rel_date_str:
                        rel_date = pd.to_datetime(rel_date_str)
                        if rel_date >= cutoff_date:
                            new_apps.append({
                                "平台": "🤖 Google Play",
                                "游戏名称": details.get('title'),
                                "开发者": details.get('developer'),
                                "发布日期": rel_date.strftime("%Y-%m-%d"),
                                "链接": f"https://play.google.com/store/apps/details?id={app_id}"
                            })
                except: continue
        except: continue
    return new_apps

if st.button("🔍 开始全量扫描", type="primary"):
    with st.spinner('正在调取应用商店 RSS 数据流和最新搜索索引...'):
        # 并行模拟：先跑 iOS 再跑 GP
        ios_list = fetch_ios_new_releases(target_keyword, days_limit, country)
        gp_list = fetch_gp_new_releases(target_keyword, days_limit, country)
        
        results = ios_list + gp_list
        
        if results:
            df = pd.DataFrame(results).drop_duplicates(subset=['游戏名称'])
            st.success(f"✅ 扫描完毕！在 {country.upper()} 市场发现了 {len(df)} 个含有 '{target_keyword}' 的新产品。")
            
            # 展示数据
            st.dataframe(
                df, 
                column_config={"链接": st.column_config.LinkColumn("查看详情")},
                use_container_width=True,
                hide_index=True
            )
            
            # 提供下载
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 导出扫描报告 (CSV)", data=csv, file_name=f"new_block_games_{datetime.now().strftime('%Y%m%d')}.csv")
        else:
            st.warning(f"⚠️ 未发现含有 '{target_keyword}' 的近期新游。建议：1. 缩短关键词(如只搜 'block') 2. 检查市场选择。")

st.info("💡 提示：App Store 的 RSS 数据大约每 6-12 小时更新一次；Google Play 的新游通常在发布 24 小时后才能被搜索到。")
