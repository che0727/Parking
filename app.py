import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import os

st.set_page_config(
    page_title="주차장 | 대구광역시 공공주차장 통합 검색",
    page_icon="🅿️",
    layout="wide"
)

# -------------------------
# 샘플 데이터
# -------------------------
@st.cache_data
def load_data():
    return pd.DataFrame([
        {"name":"하양역 공영주차장","region":"하양읍","type":"공영",
         "distance":0.6,"price":500,"total":120,"now":82,
         "h1":64,"h2":45,"hours":"24시간",
         "lat":35.9110,"lon":128.8200},
        {"name":"하양시장 공영주차장","region":"하양읍","type":"공영",
         "distance":0.9,"price":300,"total":80,"now":18,
         "h1":12,"h2":22,"hours":"08:00~22:00",
         "lat":35.9130,"lon":128.8190},
        {"name":"경산역 공영주차장","region":"경산시","type":"공영",
         "distance":4.8,"price":400,"total":150,"now":95,
         "h1":83,"h2":70,"hours":"24시간",
         "lat":35.8350,"lon":128.7290},
        {"name":"경산시청 부설주차장","region":"경산시","type":"개방",
         "distance":5.2,"price":600,"total":100,"now":12,
         "h1":8,"h2":16,"hours":"09:00~18:00",
         "lat":35.8250,"lon":128.7410},
        {"name":"대구 동성로 공영주차장","region":"대구시","type":"공영",
         "distance":18.5,"price":1000,"total":200,"now":35,
         "h1":22,"h2":30,"hours":"24시간",
         "lat":35.8690,"lon":128.5970},
        {"name":"대구 반월당 공영주차장","region":"대구시","type":"공영",
         "distance":19.2,"price":800,"total":180,"now":140,
         "h1":105,"h2":80,"hours":"24시간",
         "lat":35.8640,"lon":128.5930},
    ])

df = load_data()

# -------------------------
# 스타일
# -------------------------
st.markdown("""
<style>
.stApp {background-color:#f5f7f6}
.block-container {padding-top:1.5rem; max-width:1450px}
.hero {
    background:linear-gradient(120deg,#173c34,#286b55);
    color:white;padding:28px 30px;border-radius:16px;
    margin-bottom:22px
}
.hero p {color:#e1eee8}
.small-muted {color:#738078;font-size:13px}
.parking-card {
    background:white;border:1px solid #e0e7e2;
    border-radius:12px;padding:17px;margin-bottom:12px
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 상단 헤더
# -------------------------
st.markdown("""
<div class="hero">
    <div style="font-size:12px;letter-spacing:2px">
        SMART PARKING SERVICE
    </div>
    <h1 style="margin:10px 0 6px">🅿️ 주차장</h1>
    <p style="margin:0">
        주차장을 찾는 시간은 줄이고, 도착 후의 주차 걱정까지 덜어드립니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "프로토타입 0.2 · 현재 표시되는 주차장 정보와 예측값은 시연용 샘플입니다."
)

# -------------------------
# 검색 및 필터
# -------------------------
st.subheader("어디에 주차하시겠어요?")

c1, c2 = st.columns([3, 1])
with c1:
    destination = st.text_input(
        "목적지",
        value="대구가톨릭대학교",
        placeholder="목적지 또는 주차장 이름"
    )
with c2:
    st.text_input("검색 기준", value="목적지 기준", disabled=True)

f1, f2, f3 = st.columns(3)
with f1:
    region = st.selectbox(
        "지역",
        ["전체 지역", "하양읍", "경산시", "대구시"]
    )
with f2:
    parking_type = st.selectbox(
        "주차장 유형",
        ["전체 유형", "공영", "개방"]
    )
with f3:
    sort_option = st.selectbox(
        "정렬 기준",
        ["추천순", "거리순", "요금순", "주차 여유순"]
    )

keyword = st.text_input(
    "🔎 주차장 이름 검색",
    placeholder="예: 하양역 공영주차장"
)

# -------------------------
# 검색 결과 계산
# -------------------------
filtered = df.copy()

if region != "전체 지역":
    filtered = filtered[filtered["region"] == region]

if parking_type != "전체 유형":
    filtered = filtered[filtered["type"] == parking_type]

if keyword.strip():
    filtered = filtered[
        filtered["name"].str.contains(
            keyword.strip(), case=False, na=False
        )
    ]

# 데모용 추천 점수
# 실제 거리·요금 가중치는 추후 사용자 요구사항에 따라 조정
def recommendation_score(row):
    distance_score = max(0, 1 - row["distance"] / 20) * 25
    price_score = max(0, 1 - row["price"] / 1500) * 20
    current_score = row["now"] / row["total"] * 20
    future1_score = row["h1"] / row["total"] * 15
    future2_score = row["h2"] / row["total"] * 20

    return round(
        distance_score + price_score + current_score
        + future1_score + future2_score
    )

filtered["score"] = filtered.apply(recommendation_score, axis=1)

if sort_option == "거리순":
    filtered = filtered.sort_values("distance")
elif sort_option == "요금순":
    filtered = filtered.sort_values("price")
elif sort_option == "주차 여유순":
    filtered = filtered.sort_values("now", ascending=False)
else:
    filtered = filtered.sort_values("score", ascending=False)

# -------------------------
# 요약 지표
# -------------------------
st.divider()
st.subheader("검색 결과")

m1, m2, m3 = st.columns(3)
m1.metric("검색된 주차장", f"{len(filtered)}곳")
m2.metric("현재 주차 가능", f"{filtered['now'].sum():,}면")
m3.metric(
    "주차 여유",
    f"{(filtered['now'] / filtered['total'] >= 0.5).sum()}곳"
)

# -------------------------
# 지도와 목록
# -------------------------
left, right = st.columns([1.15, 1])

with left:
    st.subheader("주차장 위치")
    st.caption(
        "카카오맵 · 마커를 클릭하면 주차장 정보를 확인할 수 있습니다."
    )

    # 카카오 JavaScript 키 입력
    kakao_js_key = os.getenv("KAKAO_JS_KEY", "")

    # 검색 결과를 지도에 전달
    parking_json = json.dumps(
        filtered.to_dict(orient="records"),
        ensure_ascii=False
    )

    center_lat = (
        filtered["lat"].mean() if not filtered.empty else 35.9
    )
    center_lon = (
        filtered["lon"].mean() if not filtered.empty else 128.7
    )

    map_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        html, body, #map {
          width: 100%;
          height: 440px;
          margin: 0;
          padding: 0;
        }
      </style>
    </head>
    <body>
      <div id="map"></div>

      <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=__APP_KEY__"></script>
      <script>
        const parkingLots = __PARKING_DATA__;
        const centerLat = __CENTER_LAT__;
        const centerLon = __CENTER_LON__;

        kakao.maps.load(function () {
          const container = document.getElementById("map");

          const map = new kakao.maps.Map(container, {
            center: new kakao.maps.LatLng(centerLat, centerLon),
            level: 8
          });

          const bounds = new kakao.maps.LatLngBounds();
          const infoWindow = new kakao.maps.InfoWindow({
            removable: true
          });

          parkingLots.forEach(function (p) {
            const position = new kakao.maps.LatLng(p.lat, p.lon);

            const marker = new kakao.maps.Marker({
              map: map,
              position: position,
              title: p.name
            });

            bounds.extend(position);

            kakao.maps.event.addListener(marker, "click", function () {
              const content = `
                <div style="padding:12px;width:180px;font-size:13px;">
                  <strong>${p.name}</strong>
                  <hr>
                  <div>현재 가능: ${p.now}면</div>
                  <div>1시간 후: ${p.h1}면</div>
                  <div>2시간 후: ${p.h2}면</div>
                  <div>기본요금: ${Number(p.price).toLocaleString()}원</div>
                </div>
              `;

              infoWindow.setContent(content);
              infoWindow.open(map, marker);
            });
          });

          if (parkingLots.length > 1) {
            map.setBounds(bounds);
          } else if (parkingLots.length === 1) {
            map.setCenter(
              new kakao.maps.LatLng(
                parkingLots[0].lat,
                parkingLots[0].lon
              )
            );
            map.setLevel(4);
          }
        });
      </script>
    </body>
    </html>
    """

    map_html = map_html.replace(
        "__APP_KEY__", kakao_js_key
    )
    map_html = map_html.replace(
        "__PARKING_DATA__", parking_json
    )
    map_html = map_html.replace(
        "__CENTER_LAT__", str(center_lat)
    )
    map_html = map_html.replace(
        "__CENTER_LON__", str(center_lon)
    )

    if filtered.empty:
        st.info("검색 조건에 맞는 주차장이 없습니다.")
    else:
        st.iframe(
            map_html,
            height=450,
            width="stretch",
            alt="주차장 위치 지도"
        )

    st.caption(
        "주차장 위치와 주차 현황은 시연용 샘플 데이터입니다."
    )

with right:
    st.subheader("주차장 목록")

    if filtered.empty:
        st.warning("검색 조건에 맞는 주차장이 없습니다.")

    for _, p in filtered.iterrows():
        ratio = p["now"] / p["total"]

        if ratio >= 0.8:
            status = "혼잡"
        elif ratio >= 0.5:
            status = "보통"
        else:
            status = "여유"

        with st.container(border=True):
            st.markdown(f"### {p['name']}")

            st.caption(
                f"{p['region']} · {p['type']} · "
                f"목적지 기준 {p['distance']}km"
            )

            a, b = st.columns(2)
            a.metric("현재 주차 가능", f"{p['now']}면")
            b.metric("추천 점수", f"{p['score']}점")

            st.progress(min(1.0, ratio))
            st.caption(
                f"전체 {p['total']}면 중 {p['total'] - p['now']}면 이용 중"
            )

            st.markdown(
                f"**현재 {status}** · "
                f"1시간 후 {p['h1']}면 · "
                f"2시간 후 {p['h2']}면"
            )

            with st.expander("상세정보 보기"):
                st.write(f"주차장 유형: {p['type']}")
                st.write(f"운영시간: {p['hours']}")
                st.write(f"기본요금: {p['price']:,}원 / 10분 (가정)")
                st.write(f"총 주차면수: {p['total']}면")
                st.write(f"현재 주차 가능: {p['now']}면")
                st.write(f"1시간 후 예상: {p['h1']}면")
                st.write(f"2시간 후 예상: {p['h2']}면")
                st.caption(
                    "요금·운영시간·주차 현황·예측값은 모두 임의의 샘플입니다."
                )

st.divider()
st.caption(
    "주차장 | 소프트웨어공학 캡스톤 디자인 | "
    "공공주차장 통합 검색 및 주차 편의정보 제공 시스템"
)
