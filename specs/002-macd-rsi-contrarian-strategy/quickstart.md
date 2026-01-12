# Quickstart: MACD & RSI Contrarian Signal Strategy

**Feature**: 002-macd-rsi-contrarian-strategy
**Date**: 2026-01-10

## Prerequisites

- Docker and Docker Compose installed
- Node.js LTS (for frontend development)
- Python 3.9+ (for backend development)

## Getting Started

### 1. Start Development Environment

```bash
# Clone and checkout feature branch
git checkout 002-macd-rsi-contrarian-strategy

# Start backend services
docker-compose up -d backend db

# Start frontend dev server
cd frontend
npm install
npm run dev
```

### 2. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Navigate to Contrarian Strategy

1. Log in to the application
2. Click "MACD/RSI Strategy" in the navigation menu (or visit `/contrarian`)
3. View contrarian signals based on RSI oversold + MACD golden cross

## Development Workflow

### Backend Changes

```bash
cd backend

# Run tests
pytest tests/unit/test_contrarian_signals.py -v
pytest tests/integration/test_contrarian_api.py -v

# Run linting
ruff check src/

# Start in development mode
uvicorn src.main:app --reload
```

### Frontend Changes

```bash
cd frontend

# Run development server with hot reload
npm run dev

# Run E2E tests
npx playwright test tests/e2e/contrarian.spec.ts

# Run linting
npm run lint
```

## Key Files

### Backend

| File | Purpose |
|------|---------|
| `src/wizard/signal_scanner.py` | Add `scan_for_contrarian_signals()` method |
| `src/api/contrarian.py` | New API router for contrarian endpoints |
| `src/models/user_settings.py` | Add MACD/RSI settings fields |
| `tests/unit/test_contrarian_signals.py` | Unit tests for signal logic |

### Frontend

| File | Purpose |
|------|---------|
| `src/pages/ContrarianPage.tsx` | Main strategy page |
| `src/components/contrarian/ContrarianPanel.tsx` | Signal list panel |
| `src/components/contrarian/ContrarianSignalCard.tsx` | Individual signal card |
| `src/types/index.ts` | Add ContrarianSignal types |

## API Endpoints

### Get Contrarian Signals

```bash
curl -X GET "http://localhost:8000/api/contrarian/signals?max_results=10" \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "signals": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "signal_type": "BUY",
      "confidence_score": 85.5,
      "current_price": 72500.0,
      "indicators": {
        "rsi": 18.5,
        "macd": -450.25,
        "macd_signal": -520.80,
        "macd_histogram": 70.55
      }
    }
  ],
  "scanned_count": 100,
  "signal_count": 1,
  "applied_settings": {
    "rsi_period": 14,
    "rsi_threshold": 30.0,
    "macd_fast_period": 12,
    "macd_slow_period": 26,
    "macd_signal_period": 9,
    "confidence_threshold": 40.0
  }
}
```

### Get Single Stock Signal

```bash
curl -X GET "http://localhost:8000/api/contrarian/signal/005930" \
  -H "Authorization: Bearer <token>"
```

## Testing Strategy

### Unit Tests (Signal Logic)

```python
# tests/unit/test_contrarian_signals.py

def test_macd_golden_cross_detection():
    """Test MACD golden cross is correctly detected."""
    # Previous day: MACD < Signal
    # Current day: MACD >= Signal
    ...

def test_contrarian_confidence_scoring():
    """Test tiered confidence scoring."""
    # RSI <= 20 -> base 80
    # RSI 20-25 -> base 60
    # RSI 25-30 -> base 40
    ...
```

### Integration Tests (API)

```python
# tests/integration/test_contrarian_api.py

def test_get_contrarian_signals_success(client, mock_stock_data):
    """Test successful signal retrieval."""
    response = client.get("/api/contrarian/signals")
    assert response.status_code == 200
    assert "applied_settings" in response.json()
```

### E2E Tests (Frontend)

```typescript
// tests/e2e/contrarian.spec.ts

test('displays contrarian signals', async ({ page }) => {
  await page.goto('/contrarian');
  await expect(page.getByText('MACD/RSI Strategy')).toBeVisible();
  await expect(page.locator('.signal-card')).toHaveCount.greaterThan(0);
});
```

## Common Issues

### No Signals Displayed

1. Check that KOSPI stocks have sufficient price history (35+ days)
2. Verify RSI is actually ≤ 30 for some stocks (rare in bull markets)
3. Check MACD golden cross timing (must be on most recent day)

### Settings Not Applied

1. Ensure settings are saved before scanning
2. Check `applied_settings` in API response matches expectations
3. Verify database migration ran successfully

### Performance Issues

1. First scan may be slow (populating cache from yfinance)
2. Subsequent scans should use PostgreSQL cache
3. Check database has historical_prices data for KOSPI stocks

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Implement backend signal detection first (P1)
3. Add frontend page and components
4. Write tests alongside implementation
