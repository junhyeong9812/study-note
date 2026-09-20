# HTML — 문법·API 주제 목록

> 1단계 리스트업이다. 아래 주제들의 3파일(질문·서머리·정답)은 **아직 없다**.
> 기준 소스: [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) (단일 기준 — 「HTML5」라는 버전은 더 이상 기준이 아니다) · [콘텐츠 카테고리 절](https://html.spec.whatwg.org/multipage/dom.html#kinds-of-content) · [WHATWG DOM Standard](https://dom.spec.whatwg.org/) (접근성·트리 규칙의 뿌리) · [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)·[ARIA in HTML](https://www.w3.org/TR/html-aria/) (접근성 갈래) · [MDN HTML 레퍼런스](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference) (표면 확인용) · 지원 상태는 [Web Platform Status(`webstatus.dev`)](https://webstatus.dev/) 의 Baseline 데이터를 API 로 조회해 확인했다.
> 실행 검증: **가능**. 이 머신에 **Google Chrome 151.0.7922.173** 과 **Mozilla Firefox 155.0.1** 이 설치돼 있다. `google-chrome --headless --dump-dom` 으로 **파서가 만든 실제 DOM 트리**를, `--screenshot` 으로 렌더 결과를 뽑는 것을 실제로 돌려 확인했다. 파싱·오류 복구(`03`)와 콘텐츠 모델(`05`)은 `--dump-dom` 으로 눈에 보이게 검증할 수 있다. **막히는 것**: 스크린리더(NVDA·VoiceOver)가 없어 **접근성 트리가 실제로 어떻게 읽히는지는 실행 확인이 불가**하다 — Chrome 의 접근성 트리 덤프까지만 쓰고, 「스크린리더가 이렇게 읽는다」는 서술은 명세·ARIA 문서로만 접지하고 「미실행」으로 표기한다. WebKit(Safari)도 없다.\
> ⚠️ **2026-09-21 정정 — 렌더 검증은 Chrome 단일 엔진이다.** Firefox 155.0.1 은 설치돼 있으나 이 환경에서 **headless 스크린샷이 산출되지 않는다** (전용 프로파일로도 `exit 0` 으로 끝나며 파일을 만들지 않는 **조용한 실패**). 따라서 크로스 브라우저 차이를 주장할 때는 Baseline 데이터로만 접지하고, 「두 엔진에서 확인했다」고 적지 않는다.
> 기준일 2026-09-21.

## 이 언어에서 무엇을 자르는 축

HTML 은 태그 목록이 아니다. 명세 자신이 태그를 「종류」로 묶지 않고 **콘텐츠 카테고리**(흐름·구절·구획·헤딩·임베드·대화형)로 묶어 「어느 요소 안에 어느 요소를 넣을 수 있는가」를 정의한다. 그래서 축의 첫째는 **문서 구조** — 문서의 뼈대, 파서가 태그 수프를 트리로 바꾸는 규칙, 그리고 콘텐츠 모델이다. `<p>` 안에 `<div>` 를 넣으면 왜 `<p>` 가 닫혀 버리는지는 태그를 외워서는 답할 수 없고, 콘텐츠 모델과 파서 규칙을 알아야 답할 수 있다.

둘째 **시맨틱** 은 「무엇으로 감쌀 것인가」다. 여기서 중요한 것은 요소 이름의 사전적 뜻이 아니라 **그 요소가 무료로 주는 것** — 암묵 역할·키보드 동작·접근 가능한 이름이다. 그래서 시맨틱과 **접근성**(다섯째 축)은 사실상 한 몸이고, 이 목록은 접근성을 「나중에 얹는 것」이 아니라 **네이티브 시맨틱이 이미 준 것을 어떻게 깨뜨리지 않느냐**의 문제로 세웠다. ARIA 갈래의 핵심 주제(`42`)가 「ARIA 를 **언제 쓰지 말아야 하나**」인 것이 그 때문이다.

셋째 **폼** 을 가장 두껍게(13주제) 잡았다. HTML 명세에서 폼(4.10절)이 가장 큰 절인 것과 같은 이유다 — 입력 타입마다 파싱·검증·모바일 키보드·접근성이 전부 다르고, 실무에서 마크업이 가장 많이 틀리는 자리이기도 하다. 넷째 **미디어·임베드** 는 반응형 이미지와 샌드박싱처럼 **마크업만으로 성능·보안이 갈리는** 표면이다. 여섯째 **메타·SEO** 는 눈에 안 보이지만 문서의 해석을 바꾸는 `<head>` 의 층이다.

**경계 두 개를 분명히 한다.**
- **아래로**: 「언제 들어왔나」는 [`history/web/01-웹-탄생-HTML.md`](../../../../../history/web/01-웹-탄생-HTML.md)·[`03-HTML-CSS-진화.md`](../../../../../history/web/03-HTML-CSS-진화.md)(XHTML 의 좌초, WHATWG 의 반란, HTML5) 의 몫이다. 여기는 **어떻게 쓰고 무엇을 못 하나**만이다.
- **옆으로**: **스크립트로 하는 일은 전부 JS 쪽**이다. `document.querySelector`·이벤트 리스너·`dialog.showModal()`·`customElements.define()`·`popover` 를 JS 로 여는 것은 여기서 다루지 않는다. 이 목록은 **마크업과 시맨틱까지**이고, 스크립트 표면이 필요한 자리는 「여기까지가 마크업」이라고 경계를 적어 둔다. 스타일링은 [`../../css/syntax/README.md`](../../css/syntax/README.md).

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 렌더 | 우선 |
|---|------|------|----------------------|------|-----------|------|------|
| 01 | HTML 문서의 뼈대 — `<!DOCTYPE html>`·`<html lang>`·`<head>`/`<body>` 의 필수 요소 | 문서 구조 | DOCTYPE 이 오늘 하는 유일한 일(표준 모드 전환)과 `<head>` 에 반드시 있어야 하는 것을 설명할 수 있다 | — | [`../../../../../history/web/01-웹-탄생-HTML.md`](../../../../../history/web/01-웹-탄생-HTML.md) (버전 없는 시작) | 불필요 | A |
| 02 | 요소와 속성 문법 — 빈 요소·태그 생략·불리언 속성·따옴표 규칙 | 문서 구조 | `<br />` 의 슬래시가 아무 일도 안 한다는 것, `disabled="false"` 가 왜 비활성인지 설명할 수 있다 | 01 | — | 도움 | A |
| 03 | 파서와 오류 복구 — 태그 수프가 트리가 되는 과정·암묵 태그 삽입 | 문서 구조 | `<p><div>` 나 닫지 않은 `<li>` 가 어떤 DOM 트리가 되는지 예측하고, HTML 파서가 왜 절대 에러로 멈추지 않는지 설명할 수 있다 | 02 | [`../../../compiler-pipeline/`](../../../compiler-pipeline/) (파서 일반론) · [`../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../history/web/03-HTML-CSS-진화.md) (XHTML 의 엄격함이 좌초한 이유) | 필수 | B |
| 04 | 공백·텍스트·문자 참조 — 공백 축약·엔티티·`<pre>` | 문서 구조 | 소스의 줄바꿈·연속 공백이 화면에서 하나로 합쳐지는 규칙과 `&amp;`·`&nbsp;` 를 써야 하는 자리를 판단할 수 있다 | 03 | [`../../../data-representation/`](../../../data-representation/) (유니코드·인코딩) | 필수 | B |
| 05 | 콘텐츠 카테고리와 콘텐츠 모델 — 어디에 무엇을 넣을 수 있나 | 문서 구조 | 흐름·구절·구획·헤딩·임베드·대화형 카테고리로 임의의 중첩이 유효한지 판정할 수 있다 | 03 | — | 도움 | A |
| 06 | 전역 속성 — `id`/`class`/`title`/`hidden`/`data-*`/`contenteditable`/`translate` | 문서 구조 | 모든 요소에 붙는 속성이 각각 무엇을 바꾸는지와 `data-*` 가 DOM 에 어떻게 노출되는지 설명할 수 있다 | 02 | — | 도움 | A |
| 07 | `id` 와 조각 식별자 — 문서 내 링크·`:target`·스크롤 앵커 | 문서 구조 | URL 의 `#fragment` 가 무엇을 찾고 못 찾으면 어떻게 되는지, `id` 중복이 만드는 결과를 예측할 수 있다 | 06 | — | 필수 | B |
| 08 | 스크립트 로딩 — `defer`/`async`/`type=module`/`nomodule`·배치 위치 | 문서 구조 | 네 조합의 다운로드·실행 시점을 파싱과 겹쳐 그리고, 실행 순서 보장이 있는 쪽과 없는 쪽을 판정할 수 있다 | 03 · JS 42 | [`../../js/syntax/README.md`](../../js/syntax/README.md) 42·44 (ESM·동적 `import`) | 도움 | A |
| 09 | 스타일시트·리소스 힌트 연결 — `<link rel>`·`media`·`preload`/`preconnect`/`modulepreload` | 문서 구조 | 스타일시트가 렌더를 막는다는 것과 `media` 로 그 차단을 비껴가는 법, 힌트를 남용했을 때의 역효과를 판단할 수 있다 | 08 | [`../../css/syntax/README.md`](../../css/syntax/README.md) (연결된 뒤의 이야기) | 도움 | B |
| 10 | `template`·`slot`·선언적 Shadow DOM·커스텀 요소 맛보기 | 문서 구조 | `<template>` 안의 내용이 왜 파싱은 되는데 렌더되지 않는지, 슬롯이 라이트 DOM 을 어디로 투영하는지 설명할 수 있다 | 05 · JS 16 | [`../../../../../history/web/05-웹플랫폼-API.md`](../../../../../history/web/05-웹플랫폼-API.md) §6 (웹 컴포넌트의 등장) | 필수 | C |
| 11 | 구획 요소와 랜드마크 — `main`/`header`/`footer`/`nav`/`aside`/`section`/`article`/`search` | 시맨틱 | 각 요소의 암묵 랜드마크 역할을 대고, `section` 이 이름 없으면 랜드마크가 아니라는 것을 판단할 수 있다 | 05 | — | 도움 | A |
| 12 | 제목 레벨과 문서 개요 — `h1`~`h6` 가 실제로 계산되는 방식 | 시맨틱 | 「구획 요소가 제목 레벨을 자동으로 낮춰 준다」가 왜 구현되지 않았는지와 그래서 레벨을 손으로 맞춰야 한다는 것을 설명할 수 있다 | 11 | — | 도움 | A |
| 13 | 구절 시맨틱 — `strong`/`em`/`b`/`i`/`mark`/`small`/`code`/`kbd`/`samp`/`abbr` | 시맨틱 | 같은 굵게·기울임으로 보이는 두 요소 중 어느 쪽을 쓸지 「의미가 있나 없나」로 판정할 수 있다 | 05 | — | 필수 | A |
| 14 | 인용·편집·시각 — `blockquote`/`q`/`cite`·`ins`/`del`·`time` | 시맨틱 | `cite` 가 저작물 제목이지 사람 이름이 아니라는 것과 `time datetime` 의 기계 판독 형식을 쓸 수 있다 | 13 | — | 도움 | B |
| 15 | 목록 — `ul`/`ol`(`start`·`reversed`·`value`)/`dl` | 시맨틱 | 세 목록이 각각 무엇을 주장하는지와 `dl` 의 여러 `dt`/`dd` 묶음 규칙을 설명할 수 있다 | 05 | — | 필수 | A |
| 16 | 링크 — `href` 의 형태·`target`·`rel`(`noopener`/`noreferrer`/`nofollow`)·`download` | 시맨틱 | `target="_blank"` 가 왜 `rel="noopener"` 를 요구했고 지금은 왜 기본인지, 링크와 버튼이 갈리는 기준을 판단할 수 있다 | 07 | [`../../../../../history/web/02-HTTP-진화.md`](../../../../../history/web/02-HTTP-진화.md) (URL·요청 모델) | 도움 | A |
| 17 | 표 구조 — `table`/`thead`/`tbody`/`tfoot`/`caption`/`colgroup` | 시맨틱 | 파서가 `tbody` 를 자동으로 끼워 넣는 것과 `caption` 이 표의 접근 가능한 이름이 되는 것을 설명할 수 있다 | 03, 05 | — | 필수 | A |
| 18 | 표 헤더 연결 — `th`·`scope`·`headers`/`id`·`rowspan`/`colspan` | 시맨틱 | 복합 헤더 표에서 각 셀이 어느 헤더에 묶이는지 `scope` 와 `headers` 로 설계하고, 레이아웃용 표를 배제할 수 있다 | 17 | — | 도움 | A |
| 19 | `figure`/`figcaption`·`address`·`hr`·`details` 밖의 잡다한 구조 | 시맨틱 | 캡션이 그림에 묶인다는 것과 `address` 가 「연락처」지 「주소」가 아니라는 좁은 의미를 판단할 수 있다 | 11 | — | 도움 | B |
| 20 | `lang`·`dir` 과 양방향 텍스트 — `dir=auto`·`bdi`/`bdo` | 시맨틱 | `lang` 이 음성 합성·글꼴 선택·하이픈에 미치는 영향과 사용자 입력 문자열이 RTL 일 때 UI 가 깨지는 것을 `bdi` 로 막을 수 있다 | 13 | [`../../../data-representation/`](../../../data-representation/) (유니코드) · [`../../css/syntax/README.md`](../../css/syntax/README.md) 32 (논리 속성) | 필수 | B |
| 21 | `<form>` 의 제출 모델 — `action`/`method`/`enctype`·제출을 일으키는 것 | 폼 | GET 과 POST 제출이 데이터를 어디에 싣는지, 엔터 키가 암묵 제출을 일으키는 조건을 설명할 수 있다 | 05 | [`../../../../../history/web/02-HTTP-진화.md`](../../../../../history/web/02-HTTP-진화.md) (메서드·본문) | 도움 | A |
| 22 | `<input>` 타입 지도 ① 텍스트 계열 — `text`/`password`/`email`/`url`/`tel`/`search` | 폼 | 타입마다 달라지는 것(모바일 키보드·기본 검증·자동완성)을 대고, `tel` 에 기본 검증이 없는 이유를 설명할 수 있다 | 21 | — | 필수 | A |
| 23 | `<input>` 타입 지도 ② 숫자·날짜 — `number`/`range`/`date`/`time`/`datetime-local`/`month`/`week` | 폼 | 값이 항상 **로케일 무관 형식**으로 제출된다는 것과 `number` 에 전화번호를 쓰면 안 되는 이유를 판단할 수 있다 | 22 | — | 필수 | A |
| 24 | `<input>` 타입 지도 ③ 선택·특수 — `checkbox`/`radio`/`file`/`color`/`hidden`/`submit`/`image` | 폼 | 라디오 그룹이 `name` 으로 묶인다는 것과 체크 안 된 체크박스가 아예 제출되지 않는 것을 예측할 수 있다 | 22 | — | 필수 | A |
| 25 | `label` 연결과 폼 필드 이름 — `for`/`id`·감싸기·클릭 위임 | 폼 | 라벨을 연결하는 두 방법과 각각의 제약, 연결이 끊겼을 때 무엇이 사라지는지(클릭 타깃·접근 가능한 이름) 설명할 수 있다 | 22 | — | 필수 | A |
| 26 | `select`/`option`/`optgroup`·`datalist`·`textarea` | 폼 | `select` 다중 선택의 제출 형태와 `datalist` 가 자유 입력을 막지 못한다는 것, `textarea` 값이 속성이 아닌 자식 텍스트인 것을 설명할 수 있다 | 24 | — | 필수 | A |
| 27 | `fieldset`/`legend` 와 그룹 비활성화 | 폼 | 라디오 그룹의 접근 가능한 이름을 `legend` 로 주는 형태와 `fieldset[disabled]` 가 자손 전체에 퍼지는 것을 설명할 수 있다 | 25 | — | 필수 | B |
| 28 | 검증 속성 — `required`/`pattern`/`min`/`max`/`step`/`minlength`/`maxlength` | 폼 | 각 속성이 어느 타입에서만 의미를 갖는지와 `step` 이 `min` 을 기준으로 눈금을 만드는 것을 예측할 수 있다 | 23 | — | 필수 | A |
| 29 | 제약 검증 — 유효성 상태·`novalidate`·`:valid`/`:user-invalid` 의 관계 | 폼 | 마크업이 만든 유효성 상태를 CSS 가 읽는 경로와, 클라이언트 검증이 **서버 검증을 대체하지 못한다**는 경계를 판단할 수 있다 | 28 | [`../../css/syntax/README.md`](../../css/syntax/README.md) 10 (폼 의사 클래스) · JS 쪽 `checkValidity()`/`setCustomValidity()` 는 이 목록 밖 | 도움 | B |
| 30 | 폼 상태·입력 보조 속성 — `disabled`/`readonly`/`autofocus`/`autocomplete`/`inputmode` | 폼 | `disabled` 와 `readonly` 가 제출·포커스·검증에서 갈리는 세 지점과 `autocomplete` 토큰이 왜 접근성 항목인지 설명할 수 있다 | 24 | — | 필수 | A |
| 31 | 파일 업로드 — `accept`/`multiple`/`capture` 와 `enctype=multipart/form-data` | 폼 | `accept` 가 필터일 뿐 보장이 아니라는 것과 파일 제출에 `multipart` 가 필요한 이유를 설명할 수 있다 | 21, 24 | — | 필수 | B |
| 32 | `button` 의 `type` 과 폼 소유권 — `form` 속성·`formaction`/`formmethod` | 폼 | 폼 안 `<button>` 의 기본 타입이 `submit` 이라 생기는 사고와, 폼 밖 컨트롤을 `form` 속성으로 묶는 법을 설명할 수 있다 | 21 | — | 도움 | B |
| 33 | `output`·`progress`·`meter` | 폼 | 세 요소의 의미가 갈리는 지점(계산 결과 / 진행 / 범위 내 측정값)과 암묵 라이브 영역 성질을 판단할 수 있다 | 25 | — | 필수 | C |
| 34 | `img` — `alt`·`width`/`height`·`loading`/`decoding`/`fetchpriority` | 미디어·임베드 | `width`/`height` 를 적는 것이 오늘 하는 일(레이아웃 시프트 예약)과 `loading=lazy` 를 쓰면 안 되는 이미지를 판단할 수 있다 | 05 | [`../../css/syntax/README.md`](../../css/syntax/README.md) 31·44 (`aspect-ratio`·`object-fit`) | 필수 | A |
| 35 | 반응형 이미지 — `srcset`/`sizes` 의 두 서술자(`w`·`x`) | 미디어·임베드 | `sizes` 가 무엇을 브라우저에 알려 주는지와 `w` 서술자와 `x` 서술자를 언제 나눠 쓰는지 설계할 수 있다 | 34 | — | 필수 | A |
| 36 | `picture` — 아트 디렉션과 포맷 대체 | 미디어·임베드 | `srcset` 만으로 안 되고 `picture` 가 필요한 두 경우(다른 자르기 / 다른 포맷)를 판별할 수 있다 | 35 | — | 필수 | B |
| 37 | `video`/`audio` — `source`·자막 `track`·`preload`/`autoplay` 정책·`poster` | 미디어·임베드 | 브라우저가 `source` 목록을 고르는 방식과 자동재생이 차단되는 조건(소리 있는 재생)을 예측할 수 있다 | 34 | — | 필수 | B |
| 38 | `iframe` 과 `sandbox`·`allow`·`referrerpolicy`·`loading` | 미디어·임베드 | `sandbox` 가 기본으로 무엇을 다 끄는지와 토큰을 되돌려 켜는 방식, `allow-scripts allow-same-origin` 조합의 위험을 판단할 수 있다 | 34 | [`../../../security/`](../../../security/) (출처·격리) | 필수 | A |
| 39 | 인라인 SVG 와 `canvas` 의 자리 — 마크업 관점 | 미디어·임베드 | 아이콘을 인라인 SVG 로 넣을 때와 `img` 로 넣을 때 무엇이 달라지는지(스타일링·접근성), `canvas` 가 접근성 트리에 아무것도 안 남긴다는 것을 판단할 수 있다 | 34 | [`../../../../../history/web/05-웹플랫폼-API.md`](../../../../../history/web/05-웹플랫폼-API.md) §3 | 필수 | C |
| 40 | `object`/`embed`·`map`/`area` — 남아 있는 임베드 표면 | 미디어·임베드 | 오늘도 쓸 자리(PDF 임베드·이미지 맵)와 레거시로 봐야 할 자리를 구분할 수 있다 | 38 | — | 도움 | C |
| 41 | 네이티브 시맨틱이 주는 것 — 암묵 역할·이름·상태·키보드 동작 | 접근성 | `<button>` 하나가 무료로 주는 네 가지(역할·포커스·엔터/스페이스·활성 상태)를 대고, `<div onclick>` 이 그중 무엇을 잃는지 판정할 수 있다 | 11, 25 | — | 도움 | A |
| 42 | ARIA 를 언제 쓰지 말아야 하나 — 다섯 규칙과 역할 덮어쓰기 | 접근성 | 「ARIA 없는 것이 나쁜 ARIA 보다 낫다」가 무슨 뜻인지 구체 사례로 설명하고, `role` 이 암묵 역할을 덮어쓸 때 무엇이 함께 사라지는지 예측할 수 있다 | 41 | — | 도움 | A |
| 43 | 접근 가능한 이름 계산 — `alt`·`label`·`aria-label`/`aria-labelledby`·내용의 우선순위 | 접근성 | 같은 요소에 여러 이름 출처가 붙었을 때 어느 것이 이기는지 순서대로 계산할 수 있다 | 42 | — | 도움 | A |
| 44 | `alt` 판단 — 정보·장식·기능 이미지 세 갈래 | 접근성 | 임의의 이미지를 받아 `alt` 에 무엇을 쓸지(또는 빈 문자열로 둘지) 그 이미지가 하는 일로 판정할 수 있다 | 34, 43 | — | 도움 | A |
| 45 | 포커스 — `tabindex` 값의 의미·포커스 순서·`inert` | 접근성 | `tabindex="0"`·`-1`·양수가 각각 무엇을 하는지와 양수를 쓰면 안 되는 이유, `inert` 로 화면 뒤를 통째로 빼는 법을 설명할 수 있다 | 41 | — | 필수 | A |
| 46 | 라이브 영역과 상태 전달 — `aria-live`/`aria-expanded`/`aria-current`/`aria-describedby` | 접근성 | 화면에서만 보이는 상태 변화를 보조 기술에 전달하는 형태를 설계하고 `assertive` 남용의 대가를 판단할 수 있다 | 43 | — | 불필요 | B |
| 47 | `dialog` — 모달·비모달·포커스 트랩·`::backdrop`·닫기 동작 | 접근성 | `open` 속성으로 연 것과 모달로 연 것이 포커스·최상위 레이어에서 갈리는 것을 설명할 수 있다 (여는 동작 자체는 JS 표면) | 45 | [`../../css/syntax/README.md`](../../css/syntax/README.md) 22 (최상위 레이어·쌓임) | 필수 | A |
| 48 | `details`/`summary` 와 `popover` 속성 | 접근성 | 스크립트 없이 여닫는 두 표면의 차이(콘텐츠 공개 / 떠 있는 레이어)와 `popover` 의 가벼운 닫기(light dismiss)를 판단할 수 있다 | 47 | — | 필수 | B |
| 49 | 그 밖의 접근성 표면 — 건너뛰기 링크·`accesskey`·`hidden="until-found"`·`aria-hidden` 의 경계 | 접근성 | 시각적으로 숨기는 것과 접근성 트리에서 빼는 것이 다른 일임을 구분하고 네 수단을 골라 쓸 수 있다 | 45, 46 | — | 도움 | C |
| 50 | `meta` 계열 — `charset`·`viewport`·`description`·`robots`·`theme-color` | 메타·SEO | `charset` 이 왜 문서 맨 앞 1024바이트 안에 있어야 하는지와 `viewport` 없이는 모바일에서 무슨 일이 일어나는지 설명할 수 있다 | 01 | [`../../css/syntax/README.md`](../../css/syntax/README.md) 38 (미디어 쿼리가 작동하려면) | 필수 | A |
| 51 | `http-equiv` 와 문서 수준 정책 힌트 — `refresh`·`content-security-policy`·`referrer` | 메타·SEO | 메타로 줄 수 있는 것과 반드시 HTTP 헤더여야 하는 것을 구분하고 `refresh` 가 접근성에서 배제되는 이유를 판단할 수 있다 | 50 | [`../../../security/`](../../../security/) | 불필요 | C |
| 52 | Open Graph·트위터 카드와 구조화 데이터의 자리 | 메타·SEO | OG 가 **W3C/WHATWG 표준이 아니라 플랫폼 관례**라는 것과 `application/ld+json` 구조화 데이터가 들어가는 자리를 구분할 수 있다 | 50 | — | 불필요 | B |
| 53 | 정규 URL·`hreflang`·`link rel` 관계 지도 | 메타·SEO | 같은 내용이 여러 URL 로 노출될 때 `rel=canonical` 이 무엇을 주장하는지와 `rel` 토큰 전체 지도를 설명할 수 있다 | 16, 50 | — | 불필요 | B |

**53주제** (문서 구조 10 · 시맨틱 10 · 폼 13 · 미디어·임베드 7 · 접근성 9 · 메타·SEO 4)
**우선** A 30 · B 17 · C 6
**렌더** 필수 28 · 도움 20 · 불필요 5

- **분류** — `문서 구조` / `시맨틱` / `폼` / `미디어·임베드` / `접근성` / `메타·SEO` 중 하나
- **무엇을 인출하게 되나** — 한 줄. 「~를 안다」가 아니라 **「~를 설명·예측·판단할 수 있다」**
- **선행** — 먼저 봐야 하는 주제 번호(없으면 `—`). HTML 안의 선행은 모두 자기보다 작은 번호라 순환이 없다. `JS NN` 은 [`../../js/syntax/README.md`](../../js/syntax/README.md) 의 주제 번호다
- **렌더** — 이 주제가 **화면에서 눈으로 봐야 이해되는가**. `필수` / `도움` / `불필요`. HTML 은 CSS 와 달리 **「DOM 트리를 봐야 하는 것」**(03·05)과 **「접근성 트리를 들어야 하는 것」**(46)이 섞여 있어, 렌더 칸이 `도움`·`불필요` 인 주제라도 **덤프 도구는 필요하다**
- **우선** — `A`(핵심·먼저) / `B`(중요) / `C`(나중에)

## 기존 주제와 겹치는 것

| 겹치는 주제 | 기존에 있는 것 | 새 주제를 어떻게 좁혔나 |
|---|---|---|
| 01 문서 뼈대 · 03 파서·오류 복구 | [`history/web/01-웹-탄생-HTML.md`](../../../../../history/web/01-웹-탄생-HTML.md) · [`03-HTML-CSS-진화.md`](../../../../../history/web/03-HTML-CSS-진화.md) §1.1~1.6 — 버전 없는 시작, HTML 2.0~4.01, **XHTML 의 엄격함이 좌초한 이유**, WHATWG 의 반란, HTML5 | 「왜 관대한 파서가 됐나」는 거기. 여기는 **그 관대함이 오늘 만드는 구체 결과** — `<p><div>` 가 어떤 트리가 되는지, 어떤 태그가 암묵으로 삽입되는지 |
| 10 웹 컴포넌트 · 39 SVG·canvas | [`history/web/05-웹플랫폼-API.md`](../../../../../history/web/05-웹플랫폼-API.md) §3·§6 — 멀티미디어와 컴포넌트가 표준이 된 경위 | 도입 맥락은 거기. 여기는 **마크업 표면만** — `<template>` 이 렌더되지 않는 성질, 슬롯 투영, 인라인 SVG 의 스타일링·접근성 대가 |
| 16 링크 · 21 폼 제출 | [`history/web/02-HTTP-진화.md`](../../../../../history/web/02-HTTP-진화.md) — 메서드·헤더·URL 모델의 진화 | 프로토콜은 거기. 여기는 **마크업이 그 요청을 어떻게 만드느냐** — `method`/`enctype` 이 본문 형식을 바꾸는 것까지 |
| 03 파서 | [`foundations/compiler-pipeline/`](../../../compiler-pipeline/) — 렉서·파서·AST 일반론 | 파싱 일반론은 거기. 여기는 **에러로 멈추지 않는 파서**라는 HTML 고유 설계와 삽입 모드 |
| 04 문자 참조 · 20 양방향 텍스트 | [`foundations/data-representation/`](../../../data-representation/) — 유니코드·인코딩 | 인코딩 원리는 거기. 여기는 **`charset` 선언 위치·엔티티 문법·`bdi` 라는 마크업 수단** |
| 38 `iframe` sandbox · 51 `http-equiv` | [`foundations/security/`](../../../security/) — 보안 일반 | 위협 모델은 거기. 여기는 **마크업 속성이 그 경계를 어디까지 그을 수 있나**(그리고 메타로는 못 하는 것) |
| 41~49 접근성 | [`cs/engineering/development-standards/quality-standards/`](../../../../engineering/development-standards/quality-standards/) — ISO 25010 의 포용성(inclusivity)·사용자 지원 항목 | 품질 모델의 어휘만 거기 있고 **HTML 의 접근성 표면은 저장소 어디에도 없다**. 이 갈래 9주제가 그 공백을 채운다 |
| 08 스크립트 로딩 | [`../../js/syntax/README.md`](../../js/syntax/README.md) 42·44 — ESM 모듈, 동적 `import`·top-level `await` | 모듈 **의미론**은 거기. 여기는 **`<script>` 속성 조합이 만드는 다운로드·실행 타이밍**만 |
| 09 스타일시트 연결 · 29 검증 상태 · 34 이미지 크기 · 47 dialog | [`../../css/syntax/README.md`](../../css/syntax/README.md) | 스타일 규칙은 전부 CSS 목록. 여기는 **마크업이 CSS 에 넘겨주는 훅**(유효성 상태·`aspect-ratio` 의 재료·최상위 레이어)까지 |

## 뺀 것과 이유

**있는데 뺀 것**이다. 없어서 안 넣은 것이 아니다.

| 뺀 것 | 이유 |
|---|---|
| **DOM 조작 API 전부** — `querySelector`·`createElement`·`classList`·`dataset` | 마크업이 아니라 **스크립트 표면**이다. 규칙 그대로 JS 쪽으로 보낸다 |
| **이벤트** — 리스너 등록·버블링/캡처링·위임·`preventDefault` | 같은 이유. HTML 은 이벤트를 **일으키는 요소**(`21` 제출 트리거·`41` 네이티브 키보드 동작)까지만 다룬다 |
| 제약 검증 **API 호출** — `checkValidity()`·`reportValidity()`·`setCustomValidity()`·`ValidityState` | `29` 는 **속성이 만드는 유효성 상태와 CSS 가 그것을 읽는 경로**까지다. 호출 표면은 JS 이고, 현재 JS 목록에도 없다(아래 교차 대조 참조) |
| `dialog.showModal()`·`popover` 의 JS 제어·`customElements.define()`·`attachShadow()` | 같은 경계. `47`·`48`·`10` 은 **마크업으로 되는 데까지**만 — `open` 속성, `popover`/`popovertarget` 속성, 선언적 Shadow DOM |
| `fetch`·`XMLHttpRequest`·`FormData`·스토리지·Service Worker·WebSocket | 호스트 API 다. [`history/web/05-웹플랫폼-API.md`](../../../../../history/web/05-웹플랫폼-API.md) 가 「무엇이 생겼나」를 다루고, 쓰는 법은 이 목록 밖 |
| 마이크로데이터(`itemscope`/`itemprop`, 명세 5절) | 실무에서 JSON-LD 에 밀렸다. `52` 에서 구조화 데이터의 자리로만 언급 |
| `contenteditable` 로 만드는 리치 에디터·`designMode`·드래그 앤 드롭 | 전부 **스크립트와 한 몸**인 기능이다. `06` 에서 전역 속성으로만 언급 |
| 폐기 요소(`<font>`·`<center>`·`<marquee>`)와 프레임셋 | [`history/web/03`](../../../../../history/web/03-HTML-CSS-진화.md) §1.3 의 「표현 태그의 전성기, 그리고 후회」가 다룬다. 새로 배워 쓸 문법이 아니다 |
| XHTML 직렬화·XML 구문(명세 14절) | 오늘 새로 쓰지 않는다. `03` 에서 「왜 엄격 파싱이 좌초했나」로만 |
| 웹 접근성 **검사 도구**(axe·Lighthouse)와 WCAG 성공 기준 전문 | 도구·규격 문서다. 이 목록은 **HTML 이 주는 접근성 표면**에 한정한다. WCAG 전반은 필요하면 별도 갈래로 제안 |
| SEO 전략·검색엔진 랭킹 | 마크업이 아니라 마케팅이다. `50`·`52`·`53` 은 **마크업이 선언하는 것**까지만 |
| 이메일 HTML·AMP | 별개 프로파일이다 |

## HTML ↔ JS 교차 대조

[`../../js/syntax/README.md`](../../js/syntax/README.md) 52주제를 전수로 읽고 대조했다. 결과는 **겹치는 주제 0** 이다. 이유와 경계는 아래와 같다.

| 확인한 것 | 결과 |
|---|---|
| JS 목록에 DOM·이벤트 주제가 있나 | **없다.** JS 목록은 「뺀 것과 이유」에서 **DOM·브라우저 API(이벤트·fetch·스토리지·Web Workers)를 명시적으로 제외**하고 ECMA-262 언어 기능만 다룬다. 예외로 남긴 호스트 API 는 `AbortController`(JS 41)·`structuredClone`(JS 48) 둘뿐이다 |
| 그래서 HTML 에서 뺀 스크립트 주제는 어디로 가나 | **양쪽 다 없는 공백이다.** DOM 조작·이벤트·`dialog.showModal()`·`customElements.define()`·제약 검증 API 호출·`HTMLMediaElement` 제어는 **HTML 목록에도 JS 목록에도 없다.** 이 대조의 가장 중요한 결론이고, 2단계 전에 사용자 판단이 필요한 지점이다 — 「웹 플랫폼 API」를 별도 갈래로 세울지, JS 목록을 확장할지 |
| HTML 주제가 JS 를 선행으로 거는 곳 | **2곳.** `08` 스크립트 로딩 → **JS 42**(ESM 모듈)·**JS 44**(동적 `import`) / `10` 템플릿·커스텀 요소 → **JS 16**(`class` 문법). 둘 다 「HTML 속성이 무엇을 하는가」만 여기서 다루고 모듈 의미론·클래스 문법은 JS 에 맡긴다 |
| 반대 방향 — JS 가 HTML 을 전제하는 곳 | JS 43(CJS↔ESM 상호운용)이 `type` 필드·확장자 해석을 다루는데, 이는 Node 쪽이라 HTML `<script type=module>`(`08`)과 **문맥이 다르다.** 중복 아님 |
| 이름이 비슷해 확인한 것 | JS 41 「취소와 타임아웃(`AbortController`)」 ↔ HTML 37 `video` 의 로딩 제어 — 표면이 완전히 다르다. JS 31 `JSON` ↔ HTML 52 JSON-LD — JSON-LD 는 **마크업 안에 놓이는 자리**만 다루므로 중복 아님 |

## 버전·지원 기준

HTML 에는 버전이 없다. WHATWG **Living Standard** 단일 기준이고, 「HTML5」는 [`history/web/03`](../../../../../history/web/03-HTML-CSS-진화.md) §1.6 이 다루는 **2014년의 한 시점**이지 오늘의 기준이 아니다. 그래서 버전 대신 **브라우저 Baseline** 으로 기준을 잡는다.

- **기준선**: Baseline **widely available** 인 것을 「그냥 써도 되는 것」으로 본다.
- **newly available** 인 것은 3파일에 **「Baseline newly, 저변 도달 시점 <날짜>」**를 명시한다.
- **limited** 인 것은 목록에서 뺐거나 한 줄 언급으로만 남기고, 그 사실을 적는다.

아래 값은 2026-09-21 에 [`api.webstatus.dev`](https://webstatus.dev/) 의 feature API 를 직접 조회해 받은 것이다. **추측하지 않았다.**

| 기능 | 이 목록의 주제 | Baseline | newly 된 날 | widely 된 날 |
|---|---|---|---|---|
| `<dialog>` | 47 | **widely** | 2022-03-14 | 2024-09-14 |
| `<details>` | 19, 48 | **widely** | 2020-01-15 | 2022-07-15 |
| 배타적 `<details name>` | 48 | **newly** | 2024-09-03 | — |
| `popover` 속성 | 48 | **newly** | 2025-01-27 | — |
| `<search>` | 11 | **widely** | 2023-10-13 | — |
| `inert` | 45 | **widely** | 2023-04-11 | 2025-10-11 |
| `srcset`/`sizes` | 35 | **widely** | 2017-03-27 | 2019-09-27 |
| `<picture>` | 36 | **widely** | 2016-03-21 | 2018-09-21 |
| `loading=lazy` (이미지·iframe) | 34, 38 | **widely** | 2023-12-19 | 2026-06-19 |
| 날짜·시간 `<input>` 타입 | 23 | **widely** | 2021-10-05 | 2024-04-05 |
| 제약 검증 API | 29 | **widely** | 2018-12-11 | — |
| `:user-valid`/`:user-invalid` | 29 | **widely** | 2023-11-02 | — |
| `<slot>` | 10 | **widely** | 2020-01-15 | 2022-07-15 |
| Shadow DOM | 10 | **widely** | 2020-01-15 | — |
| 선언적 Shadow DOM | 10 | **widely** | 2024-02-20 | 2026-08-20 |
| 자율 커스텀 요소 | 10 | **widely** | 2020-01-15 | — |
| 폼 연계 커스텀 요소 | 10 | **widely** | 2023-03-27 | — |
| `accesskey` | 49 | **widely** | 2015-07-29 | — |
| `<meta>` | 50 | **widely** | 2015-07-29 | — |

**limited 라서 언급으로만 남긴 것** (같은 조회)

| 기능 | Baseline | 상태와 처리 |
|---|---|---|
| `hidden="until-found"` | **limited** | `49` 안에서 「숨김의 네 수단」 중 하나로 한 줄만. 아직 기본 수단으로 가르치지 않는다 |
| Invoker commands (`command`/`commandfor`) | **newly** (2025-12-12) | `48` 에서 **버튼으로 `dialog`·popover 를 스크립트 없이 여는 최신 수단**으로 언급. newly 라 주제로 세우진 않았다 |
| 커스터마이즈 가능 `<select>`(`::picker()`) | **limited** | `26` 에서 「지금은 못 하는 것」의 반례로 한 줄 |
| `getHTML()` | **newly** (2024-09-16) | 스크립트 표면이라 이 목록 밖 |
| `referenceTarget` | **limited** | 웹 컴포넌트 접근성의 미해결 문제로 `10` 에서 한 줄 |

**확인하지 못한 것** — **Open Graph(`52`)** 는 `webstatus.dev` 조회 대상이 아니다. OG 는 W3C/WHATWG 표준이 아니라 **Meta 가 정의한 프로토콜**(`ogp.me`)이고 각 플랫폼 크롤러가 제각기 해석하므로, Baseline 개념 자체가 적용되지 않는다. `52` 의 3파일에는 **「표준이 아니다」는 사실 자체**를 인출 대상으로 넣는다. 그 밖의 행은 모두 API 응답에서 직접 읽은 값이다. 다만 **`webstatus.dev` 는 2차 집계**이고, 「명세가 무엇을 요구하나」는 WHATWG 본문으로, 「내 브라우저에서 실제로 되나」는 이 머신의 Chrome 151 · Firefox 155 로 각각 다시 확인한다. **Safari/WebKit 은 없다.**
