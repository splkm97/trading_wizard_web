# Data Model: MACD & RSI Contrarian Signal Strategy

**Feature**: 002-macd-rsi-contrarian-strategy
**Date**: 2026-01-10

## Overview

This document defines the data entities, relationships, and validation rules for the contrarian signal strategy.

---

## Entities

### 1. ContrarianSignal (Runtime Data Structure)

Represents a detected MACD/RSI contrarian buy opportunity. This is a runtime dataclass, not persisted to database.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| stock_code | string | 6-digit Korean stock code | Pattern: `^\d{6}$` |
| stock_name | string | Korean stock name | Non-empty |
| signal_type | string | Always "BUY" for contrarian signals | Enum: "BUY" |
| confidence_score | float | 0-100 score based on RSI tier + MACD bonus | Range: 0.0 - 100.0 |
| current_price | float | Latest closing price in KRW | Positive |
| rsi | float | RSI(14) value | Range: 0.0 - 100.0 |
| macd | float | MACD line value | Any float |
| macd_signal | float | Signal line value | Any float |
| macd_histogram | float | MACD - Signal | Any float |
| signal_date | date | Date of golden cross detection | Valid date |

**Relationships**: None (standalone signal)

**Lifecycle**:
- Created: When scan detects valid contrarian conditions
- Used: Displayed in frontend signal panel
- Discarded: After API response (not persisted)

---

### 2. ContrarianSettings (Extension of UserSettings)

New fields added to existing `UserSettings` database model for MACD/RSI strategy configuration.

| Field | Type | Default | Description | Validation |
|-------|------|---------|-------------|------------|
| macd_rsi_rsi_period | integer | 14 | RSI calculation period | Range: 5 - 30 |
| macd_rsi_rsi_threshold | float | 30.0 | RSI oversold threshold | Range: 10.0 - 50.0 |
| macd_rsi_macd_fast_period | integer | 12 | MACD fast EMA period | Range: 5 - 20 |
| macd_rsi_macd_slow_period | integer | 26 | MACD slow EMA period | Range: 15 - 50 |
| macd_rsi_macd_signal_period | integer | 9 | MACD signal line period | Range: 5 - 15 |
| macd_rsi_confidence_threshold | float | 40.0 | Minimum confidence to display | Range: 0.0 - 100.0 |

**Relationships**: One-to-one with User

**Constraints**:
- `macd_rsi_macd_fast_period` < `macd_rsi_macd_slow_period` (enforced at API layer)

**Lifecycle**:
- Created: When user first accesses settings (defaults applied)
- Updated: Via PUT /settings endpoint
- Read: At each signal scan to apply user preferences

---

### 3. AppliedContrarianSettings (API Response Structure)

Settings snapshot included in API responses for transparency.

| Field | Type | Description |
|-------|------|-------------|
| rsi_period | integer | RSI period used for this scan |
| rsi_threshold | float | RSI threshold used |
| macd_fast_period | integer | MACD fast period used |
| macd_slow_period | integer | MACD slow period used |
| macd_signal_period | integer | MACD signal period used |
| confidence_threshold | float | Minimum confidence applied |

**Purpose**: Allows frontend to display what settings generated the current results.

---

## State Transitions

### Signal Detection Flow

```
Stock Data Loaded
      │
      ▼
Calculate Indicators (RSI, MACD)
      │
      ▼
Check RSI ≤ threshold ─── No ──► Exclude Stock
      │
      Yes
      ▼
Check MACD Golden Cross ─── No ──► Exclude Stock
      │
      Yes
      ▼
Calculate Confidence Score
      │
      ▼
Score ≥ threshold ─── No ──► Exclude Stock
      │
      Yes
      ▼
Create ContrarianSignal ──► Include in Response
```

---

## Data Validation Rules

### Frontend Input Validation (Settings Form)

| Field | Rule | Error Message |
|-------|------|---------------|
| RSI Period | 5 ≤ value ≤ 30 | "RSI period must be between 5 and 30" |
| RSI Threshold | 10 ≤ value ≤ 50 | "RSI threshold must be between 10 and 50" |
| MACD Fast | 5 ≤ value ≤ 20 | "MACD fast period must be between 5 and 20" |
| MACD Slow | 15 ≤ value ≤ 50 | "MACD slow period must be between 15 and 50" |
| MACD Signal | 5 ≤ value ≤ 15 | "MACD signal period must be between 5 and 15" |
| Confidence | 0 ≤ value ≤ 100 | "Confidence threshold must be between 0 and 100" |

### Backend Validation (Pydantic)

```python
class ContrarianSettingsUpdate(BaseModel):
    macd_rsi_rsi_period: Optional[int] = Field(None, ge=5, le=30)
    macd_rsi_rsi_threshold: Optional[float] = Field(None, ge=10.0, le=50.0)
    macd_rsi_macd_fast_period: Optional[int] = Field(None, ge=5, le=20)
    macd_rsi_macd_slow_period: Optional[int] = Field(None, ge=15, le=50)
    macd_rsi_macd_signal_period: Optional[int] = Field(None, ge=5, le=15)
    macd_rsi_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)

    @model_validator(mode='after')
    def validate_macd_periods(self):
        if self.macd_rsi_macd_fast_period and self.macd_rsi_macd_slow_period:
            if self.macd_rsi_macd_fast_period >= self.macd_rsi_macd_slow_period:
                raise ValueError("Fast period must be less than slow period")
        return self
```

---

## Database Schema Changes

### Migration: Add Contrarian Settings Columns

```sql
-- Add MACD/RSI contrarian strategy settings to user_settings table
ALTER TABLE user_settings ADD COLUMN macd_rsi_rsi_period INTEGER DEFAULT 14;
ALTER TABLE user_settings ADD COLUMN macd_rsi_rsi_threshold FLOAT DEFAULT 30.0;
ALTER TABLE user_settings ADD COLUMN macd_rsi_macd_fast_period INTEGER DEFAULT 12;
ALTER TABLE user_settings ADD COLUMN macd_rsi_macd_slow_period INTEGER DEFAULT 26;
ALTER TABLE user_settings ADD COLUMN macd_rsi_macd_signal_period INTEGER DEFAULT 9;
ALTER TABLE user_settings ADD COLUMN macd_rsi_confidence_threshold FLOAT DEFAULT 40.0;
```

**Rollback**:
```sql
ALTER TABLE user_settings DROP COLUMN macd_rsi_rsi_period;
ALTER TABLE user_settings DROP COLUMN macd_rsi_rsi_threshold;
ALTER TABLE user_settings DROP COLUMN macd_rsi_macd_fast_period;
ALTER TABLE user_settings DROP COLUMN macd_rsi_macd_slow_period;
ALTER TABLE user_settings DROP COLUMN macd_rsi_macd_signal_period;
ALTER TABLE user_settings DROP COLUMN macd_rsi_confidence_threshold;
```

---

## Sample Data

### Example ContrarianSignal

```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "signal_type": "BUY",
  "confidence_score": 85.5,
  "current_price": 72500.0,
  "rsi": 18.5,
  "macd": -450.25,
  "macd_signal": -520.80,
  "macd_histogram": 70.55,
  "signal_date": "2026-01-10"
}
```

### Example Applied Settings

```json
{
  "rsi_period": 14,
  "rsi_threshold": 30.0,
  "macd_fast_period": 12,
  "macd_slow_period": 26,
  "macd_signal_period": 9,
  "confidence_threshold": 40.0
}
```
