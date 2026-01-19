# Trading Wizard Web

한국 주식시장(KOSPI/KOSDAQ)을 대상으로 **Bollinger Band Squeeze 전략**을 활용한 웹 기반 트레이딩 시스템입니다.

## 프로젝트 개요

이 프로젝트는 [bollinger-band-trade](https://github.com/yourusername/bollinger-band-trade)의 핵심 전략을 웹 애플리케이션으로 구현한 것입니다. 볼린저 밴드의 **Squeeze(수축) 패턴**을 활용하여 변동성 돌파 시점을 포착하고, Volume, RSI, MACD 필터로 신호 품질을 개선한 트레이딩 전략을 웹 인터페이스를 통해 제공합니다.

### 핵심 전략: Bollinger Band Squeeze

**Squeeze(수축)**란 볼린저 밴드의 상단과 하단 밴드 간격이 좁아지는 현상으로, 변동성이 낮아진 상태를 의미합니다. 이후 큰 가격 움직임(돌파)이 발생할 확률이 높아 매매 기회를 제공합니다.

## 주요 기능

### 1. 매매 신호 스캐닝

- **실시간 BUY 신호**: KOSPI/KOSDAQ 종목 중 Squeeze 돌파 종목 탐지
- **SELL 신호**: 관심종목 대상 손절/익절/중간밴드 이탈 신호
- **신뢰도 스코어링**: 0-100점 다단계 평가 시스템

### 2. 관심종목 관리 (Watchlist)

- 관심 종목 추가 및 관리
- 자동 인사이트 업데이트 (일일 추천 정보와 연동)
- 종목별 기술적 지표 및 신호 모니터링

### 3. 백테스팅

- 특정 기간 전략 성과 검증
- KOSPI 100 종목 대상 백테스트

### 4. 사용자 설정

- 신뢰도 임계값 조정 (기본: 55점)
- 손절매/익절매 비율 설정
- 관심 종목 리스트 관리

## 핵심 전략 컴포넌트

### 기술적 지표

**Bollinger Bands**
- Window: 12일
- 표준편차: 1.3배
- Squeeze 감지: 밴드폭이 10일 이동평균 대비 55% 이하

**RSI (Relative Strength Index)**
- Period: 14일
- 중립구간: 30-70

**MACD**
- Fast Period: 12일
- Slow Period: 26일
- Signal Period: 9일

**Volume Ratio**
- 20일 평균 거래량 대비 비율

### 신뢰도 스코어링 시스템

```
Base Score    25점  (Bollinger Squeeze 돌파 - 항상 부여)
+ Volume      25점  (거래량 1.0x ~ 2.0x 선형 스케일)
+ RSI         20점  (50 최적, 30/70에서 0점)
+ MACD        30점  (Histogram 양수, Signal 대비 비율)
= Total      100점

기본 임계값: 55점 (설정 가능)
```

### 매매 조건

**BUY 신호 조건**
1. 가격이 상단 볼린저 밴드 돌파
2. 최근 5일 내 Squeeze 상태였거나 밴드폭 확장 중
3. 신뢰도 점수 >= 임계값 (기본 55점)

**SELL 신호 조건**
- 손절매: 기준가 대비 -4.5% (설정 가능)
- 익절매: 기준가 대비 +12.0% (설정 가능)
- 중간밴드 이탈: 가격이 중간 밴드 하향 돌파 (선택적)

> **참고**: 이 시스템은 매매 신호를 제공하는 것이며, 실제 매매는 사용자가 직접 수행해야 합니다. 포지션 추적이나 자동 매매 기능은 제공하지 않습니다.

## 프로젝트 구조

```
trading_wizard_web/
├── README.md
├── docker-compose.yml          # Docker 배포 설정
├── backend/                    # FastAPI 백엔드
│   ├── src/
│   │   ├── main.py            # 애플리케이션 진입점
│   │   ├── api/               # API 라우터
│   │   │   ├── auth.py        # 인증 API
│   │   │   ├── watchlists.py  # 관심종목 관리
│   │   │   ├── stocks.py      # 종목 정보
│   │   │   ├── recommendations.py  # 매매 추천
│   │   │   ├── backtest.py    # 백테스팅
│   │   │   ├── settings.py    # 사용자 설정
│   │   │   └── health.py      # 헬스체크
│   │   ├── core/              # 핵심 비즈니스 로직
│   │   │   ├── indicators.py  # 기술적 지표 계산
│   │   │   ├── signal_scanner.py  # 신호 스캐너
│   │   │   ├── recommendation.py  # 추천 로직
│   │   │   └── config.py      # 설정 관리
│   │   ├── models/            # 데이터 모델 (SQLAlchemy)
│   │   │   ├── user.py        # 사용자
│   │   │   ├── watchlist.py   # 관심종목
│   │   │   └── user_settings.py  # 사용자 설정
│   │   ├── services/          # 서비스 레이어
│   │   ├── auth/              # 인증 (JWT)
│   │   └── db/                # 데이터베이스
│   ├── data/                  # 데이터 파일
│   │   ├── kospi_top100.txt   # KOSPI 100 종목
│   │   └── stock_names_kr.json  # 종목명 매핑
│   └── .env.example           # 환경 변수 예시
├── frontend/                  # 프론트엔드 (Vite)
├── mockup/                    # HTML 목업
└── data/                      # 공유 데이터
```

## 기술 스택

- **Backend**: Python 3.9+, FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: JWT (JSON Web Token)
- **Data Source**: Yahoo Finance (yfinance)
- **Frontend**: Vite (React/Vue)
- **Deployment**: Docker, Docker Compose
- **Technical Analysis**: pandas, numpy

## 설치 방법

### Docker를 이용한 설치 (권장)

```bash
# 저장소 클론
git clone https://github.com/yourusername/trading_wizard_web.git
cd trading_wizard_web

# 환경 변수 설정
cp backend/.env.example backend/.env
# .env 파일 편집하여 JWT_SECRET_KEY 설정

# Docker Compose로 실행
docker-compose up -d
```

### 수동 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/trading_wizard_web.git
cd trading_wizard_web

# 백엔드 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 백엔드 실행
uvicorn src.main:app --reload --port 8000
```

## 빠른 시작

### 1. 서버 실행

```bash
# Docker 사용
docker-compose up -d

# 또는 수동 실행
cd backend && uvicorn src.main:app --reload --port 8000
```

### 2. API 문서 확인

브라우저에서 `http://localhost:8000/docs` 접속하여 Swagger UI 확인

### 3. 헬스체크

```bash
curl http://localhost:8000/api/health
```

## API 엔드포인트

### Health

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 서버 상태 확인 |

### Auth (인증)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 (JWT 발급) |
| GET | `/api/auth/me` | 현재 사용자 정보 |

### Stocks (종목)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/stocks` | 종목 검색 |
| GET | `/api/stocks/{code}` | 종목 상세 정보 |
| GET | `/api/stocks/{code}/price` | 현재가 조회 |

### Watchlists (관심종목)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/watchlists` | 관심종목 리스트 조회 |
| POST | `/api/watchlists` | 관심종목 리스트 생성 |
| DELETE | `/api/watchlists/{id}` | 관심종목 리스트 삭제 |

### Recommendations (매매 추천)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/recommendations/buy` | BUY 신호 스캔 |
| GET | `/api/recommendations/sell` | SELL 신호 스캔 |

### Backtest (백테스팅)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/backtest` | 백테스트 실행 |
| GET | `/api/backtest/{id}` | 백테스트 결과 조회 |

### Settings (설정)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/settings` | 사용자 설정 조회 |
| PUT | `/api/settings` | 설정 업데이트 |

## 환경 변수 설정

`.env` 파일 설정:

```bash
# Database
DATABASE_URL=sqlite:///./data/trading_wizard.db

# JWT
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

**주의**: 프로덕션 환경에서는 반드시 `JWT_SECRET_KEY`를 안전한 값으로 변경하세요.

## Docker 배포

### docker-compose.yml 설정

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/trading_wizard.db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-changeme-dev-secret-key}
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
```

### 배포 명령어

```bash
# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f backend

# 중지
docker-compose down
```

## 참고 자료

- [bollinger-band-trade](https://github.com/yourusername/bollinger-band-trade) - 핵심 전략 CLI 도구
- [Bollinger Bands](https://en.wikipedia.org/wiki/Bollinger_Bands) - Wikipedia
- [Bollinger Band Squeeze](https://www.investopedia.com/articles/trading/09/bollinger-band-squeeze.asp) - Investopedia
- [RSI (Relative Strength Index)](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD](https://www.investopedia.com/terms/m/macd.asp)
- [Yahoo Finance API](https://github.com/ranaroussi/yfinance) - yfinance

## 주의사항

**이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.**

- 실제 투자에 사용 시 발생하는 손실에 대해 책임지지 않습니다
- 과거 데이터 기반 백테스팅 결과가 미래 수익을 보장하지 않습니다
- Bollinger Band Squeeze 전략은 상승장/횡보장에 강하지만 하락장에 취약합니다
- 실제 투자 전 충분한 검증과 리스크 관리가 필수입니다
- 개인 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다

## 라이선스

MIT License

## 문의

프로젝트 관련 문의나 버그 리포트는 GitHub Issues를 이용해주세요.
