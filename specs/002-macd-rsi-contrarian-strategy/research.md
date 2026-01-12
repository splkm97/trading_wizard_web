# Research: MACD & RSI Contrarian Signal Strategy

**Feature**: 002-macd-rsi-contrarian-strategy
**Date**: 2026-01-10

## Overview

This document consolidates research findings for implementing the MACD/RSI contrarian signal detection strategy.

---

## Decision 1: Scanner Architecture

### Decision
Extend the existing `SignalScanner` class with a new method `scan_for_contrarian_signals()` rather than creating a separate scanner class.

### Rationale
- The existing `SignalScanner` already handles multi-tier data caching, indicator calculation, and stock universe loading
- Adding a method follows the existing pattern (`scan_for_buy_signals`, `scan_for_sell_signals`)
- Reduces code duplication and maintains single source of truth for caching logic
- Existing indicator calculations (`calculate_rsi`, `calculate_macd`) are already called in `calculate_indicators()`

### Alternatives Considered
1. **Separate `ContrarianScanner` class**: Would require duplicating caching logic and data fetching; rejected for DRY violation
2. **Modifying `scan_for_buy_signals` with strategy parameter**: Would complicate existing tests and require significant refactoring; rejected for risk

---

## Decision 2: Confidence Scoring Algorithm

### Decision
Implement threshold-based tiered scoring as specified in clarifications:
- RSI ≤ 20: Base 80 points (High confidence - deeply oversold)
- RSI 20-25: Base 60 points (Medium confidence)
- RSI 25-30: Base 40 points (Low confidence)
- MACD histogram bonus: Up to +20 points based on histogram strength

### Rationale
- Tiered approach provides clear mental model for users
- Deeper oversold conditions (lower RSI) indicate higher probability of reversal
- MACD histogram strength confirms momentum shift
- Maximum score of 100 (80 base + 20 MACD bonus) aligns with existing Bollinger strategy scoring

### Implementation Formula
```python
def calculate_contrarian_confidence(rsi: float, macd_histogram: float, macd_signal: float) -> float:
    # Base score from RSI tier
    if rsi <= 20:
        base = 80.0
    elif rsi <= 25:
        base = 60.0
    else:  # 25 < rsi <= 30
        base = 40.0

    # MACD histogram bonus (0-20 points)
    if macd_histogram > 0 and macd_signal != 0:
        # Normalize histogram relative to signal strength
        ratio = min(abs(macd_histogram) / abs(macd_signal), 1.0)
        bonus = 20.0 * ratio
    else:
        bonus = 0.0

    return min(100.0, base + bonus)
```

### Alternatives Considered
1. **Weighted average (40% RSI + 60% MACD)**: Too continuous; harder for users to interpret thresholds
2. **Simple binary (High/Low only)**: Loses nuance of medium-confidence signals

---

## Decision 3: MACD Golden Cross Detection

### Decision
Define MACD golden cross as:
- Previous day: MACD line < Signal line
- Current day: MACD line ≥ Signal line

### Rationale
- Standard technical analysis definition
- "≥" on current day ensures we catch the exact crossing point, not just post-crossing
- Strict "previous day < Signal" ensures we only detect fresh crosses, not continuation

### Implementation
```python
def detect_macd_golden_cross(df: pd.DataFrame) -> bool:
    """Detect if MACD golden cross occurred on most recent trading day."""
    if len(df) < 2:
        return False

    current = df.iloc[-1]
    previous = df.iloc[-2]

    prev_macd = previous["MACD"]
    prev_signal = previous["MACD_Signal"]
    curr_macd = current["MACD"]
    curr_signal = current["MACD_Signal"]

    # Previous day: MACD below signal
    # Current day: MACD at or above signal
    return prev_macd < prev_signal and curr_macd >= curr_signal
```

### Alternatives Considered
1. **Include crosses from past N days**: Would dilute signal quality; rejected per spec edge case requirement
2. **Use histogram sign change**: Less precise than direct line comparison; rejected

---

## Decision 4: API Endpoint Design

### Decision
Create a dedicated endpoint `GET /contrarian/signals` separate from the existing `/recommendations` endpoint.

### Rationale
- Clear separation of strategies in the API
- Frontend can fetch strategy-specific data independently
- Easier to add strategy-specific filtering and parameters
- Follows REST resource separation principle

### Endpoint Specification
```
GET /contrarian/signals
Query Parameters:
  - max_results: int (default 10)
  - confidence_threshold: float (default 40)

Response:
{
  "signals": [...],
  "scanned_count": int,
  "signal_count": int,
  "applied_settings": {
    "rsi_period": 14,
    "rsi_threshold": 30,
    "macd_fast_period": 12,
    "macd_slow_period": 26,
    "macd_signal_period": 9,
    "confidence_threshold": 40
  }
}
```

### Alternatives Considered
1. **Add `strategy` parameter to existing `/recommendations`**: Would complicate existing endpoint and require frontend changes to existing pages; rejected
2. **Return combined signals from both strategies**: Would confuse the UI; users explicitly navigate to a specific strategy page

---

## Decision 5: Settings Model Extension

### Decision
Add new fields to existing `UserSettings` model rather than creating a separate settings table.

### New Fields
```python
# MACD/RSI Contrarian Strategy Settings
macd_rsi_rsi_period: int = 14
macd_rsi_rsi_threshold: float = 30.0
macd_rsi_macd_fast_period: int = 12
macd_rsi_macd_slow_period: int = 26
macd_rsi_macd_signal_period: int = 9
macd_rsi_confidence_threshold: float = 40.0
```

### Rationale
- Follows existing pattern of single UserSettings model
- Prefixing with `macd_rsi_` avoids collision with existing MACD fields used elsewhere
- Aligns with Constitution Principle VI (Settings Consistency)

### Migration
- Add columns with defaults to existing `user_settings` table
- No data migration needed; defaults apply automatically

---

## Decision 6: Frontend Page Structure

### Decision
Create `/contrarian` route with dedicated page component following existing `TradePage.tsx` pattern.

### Components
1. **ContrarianPage.tsx**: Main page with strategy description, navigation, signal panel
2. **ContrarianPanel.tsx**: Signal list with loading/empty/error states
3. **ContrarianSignalCard.tsx**: Individual signal display with expandable details

### Rationale
- Parallel structure to existing trade page enables code reuse patterns
- Dedicated page matches user story 4 (navigation between strategies)
- Signals-only display (no position sizing) simplifies card component

### Navigation
- Add "MACD/RSI Strategy" link to main navigation
- Add strategy switcher on both TradePage and ContrarianPage

---

## Decision 7: Minimum Data Requirements

### Decision
Require minimum 35 trading days of price history to generate valid signals.

### Rationale
- MACD slow period (26 days) + signal smoothing (9 days) = 35 days minimum for stable MACD
- RSI 14-day period is covered within this window
- Consistent with existing Bollinger strategy minimum (35 days)

### Edge Case Handling
- Stocks with insufficient data are silently excluded from scan
- No error message; simply omitted from results
- This matches existing behavior in `scan_for_buy_signals`

---

## Decision 8: Testing Strategy

### Decision
Three-tier testing approach aligned with Constitution Principle III.

### Test Coverage
1. **Unit Tests** (`test_contrarian_signals.py`):
   - `test_macd_golden_cross_detection`: Various crossing scenarios
   - `test_contrarian_confidence_scoring`: RSI tier calculations
   - `test_contrarian_signal_identification`: Combined RSI + MACD logic
   - `test_edge_cases`: RSI exactly 30, insufficient data, no signals

2. **Integration Tests** (`test_contrarian_api.py`):
   - `test_get_contrarian_signals_success`: Happy path with mock data
   - `test_applied_settings_in_response`: Settings snapshot verification
   - `test_empty_signals_response`: No signals found case

3. **E2E Tests** (`contrarian.spec.ts`):
   - Navigate to contrarian page
   - Verify signal cards render with expected fields
   - Test settings update flow
   - Test empty state message

### Mock Data
Create fixture with known RSI/MACD values to ensure deterministic test outcomes.

---

## Summary

All technical unknowns have been resolved. Key decisions:

| Area | Decision |
|------|----------|
| Scanner | Extend existing `SignalScanner` with new method |
| Confidence | Threshold-based tiers (80/60/40) + MACD bonus (0-20) |
| Golden Cross | Strict previous-day-below, current-day-at-or-above |
| API | Dedicated `/contrarian/signals` endpoint |
| Settings | Extend `UserSettings` with prefixed fields |
| Frontend | Dedicated `/contrarian` page with parallel structure |
| Data | 35-day minimum history requirement |
| Testing | Unit + Integration + E2E coverage |

**Ready for Phase 1: Design & Contracts**
