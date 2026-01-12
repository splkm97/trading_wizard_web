# Feature Specification: MACD & RSI Contrarian Signal Recommendation System

**Feature Branch**: `002-macd-rsi-contrarian-strategy`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User description: "MACD & RSI 기반 역추세(Contrasting Signal) 추천 시스템 구현 - 기존 볼린저 밴드 전략 외에 새로운 주식 추천 전략 추가, 전용 페이지 생성"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View MACD/RSI Contrarian Recommendations (Priority: P1)

As a trader, I want to see stock recommendations based on the MACD/RSI contrarian strategy so that I can identify oversold stocks with emerging upward momentum.

**Why this priority**: This is the core value proposition of the feature. Without displaying recommendations, the strategy has no user-facing functionality.

**Independent Test**: Can be fully tested by navigating to the dedicated MACD/RSI strategy page and verifying that recommendations appear with RSI and MACD indicator values displayed.

**Acceptance Scenarios**:

1. **Given** I am on the MACD/RSI strategy page, **When** the system scans stocks, **Then** I see a list of stocks where RSI(14) ≤ 30 AND MACD line just crossed above Signal line
2. **Given** signals are displayed, **When** I view a signal card, **Then** I see the stock name, current price, RSI value, MACD values (MACD line, Signal line, Histogram), and confidence score (no position sizing included)
3. **Given** no stocks meet the contrarian criteria, **When** the scan completes, **Then** I see a message indicating no opportunities found with an explanation of the criteria

---

### User Story 2 - Understand Signal Reasoning (Priority: P2)

As a trader, I want to understand why a stock was recommended so that I can make informed trading decisions based on the technical analysis.

**Why this priority**: Signal transparency is essential for user trust and informed decision-making, but the feature can function without detailed explanations.

**Independent Test**: Can be tested by expanding any recommendation card and verifying the detailed explanation of RSI oversold condition and MACD golden cross timing.

**Acceptance Scenarios**:

1. **Given** a recommendation is displayed, **When** I expand the details, **Then** I see a clear explanation that the stock is in oversold territory (RSI ≤ 30) while showing bullish momentum reversal (MACD golden cross)
2. **Given** I view the expanded details, **When** I look at the indicators section, **Then** I see RSI with visual indicator of oversold zone, MACD/Signal/Histogram values with cross direction indicator

---

### User Story 3 - Configure Strategy Parameters (Priority: P3)

As a trader, I want to adjust the MACD/RSI strategy parameters so that I can customize the sensitivity of the contrarian signal detection to my trading style.

**Why this priority**: Default parameters (RSI 30, MACD 12/26/9) are industry standard and work for most users. Customization adds value but is not essential for initial use.

**Independent Test**: Can be tested by modifying RSI threshold or MACD periods in settings and verifying that subsequent scans use the updated parameters.

**Acceptance Scenarios**:

1. **Given** I am on the settings page, **When** I navigate to MACD/RSI strategy settings, **Then** I can configure RSI threshold (default 30), RSI period (default 14), MACD fast period (default 12), MACD slow period (default 26), and MACD signal period (default 9)
2. **Given** I have modified strategy parameters, **When** I view recommendations, **Then** the applied settings are displayed showing the parameters used for that scan
3. **Given** I have configured a higher RSI threshold (e.g., 35), **When** the system scans, **Then** stocks with RSI between 30-35 are now included in results

---

### User Story 4 - Navigate Between Strategies (Priority: P3)

As a trader, I want to easily switch between the Bollinger Band strategy and the MACD/RSI contrarian strategy so that I can use the most appropriate approach for current market conditions.

**Why this priority**: Navigation convenience improves user experience but doesn't affect core functionality. Users can access pages directly via URL.

**Independent Test**: Can be tested by clicking strategy navigation links and verifying seamless transition between strategy pages with respective recommendations loading.

**Acceptance Scenarios**:

1. **Given** I am on the main trading page (Bollinger Band strategy), **When** I click on the MACD/RSI strategy link, **Then** I am navigated to the dedicated MACD/RSI strategy page
2. **Given** I am on the MACD/RSI strategy page, **When** I click on the Bollinger Band strategy link, **Then** I return to the main trading page
3. **Given** I am on any page with navigation, **When** I view the navigation menu, **Then** I see both strategy options clearly labeled

---

### Edge Cases

- What happens when RSI equals exactly 30? - Stock should be included (threshold is ≤ 30, inclusive)
- What happens when MACD crossed Signal line multiple days ago? - Only detect the crossing day (previous day MACD < Signal, current day MACD ≥ Signal)
- How does system handle stocks with insufficient price history for indicator calculation? - Exclude from scan with no error; require minimum 35 trading days (26-day slow EMA + 9-day signal smoothing)
- What happens when a stock has RSI ≤ 30 but MACD golden cross occurred 2 days ago? - Not included; golden cross must be on the most recent trading day
- How does system handle weekends/holidays when detecting "today's" golden cross? - Use the most recent trading day's data, not calendar day

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate RSI with configurable period (default 14) based on closing prices
- **FR-002**: System MUST calculate MACD with configurable fast (default 12), slow (default 26), and signal (default 9) periods
- **FR-003**: System MUST detect MACD golden cross defined as: previous day MACD line < Signal line AND current day MACD line ≥ Signal line
- **FR-004**: System MUST identify contrarian buy signals where RSI ≤ threshold (default 30) AND MACD golden cross occurred on the most recent trading day
- **FR-005**: System MUST display signals (not position-sized recommendations) with stock name, code, current price, RSI value, MACD line value, Signal line value, Histogram value, and confidence score; user manually determines position size
- **FR-006**: System MUST provide a dedicated page for MACD/RSI contrarian strategy separate from the Bollinger Band strategy page
- **FR-007**: System MUST allow users to configure RSI threshold and MACD periods through the settings interface
- **FR-008**: System MUST display applied settings snapshot with each recommendation scan result
- **FR-009**: System MUST scan the same stock universe as the existing Bollinger Band strategy (KOSPI Top 100 with fallback)
- **FR-010**: System MUST calculate a confidence score using threshold-based tiers: RSI ≤ 20 = High (base 80), RSI 20-25 = Medium (base 60), RSI 25-30 = Low (base 40); adjusted upward by MACD histogram strength (up to +20 points for strong positive histogram)

### Key Entities

- **ContrarianSignal**: Represents a detected MACD/RSI contrarian opportunity; contains stock identification, indicator values (RSI, MACD, Signal, Histogram), signal timestamp, and confidence score
- **StrategySettings**: Configuration for MACD/RSI strategy parameters; includes RSI period, RSI threshold, MACD fast/slow/signal periods; relates to user preferences
- **StockIndicators**: Collection of calculated technical indicators for a stock at a point in time; includes RSI, MACD components, price data

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view MACD/RSI contrarian recommendations within 5 seconds of page load for the standard stock universe (100 stocks)
- **SC-002**: 100% of displayed recommendations correctly satisfy the contrarian criteria (RSI ≤ threshold AND MACD golden cross on most recent day)
- **SC-003**: Users can distinguish between the two strategies and navigate between them without confusion (measured by successful navigation within 2 clicks)
- **SC-004**: Strategy parameters can be modified and take effect on the next scan without requiring page refresh or application restart
- **SC-005**: Each recommendation displays all required indicator values (RSI, MACD, Signal, Histogram) with clear visual formatting
- **SC-006**: System handles edge cases (insufficient data, no signals found) gracefully with informative user messages

## Clarifications

### Session 2026-01-10

- Q: How should the confidence score be calculated for contrarian signals? → A: Threshold-based tiers: RSI ≤ 20 = High (base 80), RSI 20-25 = Medium (base 60), RSI 25-30 = Low (base 40); then adjust upward by MACD histogram positivity (stronger positive histogram adds up to +20 points)
- Q: Should the MACD/RSI strategy generate buy recommendations with position sizing or only display signals? → A: Signals only - display detected signals without position sizing; user manually decides quantity

## Assumptions

- The existing multi-tier data caching system (memory → PostgreSQL → yfinance) will be reused for price data retrieval
- RSI and MACD calculation functions already exist in the codebase (`calculate_rsi()`, `calculate_macd()`) and will be reused
- The new strategy will follow the same UI patterns as the existing Bollinger Band strategy for consistency
- Default parameters (RSI 30, MACD 12/26/9) are appropriate for Korean stock market (KOSPI) trading
- Users are familiar with RSI and MACD concepts and do not require educational tooltips (though clear labeling is required)
