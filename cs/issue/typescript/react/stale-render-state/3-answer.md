# cs/issue/typescript/react/stale-render-state — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: `race-condition`

## 정답

<!-- 질문 1:1 대응 -->

1. 함수 컴포넌트는 렌더마다 다시 호출되고, 그 안에서 만든 콜백은 **그 렌더의 `isLoading` 값**을 클로저로 잡는다.\
`showLoader()`는 state 갱신을 **예약**할 뿐, 이미 실행 중인 함수의 `isLoading` 변수를 바꾸지 않는다 — 같은 함수 안에서는 끝까지 false다. 그래서 검사가 항상 "로딩이 꺼졌다 = 중단"으로 판정됐다.\
ref는 렌더마다 새로 만들어지지 않는 **같은 객체**이고 `.current`는 쓰는 즉시 바뀐다. 모든 클로저가 같은 객체를 참조하므로 최신 값을 읽을 수 있다. state와 ref를 함께 갱신하고(`showLoader`/`hideSpinner` 안에서), async 내부는 ref를 검사한다.
   > **stale closure** — 클로저가 생성 시점의 변수 바인딩을 계속 들고 있어, 이후 바뀐 값을 보지 못하는 현상.

2. 막히지 않는다. 콜백은 마운트 때 한 번 만들어졌으므로 **마운트 시점의 잠금값(false)** 을 영원히 본다.\
잠금 조건을 ref에 동기화(`lockedRef.current = busy || draft != null`)하고, 콜백은 `lockedRef.current`를 검사한다.

3. React 18+의 동시성 루트(createRoot)는 연속 이벤트(`dragover`)에서 발생한 업데이트를 이산 이벤트(`drop`)보다 **낮은 우선순위**로 처리한다. 그래서 drop 핸들러가 실행될 때 렌더된 state는 **마지막 dragover 결과보다 오래됐을 수 있다**.\
근본 해법은 두 이벤트 사이에 state로 값을 넘기지 않는 것이다. 미리보기와 결과가 **같은 순수 함수·같은 종류의 입력(좌표)** 을 쓰게 하면, drop은 자기 좌표로 다시 계산해 미리보기와 일치한다. 상태 기계가 사라진다.
   > **이산(discrete) / 연속(continuous) 이벤트** — 클릭·드롭처럼 한 번의 의도인 이벤트와, 마우스 이동·드래그오버처럼 연달아 오는 이벤트. React는 전자를 더 급하게 처리한다.

4. 두 호출이 같은 렌더의 핸들러(같은 클로저)로 실행되면 **두 번** 보내진다. `setSending(true)`는 다음 렌더에 반영되므로, 리렌더가 커밋되기 전에 실행된 두 번째 호출도 `sending === false`를 본다. React 18은 클릭 같은 이산 이벤트의 업데이트를 이벤트가 끝날 때 동기로 반영하므로 사람의 두 클릭 사이에는 대개 리렌더가 끼지만, 같은 배치 안의 연속 호출·프로그램 호출·await 이후 재진입 등에서는 막히지 않는다 — state 가드는 보장된 상호 배제가 아니다.\
"존재 확인 후 생성"도 확인과 생성 사이에 다른 호출이 끼어들 수 있어 같은 문제다 — 두 호출 모두 "없음"을 보고 둘 다 만든다. 파일 이동 후 덮어쓰기 버튼을 중복 클릭해, 이동이 끝난 결과물을 다시 삭제한 심각한 사례가 있었다.\
해법: **동기 ref로 single-flight**(`if (busyRef.current) return; busyRef.current = true; try { … } finally { busyRef.current = false; }`) + 버튼 disabled. 창 생성처럼 완료가 이벤트로 오는 작업은 생성·오류 이벤트가 올 때까지 가드를 유지한다.

5. 오르지 않을 수 있다. 각 클릭 핸들러가 **렌더 시점에 캡처한 `font`** 에 +1을 하므로, 리렌더 전에 실행된 연타는 같은 값에 +1을 반복한다(함수형 업데이트 `setX(x => x + 1)`도 같은 문제를 피한다). 최신 저장값(`getState()`) 기준으로 증감하고, 경계값에서는 버튼을 disabled한다.\
`Number("")`는 NaN이 아니라 **0**이다. 그래서 "빈 입력"이 유효 숫자로 통과해 하한으로 clamp되어 버렸다(사양은 "빈 값이면 이전 값 복원"). 커밋 전에 정수 형식(`/^\d+$/`)을 검사하고 아니면 복원한다.

6. effect가 읽는 props는 **렌더된 값**이다. 외부 라이브러리의 파라미터 갱신이 다음 렌더 props에 언제 반영되는지 보장이 없으면, 세대를 올려 effect를 재실행해도 effect는 옛 props로 옛 세션에 붙는다 — 이어지는 `close(old)`가 방금 붙은 세션을 죽이는 경쟁도 생겼다.\
새 값을 **`pendingRef`에 직접 넣고** effect가 그것을 꺼내 쓴 뒤 비운다(consume). props 전파 타이밍에 의존하지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — async 콜백이 렌더 스냅샷 state를 검사
① 문제 코드
```tsx
const { isLoading, showLoader } = useSpinner();
const search = useCallback(async () => {
  showLoader();
  const res = await api.search(q);
  if (!isLoading) throw new Error("stop");      // 이 클로저의 isLoading 은 항상 false
  render(res);
}, [q]);
```
② 고친 코드
```tsx
// Provider: state 와 ref 를 함께 갱신
const showLoader = () => { loadingRef.current = true; setIsLoading(true); };
// 사용처
const search = useCallback(async () => {
  showLoader();
  const res = await api.search(q);
  if (!loadingRef.current) throw new Error("stop");   // 최신 값
  render(res);
}, [q]);
```
무엇이 깨졌나: 명령형 DOM 검사를 state로 바꾸면서, state가 "지금 값"이 아니라 "이 렌더의 값"이라는 차이를 놓쳤다.\
같은 구조: 같은 수정을 한 화면에만 적용해 다른 검색 화면·모달 훅에 같은 버그가 남음 — 유사 훅을 교차 검증.

### 변형 B — 마운트 1회 등록 콜백이 state를 읽음 · effect가 옛 props를 읽음
① 문제 코드
```ts
useEffect(() => {
  const sub = widget.onData((d) => { if (locked) return; send(d); });   // 마운트 시점 locked 고정
  return () => sub.dispose();
}, []);
setGen((g) => g + 1);                              // effect 재실행 → 아직 옛 props.params 로 attach
```
② 고친 코드
```ts
useEffect(() => { lockedRef.current = busy || draft != null; }, [busy, draft]);
useEffect(() => {
  const sub = widget.onData((d) => { if (sessionIdRef.current == null || lockedRef.current) return; send(d); });   // 콜백이 읽는 값은 모두 ref 로
  return () => sub.dispose();
}, []);
pendingAttachRef.current = { id, uuid };           // 새 값을 직접 전달
setGen((g) => g + 1);
// effect: const next = pendingAttachRef.current ?? props.params; pendingAttachRef.current = null;
```
무엇이 깨졌나: 수명이 긴 콜백·재실행된 effect가 렌더에 묶인 값을 읽어, 최신 값이 전달되지 않았다.

### 변형 C — 우선순위가 다른 이벤트 사이에 state로 값 전달
① 문제 코드
```ts
onDragOver = (e) => setZone(computeZone(e.clientX, e.clientY, groups));
onDrop = () => place(zone);                        // dragover 업데이트가 아직 렌더 안 됐을 수 있음
```
② 고친 코드
```ts
onDragOver = (e) => { const z = computeZone(e.clientX, e.clientY, groups); if (!sameRect(z, zone)) setZone(z); };   // 미리보기용
onDrop = (e) => place(computeZone(e.clientX, e.clientY, groups));   // 같은 순수 함수·자기 좌표
```
무엇이 깨졌나: 낮은 우선순위 업데이트의 결과를 높은 우선순위 이벤트가 읽었다.

### 변형 D — state 가드로 check-then-act
① 문제 코드
```ts
const onSend = async () => {
  if (sending) return;                             // 리렌더 전 두 번째 호출도 false
  setSending(true);
  await send(); setSending(false);
};
```
② 고친 코드
```ts
const onSend = async () => {
  if (busyRef.current) return;                     // 동기 가드
  busyRef.current = true; setSending(true);        // state 는 disabled 표시용
  try { await send(); } finally { busyRef.current = false; setSending(false); }
};
```
무엇이 깨졌나: 다음 렌더에 반영되는 state를 즉시 효력이 필요한 상호 배제에 썼다.\
같은 구조: 덮어쓰기 버튼 중복 클릭 → 이동 완료본 재삭제. 드롭으로 창 생성 시 확인-후-생성 경쟁 → 생성·오류 이벤트까지 가드 유지. 종료 경로의 동기 재진입 → 재진입 가드.

### 변형 E — 렌더 캡처 값으로 연속 증감 · 빈 입력의 숫자 강제변환
① 문제 코드
```ts
onPlus = () => setFont(clamp(font + 1));           // 렌더 캡처 값 → 연타 경합
commit = (draft) => setFont(clamp(Number(draft))); // Number("") === 0 → 하한으로 리셋
```
② 고친 코드
```ts
onPlus = () => setFont(clamp(store.getState().font + 1));   // 최신 값 기준 · 경계에서 disabled
commit = (draft) => { if (!/^\d+$/.test(draft)) return restore(); setFont(clamp(Number(draft))); };
```
무엇이 깨졌나: 연속 이벤트가 렌더 시점 값을 기준으로 계산했고, 빈 문자열이 숫자 0으로 강제변환되어 유효값처럼 통과했다.

## 검증 기록

- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
