# cs/issue/typescript/react/theming-token-reach — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문·코드 기준. 복습 전 읽지 말 것.

태그: `single-source-of-truth`

## 정답
<!-- 질문 1:1 대응 -->

1. **CSS 변수의 도달 범위.** CSS 커스텀 프로퍼티는 CSS 캐스케이드를 따라 **DOM 요소의 계산된 스타일**에 상속될 뿐이다.\
canvas 위젯은 픽셀을 JS로 직접 그리므로 색을 CSS에서 읽지 않고 초기화 때 받은 옵션 객체에서 읽는다.\
JS 옵션으로 테마를 받는 에디터도 마찬가지로, 테마는 그 라이브러리 내부 상태이지 우리 스타일시트가 아니다.\
그래서 이런 표면은 테마 스토어를 구독해 **각자의 API로** 새 색을 넘겨줘야 한다.
   > **CSS 커스텀 프로퍼티** — `--name: value`로 선언하고 `var(--name)`으로 읽는 CSS 변수. 선택자·상속으로 퍼지며 CSS 밖(JS 그리기 코드)에는 자동 전달되지 않는다.

2. **SVG 속성 vs CSS 규칙.** 바뀌지 않을 수 있다.\
`stroke="var(--bg)"` 같은 **프레젠테이션 속성**은 브라우저에 따라 `var()`를 받지 않을 수 있어(원 기록도 "미지원 경향"으로만 판단 — 대상 브라우저에서 확인할 일) 선 색이 테마를 따라간다고 기대할 수 없다.\
같은 값을 CSS 클래스 규칙(`.node { stroke: var(--bg) }`)으로 옮기면 캐스케이드 안으로 들어오므로 `var()`가 해석되고 테마 전환을 따른다.
   > **프레젠테이션 속성** — SVG 요소에 직접 쓰는 `fill`·`stroke` 같은 스타일성 속성. CSS 규칙보다 우선순위가 낮은 별도 경로다.

3. **네이티브 컨트롤의 경계.** 닫힌 `<select>` 박스는 페이지 DOM의 일부라 CSS가 먹지만, 펼친 옵션 목록은 **브라우저/OS의 네이티브 위젯**이 그린다.\
페이지 CSS 변수가 그 팝업까지 전달되지 않으므로, 스타일 손질로는 목록 팝업을 맞추는 데 한계가 있다(`color-scheme: dark`로 팝업의 명암만 맞추거나, 최신 브라우저의 커스터마이즈 가능한 select를 쓸 수 있는 환경도 있지만 토큰 색까지 보장되지는 않는다).\
그래서 테마 토큰(`--bg`/`--fg`/`--bg-hover`/`--accent`)만 쓰는 **커스텀 컴포넌트**(여기서는 중첩 트리)로 바꿨다 — 그러면 모든 픽셀이 우리 DOM이 된다.

4. **재생성 vs 라이브 재구성.** 재생성은 위젯 인스턴스를 버리므로 **내부 상태**(편집 중 내용·커서·연결된 세션)도 같이 날아간다.\
그래서 상태를 가진 위젯은 라이브 재구성을 쓴다 — 에디터는 테마 확장 슬롯만 `reconfigure`, 터미널은 `options.theme`·`fontSize`를 갱신하고 글꼴 치수가 바뀌었으니 `fit()`으로 그리드를 다시 맞춘다.\
보존할 상태가 없는 읽기 전용 뷰어는 재생성해도 된다.
   > **라이브 재구성** — 인스턴스를 유지한 채 설정 일부만 교체하는 것. 에디터의 확장 슬롯(compartment) 재구성, 위젯 옵션 갱신이 그 예다.

5. **부분 적용.** 글자색은 라이트 팔레트로 바뀌는데 배경은 다크용 rgba 그대로 남아, 배지가 **팔레트 밖 색 조합(off-palette)**으로 보인다.\
배경도 같은 토큰에서 파생시킨다: `background: color-mix(in srgb, var(--st-danger) 15%, transparent)`.\
이 식은 `rgba(C, 0.15)`와 같은 픽셀이라(transparent와의 혼합은 알파 전곱 보간이라 색은 C 그대로, 알파만 0.15) 다크 모드 모습은 보존되고, 라이트에선 토큰을 따라간다. 색공간 인자를 생략하는 문법은 최신 명세에서만 허용되므로 호환성을 위해 `in srgb`를 명시한다.
   > **color-mix()** — 두 색을 지정 색공간에서 비율대로 섞는 CSS 함수. `transparent`와 섞으면 "토큰 색의 반투명판"을 만든다.

6. **토큰 병합과 검증 모순.** 두 의미(git 추가·상태 성공)가 같은 hex를 쓰는 건 우연이다.\
한 토큰으로 합치면 라이트 테마에서 한쪽 대비를 맞추려 값을 바꿀 때 다른 쪽 의도가 같이 바뀐다 — 그래서 상태용 `--st-*`를 별도로 두었다.\
검증 grep이 `var(--accent, #89b4fa)`의 **fallback 리터럴**까지 세면, fallback은 정당한 코드인데도 "잔존"으로 잡혀 0에 원천적으로 도달할 수 없다 — 검증 설계 자체의 모순이다. 검증은 `var()` 밖의 bare 리터럴로 한정해야 한다.

7. **단일 출처 + 다중 전달.** 색의 **정의**는 토큰 한 곳(CSS 변수)에만 있어야 테마가 일관된다 — 이것이 단일 출처.\
하지만 **소비자**는 CSS 캐스케이드·canvas 옵션·서드파티 클래스·커스텀 컴포넌트로 제각각이라, 같은 토큰을 표면마다 다른 경로로 전달해야 한다.\
출처를 복제하면(위젯마다 색을 따로 하드코딩) 일관성이 깨지고, 전달을 하나로 가정하면(CSS 변수만) 도달 범위 밖이 남는다 — 둘 다 지켜야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — CSS 변수만 바꾸고 비-CSS 표면은 방치
① 문제 코드
```ts
// 테마 전환 = data-theme 속성만 바꿈
document.documentElement.dataset.theme = theme;
// canvas 터미널·에디터·도킹 레이아웃은 초기화 때 받은 다크 테마 그대로
```
② 고친 코드
```ts
useEffect(() => {                                   // 테마 스토어 구독
  term.options.theme = termTheme(theme);            // canvas 위젯: 옵션 라이브 갱신
  term.options.fontSize = fontSize;
  fitAddon.fit();                                   // 치수 변화 → 그리드 재계산
}, [theme, fontSize]);

useEffect(() => {                                   // 에디터: 재생성하지 않고 슬롯만 교체
  viewRef.current?.dispatch({ effects: themeSlot.current.reconfigure(editorThemeExt(theme)) });
}, [theme]);
export const editorThemeExt = (theme) => (theme === "light" ? [] : darkTheme);  // 자체 배경을 칠하는 다크 테마는 라이트에서 뺀다

<Layout className={`layout-theme-${theme}`} />     // 서드파티: 자체 테마 클래스
```
```css
/* SVG: 속성 stroke="var(--bg)" 대신 CSS 규칙 */
.graph-node { stroke: var(--bg); }
```
무엇이 깨졌나: 캐스케이드 밖 표면에 캐스케이드용 수단만 썼고, 재생성으로 맞추면 편집 상태가 날아갔다.

### 변형 B — OS가 그리는 네이티브 컨트롤
① 문제 코드
```tsx
<select className="root-select">{roots.map(r => <option key={r}>{r}</option>)}</select>
/* 닫힌 박스는 테마 적용, 펼친 목록은 OS 렌더 → 테마 밖 */
```
② 고친 코드
```tsx
function drawNodes(nodes) {                          // 재귀 커스텀 트리
  return nodes.map(n => n.isRoot
    ? <div className="root-row" onClick={() => pick(n)}>{n.name}</div>   // 선택 가능
    : <div className="root-dir">{n.name}{drawNodes(n.children)}</div>); // 구조만
}
/* .root-row { background: var(--bg); color: var(--fg); } .root-row:hover { background: var(--bg-hover); } */
```
무엇이 깨졌나: 네이티브 팝업은 페이지 CSS 변수의 도달 범위 밖이다.

### 변형 C — 한 시각 단위의 색이 일부만 토큰
① 문제 코드
```css
.badge-danger {
  color: var(--st-danger);                   /* 텍스트만 토큰 */
  background: rgba(R, G, B, .15);        /* 리터럴 → 라이트에서 off-palette */
  border: 1px solid rgba(R, G, B, .4);
}
```
```sh
grep -rnE '#[0-9a-f]{6}' src/ | wc -l        # var(--x, #...) fallback까지 세어 0 도달 불가
```
② 고친 코드
```css
.badge-danger {
  color: var(--st-danger);                                             /* 상태 토큰(--st-*)은 같은 hex를 쓰는 git 토큰과 분리 */
  background: color-mix(in srgb, var(--st-danger) 15%, transparent);  /* ≡ rgba(C, .15) */
  border: 1px solid color-mix(in srgb, var(--st-danger) 40%, transparent);
}
```
```sh
# 검증: var( ... ) fallback을 제외한 bare 리터럴만 센다
```
무엇이 깨졌나: 텍스트만 토큰을 따르고 짝을 이루는 배경·테두리는 고정돼 한 단위의 색이 갈라졌다.\
같은 구조: 강조색(accent)의 rgba 파생 17곳도 같은 방식으로 토큰 파생으로 회수.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
