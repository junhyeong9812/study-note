# testing/18-e2e-and-ui-testing — E2E·UI 테스트의 범위와 비용 — 정리 (힌트)

## 해결하는 문제

단위·통합·계약 테스트를 다 통과해도 "사용자가 화면에서 로그인 → 주문 → 결제를 끝까지 할 수 있나"는 아무도 확인하지 않았을 수 있다.

- *E2E(end-to-end) 테스트*: 사용자 진입점(브라우저·앱·공개 API)부터 실제 백엔드·DB까지 시스템 전체를 통과시키는 테스트.
- *UI 테스트*: 화면(DOM·위젯)을 사용자처럼 조작하고 화면에 보이는 결과를 확인하는 테스트. 실제 브라우저에서 돌 수도, jsdom 같은 가짜 DOM에서 돌 수도 있다.

대가가 크다.

```text
           ▲ 비용·느림·불안정                    Fowler "TestPyramid"(2012):
          ╱ ╲   E2E·UI                          UI를 통한 테스트는 "깨지기 쉽고, 쓰는 데 비싸고,
         ╱───╲                                   돌리는 데 오래 걸린다"
        ╱ 통합 ╲                                 Google Testing Blog(2015, Wacker):
       ╱───────╲                                 70% 단위 / 20% 통합 / 10% E2E 를 출발점으로 제안
      ╱  단위    ╲
     ╱───────────╲  ▼ 많고 빠름

     아이스크림 콘(거꾸로): E2E·수동이 대부분 → 느리고 불안정한 CI → 결국 무시된다
```

쉬운 예: 자동차 공장의 출고 전 시운전이다.

- 시운전은 차 전체가 굴러가는지 본다. 부품 검사로는 못 보는 조립 실수를 잡는다.
- 하지만 시운전에서 "덜컹거린다"만 알면 어느 부품인지 찾느라 오래 걸린다. 시운전만으로 품질을 지키려 하면 공장이 멈춘다.

똑같은 구조다.\
E2E는 조립 실수(설정·연결·화면 흐름)를 잡는 마지막 그물이다. 원인 위치는 잘 알려 주지 않으므로 수는 적게, 대상은 핵심 사용자 여정으로 고른다.

실무 예:

- 디자인 개편(클래스 이름·감싸는 div 변경)만 했는데 UI 테스트 수백 개가 빨강 → 커리큘럼 ⚠ 칸 "선택자 취약 → UI 변경마다 대량 실패".
- Wacker(2015)의 가상 사례: E2E 통과율 90% 이상을 기능 완료 조건으로 걸었는데, 마감 하루 전 로그인 하나가 깨져 통과율 5%. 파트너 팀의 나쁜 빌드, 랩 하드웨어 고장, 큰 버그 뒤에 숨은 작은 버그로 마감 7일 뒤에야 89.54%("반올림하면 90%")가 됐고, 팀은 마일스톤을 한 주 늦게 끝냈다.

## 동작·원리

### 1. 범위 — 무엇을 진짜로 두나

```text
  [브라우저] ─▶ [프론트엔드 앱] ─▶ [API 게이트웨이] ─▶ [서비스들] ─▶ [DB·브로커·외부 결제]
  ├────────── 컴포넌트/UI 테스트(jsdom, 백엔드는 가짜) ──────────┤
  ├────────── 브라우저 UI 테스트(실제 브라우저, 백엔드 가짜 또는 진짜) ─────────────────┤
  ├────────── 전 구간 E2E(전부 진짜, 외부 결제만 샌드박스) ─────────────────────────────┤
```

- SWE@G 14장의 처방: UI는 모양이 자주 바뀌어 테스트가 깨지기 쉽고, 비동기 동작이 많아 테스트하기 어렵다. 백엔드에 공개 API가 있으면 **UI/API 경계에서 테스트를 나누고**, 공개 API로 E2E를 몰아가는 편이 쉬운 경우가 많다고 적는다.
  - 화면 쪽은 백엔드를 가짜로 두고 UI 동작만, 백엔드 쪽은 API로 업무 흐름만 검증한다. 둘 사이는 계약 테스트([13-contract-testing](../13-contract-testing/2-summary.md))로 잇는다.
- 전 구간 E2E는 소수의 **핵심 사용자 여정**(가입·로그인·결제)에만 둔다.

### 2. 선택자 — 테스트가 화면을 "어떻게 찾나"

```text
  같은 버튼을 찾는 세 가지 방법

  구조·CSS 경로   div.container > form > button.btn-primary       ← 마크업 구조에 묶임
  test id         [data-testid="login-submit"]                    ← 테스트 전용 속성에 묶임
  역할·이름        getByRole('button', { name: '로그인' })           ← 사용자가 보는 것에 묶임
```

- *선택자(selector)·로케이터(locator)*: 테스트가 화면 요소를 찾는 방법.
- *접근성 트리*: 브라우저가 화면 낭독기 등에 넘기는 요소 트리. 요소마다 역할(button·textbox·alert)과 접근 가능한 이름(레이블 텍스트)이 있다.
- Testing Library 문서의 원칙: "테스트는 사용자가 코드와 상호작용하는 방식을 최대한 닮아야 한다." 쿼리 우선순위는 `getByRole` → `getByLabelText` → `getByPlaceholderText` → `getByText` → `getByDisplayValue` → `getByAltText`·`getByTitle` → `getByTestId`(최후).
- Playwright 문서: "DOM은 자주 바뀌어 탄력 없는 테스트로 이어지므로 CSS와 XPath는 권장하지 않는다." 권장 로케이터는 `getByRole`·`getByText`·`getByLabel`·…·`getByTestId`.

### 3. 실험: 마크업 개편·접근성 회귀·동작 버그에 두 스타일이 어떻게 반응하나

로그인 폼 하나를 네 판으로 만들고, 같은 동작 4개를 두 스타일로 테스트했다.

| 판 | 바뀐 것 | 사용자에게 |
|---|---|---|
| v1 | 기준 | 정상 |
| v2 | 디자인 개편 — 클래스 이름 변경, 감싸는 div 추가 | **동작 같음** |
| v3 | 이메일 `<label for>`가 input id와 안 맞음 | 접근성 회귀(레이블을 눌러도 입력칸이 안 잡히고, 화면 낭독기가 칸 이름을 못 읽는다) |
| v4 | 빈 이메일 오류 메시지를 안 띄움 | **동작 버그** |

구조 선택자 스타일(발췌):

```js
const submit = () => $('div.container > form > button.btn-primary').click();
test('B2 정상 입력 → 환영', () => {
  $('form.login-form > div.field:nth-child(1) > input').value = 'kim@example.com';
  submit();
  assert.match($('form.login-form > p.message').textContent, /환영합니다/);
});
```

역할·레이블 스타일(발췌, `@testing-library/dom` — 실험 코드는 `screen = within(doc.body)`로 jsdom 문서에 묶었다):

```js
const submit = () => screen.getByRole('button', { name: '로그인' }).click();
test('R2 정상 입력 → 환영', () => {
  screen.getByLabelText('이메일').value = 'kim@example.com';
  submit();
  assert.match(screen.getByRole('alert').textContent, /환영합니다/);
});
```

(실험, Node 22.23.2 · jsdom 26.1.0 · @testing-library/dom 10.4.2 · node:test, 브라우저 없음, 2026-10-03)

```text
v1 brittle pass=4 fail=0 failed=[]
v1 role pass=4 fail=0 failed=[]
v2 brittle pass=0 fail=4 failed=[B1 B2 B3 B4 ]
v2 role pass=4 fail=0 failed=[]
v3 brittle pass=4 fail=0 failed=[]
v3 role pass=3 fail=1 failed=[R2 ]
v4 brittle pass=3 fail=1 failed=[B1 ]
v4 role pass=3 fail=1 failed=[R1 ]
```

| 판 | 구조 선택자 실패 | 역할·레이블 실패 | 판정 |
|---|---|---|---|
| v2 디자인 개편(동작 같음) | **4/4** | 0/4 | 구조 쪽 = 거짓 경보 4건 |
| v3 접근성 회귀 | 0/4 | **1/4** | 구조 쪽 = 놓침 |
| v4 동작 버그 | 1/4 | 1/4 | 둘 다 잡음 |

- 실패 메시지도 다르다.

```text
v2 구조 선택자 B1:  error: "Cannot read properties of null (reading 'click')"
v3 역할·레이블 R2:  Found a label with the text of: 이메일, however no form control was found associated to that label. Make sure you're using the "for" attribute or "aria-labelledby" attribute correctly.
```

- 해석
  - 구조 선택자는 **동작이 그대로인 마크업 변경**에 전부 깨졌다(리팩터링 내성 0). 메시지 `null (reading 'click')`은 "요소를 못 찾았다"만 말한다.
  - 역할·레이블 선택자는 마크업 변경을 견디고, 사용자가 실제로 겪는 접근성 회귀를 잡았다. 테스트가 사용자와 같은 방식으로 요소를 찾기 때문이다.
  - 동작 버그(v4)는 두 스타일 모두 잡았다. 차이는 거짓 경보와 접근성 쪽에서 났다.
- 이 실험의 한계: jsdom은 레이아웃·렌더링을 하지 않는다(jsdom README "Unimplemented parts"). 겹침·가려짐·CSS로 숨김 같은 시각 문제는 이 실험 범위 밖이다. 실제 브라우저 테스트(Playwright 등)는 이 환경에서 브라우저를 받지 않아 돌리지 않았다.

### 4. 기다리기 — UI 테스트 불안정의 첫 원인

```text
  클릭 ──▶ fetch 시작 ─── 200ms ───▶ 응답 ──▶ DOM 갱신
     │
     └ 고정 sleep(100ms) 후 단언  → 느린 날은 실패, 빠른 날은 통과 (불안정)
     └ "조건이 참이 될 때까지" 재시도 단언 → 시간 차이에 덜 민감
```

- Testing Library `findBy*`: Promise를 반환하고, 기본 1000ms까지 재시도한다. `getBy*`는 즉시 찾고 없으면 예외, `queryBy*`는 없으면 `null`.
- Playwright: 동작 전에 "actionability" 검사(보임·안정(애니메이션 끝)·이벤트를 받음·활성)를 통과할 때까지 자동으로 기다리고, 시간 안에 통과 못 하면 `TimeoutError`로 실패한다(Playwright 문서).
- 시간·순서·네트워크가 만드는 불안정의 일반론은 [09-flaky-tests](../09-flaky-tests/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **DOM 트리 탐색** — CSS 선택자는 트리 경로 패턴(`부모 > 자식:nth-child(1)`)으로 노드를 찾는다. 경로가 구조에 묶여 있어서 중간에 노드 하나만 끼어도 매치가 사라진다.
- **접근성 트리 질의** — 역할·이름 쿼리는 DOM에서 계산한 역할(암묵 역할: `<button>` → button)과 접근 가능한 이름(레이블·텍스트 연결)으로 찾는다. 구조가 아니라 의미 속성으로 인덱싱하는 셈이다.
- **폴링 + 타임아웃** — `findBy*`·자동 대기는 "조건 검사 → 실패면 잠깐 쉬고 재검사 → 상한 넘으면 실패" 루프다. 고정 sleep보다 빠른 날은 빨리 끝나고 느린 날은 상한까지 버틴다.
- **테스트 범위 = 그래프의 경로 커버** — 사용자 여정을 화면 상태 그래프의 경로로 보면, E2E는 소수의 중요한 경로만 덮고, 나머지 간선은 아래층 테스트가 덮는다. 상태 전이 테스트 설계는 [07-test-design-techniques](../07-test-design-techniques/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 핵심 사용자 여정 3~10개를 고른다(예시 수). "이것이 깨지면 매출·가입이 멈춘다"는 것만.
2. 그 밖의 화면 동작은 컴포넌트/UI 테스트(jsdom + Testing Library, 백엔드 가짜)로 내린다.
3. 업무 규칙은 API·서비스 테스트로, 서비스 사이 모양은 계약 테스트로 내린다.
4. 선택자는 역할·레이블 → 텍스트 → test id 순으로 고른다. CSS 경로·XPath는 피한다.
5. 기다림은 조건 기반(`findBy*`, 자동 대기)으로. 고정 sleep을 쓰지 않는다.

### 2. 컴포넌트 수준 UI 테스트 (TS, Testing Library)

```ts
import { screen } from '@testing-library/dom';
import userEvent from '@testing-library/user-event';

test('빈 이메일로 제출하면 오류를 보여 준다', async () => {
  renderLogin(document);                                   // 앱 코드
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: '로그인' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('이메일 형식이 올바르지 않습니다'); // jest-dom 단언
});
```

- `user-event`는 사용자 입력 순서(포커스·키 입력·클릭)를 흉내 낸다. 실험은 단순화를 위해 `.click()`과 `.value` 대입을 썼다.

### 3. 브라우저 E2E (TS, Playwright — 문서의 권장 로케이터 형태)

```ts
import { test, expect } from '@playwright/test';

test('로그인 후 주문 목록이 보인다', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('이메일').fill('e2e-user@example.test');   // 전용 테스트 계정
  await page.getByLabel('비밀번호').fill(process.env.E2E_PASSWORD!);
  await page.getByRole('button', { name: '로그인' }).click();     // 자동 대기 후 클릭
  await expect(page.getByRole('heading', { name: '주문 목록' })).toBeVisible(); // 재시도 단언
});
```

- 이 코드는 이 노트에서 실행하지 않았다(브라우저를 받지 않음). 형태는 Playwright Locators 문서의 권장 로케이터를 따랐다.

### 4. 진단 — "UI 테스트가 대량으로 빨강"

1. 실패 메시지를 분류한다: "요소를 못 찾음"(`null`, `Unable to find`, 타임아웃) vs "찾았는데 값이 다름".
2. "못 찾음"이 같은 커밋에서 대량이면 마크업 변경이 원인일 가능성이 크다. 그 커밋의 diff가 클래스·구조만 바꿨는지 본다.
3. 동작이 같다면 테스트 쪽 선택자를 역할·레이블로 바꾼다(앞으로 같은 일이 덜 생긴다).
4. 레이블·역할로도 못 찾으면, 그 화면은 보조 기술 사용자도 못 찾는다 — 접근성 결함으로 고친다([web-platform 영역 표](../../web-platform/README.md)의 11 accessibility-basics, 미작성).

## 장애 시나리오와 대처

### 1. ⚠ 선택자 취약 → UI 변경마다 대량 실패

- 현상: 디자인 개편 PR마다 UI 테스트 수십~수백 개가 실패. 개발자가 테스트를 "고치는" 데 하루를 쓴다.
- 보이는 형태: `Cannot read properties of null`, `Unable to find element`, 타임아웃. 실험에서는 동작이 같은 v2에서 구조 선택자 4/4 실패.
- 원인: 테스트가 CSS 경로·`nth-child`·클래스 이름(구현 세부)에 묶였다.
- 대처: 역할·레이블 선택자로 바꾸고, 그래도 안 되는 곳만 `data-testid`. 리뷰 규칙으로 CSS 경로 선택자를 막는다.

### 2. 아이스크림 콘 — E2E가 너무 많다

- 현상: CI가 수십 분~수 시간, 실패의 상당수가 재실행하면 통과. 결국 빨강을 무시한다.
- 보이는 형태: E2E 통과율이 날마다 출렁인다(Wacker 2015 가상 사례의 날짜별 통과율: 5%·4%·54%·54%·54%·1%·84%·87%·89.54%).
- 원인: 업무 규칙·경계값까지 E2E로 검증한다. E2E 하나가 실패하면 원인이 여러 층 중 어디인지 모른다.
- 대처: E2E는 핵심 여정만 남기고, 규칙은 단위·API 테스트로 내린다. 피라미드 균형은 [01-why-test-and-pyramid](../01-why-test-and-pyramid/2-summary.md).

### 3. 고정 sleep으로 인한 간헐 실패

- 현상: 로컬에서는 통과, CI에서 가끔 실패.
- 보이는 형태: 단언 시점에 요소가 아직 없음. 실패 시 스크린숏에 로딩 스피너.
- 원인: `sleep(500)` 같은 고정 대기. CI가 느린 날 초과한다.
- 대처: 조건 기반 대기(`findBy*`, Playwright 자동 대기·`expect(...).toBeVisible()`)로 바꾼다.

### 4. E2E가 공유 환경·공유 데이터 때문에 깨진다

- 현상: 다른 팀 배포·다른 테스트의 데이터 때문에 실패.
- 보이는 형태: "이미 존재하는 이메일", 남이 지운 테스트 상품. Wacker 사례의 "파트너 팀이 테스트 환경에 나쁜 빌드를 배포".
- 원인: 밀폐되지 않은 SUT와 공유 테스트 데이터.
- 대처: 실행마다 고유한 테스트 데이터(접두사·UUID), 가능한 범위에서 전용 환경. 외부 의존은 계약 테스트 + 가짜로 대체한다([08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md)의 밀폐성).

## 핵심 문장

- E2E·UI 테스트는 조립 실수를 잡는 마지막 그물이다. 느리고 원인 위치를 잘 알려 주지 않으므로 핵심 사용자 여정에만 둔다.
- 실험에서 동작이 같은 마크업 개편에 구조 선택자 테스트는 4/4 실패, 역할·레이블 테스트는 0/4 실패했다.
- 같은 실험에서 레이블 연결이 끊긴 접근성 회귀는 역할·레이블 테스트만 잡았다(1/4), 구조 선택자는 0/4.
- 고정 sleep 대신 조건이 참이 될 때까지 재시도하는 대기를 쓴다(`findBy*` 기본 1000ms, Playwright actionability 자동 대기).
- SWE@G 14장은 UI/API 경계에서 테스트를 나누고 공개 API로 E2E를 몰아가는 편이 쉬운 경우가 많다고 적는다.

## 관련 주제·근거

- 선행
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 충실도·밀폐성.
  - [13-contract-testing](../13-contract-testing/2-summary.md) — UI/API 경계와 서비스 사이를 잇는 계약.
- 후속·연결
  - [19-testing-in-production](../19-testing-in-production/2-summary.md) — 운영에서 도는 E2E(합성 모니터링·prober).
  - [01-why-test-and-pyramid](../01-why-test-and-pyramid/2-summary.md), [02-good-unit-tests](../02-good-unit-tests/2-summary.md)(리팩터링 내성), [09-flaky-tests](../09-flaky-tests/2-summary.md).
  - web-platform 11 accessibility-basics, 21 component-and-state-patterns — 미작성([web-platform 영역 표](../../web-platform/README.md)).
- 교재·글
  - SWE@G 14장 "Larger Testing" — Browser and Device Testing, UI 테스트가 깨지기 쉬운 이유와 UI/API 경계 분리 <https://abseil.io/resources/swe-book/html/ch14.html>
  - Martin Fowler, "TestPyramid", 2012-05-01 — UI 테스트는 "brittle, expensive to write, and time consuming to run", 아이스크림 콘 <https://martinfowler.com/bliki/TestPyramid.html>
  - Mike Wacker, "Just Say No to More End-to-End Tests", Google Testing Blog, 2015-04-22 — 90% 통과율 가상 사례, 70/20/10 <https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html>
- 제품 문서
  - Testing Library — About Queries(우선순위, getBy·queryBy·findBy, findBy 기본 1000ms) <https://testing-library.com/docs/queries/about/>
  - Playwright — Locators(CSS·XPath 비권장) <https://playwright.dev/docs/locators>, Auto-waiting/Actionability(Visible·Stable·Receives Events·Enabled, TimeoutError) <https://playwright.dev/docs/actionability>
  - jsdom README — Unimplemented parts(Navigation·Layout) <https://github.com/jsdom/jsdom>
- 실험 목록
  - `app.js`(로그인 폼 v1~v4), `brittle.test.js`(CSS 경로 선택자 4개), `role.test.js`(역할·레이블 4개), `run.sh`(판×스타일 실행). node:22-bookworm-slim 컨테이너(`--network none`), Node 22.23.2, jsdom 26.1.0, @testing-library/dom 10.4.2, node:test TAP 출력, 2026-10-03. v1 8개 실행 시간 2179~2290ms(3회, 실행마다 다르다 — 점검 재실행 1회는 3031ms).
