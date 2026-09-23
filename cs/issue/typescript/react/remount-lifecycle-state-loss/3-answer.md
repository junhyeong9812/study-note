# cs/issue/typescript/react/remount-lifecycle-state-loss — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. 보이는 탭만 마운트하는 렌더러에서 탭 전환은 **리마운트**다. 무거운 패널은 마운트 후 위젯(터미널 등)을 만드는 데 한 프레임보다 오래 걸려, 1 rAF 뒤 조회하면 대상이 아직 없다(null) — 포커스가 조용히 실패한다.\
프레임 수를 늘리는 것은 "이 정도면 생성됐겠지"라는 추측이라, 더 무거운 패널이나 느린 기기에서 또 경합한다. 또 레이아웃 API의 `focus()`는 **그룹**만 포커스하고 그 안의 콘텐츠는 포커스하지 않아 첫 시도도 실패했다 — 그 뒤 "1 프레임 뒤 직접 포커스"도 무거운 패널에서 실패해, 두 차례 시도 끝에 책임 위치를 바꿔 끝났다.
   > **리마운트(remount)** — 컴포넌트가 언마운트된 뒤 새 인스턴스로 다시 마운트되는 것. state·ref·effect 구독이 모두 새로 시작된다.

2. 위젯이 언제 생기는지 **정확히 아는 쪽은 위젯을 만든 패널 자신**이다. 패널이 위젯 생성 직후(마운트 effect 안에서) 스스로 포커스하면, 기다릴 시간 자체가 없어진다 — "언제 찾을까"가 "누가 할까"로 바뀐다.\
리마운트 없이 활성만 바뀌는 경우는 마운트 effect가 다시 돌지 않으므로, 레이아웃의 **활성 변경 이벤트**(`onDidActiveChange`)를 구독해 활성이 될 때 포커스한다. 이미 마운트된 패널로의 단축키 이동만 바깥에서 처리하되, 짧은 재시도(≤10회) + 가시성 가드(`offsetParent !== null`)를 둔다.

3. 컴포넌트 state는 탭을 떠날 때마다 **소실**된다 — 돌아오면 늘 기본 영역으로 포커스된다.\
모듈 Map으로 옮기면 살아남지만, 닫힌 패널의 항목을 지우지 않으면 ① Map이 **무한히 커지고** ② 패널 id가 재사용될 때 **다른 패널에 옛 영역이 복원**된다.\
삭제는 탭 전환(가시성)이 아니라 **실제 제거 이벤트**(`onDidRemovePanel`)에서 해야 한다. 가시성 이벤트에서 지우면 원래 목적(전환 후 복원)이 사라진다.

4. 구독을 **앱 레벨(창당 하나)** 전역 리스너로 올리고, 세션 id↔패널 매핑을 스토어 레지스트리에 둔다. 마운트된 패널이 있으면 그 패널의 리스너가 정확한 값으로 처리하고, 전역 리스너는 "붙어 있는 패널 수(ref-count)"가 0일 때만 처리해 이중 갱신을 피한다.\
"컴포넌트 폐기"는 가시성 변화에도 일어나고 "패널 제거"는 수명 종료에만 일어난다. 리마운트 정리 지점에서 세션 상태를 지우면 **탭을 벗어나는 순간 배지가 사라진다** — 상태 삭제는 세션 종료 이벤트에서만, 리마운트 정리는 분리(detach)만 한다.

5. `click`은 **같은 요소**에서 `mousedown`과 `mouseup`이 모두 일어나야 발생한다. mousedown 처리 중에 전체를 재생성하면 누른 요소는 이미 문서에서 분리되어, 그 뒤의 mouseup·click은 새 노드로 전달되지 않는다.\
매 프레임 `innerHTML = ''`로 말풍선을 다시 만드는 루프도 같다 — down과 up 사이에 요소가 교체되어 클릭이 발생하지 않고, 라벨도 매 프레임 깜빡인다.\
해법: 포커스 표시는 클래스만 토글하는 경량 갱신으로. 렌더 루프는 노드를 풀링해 재사용하고, 데이터가 바뀔 때만 재구성(rebuild)하며 매 프레임에는 위치만 갱신(reposition)한다.

6. **분리**한다. `innerHTML = ''`는 자식 노드를 문서 트리에서 떼어낼 뿐이라, JS가 그 노드나 위젯 인스턴스를 참조하고 있으면 살아 있고 `appendChild`로 다시 붙일 수 있다.\
그래서 인스턴스 레지스트리(`instances[tabId]`)가 위젯과 그 루트 요소를 **소유**하고, 렌더는 새 컨테이너에 그 요소를 재부착한 뒤 다음 프레임에 크기를 맞춘다. 파괴(dispose)는 탭 닫기에서만 한다 — "인스턴스 존재 ⟺ 탭 존재" 불변식.\
분리 상태에서는 폭이 0이라, 크기 맞춤이 잘못된 행·열을 계산해 레이아웃이 깨진다. `el.isConnected && clientWidth > 0`일 때만 맞추고, 파괴 후 늦게 온 rAF도 이 가드로 조기 반환한다.

## 문제 구조 (추상화 코드)

### 변형 A — 바깥에서 고정 프레임 뒤 자식 DOM을 찾음
① 문제 코드
```ts
function focusActivePanel() {
  layout.setActive(panel);                                   // 탭 전환 = 리마운트
  requestAnimationFrame(() => document.querySelector(".active .widget")?.focus());   // 무거운 패널은 아직 null
}
```
② 고친 코드
```ts
// 패널 안: 콘텐츠 소유자 self-focus
useEffect(() => { const w = createWidget(host); w.focus(); return () => w.dispose(); }, []);
useEffect(() => {
  const d = props.api.onDidActiveChange(() => { if (props.api.isActive) widgetRef.current?.focus(); });   // 리마운트 없는 활성화
  return () => d.dispose();
}, [props.api]);
```
무엇이 깨졌나: 자식 초기화 시간을 모르는 바깥 코드가 추측한 타이밍에 자식 DOM을 찾았다.

### 변형 B — 리마운트에 휘발되는 뷰 상태 → 밖으로 옮긴 뒤의 삭제 책임
① 문제 코드
```ts
const [lastArea, setLastArea] = useState("main");            // 탭 전환마다 소실
// → 모듈로 옮김
const lastArea = new Map<string, Area>();                    // 닫힌 패널 항목 영구 잔류 · id 재사용 시 오복원
```
② 고친 코드
```ts
const lastArea = new Map<string, Area>();
export const remember = (id, a) => lastArea.set(id, a);
export const recall = (id) => lastArea.get(id);
export const forget = (id) => lastArea.delete(id);
layout.onDidRemovePanel((p) => forget(p.id));                // 실제 제거에서만 (탭 전환 아님)
restoreFocus = () => focusArea(recall(props.api.id) ?? "main");   // 안전 폴백
```
무엇이 깨졌나: 컴포넌트보다 오래 사는 상태를 밖으로 옮기면서 삭제 책임도 함께 넘어왔는데 그 책임을 지지 않았다.

### 변형 C — 백그라운드 탭 = 컴포넌트 부재 → 세션 구독 소실
① 문제 코드
```tsx
function SessionPanel({ sessionId }) {
  useEffect(() => subscribe(sessionId, updateBadge), [sessionId]);   // 탭이 뒤로 가면 구독 사라짐
  useEffect(() => () => removeSessionState(sessionId), []);          // 탭 이탈 = 배지 소실
}
```
② 고친 코드
```tsx
// 앱 레벨 (창당 1개)
useEffect(() => subscribeAll((ev) => {
  if (registry.attachedCount(ev.sessionId) > 0) return;   // 마운트된 패널이 처리
  updateBadge(ev);
}), []);
function SessionPanel({ sessionId }) {
  useEffect(() => { registry.attach(sessionId); return () => registry.detach(sessionId); }, [sessionId]);
}
onSessionClosed((id) => removeSessionState(id));          // 상태 삭제는 세션 종료에서만
```
무엇이 깨졌나: 세션 수명의 구독·상태를 가시성 수명의 컴포넌트에 두었다.

### 변형 D — 이벤트 도중 또는 매 프레임 DOM 재생성
① 문제 코드
```js
pane.addEventListener("mousedown", () => { state.active = pane.id; renderPanes(); });   // 같은 클릭의 click 소실
function loop() {
  if (frame % 5 === 0) container.innerHTML = "";          // down·up 사이 요소 교체 → click 없음 · 깜빡임
  labels.forEach((l) => container.appendChild(makeLabel(l)));
}
```
② 고친 코드
```js
pane.addEventListener("mousedown", () => {
  state.active = pane.id;
  panes.forEach((p) => p.el.classList.toggle("focused", p.id === state.active));   // 경량 갱신
}, true);
function rebuild() { /* 데이터 변경 시에만: 풀에서 노드 재사용, 남는 노드는 숨김 */ }
function loop() { reposition(); }                          // 매 프레임은 위치만
```
무엇이 깨졌나: 이벤트 대상이 되는 노드를 이벤트 한 쌍(down·up) 사이에 교체했다.

### 변형 E — 전면 재렌더 뷰 위의 영속 위젯
① 문제 코드
```js
function render() {
  body.innerHTML = "";
  if (isWidgetTab(active)) openNewWidget(body);            // 렌더마다 위젯·연결·스크롤백 파괴 후 재생성
}
```
② 고친 코드
```js
const instances = {};                                      // 인스턴스 존재 ⟺ 탭 존재
function render() {
  body.innerHTML = "";                                     // 분리만 — 파괴 아님
  const inst = instances[active];
  if (inst) { body.appendChild(inst.el); requestAnimationFrame(() => inst.refit()); }
}
inst.refit = () => { if (!inst.el.isConnected || inst.el.clientWidth === 0) return; fit(); };   // 붙은 뒤에만
function closeTab(id) { instances[id]?.dispose(); delete instances[id]; }   // 이동·분할은 재배치일 뿐
```
무엇이 깨졌나: 렌더가 DOM을 버릴 때 위젯의 수명까지 함께 버렸다(이 변형은 설계 단계에서 식별된 함정).

## 검증 기록

- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
