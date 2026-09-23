# cs/issue/typescript/react/async-subscription-cleanup — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답

<!-- 질문 1:1 대응 -->

1. cleanup은 **동기**로 즉시 실행되고, 해제 함수는 promise가 resolve된 **다음 마이크로태스크 이후**에야 변수에 들어온다.\
언마운트가 resolve보다 먼저 오면 cleanup 시점의 `unlisten`은 아직 `undefined`라 `unlisten?.()`는 아무것도 하지 않는다.\
그 뒤 resolve가 `unlisten = f`를 대입하지만, 그것을 부를 코드(cleanup)는 이미 지나갔다 — 리스너는 앱이 끝날 때까지 남는다.
   > **cleanup** — effect가 반환한 함수. 다음 effect 실행 전이나 언마운트 때 React가 동기로 호출한다.

2. **두 번**이다.\
첫 mount의 `listen`이 등록되고, 곧바로 온 unmount의 cleanup은 핸들을 못 받아 해제하지 못한다. 두 번째 mount가 또 등록한다.\
결과적으로 같은 이벤트에 콜백이 둘 붙어 있어 응답 텍스트가 **정확히 두 번씩** 출력된다 — 배수가 정확히 2인 것이 "StrictMode 이중 실행 × 해제 누락"의 지문이다.
   > **StrictMode 이중 실행** — 개발 모드에서 effect의 정리 누락을 드러내려고 mount→unmount→mount를 일부러 한 번 더 돌리는 동작.

3. **disposed 플래그**는 "도착한 핸들을, 이미 정리된 상태면 즉시 부른다"를 보장한다 — 해제 책임이 도착 시점으로 옮겨진다.\
**promise 해제**(`return () => { p.then(f => f()) }`)는 cleanup이 promise 자체를 잡고 있어 "언젠가 도착하면 그때 해제"를 보장한다. 둘 다 누수를 막지만, 두 방식 모두 cleanup 이후 해제 함수가 실제로 불리기 전까지는 리스너가 살아 있어 콜백이 불릴 수 있다 — 콜백 안에서도 disposed를 보는 편이 안전하다.\
await가 여러 번이면(연결 생성 수 초 → 구독 등록) **각 await 직후** `if (disposed) { 방금 얻은 것 해제; return; }`를 둬야 한다. 첫 await 뒤에서만 검사하면, 두 번째 await 동안 언마운트된 경우 리스너가 이미 폐기된 위젯(수 MB 스크롤백)을 계속 참조한다.

4. 같은 점: 둘 다 "결과가 도착했을 때 그 결과의 주인이 아직 유효한가"를 판정한다.\
다른 점: disposed는 **한 effect 인스턴스의 생사**만 보지만, 세대 번호는 **같은 주인에게 겹쳐 들어온 여러 요청 중 최신이 무엇인가**까지 본다 — 두 attach가 동시에 진행되면 진 쪽(옛 세대)이 자기 결과를 스스로 닫는다.\
닫기·언마운트가 세대를 올리지 않으면, 닫은 뒤 늦게 도착한 attach가 "내가 최신"이라고 판단해 ref를 채우고, 그걸 닫을 코드는 이미 지나가 원격 연결이 세션 종료 때까지 남는다.
   > **세대(generation) 토큰** — 작업 시작 때 발급한 증가 번호. 완료 시점에 현재 번호와 다르면 결과를 버리거나 닫는다.

5. 구독 실패를 처리하지 않으면 unhandled rejection이 나고, 이 사례처럼 구독 await 뒤에 초기화 단계(초기 데이터 적재)가 이어지는 구조라면 그 단계에 도달하지 못해 **빈 화면**이 된다(rejection 자체가 화면을 비우는 것이 아니라 이후 코드가 실행되지 않는 것이다).\
또 구독 전에 선점한 자원(세션 claim·슬롯)이 풀리지 않으면 tombstone처럼 남아 다음 후보를 막는다.\
그래서 등록은 "성공 / 언마운트 후 성공 / 실패" 세 경로를 다 가져야 하고, 실패 경로는 선점 해제 + 사용자에게 보이는 실패 상태가 된다.

6. 이전 disposable을 해제하지 않고 재설치하면 콜백이 누적된다 — 레이아웃이 한 번 바뀔 때 핸들러가 N번 불리고, 겹친 드래그를 취소해도 **옛 dragend 리스너가 늦게 발화**해 의도하지 않은 동작(팝아웃 생성)을 한다.\
제스처마다 AbortController 하나를 만들고 모든 리스너를 `{ signal }`로 등록하면, 새 제스처 시작·언마운트 때 `abort()` 한 번으로 그 제스처의 리스너가 전부 떨어진다 — 해제 대상을 하나하나 기억할 필요가 없다.

7. 명령형 인스턴스와 DOM 리스너는 선언형 렌더가 새 DOM을 만들어도 **스스로 사라지지 않는다** — (이 사례의 차트 라이브러리처럼) 같은 canvas에 이전 인스턴스를 파괴하지 않고 새 차트를 만들면 "이미 사용 중" 오류가 나고, 템플릿을 다시 그릴 때마다 리스너가 중복된다.\
그래서 재생성 전에 `destroy()`하고, 노드에 "바인딩됨" 표시를 남겨 한 번만 바인딩한다 — "수명을 명시적으로 소유한다"는 점에서 이 카드와 같은 원리다.\
promise를 메모이즈하면 **거부된 promise도** 캐시되어, 이후 호출은 모두 같은 거부를 즉시 돌려받는다. 실패 시 캐시를 비워야 재시도가 가능하다.

## 문제 구조 (추상화 코드)

### 변형 A — 핸들이 cleanup보다 늦게 도착 (StrictMode 이중 등록)
① 문제 코드
```ts
useEffect(() => {
  let un: (() => void) | undefined;
  listen("output", onChunk).then((f) => (un = f));   // 핸들은 나중에
  return () => un?.();                               // 이 시점엔 undefined → 해제 안 됨
}, []);
```
② 고친 코드
```ts
useEffect(() => {
  let disposed = false;
  let un: (() => void) | undefined;
  listen("output", onChunk)
    .then((f) => (disposed ? f() : (un = f)))        // 도착 즉시 판정
    .catch((e) => { if (!disposed) reportError(e); });   // 등록 실패를 삼키지 않는다
  // onChunk 안에서도 disposed 확인 — 해제 함수가 도착·호출되기 전까지는 이벤트가 올 수 있다
  return () => { disposed = true; un?.(); };
}, []);
```
무엇이 깨졌나: 해제 책임을 cleanup 시점에만 두어, 늦게 도착한 핸들을 아무도 부르지 않았다.\
같은 구조: 패널을 빨리 닫으면 상태 채널 리스너만 남던 경우 — cleanup에서 `p.then(f => f())`로 promise 자체를 해제.\
같은 구조: 창 간 드롭 대상 리스너가 remount마다 중복되던 경우 — 같은 disposed 가드.

### 변형 B — await가 여러 번인데 재검사가 한 번뿐
① 문제 코드
```ts
async function start() {
  const conn = await openConnection();      // 수 초 걸림
  const un = await listen("data", (d) => widget.write(d));
  unRef = un;                               // 언마운트됐어도 등록 → 폐기된 widget 영구 참조
  setTimeout(() => setReady(), 3000);      // 언마운트 후에도 발화
}
```
② 고친 코드
```ts
async function start() {
  const conn = await openConnection();
  if (disposed) { conn.close(); return; }
  let un;
  try { un = await listen("data", (d) => { if (!disposed) widget.write(d); }); }
  catch (e) { conn.close(); registry.release(id); reportError(e); return; }   // 등록 실패: 연결·선점 해제 + 실패 표시
  if (disposed) { un(); return; }
  unRef = un;
  timer = setTimeout(() => { if (!disposed) setReady(); }, 3000);
}
```
무엇이 깨졌나: await 사이의 모든 지점이 언마운트 가능 지점인데 한 곳만 지켰고, 실패 경로는 선점을 풀지 않았다.\
같은 구조: 첫 구독이 실패하면 unhandled rejection으로 초기화 단계에 닿지 못해 빈 화면이 되던 경우 — 등록 실패 경로가 없었다.

### 변형 C — 늦게 도착한 비동기 attach가 버려진 자원을 붙잡음 (세대 토큰)
① 문제 코드
```ts
async function attach(sessionId) {
  const term = await remote.attach(sessionId);   // 도중에 다른 attach·탭 전환·닫기 가능
  setTerm(term);                                 // ref 는 렌더 뒤 effect 에서 맞춰짐 → 동시 호출 둘 다 null 을 봄
}
```
② 고친 코드
```ts
async function attach(sessionId) {
  const my = ++attachSeq.current;
  const term = await remote.attach(sessionId);
  if (my !== attachSeq.current) { term.close(); return; }   // 진 쪽이 자기 것을 닫음
  termRef.current?.close();                                 // 교체라면 이전 연결 정리(유지·detach 정책이면 그에 맞게)
  termRef.current = term;                                   // ref 를 세우는 순간 동기 갱신(렌더 뒤 effect 아님)
}
function close() { attachSeq.current++; termRef.current?.close(); }   // 닫기·언마운트도 세대 올림
```
무엇이 깨졌나: 결과를 받을 주인이 아직 최신인지 확인하지 않아, 늦은 결과가 원격 연결을 세션 종료까지 붙잡았다.

### 변형 D — 재설치되는 disposable을 해제하지 않음
① 문제 코드
```ts
onReady(() => {
  layout.onDidChange(save);                 // onReady 가 다시 오면 또 등록
});
function onDragStart() {
  window.addEventListener("dragend", onEnd, true);   // 이전 제스처 것이 남아 늦게 발화
}
```
② 고친 코드
```ts
let disposables: Disposable[] = [];
onReady(() => {
  disposables.forEach((d) => d.dispose());
  disposables = [layout.onDidChange(save)];
});
let gesture: AbortController | null = null;
function onDragStart() {
  gesture?.abort();                                  // 이전 제스처 정리
  gesture = new AbortController();
  window.addEventListener("dragend", onEnd, { capture: true, signal: gesture.signal });
}
// unmount: gesture?.abort()
```
무엇이 깨졌나: 재할당이 이전 disposable의 수명을 끝내지 않아 옛 콜백이 계속 살아 있었다.

## 검증 기록

- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~D)은 "선언형 effect의 cleanup과 비동기 도착 시점을 disposed·세대로 맞춘다"이다.\
같은 원리(수명이 렌더와 따로 도는 자원)에 다른 방안이 쓰인 사례:

### 방안 1 — 명령형 라이브러리 인스턴스·리스너 수명을 직접 소유
```js
// 문제
function openModal(data) {
  container.innerHTML = template(data);                 // canvas 재생성 또는 재사용
  state.chart = new ChartLib(canvas, cfg(data));            // 같은 canvas 에 두 번째 → "이미 사용 중"
  canvas.addEventListener("wheel", zoom);                // 렌더마다 중복 · passive 미명시(대상·브라우저에 따라 passive 취급되면 preventDefault 무시)
}
let apiPromise;
const getStatus = () => (apiPromise ??= fetch(url).then((r) => r.json()));   // 실패도 영구 캐시

// 고친
function openModal(data) {
  state.chart?.destroy();                                // 재생성 전 파괴
  state.chart = new ChartLib(canvas, cfg(data));
  if (!canvas.dataset.bound) {                           // 노드당 1회 바인딩
    canvas.dataset.bound = "1";
    canvas.addEventListener("wheel", (e) => { e.preventDefault(); zoom(e); }, { passive: false });
  }
}
const getStatus = () =>
  (apiPromise ??= fetch(url)
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })   // fetch 는 HTTP 오류로 reject 하지 않는다
    .catch((e) => { apiPromise = null; throw e; }));
```
같은 구조: 회전 여부를 플래그 두 개에 직접 대입하던 것을 파생값(`!pausedByUser && !modalOpen`)으로 바꿔 모순 상태를 구조적으로 없앰.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: effect + disposed/세대 | 컴포넌트 수명 = 구독 수명 | 가드 코드 몇 줄 | await마다 재검사를 빠뜨리면 누수 | React 컴포넌트 안의 비동기 구독 |
| 1. 인스턴스·리스너 직접 소유 | 렌더가 DOM을 통째로 다시 만든다 | 인스턴스 참조·바인딩 표시 관리 | destroy 누락 시 중복·오류, 바인딩 표시가 노드와 함께 사라지면 재바인딩 | 바닐라 JS·명령형 라이브러리 |

**결론**: 프레임워크가 cleanup 시점을 주면 그 시점과 비동기 도착을 **disposed·세대로 맞추는 쪽**이 간단하다.\
렌더가 DOM을 재생성하고 인스턴스가 그 밖에 사는 명령형 코드에서는 cleanup 훅이 없으므로, **인스턴스 참조를 한 곳이 소유**하고 재생성 직전 파괴·노드당 1회 바인딩으로 수명을 직접 관리한다.
