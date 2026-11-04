# issue/typescript/react/instance-scope-of-global-state — 정답

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

4. (별도 동기화가 없으면) 갱신되지 않는다. persist는 **저장소(localStorage)** 에 쓰는 것이고, 다른 창은 자기 런타임의 스토어 인스턴스를 메모리에 들고 있다 — 같은 출처의 다른 창이 `storage` 이벤트를 받아 재수화(rehydrate)하도록 따로 구현하지 않는 한 그 쓰기를 메모리에 반영하지 않는다.\
소비자(해당 뷰)가 없는 창에서 발행한 요청은 **영원히 처리되지 않고 남는다** — 모드는 영속적으로 바뀌었는데 그에 따른 전환은 일어나지 않는다.\
"이 상태의 writer는 메인 창 하나"라는 불변식을 두면 여러 창이 같은 키를 덮어쓰는 last-writer-wins 경쟁이 **구조적으로 도달 불가**가 된다. 불변식이 깨지면 그때 창 간 동기화를 설계한다.

5. 매핑이 **원래 창의 런타임에만** 있으므로, 옮겨진 뷰는 라이브 이벤트·종료 이벤트를 받지 못하고, 원래 창은 탭이 옮겨졌을 뿐인데 "닫힘"으로 오탐한다.\
비동기 등록이 끝나기 전의 조회는 "아직 없음"이다. 이를 "죽음"으로 읽으면 **살아 있는 세션을 종료된 것으로 표시**한다. 해법은 다른 창으로의 이동을 차단(그 자리에서 닫기)하고, 원본이 사라지면 딸린 뷰도 닫고, 마운트 시점의 생존 조회를 없애는 것이다.

6. ES 모듈은 **같은 모듈 그래프(보통 한 서버 프로세스) 안에서 한 번** 평가되고 그 결과(export된 객체)는 싱글턴으로 공유된다. 서버 프로세스는 여러 사용자의 요청을 처리하므로, 한 요청이 그 객체를 제자리 변형하면 **그 프로세스가 처리하는 이후 요청들이** 그 변형을 본다(프로세스·워커·번들이 여럿이면 인스턴스별로 따로 오염되어 증상이 간헐적으로 보인다).\
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

if (surfaceId === activeSurfaceId) setInterval(() => reloadTreeFor(project), 4000);   // 프로젝트 스코프 · 활성 표면만 (effect 안에서 등록, 비활성·언마운트 시 clearInterval)
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

- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~D)은 "상태·식별자를 인스턴스 스코프로 내리거나, 둘이 되는 상황을 구조적으로 막는다"이다.\
같은 원리(모듈 싱글턴이 여러 소비자에게 공유됨)에 다른 방안이 쓰인 사례:

### 방안 1 — 서버 렌더의 모듈 싱글턴은 변형 전 복제
```ts
import fallbackData from "./fallback.json";      // 모듈 그래프당 한 번 평가 → 같은 프로세스의 모든 요청이 공유

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
공유 객체가 **읽기 전용 원본**이어야 하는 경우(서버 모듈의 기본 데이터)는 스코프를 나눌 대상이 요청이므로, 변형 전에 복제하는 쪽이 작고 확실한 편이다(복제 비용이 크면 원본을 동결해 변형 경로를 드러내고 변형 없는 조립으로 바꾸는 방법도 있다).

## 방안 비교 — 물리적으로 하나뿐인 전역은 인스턴스 스코프로 내릴 수 없다

기본 방안은 "상태를 인스턴스 스코프로 내리거나, primary 하나만 소비하게 한다"이다.\
그런데 **문서의 키 입력**이나 **body의 스타일 값**처럼 자원 자체가 문서에 하나뿐이면 내릴 곳이 없다.\
같은 "전역 = 내 것" 가정(각 인스턴스가 "이 전역은 나 하나만 쓴다"고 행동)에서 대화상자를 겹쳐 열었을 때 두 결함이 나왔다:\
① ESC 한 번에 겹친 대화상자가 **전부** 닫힘 ② 위 대화상자만 닫았는데 **배경 스크롤 잠금이 풀림**.

### 방안 2 — 인스턴스별 전역 리스너 대신 공유 리스너 1개 + 스택(맨 위만 처리)
① 문제 코드
```js
function openDialog() {
  const dialog = createDialog();
  const handleKey = (e) => {                                  // 인스턴스마다 새 클로저 — 자기 대화상자만 안다
    if (e.key === 'Escape') dialog.close('escape');       // "내가 맨 위인가?" 확인 없음
  };
  document.addEventListener('keydown', handleKey, true);
  dialog.onCleanup(() => document.removeEventListener('keydown', handleKey, true));
  return dialog;
}
```
```
document keydown 리스너: [handleKey#1, handleKey#2]   — 같은 노드의 리스너는 등록 순서대로 하나씩 실행

(가) #2가 #1 안에서 열림(논리 자식)          (나) #1, #2가 형제
  handleKey#1 → #1 close                          handleKey#1 → #1 close
    └ 부모 정리가 자식부터 → #2도 정리          handleKey#2 → #2 close
      (#2의 리스너도 이때 해제)                 → 전부 닫힘
  handleKey#2 → 이미 해제 → 호출 안 됨
  → 맨 위가 아닌 #1이 반응해 자식까지 휩쓺
원인은 하나: 맨 위 확인 없음 (캡처·버블과 무관)
```
② 고친 코드
```js
const layers = [];                                         // 모듈에 하나
const top = () => layers[layers.length - 1];

function handleKey(e) {                                       // 리스너도 하나
  const dialog = top();
  if (!dialog) return;
  if (e.key === 'Escape') { e.preventDefault(); dialog.close('escape'); }   // 맨 위 하나만
  else if (e.key === 'Tab') trapFocus(e, dialog);         // 가장자리에서만 preventDefault + 반대쪽 끝으로
}

function openDialog() {
  const dialog = createDialog();
  layers.push(dialog);
  if (layers.length === 1) document.addEventListener('keydown', handleKey, true);    // 0 → 1
  dialog.onCleanup(() => {
    layers.splice(layers.indexOf(dialog), 1);
    if (layers.length === 0) document.removeEventListener('keydown', handleKey, true); // 1 → 0
  });
  return dialog;
}
```
무엇이 깨졌나: 각 리스너가 자기 인스턴스만 알아 "누가 맨 위인가"라는 **전체에 대한 사실**을 판정할 곳이 없었다.\
같은 자리의 Tab 가두기: 포커스 이동은 브라우저 기본(DOM 순서)에 맡기고, **마지막에서 Tab·처음에서 Shift+Tab일 때만** 기본 이동을 취소하고 반대쪽 끝으로 보낸다 — `preventDefault`가 없으면 우리가 옮긴 직후 브라우저가 원래 이동을 마저 해 한 칸 더 간다.\
테스트: 두 개를 열고 ESC 한 번에 1개 남고, 두 번째에 0개.

### 방안 3 — 공유 자원 참조 카운트: 0↔1 경계에서만 실제로 바꾸고, 원래 값은 한 번만 저장
① 문제 코드
```js
// 열 때                                  // 닫을 때
body.style.overflow = 'hidden';           body.style.overflow = '';      // 무조건 해제 + 원래 값 대신 빈 값
```
```
#1 열기  'hidden' 🔒
#2 열기  'hidden' 🔒
#2 닫기  ''       🔓  ← #1이 아직 열려 있는데 풀림 ✗
#1 닫기  ''       🔓  ← 페이지가 원래 갖던 인라인 값도 지워짐 ✗
```
② 고친 코드
```js
let holders = 0;
let saved = '';

function acquireLock() {
  if (holders++ === 0) {                  // 증가 전 0 = 내가 첫 번째 → 실제 잠금
    saved = body.style.overflow;          //   원래 값은 이때 한 번만 기억
    body.style.overflow = 'hidden';
  }
}
function releaseLock() {
  if (--holders === 0) body.style.overflow = saved;   // 감소 후 0 = 내가 마지막 → 원래 값으로
}

function openDialog() {
  const dialog = createDialog();
  acquireLock();
  dialog.onCleanup(releaseLock);          // close() 안이 아니라 정리 경로에 — 부모 파괴로 연쇄 정리돼도 감소
  return dialog;                          // close()는 closed 플래그로 1회만 정리 → 이중 감소 없음
}
```
```
#1 열기  holders 0→1  'hidden' (원래 값 기억)  🔒
#2 열기  holders 1→2  (변경 없음)              🔒
#2 닫기  holders 2→1  (변경 없음)              🔒 ✓
#1 닫기  holders 1→0  원래 값 복원             🔓 ✓
```
무엇이 깨졌나: 각 인스턴스가 "내가 잠갔으니 내가 푼다"고만 생각했다 — 잠금이 아직 필요한 다른 보유자를 몰랐고, 해제 값도 자기가 본 적 없는 원래 상태를 덮었다.\
테스트: 원래 인라인 값 `scroll` → 둘 열고 위를 닫아도 `hidden` 유지 → 마지막을 닫으면 `scroll` 복원. 카운트를 빼면 실패(변이 점검).\
해제를 정리 경로에 두는 이유는 [cleanup-on-every-exit-path](../../../cross-cutting/reliability/cleanup-on-every-exit-path/)와 같다 — 종료 경로(직접 닫기·부모 파괴)가 여럿이다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 인스턴스 스코프화 / primary만 소비 | 상태를 인스턴스별로 나눌 수 있다 | 전역 지점 전수 조사 | 한 지점이라도 놓치면 누출 | 인스턴스가 각자 상태를 가질 수 있는 UI |
| 2. 공유 리스너 1개 + 스택 | 이벤트는 하나지만 처리할 대상은 "맨 위" 하나다 | 모듈 스택 관리 · 스택 정리를 모든 종료 경로에 | 스택에서 빠지지 않은 인스턴스가 남으면 맨 위 판정이 틀림 | 문서 단위 키 입력·바깥 클릭을 겹친 레이어가 나눠 쓸 때 |
| 3. 참조 카운트 (0↔1 경계 + 원래 값 1회 저장) | 자원은 하나고 "누군가 필요로 하는 동안" 켜져 있어야 한다 | 카운터 + 저장값 | 해제 누락 → 영구 잠금 · 이중 해제 → 음수·조기 해제 | body 스타일·전역 리스너 부착·로딩 표시처럼 켜고 끄는 공유 자원 |

**결론**: 상태를 **나눌 수 있으면** 인스턴스 스코프로 내린다(기본).\
자원이 **물리적으로 하나**면 나눌 수 없으므로, 인스턴스가 전역을 직접 만지지 않게 하고 **한 곳이 전체를 보고 결정**하게 한다 — "누가 처리하나"가 문제면 스택(2), "언제 켜고 끄나"가 문제면 참조 카운트(3).\
두 방안 모두 정확성은 **해제가 모든 종료 경로에서 정확히 한 번** 일어나는 데 달려 있다 — 획득 옆에서 정리를 예약하고, 닫기는 멱등으로 둔다.

- 2026-11-04: 사건 기록 대조·추상화(Claude 초안)
