# 웹 플랫폼 API — 주제 목록

> 1단계 리스트업이다. **01\~08 은 3파일(질문·서머리·정답)이 있고**(2026-09-25 — 01\~04 첫 배치, 05\~08 이어진 배치), 나머지는 아직 없다.
> 첫 배치가 이 갈래의 형식을 굳혔다 — **관측 3창**(`--dump-dom` 트리 · `nodeType`/`length` 인벤토리 · **같은 것을 두 번 읽기**)에 주제마다 네 번째 창을 하나씩 더 세운다. 근거 블록은 전부 `capture.sh` → `assemble-blocks.py` 조립기로 넣었고 사람이 옮겨 적지 않는다.
> **검증은 Chrome 151 단일 엔진**이므로 3파일은 **이식성을 주장하지 않는다**(명세 문장을 근거로 드는 자리만 예외). `--virtual-time-budget` 은 쓰지 않았다.
> 이 갈래는 언어가 아니라 **플랫폼**이다 — 언어 문법은 [`../languages/`](../languages/) 에 있다.
> 기준 소스: [WHATWG DOM Standard](https://dom.spec.whatwg.org/) · [WHATWG HTML Living Standard — Web application APIs](https://html.spec.whatwg.org/multipage/webappapis.html) (스크립팅·수명주기·폼 제어 절) · [WHATWG Fetch](https://fetch.spec.whatwg.org/) · [WHATWG URL](https://url.spec.whatwg.org/) · [WHATWG Storage](https://storage.spec.whatwg.org/) · [WHATWG WebSockets](https://websockets.spec.whatwg.org/) · [W3C Service Workers](https://w3c.github.io/ServiceWorker/) · [W3C IndexedDB](https://w3c.github.io/IndexedDB/) · [W3C UI Events](https://w3c.github.io/uievents/) · [W3C Pointer Events](https://w3c.github.io/pointerevents/) · [Intersection Observer](https://www.w3.org/TR/intersection-observer/) · [Resize Observer](https://drafts.csswg.org/resize-observer/) · [Web Animations](https://drafts.csswg.org/web-animations-1/) · [HTML Canvas 절](https://html.spec.whatwg.org/multipage/canvas.html) · [W3C CSP](https://w3c.github.io/webappsec-csp/) · [W3C Permissions](https://w3c.github.io/permissions/) · [W3C Media Capture](https://w3c.github.io/mediacapture-main/) · [W3C Performance Timeline](https://w3c.github.io/performance-timeline/) · [WICG Scheduling APIs](https://wicg.github.io/scheduling-apis/) · 표면 확인용으로 [MDN Web API 레퍼런스](https://developer.mozilla.org/en-US/docs/Web/API) · 지원 상태는 [`api.webstatus.dev`](https://webstatus.dev/) 의 Baseline 데이터를 직접 조회해 확인했다(아래 지원 표).
> 실행 검증: **가능**. 이 머신에 **Google Chrome 151.0.7922.173** 과 **Mozilla Firefox 155.0.1** 이 있다. `google-chrome --headless --dump-dom` 으로 **스크립트를 실제로 돌린 뒤의 DOM** 을 뽑는 것을 확인했다 — 같은 `<p>` 를 `getElementsByTagName`(라이브)과 `querySelectorAll`(정적)로 잡아 두고 노드를 하나 더 붙였더니 `live=2 static=1` 이 나왔다(`02`의 핵심이 그대로 관측된다). `--virtual-time-budget` 으로 타이머·`getBoundingClientRect`·`getComputedStyle`·`dataset` 까지 한 번에 확인했다. 보안 문맥이 필요한 것은 `python3 -m http.server` 로 `http://localhost` 를 띄워 `isSecureContext=true`·`localStorage` 동작·`crossOriginIsolated=false` 를 확인했다. **막히는 것**: Service Worker 등록 프로미스는 headless 의 가상 시간 아래에서 정착하지 않았다(`49`·`50` 은 CDP 로 몰거나 실제 창에서 확인해야 한다). **WebKit(Safari)은 이 머신에 없다** — Blink 와 Gecko 둘뿐이므로 Safari 차이는 명세와 Baseline 날짜로만 접지하고 「미실행」으로 표기한다.\
> ⚠️ **2026-09-21 정정 — 렌더 검증은 Chrome 단일 엔진이다.** Firefox 155.0.1 은 설치돼 있으나 이 환경에서 **headless 스크린샷이 산출되지 않는다** (전용 프로파일로도 `exit 0` 으로 끝나며 파일을 만들지 않는 **조용한 실패**). 따라서 크로스 브라우저 차이를 주장할 때는 Baseline 데이터로만 접지하고, 「두 엔진에서 확인했다」고 적지 않는다.
> 기준일 2026-09-21.

## 이 갈래가 선 이유

13개 언어 목록을 끝내고 보니 **아무도 맡지 않은 면적**이 드러났다.
[`../languages/js/syntax/README.md`](../languages/js/syntax/README.md) 는 ECMA-262 만 다루고 「DOM·브라우저 API 는 언어가 아니라 호스트」라며 명시적으로 뺐다(예외는 `AbortController`·`structuredClone` 둘뿐이다).
[`../languages/html/syntax/README.md`](../languages/html/syntax/README.md) 는 「스크립트로 하는 일은 전부 JS 쪽」이라며 마크업과 시맨틱까지만 잘랐고, [`../languages/css/syntax/README.md`](../languages/css/syntax/README.md) 는 선언적 스타일 계산까지만 잘랐다.
**셋 다 각자 옳게 잘랐는데, 합치면 그 사이가 비어 있다** — `querySelector` 도, 이벤트 전파도, `fetch` 도, `dialog.showModal()` 도 어느 목록에도 없다. HTML 목록의 교차 대조 절이 이미 이 공백을 결론으로 적어 두었다.
그 빈자리가 이 갈래다. 언어가 아니라 **브라우저라는 실행 환경이 제공하는 객체와 규칙**이므로 `languages/` 밖에 선다.

## 무엇을 자르는 축

축은 **「무엇을 건드리는 API 인가」** 로 세웠다. 명세 단위(DOM / HTML / Fetch / Service Worker …)로 자르면 배우는 사람에게는 경계가 보이지 않는다 — `AbortController` 는 DOM 명세에 있지만 실제로는 `fetch` 와 같이 배워야 하고, `requestAnimationFrame` 은 HTML 명세에 있지만 실제로는 관측·스케줄링 이야기다.

**`DOM`** 은 문서 트리를 읽고 쓰는 표면이다. 조회·삽입·속성이 앞에 오고, 그 뒤에 **스크립트가 스타일과 기하를 읽는 자리**(`08`~`09`)를 붙였다. 이 둘을 붙여 놓은 이유는 하나다 — 그 다음 주제가 **레이아웃 스래싱**(`10`)이기 때문이다. 읽기와 쓰기를 교차시키면 브라우저가 프레임마다 레이아웃을 강제로 다시 돌린다는 사실은 「동작은 하는데 조용히 느려진다」의 대표 원인이고, `getComputedStyle`·`getBoundingClientRect` 가 무엇을 트리거하는지 모르면 진단이 불가능하다. 그래서 이 갈래에서 유일하게 **API 가 아니라 실패 모드 자체를 주제로 세운 자리**다.

**`이벤트`** 는 전파 모델 하나만 제대로 세우면 나머지가 따라온다. 전파 3단계(`16`) → 멈추는 두 방법의 구분(`17`) → 위임(`18`) → `passive`(`19`) 순서가 그 뼈대다. 여기서 갈리는 것은 문법이 아니라 **누가 먼저 불리고, 무엇을 막았고, 리스너가 언제까지 살아 있는가**다.

**`네트워크`** 는 `fetch` 하나에서 출발해 **본문·취소·출처·자격 증명**으로 퍼진다. CORS(`28`)를 「에러 메시지」가 아니라 **브라우저가 응답 읽기를 막는 규칙**으로 세운 것이 이 갈래의 핵심이다.

**`관측·스케줄링`** 은 「폴링 대신 브라우저에게 알려 달라고 하는 것」과 「언제 실행할지 브라우저와 협상하는 것」 둘이다. `40`(마이크로태스크 대 태스크)은 JS 목록의 이벤트 루프(JS 36)를 선행으로 걸고, **여기서는 렌더 단계가 그 사이 어디에 끼는가**만 다룬다.

**`저장·상태`**, **`워커·동시성`**, **`미디어·그래픽`**, **`보안·권한`** 은 각각 지속성·병렬성·재생/픽셀·경계의 축이다. 보안·권한 갈래에 **제약 검증 API**(`60`)를 둔 것은 분류상 어색해 보이지만 의도적이다 — 이 API 의 인출 대상이 「클라이언트 검증은 서버 검증을 대체하지 못한다」는 **경계 판단**이기 때문이다.

**「언제 들어왔나」는 여기가 아니다.** DOM 이 어떻게 표준이 됐고 AJAX 가 무엇을 바꿨고 Service Worker·WebAssembly 가 왜 들어왔는지는 [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) 의 몫이다. 이 목록은 **어떻게 쓰고 무엇을 못 하나**만 다룬다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 렌더 | 우선 |
|---|------|------|----------------------|------|-----------|------|------|
| 01 | [문서와 노드 트리](01-document-and-node-tree/) — `Node`/`Element`/`Text`/`Comment`·`childNodes` 대 `children`·탐색 | DOM | 노드와 요소를 구분해 두 컬렉션이 갈리는 지점을 설명하고, 소스의 줄바꿈이 어디서 텍스트 노드가 되는지 예측할 수 있다 | HTML 05 | — | 도움 | A |
| 02 | [요소 조회](02-element-queries-and-live-collections/) — `querySelector` 계열·`getElementById`/`getElementsBy*` 와 라이브 대 정적 컬렉션 | DOM | 조회 뒤에 노드를 붙였을 때 결과가 따라 변하는 쪽과 아닌 쪽을 판정하고, 라이브 컬렉션을 순회하며 삭제할 때 나는 사고를 예측할 수 있다 | 01 · CSS 08 | — | 도움 | A |
| 03 | [노드 생성·삽입·이동·제거](03-node-creation-insertion-removal/) — `createElement`·`append`/`prepend`/`before`/`after`·`remove` | DOM | 이미 트리에 있는 노드를 다시 삽입하면 복사가 아니라 **이동**이라는 것과 `append` 와 `appendChild` 가 갈리는 지점을 설명할 수 있다 | 01 | — | 필수 | A |
| 04 | [`textContent` 대 `innerHTML` 대 `innerText`](04-textcontent-innerhtml-innertext/) — 파싱·비용·XSS | DOM | 세 프로퍼티가 각각 무엇을 읽고 쓰는지 구분하고, `innerHTML` 이 왜 신뢰할 수 없는 문자열에 쓰면 안 되는 표면인지 공격 경로로 설명할 수 있다 | 03 | [`../security/`](../security/) | 필수 | A |
| 05 | [`DocumentFragment` 와 `<template>` 복제](05-documentfragment-and-template/) — 일괄 삽입 | DOM | 조각에 모아 한 번에 붙이는 것이 무엇을 줄이는지 설명하고 `template.content` 를 `cloneNode(true)` 로 찍어 쓰는 형태를 설계할 수 있다 | 03 · HTML 10 | — | 도움 | A |
| 06 | [속성(attribute) 대 성질(property)](06-attribute-vs-property/) — `getAttribute`/`setAttribute` 와 IDL 프로퍼티의 반영 | DOM | `input.value` 를 바꿔도 `value` 속성이 그대로인 이유를 설명하고 `checked`·`href`·`class` 처럼 반영 규칙이 제각각인 것을 판정할 수 있다 | 01 · HTML 02 | — | 도움 | A |
| 07 | [`dataset`·`classList`·인라인 `style`](07-dataset-classlist-inline-style/) — 스크립트가 만지는 세 표면 | DOM | `data-foo-bar` 가 `dataset.fooBar` 가 되는 규칙, `classList.toggle` 의 두 번째 인자, `el.style` 이 인라인만 본다는 것을 설명할 수 있다 | 06 | — | 도움 | A |
| 08 | [`getComputedStyle`](08-getcomputedstyle/) — 스크립트에서 계산값을 읽는다는 것 | DOM | `el.style` 로는 안 보이던 값이 왜 여기서는 보이는지, 돌려받는 것이 내가 쓴 문자열이 아니라 계산값이라는 것을 예측할 수 있다 | 07 · CSS 04 | — | 도움 | A |
| 09 | 요소 기하 — `getBoundingClientRect`·`offset*`/`client*`/`scroll*` 과 좌표계 | DOM | 뷰포트 기준과 문서 기준 좌표를 변환하고, 세 계열이 테두리·스크롤바·`transform` 을 각각 포함하는지 판정할 수 있다 | 01 · CSS 15 | — | 필수 | A |
| 10 | 레이아웃 스래싱 — 읽기·쓰기 교차로 나는 강제 동기 레이아웃 | DOM | 루프 안에서 기하를 읽고 스타일을 쓰면 왜 프레임이 무너지는지 설명하고, 읽기 묶음과 쓰기 묶음으로 갈라 고치는 형태를 설계할 수 있다 | 08, 09 · CSS 56 | [`../../../history/web/04-브라우저-엔진.md`](../../../history/web/04-브라우저-엔진.md) | 필수 | A |
| 11 | 스크롤 제어 — `scrollTo`/`scrollBy`/`scrollIntoView`·스크롤 컨테이너 찾기·위치 복원 | DOM | 실제로 스크롤되는 요소가 누구인지 찾아내고, 복원이 이미지 로딩과 경합해 튀는 자리를 예측할 수 있다 | 09 · CSS 23 | — | 필수 | B |
| 12 | Shadow DOM — `attachShadow`·캡슐화 경계·슬롯 할당·`::part` | DOM | 그림자 경계가 선택자·스타일·이벤트에 각각 무엇을 하는지 설명하고 `open` 과 `closed` 가 실제로 무엇을 막는지 판단할 수 있다 | 01 · HTML 10 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §6 | 필수 | B |
| 13 | 커스텀 요소 수명주기 — `customElements.define`·`connected`/`disconnected`/`attributeChanged`·업그레이드 | DOM | 파서가 먼저 만든 요소가 나중 정의로 「업그레이드」되는 순서를 추적하고, 생성자에서 하면 안 되는 일을 판정할 수 있다 | 12 · JS 16 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §6 | 도움 | B |
| 14 | `dialog`·`popover` 의 스크립트 제어 — `showModal()`·`togglePopover()`·최상위 레이어·포커스 | DOM | `show()` 와 `showModal()` 이 포커스·배경 비활성·`::backdrop` 에서 갈리는 것과 팝오버의 가벼운 닫기가 언제 일어나는지 예측할 수 있다 | 03 · HTML 47, HTML 48 | — | 필수 | B |
| 15 | 리스너 등록과 해제 — `addEventListener` 옵션 객체·`removeEventListener` 의 동일성 조건·`handleEvent` | 이벤트 | 익명 함수로 등록한 리스너를 왜 제거할 수 없는지 설명하고 객체를 리스너로 넘기는 형태를 쓸 수 있다 | HTML 41 | — | 도움 | A |
| 16 | 전파 3단계 — 캡처·타깃·버블과 `target` 대 `currentTarget` | 이벤트 | 중첩 구조에서 리스너 호출 순서를 적고, 버블하지 않는 이벤트(`focus`·`load`)를 어떻게 잡는지 판정할 수 있다 | 15 | — | 필수 | A |
| 17 | `stopPropagation` 대 `preventDefault` — 전파를 멈추는 것과 기본 동작을 막는 것 | 이벤트 | 둘이 서로 다른 일을 한다는 것을 링크·폼·체크박스로 설명하고 `stopImmediatePropagation`·`cancelable`·`defaultPrevented` 를 판정할 수 있다 | 16 | — | 필수 | A |
| 18 | 이벤트 위임 — 조상 하나로 자손 전체 받기·`closest()` 로 되찾기 | 이벤트 | 나중에 추가된 요소에 리스너를 다시 안 달아도 되는 이유를 전파로 설명하고, 위임이 깨지는 경우(비버블 이벤트·그림자 경계)를 판단할 수 있다 | 16 · CSS 08 | — | 필수 | A |
| 19 | `passive` 와 스크롤 성능 — 기본값이 바뀐 이유 | 이벤트 | `touchstart`/`wheel` 리스너가 스크롤을 왜 지연시키는지 설명하고 `passive: true` 에서 `preventDefault()` 가 무시되는 것을 예측할 수 있다 | 17 | — | 필수 | A |
| 20 | 리스너 수명 — `once`·`signal` 로 해제하기와 누수 | 이벤트 | 리스너 하나가 어떤 객체 그래프를 붙들어 두는지 그리고, `AbortSignal` 하나로 여러 리스너를 한 번에 떼는 형태를 설계할 수 있다 | 15 · JS 41 | [`../memory-management/`](../memory-management/) | 불필요 | A |
| 21 | 커스텀 이벤트 — `CustomEvent`·`dispatchEvent`·`detail`·`bubbles`/`composed` | 이벤트 | 내 이벤트가 그림자 경계를 넘을지를 `composed` 로 정하고, 디스패치가 동기라는 성질이 만드는 흐름을 예측할 수 있다 | 12, 16 | — | 도움 | B |
| 22 | 입력 이벤트의 순서 — `keydown`→`beforeinput`→`input`→`change` 와 IME 조합 | 이벤트 | 한 번의 타이핑에서 어떤 이벤트가 어떤 순서로 나는지 적고, 한글·일본어 조합 중에 `input` 값을 믿으면 안 되는 이유를 설명할 수 있다 | 16 · HTML 22 | — | 필수 | A |
| 23 | 포인터 이벤트 — `pointerdown` 계열·마우스/터치/펜 통합·`setPointerCapture` | 이벤트 | 마우스 이벤트와 포인터 이벤트가 겹쳐 나는 순서를 추적하고, 드래그가 요소 밖으로 나가도 안 끊기게 캡처로 고정할 수 있다 | 17 | — | 필수 | B |
| 24 | 문서 수명주기 이벤트 — `DOMContentLoaded`/`load`·`visibilitychange`·`pagehide`/`pageshow` 와 bfcache | 이벤트 | 「떠날 때」를 어느 이벤트로 잡아야 하는지 모바일까지 포함해 판정하고, bfcache 로 되살아난 페이지에서 `load` 가 다시 안 나는 것을 설명할 수 있다 | 16 · HTML 08 | — | 도움 | A |
| 25 | `fetch` 와 `Request`/`Response` — 옵션·헤더·상태 코드가 예외가 아니라는 것 | 네트워크 | 404 에서 왜 `catch` 가 안 도는지 설명하고 `Request`/`Response` 를 값처럼 만들어 재사용·`clone()` 하는 형태를 설계할 수 있다 | JS 39 | [`../../../history/web/02-HTTP-진화.md`](../../../history/web/02-HTTP-진화.md) · [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §2 | 도움 | A |
| 26 | 응답 본문과 스트리밍 — `json()`/`text()`/`blob()` 은 한 번만·`body` 와 `ReadableStream` | 네트워크 | 본문을 두 번 읽으면 왜 실패하는지 설명하고, 진행률 표시나 조기 처리를 위해 청크 단위로 읽는 형태를 짤 수 있다 | 25 · JS 40 | [`../../ops-patterns/05-backpressure/`](../../ops-patterns/05-backpressure/) | 도움 | B |
| 27 | `AbortController` 로 취소와 타임아웃 — `AbortSignal.timeout()`/`any()` | 네트워크 | 취소가 요청을 「없던 일」로 만들지 않는다는 것(서버는 이미 처리했을 수 있다)을 판단하고 여러 신호를 합치는 형태를 쓸 수 있다 | 25 · JS 41 | [`../../ops-patterns/deadline-propagation/`](../../ops-patterns/deadline-propagation/) | 불필요 | A |
| 28 | CORS — 단순 요청과 프리플라이트, 막는 것과 못 막는 것 | 네트워크 | 브라우저가 막는 것은 요청 전송이 아니라 **응답 읽기**라는 것을 설명하고, 어떤 헤더·메서드가 프리플라이트를 유발하는지 판정할 수 있다 | 25 | [`../security/`](../security/) | 도움 | A |
| 29 | 자격 증명과 `credentials` — 쿠키가 실리는 조건·와일드카드 금지 | 네트워크 | 교차 출처 요청에 쿠키가 실리려면 양쪽이 각각 무엇을 해야 하는지 대고, `Access-Control-Allow-Origin: *` 과 왜 같이 못 쓰는지 설명할 수 있다 | 28 | — | 도움 | A |
| 30 | 요청 본문 만들기 — `FormData`·`URLSearchParams`·JSON 과 `Content-Type` 자동 설정 | 네트워크 | `FormData` 를 넘길 때 `Content-Type` 을 직접 쓰면 왜 깨지는지 설명하고 폼 제출과 같은 본문을 스크립트로 재현할 수 있다 | 25 · HTML 21 | — | 도움 | A |
| 31 | `Blob`·`File`·`FileReader` 와 오브젝트 URL | 네트워크 | 파일 입력에서 받은 것을 미리보기·업로드·저장으로 각각 어떻게 넘기는지 고르고, `createObjectURL` 을 해제하지 않으면 무엇이 남는지 판단할 수 있다 | 30 · HTML 31 | [`../memory-management/`](../memory-management/) | 필수 | B |
| 32 | 서버 보내기 이벤트 — `EventSource`·자동 재연결·`Last-Event-ID` | 네트워크 | 단방향 푸시에 WebSocket 대신 이것을 고르는 근거를 대고, 재연결과 이벤트 유실의 경계를 설명할 수 있다 | 25 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §4 | 도움 | B |
| 33 | WebSocket — 핸드셰이크·프레임·닫힘 코드와 재연결 설계 | 네트워크 | HTTP 로 시작해 프로토콜이 바뀌는 과정을 설명하고, 끊김을 감지해 백오프로 다시 붙는 형태를 설계할 수 있다 | 32 | [`../../ops-patterns/01-retry-backoff/`](../../ops-patterns/01-retry-backoff/) · [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §4 | 도움 | B |
| 34 | `navigator.sendBeacon` 과 이탈 시점 전송 — `fetch` 의 `keepalive` 와의 관계 | 네트워크 | 페이지가 사라지는 중에 보낸 요청이 왜 잘리는지 설명하고 비콘·`keepalive`·`visibilitychange` 를 조합해 고를 수 있다 | 24, 25 | — | 불필요 | B |
| 35 | `IntersectionObserver` — 루트·`rootMargin`·`threshold` 와 지연 로딩 | 관측·스케줄링 | 스크롤 이벤트로 위치를 재는 방식과 비용이 왜 다른지 설명하고 무한 스크롤·노출 집계의 관측 조건을 설계할 수 있다 | 09, 19 | — | 필수 | A |
| 36 | `ResizeObserver` — 관측 상자 세 종류와 무한 루프 경고 | 관측·스케줄링 | 창 크기 이벤트로는 안 잡히는 크기 변화를 잡아내고, 콜백 안에서 크기를 바꿨을 때 나는 루프 경고를 설명할 수 있다 | 09 | — | 필수 | B |
| 37 | `MutationObserver` — 관측 옵션·레코드 묶음·마이크로태스크 타이밍 | 관측·스케줄링 | 변경 통지가 즉시가 아니라 묶여서 온다는 성질을 설명하고 남의 스크립트가 만든 DOM 변화에 반응하는 형태를 설계할 수 있다 | 03 | — | 도움 | C |
| 38 | `requestAnimationFrame` 과 프레임 예산 | 관측·스케줄링 | 콜백이 렌더 단계의 어디에서 불리는지 그리고, 한 프레임에 쓸 수 있는 시간과 그것을 넘겼을 때 보이는 증상을 판단할 수 있다 | 10 · CSS 56 | [`../../../history/web/04-브라우저-엔진.md`](../../../history/web/04-브라우저-엔진.md) | 필수 | A |
| 39 | 유휴 스케줄링 — `requestIdleCallback`·`scheduler.postTask()`/`yield()` 와 긴 작업 쪼개기 | 관측·스케줄링 | 긴 동기 작업이 입력 응답을 어떻게 막는지 설명하고, 양보로 쪼개는 형태와 각 API 의 지원 한계를 판단할 수 있다 | 38 | [`../../ops-patterns/10-scheduler/`](../../ops-patterns/10-scheduler/) · [`../process-thread/`](../process-thread/) | 도움 | B |
| 40 | 마이크로태스크 대 태스크 대 렌더 — 브라우저에서의 실제 순서 | 관측·스케줄링 | `Promise.then`·`setTimeout(0)`·`requestAnimationFrame` 세 콜백의 실행 순서를 적고, 마이크로태스크가 렌더를 굶기는 자리를 예측할 수 있다 | 38 · JS 36 | [`../process-thread/`](../process-thread/) | 도움 | A |
| 41 | `localStorage`/`sessionStorage` — 동기 비용·용량·`storage` 이벤트·범위 | 저장·상태 | 이 API 가 메인 스레드를 막는다는 사실이 언제 문제가 되는지 판단하고, 두 저장소의 수명·공유 범위와 탭 간 통지를 설명할 수 있다 | — | — | 불필요 | A |
| 42 | IndexedDB — 객체 저장소·인덱스·트랜잭션·`onupgradeneeded` | 저장·상태 | 트랜잭션이 왜 「가만히 두면 닫히는지」 설명하고, 스키마를 업그레이드 시점에만 바꿀 수 있다는 제약 위에서 마이그레이션을 설계할 수 있다 | 41 · JS 39 | [`../../data-structure/15-b-tree/`](../../data-structure/15-b-tree/) | 도움 | B |
| 43 | Cache Storage 와 저장 할당량 — `caches`·`StorageManager`·축출 | 저장·상태 | 캐시 항목의 키가 `Request` 라는 것을 설명하고, 브라우저가 저장소를 조용히 비울 수 있다는 전제 위에서 설계할 수 있다 | 25, 42 | [`../../data-structure/10-lru-cache/`](../../data-structure/10-lru-cache/) | 불필요 | B |
| 44 | 쿠키 — `document.cookie` 와 속성(`SameSite`·`HttpOnly`·`Secure`·`Domain`/`Path`) | 저장·상태 | 스크립트가 못 읽는 쿠키가 왜 필요한지 설명하고, `SameSite` 세 값이 교차 사이트 요청에서 각각 무엇을 막는지 판정할 수 있다 | 29 | [`../security/`](../security/) · [`../../engineering/development-standards/security-standards/`](../../engineering/development-standards/security-standards/) | 불필요 | A |
| 45 | `URL`·`URLSearchParams` — 파싱·상대 해석·인코딩 | 저장·상태 | 문자열을 자르는 대신 `URL` 로 다루면 무엇이 자동으로 맞는지 설명하고, 공백·`+`·한글이 인코딩되는 규칙을 예측할 수 있다 | — | [`../data-representation/`](../data-representation/) | 불필요 | A |
| 46 | History API 와 `popstate` — `pushState`/`replaceState`·스크롤 복원·SPA 라우팅 | 저장·상태 | 주소만 바꾸고 문서는 두는 방식이 무엇을 깨뜨리는지(뒤로 가기·새로고침·공유) 판단하고 라우터가 하는 일을 직접 재현할 수 있다 | 24, 45 | [`../../../history/web/06-웹아키텍처-진화.md`](../../../history/web/06-웹아키텍처-진화.md) | 필수 | A |
| 47 | Web Worker — 생성·`postMessage`·구조적 복제의 한계 | 워커·동시성 | 워커에 넘길 수 있는 것과 없는 것(함수·DOM 노드)을 판정하고, 메시지 왕복 비용이 이득을 잡아먹는 지점을 판단할 수 있다 | JS 48 | [`../process-thread/`](../process-thread/) · [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §7 | 불필요 | B |
| 48 | 전송과 공유 메모리 — `Transferable`·`SharedArrayBuffer`·`Atomics`·교차 출처 격리 | 워커·동시성 | 복사·전송·공유 셋을 구분하고, `SharedArrayBuffer` 를 쓰려면 문서가 무엇을(COOP/COEP) 선언해야 하는지 설명할 수 있다 | 47 | [`../process-thread/`](../process-thread/) · [`../memory-management/`](../memory-management/) | 불필요 | C |
| 49 | Service Worker 수명주기 — 등록·`install`/`activate`·`skipWaiting`/`clients.claim`·업데이트 | 워커·동시성 | 새 버전이 왜 바로 적용되지 않고 대기하는지 상태 전이로 설명하고, 강제로 넘기는 것이 만드는 위험을 판단할 수 있다 | 47 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §5 · [`../../ops-patterns/19-graceful-shutdown/`](../../ops-patterns/19-graceful-shutdown/) | 도움 | B |
| 50 | Service Worker 의 `fetch` 가로채기와 캐시 전략 | 워커·동시성 | 캐시 우선·네트워크 우선·재검증 세 전략이 각각 무엇을 희생하는지 대고, 오프라인 폴백과 버전 전환을 설계할 수 있다 | 43, 49 | [`../../ops-patterns/09-stampede/`](../../ops-patterns/09-stampede/) · [`../../data-structure/10-lru-cache/`](../../data-structure/10-lru-cache/) | 도움 | B |
| 51 | 문서·탭 간 통신 — `BroadcastChannel`·`MessageChannel`·Web Locks | 워커·동시성 | 같은 출처의 여러 탭이 상태를 나누는 수단을 비교해 고르고, 한 탭만 일하게 만드는 잠금 형태를 설계할 수 있다 | 47 | [`../../ops-patterns/11-distributed-lock/`](../../ops-patterns/11-distributed-lock/) · [`../../ops-patterns/12-leader-election/`](../../ops-patterns/12-leader-election/) | 도움 | C |
| 52 | `HTMLMediaElement` 제어 — `play()` 프로미스·자동재생 정책·`readyState`/버퍼링·`timeupdate` | 미디어·그래픽 | `play()` 가 거부될 수 있다는 것과 그 조건(소리·사용자 제스처)을 설명하고, 버퍼링 상태를 이벤트로 추적할 수 있다 | 15 · HTML 37 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §3 | 필수 | B |
| 53 | Canvas 2D — 컨텍스트·좌표·`devicePixelRatio`·`drawImage`·픽셀 데이터 | 미디어·그래픽 | 캔버스의 속성 크기와 CSS 크기가 다르면 왜 흐려지는지 설명하고, 픽셀을 읽는 연산이 오염(taint)과 성능에서 걸리는 지점을 판단할 수 있다 | 09 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §3 | 필수 | B |
| 54 | Web Animations API — `element.animate()`·재생 제어·CSS 애니메이션과의 경계 | 미디어·그래픽 | 같은 움직임을 CSS 로 할 때와 스크립트로 할 때 무엇이 달라지는지(합성·제어·우선순위) 판단하고 재생·역재생·완료 대기를 다룰 수 있다 | 07 · CSS 53 | — | 필수 | B |
| 55 | `getUserMedia` 맛보기 — 권한·`MediaStream`·트랙 정지 | 미디어·그래픽 | 카메라·마이크를 얻는 흐름이 왜 비동기이고 거부될 수 있는지 설명하고, 트랙을 멈추지 않으면 표시등이 남는 것을 판단할 수 있다 | 52 | [`../../../history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §7 | 필수 | C |
| 56 | 동일 출처 정책 — 출처의 정의와 격리 경계 | 보안·권한 | 두 URL 이 같은 출처인지 판정하고, 정책이 막는 것(읽기)과 막지 않는 것(요청 전송·자원 임베드)을 구분할 수 있다 | 28 | [`../security/`](../security/) · [`../../../history/network/04-네트워크-보안.md`](../../../history/network/04-네트워크-보안.md) | 불필요 | A |
| 57 | `postMessage` 와 출처 검증 — 창·iframe·워커 간 메시지 | 보안·권한 | 보낼 때 `targetOrigin` 을, 받을 때 `event.origin` 을 각각 왜 검사해야 하는지 공격 시나리오로 설명할 수 있다 | 56 · HTML 38 | [`../security/`](../security/) | 불필요 | A |
| 58 | CSP 가 막는 것 — 인라인 스크립트·`nonce`/`hash`·위반 리포트 | 보안·권한 | 정책 한 줄을 읽고 어떤 로딩이 차단되는지 판정하며, CSP 가 XSS 의 완화이지 해결이 아니라는 경계를 설명할 수 있다 | 04, 56 · HTML 51 | [`../security/`](../security/) · [`../../engineering/development-standards/security-standards/`](../../engineering/development-standards/security-standards/) | 도움 | B |
| 59 | Permissions API 와 권한 요청 — `query()`·상태 세 값·사용자 제스처 | 보안·권한 | 묻기 전에 상태를 조회하는 형태를 설계하고, 거부가 영구적일 수 있다는 전제에서 대체 경로를 만들 수 있다 | 55, 56 | — | 필수 | B |
| 60 | 제약 검증 API — `checkValidity`/`reportValidity`/`setCustomValidity`·`ValidityState` | 보안·권한 | 마크업이 만든 유효성 상태를 스크립트로 읽고 덮어쓰는 형태를 설계하며, 클라이언트 검증이 서버 검증을 대체하지 못하는 이유를 설명할 수 있다 | 06 · HTML 28, HTML 29 | — | 필수 | B |

**60주제** (DOM 14 · 이벤트 10 · 네트워크 10 · 관측·스케줄링 6 · 저장·상태 6 · 워커·동시성 5 · 미디어·그래픽 4 · 보안·권한 5)
**우선** A 32 · B 24 · C 4
**렌더** 필수 24 · 도움 25 · 불필요 11

- **분류** — `DOM` / `이벤트` / `네트워크` / `관측·스케줄링` / `저장·상태` / `워커·동시성` / `미디어·그래픽` / `보안·권한` 중 하나
- **무엇을 인출하게 되나** — 한 줄. 「~를 안다」가 아니라 **「~를 설명·예측·판단할 수 있다」**
- **선행** — 먼저 봐야 하는 것. 이 갈래 안의 선행은 모두 자기보다 작은 번호라 순환이 없다. `JS NN`·`HTML NN`·`CSS NN` 은 각각 [`../languages/js/syntax/README.md`](../languages/js/syntax/README.md)·[`../languages/html/syntax/README.md`](../languages/html/syntax/README.md)·[`../languages/css/syntax/README.md`](../languages/css/syntax/README.md) 의 주제 번호다
- **기존 주제** — `cs/**`·`history/**` 에 이미 있는 것(없으면 `—`)
- **렌더** — **화면에서 눈으로 봐야 이해되는가**. `필수` / `도움` / `불필요`. 다만 이 갈래는 `불필요` 인 주제라도 **콘솔·네트워크 탭·`--dump-dom` 같은 관측 수단은 필요하다** — 「보이지 않는 것을 보이게 만드는 것」이 주제인 경우가 많다
- **우선** — `A`(핵심·먼저) / `B`(중요) / `C`(나중에)

## 기존 갈래와의 경계

| 축 | 저기 있는 것 | 여기 있는 것 |
|---|---|---|
| [`js/syntax`](../languages/js/syntax/README.md) (ECMA-262) | `class`·`async`/`await`·Promise **문법**, 이벤트 루프의 **언어 쪽 모델**(JS 36~40), `AbortController`(JS 41)·`structuredClone`(JS 48) 의 **개념** | 그 문법으로 **호출하는 플랫폼 객체** — `fetch`(`25`)·`AbortSignal.timeout()`(`27`)·워커의 구조적 복제 한계(`47`). `40` 은 JS 36 을 선행으로 걸고 **렌더 단계가 그 사이 어디에 끼는가**만 다룬다 |
| [`html/syntax`](../languages/html/syntax/README.md) (마크업·시맨틱) | `<dialog>`·`popover` **속성**, `<template>`/`<slot>` **마크업**, `required`/`pattern` 검증 **속성**, `<video>` **속성**, `<script defer>` | 그 요소를 **스크립트로 다루는 표면** — `showModal()`/`togglePopover()`(`14`), `template.content` 복제(`05`), `checkValidity()`(`60`), `play()` 프로미스(`52`), `DOMContentLoaded` 타이밍(`24`) |
| [`css/syntax`](../languages/css/syntax/README.md) (선언적 스타일) | 캐스케이드·값 처리 단계(CSS 04), 박스 모델(CSS 15), 렌더링 파이프라인과 `will-change`(CSS 56), `@keyframes`/`transition`(CSS 52·53) | 스크립트에서 **스타일·레이아웃을 읽고 쓰는 것** — `getComputedStyle`(`08`), `getBoundingClientRect`(`09`), **리플로를 유발하는 자리**(`10`), `element.animate()`(`54`) |
| [`history/web`](../../../history/web/) | **언제·왜 들어왔나** — DOM 표준화, AJAX, WebSocket·WebRTC, Service Worker·PWA, 웹 컴포넌트, WebAssembly | **오늘 어떻게 쓰고 무엇을 못 하나** — 같은 API 라도 역사 서술은 링크만 하고 규칙·실패 모드만 다룬다 |

## 기존 주제와 겹치는 것

| 겹치는 주제 | 기존에 있는 것 | 새 주제를 어떻게 좁혔나 |
|---|---|---|
| `12`·`13` 웹 컴포넌트 · `32`·`33` SSE/WebSocket · `49`·`50` Service Worker · `53` Canvas · `55` getUserMedia | [`history/web/05-웹플랫폼-API.md`](../../../history/web/05-웹플랫폼-API.md) §3~§7 — 무엇이 언제 표준이 됐나 | 도입 경위는 링크만. 여기는 **오늘의 호출 표면과 실패 모드** — 업그레이드 순서, 재연결 설계, waiting 상태, 캔버스 오염 |
| `10` 레이아웃 스래싱 · `38` 프레임 예산 | [`history/web/04-브라우저-엔진.md`](../../../history/web/04-브라우저-엔진.md) · [`css/syntax`](../languages/css/syntax/README.md) 56 (렌더링 파이프라인) | 엔진 계보는 역사 쪽, **어느 CSS 속성이 어느 단계를 돌리나**는 CSS 56. 여기는 **스크립트가 그 파이프라인을 강제로 동기 실행시키는 호출 목록**과 읽기/쓰기 분리라는 고치는 법 |
| `25` fetch · `28` CORS · `29` credentials | [`history/web/02-HTTP-진화.md`](../../../history/web/02-HTTP-진화.md) · [`foundations/security/`](../security/) | 프로토콜과 위협 모델은 그쪽. 여기는 **브라우저가 응답 읽기를 막는 규칙**이라는 클라이언트 쪽 표면에 한정 |
| `27` 취소·타임아웃 | [`ops-patterns/deadline-propagation/`](../../ops-patterns/deadline-propagation/) | 데드라인 전파 패턴 일반론은 그쪽. 여기는 **`AbortSignal` 이라는 브라우저 표면 하나** — 신호 합치기와 「취소해도 서버는 이미 했다」는 경계 |
| `33` 재연결 | [`ops-patterns/01-retry-backoff/`](../../ops-patterns/01-retry-backoff/) | 백오프 알고리즘은 그쪽. 여기는 **WebSocket 닫힘 코드로 재시도 여부를 가르는 판단**까지 |
| `43`·`50` 캐시 | [`data-structure/10-lru-cache/`](../../data-structure/10-lru-cache/) · [`ops-patterns/09-stampede/`](../../ops-patterns/09-stampede/) | 캐시 자료구조와 쇄도 패턴은 그쪽. 여기는 **Cache Storage 의 키가 `Request` 라는 것**과 Service Worker 전략 세 가지의 트레이드오프 |
| `39`·`40`·`47`·`48` 스케줄링·워커 | [`foundations/process-thread/`](../process-thread/) · [`ops-patterns/10-scheduler/`](../../ops-patterns/10-scheduler/) | 스레드·스케줄러 일반론은 그쪽. 여기는 **단일 메인 스레드 + 이벤트 루프**라는 브라우저의 구체 제약과 COOP/COEP 라는 격리 요구 |
| `51` 탭 간 조율 | [`ops-patterns/11-distributed-lock/`](../../ops-patterns/11-distributed-lock/) · [`12-leader-election/`](../../ops-patterns/12-leader-election/) | 분산 잠금·리더 선출 이론은 그쪽. 여기는 **같은 브라우저 안 탭들**이라는 훨씬 좁은 범위와 Web Locks 라는 표면 |
| `20`·`31` 누수 | [`foundations/memory-management/`](../memory-management/) | GC 일반론은 그쪽. 여기는 **리스너와 오브젝트 URL 이라는 두 구체 누수 경로** |
| `42` IndexedDB | [`data-structure/15-b-tree/`](../../data-structure/15-b-tree/) | 인덱스 자료구조는 그쪽. 여기는 **트랜잭션 자동 종료와 버전 업그레이드**라는 API 규칙 |
| `44`·`58` 쿠키·CSP | [`foundations/security/`](../security/) · [`engineering/…/security-standards/`](../../engineering/development-standards/security-standards/) | 인증·표준 요구사항은 그쪽. 여기는 **브라우저가 실제로 강제하는 속성과 지시어** |
| `45` URL 인코딩 | [`foundations/data-representation/`](../data-representation/) | 유니코드·인코딩 원리는 그쪽. 여기는 **`URL` 객체가 적용하는 퍼센트 인코딩 규칙** |
| `46` SPA 라우팅 | [`history/web/06-웹아키텍처-진화.md`](../../../history/web/06-웹아키텍처-진화.md) | SPA·SSR 아키텍처 변천은 그쪽. 여기는 **History API 호출과 `popstate` 가 나는 조건** |

## 뺀 것과 이유

**있는데 뺀 것**이다. 없어서 안 넣은 것이 아니다.

| 뺀 것 | 이유 |
|---|---|
| `Selection`·`Range`·`contenteditable` 리치 에디터 | 면적은 크지만 실무 빈도가 낮고, 오늘은 `EditContext`(Baseline limited)로 판이 바뀌는 중이다. `03` 에서 노드 조작의 한 형태로만 언급 |
| 포커스 이벤트(`focus`/`focusin`)와 포커스 관리 | `16` 의 「버블하지 않는 이벤트」 예로 흡수했다. 포커스 순서·`tabindex`·`inert` 는 이미 HTML 45 가 다룬다 |
| 드래그 앤 드롭 API(`dragstart`·`DataTransfer`) | 명세가 낡았고 실무에서는 포인터 이벤트(`23`)로 직접 만드는 쪽이 많다. 필요하면 다음 라운드 |
| `PerformanceObserver`·Navigation/Resource Timing·웹 바이탈(LCP·CLS·INP) | 「측정」은 API 사용법보다 **지표 정의**가 본체라 축이 다르다. 별도 갈래(성능 측정)로 제안한다 |
| WebGL·WebGPU·WebAssembly·WebRTC 연결 수립 | 각각이 독립 갈래 크기다. `53` 은 Canvas **2D** 까지, `55` 는 스트림을 얻는 데까지만 |
| Notification·Push·Geolocation·Web Bluetooth/USB/Serial 등 디바이스 API | 권한 모델은 `59` 가 대표로 다루고 개별 API 는 뺐다. 대부분 Baseline 이 고르지 않거나 데스크톱 한정이다 |
| Web Crypto(`crypto.subtle`) | 해시·HMAC·서명의 **의미**는 [`foundations/security/`](../security/) 에 이미 있다. 브라우저 표면만 따로 세울 만큼 크지 않다 |
| Trusted Types·Sanitizer API | XSS 방어의 다음 수단이지만 Sanitizer 는 Baseline **limited**, Trusted Types 는 **newly**(2026-02-24)다. `04`·`58` 안에서 한 줄씩만 |
| Navigation API(`navigation.navigate`) | Baseline **newly**(2026-01-13). `46` 이 History API 를 다루고, 후계 API 라는 사실만 언급 |
| `URLPattern`·`WebTransport`·`fetchLater`·Cookie Store·Scoped custom element registries | newly 이거나 limited. 「지금 배워 쓰는 표면」 기준선 밖이다(아래 지원 표에 근거) |
| Origin Private File System·File System Access | 저장 갈래를 한 번 더 키우는 데다 쓰기 권한 모델이 별개다. `31` 의 파일 읽기까지만 |
| 브라우저 확장 API·Node 런타임 API | 이 플랫폼이 아니다 |
| 프레임워크의 가상 DOM·상태 관리 | 라이브러리 층이다. [`history/js/06-프레임워크-진화.md`](../../../history/js/06-프레임워크-진화.md) 의 몫 |
| 개발자 도구 사용법 | 도구다. 다만 `10`·`38`·`40` 의 검증 수단으로 3파일 안에서 쓴다 |

## 버전·지원 기준

웹 플랫폼 API 에는 버전이 없다. 대부분 **Living Standard** 이고, 기준은 **브라우저 Baseline** 하나다.

- **기준선**: Baseline **widely available**(주요 엔진 전부에서 30개월 이상) 인 것을 「그냥 써도 되는 것」으로 본다.
- **newly available** 인 것은 주제 이름·3파일에 「**Baseline newly, 저변 도달 시점 <날짜>**」를 명시한다.
- **limited** 인 것은 원칙적으로 뺐고(위 표), 남긴 것은 그 사실과 어느 엔진이 없는지를 적는다.

아래 값은 2026-09-21 에 [`api.webstatus.dev`](https://webstatus.dev/) 의 feature API 를 직접 조회해 받은 것이다. **추측하지 않았다.**

| 기능 | 이 목록의 주제 | Baseline | newly 된 날 | widely 된 날 |
|---|---|---|---|---|
| Shadow DOM | 12 | **widely** | 2020-01-15 | 2022-07-15 |
| 선언적 Shadow DOM | 12 | **widely** | 2024-02-20 | 2026-08-20 |
| 자율 커스텀 요소 | 13 | **widely** | 2020-01-15 | 2022-07-15 |
| 폼 연계 커스텀 요소 | 13 | **widely** | 2023-03-27 | 2025-09-27 |
| `<dialog>` | 14 | **widely** | 2022-03-14 | 2024-09-14 |
| Popover | 14 | **newly** | 2025-01-27 | — |
| Pointer Events | 23 | **widely** | 2020-07-28 | 2023-01-28 |
| `input` 이벤트 | 22 | **widely** | 2020-01-15 | 2022-07-15 |
| Composition 이벤트(IME) | 22 | **widely** | 2017-04-19 | 2019-10-19 |
| Page Visibility | 24 | **widely** | 2015-07-29 | 2018-01-29 |
| Page transition 이벤트(`pageshow`/`pagehide`) | 24 | **widely** | 2015-07-29 | 2018-01-29 |
| Fetch | 25 | **widely** | 2017-03-27 | 2019-09-27 |
| Streams | 26 | **widely** | 2022-06-28 | 2024-12-28 |
| `AbortController`/`AbortSignal` | 27 | **widely** | 2019-03-25 | 2021-09-25 |
| Abortable fetch | 27 | **widely** | 2019-03-25 | 2021-09-25 |
| `AbortSignal.timeout()` | 27 | **newly** | 2024-04-18 | — |
| `AbortSignal.any()` | 20, 27 | **newly** | 2024-03-19 | — |
| Server-sent events | 32 | **widely** | 2020-01-15 | 2022-07-15 |
| WebSockets | 33 | **widely** | 2015-07-29 | 2018-01-29 |
| Beacons(`sendBeacon`) | 34 | **widely** | 2018-04-12 | 2020-10-12 |
| Intersection Observer | 35 | **widely** | 2019-03-25 | 2021-09-25 |
| Resize Observer | 36 | **widely** | 2020-07-28 | 2023-01-28 |
| `MutationObserver` | 37 | **widely** | 2015-07-29 | 2018-01-29 |
| `requestAnimationFrame()` | 38 | **widely** | 2015-07-29 | 2018-01-29 |
| `localStorage`/`sessionStorage` | 41 | **widely** | 2015-07-29 | 2018-01-29 |
| IndexedDB | 42 | **widely** | 2021-09-20 | 2024-03-20 |
| Storage Manager(할당량) | 43 | **widely** | 2023-09-18 | 2026-03-18 |
| Cookies | 44 | **widely** | 2015-07-29 | 2018-01-29 |
| Storage Access API | 44 | **widely** | 2023-12-05 | 2026-06-05 |
| History | 46 | **widely** | 2015-07-29 | 2018-01-29 |
| `structuredClone()` | 47 | **widely** | 2022-03-14 | 2024-09-14 |
| 워커의 JS 모듈 | 47 | **widely** | 2023-06-06 | 2025-12-06 |
| `SharedArrayBuffer` 와 `Atomics` | 48 | **widely** | 2021-12-13 | 2024-06-13 |
| Transferable `ArrayBuffer` | 48 | **widely** | 2024-03-05 | 2026-09-05 |
| Service Workers | 49, 50 | **widely** | 2018-04-30 | 2020-10-30 |
| Service Worker 의 JS 모듈 | 49 | **newly** | 2026-01-13 | — |
| `BroadcastChannel` | 51 | **widely** | 2022-03-14 | 2024-09-14 |
| Web Locks | 51 | **widely** | 2022-03-14 | 2024-09-14 |
| Offscreen Canvas | 53 | **widely** | 2023-03-27 | 2025-09-27 |
| Web Animations | 54 | **widely** | 2020-09-16 | 2023-03-16 |
| Media Capture(`getUserMedia`) | 55 | **widely** | 2017-09-19 | 2020-03-19 |
| Content Security Policy | 58 | **widely** | 2016-08-02 | 2019-02-02 |
| Permissions | 59 | **widely** | 2022-09-12 | 2025-03-12 |
| 제약 검증 API | 60 | **widely** | 2018-12-11 | 2021-06-11 |

**limited/newly 라서 뺐거나 한 줄로만 남긴 것** (같은 조회)

| 기능 | Baseline | 실제 상태와 처리 |
|---|---|---|
| `requestIdleCallback()` | **limited** | Chrome 2015·Firefox 2017 에 있고 **Safari 미구현**. `39` 에 **남겼다** — 유휴 스케줄링 축을 통째로 빼면 「긴 작업 쪼개기」를 다룰 자리가 사라지고, 이 머신의 두 엔진에서 실물 확인이 되기 때문이다. 3파일에 「Baseline limited, Safari 미구현」과 대체 수단을 명시한다 |
| Scheduler API(`postTask`/`yield`) | **limited** | Chrome 2024-09·Firefox 2025-08, **Safari 없음**. `39` 안에서 「표준화 중인 후계」로만 |
| Trusted Types | **newly** (2026-02-24) | `04`·`58` 에서 언급만. 저변 도달 전이다 |
| Sanitizer API | **limited** | 같은 자리에서 한 줄. `innerHTML` 의 대안으로 확정되지 않았다 |
| Navigation API | **newly** (2026-01-13) | `46` 에서 History API 의 후계로 언급만 |
| `URLPattern` | **newly** (2025-09-15) | `45`·`46` 에서 라우팅 매칭 수단으로 한 줄 |
| WebTransport | **newly** (2026-03-24) | `33` 에서 WebSocket 의 다음 후보로 한 줄 |
| Partitioned cookies(CHIPS) | **limited** | `44` 에서 서드파티 쿠키 종료와 함께 한 줄 |
| Cookie Store API | **limited** | `44` 에서 `document.cookie` 의 비동기 대안으로 한 줄 |
| `fetchLater()` | **limited** | `34` 에서 비콘의 다음 세대로 한 줄 |
| Mutation events(구식) | **limited** | `37` 에서 「`MutationObserver` 가 대체한 것」으로만 |
| Scoped custom element registries | **limited** | `13` 에서 커스텀 요소 이름 충돌 문제의 미래 해법으로 한 줄 |
| Intersection Observer v2(가시성 추적) | **limited** | `35` 에서 「클릭재킹 탐지용으로 제안됐으나 Chromium 한정」으로 한 줄 |
| Long animation frames | **limited** | 성능 측정 갈래로 보냈다(위 「뺀 것」) |

**확인하지 못한 것** — `MessageChannel`·`crossOriginIsolated`(COOP/COEP)·`DocumentFragment`·`getComputedStyle`·`getBoundingClientRect` 처럼 **오래돼 Baseline 추적 대상 자체가 아닌 표면**은 조회로 확인할 수 없었다. 이들은 모든 현행 엔진에 있으므로 이 목록에서는 지원을 논점으로 삼지 않고, 명세 본문으로만 접지한다. 나머지 행은 모두 API 응답에서 직접 읽은 값이다. 다만 **`webstatus.dev` 는 2차 집계**다 — 「명세가 무엇을 요구하나」는 위 1차 명세로, 「내 브라우저에서 실제로 되나」는 이 머신의 Chrome 151 · Firefox 155 로 각각 다시 확인한다. **Safari/WebKit 은 없으므로** Safari 가 마지막으로 따라온 기능(Streams·IndexedDB·`BroadcastChannel`·Permissions)과 Safari 미구현 기능(`requestIdleCallback`·Scheduler API)은 Baseline 날짜로만 접지하고 「미실행」으로 표기한다.
