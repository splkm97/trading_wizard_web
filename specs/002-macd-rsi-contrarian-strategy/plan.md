# Implementation Plan: MACD & RSI Contrarian Signal Recommendation System

**Branch**: `002-macd-rsi-contrarian-strategy` | **Date**: 2026-01-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-macd-rsi-contrarian-strategy/spec.md`

## Summary

Implement a new trading strategy that identifies contrarian buy signals based on RSI oversold conditions (≤30) combined with MACD golden cross events. This strategy complements the existing Bollinger Band Squeeze strategy by targeting stocks showing bullish momentum reversal from oversold territory. The feature includes a dedicated frontend page, backend signal scanner, configurable settings, and follows signals-only display (no position sizing).

## Technical Context

**Language/Version**: Python 3.9+ (Backend), TypeScript (Frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, React 18+, Vite 5+, Tailwind CSS 3.x, yfinance, pandas
**Storage**: SQLite (dev), PostgreSQL (prod) - existing schema extended for new settings
**Testing**: pytest (backend), Playwright (frontend E2E)
**Target Platform**: Web application (Docker deployment)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 5-second page load for 100-stock scan (SC-001)
**Constraints**: Reuse existing multi-tier caching (memory → PostgreSQL → yfinance)
**Scale/Scope**: KOSPI Top 100 stocks, single user settings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | ✅ PASS | Reuses existing `calculate_rsi()`, `calculate_macd()` - deterministic calculations |
| II. Type Safety & Validation | ✅ PASS | Will use Pydantic models for API, TypeScript strict mode for frontend |
| III. Test Coverage Required | ✅ PASS | Unit tests for contrarian signal logic, integration tests for API |
| IV. Separation of Concerns | ✅ PASS | Scanner logic in `wizard/`, API in `api/`, UI in `components/` |
| V. Security & Authentication | ✅ PASS | Inherits existing JWT auth for settings endpoints |
| VI. Settings Consistency | ✅ PASS | MACD/RSI settings added to UserSettings, applied at scan time, returned in API response |

**Gate Result**: PASS - No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-macd-rsi-contrarian-strategy/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.yaml         # OpenAPI spec for new endpoints
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── recommendations.py      # Existing - extend or add new endpoint
│   │   ├── contrarian.py           # NEW: Dedicated endpoint for MACD/RSI signals
│   │   └── settings.py             # Existing - extend for MACD/RSI params
│   ├── models/
│   │   └── user_settings.py        # Existing - add MACD/RSI fields
│   ├── services/
│   │   └── settings_service.py     # Existing - include new fields
│   └── wizard/
│       ├── signal_scanner.py       # Existing - add contrarian scan method
│       └── contrarian_scanner.py   # NEW: Dedicated scanner class (optional)
└── tests/
    ├── unit/
    │   └── test_contrarian_signals.py  # NEW: Unit tests for signal logic
    └── integration/
        └── test_contrarian_api.py      # NEW: API integration tests

frontend/
├── src/
│   ├── components/
│   │   └── contrarian/
│   │       ├── ContrarianSignalCard.tsx   # NEW: Signal display card
│   │       └── ContrarianPanel.tsx        # NEW: Main panel component
│   ├── pages/
│   │   └── ContrarianPage.tsx             # NEW: Dedicated strategy page
│   ├── services/
│   │   └── api.ts                         # Existing - add contrarian endpoints
│   └── types/
│       └── index.ts                       # Existing - add contrarian types
└── tests/
    └── e2e/
        └── contrarian.spec.ts             # NEW: E2E tests
```

**Structure Decision**: Follows existing web application pattern. New contrarian functionality added alongside Bollinger Band strategy with minimal changes to existing code.

## Complexity Tracking

> No violations detected. Table not required.
