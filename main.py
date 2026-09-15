import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import urllib.request

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

# ------------------------------------------------------------
# 한글 폰트 설정 (스트림릿 클라우드 리눅스 환경 대응)
# ------------------------------------------------------------
@st.cache_resource
def set_korean_font():
    try:
        font_url = "https://raw.githubusercontent.com/naver/nanumfont/master/fonts/NanumGothic.ttf"
        font_path = "/tmp/NanumGothic.ttf"
        urllib.request.urlretrieve(font_url, font_path)
        fm.fontManager.addfont(font_path)
        plt.rcParams["font.family"] = "NanumGothic"
    except Exception:
        # 폰트를 못 가져오면 기본 폰트로 진행 (그래프의 한글이 깨질 수 있음)
        plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ------------------------------------------------------------
# 데이터 불러오기 & 전처리
# ------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df

df = load_data()

# 연도별 평균/최저/최고 기온 집계
yearly = (
    df.groupby("연도")[["평균기온", "최저기온", "최고기온"]]
    .mean()
    .reset_index()
)

# 관측 자료가 부족한(1년치 데이터가 너무 적은) 첫해/마지막해는 제외
year_counts = df.groupby("연도").size()
valid_years = year_counts[year_counts >= 300].index  # 관측일수 300일 이상인 연도만 사용
yearly = yearly[yearly["연도"].isin(valid_years)].reset_index(drop=True)

# ------------------------------------------------------------
# 헤더
# ------------------------------------------------------------
st.title("🌡️ 서울, 100년의 기온 변화")
st.markdown(
    f"""
서울 기상 관측이 시작된 **{int(yearly['연도'].min())}년**부터 **{int(yearly['연도'].max())}년**까지,
연평균 기온이 어떻게 변해왔는지 한눈에 살펴봐요.
"""
)

# ------------------------------------------------------------
# 핵심 지표 카드
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

first_year = yearly.iloc[0]
last_year = yearly.iloc[-1]
temp_change = last_year["평균기온"] - first_year["평균기온"]

with col1:
    st.metric(
        f"{int(first_year['연도'])}년 연평균 기온",
        f"{first_year['평균기온']:.1f} °C"
    )
with col2:
    st.metric(
        f"{int(last_year['연도'])}년 연평균 기온",
        f"{last_year['평균기온']:.1f} °C"
    )
with col3:
    st.metric(
        "그 사이 기온 변화",
        f"{temp_change:+.1f} °C",
        delta=f"{temp_change:+.1f} °C"
    )
with col4:
    hottest = yearly.loc[yearly["평균기온"].idxmax()]
    st.metric(
        "가장 더웠던 해",
        f"{int(hottest['연도'])}년",
        delta=f"{hottest['평균기온']:.1f} °C"
    )

st.divider()

# ------------------------------------------------------------
# 메인 그래프: 연평균 기온 변화 + 추세선
# ------------------------------------------------------------
st.subheader("📈 연평균 기온 변화 추이")

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    yearly["연도"], yearly["평균기온"],
    color="#4C72B0", linewidth=1.5, alpha=0.8, label="연평균 기온"
)

# 추세선 (선형 회귀)
z = np.polyfit(yearly["연도"], yearly["평균기온"], 1)
trend = np.poly1d(z)
ax.plot(
    yearly["연도"], trend(yearly["연도"]),
    color="#C44E52", linewidth=2.5, linestyle="--",
    label=f"추세선 (10년당 {z[0]*10:+.2f}°C)"
)

ax.set_xlabel("연도")
ax.set_ylabel("연평균 기온 (°C)")
ax.set_title("서울 연평균 기온 변화 (100여 년간)")
ax.legend(loc="upper left")
ax.grid(alpha=0.3)

st.pyplot(fig)

st.caption(
    "💡 추세선의 기울기는 최소제곱법으로 계산한 선형 추세이며, "
    "실제 기온은 해마다 오르내림이 있습니다."
)

st.divider()

# ------------------------------------------------------------
# 최고·최저 기온 함께 보기
# ------------------------------------------------------------
st.subheader("🔺🔻 연평균 최고·최저 기온도 함께 보기")

fig2, ax2 = plt.subplots(figsize=(12, 5))
ax2.plot(yearly["연도"], yearly["최고기온"], color="#DD8452", label="연평균 최고기온")
ax2.plot(yearly["연도"], yearly["평균기온"], color="#4C72B0", label="연평균 기온")
ax2.plot(yearly["연도"], yearly["최저기온"], color="#55A868", label="연평균 최저기온")
ax2.set_xlabel("연도")
ax2.set_ylabel("기온 (°C)")
ax2.set_title("서울 연평균 최고·평균·최저기온 변화")
ax2.legend(loc="upper left")
ax2.grid(alpha=0.3)

st.pyplot(fig2)

st.divider()

# ------------------------------------------------------------
# 10년 단위 비교
# ------------------------------------------------------------
st.subheader("📊 10년 단위로 살펴보기")

yearly["연대"] = (yearly["연도"] // 10) * 10
decade_avg = yearly.groupby("연대")["평균기온"].mean().reset_index()
decade_avg["연대"] = decade_avg["연대"].astype(str) + "년대"

fig3, ax3 = plt.subplots(figsize=(12, 5))
bars = ax3.bar(decade_avg["연대"], decade_avg["평균기온"], color="#4C72B0")
ax3.set_xlabel("연대")
ax3.set_ylabel("평균 기온 (°C)")
ax3.set_title("연대별 평균 기온")
ax3.grid(alpha=0.3, axis="y")
plt.xticks(rotation=45, ha="right")

for bar in bars:
    height = bar.get_height()
    ax3.annotate(
        f"{height:.1f}",
        xy=(bar.get_x() + bar.get_width() / 2, height),
        xytext=(0, 3),
        textcoords="offset points",
        ha="center", fontsize=9
    )

st.pyplot(fig3)

st.divider()

# ------------------------------------------------------------
# 원본 데이터 살짝 보여주기
# ------------------------------------------------------------
with st.expander("📄 연도별 데이터 직접 보기"):
    st.dataframe(
        yearly[["연도", "평균기온", "최저기온", "최고기온"]]
        .rename(columns={
            "연도": "연도",
            "평균기온": "연평균 기온(°C)",
            "최저기온": "연평균 최저기온(°C)",
            "최고기온": "연평균 최고기온(°C)"
        })
        .round(1),
        use_container_width=True,
        hide_index=True
    )

st.caption("데이터 출처: 기상청 서울(108) 지점 일별 관측자료")
