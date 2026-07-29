import json
import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from db.service_center.service_center import (
    get_manufacturer_list,
    get_service_centers,
    get_sido_list,
    get_sigungu_list,
)

load_dotenv()

KAKAO_JS_KEY = os.getenv("KAKAO_JS_KEY")

# ==========================
# 브랜드 컬러 시스템
# ==========================
BRAND_COLORS = {
    "현대": {"main": "#00AAD2", "dark": "#00728C"},
    "기아": {"main": "#BB162B", "dark": "#8C0F20"},
    "벤츠": {"main": "#1A1A1A", "dark": "#000000"},
    "BMW": {"main": "#0066B1", "dark": "#003D6B"},
    "폭스바겐": {"main": "#001E50", "dark": "#000E28"},
}
DEFAULT_ACCENT = {"main": "#2563EB", "dark": "#1D4ED8"}


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


# ==========================
# 페이지 기본 설정 및 세션 상태 초기화
# ==========================
st.set_page_config(
    page_title="Service Center",
    layout="wide",
)

# 조회 버튼 누르기 전과 후의 조건을 분리 관리
if "applied_company" not in st.session_state:
    st.session_state["applied_company"] = "현대"

if "applied_sido" not in st.session_state:
    st.session_state["applied_sido"] = "전체"

if "applied_sigungu" not in st.session_state:
    st.session_state["applied_sigungu"] = "전체"

# 조회할 때마다 값을 바꿔서, 검색 결과가 이전과 완전히 같더라도
# 지도 컴포넌트가 매번 새로 초기화(리셋)되도록 만드는 용도
if "search_token" not in st.session_state:
    st.session_state["search_token"] = 0

# 현재 확정/적용된 테마 색상 계산
brand_name_dict = {
    "현대": "Hyundai",
    "기아": "Kia",
    "벤츠": "Mercedes-Benz",
    "BMW": "BMW",
    "폭스바겐": "Volkswagen",
}

applied_company = st.session_state["applied_company"]
brand_name = brand_name_dict[applied_company]

_accent = BRAND_COLORS.get(applied_company, DEFAULT_ACCENT)
ACCENT = _accent["main"]
ACCENT_DARK = _accent["dark"]
ACCENT_SOFT = hex_to_rgba(ACCENT, 0.08)
ACCENT_SOFT_STRONG = hex_to_rgba(ACCENT, 0.16)

# ==========================
# Custom CSS (적용된 테마 기반)
# ==========================
st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

    /* ==========================================
    [1. 테마 변수]
    config.toml(base="light")로 테마가 고정되어 있으므로
    여기서는 다크모드 방어용 !important 없이 색상 변수만 정의.
    ========================================== */
    :root {{
        --accent: {ACCENT};
        --accent-dark: {ACCENT_DARK};
        --accent-soft: {ACCENT_SOFT};
        --accent-soft-strong: {ACCENT_SOFT_STRONG};
        --ink: #0F172A;
        --ink-soft: #64748B;
        --line: #E7EAF0;
        --surface: #FFFFFF;
        --canvas: #F6F8FB;
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--canvas);
    }}

    /* ==========================================
    [2. 셀렉트박스 & 인풋 스타일]
    BaseWeb 컴포넌트 기본 스타일을 덮어쓰기 위한 것으로,
    특이도 문제 때문에 !important가 필요함(다크모드와는 무관).
    ========================================== */
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-baseweb="base-input"] {{
        background-color: var(--canvas) !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
        border-radius: 9px !important;
        box-shadow: none !important;
    }}

    /* 셀렉트박스 호버 시 테두리 액센트 컬러 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:hover {{
        border-color: var(--accent) !important;
    }}

    /* 셀렉트박스 텍스트 & 아이콘 색상 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {{
        color: var(--ink) !important;
        fill: var(--ink) !important;
    }}

    /* 셀렉트박스 라벨(제목) 글자색 */
    div[data-testid="stSelectbox"] label p {{
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        line-height: 1.15rem !important;
        letter-spacing: 0.01em;
        color: var(--ink-soft) !important;
        text-transform: uppercase;
    }}

    /* 드롭다운 메뉴 팝업 (클릭 시 나오는 전체 리스트) */
    div[data-baseweb="popover"] ul[data-baseweb="menu"],
    ul[data-testid="stSelectboxVirtualDropdown"] {{
        background-color: var(--surface) !important;
        border-color: var(--line) !important;
    }}

    /* 드롭다운 개별 옵션 아이템 */
    li[data-baseweb="option"] {{
        background-color: var(--surface) !important;
        color: var(--ink) !important;
    }}

    li[data-baseweb="option"]:hover,
    li[data-baseweb="option"][aria-selected="true"] {{
        background-color: {ACCENT_SOFT} !important;
        color: var(--ink) !important;
    }}

    /* 비활성화된 셀렉트박스(시/군/구 미선택 시) */
    div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-disabled="true"] {{
        background-color: #EEF1F5 !important;
        border: 1px dashed #CBD5E1 !important;
        cursor: not-allowed !important;
    }}
    div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-disabled="true"] * {{
        color: #94A3B8 !important;
        fill: #94A3B8 !important;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1360px;
    }}

    /* ---------- 헤더 ---------- */
    .main-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.6rem;
        padding-bottom: 1.4rem;
        border-bottom: 1px solid #E7EAF0;
    }}
    .main-header .eyebrow {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        color: var(--accent);
        text-transform: uppercase;
        margin-bottom: 0.55rem;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .main-header .eyebrow::before {{
        content: "";
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 0 4px var(--accent-soft);
    }}
    .main-header h1 {{
        font-family: 'Manrope', sans-serif;
        font-size: 2.05rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.03em;
    }}
    .main-header p {{
        color: #64748B !important;
        font-size: 0.94rem;
        margin: 0;
    }}
    .main-header .brand-chip {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.85rem;
        color: #FFFFFF !important;
        background: var(--accent);
        padding: 0.55rem 1.05rem;
        border-radius: 999px;
        white-space: nowrap;
        box-shadow: 0 6px 16px var(--accent-soft-strong);
        transition: all 0.25s ease;
    }}

    .field-label-spacer {{
        min-height: 1.15rem;
        margin-bottom: 0.4rem;
        font-size: 0.76rem;
        font-weight: 700;
        line-height: 1.15rem;
        letter-spacing: 0.01em;
        text-transform: uppercase;
        visibility: hidden;
        user-select: none;
    }}

    /* ---------- 필터 패널 / 카드 ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: #FFFFFF !important;
        border: 1px solid #E7EAF0 !important;
        border-radius: 14px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] {{
        padding: 0 0.85rem;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:first-child {{
        padding-left: 0.1rem;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:last-child {{
        padding-right: 0.1rem;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:not(:last-child) {{
        border-right: 1px solid #E7EAF0;
    }}

    /* ---------- 버튼 ---------- */
    div.stButton > button {{
        width: 100% !important;
        background: var(--accent) !important;
        color: #FFFFFF !important;
        border-radius: 9px;
        height: 2.7rem;
        font-weight: 700;
        font-size: 0.95rem;
        border: none !important;
        transition: all 0.15s ease-in-out;
        margin-top: 0;
        box-shadow: 0 4px 12px var(--accent-soft-strong);
        letter-spacing: -0.01em;
    }}
    div.stButton > button:hover {{
        background: var(--accent-dark) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 8px 18px var(--accent-soft-strong);
    }}
    div.stButton > button:active {{
        transform: translateY(0px);
    }}

    .dirty-hint {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        color: var(--accent);
        text-align: center;
        margin-top: 0.55rem;
        letter-spacing: 0.01em;
    }}
    .st-key-apply_btn_dirty {{
        border-color: var(--accent) !important;
    }}
    .st-key-apply_btn_dirty div.stButton > button {{
        animation: pulse-glow 1.6s ease-in-out infinite;
    }}
    @keyframes pulse-glow {{
        0%, 100% {{ box-shadow: 0 4px 12px var(--accent-soft-strong); }}
        50% {{ box-shadow: 0 4px 22px var(--accent-soft-strong), 0 0 0 6px var(--accent-soft); }}
    }}

    /* ---------- 결과 요약 바 ---------- */
    .result-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF !important;
        border: 1px solid #E7EAF0 !important;
        border-left: 4px solid var(--accent) !important;
        border-radius: 10px;
        padding: 0.85rem 1.2rem;
        margin-top: 1.0rem;
        margin-bottom: 1.1rem;
        font-size: 0.92rem;
        color: #0F172A !important;
    }}
    .result-bar .result-location {{
        color: #64748B !important;
    }}
    .result-bar .result-location b {{
        color: #0F172A !important;
        font-weight: 700;
    }}
    .result-bar .result-count {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--accent);
    }}
    .result-bar .result-count span {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: #64748B !important;
        margin-left: 0.15rem;
    }}

    /* ---------- 빈 상태 ---------- */
    .empty-state {{
        background: #FFFFFF !important;
        border: 1px dashed #E7EAF0 !important;
        border-radius: 14px;
        padding: 3rem 1.5rem;
        text-align: center;
        color: #64748B !important;
        font-size: 0.95rem;
    }}
    .empty-state .empty-icon {{
        font-size: 2rem;
        margin-bottom: 0.6rem;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================
# 헤더 영역
# ==========================
st.markdown(
    f"""
<div class="main-header">
    <div>
        <div class="eyebrow">Official Service Network</div>
        <h1>Service Center</h1>
        <p>지역과 제조사를 선택하여 주변 공식 서비스센터 위치 및 상세 정보를 확인하세요.</p>
    </div>
    <div class="brand-chip">🔧 {brand_name} Service Center</div>
</div>
""",
    unsafe_allow_html=True,
)


# ==========================
# 지도 + 리스트를 하나의 컴포넌트로 렌더링
# (같은 iframe/JS 스코프 안에 있어야 리스트 클릭 -> 지도 포커스가 가능함)
# ==========================
def render_map_and_list(df, accent, accent_dark, search_token):
    df = df.reset_index(drop=True)
    locations = df.rename(
        columns={
            "name": "센터명",
            "address": "주소",
            "phone": "전화번호",
            "latitude": "위도",
            "longitude": "경도",
        }
    ).to_dict("records")

    location_json = json.dumps(locations, ensure_ascii=False)

    cards = ""
    for idx, (_, row) in enumerate(df.iterrows()):
        name = row.get("name", "센터명 없음")
        address = row.get("address", "주소 정보 없음")
        phone = row.get("phone", "전화번호 없음")

        kakao_search_url = f"https://map.kakao.com/link/search/{address} {name}"

        cards += f"""
        <div class="center-card" data-index="{idx}" onclick="focusCenter({idx})">
            <div class="card-index">{idx + 1:02d}</div>
            <div class="card-body">
                <div class="card-header">
                    <span class="center-name">{name}</span>
                </div>
                <div class="center-address">📍 {address}</div>

                <div class="card-actions">
                    <a href="tel:{phone}" class="btn-phone" onclick="event.stopPropagation()">📞 {phone}</a>
                    <a href="{kakao_search_url}" target="_blank" class="btn-map" onclick="event.stopPropagation()">🧭 길찾기</a>
                </div>
            </div>
        </div>
        """

    html = f"""
<!-- search_token:{search_token} -->
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet">
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        padding: 0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .wrap {{
        display: flex;
        gap: 16px;
        align-items: stretch;
    }}
    #map {{
        flex: 2;
        min-width: 0;
        height: 580px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
        border: 1px solid #E7EAF0;
    }}
    .list-panel {{
        flex: 1;
        min-width: 0;
    }}
    .center-list-container {{
        height: 580px;
        overflow-y: auto;
        padding-right: 6px;
        box-sizing: border-box;
    }}
    .center-card {{
        display: flex;
        gap: 12px;
        background-color: #FFFFFF;
        border: 1px solid #E7EAF0;
        border-left: 3px solid {accent};
        border-radius: 12px;
        padding: 15px 16px;
        margin-bottom: 11px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        transition: all 0.15s ease;
        cursor: pointer;
    }}
    .center-card:hover {{
        border-color: #CBD5E1;
        border-left-color: {accent};
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
        transform: translateY(-1px);
    }}
    .center-card.active {{
        background-color: {hex_to_rgba(accent, 0.07)};
        border-color: {accent};
        border-left-width: 4px;
    }}
    .card-index {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        color: {accent_dark};
        background: {hex_to_rgba(accent, 0.1)};
        border-radius: 6px;
        min-width: 28px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
    }}
    .card-body {{
        flex: 1;
        min-width: 0;
    }}
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }}
    .center-name {{
        font-size: 1.0rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.01em;
    }}
    .center-address {{
        font-size: 0.83rem;
        color: #64748B;
        margin-bottom: 12px;
        line-height: 1.45;
    }}
    .card-actions {{
        display: flex;
        gap: 8px;
    }}
    .btn-phone {{
        flex: 1;
        text-align: center;
        font-size: 0.81rem;
        font-weight: 600;
        color: {accent_dark};
        background-color: {hex_to_rgba(accent, 0.08)};
        padding: 8px 0;
        border-radius: 7px;
        text-decoration: none;
        transition: background-color 0.15s ease;
    }}
    .btn-map {{
        flex: 1;
        text-align: center;
        font-size: 0.81rem;
        font-weight: 600;
        color: #475569;
        background-color: #F8FAFC;
        border: 1px solid #E7EAF0;
        padding: 8px 0;
        border-radius: 7px;
        text-decoration: none;
        transition: background-color 0.15s ease;
    }}
    .btn-phone:hover {{ background-color: {hex_to_rgba(accent, 0.16)}; }}
    .btn-map:hover {{ background-color: #F1F5F9; color: #1E293B; }}

    .center-list-container::-webkit-scrollbar {{ width: 5px; }}
    .center-list-container::-webkit-scrollbar-thumb {{
        background-color: #E2E8F0;
        border-radius: 3px;
    }}

    /* ---------- 지도 인포윈도우 ---------- */
    .info-card {{
        padding: 14px 16px;
        width: 250px;
        font-size: 13px;
        line-height: 1.45;
        color: #1E293B;
        border-top: 3px solid {accent};
        border-radius: 2px;
        box-sizing: border-box;
    }}
    .info-title {{
        font-size: 14px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 6px;
    }}
    .info-addr {{
        color: #64748B;
        margin-bottom: 10px;
        word-break: keep-all;
        font-size: 12px;
    }}
    /* 전화번호 길이에 상관없이 안 깨지도록 가로 2등분 대신 세로로 쌓음 */
    .info-actions {{
        display: flex;
        flex-direction: column;
        gap: 6px;
    }}
    .info-phone, .info-direction {{
        display: block;
        width: 100%;
        box-sizing: border-box;
        text-align: center;
        text-decoration: none;
        font-weight: 600;
        font-size: 12px;
        padding: 7px 0;
        border-radius: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .info-phone {{
        color: {accent_dark};
        font-family: 'JetBrains Mono', monospace;
        background: {hex_to_rgba(accent, 0.1)};
    }}
    .info-direction {{
        color: #475569;
        background: #F1F5F9;
        border: 1px solid #E2E8F0;
    }}
</style>

<script>
window.kakao = window.kakao || {{}};
window.kakao.maps = window.kakao.maps || {{}};
window.daum = window.daum || {{}};
window.daum.maps = window.daum.maps || {{}};
</script>

</head>
<body>

<div class="wrap">
    <div id="map"></div>
    <div class="list-panel">
        <div class="center-list-container">
            {cards}
        </div>
    </div>
</div>

<script>
var data = {location_json};
var accentColor = "{accent}";

// ============================================================
// 지도/마커 초기화 로직을 함수로 분리.
// 이 함수는 카카오 SDK 다운로드가 "완전히" 끝난 뒤에만 호출됨
// (script.onload -> kakao.maps.load(initMap))
// 기존 코드는 SDK 로드를 기다리지 않고 별도로 kakao.maps.load(...)를
// 즉시 호출해서, SDK가 늦게 도착하면 kakao.maps가 아직 빈 객체({{}})라서
// "kakao.maps.load is not a function" 에러가 발생했음.
// ============================================================
function initMap() {{

    var container = document.getElementById("map");

    var options = {{
        center: new kakao.maps.LatLng(36.5, 127.8),
        level: 12
    }};

    var map = new kakao.maps.Map(container, options);

    var bounds = new kakao.maps.LatLngBounds();
    var activeInfoWindow = null;
    var activeCardEl = null;

    var markers = [];
    var infoWindows = [];
    var validMarkerCount = 0;


    var markerImage = new kakao.maps.MarkerImage(
        "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="34" height="42" viewBox="0 0 34 42">' +
            '<path d="M17 0C7.6 0 0 7.6 0 17c0 12.7 17 25 17 25s17-12.3 17-25C34 7.6 26.4 0 17 0z" fill="' + accentColor + '"/>' +
            '<circle cx="17" cy="17" r="7" fill="#fff"/>' +
            '</svg>'
        ),
        new kakao.maps.Size(34, 42),
        {{
        offset: new kakao.maps.Point(17, 42)
        }}
    );


    function openInfo(idx) {{
        if (activeInfoWindow) {{
            activeInfoWindow.close();
        }}

        var marker = markers[idx];
        var info = infoWindows[idx];

        if (!marker || !info) {{
            return;
        }}

        info.open(map, marker);
        activeInfoWindow = info;
    }}


    function highlightCard(idx) {{
        if (activeCardEl) {{
            activeCardEl.classList.remove("active");
        }}

        var el = document.querySelector(
            '.center-card[data-index="' + idx + '"]'
        );

        if (el) {{
            el.classList.add("active");
            activeCardEl = el;
        }}
    }}


    window.focusCenter = function(idx) {{

        var marker = markers[idx];

        if (!marker) {{
            return;
        }}

        var pos = marker.getPosition();

        map.setLevel(3);

        setTimeout(function() {{
            map.panTo(pos);
            openInfo(idx);
            highlightCard(idx);
        }}, 100);

    }};


    setTimeout(function(){{

        map.relayout();


        data.forEach(function(center, idx) {{

            var lat = parseFloat(center.위도);
            var lng = parseFloat(center.경도);


            if (
                isNaN(lat) ||
                isNaN(lng) ||
                lat < 33 ||
                lat > 39 ||
                lng < 124 ||
                lng > 132
            ) {{
                markers.push(null);
                infoWindows.push(null);
                return;
            }}


            var position = new kakao.maps.LatLng(lat, lng);


            var marker = new kakao.maps.Marker({{
                map: map,
                position: position,
                image: markerImage
            }});


            var directionsUrl =
                "https://map.kakao.com/link/search/" +
                center.주소 +
                " " +
                center.센터명;


            var content = `
                <div class="info-card">
                    <div class="info-title">${{center.센터명}}</div>
                    <div class="info-addr">${{center.주소}}</div>

                    <div class="info-actions">
                        <a href="tel:${{center.전화번호}}" class="info-phone">
                            📞 ${{center.전화번호}}
                        </a>

                        <a href="${{directionsUrl}}" target="_blank" class="info-direction">
                            🧭 길찾기
                        </a>
                    </div>
                </div>
            `;


            var info = new kakao.maps.InfoWindow({{
                content: content,
                removable: true
            }});


            kakao.maps.event.addListener(
                marker,
                "click",
                function() {{
                    openInfo(idx);
                    highlightCard(idx);
                }}
            );


            markers.push(marker);
            infoWindows.push(info);

            bounds.extend(position);

            validMarkerCount++;

        }});


        if (validMarkerCount > 0) {{

            if (validMarkerCount === 1) {{

                map.setCenter(
                    bounds.getSouthWest()
                );

                map.setLevel(4);

            }} else {{

                map.setBounds(bounds);

            }}

        }}


        map.relayout();


    }}, 60);

}}


// ============================================================
// SDK 스크립트를 삽입하고, 다운로드가 "완전히" 끝난 뒤(script.onload)에만
// kakao.maps.load(initMap)을 호출해서 initMap이 절대 먼저 실행되지 않도록 보장.
// ============================================================
(function() {{
    var script = document.createElement("script");

    script.src =
        "https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false";

    script.onload = function() {{
        kakao.maps.load(initMap);
    }};

    document.head.appendChild(script);
}})();
</script>

</body>
</html>
"""
    components.html(html, height=596)


# ==========================
# 1. 상단 필터 영역 (드롭다운 3개 + 조회 버튼을 한 줄/한 패널에 배치해서
#    라인하이트나 위치가 서로 어긋나지 않게 함)
# ==========================
with st.container(border=True):
    col_sido, col_sigungu, col_company, col_button = st.columns([1, 1, 1, 0.85])

    with col_sido:
        raw_sido = get_sido_list()
        sido_list = list(dict.fromkeys(["전체"] + raw_sido))
        selected_sido = st.selectbox("📍 시 / 도", sido_list)

    with col_sigungu:
        if selected_sido == "전체":
            sigungu_list = ["전체"]
        else:
            raw_sigungu = get_sigungu_list(selected_sido)
            sigungu_list = list(dict.fromkeys(["전체"] + raw_sigungu))

        selected_sigungu = st.selectbox(
            "🏙️ 시 / 군 / 구",
            sigungu_list,
            disabled=(selected_sido == "전체"),
        )

    with col_company:
        brand_keys = get_manufacturer_list()
        default_index = (
            brand_keys.index(applied_company) if applied_company in brand_keys else 0
        )
        selected_company = st.selectbox("🏭 제조사", brand_keys, index=default_index)

    # 화면에 보이는 선택값이 마지막으로 "조회하기"를 눌렀던 조건과 다르면
    # 아직 반영되지 않은 변경사항이 있다는 뜻 -> 버튼을 눈에 띄게 강조
    is_dirty = (
        selected_sido != st.session_state["applied_sido"]
        or selected_sigungu != st.session_state["applied_sigungu"]
        or selected_company != st.session_state["applied_company"]
    )

    with col_button:
        # 셀렉트박스들과 같은 높이의 라벨 자리(투명)를 만들어서
        # 버튼이 셀렉트박스와 정확히 같은 줄에 오도록 맞춤
        st.markdown(
            '<div class="field-label-spacer">조회</div>', unsafe_allow_html=True
        )
        btn_key = "apply_btn_dirty" if is_dirty else "apply_btn_clean"
        with st.container(key=btn_key):
            button_label = "🔍 변경사항 조회" if is_dirty else "🔍 조회하기"
            search_clicked = st.button(button_label, use_container_width=True)

if is_dirty:
    st.markdown(
        '<div class="dirty-hint">● 선택을 변경했어요 · "조회하기"를 눌러야 결과에 반영됩니다</div>',
        unsafe_allow_html=True,
    )


# ==========================
# 데이터 처리 및 조회 버튼 눌렀을 때만 조건/컬러 변경 적용
# ==========================
if search_clicked:
    st.session_state["applied_company"] = selected_company
    st.session_state["applied_sido"] = selected_sido
    st.session_state["applied_sigungu"] = selected_sigungu
    st.session_state["search_token"] += 1
    st.session_state["map_result"] = get_service_centers(
        company=selected_company,
        sido=selected_sido,
        sigungu=selected_sigungu,
    )
    st.rerun()

# 최초 실행 시 데이터 로드
if "map_result" not in st.session_state:
    st.session_state["map_result"] = get_service_centers(
        company=st.session_state["applied_company"],
        sido=st.session_state["applied_sido"],
        sigungu=st.session_state["applied_sigungu"],
    )

df = pd.DataFrame(st.session_state["map_result"])

# 라벨에 적용된 상태 반영
app_sido = st.session_state["applied_sido"]
app_sigungu = st.session_state["applied_sigungu"]

if app_sido == "전체":
    location_label = "전국"
elif app_sigungu == "전체":
    location_label = app_sido
else:
    location_label = f"{app_sido} {app_sigungu}"


# ==========================
# 2. 결과 요약 바 (전체 너비로 중간 배치)
# ==========================
st.markdown(
    f"""
    <div class="result-bar">
        <span class="result-location"><b>{location_label}</b> · <b>{applied_company}</b> 서비스센터 검색 결과</span>
        <span class="result-count">{len(df)}<span>곳</span></span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================
# 3. 지도 + 리스트 영역 (하나의 컴포넌트로 결합)
# ==========================
if df.empty:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🗺️</div>
            해당 조건에 등록된 서비스센터 검색 결과가 없습니다.<br>
            다른 지역이나 제조사를 선택해보세요.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    render_map_and_list(df, ACCENT, ACCENT_DARK, st.session_state["search_token"])
