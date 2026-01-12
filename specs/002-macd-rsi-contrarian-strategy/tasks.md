# Tasks: MACD & RSI Contrarian Signal Recommendation System

**Input**: Design documents from `/specs/002-macd-rsi-contrarian-strategy/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

**Tests**: Tests are included as required by Constitution Principle III (Test Coverage Required)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and shared infrastructure for contrarian strategy

- [x] T001 Add contrarian settings fields to backend/src/models/user_settings.py (macd_rsi_rsi_period, macd_rsi_rsi_threshold, macd_rsi_macd_fast_period, macd_rsi_macd_slow_period, macd_rsi_macd_signal_period, macd_rsi_confidence_threshold)
- [x] T002 Create database migration for new user_settings columns in backend/ (SQLite with defaults)
- [x] T003 [P] Add ContrarianSignal and ContrarianIndicators TypeScript types to frontend/src/types/index.ts
- [x] T004 [P] Add AppliedContrarianSettings TypeScript type to frontend/src/types/index.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement calculate_contrarian_confidence() function in backend/src/wizard/signal_scanner.py per research.md formula (RSI tiers 80/60/40 + MACD bonus 0-20)
- [x] T006 Implement detect_macd_golden_cross() function in backend/src/wizard/signal_scanner.py (previous day MACD < Signal, current day MACD >= Signal)
- [x] T007 Implement scan_for_contrarian_signals() method in SignalScanner class in backend/src/wizard/signal_scanner.py (uses RSI threshold, golden cross detection, confidence scoring)
- [x] T008 [P] Add Pydantic schemas for ContrarianSignal, ContrarianIndicators, AppliedContrarianSettings, ContrarianSignalsResponse to backend/src/api/contrarian.py
- [x] T009 [P] Add contrarian API client functions (getContrarianSignals, getContrarianSignalForStock) to frontend/src/services/api.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View MACD/RSI Contrarian Recommendations (Priority: P1) 🎯 MVP

**Goal**: Display contrarian buy signals with RSI/MACD indicators on a dedicated page

**Independent Test**: Navigate to /contrarian page and verify signals display with RSI ≤ 30 AND MACD golden cross, showing stock name, price, RSI, MACD values, and confidence score

### Tests for User Story 1

- [x] T010 [P] [US1] Create unit test for calculate_contrarian_confidence() in backend/tests/unit/test_contrarian_signals.py (test RSI tiers: ≤20→80, 20-25→60, 25-30→40, plus MACD bonus)
- [x] T011 [P] [US1] Create unit test for detect_macd_golden_cross() in backend/tests/unit/test_contrarian_signals.py (test crossing scenarios, edge cases)
- [x] T012 [P] [US1] Create unit test for scan_for_contrarian_signals() in backend/tests/unit/test_contrarian_signals.py (test combined RSI+MACD logic, insufficient data exclusion)
- [x] T013 [P] [US1] Create integration test for GET /contrarian/signals endpoint in backend/tests/integration/test_contrarian_api.py

### Implementation for User Story 1

- [x] T014 [US1] Create GET /contrarian/signals endpoint in backend/src/api/contrarian.py (uses SignalScanner.scan_for_contrarian_signals, returns signals with applied_settings)
- [x] T015 [US1] Register contrarian router in backend/src/main.py
- [x] T016 [P] [US1] Create ContrarianSignalCard component in frontend/src/components/contrarian/ContrarianSignalCard.tsx (display stock name, price, RSI, MACD line/signal/histogram, confidence score)
- [x] T017 [P] [US1] Create ContrarianPanel component in frontend/src/components/contrarian/ContrarianPanel.tsx (fetch signals, loading/error/empty states, signal list)
- [x] T018 [US1] Create ContrarianPage in frontend/src/pages/ContrarianPage.tsx (strategy description, ContrarianPanel, applied settings display)
- [x] T019 [US1] Add /contrarian route to frontend/src/App.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional - users can view contrarian signals on dedicated page

---

## Phase 4: User Story 2 - Understand Signal Reasoning (Priority: P2)

**Goal**: Provide detailed explanation of why a stock was recommended with expandable details

**Independent Test**: Expand any signal card and verify detailed explanation shows RSI oversold condition and MACD golden cross timing with visual indicators

### Tests for User Story 2

- [ ] T020 [P] [US2] Create unit test for signal reason formatting in backend/tests/unit/test_contrarian_signals.py (verify reason text includes RSI oversold explanation and MACD cross description)

### Implementation for User Story 2

- [ ] T021 [US2] Add format_contrarian_reason_detail() function to backend/src/wizard/signal_scanner.py (generate detailed Korean explanation of RSI oversold + MACD golden cross)
- [ ] T022 [US2] Update ContrarianSignalCard in frontend/src/components/contrarian/ContrarianSignalCard.tsx to add expandable details section with RSI visual indicator (oversold zone highlight) and MACD cross direction indicator
- [ ] T023 [US2] Add CSS styling for expanded details, RSI zone visualization, and MACD indicators in frontend/src/components/contrarian/ContrarianSignalCard.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can view signals AND understand the reasoning

---

## Phase 5: User Story 3 - Configure Strategy Parameters (Priority: P3)

**Goal**: Allow users to customize RSI threshold, MACD periods, and confidence threshold

**Independent Test**: Modify RSI threshold in settings, trigger new scan, verify signals use updated parameters shown in applied_settings

### Tests for User Story 3

- [ ] T024 [P] [US3] Create integration test for contrarian settings update via PUT /settings in backend/tests/integration/test_contrarian_api.py (verify settings persist and apply to scans)

### Implementation for User Story 3

- [ ] T025 [US3] Update settings Pydantic schemas in backend/src/api/settings.py to include macd_rsi_* fields with validation (fast < slow period constraint)
- [ ] T026 [US3] Update settings_service to include macd_rsi_* fields when loading/saving in backend/src/services/settings_service.py
- [ ] T027 [US3] Add MACD/RSI settings section to frontend settings page component (RSI period/threshold, MACD fast/slow/signal periods, confidence threshold)
- [ ] T028 [US3] Update ContrarianPanel to display applied_settings snapshot showing parameters used for current scan in frontend/src/components/contrarian/ContrarianPanel.tsx

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Navigate Between Strategies (Priority: P3)

**Goal**: Enable easy navigation between Bollinger Band and MACD/RSI strategy pages

**Independent Test**: Click strategy navigation links and verify seamless transition between pages with respective signals loading

### Tests for User Story 4

- [ ] T029 [P] [US4] Create E2E test for strategy navigation in frontend/tests/e2e/contrarian.spec.ts (navigate to /contrarian, verify page loads, click to TradePage, click back)

### Implementation for User Story 4

- [ ] T030 [US4] Add "MACD/RSI Strategy" link to main navigation menu in frontend/src/App.tsx or navigation component
- [ ] T031 [US4] Add strategy switcher component to ContrarianPage in frontend/src/pages/ContrarianPage.tsx (link to TradePage)
- [ ] T032 [US4] Add strategy switcher to TradePage in frontend/src/pages/TradePage.tsx (link to ContrarianPage)

**Checkpoint**: All user stories should now be independently functional with full navigation

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Add GET /contrarian/signal/{stock_code} single stock endpoint to backend/src/api/contrarian.py
- [ ] T034 [P] Create edge case unit tests in backend/tests/unit/test_contrarian_signals.py (RSI exactly 30, MACD crossed 2 days ago, insufficient data)
- [ ] T035 [P] Add empty state message to ContrarianPanel explaining contrarian criteria when no signals found in frontend/src/components/contrarian/ContrarianPanel.tsx
- [ ] T036 Run backend tests and fix any failures: cd backend && pytest tests/
- [ ] T037 Run frontend build and fix any TypeScript errors: cd frontend && npm run build
- [ ] T038 Validate implementation against quickstart.md scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories - **MVP**
- **User Story 2 (P2)**: Can start after Foundational - Builds on US1 components but independently testable
- **User Story 3 (P3)**: Can start after Foundational - Extends settings, integrates with US1 scan
- **User Story 4 (P3)**: Can start after Foundational - Only requires US1 page to exist for navigation

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend before frontend (API before UI)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 and T004 can run in parallel (different frontend files)

**Phase 2 (Foundational)**:
- T008 and T009 can run in parallel (backend schemas vs frontend API client)

**Phase 3 (US1)**:
- T010, T011, T012, T013 can run in parallel (independent test files)
- T016, T017 can run in parallel (different frontend components)

**Phase 4-6 (US2, US3, US4)**:
- Test tasks marked [P] can run in parallel within each story
- Different stories can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create unit test for calculate_contrarian_confidence() in backend/tests/unit/test_contrarian_signals.py"
Task: "Create unit test for detect_macd_golden_cross() in backend/tests/unit/test_contrarian_signals.py"
Task: "Create unit test for scan_for_contrarian_signals() in backend/tests/unit/test_contrarian_signals.py"
Task: "Create integration test for GET /contrarian/signals endpoint in backend/tests/integration/test_contrarian_api.py"

# Launch frontend components in parallel (after backend API ready):
Task: "Create ContrarianSignalCard component in frontend/src/components/contrarian/ContrarianSignalCard.tsx"
Task: "Create ContrarianPanel component in frontend/src/components/contrarian/ContrarianPanel.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 (T010-T019)
4. **STOP and VALIDATE**: Test contrarian page independently
5. Deploy/demo if ready - users can view MACD/RSI signals

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Signal reasoning available
4. Add User Story 3 → Test independently → Custom parameters
5. Add User Story 4 → Test independently → Full navigation
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1) - MVP priority
   - Developer B: User Story 3 (P3) - Settings preparation
3. After US1 complete:
   - Developer A: User Story 2 (P2) - Enhance US1 cards
   - Developer B: User Story 4 (P3) - Navigation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing code reuse: `calculate_rsi()`, `calculate_macd()`, SignalScanner caching
