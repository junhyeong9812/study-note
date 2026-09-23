# cs/issue/typescript/react/css-containing-context — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 기록 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. flex 아이템의 `min-width`/`min-height` 기본값은 `auto` — 아이템이 스크롤 컨테이너가 아니면 **내용 기반 최소 크기**(대체로 min-content, 지정 크기가 있으면 그것과 비교해 작은 쪽)다. 아이템 자신이 `overflow: hidden/auto/scroll`이면 자동 최소는 0이다.\
그래서 컨테이너가 좁아져도 아이템은 내용 최소폭 아래로 줄지 않고 이웃을 밀어내거나 덮는다. `min-width: 0`을 주면 하한이 0이 되어 flex가 공간을 정상 배분한다.\
grid의 `1fr`은 `minmax(auto, 1fr)`이라 최소값이 (스크롤 컨테이너가 아닌 아이템이면) 역시 내용 기반 최소 크기다 — 안쪽 요소의 최소폭(차트 하한 등)이 트랙을 대화상자 밖까지 키운다. `minmax(0, 1fr)`은 하한을 0으로 내려 트랙이 컨테이너를 따른다.\
주의: 전역 `* { min-width: 0 }`은 내용 최소폭에 의존하는 요소를 깨므로, **줄어야 하는 성장 자식에만** 준다.
   > **min-content** — 요소가 줄바꿈 가능한 곳을 모두 꺾었을 때의 최소 폭. flex/grid의 `auto` 최소 크기는 대개 이 값을 기준으로 하지만, 아이템이 스크롤 컨테이너이거나 축·트랙 조건에 따라 0이 될 수 있다.

2. 휠·터치·스크롤바로는 도달할 수 없다. `max-height`로 높이를 묶어도 `overflow: hidden`이면 초과분은 **사용자 스크롤 UI 없이 잘린다** — 하단 버튼이 DOM에 있지만 마우스 사용자는 닿을 수 없다.\
hidden 요소도 스크롤 컨테이너라 `scrollTop` 변경·`scrollIntoView`·Tab 포커스 이동으로는 스크롤될 수 있다(브라우저 동작에 의존) — 이것을 해결로 삼으면 안 된다. `overflow: clip`은 스크롤 컨테이너 자체를 만들지 않아 프로그램 스크롤도 안 된다.\
`overflow: hidden` 다음에 `overflow-y: auto`를 쓰면 축별 덮어쓰기라 **x는 hidden(모서리 클리핑 유지), y는 auto(스크롤)** 가 된다. 상한은 항상 넘침 정책과 짝으로 리뷰한다.

3. `scrollTop`은 스크롤 컨테이너(`overflow`가 `auto/scroll/hidden` — visible·clip이 아닌 요소, 또는 문서 스크롤 요소)이면서 **내용이 실제로 넘치는** 요소에서만 효과가 있다(사용자 스크롤까지 원하면 auto/scroll). 내용 크기만큼 늘어나는 요소는 넘칠 것이 없으니 no-op이다 — 부모를 타고 올라가 **첫 스크롤 조상**을 조작해야 한다.\
스크롤 박스를 중첩하면(안쪽 블록에 max-height + overflow) 키보드 스크롤은 포커스가 있는 곳의 가장 가까운 스크롤 컨테이너에만 적용되므로, 바깥 컨테이너에 포커스가 있으면 안쪽 내용을 키보드로 내리지 못해 갇힐 수 있다(스크롤 박스의 키보드 포커스 가능 여부는 브라우저마다 다르다). 안쪽 상한을 지우고 **스크롤 주체를 하나**로 둔다.\
같은 계열: 부모 클래스의 `overflow: hidden`(자체 스크롤하는 에디터를 전제)을 그대로 물려받은 새 컨테이너는 스크롤 주체가 없어 스크롤이 죽는다 — 그 컨테이너에서 `overflow-y: auto`로 덮는다.

4. 둘 다 "**어느 조상이 자손의 그리기 영역·좌표 기준을 정하는가**"의 문제다.\
`overflow: hidden` 조상은 자손을 자기 padding box 밖으로 그리지 못하게 **클리핑**한다 — 그 조상이 드롭다운의 포함 블록이거나 포함 블록 체인 안에 있으면 absolute 드롭다운은 그 안에 갇힌다(포함 블록이 그 조상보다 바깥이면 잘리지 않고, fixed 자손은 보통 이 클리핑을 받지 않는다).\
`container-type: inline-size`는 (이 사례 시점의 스펙·브라우저 구현에서) layout containment를 함께 적용하고, layout containment는 absolute·fixed 자손의 **containing block과 스택 컨텍스트를 새로 만든다** — 뷰포트 좌표(clientX/Y)로 띄우던 fixed 메뉴가 그 조상 기준으로 배치된다. 이 효과는 스펙 논의·브라우저 버전에 따라 달라질 수 있으니 대상 브라우저에서 최소 재현으로 확인하고, fixed 자손이 있는 조상은 피해 fixed 자손이 없는 행 단위 요소에 건다.\
구분: 클리핑(그리기 영역을 자름 — overflow·paint containment), containing block(위치·% 크기의 기준), 스택 컨텍스트(z-index 비교 범위), 크기 containment(내용이 자기 크기에 영향 못 줌)는 서로 다른 효과다 — layout containment만으로는 자손을 자르지 않는다.\
같은 계열: positioned 조상이 없는 absolute 헤더의 포함 블록은 초기 포함 블록(뷰포트 크기)이라 body의 `min-width` 하한을 받지 않는다. `height: 100%`의 기준도 부모 레이아웃에 따라 달라, 가로 flex를 전제로 쓴 규칙이 세로 스택에서 스택 전체 높이로 해석된다.
   > **containing block** — 요소의 위치·% 크기를 계산하는 기준 사각형. fixed는 보통 뷰포트지만 transform·filter·layout/paint containment 등을 가진 조상이 있으면 그 조상이 된다. 클리핑과는 별개 개념이다.

5. 컨테이너 쿼리는 뷰포트가 아니라 **가장 가까운 컨테이너 조상의 폭**에 반응한다.\
공용 클래스에 걸면 원래 좁게 설계된 인스턴스(240~360px 칼럼)는 창이 아무리 넓어도 임계값 미만이라 항상 "좁은 상태"로 판정된다.\
적용 대상을 **수식 클래스 + `container-name`** 으로 한정해, 혼잡한 한 곳에서만 규칙이 동작하게 한다.

6. 출처·중요도(`!important`)·캐스케이드 레이어가 같다는 전제에서, 같은 특이도의 선택자는 **소스 순서**가 승부를 가른다 — 공용 클래스가 앞에 정의된 클래스에는 이기고 뒤에 정의된 클래스에는 진다. 호출처마다 결과가 달라진다.\
`:where(.cls)`는 특이도를 0으로 만들어, 공용 기본 스타일을 **호출자의 일반 선택자가 순서와 무관하게 덮기 쉽게** 한다 — 단 호출자 규칙이 더 낮은 레이어에 있거나 역시 특이도 0이면서 앞에 있으면 여전히 지므로 무조건 보장은 아니다.\
넓은 후손 선택자(`.area span { min-width }`)는 서드파티가 span으로 렌더한 값까지 잡는다. 직계 선택자(`.a > div > .b`)는 라이브러리가 끼워 넣은 래퍼 div 때문에 매칭을 놓친다. 타입 열거식 리셋(`input[type=text|tel|…]`)은 열거에서 빠진 새 type(email)을 놓쳐 그 입력만 content-box로 넘친다.\
공통 교훈: 선택자 가정 대신 **렌더된 실제 DOM과 계산값**을 먼저 확인한다. 공용 클래스 규칙을 바꿀 때는 그 클래스를 쓰는 **다른 호출 경로**(다른 창의 툴바 등)를 전수 확인한다.
   > **특이도(specificity)** — 선택자 충돌 시 우선순위를 정하는 점수. 캐스케이드에서 출처·중요도·레이어 비교 다음에 적용되며, 그것들과 특이도가 모두 같으면 나중에 선언된 규칙이 이긴다.

7. `display: none`은 요소를 레이아웃에서 빼 **박스 자체가 없다**. 측정값은 API에 따라 다르다 — 이 사례처럼 `parseInt(getComputedStyle().height)`를 쓰고 높이가 `auto`면 NaN이 되어 위젯이 조기 반환했지만, 높이를 CSS로 명시했다면 그 값이 나오고 `getBoundingClientRect`·`clientHeight`·ResizeObserver는 0을 준다. 그래서 안전성을 NaN에 의존하지 말고, 표시 여부와 측정값의 유효성(양수·최소치)을 검사해 무시하고 다시 보일 때 refit해야 한다. 레이어를 토글할 때마다 그리드가 깨졌다가 다시 그려지는 비용도 있다.\
겹친 레이어의 `visibility: hidden`은 **크기를 유지**한 채 그리기·포커스·히트테스트만 끈다 — 크기 기반 위젯의 상태가 그대로 보존되고, 숨은 요소는 탭 순서에서도 빠진다.\
`height: 0`은 **0px이라는 유효한 크기**를 준다(`flex: 0`은 `flex: 0 1 0%` — grow 0·basis 0일 뿐 높이 0을 보장하지 않지만, 이 사례 레이아웃에서는 0에 가까운 크기가 됐다). 측정 코드는 최소값(2열×1행)을 계산하고 resize 이벤트가 실제 백엔드(PTY)까지 전파되어 화면이 파괴된다 — 이것이 실제 상태를 망가뜨리는 경우다. 백스톱으로 비정상적으로 작은 크기(예: 10열·3행 미만)의 resize를 차단한다.

## 문제 구조 (추상화 코드)

### 변형 A — flex/grid 자동 최소 크기가 줄어듦을 막음
① 문제 코드
```css
.row      { display: flex; }
.pane     { flex: 1 1 0; }                    /* min-width: auto → 내용 최소폭 아래로 못 줄어 이웃을 덮음 */
.dock     { flex: 1; }                         /* 세로 flex 안: min-height: auto → 자식 위젯 0 높이/넘침 */
.dialog   { display: grid; grid-template-columns: 1fr; }   /* 1fr = minmax(auto,1fr) → 안쪽 최소폭이 트랙을 키움 */
.group    { display: inline-flex; white-space: nowrap; }  /* 좁은 폭에서 버튼 그룹이 잘려 도달 불가 */
```
② 고친 코드
```css
.pane     { flex: 1 1 0; min-width: 0; min-height: 0; }   /* 성장 자식에만 */
.dock     { flex: 1; min-height: 0; position: relative; }
.dialog   { grid-template-columns: minmax(0, 1fr); }
.chart-wrap { flex: 0 0 auto; }                /* 부모 추종 캔버스 × flex-grow 성장 루프 차단 */
.group    { display: inline-flex; flex-wrap: wrap; min-width: 0; }
```
무엇이 깨졌나: "내용보다 작아지지 않는다"는 기본 하한이 공간 배분을 막았다.\
같은 구조: 고정폭 칼럼들의 합이 컨테이너를 넘으면 `min-width: 0`인 요소가 먼저 0이 된 뒤 overflow — 칼럼 폭을 "컨테이너 실측 − 다른 칼럼 − 최소치"로 동적 clamp.\
같은 구조: 반응형 차트(부모 크기 추종)와 `height: 100%`·flex-grow가 맞물려 캔버스가 계속 커지는 피드백 루프 — 캔버스에 직접 min-width를 주지 않고 래퍼로 크기를 고정.\
같은 구조: 입력 요소의 고유폭(`size` 속성)이 flex 최소 크기가 되어 잘림(`min-width: 0`), 기본 `flex-shrink: 1`이 아코디언 목록을 2px로 붕괴(`flex-shrink: 0`).

### 변형 B — 높이 상한과 넘침 정책의 짝 불일치 · 스크롤 주체 오인
① 문제 코드
```css
.modal { overflow: hidden; }
.modal { max-height: 85vh; }                   /* 상한만 추가 → 초과분 조용히 잘림 */
.detail-block { max-height: 300px; overflow: auto; }   /* 중첩 스크롤 → 바깥 포커스가 못 내림 */
.md-view { /* .body 클래스를 공유: overflow: hidden (자체 스크롤 에디터 전제) */ }
```
```ts
listEl.scrollTop = listEl.scrollHeight;        // 내용 크기만큼 늘어나는 요소 → no-op
```
② 고친 코드
```css
.modal { max-height: 85vh; overflow-x: hidden; overflow-y: auto; }
.detail-block { /* 상한 제거 — 스크롤은 바깥 컨테이너 하나 */ }
.md-view { overflow-y: auto; }
```
```ts
const scroller = closestScrollable(listEl);    // 첫 스크롤 조상
if (stickBottom) requestAnimationFrame(() => { scroller.scrollTop = scroller.scrollHeight; });
```
무엇이 깨졌나: 크기를 묶는 쪽과 넘침을 처리하는 쪽이 따로 결정되어, 넘친 내용이 잘리거나 엉뚱한 요소가 스크롤 대상이 됐다.

### 변형 C — 클리핑·containing block을 만드는 조상
① 문제 코드
```css
.tab-strip { overflow: hidden; }               /* 탭 안에 그린 확인 드롭다운이 잘림 */
.shell { container-type: inline-size; }        /* 자손 fixed 메뉴·모달이 셸 기준으로 배치 */
```
② 고친 코드
```css
/* 탭은 "닫기 요청"만 발행, 확인 UI 는 앱 레벨 모달이 렌더 */
.toolbar, .pane-head { container-type: inline-size; }   /* fixed 자손이 없는 행에만 */
.tabbar { overflow-x: auto; }                  /* 자손에 fixed 가 있으면 container 대신 */
```
무엇이 깨졌나: 자손의 그리기 영역·좌표 기준을 조상이 바꾸는데, 그 조상을 모른 채 자손만 봤다.\
같은 구조: absolute 헤더는 뷰포트가 포함 블록이라 body의 `min-width`를 받지 않음 — 헤더에도 하한 지정.\
같은 구조: 가로 flex 전제의 `height: 100%`가 세로 스택에서 스택 전체 높이로 해석되어 패널이 대화상자 밖으로 겹침 — 페이지 스코프에서 `height: auto`.\
검증 방법: 수정 전후 CSS를 헤드리스 브라우저 두 프레임에 렌더해 여러 폭에서 요소 rect를 전수 비교(diff 0).

### 변형 D — z-index 숫자 경쟁
① 문제 코드
```css
.overlay-a { z-index: 20; }  .overlay-b { z-index: 30; }  .dnd { z-index: 9999; }   /* 근거 없는 숫자 산재 */
```
② 고친 코드
```css
:root { --z-sticky: 1; --z-lock: 10; --z-pane-modal: 20; --z-peek: 30; /* ... 기존 값 그대로 */ }
.dnd { z-index: var(--z-dnd); }
/* 감사 스크립트: z-index 리터럴 금지(exit 1) · 치환 전후 해석값 순서 일치 증명 */
```
무엇이 깨졌나: 같은 스택 컨텍스트에서 경쟁하는 오버레이들에 단일 스케일이 없어 "더 큰 숫자" 인플레이션이 계속됐다.

### 변형 E — 컨테이너 쿼리 대상 과확장
① 문제 코드
```css
@container (max-width: 560px) { .pane-head .title { display: none; } }   /* 모든 pane head 에 적용 */
```
② 고친 코드
```css
.pane-head--busy { container-type: inline-size; container-name: head-busy; }
@container head-busy (max-width: 560px) { .pane-head--busy .title { display: none; } }
```
무엇이 깨졌나: 폭 기준이 "가장 가까운 컨테이너"인데 원래 좁은 인스턴스까지 같은 규칙을 받았다.

### 변형 F — 캐스케이드·선택자 범위
① 문제 코드
```css
.btn-a { height: 24px; }            /* 앞 정의 */
.more  { height: 21px; }            /* 공용: 앞의 것엔 이기고 */
.btn-b { height: 24px; }            /* 뒤 정의엔 짐 → 호출처마다 치수가 다름 */
.area span { min-width: 120px; }    /* 라이브러리가 span 으로 렌더한 값까지 걸림 */
.panel > div > .content { }         /* 라이브러리 래퍼 div 가 끼면 미매칭 */
input[type=text], input[type=tel] { box-sizing: border-box; }   /* email 누락 */
```
② 고친 코드
```css
:where(.more) { height: 21px; }     /* 특이도 0 — 호출자가 덮음 */
.area .item > span { min-width: auto; }
.panel .content { }
input { box-sizing: border-box; }
.toolbar .title:not(:only-child) { /* 접기 규칙을 제목 하나뿐인 다른 호출 경로에서 제외 */ }
```
무엇이 깨졌나: 선택자가 가정한 DOM·순서와 실제 렌더 DOM·정의 순서가 달랐다.\
같은 구조: 유틸리티 CSS 프레임워크의 기본 리셋이 레거시 CSS를 덮어 깨짐 — 프레임워크 제거.\
같은 구조: 한글 균등배분용 자간이 영문 인쇄물에도 적용 — 인쇄 루트에 언어 클래스를 두고 자간 0.

### 변형 G — 숨김 방식이 측정 크기를 바꿈
① 문제 코드
```tsx
{mode === "dev" ? <DevLayer /> : <MainLayer />}          // 전환마다 리마운트 → 스크롤백·탭 소실
<div style={collapsed ? { height: 0 } : { flex: 1 }}>    // 0px → 측정 2×1 → resize 가 백엔드까지 전파
  <Terminal />
</div>
```
② 고친 코드
```tsx
<div className="layer front"><MainLayer /></div>          // 둘 다 absolute inset:0 로 겹침
<div className="layer back"><DevLayer /></div>            // .back { visibility: hidden } — 크기 유지
<div style={collapsed ? { display: "none" } : { flex: 1 }}>   // 측정값은 API에 따라 NaN/0 — 아래 가드가 실제 방어선
  <Terminal onResize={(c, r) => { if (!(c >= 10 && r >= 3)) return; resizeBackend(c, r); }} />  {/* NaN·0·과소 차단, 재표시 후 refit */}
</div>
```
무엇이 깨졌나: 컨테이너 크기로 행·열을 계산하는 위젯에 "0이라는 유효한 크기"가 전달됐다.

## 검증 기록

- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~G)은 "문제를 소유한 조상을 찾아 그 조상의 정책을 고친다"이다.\
같은 원리(클리핑 조상에 갇힌 팝오버)에 다른 방안이 쓰인 사례:

### 방안 1 — 조상 컨텍스트를 탈출: body 포털 + fixed + 뷰포트 클램프 + ResizeObserver
```tsx
// 문제: overflow:hidden 표면 안의 absolute 드롭다운이 잘려 안 열림 · 화면 밖으로 나감
<div className="surface" style={{ overflow: "hidden" }}>
  <Badge /> {open && <Menu style={{ position: "absolute" }} />}
</div>

// 고친
function useAnchoredPosition(anchorRef, menuRef, open) {
  const [pos, setPos] = useState(null);
  useLayoutEffect(() => {
    if (!open) return;
    const place = () => setPos(computeAnchoredPosition(
      anchorRef.current.getBoundingClientRect(), menuRef.current.getBoundingClientRect(), viewport()));
    place();
    const ro = new ResizeObserver(place); ro.observe(menuRef.current);   // 목록 크기 변화(크기만 — 위치 이동은 못 봄)
    window.addEventListener("scroll", place, true); window.addEventListener("resize", place);
    return () => { ro.disconnect(); /* ...remove listeners */ };
  }, [open]);
  return pos;
}
createPortal(<Menu style={pos ? { position: "fixed", ...pos } : { visibility: "hidden" }} />, document.body);
```
남은 틈: 분할 리사이즈·사이드바 접기처럼 **레이아웃이 앵커를 옮기는** 경우는 scroll/resize 어느 것도 발화하지 않아 메뉴가 앵커에서 떨어진다. 트리거 요소를 ResizeObserver에 넣어도 크기 변화 없는 위치 이동은 감지하지 못하므로, 앵커를 옮기는 레이아웃 이벤트(분할·접기 토글)에서 재배치하거나 열려 있는 동안 앵커 rect를 프레임마다 비교하는 식의 추적이 필요하다(제안 단계).

### 방안 2 — 상하 뒤집기는 "가용 공간이 큰 쪽 + 그 공간으로 maxHeight"
```ts
// 문제: 위에 전체 높이가 들어갈 때만 위로 → 위아래 모두 부족하면 아래로 열려 트리거를 덮음
const openUp = spaceAbove >= menuH;
// 고친: 순수 함수 + 단위 테스트
function computeAnchoredPosition(a, m, vp) {
  const above = a.top - vp.top, below = vp.bottom - a.bottom;
  const openUp = above > below;
  const maxHeight = Math.max(0, openUp ? above : below);         // 앵커가 화면 밖이면 음수 → 0
  const maxWidth = vp.right - vp.left;                             // 메뉴가 뷰포트보다 넓은 경우
  const left = Math.max(vp.left, Math.min(a.left, vp.right - Math.min(m.width, maxWidth)));
  return openUp ? { bottom: vp.bottom - a.top, left, maxHeight, maxWidth }
                : { top: a.bottom, left, maxHeight, maxWidth };
}
// 전제: 메뉴 자체에 overflow-y: auto — maxHeight 로 잘린 항목은 메뉴 내부 스크롤로 도달
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 소유 조상의 정책 수정 | 조상 정책을 바꿔도 다른 자손이 안 깨진다 | CSS 몇 줄 | 조상 정책(클리핑·containment)이 다른 이유로 필요하면 못 바꿈 | 크기·스크롤·쿼리·캐스케이드 문제 대부분 |
| 1. 포털 + fixed + 직접 배치 | 조상 클리핑을 유지해야 한다 | 위치 계산·관측 코드, 포커스·이벤트 경로 관리 | 앵커 이동을 못 보면 떨어져 뜸 | 드롭다운·컨텍스트 메뉴·팝오버 |
| 2. 큰 공간 선택 + maxHeight | 방안 1의 배치 규칙 | 순수 함수 하나 | "들어가느냐" 이진 판정은 양쪽 부족 시 트리거를 덮음 | 화면 가장자리 근처 앵커 |

**결론**: 크기·스크롤·쿼리·캐스케이드 문제는 **조상의 정책을 고치는 쪽**이 근본 해결이고 비용도 작다.\
조상의 클리핑·containment가 그 자체로 필요한 경우(둥근 모서리 클리핑, 표면 격리)에는 팝오버처럼 **밖에 떠야 하는 요소만 포털로 탈출**시키고, 위치는 앵커 rect로 직접 계산하되 뒤집기는 큰 공간 쪽 + maxHeight(+ 메뉴 내부 스크롤·폭 제한)로 가장자리 사례를 덮는다 — 앵커 위치 이동 추적은 별도로 필요하다.
