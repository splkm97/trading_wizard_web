# Research: Turn-Based Trading Simulation Game

**Date**: 2026-01-08
**Feature**: 001-trading-simulation

## Research Summary

기존 Trading Wizard Web 시스템을 분석하여 시뮬레이션 게임 구현에 필요한 기술적 결정을 도출함.

---

## 1. 지표 계산 로직 재사용

### Decision
기존 `backend/src/core/indicators.py`의 함수들을 그대로 재사용한다.

### Rationale
- `calculate_all_indicators()`: 볼린저 밴드, RSI, MACD, Volume Ratio 계산이 이미 구현됨
- `calculate_confidence_score()`: 0-100점 신뢰도 점수 계산 로직 존재
- 기존 백테스트 시스템에서 검증된 코드

### Alternatives Considered
- 새로 구현: 불필요한 중복, 일관성 문제 발생 가능
- 외부 라이브러리 (TA-Lib): 추가 의존성, 기존 시스템과 결과 불일치 위험

---

## 2. 게임 상태 저장 전략

### Decision
새로운 DB 모델 (`GameSession`, `SimulatedPosition`, `SimulatedTrade`)을 생성하고, 기존 실제 포트폴리오 모델과 분리한다.

### Rationale
- 실제 거래 기록(`Trade`, `Position`)과 시뮬레이션 데이터 혼동 방지
- 게임 세션별 독립적인 상태 관리 가능
- 게임 삭제/리셋 시 실제 데이터 영향 없음

### Alternatives Considered
- 기존 모델에 `is_simulated` 플래그 추가: 쿼리 복잡성 증가, 데이터 오염 위험
- 별도 DB 사용: 과도한 복잡성, 인프라 비용

---

## 3. 프론트엔드 상태 관리

### Decision
React useState/useReducer와 API 호출 기반 상태 관리. 전역 상태 라이브러리 미사용.

### Rationale
- 게임 상태는 서버(DB)가 source of truth
- 현재 앱 규모에서 Redux/Zustand 등은 과잉
- 기존 `AuthContext` 패턴과 일관성 유지

### Alternatives Considered
- Redux: 보일러플레이트 과다, 학습 곡선
- Zustand/Jotai: 추가 의존성, 현재 규모에 불필요

---

## 4. 차트 라이브러리

### Decision
기존 백테스트 페이지에서 사용 중인 차트 라이브러리/컴포넌트 재사용.

### Rationale
- `BacktestPortfolioChart` 컴포넌트 존재
- 일관된 UI/UX
- 추가 의존성 없음

### Alternatives Considered
- 새 차트 라이브러리 도입 (Chart.js, ApexCharts): 불필요한 번들 크기 증가

---

## 5. 턴 진행 시 데이터 로딩

### Decision
턴 진행 시 해당 날짜의 KOSPI 100 종목 데이터를 yfinance에서 가져오고, 지표를 실시간 계산한다.

### Rationale
- 과거 데이터는 yfinance에서 안정적으로 제공
- 지표 계산은 빠름 (< 1초 per stock batch)
- 사전 계산된 데이터 캐시보다 구현 단순

### Alternatives Considered
- 전체 기간 데이터 사전 로드: 초기 로딩 시간 과다, 메모리 사용 증가
- 별도 데이터 서버: 인프라 복잡성

### Performance Consideration
- KOSPI 100 종목 지표 계산: ~2-3초 (acceptable for turn-based game)
- 필요 시 백그라운드 프리페칭으로 최적화 가능

---

## 6. 백테스트 리포트 재사용

### Decision
기존 `BacktestResultDetailResponse` 형식과 `backtest/` UI 컴포넌트를 그대로 활용한다.

### Rationale
- FR-015, FR-016 요구사항: 기존 백테스트 시스템과 호환
- `BacktestDetail`, `BacktestPortfolioChart`, `BacktestStockRanking` 등 재사용 가능
- 개발 시간 단축

### Implementation
- 게임 거래 기록을 기존 백테스트 JSON 형식으로 변환하는 함수 구현
- 모달에서 기존 백테스트 상세 컴포넌트 렌더링

---

## 7. API 엔드포인트 설계

### Decision
RESTful 패턴, 기존 API 구조와 일관성 유지.

```
POST   /api/simulation/sessions          # 새 게임 생성
GET    /api/simulation/sessions          # 게임 목록
GET    /api/simulation/sessions/{id}     # 게임 상태 조회
POST   /api/simulation/sessions/{id}/turn # 턴 진행
POST   /api/simulation/sessions/{id}/trade # 거래 실행
GET    /api/simulation/sessions/{id}/recommendations # 추천 종목
GET    /api/simulation/sessions/{id}/report # 백테스트 리포트
DELETE /api/simulation/sessions/{id}     # 게임 삭제
```

### Rationale
- 기존 `/api/backtest`, `/api/portfolio` 패턴과 일관
- 리소스 중심 설계
- 프론트엔드 구현 용이

---

## 8. 인증 통합

### Decision
기존 PEM 파일 기반 인증 미들웨어 (`get_current_user`) 재사용.

### Rationale
- FR-000 요구사항
- 기존 인프라 활용
- 추가 구현 불필요

### Implementation
- 모든 `/api/simulation/*` 엔드포인트에 `Depends(get_current_user)` 적용
- GameSession 모델에 `user_id` FK 포함

---

## Resolved Clarifications

| Topic | Resolution |
|-------|------------|
| 지표 계산 방식 | 기존 `core/indicators.py` 재사용 |
| 데이터 저장소 | SQLite/PostgreSQL, 새 모델 생성 |
| 차트 라이브러리 | 기존 컴포넌트 재사용 |
| 상태 관리 | Server-side state + React local state |
| API 설계 | RESTful, 기존 패턴 따름 |
