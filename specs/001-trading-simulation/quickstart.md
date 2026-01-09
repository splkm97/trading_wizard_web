# Quickstart: Turn-Based Trading Simulation Game

**Date**: 2026-01-08
**Feature**: 001-trading-simulation

## Prerequisites

- Trading Wizard Web 프로젝트 설정 완료
- Backend 서버 실행 중 (`uvicorn src.main:app --reload`)
- Frontend 개발 서버 실행 중 (`npm run dev`)
- 로그인된 상태 (PEM 파일 기반 인증)

---

## 1. 게임 시작하기

### 1.1 시뮬레이션 페이지 접속

```
http://localhost:5173/simulation
```

### 1.2 새 게임 생성

1. "새 게임 시작" 버튼 클릭
2. 게임 설정 입력:
   - **게임 이름** (선택): 예) "2024년 1분기 테스트"
   - **시작일**: 시뮬레이션 시작 날짜 선택
   - **종료일**: 시뮬레이션 종료 날짜 선택
   - **초기 자본금**: 기본값 1억원, 변경 가능
3. "게임 시작" 버튼 클릭

### API 호출 예시

```bash
curl -X POST http://localhost:8000/api/simulation/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2024년 1분기 테스트",
    "start_date": "2024-01-02",
    "end_date": "2024-03-29",
    "initial_capital": 100000000
  }'
```

---

## 2. 게임 플레이

### 2.1 추천 종목 확인

게임 시작 후 메인 화면에서:

1. **추천 종목 리스트** 확인
   - 볼린저 밴드 점수 50점 이상인 종목만 표시
   - 점수 높은 순으로 정렬
   - 이미 보유 중인 종목은 별도 표시 (파란색 배경)

2. **종목 클릭**하여 상세 정보 확인
   - 가격 차트 (최근 60일)
   - 볼린저 밴드 표시
   - RSI, MACD, 거래량 비율 지표
   - 신뢰도 점수 breakdown

### 2.2 매매 결정

**보유하지 않은 종목:**
- `매수(Buy)` 버튼: 매수 금액/수량 입력 후 매수
- `관망(Skip)` 버튼: 이 종목 패스

**보유 중인 종목:**
- `매도(Sell)` 버튼: 전량 매도
- `홀딩(Hold)` 버튼: 계속 보유

### 매수 예시

```bash
curl -X POST http://localhost:8000/api/simulation/sessions/{session_id}/trade \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "005930.KS",
    "action": "BUY",
    "quantity": 100
  }'
```

### 매도 예시

```bash
curl -X POST http://localhost:8000/api/simulation/sessions/{session_id}/trade \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "005930.KS",
    "action": "SELL"
  }'
```

### 2.3 턴 진행

모든 결정을 마친 후:

1. **"Next Day"** 버튼 클릭
2. 다음 거래일로 이동
3. 보유 종목의 평가 금액이 새로운 종가로 업데이트
4. 포트폴리오 요약 확인

```bash
curl -X POST http://localhost:8000/api/simulation/sessions/{session_id}/turn \
  -H "Authorization: Bearer <token>"
```

---

## 3. 포트폴리오 확인

### 3.1 포트폴리오 패널

화면 우측에 항상 표시:

- **보유 현금**: 현재 현금 잔액
- **보유 종목**: 각 종목별 정보
  - 종목명
  - 보유 수량
  - 평균 매수가
  - 현재가
  - 평가 손익 (금액 + %)
- **총 자산**: 현금 + 보유 종목 평가액
- **총 수익률**: (총 자산 - 초기 자본) / 초기 자본 × 100

---

## 4. 리포트 확인

### 4.1 실시간 백테스트 리포트

1. **"현재 리포트 보기"** 버튼 클릭
2. 모달에서 확인 가능한 항목:
   - **Equity Curve**: 일별 포트폴리오 가치 그래프
   - **MDD**: 최대 낙폭
   - **승률**: 수익 거래 / 전체 매도 거래
   - **손익비**: 평균 수익 / 평균 손실
   - **종목별 기여도**: 종목별 실현 손익

```bash
curl http://localhost:8000/api/simulation/sessions/{session_id}/report \
  -H "Authorization: Bearer <token>"
```

### 4.2 거래 내역 내보내기

1. 리포트 모달 또는 설정에서 **"거래 내역 내보내기"** 클릭
2. JSON 파일 다운로드
3. 기존 백테스트 시스템에서 분석 가능

```bash
curl http://localhost:8000/api/simulation/sessions/{session_id}/export \
  -H "Authorization: Bearer <token>" \
  -o trades.json
```

---

## 5. 게임 종료

### 5.1 자동 종료

- 마지막 거래일(종료일)에 도달하면 자동 종료
- 게임 종료 화면에서 최종 성과 요약 표시

### 5.2 수동 중단

- 게임 목록에서 게임 삭제 가능
- 삭제된 게임의 데이터는 복구 불가

---

## 6. 게임 재개

### 6.1 진행 중인 게임 목록

```
http://localhost:5173/simulation
```

- 진행 중인 게임 목록 표시
- 게임 클릭하여 이어서 플레이

### 6.2 게임 상태 복원

- 마지막 저장된 상태에서 자동 재개
- 현재 턴, 포트폴리오, 거래 이력 모두 보존

---

## Troubleshooting

### 추천 종목이 없습니다

- 해당 날짜에 볼린저 밴드 점수 50점 이상 종목이 없음
- 정상적인 상황 - "Next Day"로 다음 날로 이동

### 현금이 부족합니다

- 매수 금액이 보유 현금을 초과
- 더 적은 수량으로 매수하거나, 일부 종목 매도 후 재시도

### 데이터 로딩 실패

- yfinance 연결 문제일 수 있음
- 인터넷 연결 확인 후 페이지 새로고침
- 2020년 이전 데이터는 지원되지 않을 수 있음

### 턴 진행이 안 됩니다

- 게임이 이미 종료 상태일 수 있음
- 게임 상태가 `COMPLETED`인지 확인

---

## 성공 기준 검증

| 기준 | 검증 방법 |
|------|----------|
| SC-001: 첫 거래 3분 이내 | 게임 시작 → 종목 선택 → 매수 완료 시간 측정 |
| SC-002: 리스트 로딩 2초 | 브라우저 개발자 도구 Network 탭 확인 |
| SC-003: 차트 표시 1초 | 종목 클릭 후 차트 렌더링 시간 |
| SC-004: 턴 진행 3초 | Next Day 클릭 후 결과 표시 시간 |
| SC-005: 리포트 로딩 2초 | 리포트 버튼 클릭 후 모달 표시 시간 |
| SC-006: 올바른 버튼 표시 | 보유/미보유 종목에 따른 버튼 확인 |
| SC-007: 상태 복구 | 새로고침 후 게임 상태 유지 확인 |
| SC-008: JSON 호환성 | 내보낸 JSON을 기존 백테스트 UI에서 로드 |
