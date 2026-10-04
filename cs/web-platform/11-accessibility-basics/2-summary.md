# web-platform/11-accessibility-basics — 시맨틱 마크업·접근성 트리·키보드·ARIA — 정리 (힌트)

## 해결하는 문제

화면을 눈으로 보고 마우스로 누르는 사용자만 있는 것이 아니다.

```text
  같은 "결제하기" 버튼을 쓰는 여러 길

  마우스 사용자     ── 눈 + 클릭 ─────────────────────┐
  키보드 사용자     ── Tab으로 이동, Enter·Space ─────┤
  스크린리더 사용자 ── "버튼, 결제하기" 음성 ─────────┼──> 버튼이 동작해야 한다
  음성 제어 사용자  ── "결제하기 클릭" 발화 ──────────┘
```

- 스크린리더·음성 제어 같은 보조 기술은 화면 그림에서 역할·이름을 읽지 않는다. 브라우저가 따로 만든 **접근성 트리**에서 얻는다.
  - 키보드·화면 확대기 사용자 중에는 화면을 보며 조작하는 사람도 많다. 이들에게는 포커스 이동·포커스 표시가 핵심이다.
  - *보조 기술(assistive technology)*: 스크린리더·화면 확대기·음성 제어·스위치 입력처럼, 사용자 대신 화면을 읽거나 조작하는 프로그램.
  - *접근성 트리(accessibility tree)*: 브라우저가 DOM에서 뽑아 보조 기술에 넘기는 트리. 노드마다 역할(role)·이름(name)·상태(state)를 가진다.
- `<div onclick>`으로 만든 버튼은 마우스로는 눌린다. 하지만 접근성 트리에 "버튼"이 없고, Tab으로 갈 수도 없다(아래 실험).

쉬운 예: 엘리베이터 버튼에 점자가 없으면 시각장애인은 층을 고를 수 없다. 버튼은 "있지만" 그 사람에게는 없는 것과 같다.

똑같은 구조다.\
웹에서는 점자가 접근성 트리의 역할·이름이고, "누를 수 있음"이 키보드 포커스와 Enter·Space 동작이다.

실무 예:
- 결제 폼의 "다음" 버튼이 `<div>`라서 키보드 사용자가 결제를 끝내지 못한다.
- 아이콘만 있는 닫기 버튼에 이름이 없어 스크린리더가 "버튼"이라고만 읽는다.
- WebAIM Million 2026(2026-02, 상위 100만 홈페이지를 WAVE로 자동 검사)에서 95.9%가 WCAG 2 자동 검출 실패를 가졌다. 입력 레이블 누락 51%, 빈 버튼 30.6%다.

## 동작·원리

### 1. DOM → 접근성 트리 → 보조 기술

```text
   DOM                              접근성 트리 (Chrome 151 실측)          보조 기술
  <h1>결제</h1>             ──>   heading  "결제"                  ──>  "제목 1, 결제"
  <button>결제하기</button> ──>   button   "결제하기"  focusable   ──>  "버튼, 결제하기"
  <div onclick>결제하기</div> ──> generic  ""                      ──>  (그냥 글자 "결제하기")
  <label for=e>이메일 주소</label>
  <input id=e type=email>   ──>   textbox  "이메일 주소" focusable ──>  "편집, 이메일 주소"
```

- 브라우저는 HTML 요소마다 정해진 **암묵적 역할**을 접근성 트리에 넣는다. 이 대응표가 W3C HTML-AAM(HTML Accessibility API Mappings)이다.
  - *역할(role)*: 이 노드가 무엇인가(button·link·textbox·heading…).
  - *접근 가능한 이름(accessible name)*: 보조 기술이 읽는 이름. 버튼은 안쪽 글자, 입력칸은 연결된 `<label>`에서 온다.
  - *상태(state)*: 눌림(`aria-pressed`)·펼침(`aria-expanded`)·비활성(`disabled`) 같은 바뀌는 값.
- WCAG 2.2 SC 4.1.2 Name, Role, Value(수준 A)가 이 세 값을 요구한다.

### 2. 네이티브 요소가 공짜로 주는 것

```text
                       <button>    <div onclick>    <div role=button tabindex=0>
  역할(접근성 트리)      button      generic          button
  Tab으로 도달          예           아니오            예
  Enter로 click        예           아니오            아니오 (직접 구현해야)
  Space로 click        예           아니오            아니오 (직접 구현해야)
  폼 제출·disabled      예           아니오            아니오
```

- 표의 Tab·Enter·Space 칸은 아래 실험(Chrome 151)에서 본 결과다.
- ARIA는 **접근성 트리에 보이는 의미만** 바꾼다. 키보드 동작은 주지 않는다.
  - ARIA APG "Read Me First": ARIA 역할은 브라우저가 키보드 동작이나 스타일을 제공하게 하지 않는다. `role="button"`은 "Enter·Space에 반응하겠다"는 **약속**이고, 그 약속은 개발자가 JS로 지켜야 한다.
  - *ARIA(WAI-ARIA)*: 접근성 트리의 역할·이름·상태를 HTML 속성(`role`, `aria-*`)으로 덧붙이거나 바꾸는 W3C 명세. 현재 권고안은 WAI-ARIA 1.2.

### 3. "잘못된 ARIA가 없는 것보다 나쁘다"

```text
  <span role=button aria-hidden=true tabindex=0>숨긴 버튼</span>

  키보드:      Tab ──> 여기에 멈춘다 (포커스 있음)
  접근성 트리:  ignored (없는 노드)
  스크린리더:   포커스는 왔는데 읽을 정보(역할·이름)가 트리에 없다 → "빈 정지점"
               (실제 발화는 보조 기술마다 다를 수 있다 — 이 노트는 재지 않았다)
```

- W3C "Using ARIA"의 규칙
  - 첫째: 필요한 의미·동작이 이미 들어 있는 네이티브 HTML 요소가 있으면, 다른 요소에 ARIA를 붙이지 말고 그것을 쓴다.
  - 넷째: 포커스 가능한 요소에 `role="presentation"`이나 `aria-hidden="true"`를 쓰지 않는다.
- ARIA APG에는 "No ARIA is better than Bad ARIA" 절이 있다. 잘못된 역할은 보조 기술에 거짓 정보를 준다.
- WebAIM Million 2026: ARIA가 있는 홈페이지의 평균 검출 오류는 59.1개, 없는 페이지는 42개였다. 상관관계이지 인과는 아니다(해석). 복잡한 페이지일수록 ARIA도 많이 쓰기 때문일 수 있다.

### 4. 키보드 포커스 순서

```text
  DOM 순서:   [input tabindex=3] ... [button] [div role=button tabindex=0] ... [a href]
  Tab 순서:   ① 양수 tabindex가 먼저(값 오름차순)  ② 나머지 포커스 가능 요소를 DOM 순서대로
              ③ tabindex=-1 은 Tab 순서에서 빠짐(스크립트 focus()는 가능)
                 — 표준은 "should"다. 순차 이동만 가능한 사용자를 위해 UA가 넣을 수 있다
```

- HTML 표준의 "sequential focus navigation order"는 양수 `tabindex`를 먼저, 0(과 기본 포커스 가능 요소)을 DOM 순서대로 두라고 권고한다(규범어 "should"). 실험의 Chrome 151도 그렇게 동작했다.
- 양수 `tabindex`는 화면 순서와 Tab 순서를 어긋나게 한다. WCAG 2.2 SC 2.4.3 Focus Order(A) 위반으로 이어지기 쉽다. axe-core는 `tabindex` 규칙으로 경고한다(아래 실험).
- 포커스 관련 WCAG 2.2 기준(수준 표기는 WCAG 2.2 권고안 원문)
  - 2.1.1 Keyboard(A): 기능을 키보드로 쓸 수 있어야. 예외는 기능 자체가 포인터 이동 경로에 의존할 때뿐이다(자유 곡선 그리기 등). 원문 Note 1: 손글씨 입력은 입력 *기법*만 경로 의존이고 기능(글자 입력)은 아니므로 예외가 아니다.
  - 2.1.2 No Keyboard Trap(A): 들어간 곳에서 키보드로 빠져나올 수 있어야.
  - 2.4.7 Focus Visible(AA): 포커스 위치가 보여야. `outline: none`만 걸고 대체 표시를 안 주면 깨진다.
  - 2.4.11 Focus Not Obscured (Minimum)(AA, 2.2 신설): 고정 헤더·쿠키 배너가 포커스된 요소를 완전히 가리면 안 된다.
  - 2.5.8 Target Size (Minimum)(AA, 2.2 신설): 포인터 대상은 24×24 CSS px 이상. 간격·동등 대체·인라인·UA 기본·필수 예외가 있다.

### 실험: 접근성 트리·Tab 순서·Enter/Space를 실제로 잰다

환경: headless Chrome 151.0.7922.173, Playwright `playwright-core` 1.62, CDP `Accessibility.getFullAXTree`·`Accessibility.getPartialAXTree`, 2026-10-04. 같은 스크립트를 두 번 돌려 출력이 같았다(시간 수치가 없는 결정적 실험).

```html
<!-- 실험 페이지(핵심) -->
<h1>결제</h1>
<div id="divbtn" onclick="log('div')">결제하기(div)</div>
<button id="btn" onclick="log('button')">결제하기(button)</button>
<div id="rolebtn" role="button" tabindex="0" onclick="log('rolebtn')">결제하기(role=button)</div>
<span id="ghost" role="button" aria-hidden="true" tabindex="0">숨긴 버튼</span>
<button id="iconbtn"><svg width="16" height="16"></svg></button>
<button id="labeled" aria-label="닫기">X</button>
<input id="noLabel" type="text" placeholder="이메일">
<label for="withLabel">이메일 주소</label><input id="withLabel" type="email">
<a id="nohref" onclick="log('a')">링크(href 없음)</a>
<a id="link" href="#x">링크(href)</a>
<a id="plainA">앵커(href·onclick 없음)</a>
<div id="fixed" role="button" tabindex="0" onclick="log('fixed')"
     onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();this.click()}">결제하기(role+키 처리)</div>
<input id="pos" tabindex="3" value="tabindex=3">
```

```js
// 측정(핵심): 요소별 접근성 노드, Tab 11번, 포커스 후 Enter·Space
const cdp = await page.context().newCDPSession(page);
await cdp.send('Accessibility.enable');
const { root } = await cdp.send('DOM.getDocument', { depth: 0 });
const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: '#divbtn' });
const { nodes } = await cdp.send('Accessibility.getPartialAXTree', { nodeId, fetchRelatives: false });
// nodes[0].role.value, nodes[0].name.value, nodes[0].ignored
for (let i = 0; i < 11; i++) { await page.keyboard.press('Tab'); /* document.activeElement.id 기록 */ }
// 요소마다: activeElement.blur() → el.focus() → Enter → Space → 클릭 로그 확인
```

(실험, headless Chrome 151, 스로틀 없음, 기본 뷰포트 1280×720, 2026-10-04)

```text
== per element ==
#divbtn: role=generic name="" ignored=false
#btn: role=button name="결제하기(button)" ignored=false
#rolebtn: role=button name="결제하기(role=button)" ignored=false
#ghost: role=none name="" ignored=true
#iconbtn: role=button name="" ignored=false
#labeled: role=button name="닫기" ignored=false
#noLabel: role=textbox name="이메일" ignored=false
#withLabel: role=textbox name="이메일 주소" ignored=false
#nohref: role=link name="링크(href 없음)" ignored=false
#link: role=link name="링크(href)" ignored=false
#plainA: role=generic name="" ignored=false
#fixed: role=button name="결제하기(role+키 처리)" ignored=false
== Tab order ==
pos -> btn -> rolebtn -> ghost -> iconbtn -> labeled -> noLabel -> withLabel -> link -> fixed -> BODY
== Enter/Space activation ==
#divbtn: focus()->active=(body) clicks=[]
#btn: focus()->active=btn clicks=["button","button"]
#rolebtn: focus()->active=rolebtn clicks=[]
#nohref: focus()->active=(body) clicks=[]
#fixed: focus()->active=fixed clicks=["fixed","fixed"]
```

관찰과 해석
- `div onclick`은 역할이 `generic`, 이름도 없다. Tab 순서에 없고 `focus()`도 받지 않는다. 키보드·스크린리더 사용자에게는 버튼이 없다.
- `<button>`은 Enter·Space 모두에서 `click`이 났다(로그 2개).
- `role="button" tabindex="0"`은 역할과 포커스는 얻었다. 그러나 Enter·Space에 `click`이 0개다. 키 처리를 직접 넣은 `#fixed`에서야 2개가 됐다.
- `#ghost`(aria-hidden + tabindex=0)는 접근성 트리에서 빠졌는데(`ignored=true`) Tab은 여기에 멈춘다. 트리에 없는 Tab 정지점, 곧 "빈 정지점"의 조건이 실측으로 보인다. 스크린리더 발화는 재지 않았다 — W3C ACT 규칙은 이것이 보조 기술 사용자에게 혼란을 줄 수 있다고 한다.
- `#iconbtn`은 버튼이지만 이름이 `""`다. `#labeled`는 `aria-label`이 보이는 글자 "X"를 덮어 "닫기"가 이름이 됐다.
- `#noLabel`은 `placeholder`가 이름으로 쓰였다("이메일"). 접근 가능한 이름 계산에서 placeholder는 마지막 대체 수단이다. 입력을 시작하면 placeholder가 화면에서 사라지므로 레이블을 대신하지 못한다(WCAG 3.3.2 Labels or Instructions).
- `href` 없는 `<a>`는 Tab 순서에 없다. 그런데 Chrome 151은 `onclick`이 붙은 `#nohref`를 `link`로 노출했고, 아무것도 없는 `#plainA`는 `generic`이었다. 스크린리더는 "링크"라고 읽는데 키보드로는 갈 수 없는 상태다. 다른 엔진(Firefox·Safari)의 노출은 확인하지 않았다 `[?]`.
- `tabindex=3`인 `#pos`가 DOM 맨 끝에 있는데 Tab 첫 번째였다.

### 실험: 자동 검사기가 잡는 것과 놓치는 것

같은 페이지에 axe-core 4.13.0을 주입해 `axe.run(document)`을 돌렸다(headless Chrome 151, 2026-10-04).

```text
aria-hidden-focus [serious] #ghost
button-name [critical] #iconbtn
document-title [serious] html
label [critical] #pos
landmark-one-main [moderate] html
region [moderate] h1, #divbtn, #noLabel, label, #withLabel, #nohref, #link, #plainA, #pos
tabindex [serious] #pos
```

- 잡은 것: 빈 정지점(`aria-hidden-focus`), 이름 없는 버튼(`button-name`), 레이블 없는 입력(`label` — `#pos`), 양수 tabindex.
- **놓친 것**: `#divbtn`(클릭되는 div), `#rolebtn`(Enter·Space 미구현), `#nohref`(포커스 불가 링크). 셋 다 "키보드로 실제 눌러 봐야" 드러나는 문제다.
- `#noLabel`도 `label` 위반으로 잡히지 않았다. placeholder가 이름을 채웠기 때문이다(해석).
- 결론: 자동 검사는 출발점이다. 키보드만으로 한 바퀴 돌아 보는 수동 점검을 대신하지 못한다.

## 쓰이는 자료구조·알고리즘

- **접근성 트리 = DOM에서 가지치기한 트리** — 의미 없는 `div`·`span`(generic)은 접거나 빼고, `aria-hidden` 하위 트리는 통째로 뺀다. 스크린리더는 이 트리를 깊이 우선 순서로 읽는다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)(트리 순회)
- **포커스 순서 = 안정 정렬(한 포커스 탐색 범위 안에서)** — 키(양수 `tabindex` 값, 0은 맨 뒤 그룹)로 정렬하고 같은 키는 트리 순서를 지킨다. 표준은 섀도 트리·팝오버 같은 *포커스 탐색 범위*마다 따로 정렬한 뒤 그 범위를 제자리에 펼쳐 넣는다(HTML "Focus" 절). 이 실험 페이지는 범위가 하나라 단순 정렬과 같다. [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)(안정 정렬)
- **접근 가능한 이름 계산 = 우선순위 폴백 체인** — `aria-labelledby` → `aria-label` → 네이티브 레이블(`<label>`·안쪽 글자·`alt`) → `title`·`placeholder` 순으로 첫 값을 쓴다(W3C Accessible Name and Description Computation 1.2, HTML-AAM). 실험의 `#labeled`·`#noLabel`이 이 체인의 결과다.
- **포커스 트랩 = 순환 목록** — 모달 안에서 마지막 요소 다음 Tab이 첫 요소로 돌아간다. `<dialog>`의 `showModal()`은 바깥을 inert로 만들어 Tab이 바깥 페이지 요소로 가지 않게 한다([languages/web-api/14](../../../languages/web-api/14-dialog-popover-scripting/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 네이티브 요소 먼저

```html
<!-- 나쁨 -->
<div class="btn" onclick="pay()">결제하기</div>
<span class="link" onclick="go('/terms')">약관</span>

<!-- 좋음: 역할·포커스·키보드 활성화가 따라온다(button은 Enter·Space, 링크는 Enter).
     폼 제출은 폼 안의 type="submit" 버튼일 때만 -->
<button type="button" onclick="pay()">결제하기</button>
<a href="/terms">약관</a>
```

- 구분 기준: **이동이면 `<a href>`**, **동작이면 `<button>`**.
- 스타일 때문에 div를 쓰는 경우가 많다. `button { all: unset; }` 뒤 다시 꾸미면 된다. 단 `all: unset`은 포커스 표시도 지우므로 `:focus-visible` 스타일을 다시 준다(WCAG 2.4.7).

### 2. 네이티브가 없는 위젯만 ARIA + 키보드를 직접

```ts
// 토글 버튼: 네이티브 <button>에 상태만 ARIA로 더한다
const btn = document.querySelector<HTMLButtonElement>('#mute')!;
btn.addEventListener('click', () => {
  const on = btn.getAttribute('aria-pressed') === 'true';
  btn.setAttribute('aria-pressed', String(!on));   // 스크린리더: "눌림/안 눌림"
});
```

- 탭 목록·콤보박스·트리처럼 HTML에 없는 위젯은 ARIA APG의 해당 패턴(역할 구조 + 키보드 표)을 그대로 따른다. 탭 패턴이면 화살표 키 이동과 탭 목록 안의 포커스 관리가 함께 필요하다. APG 예시는 roving tabindex(선택된 탭만 `tabindex=0`, 나머지 `-1`)를 쓴다. `aria-activedescendant`도 APG가 드는 다른 방법이다. 수동 활성화 탭에서는 화살표로 포커스된 탭과 선택된 탭이 다를 수 있다.

### 3. 이름·레이블

```html
<label for="email">이메일 주소</label>
<input id="email" type="email" autocomplete="email">

<button aria-label="닫기"><svg aria-hidden="true">…</svg></button>   <!-- 아이콘 버튼 -->
<img src="chart.png" alt="3분기 매출 12% 증가">                       <!-- 정보 이미지 -->
<img src="divider.png" alt="">                                       <!-- 장식 이미지: 빈 alt -->
<html lang="ko">                                                     <!-- 3.1.1 Language of Page -->
```

### 4. 진단 순서

1. **키보드만으로 한 바퀴**: 마우스를 치우고 Tab·Shift+Tab·Enter·Space·Esc로 주요 흐름(로그인·결제)을 끝까지 간다. 포커스가 보이나, 순서가 화면과 맞나, 갇히지 않나.
2. **접근성 트리 보기**: Chrome DevTools → Elements → Accessibility 창(역할·이름·계산 경로). 자동화는 CDP `Accessibility.getFullAXTree`(위 실험), Playwright `locator.ariaSnapshot()`/`getByRole`(옛 `page.accessibility`는 playwright-core 1.62 타입 정의에 없다).
3. **자동 검사**: axe-core·Lighthouse 접근성 감사. CI에 넣되, 통과가 "접근 가능"을 뜻하지 않는다는 점을 위 실험이 보여 준다.
4. **스크린리더 실측**: NVDA(Windows)·VoiceOver(macOS·iOS)·TalkBack(Android)으로 핵심 화면을 들어 본다. 접근성 트리는 보조 기술의 **입력**이지 실제로 읽히는 문장이 아니다.

테스트에서 역할로 찾는 습관이 역할·이름 회귀를 막는다(해석). 키보드 회귀는 키로 눌러 봐야 잡힌다.

```ts
// Playwright: 역할+이름으로 찾으면, 역할 없는 <div onclick>으로 바뀌는 순간 테스트가 깨진다
// 단 <div role="button">은 그대로 잡히고 .click()은 마우스 클릭이다 → Enter·Space 누락은 못 잡는다
await page.getByRole('button', { name: '결제하기' }).click();
// 키보드 활성화까지 보려면 .click() 대신: await page.getByRole('button', { name: '결제하기' }).press('Enter');
await page.getByLabel('이메일 주소').fill('a@example.com');
```

## 장애 시나리오와 대처

### 1. div 버튼 → 키보드·스크린리더로 결제 불가

- **현상**: 키보드 사용자가 "결제하기"에 도달하지 못한다. 스크린리더는 그냥 글자로 읽는다.
- **보이는 형태**: Tab을 눌러도 포커스가 버튼을 건너뛴다. 접근성 트리에서 `generic`, 이름 없음(실험 `#divbtn`). 자동 검사는 대개 통과한다(실험에서 axe가 잡지 못함).
- **원인**: `div`에는 역할·포커스·키보드 활성화가 없다. 브라우저가 Enter·Space를 `click`으로 바꿔 주지 않으므로 `onclick`은 키보드로는 불리지 않는다(실험 `#divbtn` clicks=[]).
- **대처**: `<button>`으로 바꾼다. 못 바꾸면 `role="button"` + `tabindex="0"` + Enter·Space 키 처리를 모두 넣는다(실험 `#fixed`). 셋 중 하나만 넣으면 반쪽이다(실험 `#rolebtn`).

### 2. 잘못된 ARIA → 없느니만 못한 상태

- **현상**: 스크린리더가 엉뚱한 역할을 읽거나, 포커스가 갔는데 아무것도 읽지 않는다.
- **보이는 형태**: axe `aria-hidden-focus`, `aria-allowed-role`, `aria-required-children` 같은 위반. 접근성 트리에서 `ignored=true`인데 Tab이 멈추는 노드(실험 `#ghost`).
- **원인**: 모달을 열 때 배경에 `aria-hidden="true"`만 걸고 배경 버튼들의 포커스는 그대로 둠. `role="menu"`를 내비게이션 링크 목록에 붙여 메뉴 키보드 동작을 약속만 함.
- **대처**: 배경 차단은 `inert` 속성이나 `<dialog>.showModal()`을 쓴다(포커스와 접근성 트리를 함께 막는다). 역할을 붙였으면 APG 키보드 표를 구현하거나, 구현하지 않을 거면 역할을 뗀다.

### 3. 포커스 표시 제거 → 키보드 사용자가 위치를 잃음

- **현상**: Tab을 누르면 무언가 움직이는데 어디 있는지 안 보인다.
- **보이는 형태**: CSS 리셋에 `*:focus { outline: none }`. WCAG 2.4.7 위반.
- **원인**: 마우스 클릭 때 테두리가 보기 싫어 일괄 제거.
- **대처**: `:focus-visible`만 꾸민다. 브라우저가 키보드 탐색 같은 경우에만 이 상태를 매칭하는 휴리스틱을 쓴다(CSS Selectors Level 4). 고정 헤더가 포커스 요소를 가리면 `scroll-padding-top`으로 띄운다(2.4.11).

### 4. SPA 화면 전환 후 포커스·알림 없음

- **현상**: 라우트가 바뀌어 화면 내용이 바뀌었는데, 스크린리더는 아무 말도 안 한다. 포커스는 사라진 링크 자리(또는 `body`)에 남는다.
- **보이는 형태**: 전환 직후 `document.activeElement`가 `body`. 사용자는 Tab을 처음부터 다시 누른다.
- **원인**: 전체 페이지 로드가 없으니 브라우저가 새 문서를 알리지 않는다.
- **대처**: 전환 뒤 새 화면의 `<h1>`(`tabindex="-1"`)에 `focus()`를 옮기고 `document.title`을 갱신한다. 비동기 결과("저장됨")는 `aria-live="polite"` 영역으로 알린다.

### 5. 아이콘 버튼·입력칸 이름 누락

- **현상**: "버튼", "편집"만 읽힌다.
- **보이는 형태**: axe `button-name`·`label`·`link-name`. 접근성 트리 이름이 `""`(실험 `#iconbtn`). WebAIM Million 2026의 빈 버튼 30.6%, 레이블 누락 51%가 이 유형이다.
- **원인**: 아이콘(SVG·아이콘 폰트)만 넣고 텍스트 대안을 안 줌. placeholder를 레이블 대신 씀.
- **대처**: `aria-label` 또는 화면에서 숨긴 텍스트. 입력칸은 보이는 `<label>`을 기본으로 한다.

## 핵심 문장

- 스크린리더 같은 보조 기술은 화면 그림이 아니라 접근성 트리(역할·이름·상태)를 읽는다. 브라우저는 네이티브 HTML 요소에서 이 값을 만든다.
- `<button>`은 역할·포커스·Enter/Space 활성화를 공짜로 준다. `<div onclick>`은 셋 다 없다(Chrome 151 실측).
- ARIA는 접근성 트리의 의미만 바꾸고 키보드 동작은 주지 않는다. `role="button"`은 Enter·Space를 직접 구현하겠다는 약속이다.
- 포커스 가능한 요소에 `aria-hidden`을 걸면 "포커스는 오는데 트리에 읽을 정보가 없는" 빈 정지점이 생긴다. 잘못된 ARIA는 없는 것보다 나쁠 수 있다.
- 양수 `tabindex`는 Tab 순서를 DOM 순서와 어긋나게 한다.
- 자동 검사기는 이름 누락·잘못된 ARIA를 잘 잡지만 div 버튼·키 처리 누락은 놓친다. 키보드 한 바퀴 점검이 함께 필요하다.

## 관련 주제·근거

- 선행
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md) — DOM 트리·이벤트 전파
- 후속·연결
  - [17-list-virtualization](../17-list-virtualization/2-summary.md) — 가상화한 목록이 스크린리더·찾기에서 빠지는 문제
  - [10-rendering-strategies](../10-rendering-strategies/2-summary.md) — SPA 라우팅과 포커스 관리
  - [12-internationalization-and-localization](../12-internationalization-and-localization/2-summary.md) — `lang` 속성, RTL
  - [languages/web-api/14 dialog·popover](../../../languages/web-api/14-dialog-popover-scripting/2-summary.md) — `showModal()`·inert·초기 포커스
  - [languages/web-api/22 입력 이벤트 순서](../../../languages/web-api/22-input-event-order/2-summary.md), [languages/web-api/18 이벤트 위임](../../../languages/web-api/18-event-delegation/2-summary.md)
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md), [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- 표준·문서
  - WCAG 2.2(W3C 권고안, 현행판 2024-12-12) — 1.3.1·2.1.1·2.1.2·2.4.3·2.4.7·2.4.11·2.5.8·3.1.1·3.3.2·4.1.2, 4.1.1 Parsing 삭제 <https://www.w3.org/TR/WCAG22/>
  - Understanding SC 2.5.8 Target Size (Minimum) — 24×24 CSS px와 예외 5개 <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html>
  - WAI-ARIA 1.2 <https://www.w3.org/TR/wai-aria-1.2/>
  - ARIA Authoring Practices Guide "Read Me First" — No ARIA is better than Bad ARIA, 역할은 키보드 동작을 주지 않는다 <https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/>
  - W3C "Using ARIA" — ARIA 사용 규칙(첫째: 네이티브 우선, 넷째: 포커스 가능 요소에 aria-hidden 금지) <https://www.w3.org/TR/using-aria/>
  - HTML-AAM(HTML 요소 → 역할 대응) <https://www.w3.org/TR/html-aam-1.0/> · Accessible Name and Description Computation 1.2 <https://www.w3.org/TR/accname-1.2/>
  - HTML 표준 "Focus" 절 — sequential focus navigation·포커스 탐색 범위, `tabindex`(음수 값 제외는 should), `inert` <https://html.spec.whatwg.org/multipage/interaction.html#focus>
  - WebAIM Million 2026 — 95.9% 실패, 평균 56.1개, 레이블 누락 51%, 빈 버튼 30.6%, ARIA 있음 59.1 vs 없음 42 <https://webaim.org/projects/million/>
  - W3C ACT 규칙 "Element with aria-hidden has no content in sequential focus navigation" <https://www.w3.org/WAI/standards-guidelines/act/rules/6cfa84/>
  - HTML 표준 `dialog` — `closedby`(auto: `showModal()`이면 닫기 요청으로 닫힘) <https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element>
  - axe-core 규칙 목록 <https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md>
- 실험 목록
  - 접근성 트리·Tab 순서·Enter/Space: headless Chrome 151.0.7922.173 + playwright-core 1.62.1(Node 20.19), CDP `Accessibility.getPartialAXTree`·`getFullAXTree`, 키보드 `Tab`×11·`Enter`·`Space`. 두 번 실행해 같은 출력.
  - 자동 검사: 같은 페이지 + axe-core 4.13.0 `axe.run(document)`.
  - 사실 점검 재실행(2026-10-04, 같은 Chrome 151·playwright-core 1.62.1·axe-core 4.13.0): 두 스크립트 출력이 위와 같았다.
