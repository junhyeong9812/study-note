# web-platform/11-accessibility-basics — 정답

## 정답

### 1. 접근성 트리와 Name·Role·Value

- 브라우저가 DOM에서 뽑아 보조 기술에 넘기는 **접근성 트리**를 본다.
- 노드마다 **역할**(button·link·textbox…), **접근 가능한 이름**(읽어 줄 이름), **상태·값**(눌림·펼침·비활성·입력값)을 갖는다.
- WCAG 2.2 SC 4.1.2 Name, Role, Value(수준 A)가 이 셋을 보조 기술이 알 수 있게 하라고 요구한다.

### 2. 세 가지 "결제하기"

(실험, headless Chrome 151, 2026-10-04)

| | 역할 | Tab 도달 | Enter·Space 후 click |
|---|---|---|---|
| `div onclick` | `generic`, 이름 `""` | 아니오(`focus()`도 안 받음) | 0 |
| `button` | `button` "결제하기" | 예 | 2(Enter 1, Space 1) |
| `div role=button tabindex=0` | `button` "결제하기" | 예 | 0 |

- 실험 출력: `#divbtn: ... clicks=[]`, `#btn: ... clicks=["button","button"]`, `#rolebtn: ... clicks=[]`.

### 3. ARIA는 약속, 동작은 개발자 몫

- `role="button"`은 접근성 트리의 역할만 `button`으로 바꿨다. `tabindex="0"`은 포커스만 줬다. 그래서 스크린리더는 "버튼"이라고 읽지만 Enter·Space는 아무 일도 하지 않는다(ARIA APG "Read Me First": 역할은 키보드 동작을 주지 않는다).
- 더 넣을 것: `keydown`에서 Enter·Space를 받아 `click()`을 부르고, Space의 기본 스크롤을 `preventDefault()`로 막는다. 실험의 `#fixed`가 이렇게 해서 `clicks=["fixed","fixed"]`가 됐다.
- 더 나은 답은 `<button>`으로 바꾸는 것이다(Using ARIA 첫째 규칙).

### 4. 빈 정지점

- 접근성 트리: `role=none`, `ignored=true` — 트리에서 빠진다.
- Tab 순서: 그대로 들어 있다(실험 Tab 순서의 `... rolebtn -> ghost -> iconbtn ...`).
- 사용자는 Tab으로 포커스가 갔는데 접근성 트리에는 없는(읽을 역할·이름이 없는) 자리를 만난다. 실제 발화는 실험하지 않았다 — W3C ACT 규칙은 보조 기술 사용자에게 혼란을 줄 수 있다고 한다.
- Using ARIA의 넷째 규칙(포커스 가능한 요소에 `role="presentation"`이나 `aria-hidden="true"`를 쓰지 않는다)을 어겼다. axe-core는 `aria-hidden-focus`로 잡았다.

### 5. 양수 tabindex

- 첫 Tab은 DOM 맨 끝의 `tabindex=3` 입력칸으로 간다. 실험의 Tab 순서가 `pos -> btn -> ...`였다.
- HTML 표준의 순차 포커스 순서는 양수 `tabindex`를 먼저(값 오름차순), 그다음 0·기본 포커스 요소를 DOM 순서로 둔다.
- 문제: 화면 읽기 순서와 Tab 순서가 어긋난다(SC 2.4.3 Focus Order). 다른 곳에 양수 값을 하나 더 넣으면 전체 순서를 다시 맞춰야 한다. axe `tabindex` 규칙이 경고한다.

### 6. 자동 검사의 범위

- 잡은 것(axe-core 4.13.0): `aria-hidden-focus`(#ghost), `button-name`(#iconbtn), `label`(#pos), `tabindex`(#pos).
- 놓친 것: `#divbtn`(클릭되는 div), `#rolebtn`(Enter·Space 미구현), `#nohref`(href 없는 링크).
- 이유: 정적 DOM·접근성 트리만 보고는 "이 div가 클릭을 받는 버튼 노릇을 한다"거나 "키를 누르면 동작한다"를 판단하기 어렵다. 실제로 키를 눌러 보는 동작 검사가 필요하다(해석).

### 7. 이름 계산

- 대략 `aria-labelledby` → `aria-label` → 네이티브 출처(`<label>`, 버튼 안쪽 글자, `alt`) → `title`·`placeholder` 순으로 처음 나온 값을 쓴다(AccName 1.2, HTML-AAM).
- `<button aria-label="닫기">X</button>` → 이름 "닫기"(보이는 "X"를 덮음). 실험 `#labeled: role=button name="닫기"`.
- `placeholder="이메일"`만 있는 입력 → 이름 "이메일"(실험 `#noLabel`). 이름은 있지만, 입력을 시작하면 placeholder가 사라져 무엇을 넣는 칸인지 화면에서 잃는다. 보이는 `<label>`이 필요하다(SC 3.3.2). axe는 이 경우를 `label` 위반으로 잡지 않았다.

### 8. SPA 전환 후 침묵

- 원인: 전체 페이지 로드가 없어 보조 기술에 새 문서를 알리는 일이 없다. 포커스는 사라진 링크 자리나 `body`에 남는다.
- 대처
  - 새 화면의 `<h1 tabindex="-1">`에 `focus()`를 옮긴다(Tab 순서에는 넣지 않고 스크립트로만 포커스).
  - `document.title`을 갱신한다.
  - 짧은 결과 알림은 `aria-live="polite"` 영역으로 보낸다.

### 9. aria-hidden만으로는 배경이 막히지 않는다

- `aria-hidden`은 접근성 트리에서만 숨긴다. 포커스 가능성은 그대로라 Tab이 배경 버튼으로 간다. 4번의 빈 정지점이 여러 개 생긴 셈이다.
- 고치기: 배경 컨테이너에 `inert` 속성을 건다(포커스·클릭·접근성 트리를 함께 막음). 또는 `<dialog>`를 `showModal()`로 연다 — 바깥이 inert가 되고 기본값(`closedby` 없음 = auto)이면 Esc 닫기도 따라온다. `closedby="none"`이나 `cancel` 이벤트 취소로 바꿀 수 있다.

### 10. WCAG 2.2 신설 AA 두 개

- 2.4.11 Focus Not Obscured (Minimum): 포커스를 받은 요소가 작성자가 만든 콘텐츠에 완전히 가려지면 안 된다. 고정 헤더·하단 쿠키 배너·채팅 위젯이 Tab으로 내려간 요소를 덮는 경우 깨진다. `scroll-padding`으로 띄운다.
- 2.5.8 Target Size (Minimum): 포인터 대상은 24×24 CSS px 이상(간격·동등 대체·인라인·UA 기본·필수 예외). 작은 아이콘 버튼이 촘촘히 붙은 툴바·표 안 아이콘에서 깨진다.
