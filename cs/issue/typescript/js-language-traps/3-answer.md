# cs/issue/typescript/js-language-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **TDZ.** `const`/`let` 선언은 스코프 시작으로 호이스팅되지만 **초기화는 선언 줄에서** 일어난다.\
그 사이 구간(TDZ)에서 이름에 접근하면 ReferenceError다.\
의존성 배열 `[items, locale]`은 useEffect 호출 시점(= 선언 줄보다 위)에 평가되므로 TDZ에 걸린다.\
리팩토링 중 `useRouter()` 줄이 아래로 이동하면서 드러났고, 선언을 컴포넌트 최상단으로 옮기고 중복을 제거해 고쳤다.
   > **TDZ(Temporal Dead Zone)** — `let`/`const`/`class` 이름이 스코프에 존재하지만 아직 초기화되지 않아 접근하면 ReferenceError가 나는 구간.

2. **객체 리터럴은 즉시 평가.** 객체 리터럴은 생성될 때 **모든 속성 값 표현식을 평가**한 뒤에야 `[step]`으로 조회한다.\
그래서 선택되지 않은 분기의 `t()` 호출과 엘리먼트 생성도 매 렌더 실행된다.\
값을 썽크(`() => <CompA/>`)로 감싸고 조회 결과를 호출하면 선택된 것만 평가된다.\
이 사례는 실제 버그가 아니라 리뷰 분석이었다 — 목적은 성능보다 **부수효과 안전과 의도 일치**다.

3. **중복 키는 무음 덮어쓰기.** 에러가 나지 않는다 — JS 객체 리터럴은 같은 키를 허용하고 **마지막 값**으로 덮는다.\
`META.PENDING.tone`은 `"neutral"`이라 결제 대기 상태가 회색으로 표시됐다.\
여러 도메인(주문·결제·…)의 상태를 한 평면 맵에 넣으면 같은 단어(`PENDING`)가 충돌한다.\
도메인별 상태 타입·메타로 분리하고 린트 `no-dupe-keys`·타입 검사로 검출한다.

4. **await 없는 return.** 호출되지 않는다.\
`return api.post(...)`는 **pending promise를 그대로 반환**하고 try 블록은 즉시 끝난다.\
reject는 그 뒤에 일어나므로 이 함수의 catch가 아니라 호출부로 전파된다.\
`return await api.post(...)`는 이 함수 안에서 결과를 기다리므로 reject가 try 안에서 throw로 바뀌어 catch가 잡는다.\
(이 수정은 별도 PR로 권고됐고 적용 여부는 기록에 없다.)

5. **단일 스레드.** JS는 한 스레드에서 이벤트 루프로 돈다.\
`while (Date.now() < end) {}`는 그 스레드를 점유해 렌더링·입력·타이머 콜백이 전부 멈춘다.\
대기는 이벤트 루프에 제어를 돌려주는 방식으로 한다: `new Promise(r => setTimeout(r, ms))` + 호출부 `await`.
   > **이벤트 루프** — 단일 스레드가 작업 큐에서 콜백을 하나씩 꺼내 실행하는 구조. 실행 중인 동기 코드가 끝나야 다음 콜백이 돈다.

6. **구조화 에러의 문자열 변환.** IPC가 직렬화한 에러는 문자열이 아니라 `{ message, ... }` 객체다.\
`String(obj)`은 `Object.prototype.toString`을 불러 `"[object Object]"`만 준다.\
에러가 문자열·Error·객체 중 무엇이든 `.message`를 꺼내는 헬퍼로 표시한다.

7. **정적 도구의 범위.** 중복 키는 `no-dupe-keys`로, TDZ는 린트의 선언 전 사용 규칙(`no-use-before-define`)이나 TS로, 반환 promise의 await 누락은 린트의 `return-await` 류 규칙으로 잡을 수 있다.\
객체 리터럴 즉시 평가와 busy-wait은 **문법상 정상**이라 도구가 "틀렸다"고 하지 않는다 — 의도를 아는 리뷰가 잡는다.\
`String(err)`은 타입이 `unknown`/객체임을 TS가 알 때 경고할 여지가 있지만, IPC 경계의 에러 형태는 런타임 계약이라 헬퍼로 한 곳에 가둔다.

## 문제 구조 (추상화 코드)

### 변형 A — 선언 전 접근 (TDZ)
① 문제 코드
```tsx
function Panel() {
  useEffect(() => { /* ... */ }, [items, locale]);   // locale 은 아직 TDZ → ReferenceError
  const { locale } = useRouter();
}
```
② 고친 코드
```tsx
function Panel() {
  const { locale } = useRouter();                    // 최상단
  useEffect(() => { /* ... */ }, [items, locale]);
}
```
무엇이 깨졌나: 코드 이동으로 사용이 선언보다 앞에 놓였다.

### 변형 B — 객체 리터럴 dispatch의 즉시 평가
① 문제 코드
```tsx
return {
  [Step.AUTH]:    <LoginStep title={t("a")} hint={t("b")} />,   // CONFIRM 이어도 매 렌더 평가
  [Step.CONFIRM]: <ConfirmStep />,
}[step];
```
② 고친 코드
```tsx
const steps = {
  [Step.AUTH]:    () => <LoginStep title={t("a")} hint={t("b")} />,
  [Step.CONFIRM]: () => <ConfirmStep />,
};
return (steps[step] ?? steps[Step.CONFIRM])();
```
무엇이 깨졌나: 객체 리터럴을 지연 평가되는 switch로 착각했다.

### 변형 C — 중복 키 무음 덮어쓰기
① 문제 코드
```ts
const STATUS_META = {
  PENDING: { tone: "warn" },      // 주문 도메인
  // ...
  PENDING: { tone: "neutral" },   // 다른 도메인 — 앞의 값을 조용히 덮음
};
```
② 고친 코드
```ts
const ORDER_STATUS_META: Record<OrderStatus, Meta> = { PENDING: { tone: "warn" } /* ... */ };
const OTHER_STATUS_META: Record<OtherStatus, Meta> = { PENDING: { tone: "neutral" } /* ... */ };
// + eslint no-dupe-keys
```
무엇이 깨졌나: 여러 도메인의 이름 공간을 한 평면 맵에 합쳤다.

### 변형 D — 비동기·스레드 함정
① 문제 코드
```ts
async function save(data) {
  try { return http.post("/x", data); }       // reject 는 try 가 끝난 뒤 → catch 우회
  catch (e) { handleApiError(e); }
}
function sleep(ms) { const end = Date.now() + ms; while (Date.now() < end) {} }   // 메인 스레드 점유
```
② 고친 코드
```ts
async function save(data) {
  try { return await http.post("/x", data); }
  catch (e) { handleApiError(e); }
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));    // 호출부: await sleep(100)
```
무엇이 깨졌나: promise 반환 시점과 reject 시점, 동기 대기와 이벤트 루프의 관계를 놓쳤다.

### 변형 E — 구조화 에러의 문자열 변환
① 문제 코드
```ts
invoke("cmd").catch(err => setError(String(err)));    // "[object Object]"
```
② 고친 코드
```ts
const errString = (e: unknown) =>
  typeof e === "string" ? e : (e as { message?: string })?.message ?? JSON.stringify(e);
invoke("cmd").catch(err => setError(errString(err)));
```
무엇이 깨졌나: IPC 경계의 에러가 문자열이라고 가정했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
