# cs/issue/typescript/react/tree-position-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문·코드 기준. 복습 전 읽지 말 것.

태그: `test-reliability`

## 정답
<!-- 질문 1:1 대응 -->

1. **리마운트.** React는 재조정(reconciliation) 때 **요소 타입·트리상 위치·key**가 같으면 같은 인스턴스로 보고 상태를 유지한다.\
조건부 래퍼를 넣고 빼면 위쪽 패널의 부모가 바뀌어 트리 위치가 달라지므로, React는 기존 인스턴스를 언마운트하고 새로 마운트한다.\
화면상으로는 "계속 보이던" 패널이지만 컴포넌트 상태(입력 중 텍스트)는 새 인스턴스와 함께 초기값으로 돌아갔다.
   > **재조정(reconciliation)** — 새 렌더 결과를 이전 트리와 비교해 어떤 인스턴스를 유지·교체할지 정하는 React의 비교 과정.

2. **상시 래퍼 vs 상태 승격.** 래퍼를 항상 렌더하고 자식에 고정 key를 주면, 토글 전후 위쪽 패널의 위치·key가 같아 **identity가 보존**된다.\
하지만 두 자식의 자리를 맞바꾸는 스왑은 각 컴포넌트의 트리 위치 자체가 바뀌므로 양쪽 다 리마운트된다 — 이건 구조의 귀결이다.\
위치와 무관하게 상태를 지키려면 로컬 상태를 부모나 스토어로 **승격**해야 한다(근본 해법).

3. **Context의 공급 범위.** Context 값은 **트리상 조상 프로바이더**에서만 공급된다.\
사이드바가 "논리적으로 같은 영역"이어도 메인 영역 프로바이더의 하위가 아닌 다른 가지에서 렌더되면 값을 받을 수 없다.\
프로바이더 밖 호출을 throw하게 한 것은 **설계**다 — 조용히 기본값으로 폴백하면 잘못된 값으로 동작하는 결함이 숨는다. 고친 방법은 사이드바 가지에도 프로바이더를 배선하는 것이었다.

4. **포털 이벤트 버블.** 포털은 **DOM 위치만** body로 옮긴다.\
React 합성 이벤트는 DOM이 아니라 **React 컴포넌트 트리**를 따라 전파되므로, 모달을 렌더한 패널이 React 조상인 한 모달 안의 키 이벤트는 그 패널의 `onKeyDown`까지 올라간다.
   > **합성 이벤트(synthetic event)** — React가 루트에서 네이티브 이벤트를 받아 자기 컴포넌트 트리 기준으로 다시 전파하는 이벤트 객체.

5. **transform과 구조적 해소.** CSS `transform`이 있는 조상은 `position: fixed` 자손의 **containing block**이 되어, 전체 화면 백드롭이 그 패널 안에 갇힐 수 있다. 팝아웃 창은 문서가 따로이기도 하다 — 그래서 포털을 썼다.\
구조적 해소: 열림 상태를 버튼 인스턴스가 아니라 **모듈 레벨 소유권**(창당 하나)으로 올리고, 창 루트의 레이어 컴포넌트가 모달을 렌더한다.\
그러면 모달의 React 조상에 그 패널이 없어 버블할 경로 자체가 사라진다. `stopPropagation`은 그 위의 백스톱으로만 둔다(`preventDefault`는 하지 않아 입력 동작 불변).
   > **containing block** — 요소의 위치·크기 계산 기준이 되는 상자. `fixed`는 보통 뷰포트지만 `transform` 조상이 있으면 그 조상이 된다.

6. **DOM 판정 vs React 전파.** 팝오버는 포털이라 DOM상 트리거 밖에 있으므로, `trigger.contains(t)`는 팝오버 안 클릭을 "바깥"으로 판정해 **열자마자 닫는다**.\
중첩 포털의 경우 부모 메뉴의 React `onClick`은 **호출된다**(React 트리로 버블). 반면 `closest('[data-keep-menu]')`는 DOM을 거슬러 올라가므로 body 끝에 있는 하위 팝오버에서 원래 래퍼를 **찾지 못한다**.\
그래서 첫 클릭에 부모 메뉴가 닫히고 선택이 사라졌다. 판정에 팝오버 자신(`popRef`)을 넣고, 닫기 조건을 `popRef.current?.contains(t)` 가드로 바꿔 해결했다.

7. **버그를 계약으로 고정한 테스트.** 새 테스트는 단일 포털·일반 버튼 픽스처만 보고 "항목을 누르면 메뉴는 닫힌다"를 단언했다 — 중첩 포털에서 닫히면 안 되는 경우를 모른 채, 결함을 일으키는 동작을 **정답으로** 못박은 것이다.\
그래서 전체 스위트가 green인데도 결함이 들어왔다. 고친 뒤에는 그 테스트를 지우고 중첩 포털 시나리오 테스트를 새로 썼다.\
이빨 확인 = **가드를 제거하면 그 테스트만 정확히 실패하는지** 본다. 키 이벤트 테스트도 대조군(모달 밖 키는 조상이 받는다)을 함께 둬야 "아무것도 전파되지 않아서 통과"하는 무효 테스트를 막는다.

## 문제 구조 (추상화 코드)

### 변형 A — 조건부 래퍼로 트리 위치가 바뀜 (인스턴스 동일성)
① 문제 코드
```tsx
return split
  ? <PanelGroup><Panel><Top /></Panel><Panel><Bottom /></Panel></PanelGroup>
  : <Top />;                           // 토글 시 Top의 부모·위치가 바뀜 → 리마운트 → 입력 소실
```
② 고친 코드
```tsx
<PanelGroup>                           // 상시 렌더
  <Panel id="top"><Head key="top-head" /><Body key="top-body" /></Panel>
  {split && <Panel id="bottom">...</Panel>}
</PanelGroup>
// 두 자리를 맞바꾸는 스왑은 여전히 양쪽 리마운트 → 근본 해법은 상태 승격
```
무엇이 깨졌나: 화면 연속성과 트리 위치 연속성을 같은 것으로 가정했다.

### 변형 B — 프로바이더 밖 가지에서 Context 사용
① 문제 코드
```tsx
<Layout>
  <Panel id="main"><ScopeProvider id="primary">{mainArea}</ScopeProvider></Panel>
  <Panel id="sidebar">{sidebar /* 여기서 useScope() → throw */}</Panel>
</Layout>
```
② 고친 코드
```tsx
<Panel id="sidebar">
  <ScopeProvider id="primary" project={activeProject}>{sidebar}</ScopeProvider>
</Panel>

function useScope() {
  const v = useContext(ScopeCtx);
  if (!v) throw new Error("useScope outside ScopeProvider");   // 무음 폴백 대신 즉시 노출
  return v;
}
```
무엇이 깨졌나: "모든 대상이 프로바이더 안에서 렌더된다"는 가정이 트리의 다른 가지에서 틀렸다(착수 스모크에서 발견).

### 변형 C — 포털 모달의 키 이벤트가 React 조상으로 버블
① 문제 코드
```tsx
function Panel() {
  const [open, setOpen] = useState(false);
  return <div onKeyDown={movePaneOnCtrlArrow}>            // React 조상
    <button onClick={() => setOpen(true)} />
    {open && createPortal(<Modal />, document.body)}      // DOM은 body, React 부모는 Panel
  </div>;
}
```
② 고친 코드
```ts
let openState = false; let triggerEl: HTMLElement | null = null;   // 모듈(창) 소유
export function openSettings(from: HTMLElement | null) { triggerEl = from; openState = true; emit(); }

export function SettingsLayer() {                                   // 창 루트에 하나
  const open = useSyncExternalStore(subscribe, isOpen, isOpen);
  useEffect(() => {
    if (!open) return;
    const back = triggerEl;
    containerRef.current?.focus();
    return () => { if (back && back.isConnected) back.focus(); };  // 포커스 복원 가드
  }, [open]);
  // 포털 루트: role="dialog" aria-modal, onKeyDown/onKeyUp → stopPropagation (백스톱, preventDefault 없음)
}
// 버튼은 상태를 들지 않는다: onClick={(e) => openSettings(e.currentTarget)}
```
무엇이 깨졌나: 포털이 DOM 위치를 옮겨도 React 조상 관계는 그대로라 조상 핸들러가 모달 입력을 가로챘다.

### 변형 D — 포털 팝오버의 바깥클릭 판정이 DOM 기준 (중첩 포털 포함)
① 문제 코드
```tsx
// 바깥클릭
if (!triggerRef.current?.contains(t)) close();            // 포털 팝오버 안 클릭도 "바깥"

// 부모 메뉴: React onClick은 중첩 포털 클릭까지 받는다
<div data-keep-menu onClick={(e) => {
  if (!(e.target as Element).closest("[data-keep-menu]")) closeMenu();   // 포털 DOM에선 못 찾음
}}>
```
```ts
test("항목을 누르면 메뉴는 닫힌다", ...);                 // 단일 포털 픽스처 — 결함 동작을 계약으로 고정
```
② 고친 코드
```tsx
if (!triggerRef.current?.contains(t) && !popRef.current?.contains(t)) close();   // 자신 포함

<div onClick={(e) => {
  if (popRef.current?.contains(e.target as Node)) return;  // 중첩 포털 클릭 제외
  closeMenu();
}}>
```
```ts
// 결함을 고정하던 테스트 제거
test("중첩 포털 팝오버 클릭은 부모 메뉴를 닫지 않는다", ...); // 포털이 React 트리로 버블한다는 근거 주석
// 이빨 확인: popRef 가드를 제거하면 이 테스트만 실패
```
무엇이 깨졌나: DOM 트리 기반 판정(`contains`·`closest`)과 React 트리 기반 이벤트 전파가 포털 경계에서 어긋났고, 테스트는 한쪽 픽스처로 그 어긋남을 정답으로 굳혔다.\
같은 구조: 같은 사건이 회고 기록에서 "틀린 동작을 지키는 테스트" 사례로 다시 정리됨(좁은 화면 접힘 메뉴의 옵션 선택 소실).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
