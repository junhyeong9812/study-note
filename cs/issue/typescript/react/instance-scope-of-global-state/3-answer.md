# cs/issue/typescript/react/instance-scope-of-global-state — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. 문서 id는 문서 전체에서 유일하다고 가정된다. 두 트리가 같은 id를 가지면 `getElementById`는 **첫 번째 것만** 돌려주고, 두 번째 트리의 포커스·스크롤 조작은 첫 트리로 간다.\
모듈 스코프 캐시·전역 버스 구독도 같은 부류다 — 모두 "이 자원은 나 하나만 쓴다"는 가정을 **코드 밖(문서·모듈·전역)** 에 두었다. 인스턴스가 둘이 되면 같은 자원을 두 번 등록하거나, 한쪽의 기록을 다른 쪽이 읽는다.

2. 두 번째 인스턴스의 요청 프로젝트는 전역 활성 프로젝트와 다르므로, 가드는 **자기 응답을 전부 "늦은 응답"으로 판정해 버린다** — 보조 화면은 영원히 비어 있다.\
인스턴스 스코프 가드는 "이 응답을 요청한 시점의 프로젝트"와 "**이 인스턴스가 지금** 보여주는 프로젝트(인스턴스 ref)"를 비교해야 한다.
   > **stale-guard** — 비동기 응답이 도착했을 때 그 응답이 아직 유효한 요청의 것인지 확인해, 늦은 응답을 버리는 검사.

3. 보조 트리의 인터벌이 **주 트리(전역 활성 프로젝트)** 를 리로드한다 — 자기 트리는 갱신되지 않고, 주 트리는 불필요한 리로드를 두 배로 받는다.\
펼침 상태를 전역 활성 키 아래에 기록하면 보조 트리의 펼침이 **주 트리의 저장된 트리 상태를 오염**시킨다. 리로드·in-flight 집합·세대·펼침 상태를 모두 **프로젝트 키별**로 두고, 주기 작업은 활성 표면만 돌린다(활성화 즉시 따라잡기).

4. 갱신되지 않는다. persist는 **디스크(localStorage)** 에 쓰는 것이고, 다른 창은 자기 런타임의 스토어 인스턴스를 메모리에 들고 있어 그 쓰기를 모른다.\
소비자(해당 뷰)가 없는 창에서 발행한 요청은 **영원히 처리되지 않고 남는다** — 모드는 영속적으로 바뀌었는데 그에 따른 전환은 일어나지 않는다.\
"이 상태의 writer는 메인 창 하나"라는 불변식을 두면 여러 창이 같은 키를 덮어쓰는 last-writer-wins 경쟁이 **구조적으로 도달 불가**가 된다. 불변식이 깨지면 그때 창 간 동기화를 설계한다.

5. 매핑이 **원래 창의 런타임에만** 있으므로, 옮겨진 뷰는 라이브 이벤트·종료 이벤트를 받지 못하고, 원래 창은 탭이 옮겨졌을 뿐인데 "닫힘"으로 오탐한다.\
비동기 등록이 끝나기 전의 조회는 "아직 없음"이다. 이를 "죽음"으로 읽으면 **살아 있는 세션을 종료된 것으로 표시**한다. 해법은 다른 창으로의 이동을 차단(그 자리에서 닫기)하고, 원본이 사라지면 딸린 뷰도 닫고, 마운트 시점의 생존 조회를 없애는 것이다.

6. ES 모듈은 **프로세스당 한 번** 평가되고 그 결과(export된 객체)는 싱글턴으로 공유된다. 서버 프로세스는 여러 사용자의 요청을 처리하므로, 한 요청이 그 객체를 제자리 변형하면 **이후 모든 요청이** 그 변형을 본다.\
`structuredClone`은 요청마다 **독립된 깊은 사본**을 만들어, 한 요청의 변형이 공유 원본에 닿지 않게 한다.
   > **모듈 싱글턴** — 모듈 최상위에서 만든 값은 import하는 모든 곳이 같은 인스턴스를 공유한다는 성질.

7. 구조적 금지(같은 탭은 한쪽만 — 반대쪽을 고르면 자동 스왑, 다른 창으로의 이동 차단)는 **"둘"이 되는 상황 자체를 없애** 모든 전역 지점을 고칠 필요를 없앤다 — 대신 사용자가 할 수 있는 조합이 줄어든다.\
인스턴스 스코프화는 기능 제약이 없지만 **모든 전역 지점을 전수 조사**해야 하고(한 조사에서 위험 17건), 하나라도 놓치면 누출이 남는다. 복원(persist)된 상태도 같은 규칙을 통과해야 금지가 우회되지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 문서 id·전역 가드·전역 리로드·전역 키
① 문제 코드
```tsx
<ul id="tree">...</ul>                                         // 두 인스턴스가 같은 id
document.getElementById("tree")?.focus();                     // 첫 것만

const res = await loadGraph(project);
if (store.getState().activeProject !== project) return;       // 보조 인스턴스는 자기 응답 전량 거절

setInterval(() => reloadActiveTree(), 4000);                  // 전역 활성 트리를 리로드
toggleExpanded(path) { expanded[s.activeProject].toggle(path); }   // 보조의 펼침이 주 트리에 기록
```
② 고친 코드
```tsx
<ul id={treeId}>...</ul>                                      // 인스턴스별 id
document.getElementById(treeId)?.focus();

const res = await loadGraph(project);
if (projectRef.current !== project) return;                   // 인스턴스 ref 비교

if (surfaceId === activeSurfaceId) setInterval(() => reloadTreeFor(project), 4000);   // 프로젝트 스코프 · 활성 표면만
toggleExpandedFor(project, path);                             // in-flight Set · 세대 Map · 메모도 프로젝트별
```
무엇이 깨졌나: "전역 = 내 것"이라는 암묵 동치가 두 번째 인스턴스에서 서로의 상태를 읽고 쓰는 누출로 바뀌었다.

### 변형 B — 전역 요청 버스·창 리스너를 두 인스턴스가 소비
① 문제 코드
```tsx
function Workspace() {
  useEffect(() => requestBus.on("open-file", openFile), []);   // 표면이 둘이면 요청 하나를 두 번 처리
  useEffect(() => onWindowClose(saveLayout), []);
}
```
② 고친 코드
```tsx
function Workspace({ secondary }) {
  const isPrimary = !secondary;
  useEffect(() => (isPrimary ? requestBus.on("open-file", openFile) : undefined), [isPrimary]);
  // 세션 dedupe·닫기 요청 소유는 표면 레지스트리가 결정
}
// 사이드바: 같은 탭 양쪽 금지를 순수 함수로 (persist 복원도 이 함수를 통과)
function pickTab(state, side, tab) {
  const theirs = side === "top" ? state.bottomTab : state.topTab;
  if (theirs === tab) return { ...state, topTab: state.bottomTab, bottomTab: state.topTab };   // 자동 스왑
  return { ...state, [side === "top" ? "topTab" : "bottomTab"]: tab };
}
```
무엇이 깨졌나: "창당 하나"를 전제로 전역 지점을 소비하던 컴포넌트가 둘로 마운트됐다.

### 변형 C — 창별 런타임: persist는 다른 창 메모리에 전파되지 않음
① 문제 코드
```ts
function confirmReview() {
  store.setMode(project, "normal");       // persist → 디스크만 바뀜
  store.requestDevReview(project);        // 이 창엔 소비자(뷰) 없음 → 영원히 잔류
}
```
② 고친 코드
```ts
function confirmReview() {
  if (currentWindowLabel() !== "main") { save(); notice("메인 창에서 전환하세요"); return; }
  store.setMode(project, "normal");       // 불변식: 이 키의 writer = 메인 창 단독
  store.requestDevReview(project);
}
```
무엇이 깨졌나: 창마다 스토어 인스턴스가 따로인데, 영속화가 곧 공유라고 가정했다.

### 변형 D — 창 로컬 레지스트리와 등록 전 조회
① 문제 코드
```ts
moveToWindow(peekView, otherWindow);     // id↔세션 매핑은 원래 창에만 → 라이브·종료 이벤트 유실
onMount(async () => {
  const live = await listLiveSessions(); // 등록 전이면 빈 목록
  if (!live.includes(uuid)) markClosed(uuid);   // "없음" = "죽음" 오판
});
```
② 고친 코드
```ts
if (isPeek(view)) { closeInPlace(view); return; }   // 창 이동 차단 (진입점에서 선판정)
onSourceTabRemoved(() => closePeek());               // 원본이 사라지면 딸린 뷰도 닫기
// 마운트 시 생존 조회 제거 — 종료는 종료 이벤트로만 판단
```
무엇이 깨졌나: 창(런타임) 로컬 자료구조를 창을 건너 쓸 수 있다고 가정했고, 비동기 등록 전의 부재를 사실로 읽었다.

## 검증 기록

- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~D)은 "상태·식별자를 인스턴스 스코프로 내리거나, 둘이 되는 상황을 구조적으로 막는다"이다.\
같은 원리(모듈 싱글턴이 여러 소비자에게 공유됨)에 다른 방안이 쓰인 사례:

### 방안 1 — 서버 렌더의 모듈 싱글턴은 변형 전 복제
```ts
import fallbackData from "./fallback.json";      // 프로세스당 한 번 평가 → 모든 요청이 공유

// 문제
export function getPageData() {
  applyMockOverlay(fallbackData);                 // 제자리 변형 → 이후 모든 요청이 이 변형을 봄
  return fallbackData;
}
// 고친
export function getPageData() {
  const data = structuredClone(fallbackData);     // 요청마다 독립 사본
  applyMockOverlay(data);
  return data;
}
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 인스턴스 스코프화 / 구조적 금지 | 인스턴스가 상태를 소유할 수 있다 | 전역 지점 전수 조사 · 또는 기능 제약 | 한 지점이라도 놓치면 누출 | 같은 컴포넌트를 여러 번 띄우는 클라이언트 UI |
| 1. 공유 원본을 복제해 사용 | 원본은 읽기 전용 템플릿이다 | 요청마다 복제 비용 | 복제를 우회한 변형 경로가 생기면 다시 오염 | 서버 렌더의 정적 데이터·기본값 |

**결론**: 상태를 **인스턴스가 소유해야 하는** 경우(UI 인스턴스·창)는 키·가드·구독을 인스턴스 스코프로 내리고, 전수 조사가 어렵거나 "둘"이 의미 없으면 구조적으로 금지한다.\
공유 객체가 **읽기 전용 원본**이어야 하는 경우(서버 모듈의 기본 데이터)는 스코프를 나눌 대상이 요청이므로, 변형 전에 복제하는 쪽이 가장 작고 확실하다.
