# 🚗 자동차 리콜·결함 안전 대시보드 — 차모아

**안전한 드라이빙의 시작, 차모아**

SKN35-1st-2Team 프로젝트

---

## 📌 프로젝트 소개

**차모아**는 제조사·차종별 자동차 리콜 및 결함 정보를 한눈에 확인할 수 있는 Streamlit 기반 웹 대시보드입니다. 리콜 현황 조회, 통계 분석, 관련 뉴스, 서비스센터 위치, FAQ, 커뮤니티 기능을 통합 제공하여 사용자가 안전한 차량 정보를 쉽게 얻을 수 있도록 돕습니다.

## 👥 팀원 및 역할

| 이름 | 메인 담당 | 서브 담당 |
|---|---|---|
| 김도영 | Crawling, DB, Git 관리 | Chart 페이지 구현 |
| 고은하 | Crawling (기업별 FAQ) | Streamlit FAQ 페이지 구현 |
| 박민하 | Streamlit (리콜 뉴스·커뮤니티 페이지) | DB |
| 박찬룡 | Crawling, DB, Git 관리 | 정비소·지도(Kakao Map) 구현 |
| 황건우 | DB, ERD 설계 | 조회 페이지 구현 |

## 🛠 기술 스택

- **Frontend/UI**: Streamlit (Multi-page App)
- **Backend/Data**: Python
- **Database**: MySQL
- **Crawling**: Selenium, BeautifulSoup
- **지도 API**: Kakao Map API

---

## 🗂 ERD 설계

제조사를 중심으로 차량·리콜·서비스센터·커뮤니티 데이터를 연결하는 구조로 설계했습니다.

### 주요 테이블

- **manufacturer**: 제조사 정보 (id, name)
- **car_model**: 차량 모델 정보 (id, manufacturer_id FK, name)
- **car_recall**: 리콜 정보 (id, car_model_id FK, recall_start_date, recall_count, recall_reason)
- **service_center**: 서비스센터 정보 (id, manufacturer_id FK, name, address, phone, latitude, longitude)
- **posts**: 커뮤니티 게시글 (id, manufacturer_id FK, car_model_id FK, title, content, category, author, password, likes, views, created_at, updated_at)
- **comments**: 게시글 댓글 (id, post_id FK, content, author, password, created_at, updated_at)
- **news**: 리콜/결함 관련 뉴스 (독립 테이블)
- **faq**: 자주 묻는 질문 (독립 테이블)
- **legal_dong**: 법정동 정보 (독립 테이블)

### 설계 변경 이력 — 스키마 정규화

**BEFORE**: `car_recall` 테이블에 제조사명·모델명을 문자열(VARCHAR)로 직접 저장 → 리콜 건마다 제조사·모델 정보가 중복 저장되고, 정보 수정 시 여러 행을 동시에 수정해야 하는 갱신 이상(Update Anomaly) 발생

**AFTER**: `manufacturer` / `car_model` 테이블을 분리하고, `car_recall`은 `car_model_id`(FK)만 참조하도록 정규화하여 데이터 중복과 갱신 이상 문제를 해결

---

## 🏗 시스템 설계

### 아키텍처

```
사용자(브라우저)
      ↓
Streamlit Multi-page App
      ↓
Python (데이터 처리·백엔드 로직)
      ↓
MySQL DB (car_recall 등 정규화된 데이터)
```

### 페이지 구성 (총 7개)

| 페이지 | 설명 |
|---|---|
| Home | 리콜 현황·최근 뉴스·서비스센터를 한눈에 요약 |
| Chart | 제조사별 리콜 건수 추이 및 위험도 비교 분석 |
| Search | 브랜드·차종·결함 키워드로 리콜 이력 상세 검색 |
| FAQ | 리콜 신고 절차 등 자주 묻는 질문 안내 |
| News | 리콜·결함 관련 최신 뉴스 검색 및 목록 제공 |
| Service Center | 지역·제조사별 공식 서비스센터 위치 지도 |
| Community | 리콜 경험과 대응 정보를 공유하는 게시판 |

### Search 페이지 (개발 중)

`pages/search.py` — 현재 UI 우선 구현 단계로 DB 연동은 임시 제거, 추후 재연결 예정

- 브랜드 선택 (selectbox, 하드코딩 리스트: 현대자동차/기아/벤츠/BMW/폭스바겐)
- 차량 모델 키워드 검색 (자유 텍스트)
- 결함 키워드 검색 (자유 텍스트)

**검토 중인 개선 요소**: 사이드바 필터 분리, `st.session_state`로 검색 조건 유지, `st.tabs`로 결과 구분, 로딩 스피너, CSV 다운로드

---

## 📁 폴더 구조

기존 emotion_diary(감정일기) Streamlit 프로젝트 구조를 참고하여 표준화했습니다.

```
SKN35-1st-2Team/
│
├─ crawled/        # 크롤링한 원본 데이터
├─ data/           # 서비스에서 사용하는 데이터
├─ database/       # SQL 및 DB 관리
│
├─ src/
│  ├─ app/         # Streamlit 화면
│  ├─ crawlers/    # Selenium · BeautifulSoup 크롤러
│  ├─ db/          # DB 연결 및 조회 로직
│  └─ utils/       # 공통 함수
│
├─ .env            # 환경설정
└─ README.md       # 프로젝트 설명
```

### 폴더 구조 표준화의 효과

- ✅ **모듈 임포트 오류 예방**: `pages/` 내 여러 파일에서 공통 모듈 참조 시 경로 문제 감소
- ✅ **유지보수성 향상**: 기능별 파일 분리로 필요한 코드를 빠르게 찾고 수정 가능
- ✅ **협업 효율성 증대**: 동일한 디렉터리 구조·규칙으로 파일 위치 예측 용이
- ✅ **팀 협업 충돌 최소화**: 담당 페이지 파일 분리로 동시 작업 시 충돌 감소

---

## 🐛 문제 해결 (Troubleshooting)

### ① DB 이슈

| 문제 | 해결 |
|---|---|
| DB 적재 스크립트(`connect_db.py`) 실행 시 기존 테이블 스키마의 PK(`id`) 유실 | 적재 모드를 `if_exists='replace'`에서 `if_exists='append'`로 변경하여 스키마 보존 및 데이터 추가 적재 |
| Streamlit 앱 실행 중 DB 커넥션 점유로 DBeaver에서 테이블 Drop 에러 발생 | VS Code의 Streamlit 프로세스를 중지해 DB 세션 해제 후 스키마 수정 진행 |
| 검색창에서 Enter 입력 시 검색이 실행되지 않고 버튼 클릭만 동작 | 디자인 개선 중 `st.form`을 제거하면서 발생 → `st.form` + `st.form_submit_button` 구조로 복원하여 해결 |

### ② 구조·개발 이슈

| 문제 | 해결 |
|---|---|
| `car_recall`에 제조사·모델명을 문자열로 직접 저장해 중복·오타 문제 발생 | `manufacturer` / `car_model` 테이블 분리 후 FK(`car_model_id`)로 참조하도록 정규화 |
| 멀티페이지 앱에서 `pages/` 하위 파일 간 공통 모듈 임포트 경로 오류 반복 | 폴더 구조 표준화 및 임포트 경로 점검으로 오류 재현 지점 제거 |
| 검색 페이지 개발 중 DB 연동 로직이 UI 완성 속도를 저해 | DB 연동을 임시 제거하고 UI(브랜드 selectbox, 키워드 입력)를 먼저 완성 → 이후 단계적 DB 재연결 예정 |

### ③ 기능 구현 이슈

| 문제 | 해결 |
|---|---|
| 서비스센터 주소 크롤링 시 위도·경도 좌표가 없어 카카오맵 마커 표시 불가 | 별도 util 함수를 만들어 카카오맵 API로 주소값을 위도·경도로 변환 |
| FAQ 페이지에서 `st.expander` 펼침/접힘 상태가 인터랙션마다 초기화되는 문제 | `st.button` + `st.session_state`로 상태 관리 로직 구축, UI 제어 안정성 확보 |

---

## 🙏 감사합니다
