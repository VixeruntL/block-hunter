import streamlit as st
import requests
from google_play_scraper import search
import pandas as pd

# 基础设置
st.set_page_config(page_title="App Search Tool", layout="wide")
st.title("🌐 Universal App Store Search")

# 侧边栏
with st.sidebar:
    st.header("Settings")
    kw = st.text_input("Keyword", "block blast")
    cc = st.selectbox("Country", ["us", "cn", "jp", "kr", "gb"], index=0)
    limit = st.slider("Limit", 10, 200, 50)

# 获取 iOS 数据
def get_ios(keyword, country, n):
    url = f"https://itunes.apple.com/search?term={keyword}&entity=software&country={country}&limit={n}"
    try:
        res = requests.get(url, timeout=10).json()
        data = []
        for i, item in enumerate(res.get('results', [])):
            data.append({
                "Rank": i + 1,
                "Name": item.get('trackName'),
                "Developer": item.get('artistName'),
                "Rating": item.get('averageUserRating'),
                "Link": item.get('trackViewUrl')
            })
        return data
    except:
        return []

# 获取 Android 数据
def get_gp(keyword, country, n):
    try:
        res = search(keyword, lang="en", country=country, n_hits=n)
        data = []
        for i, item in enumerate(res):
            data.append({
                "Rank": i + 1,
                "Name": item.get('title'),
                "Developer": item.get('developer'),
                "Rating": item.get('score'),
                "Link": f"https://play.google.com/store/apps/details?id={item.get('appId')}"
            })
        return data
    except:
        return []

# 运行按钮
if st.button("Search Now", type="primary"):
    tab1, tab2 = st.tabs(["iOS (App Store)", "Android (Google Play)"])
    
    ios_res = get_ios(kw, cc, limit)
    gp_res = get_gp(kw, cc, limit)
    
    with tab1:
        if ios_res:
            df_ios = pd.DataFrame(ios_res)
            st.dataframe(df_ios, use_container_width=True, hide_index=True)
            # 简单的下载按钮
            csv_ios = df_ios.to_csv(index=False).encode('utf-8')
            st.download_button("Download iOS CSV", data=csv_ios, file_name="ios_apps.csv")
        else:
            st.write("No results found for iOS.")

    with tab2:
        if gp_res:
            df_gp = pd.DataFrame(gp_res)
            st.dataframe(df_gp, use_container_width=True, hide_index=True)
            # 简单的下载按钮
            csv_gp = df_gp.to_csv(index=False).encode('utf-8')
            st.download_button("Download Android CSV", data=csv_gp, file_name="gp_apps.csv")
        else:
            st.write("No results found for Android.")

st.divider()
st.caption("Universal Search Tool - Beta")
