# cs/issue/typescript/react/render-and-subscription-cost — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답

<!-- 질문 1:1 대응 -->

1. 전 행 렌더는 비용이 **전체 행 수**에 비례한다. 가상화는 보이는 창(+위아래 여유 overscan)만 렌더해 비용을 **뷰포트 높이**에 묶는다.\
`end = min(len, ceil((scrollTop + viewH) / ROW_H) + OVERSCAN)`, `start = max(0, min(floor(scrollTop / ROW_H) - OVERSCAN, end))`. 전체 높이 `len * ROW_H`의 spacer로 스크롤바를 유지하고, 창은 `top = start * ROW_H`에 절대 배치한다. 뷰 높이는 ResizeObserver로 재고, 오프셋 정확도를 위해 컨테이너 padding은 0으로 둔다.\
행 높이가 가변이면 `scrollTop / ROW_H`로 인덱스를 구할 수 없어, 원본·마크다운처럼 높이가 달라지는 뷰는 대상에서 뺐다.
   > **overscan** — 보이는 범위 밖으로 미리 더 렌더하는 행 수. 빠른 스크롤에서 빈 틈이 보이지 않게 한다.

2. 셀렉터 없는 `subscribe`는 **변경 범위와 무관하게 state 참조를 바꾸는 모든 set**에 호출된다. 150ms마다 갱신이 오고 그때마다 N개 세션을 전수 비교하므로, 갱신 하나가 세션 하나를 바꿔도 비용은 N이다 — 갱신 수도 세션 수에 비례해 늘면(세션마다 갱신이 오면) 합계는 O(N²)에 가까워진다.\
변경을 만드는 스토어 액션은 **어느 세션의 무엇이 바뀌었는지** 이미 안다. 그 자리에서 이전·이후 신호를 이벤트로 직접 통지하면 변경 하나당 한 번만 일한다 — O(1). 콜백 예외는 격리해 한 구독자의 오류가 액션을 깨지 않게 한다.

3. (이 사례의 zustand 류 스토어에서) `set`은 반환값이 현재 state와 `Object.is`로 같지 않으면 현재 state에 **얕게 merge해 새 루트 객체**를 만들고 리스너를 호출한다. `{}`를 반환하면 `Object.is(state, {})`가 거짓이라 내용이 같은 **새 루트 참조**가 생기고 전 리스너가 깨어난다(셀렉터로 구독한 컴포넌트는 선택 결과가 같으면 리렌더를 건너뛰지만, 모든 셀렉터·리스너가 한 번씩은 다시 돈다).\
변화 없음은 `state` 자신을 반환해야 한다. 삭제 0건인 정리 함수가 새 객체를 돌려주면 그 객체를 보는 파생값(세대 번호 등)이 매번 증가해 **파생 이벤트가 폭주**한다 — 0건이면 기존 객체를 그대로 돌려준다.
   > **참조 동등성(referential equality)** — 두 값이 같은 객체인지(`Object.is`)로 변경을 판단하는 방식. 내용 비교보다 싸지만 "같은 내용 = 같은 참조"를 지켜야 의미가 있다.

4. 노드마다 O(E) 탐색 × N개 노드 = **O(N·E)** 가 스토어 갱신마다 반복된다.\
`expanded` 배열의 **정체성(identity)을 키로** 메모한 Set을 쓰면 판정은 O(1)이고 Set은 배열이 바뀔 때만 다시 만든다.\
안전 계약: **배열을 제자리 변경(push)하지 않는다** — 제자리 변경은 identity가 같아 메모가 옛 Set을 돌려준다. 토글은 항상 새 배열을 만든다. 표면(인스턴스)마다 메모를 분리해 서로 캐시를 밀어내지 않게 한다. `memo.has(p) ≡ 기존 includes(p)`를 특성 테스트로 고정한다.

5. 누수가 없어도 **매 주기 반복되는 일의 양**이 데이터 크기 × 빈도로 커지기 때문이다 — 분석 추정으로 활발한 세션 3개에 초당 200MB급 할당 churn이었다.\
결과가 불변인 계산(한 번 정해지는 부모 연결, 끝난 하위 작업의 결과)은 한 번 계산해 캐시하고, 저장은 debounce, 바이트 단위 반복 제거는 한 번에 drain, 렌더마다 도는 필터·정렬은 메모로 공유한다.\
동작 보존은 **특성 테스트 baseline을 먼저** 만들어 고정한 뒤 바꾼다. 이 과정에서 리뷰가 보존 위반을 여러 차례 적발했다 — 캐시는 "완전 동치"가 증명될 때만 넣는다.

6. mousemove는 초당 수십~수백 번 오고, 그때마다 전체를 렌더하면 비용이 이벤트 빈도 × 트리 크기다.\
rAF로 묶으면 **프레임당 한 번**만 반영하고, 스토어 커밋은 mouseup에서 한 번만 한다. 교환: 드래그 중에는 스토어 값이 최종값이 아니다 — 드래그 중 다른 구독자가 중간값을 봐야 하는 경우엔 맞지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 전 행 렌더 → 고정 높이 가상화
① 문제 코드
```tsx
return <div className="diff">{lines.map((l, i) => <Row key={i} line={l} />)}</div>;   // 비용 ∝ 행 수
```
② 고친 코드
```tsx
const ROW_H = 18, OVERSCAN = 24;
const end = Math.min(lines.length, Math.ceil((scrollTop + viewH) / ROW_H) + OVERSCAN);
const start = Math.max(0, Math.min(Math.floor(scrollTop / ROW_H) - OVERSCAN, end));
return (
  <div className="diff" onScroll={onScroll} style={{ padding: 0 }}>
    <div style={{ height: lines.length * ROW_H, position: "relative" }}>
      <div style={{ position: "absolute", top: start * ROW_H }}>
        {lines.slice(start, end).map((l, i) => <Row key={start + i} line={l} />)}
      </div>
    </div>
  </div>
);
```
무엇이 깨졌나: 렌더 비용이 보이는 양이 아니라 전체 데이터 크기에 비례했다(성능 예방 개선).

### 변형 B — 셀렉터 없는 전체 구독으로 변화 감지
① 문제 코드
```ts
store.subscribe((s, prev) => {
  for (const id of Object.keys(s.sessions))          // 모든 set 마다 전 세션 비교
    if (needsReview(s.sessions[id]) && !needsReview(prev.sessions[id])) notify(id);
});
```
② 고친 코드
```ts
// 변경을 만드는 액션이 변경분만 직접 통지
updateSession(id, next) {
  const prev = get().sessions[id];
  set(/* ... */);
  emitAttention({ id, prev: needsReview(prev), next: needsReview(next) });   // O(1)
}
function emitAttention(ev) { for (const cb of listeners) { try { cb(ev); } catch (e) { report(e); } } }
```
무엇이 깨졌나: 변경 범위를 아는 쪽이 아니라 모르는 쪽이 매번 전체를 비교했다.

### 변형 C — 변화가 없는데 새 참조를 반환
① 문제 코드
```ts
set((s) => (shouldChange(s) ? { items: next } : {}));   // {} → merge 로 새 루트 → 전 리스너 wake
function cap(map, keep) {
  const out = { ...map };                                // 삭제 0건이어도 새 객체 → 파생 세대 폭주
  for (const k of overflow(map, keep)) delete out[k];
  return out;
}
```
② 고친 코드
```ts
set((s) => (shouldChange(s) ? { items: next } : s));    // 변화 없으면 state 자신
function cap(map, keep) {
  const drop = overflow(map, keep);
  if (drop.length === 0) return map;                     // identity 보존
  const out = { ...map }; drop.forEach((k) => delete out[k]); return out;
}
```
무엇이 깨졌나: 변경 감지가 참조 동등성인데 "내용이 같으면 참조도 같다"를 지키지 않았다.\
같은 구조: 폴링 결과 트리의 identity를 보존해 폴링마다 전체 리렌더를 억제.

### 변형 D — 렌더마다 선형 탐색
① 문제 코드
```ts
const isOpen = (s, path) => s.expanded.includes(path);   // 노드당 O(E) × N × 모든 set
```
② 고친 코드
```ts
// 계약: expanded 배열은 제자리 변경 금지 — 토글은 항상 새 배열
const memo = new Map<string, { arr: string[]; set: Set<string> }>();   // 표면별
function expandedSetOf(s, surface) {
  const m = memo.get(surface);
  if (m && m.arr === s.expanded[surface]) return m.set;
  const set = new Set(s.expanded[surface]); memo.set(surface, { arr: s.expanded[surface], set }); return set;
}
// 특성 테스트: expandedSetOf(s, x).has(p) === s.expanded[x].includes(p)
```
무엇이 깨졌나: 입력이 바뀌지 않았는데 매 렌더 같은 탐색을 반복했다.

### 변형 E — 핫패스에서 불변 결과 재계산·전량 복제
① 문제 코드
```ts
setInterval(() => {
  const snap = deepClone(timeline);                 // 틱마다 전체 복제·직렬화·디스크 재작성
  save(serialize(snap));
  for (const a of agents) a.parent = findParentByScan(a, calls);   // 결과 불변인데 매 틱 O(A×C)
}, 150);
while (buf.length > max) buf.shift();               // 1개씩 제거 반복
```
② 고친 코드
```ts
setInterval(() => {
  for (const a of agents) a.parent ??= parentCache.get(a.id) ?? cacheParent(a, calls);   // 한 번만 (부모가 확정됐을 때만 캐시 — 미확정이면 다음 틱 재시도)
  scheduleSave();                                   // debounce + 메타 사이드카
}, 150);
buf.splice(0, Math.max(0, buf.length - max));       // drain 1회
// 모든 변경 전: 특성 테스트 baseline 으로 동작 보존 고정
```
무엇이 깨졌나: 변하지 않는 결과를 주기마다 다시 계산하고 전체를 복제해, 누수 없이도 CPU·할당이 크기 × 빈도로 늘었다.\
같은 구조: 끝난 하위 작업의 tail을 영구 보관 → 드롭 + 결과 캐시. 세션마다 주기적으로 외부 프로세스를 띄워 같은 값을 조회 → 세션 캐시.\
같은 구조: 렌더마다 그룹별 filter+sort 2회 → 인덱스를 메모로 공유. 선택 항목을 배열 탐색 → Map. 목록 렌더를 최근 N개로 제한.\
같은 구조: 스플리터 mousemove마다 전체 재렌더 → rAF로 묶고 mouseup에서 커밋.

## 검증 기록

- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
