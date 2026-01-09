# Implementation Plan: Turn-Based Trading Simulation Game

**Branch**: `001-trading-simulation` | **Date**: 2026-01-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-trading-simulation/spec.md`

## Summary

턴제 기반 트레이딩 시뮬레이션 게임을 구현한다. KOSPI Top 100 종목 중 볼린저 밴드 점수 50점 이상인 종목을 매일(턴) 추천하고, 사용자가 보유 여부에 따라 동적으로 변하는 UI를 통해 매수/매도 결정을 내린다. 기존 백테스트 시스템의 지표 계산 로직과 UI 컴포넌트를 재사용하며, 새로운 GameSession 기반 상태 관리를 추가한다.

## Technical Context

**Language/Version**: Python 3.9+ (Backend), TypeScript (Frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, React 18+, Vite 5+, Tailwind CSS 3.x
**Storage**: SQLite (dev), PostgreSQL (prod option) - 기존 시스템과 동일
**Testing**: pytest (Backend), 기존 테스트 패턴 따름
**Target Platform**: Web (Desktop/Mobile responsive)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 
- 추천 종목 리스트 로딩 < 2초
- 종목 상세 차트 표시 < 1초
- 턴 진행 결과 반영 < 3초
**Constraints**: 
- 기존 PEM 파일 기반 인증 시스템 사용
- 기존 백테스트 JSON 형식과 100% 호환
- yfinance 데이터 기반 (2020년부터)
**Scale/Scope**: 단일 사용자 동시 1개 게임 세션, KOSPI 100 종목

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Data Integrity First | PASS | 기존 `core/indicators.py`의 결정론적 지표 계산 로직 재사용. 게임 상태는 DB에 원자적으로 저장. |
| II. Type Safety & Validation | PASS | Pydantic 모델로 모든 API 요청/응답 검증. TypeScript strict mode 사용. |
| III. Test Coverage Required | PASS | 게임 상태 전환 로직, 포트폴리오 계산에 대한 단위/통합 테스트 포함 예정. |
| IV. Separation of Concerns | PASS | `core/` - 순수 게임 로직, `services/` - 데이터 접근, `api/` - HTTP 변환. |
| V. Security & Authentication | PASS | 기존 PEM 기반 JWT 인증 사용. 게임 세션은 user_id로 스코프. |

**Gate Status**: PASS - 모든 원칙 준수

## Project Structure

### Documentation (this feature)

```text
specs/001-trading-simulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── simulation.py        # NEW: 시뮬레이션 게임 API 엔드포인트
│   ├── models/
│   │   └── game_session.py      # NEW: GameSession, SimulatedPosition, SimulatedTrade 모델
│   ├── services/
│   │   └── simulation_service.py # NEW: 게임 로직 서비스
│   ├── core/
│   │   └── indicators.py        # EXISTING: 지표 계산 (재사용)
│   └── wizard/
│       └── signal_scanner.py    # EXISTING: 신호 스캐너 (재사용)
└── tests/
    ├── unit/
    │   └── test_simulation_game.py   # NEW: 게임 로직 단위 테스트
    └── integration/
        └── test_simulation_api.py    # NEW: API 통합 테스트

frontend/
├── src/
│   ├── pages/
│   │   └── SimulationPage.tsx        # NEW: 게임 메인 페이지
│   ├── components/
│   │   └── simulation/               # NEW: 시뮬레이션 컴포넌트들
│   │       ├── GameSetupForm.tsx     # 게임 설정 폼
│   │       ├── StockRecommendationList.tsx  # 추천 종목 리스트
│   │       ├── StockDetailPanel.tsx  # 종목 상세 (차트 + 지표)
│   │       ├── TradeActionButtons.tsx # 동적 거래 버튼
│   │       ├── PortfolioPanel.tsx    # 포트폴리오 상태
│   │       ├── TurnProgressBar.tsx   # 턴 진행 상태
│   │       └── GameReportModal.tsx   # 백테스트 리포트 모달
│   ├── services/
│   │   └── simulation.ts             # NEW: 시뮬레이션 API 클라이언트
│   └── types/
│       └── simulation.ts             # NEW: 시뮬레이션 타입 정의
└── tests/
    └── (기존 테스트 패턴 따름)
```

**Structure Decision**: 기존 Web application 구조 (Option 2)를 확장. 새로운 도메인(`simulation`)을 각 레이어에 추가하는 방식으로 기존 코드와의 분리를 유지하면서도 공통 인프라(인증, DB, 지표 계산)를 재사용.

## Reusable Components (Existing)

기존 시스템에서 재사용 가능한 컴포넌트:

| Component | Location | Usage |
|-----------|----------|-------|
| 지표 계산 | `backend/src/core/indicators.py` | `calculate_all_indicators()`, `calculate_confidence_score()` |
| 신호 스캐너 | `backend/src/wizard/signal_scanner.py` | 볼린저 밴드 점수 계산 |
| 백테스트 결과 UI | `frontend/src/components/backtest/` | `BacktestPortfolioChart`, `BacktestResultCard` 등 |
| 인증 시스템 | `backend/src/auth/`, `frontend/src/contexts/AuthContext.tsx` | PEM 기반 JWT 인증 |
| API 클라이언트 | `frontend/src/services/api.ts` | HTTP 요청 래퍼 |
| 공통 UI | `frontend/src/components/common/` | Button, Card, Table, Modal 등 |

## Complexity Tracking

> **No violations detected** - 기존 아키텍처 패턴을 따르며, 새로운 복잡성 추가 없음.

| Item | Justification |
|------|---------------|
| 새 모델 3개 추가 | GameSession, SimulatedPosition, SimulatedTrade - 기존 Portfolio/Position/Trade와 분리하여 실제 거래와 시뮬레이션 데이터 구분 |
| 새 API 라우터 1개 | `/api/simulation` - 기존 API 구조와 일관성 유지 |
