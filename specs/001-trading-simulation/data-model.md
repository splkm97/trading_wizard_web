# Data Model: Turn-Based Trading Simulation Game

**Date**: 2026-01-08
**Feature**: 001-trading-simulation

## Entity Relationship Overview

```
User (existing)
  │
  └──< GameSession (1:N)
         │
         ├──< SimulatedPosition (1:N)
         │
         └──< SimulatedTrade (1:N)
```

---

## Entities

### GameSession

시뮬레이션 게임 세션. 사용자별 독립적인 게임 인스턴스를 관리.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 고유 식별자 |
| user_id | UUID | FK(User), NOT NULL, INDEX | 소유 사용자 |
| name | VARCHAR(100) | NULLABLE | 게임 이름 (선택) |
| start_date | DATE | NOT NULL | 시뮬레이션 시작일 |
| end_date | DATE | NOT NULL | 시뮬레이션 종료일 |
| current_date | DATE | NOT NULL | 현재 턴(거래일) |
| initial_capital | DECIMAL(15,2) | NOT NULL, DEFAULT 100000000 | 초기 자본금 (원) |
| cash_balance | DECIMAL(15,2) | NOT NULL | 현재 현금 잔액 |
| status | ENUM | NOT NULL, DEFAULT 'IN_PROGRESS' | 게임 상태 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL, ON UPDATE NOW | 수정 시각 |

**Status ENUM Values**:
- `IN_PROGRESS`: 진행 중
- `COMPLETED`: 종료 (마지막 날 도달)
- `ABANDONED`: 중단

**Validation Rules**:
- `start_date` < `end_date`
- `start_date` <= `current_date` <= `end_date`
- `initial_capital` > 0
- `cash_balance` >= 0

**State Transitions**:
```
[NEW] → IN_PROGRESS (게임 시작)
IN_PROGRESS → COMPLETED (마지막 날 도달)
IN_PROGRESS → ABANDONED (사용자 중단)
```

---

### SimulatedPosition

게임 내 가상 포지션. 현재 보유 중인 종목.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 고유 식별자 |
| session_id | UUID | FK(GameSession), NOT NULL, INDEX | 소속 게임 세션 |
| stock_code | VARCHAR(20) | NOT NULL | 종목 코드 (예: 005930.KS) |
| stock_name | VARCHAR(100) | NOT NULL | 종목명 |
| quantity | INTEGER | NOT NULL | 보유 수량 |
| avg_entry_price | DECIMAL(15,2) | NOT NULL | 평균 매수가 |
| entry_date | DATE | NOT NULL | 최초 매수일 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | 생성 시각 |
| updated_at | TIMESTAMP | NOT NULL, ON UPDATE NOW | 수정 시각 |

**Unique Constraint**: (session_id, stock_code)

**Validation Rules**:
- `quantity` > 0
- `avg_entry_price` > 0

**Lifecycle**:
- 매수 시 생성 (또는 수량/평균가 업데이트)
- 전량 매도 시 삭제

---

### SimulatedTrade

게임 내 가상 거래 기록. 모든 매수/매도 이력.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 고유 식별자 |
| session_id | UUID | FK(GameSession), NOT NULL, INDEX | 소속 게임 세션 |
| trade_date | DATE | NOT NULL | 거래일 |
| stock_code | VARCHAR(20) | NOT NULL | 종목 코드 |
| stock_name | VARCHAR(100) | NOT NULL | 종목명 |
| action | ENUM | NOT NULL | 거래 유형 (BUY/SELL) |
| quantity | INTEGER | NOT NULL | 거래 수량 |
| price | DECIMAL(15,2) | NOT NULL | 거래 가격 (종가) |
| total_amount | DECIMAL(15,2) | NOT NULL | 총 거래 금액 |
| realized_pnl | DECIMAL(15,2) | NULLABLE | 실현 손익 (SELL 시) |
| realized_pnl_pct | DECIMAL(8,4) | NULLABLE | 실현 손익률 (SELL 시) |
| confidence_score | DECIMAL(5,2) | NULLABLE | 매수 시 신뢰도 점수 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | 생성 시각 |

**Action ENUM Values**:
- `BUY`: 매수
- `SELL`: 매도

**Validation Rules**:
- `quantity` > 0
- `price` > 0
- `total_amount` = `quantity` * `price`
- `realized_pnl` is set only when `action` = SELL

---

## Computed/Derived Fields (Not Stored)

게임 상태 조회 시 실시간 계산되는 필드:

### Portfolio Summary (from GameSession + SimulatedPositions)

| Field | Calculation |
|-------|-------------|
| total_positions_value | SUM(position.quantity * current_price) for all positions |
| total_value | cash_balance + total_positions_value |
| total_return | total_value - initial_capital |
| total_return_pct | (total_return / initial_capital) * 100 |
| unrealized_pnl | SUM(position unrealized PnL) |

### Position Details (from SimulatedPosition + current price)

| Field | Calculation |
|-------|-------------|
| current_price | 해당 날짜 종가 (yfinance) |
| current_value | quantity * current_price |
| unrealized_pnl | current_value - (quantity * avg_entry_price) |
| unrealized_pnl_pct | (unrealized_pnl / (quantity * avg_entry_price)) * 100 |

### Backtest Metrics (from SimulatedTrades)

기존 BacktestResult와 동일한 형식으로 계산:
- `total_trades`: COUNT(trades)
- `winning_trades`: COUNT(trades WHERE realized_pnl > 0)
- `win_rate_pct`: (winning_trades / total_sell_trades) * 100
- `max_drawdown_pct`: 일별 포트폴리오 가치에서 계산
- `profit_factor`: gross_profit / gross_loss

---

## Migration Notes

### New Tables
1. `game_sessions` - GameSession 엔티티
2. `simulated_positions` - SimulatedPosition 엔티티
3. `simulated_trades` - SimulatedTrade 엔티티

### Indexes
- `game_sessions`: (user_id), (user_id, status)
- `simulated_positions`: (session_id), (session_id, stock_code) UNIQUE
- `simulated_trades`: (session_id), (session_id, trade_date)

### Foreign Key Cascades
- GameSession 삭제 시: SimulatedPosition, SimulatedTrade CASCADE DELETE

---

## JSON Export Format (FR-016 Compatibility)

기존 백테스트 시스템과 호환을 위한 JSON 변환 형식:

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "initial_capital": 100000000,
  "final_value": 115000000,
  "total_return_pct": 15.0,
  "max_drawdown_pct": 5.2,
  "total_trades": 24,
  "winning_trades": 16,
  "win_rate_pct": 66.67,
  "trades": [
    {
      "date": "2024-01-15",
      "stock_code": "005930.KS",
      "stock_name": "삼성전자",
      "action": "BUY",
      "price": 72000,
      "quantity": 100,
      "pnl": null,
      "pnl_pct": null
    },
    {
      "date": "2024-02-20",
      "stock_code": "005930.KS",
      "stock_name": "삼성전자",
      "action": "SELL",
      "price": 78000,
      "quantity": 100,
      "pnl": 600000,
      "pnl_pct": 8.33
    }
  ],
  "daily_values": [
    ["2024-01-01", 100000000],
    ["2024-01-02", 100500000],
    ...
  ]
}
```
