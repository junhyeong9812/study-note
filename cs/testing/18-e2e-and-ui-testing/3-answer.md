# testing/18-e2e-and-ui-testing — 정답

## 정답

### 1. 필요한 이유와 적게 두는 이유

- 필요한 이유: 아래층 테스트는 부품과 경계를 따로 본다. 화면 → API → 서비스 → DB를 실제로 잇는 조립·설정 실수는 전체를 통과시켜야 보인다.
- 적게 두는 이유
  - 느리다 — 피드백이 늦다(Wacker 2015).
  - 불안정하다 — 코드 결함과 무관한 실패(환경·하드웨어·타이밍).
  - 원인 위치를 잘 알려 주지 않는다 — 실패 하나에 여러 층이 의심된다.
  - Fowler(2012): UI를 통한 테스트는 "brittle, expensive to write, and time consuming to run".

### 2. 범위 그림

```text
 [브라우저] → [프론트엔드] → [API] → [서비스] → [DB·외부]
 ├ 컴포넌트/UI(jsdom, 백엔드 가짜) ┤
 ├ 브라우저 UI(실제 브라우저) ──────────┤ (백엔드는 가짜 또는 진짜)
 ├ 전 구간 E2E ────────────────────────────────────────────┤
```

- UI/API 경계 분리: 프론트엔드와 API 사이를 자른다. 화면 쪽은 백엔드를 가짜로 두고 UI 동작만, 백엔드 쪽은 공개 API로 업무 흐름을 검증한다. 둘 사이는 계약 테스트로 잇는다.

### 3. 마크업 개편

(실험, Node 22.23.2 · jsdom 26.1.0 · @testing-library/dom 10.4.2, 2026-10-03)

```text
v2 brittle pass=0 fail=4 failed=[B1 B2 B3 B4 ]
v2 role pass=4 fail=0 failed=[]
```

- 구조 선택자 4/4 실패 — 전부 거짓 경보. 역할·레이블 0/4 실패.

### 4. 레이블 연결 끊김

```text
v3 brittle pass=4 fail=0 failed=[]
v3 role pass=3 fail=1 failed=[R2 ]
```

- 구조 선택자는 input을 경로로 찾으므로 모두 통과 — 회귀를 놓친다.
- 역할·레이블 테스트는 `getByLabelText('이메일')`에서 실패: `Found a label with the text of: 이메일, however no form control was found associated to that label. Make sure you're using the "for" attribute or "aria-labelledby" attribute correctly.`
- 메시지가 원인(레이블과 입력칸 연결)과 고칠 곳(`for`·`aria-labelledby`)을 알려 준다. 이 결함은 화면 낭독기 사용자도 겪는다.

### 5. 쿼리 우선순위

- `getByRole` → `getByLabelText` → `getByPlaceholderText` → `getByText` → `getByDisplayValue` → `getByAltText` → `getByTitle` → `getByTestId`.
- `getByTestId`가 마지막인 이유: 사용자는 test id를 보지 못한다. 원칙("테스트는 사용자가 상호작용하는 방식을 닮아야 한다")에서 가장 멀다. 역할·텍스트로 찾을 수 없을 때만 쓴다.
- `getBy`: 없거나 여럿이면 예외(동기). `queryBy`: 없으면 `null`(여럿이면 예외). `findBy`: Promise, 기본 1000ms까지 재시도.

### 6. 기다림

- 조건 기반 대기: `findBy*`, Playwright의 자동 대기와 재시도 단언(`await expect(locator).toBeVisible()`).
- Playwright actionability: 보임(Visible) · 안정(Stable, 애니메이션 끝) · 이벤트를 받음(Receives Events, 다른 요소에 가려지지 않음) · 활성(Enabled). 시간 안에 통과 못 하면 `TimeoutError`.

### 7. jsdom의 한계

- jsdom README: 레이아웃(CSS에 따른 배치 계산)과 내비게이션은 범위 밖이다. 레이아웃 관련 속성은 0 같은 가짜 값을 돌려준다.
- 그래서 요소 겹침·가려짐, CSS로 숨겨진 버튼, 화면 크기별 배치, 페이지 이동이 걸린 흐름은 jsdom 테스트로 못 잡는다. 실제 브라우저 테스트가 필요하다.

### 8. 200개 대량 실패

1. 메시지 분류: `null`(못 찾음)이 대부분이면 선택자 문제일 가능성이 크다.
2. 그 PR의 diff가 클래스·구조만 바꿨는지 확인한다 — 동작이 같다면 테스트가 구현 세부에 묶인 것(거짓 경보).
3. 선택자를 역할·레이블로 바꾼다. 역할·레이블로 못 찾는 요소는 접근성 결함으로 고친다.
4. 재발 방지: 리뷰·린트 규칙으로 CSS 경로·`nth-child` 선택자를 막고, 꼭 필요하면 `data-testid`.

### 9. 출렁이는 통과율

- 구조적 원인: 업무 규칙·세부 동작까지 E2E로 검증하는 아이스크림 콘. 공유 환경(다른 팀 배포·하드웨어)에 기대고, 실패 하나가 많은 테스트를 함께 떨어뜨린다(Wacker 사례: 거의 모든 테스트가 로그인하므로 로그인이 깨지자 거의 다 실패). Wacker(2015) 가상 사례의 숫자가 이 모양이다.
- 대처: E2E는 핵심 여정만, 규칙은 단위·API 테스트로 내린다. 외부 의존은 계약 + 가짜로, 테스트 데이터는 실행마다 고유하게. 남은 불안정 테스트는 격리하고 원인을 고친다(09-flaky-tests).
