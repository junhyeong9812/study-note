# cs/issue/typescript/react/effect-dependency-and-timing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. effect는 deps 원소의 **값이 달라졌을 때만** 다시 돈다. `path`가 같으면 다른 항목이어도 "변화 없음"이고, 원시값 `commit`을 같은 값으로 다시 선택해도 "변화 없음"이다.\
그 결과 파일이 바뀌었거나 첫 조회가 실패해 재시도해야 하는 상황에서도 fetch가 일어나지 않았다.\
정체성은 **엔티티 id를 `refreshKey`로** deps에 넣어 담는다(다른 호출부는 undefined라 기존 동작 유지). "액션마다 실행"은 액션이 일어날 때마다 **새 객체**를 상태에 넣어, 참조가 바뀌도록 해서 담는다 — 같은 액션 안의 다른 클릭(파일 선택)은 객체를 바꾸지 않아 불필요한 refetch가 없다.
   > **deps(의존성 배열)** — effect를 다시 실행할지 판단하는 값 목록. 각 원소를 이전 렌더 값과 `Object.is`로 비교한다.

2. 매 렌더 새 객체는 항상 "다름"이므로 **매 렌더 effect가 돈다** — 실패를 캐시하지 않으니 실패한 조회도 매번 다시 나가 호출이 폭주한다. 해법: 키 **문자열**을 deps로, 실패는 `null` sentinel로 캐시.\
교착: A 조회 중 B로 갔다가 A로 돌아오면, in-flight 가드는 "A는 진행 중"이라 재요청을 막고, 첫 A 요청의 결과는 cleanup의 `alive=false` 때문에 버려진다 — 누구도 결과를 반영하지 않아 **영구 "불러오는 중"** 이 된다.\
해법은 결과를 컴포넌트 수명이 아니라 **키 스코프로 항상 캐시**하는 것이다(언마운트 후 setState는 무해한 no-op). 캐시 축출이 현재 보고 있는 키를 밀어내도 같은 고착이 생기므로, 캐시 미스를 deps에 넣어 재요청하게 한다.

3. effect로 동기화하면, 커밋·페인트된 첫 프레임에는 **옛 값**이 쓰인다 — 같은 대상을 두 번 그리는 UI가 한 프레임 겹쳐 보인다.\
그 옛 값이 "마운트할지"를 결정한다면, 한 프레임 동안 마운트되면서 **부작용(프로세스 생성)** 이 이미 실행된다 — 화면 깜빡임이 아니라 되돌릴 수 없는 동작이다.\
"렌더 중 조정"은 `prevRef`로 입력 전환을 감지해 **렌더 도중** 조건부 `setState`를 부른다. React는 그 렌더 결과를 버리고 페인트 전에 즉시 다시 렌더하므로 옛 값이 화면·자식 마운트에 도달하지 않는다. 더 좋은 것은 파생값을 아예 저장하지 않고 매 렌더 계산하는 것이다.
   > **렌더 중 조정(adjust state during render)** — 이전 입력을 ref로 기억해, 입력이 바뀐 렌더에서 곧바로 파생 state를 고치는 패턴. effect보다 한 프레임 빠르다.

4. 브라우저는 비활성 탭의 타이머를 스로틀하므로 tick이 덜 온다 — tick 수로 센 경과 시간은 **실제보다 느리게** 흐른다.\
prop을 state로 옮겨 담으면 prop이 바뀐 렌더에서 state는 아직 옛 값이다. `remaining`이 null→3600이 된 렌더에서 `left`가 0이면 `expired = true`가 계산되고, 만료 effect가 오발화해 인증 직후 즉시 로그아웃된다.\
해법: 남은 초를 state에 두지 않고 **절대 마감시각에서 매 렌더 도출**(stale 창 제거), 탭 복귀(visibility/focus) 때 재계산, interval은 표시값이 바뀔 때만 tick.

5. deps 값이 같으면 memo·effect는 "새 회차"를 알 수 없다. **회차 식별자 `resetNonce`**(발송 회차 번호)를 파라미터로 받아 deps에 넣는다. 만료 처리도 `${remaining}-${resetNonce}` 같은 회차 키로 "회차당 1회"를 보장한다.

6. **`ResizeObserver`** 로 내용 요소의 크기 변화 자체를 관찰한다 — 원인이 무엇이든 높이가 바뀌면 발화한다. deps에 값을 더 넣는 방식은 다른 성장 요인을 또 놓치고, DOM 변경 관찰(MutationObserver)은 높이와 무관한 변화에도 발화한다.\
루프가 없는 조건: 콜백이 `scrollTop`만 바꾸고 관찰 대상의 **border-box 크기는 바꾸지 않는다**. 크기를 바꾸는 쪽으로 반응하면 관찰→변경→관찰의 루프가 된다. 관찰 대상 밖의 요소가 커지는 경우는 여전히 못 본다(범위 한계).

7. effect 본문에서 동기로 state를 바꾸면 **커밋 직후 추가 렌더**가 곧바로 일어나 렌더가 연쇄된다.\
동기 `setLoading(true)`는 사용자 액션의 **이벤트 핸들러**에 두고, 마운트 effect에서는 await 이후에만 state를 바꾸거나 `Promise.resolve().then(() => load())`로 비동기 경로에 넣는다.

## 문제 구조 (추상화 코드)

### 변형 A — deps가 의도(정체성·액션·회차)를 담지 못함
① 문제 코드
```ts
const text = useFileText(path);                               // 같은 path 의 다른 항목 → 재조회 없음
useEffect(() => { openTopFile(root, commit); }, [root, commit]);   // 같은 commit 재클릭 → 무시
const deadline = useMemo(() => now() + expiresIn * 1000, [expiresIn]);   // 180 → 180 : 새 회차 모름
```
② 고친 코드
```ts
const text = useFileText(path, { refreshKey: item.id });      // 엔티티 정체성을 deps 로
openHistory = (root, commit) => set({ history: { root, commit }, historyFile: null });   // 액션마다 새 객체
useEffect(() => { openTopFile(history); }, [history]);
const cd = useTimer(expiresIn, resetNonce);                 // 회차 키
useFireOnce(cd.expired, `${expiresIn}-${resetNonce}`, onTimeout);
```
무엇이 깨졌나: effect가 값 동등성으로만 판단한다는 사실을 두고, "다시 해야 하는 이유"를 deps에 넣지 않았다.

### 변형 B — 매 렌더 새 객체 deps · 가드와 폐기의 교착
① 문제 코드
```ts
useEffect(() => {
  if (inflight.has(key)) return;                  // 중복 방지
  let alive = true;
  inflight.add(key);
  loadItem(selectedItem).then((d) => { if (alive) setDetail(d); })   // 실패는 캐시 안 함
    .finally(() => inflight.delete(key));
  return () => { alive = false; };                // A→B→A: 결과 폐기 + 재요청 차단 → 영구 로딩
}, [selectedItem]);                               // 매 emit 새 객체 → 매번 재실행
```
② 고친 코드
```ts
const key = `${sessionId}:${itemId}`;             // 안정 키 (세션 간 오염도 차단)
useEffect(() => {
  if (cache.has(key) || inflight.has(key)) return;
  inflight.add(key);
  loadItem(key)
    .then((d) => cache.set(key, d), () => cache.set(key, null))   // 실패도 sentinel 캐시
    .finally(() => { inflight.delete(key); bump(); });            // 결과는 항상 키 스코프로 반영
}, [key, cache.has(key)]);                        // 축출로 미스가 되면 재요청
```
무엇이 깨졌나: 참조가 매번 다른 deps와, 결과를 컴포넌트 수명에 묶은 폐기가 중복 방지 가드와 맞물렸다.

### 변형 C — 렌더에서 파생 가능한 값을 effect로 동기화
① 문제 코드
```tsx
useEffect(() => { if (active !== visited) setVisited(null); }, [active]);   // 한 프레임 옛 visited
return visited === active ? <HeavyLayer /> : null;                         // 그 프레임에 마운트 → 프로세스 생성
```
② 고친 코드
```tsx
if (prevActiveRef.current !== active) {             // 렌더 중 조정
  prevActiveRef.current = active;
  if (visited !== null && visited !== active) setVisited(null);
}
const show = !!active && visited === active;        // 저장하지 않고 파생
return show ? <HeavyLayer /> : null;
```
무엇이 깨졌나: effect는 페인트 뒤에 도는데, 그 전 프레임의 옛 값이 마운트 여부를 결정했다.\
같은 구조: "오른쪽 표면이 활성 프로젝트와 같으면 닫기"를 effect로 해 한 프레임 같은 화면 두 개가 겹침 — 가시 여부를 렌더 중 순수 파생, effect는 영속 값 청소에만.\
같은 구조: 한 번 켜지면 영구 유지하던 래치가 재방문 이익 없이 무거운 자식을 다시 띄움 — 전환 시 해제.

### 변형 D — 시간 경과를 tick 수·옮겨 담은 state로 계산
① 문제 코드
```ts
const [left, setLeft] = useState(0);
useEffect(() => { setLeft(remaining ?? 0); }, [remaining]);   // null→3600 렌더에서 left 는 아직 0
useEffect(() => { const t = setInterval(() => setLeft((s) => s - 1), 1000); return () => clearInterval(t); }, []);
const expired = left <= 0;                                   // 오발화 → 즉시 로그아웃
```
② 고친 코드
```ts
const deadline = useMemo(() => (remaining == null ? null : Date.now() + remaining * 1000), [remaining, resetNonce]);
const [, force] = useReducer((x) => x + 1, 0);
useEffect(() => { /* 표시값이 바뀔 때만 tick · visibilitychange/focus 에서 force() */ }, [deadline]);
const left = deadline == null ? null : Math.max(0, Math.ceil((deadline - Date.now()) / 1000));   // 매 렌더 도출
const expired = left === 0;
```
무엇이 깨졌나: 경과 시간을 스로틀되는 tick 수로 셌고, prop을 state로 옮긴 사이의 stale 창이 만료 판정을 오발화시켰다.

### 변형 E — deps 밖 요인으로 변하는 크기
① 문제 코드
```ts
useEffect(() => { if (stick) el.scrollTop = el.scrollHeight; }, [items, turns.length]);   // 스트리밍·펼침·폰트 누락
```
② 고친 코드
```ts
useEffect(() => {
  const ro = new ResizeObserver(() => { if (stickRef.current) el.scrollTop = el.scrollHeight; });
  ro.observe(content);                  // scrollTop 만 변경 → 관찰 대상 크기 불변 → 루프 없음
  return () => ro.disconnect();
}, []);
```
무엇이 깨졌나: 높이는 deps에 없는 요인으로도 바뀌는데, 값 변화만 보는 effect로 크기 변화를 대신했다.

### 변형 F — effect 본문의 동기 setState
① 문제 코드
```ts
const load = async (page, q) => { setLoading(true); /* ... */ };
useEffect(() => { void load(1, ""); }, [load]);            // 커밋 직후 추가 렌더 연쇄
```
② 고친 코드
```ts
useEffect(() => { void Promise.resolve().then(() => load(1, "")); }, [load]);
// 동기 setLoading(true) 는 사용자 액션의 이벤트 핸들러 경로에서만
```
무엇이 깨졌나: effect에서 동기로 state를 바꿔 커밋마다 렌더가 한 번 더 연쇄됐다.

## 검증 기록

- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
