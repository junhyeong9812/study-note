# cs/issue/typescript/react/dependent-state-reset — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. 선택 상태는 **유령 참조**가 된다 — 더 이상 존재하지 않는 항목을 가리키지만 화면·로직은 여전히 "선택됨"으로 취급한다.\
그 선택을 대상 경로로 쓰기 작업(저장소 명령 등)을 하면 **존재하지 않는 경로**로 쓰기가 향한다.\
그래서 목록을 갱신하는 바로 그 지점에서 "선택이 새 목록에 아직 있는가"를 재검증해 없으면 `null`로 되돌린다. 상위 컨텍스트(프로젝트) 전환 때는 무조건 리셋한다.
   > **유령 참조(stale reference)** — 대상이 사라지거나 바뀌었는데 계속 남아 있는 식별자·포인터.

2. 빈 화면이 된다. 이전 `scrollTop`이 유지되어 파생된 `start`가 새 데이터 길이보다 커지고, `[start, end)` 창에 그릴 행이 없다.\
수정은 둘이다: 데이터가 바뀌면 `scrollTop`을 0으로 **리셋**하고, 파생 인덱스는 `start = min(start, end)`로 **clamp**한다 — 리셋은 정상 경로를, clamp는 리셋 전 한 번의 렌더를 지킨다.
   > **가상화(windowing)** — 보이는 범위의 행만 렌더하고 나머지는 높이만 차지하게 하는 기법. 창의 위치를 스크롤 위치에서 파생한다.

3. 앵커가 목록에 없으면 `findIndex`는 **-1**을 돌려주고, 이를 그대로 쓰는 내비 코드는 목록의 처음이나 끝으로 점프한다. 닫기 버튼이 선택을 지우면 복원 대상이 없어 스크롤이 맨 위로 튄다.\
해법: 닫기는 **선택을 유지**하는 다른 경로(Esc)와 같게 만든다. 항목을 접을 때는 숨겨질 선택을 **남아 보이는 조상(턴 헤더)으로 승격**하고, 접힌 그룹은 헤더를 내비 정지점으로 남긴다.\
같은 헤더에서 "선택" 클릭과 "접기" 클릭이 충돌하면 접기 버튼을 별도 히트 영역으로 분리하고 이벤트 전파를 막는다.

4. 기본값이 "데이터의 최대 키"라면, 데이터에 키를 **하나라도 추가**하는 코드는 모두 기본 선택을 바꿀 수 있는 코드가 된다 — 기본값 로직이 그 코드들과 보이지 않게 결합돼 있다.\
목 데이터가 존재하지 않던 최신 키(빈 월)를 만들면, 초기 화면이 실데이터가 없는 그 키로 바뀐다. 수정은 목 보강을 "이미 받은 키에만" 하도록 제한하는 것이다.

5. 옛 `src`의 실패 표시("이미지 없음")가 **새 `src`에도 그대로** 남는다 — 컴포넌트 인스턴스가 재사용되면 로컬 state도 재사용되기 때문이다.\
일반 원리: 입력(prop)에서 파생된 로컬 state는 입력이 바뀔 때 리셋하지 않으면 이전 값이 남는다. `src`가 바뀔 때 `failed`를 리셋한다 — effect로 리셋하면 커밋 후에야 바뀌어 한 번은 옛 표시로 렌더되므로, 정확히 하려면 `key={src}`로 리마운트하거나 렌더 중에 이전 src와 비교해 리셋한다.

6. **설계**일 수 있다. 선택된 행만 라이브로 조회하고 나머지는 스캔 당시 값을 보여주는 것은 비용과 신선도의 교환이다.\
유령 참조와 다른 점은 **쓰기 대상이 되지 않고, 어느 값이 스냅샷인지가 규칙으로 정해져 있다**는 것이다. 잘못된 것은 스냅샷 값을 라이브 값처럼 믿고 행동하는 경우다.

## 문제 구조 (추상화 코드)

### 변형 A — 목록이 바뀌어도 선택이 남음
① 문제 코드
```ts
const roots = await scanRoots(project);
setRoots(roots);                               // selectedRoot 는 그대로
// ...
await runWrite(selectedRoot ?? project, args);  // 사라진 root 로 쓰기
```
② 고친 코드
```ts
const roots = await scanRoots(project);
setRoots(roots);
setSelectedRoot((cur) => (cur && roots.some((r) => r.path === cur) ? cur : null));   // 재검증
useEffect(() => setSelectedRoot(null), [project]);                                    // 상위 전환 리셋
const target = selectedRoot ?? project;        // 출처 변수 하나 → 모든 쓰기 호출이 이것만 사용
```
무엇이 깨졌나: 선택지 목록이 바뀌었는데 그 목록에 종속된 선택을 재검증하지 않았다.\
같은 구조: 저장소를 바꾼 뒤 조회 기준 ref가 없는 브랜치를 가리킴 — 컨텍스트 전환 시 ref 리셋 + 조회 실패는 빈 목록으로(이중 안전망).

### 변형 B — 파생 인덱스가 새 데이터 범위를 벗어남
① 문제 코드
```ts
const start = Math.floor(scrollTop / ROW_H) - OVERSCAN;   // 이전 데이터의 scrollTop 그대로
const end = Math.min(lines.length, /* ... */);            // start > end → 빈 화면
```
② 고친 코드
```ts
useEffect(() => { scrollEl.scrollTop = 0; }, [text]);      // 데이터 교체 시 리셋
const start = Math.max(0, Math.min(Math.floor(scrollTop / ROW_H) - OVERSCAN, end));   // clamp
```
무엇이 깨졌나: 파생의 원천(데이터 길이)이 바뀌었는데 파생에 쓰는 다른 입력(scrollTop)은 옛 값이었다.

### 변형 C — 앵커가 지워지거나 파생 목록에서 사라짐
① 문제 코드
```ts
onCloseClick = () => setSelected(null);        // 복원 대상 소실 → 맨 위로 튐
for (const g of groups) {
  if (collapsed.has(g.id)) continue;           // 헤더까지 스킵 → 선택이 목록에서 사라짐
  g.items.forEach((it) => nav.push(it));
}
const i = nav.findIndex((e) => e === selected); // -1 → 처음/끝으로 점프
```
② 고친 코드
```ts
onCloseClick = () => { closePanel(); focusItems(); };   // Esc 경로와 동일: 선택 유지
for (const g of groups) {
  nav.push({ kind: "group", g });              // 접혀도 헤더는 정지점
  if (collapsed.has(g.id)) continue;
  g.items.forEach((it) => nav.push(it));
}
function collapse(g) { if (g.contains(selected)) setSelected(g.head); setCollapsed(/* ... */); }   // 승격
```
무엇이 깨졌나: 내비·복원이 "현재 선택"을 앵커로 쓰는데, 닫기·접기 경로가 앵커를 지우거나 숨겼다.

### 변형 D — 데이터에서 파생한 기본값이 데이터 추가 코드와 결합
① 문제 코드
```ts
const initial = max(Object.keys(dataByMonth));   // 기본 선택 = 최신 키
applyMock(dataByMonth);                          // 목이 없던 월을 새로 만듦 → 초기 화면 탈취
```
② 고친 코드
```ts
function applyMock(data) {
  for (const k of Object.keys(mock)) if (k in data) merge(data[k], mock[k]);   // 이미 받은 키에만
}
```
무엇이 깨졌나: 기본값 파생 규칙이 키 집합 전체에 의존하는데, 키를 더하는 코드가 그 사실을 몰랐다.

### 변형 E — prop에서 파생한 로컬 state가 prop 변경 후에도 남음
① 문제 코드
```tsx
function Img({ src, alt, ...rest }) {
  const [failed, setFailed] = useState(false);   // src 가 바뀌어도 true 유지
  if (!src || failed) return <span>NO IMAGE</span>;
  return <img src={src} alt={alt} onError={() => setFailed(true)} {...rest} />;   // rest 가 onError 를 덮을 수 있음
}
```
② 고친 코드
```tsx
function Img({ src, alt, ...rest }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);      // 입력이 바뀌면 파생 상태 리셋(한 번은 옛 표시 — key={src} 가 더 정확)
  if (!src || failed) return <span>NO IMAGE</span>;
  return <img {...rest} src={src} alt={alt} onError={() => setFailed(true)} />;   // 보호할 prop 은 spread 뒤
}
```
무엇이 깨졌나: 파생 state의 수명을 입력이 아니라 인스턴스에 묶어, 재사용된 인스턴스가 옛 입력의 결과를 보였다.

## 검증 기록

- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
