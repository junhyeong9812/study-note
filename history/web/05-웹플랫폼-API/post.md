# 웹 플랫폼 API의 확장 — 브라우저가 앱 플랫폼이 되다

> 원본: `~/project/web-history/05-웹플랫폼-API.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-18).\
> 연도·인명·논문명·표준번호·코드는 원문 그대로다.\
> 용어 블록의 「예:」, 「대가는 무엇인가」, 트레이드오프 표는 원문에 없는 보충 설명이다.\
> 「대가는 무엇인가」는 원문에 그 서술이 있는 절에만 붙어 있다 — 없는 절은 비워 두었다.

## 한눈에 — 쉽게 말하면

원문이 이 편을 한 줄로 요약한 문장은 이렇다.

> 정적인 문서 뷰어였던 브라우저가 DOM 표준화, 비동기 통신(AJAX), 그래픽·미디어, 실시간 통신, 오프라인·설치, 컴포넌트, 네이티브 코드 실행(WebAssembly)을 차례로 흡수하며 운영체제급 애플리케이션 플랫폼으로 진화한 약 25년의 역사.

**브라우저 = 처음엔 신문 가판대였는데, 설비가 하나씩 들어와 만능 작업실이 된 방.**

- 처음 이 방에는 **읽을 것을 붙여 놓는 게시판** 하나뿐이었다.\
  들어와서 읽고 나가는 것이 전부였다.
- 그런데 사람들이 "여기서 그림도 그리고 싶다", "전화도 걸고 싶다", "전기가 나가도 일하고 싶다"고 요구하기 시작했다.
- 처음엔 **외부 업체가 장비를 들고 들어왔다**(Flash·Java Applet·ActiveX).\
  장비는 강력했지만 건물 규격에 안 맞아 자꾸 사고를 냈다.
- 그래서 건물주가 **그 기능들을 아예 방의 기본 설비로 붙박이**로 넣기 시작했다.\
  그림판(Canvas), 전화선(WebRTC), 비상 발전기(Service Worker), 공작 기계(WebAssembly) 순으로.

이 방 이야기가 **똑같은 구조로** 웹 플랫폼 API의 약 25년이다.\
오늘 우리가 브라우저에서 화상회의를 하고 이미지를 편집하는 것이 그 붙박이 설비들 덕이다.

```text
[1998]  게시판만 있는 방
   |    문서를 읽는다. 스크립트가 글자를 조금 바꿀 수 있다 (DOM)
   v
[2005]  심부름꾼이 생기고, 그림판도 붙박이로 들어온다
   |    새로고침 없이 서버에서 데이터만 받아온다 (AJAX, 2005 명명)
   |    스크립트가 픽셀을 직접 그린다 (Canvas, 2004)
   v
[2011]  전화선과 3D 장비가 붙박이로 들어온다
   |    WebGL·WebSocket·WebRTC
   v
[2015]  전기가 나가도 돌아간다
   |    Service Worker·PWA — 설치되고 오프라인에서 열린다
   v
[2017]  다른 언어로 만든 기계도 돌린다
        WebAssembly — C/C++/Rust 코드가 브라우저 안에서 돈다
```

> **API(Application Programming Interface)** — 어떤 기능을 쓰라고 미리 정해 놓은 호출 규격.\
> 예: `navigator.geolocation.getCurrentPosition(...)` 이라고 부르면 위치를 돌려준다는 약속이 API다.

> **플러그인(plugin)** — 브라우저 밖에서 따로 돌면서 브라우저 안에 화면을 끼워 넣던 외부 프로그램.\
> 예: 옛날 동영상 사이트에서 "Flash Player를 설치하세요"가 뜨던 것.

> **표준화(standardization)** — 여러 회사가 같은 규격을 쓰기로 문서로 합의하는 것.\
> 예: 같은 `<video>` 태그가 Chrome·Safari·Firefox 어디서나 똑같이 동작하는 이유다.

## 개요

이 문서는 특정 버전이 아니라 **하나의 흐름**을 다룬다.\
"브라우저는 어떻게 문서를 보여주는 프로그램에서 포토샵·화상회의·게임·오피스를 돌리는 플랫폼이 되었나."\
각 API가 **언제, 왜 브라우저에 들어왔는지**를 시대 순으로 추적한다.

핵심 동력은 일관된다.

- ① 네이티브 앱(데스크톱·모바일)이 할 수 있는 일을 웹도 하게 만들려는 압력.
- ② Flash·Java Applet·ActiveX 같은 **플러그인을 표준 API로 흡수·제거**하려는 흐름.
- ③ 단일 회사(Microsoft IE6) 독점에서 **WHATWG·W3C·Khronos·IETF의 다자 표준화**로의 이동.

> **네이티브 앱(native app)** — 브라우저를 거치지 않고 운영체제 위에서 직접 도는 프로그램.\
> 예: 설치해서 쓰는 포토샵이나 스마트폰 앱스토어에서 받는 앱.

원문의 타임라인 도식을 세로로 옮기면 이렇다.

```text
웹 플랫폼 API 확장 타임라인

1998        DOM Level 1 (W3C 권고)
  |
1999        XMLHTTP (IE5 ActiveX)
  |
2004-2005   Gmail/Maps · "AJAX" 명명 · Canvas
  |
2008-2011   HTML5 흐름 · WebSocket(RFC 6455) · WebGL 1.0 · WebRTC 오픈소스
  |
2014-2015   Service Worker · PWA 명명 · fetch · Web Components(브라우저 탑재)
  |
2017        WebAssembly MVP 4개 브라우저 합의
  |
2021-2023   WebRTC 1.0 권고 · WebGPU(Chrome 113)
```

## 시대적 배경 — 문서에서 애플리케이션으로

*(이 편의 「시대 배경」에 해당한다)*

초기 웹(1991~)은 **하이퍼텍스트 문서**를 위한 것이었다.\
HTML은 마크업, HTTP는 문서 전송, 브라우저는 렌더러.\
1995년 Netscape가 JavaScript를, Microsoft가 JScript를 내놓으며 페이지에 동작을 넣을 수 있게 됐지만, 두 회사는 서로 다른 객체 모델(`document.layers` vs `document.all`)을 제공했다.\
같은 코드가 한 브라우저에서만 도는 **브라우저 전쟁**(Browser Wars)의 시대였고, 이는 표준화의 필요를 낳았다.

같은 일을 하려는데 두 갈래로 갈라져 있던 모습을 그리면 이렇다.

```text
같은 일을 하는데 회사마다 다른 객체 모델을 써야 했다

Netscape 쪽                        IE 쪽
+---------------------------+      +---------------------------+
| document.layers[...]      |      | document.all[...]         |
+---------------------------+      +---------------------------+
        |                                    |
        +----------- 둘 다 써야 한다 --------+
                          |
                          v
            브라우저마다 갈라지는 코드 (분기 지옥)
```

2000년대 중반까지 "리치한 웹 경험"은 대부분 **플러그인**이 담당했다.\
동영상·게임·애니메이션은 Adobe Flash, 엔터프라이즈 위젯은 Java Applet, Windows 통합은 ActiveX.\
플러그인은 강력했지만 브라우저 외부의 바이너리라 보안 구멍·크래시·배터리 소모·모바일 미지원(특히 2007년 iPhone의 Flash 거부)이라는 약점을 안고 있었다.\
2004년 결성된 **WHATWG**(Apple·Mozilla·Opera)는 "플러그인이 하던 일을 브라우저의 표준 기능으로 끌어들인다"는 방향으로 HTML5를 추진했고, 이 문서가 다루는 거의 모든 API가 그 큰 전략의 산물이다.

플러그인 방식과 표준 API 방식을 나란히 놓으면 이렇다.

```text
플러그인 시대                        표준 API 시대
+-----------------------------+      +-----------------------------+
| 브라우저                    |      | 브라우저                    |
|   +-------------------+     |      |   <video> 가 브라우저의     |
|   | Flash (외부       |     |      |   기본 기능                 |
|   |  바이너리)        |     |      |                             |
|   +-------------------+     |      |                             |
+-----------------------------+      +-----------------------------+
 보안 구멍·크래시·배터리            설치 없음·모바일에서도 동작
 소모·모바일 미지원
```

## 무엇이 바뀌었나

### 1. DOM 표준화 — 스크립트가 문서를 조작하는 공통 인터페이스

#### 무엇이며 왜 들어왔나

**무엇** — DOM(Document Object Model)은 HTML/XML 문서를 **객체 트리**로 표현해 스크립트가 내용·구조·스타일을 동적으로 읽고 바꾸게 하는, 언어 중립·플랫폼 중립 인터페이스다.

> **DOM(Document Object Model)** — 페이지를 나뭇가지 모양의 객체 묶음으로 본 것. 문서의 "조작 손잡이".\
> 예: `<ul>` 밑에 `<li>`가 매달린 구조를 그대로 객체로 만들어, 코드가 가지 하나를 더 달 수 있게 한다.

문서 하나가 트리로 보이는 모습을 그리면 이렇다.

```text
<html>
  |
  +-- <body>
        |
        +-- <ul>            <- getElementsByTagName("ul")[0] 로 잡는 가지
              |
              +-- <li> 기존 항목
              +-- <li> 새 항목   <- appendChild 로 방금 매단 가지
```

**왜 들어왔나** — 브라우저 전쟁이 만든 `document.all`(IE) ↔ `document.layers`(Netscape)의 분열을 끝내기 위해, W3C는 **1998년 10월 1일 DOM Level 1을 권고(Recommendation)로 발표**했다.\
이후 DOM Level 2(이벤트 모델·`getElementById`·네임스페이스), Level 3을 거쳐, 현재는 WHATWG의 **DOM Living Standard**가 단일 출처다.

> **권고(Recommendation)** — W3C가 "이제 이걸 표준으로 쓰라"고 확정 발표하는 최종 단계.\
> 예: 1998년 10월 1일 DOM Level 1이 이 단계에 올라 브라우저들이 맞춰 구현하기 시작했다.

**왜 이게 나은가** — DOM은 이 문서가 다루는 모든 후속 API의 **토대**다.\
AJAX로 받은 데이터를 화면에 반영하는 것도, Canvas 엘리먼트를 잡는 것도, Web Component를 정의하는 것도 전부 DOM 위에서 일어난다.

```javascript
// DOM Level 1: 트리 탐색과 생성
const list = document.getElementsByTagName("ul")[0];
const li = document.createElement("li");
li.appendChild(document.createTextNode("새 항목"));
list.appendChild(li);

// DOM Level 2 (2000): 표준 이벤트 모델 — IE의 attachEvent와 분열돼 있던 것을 통일
button.addEventListener("click", (e) => {
  e.preventDefault();
  console.log("clicked", e.target);
});
```

코드를 한 줄씩 읽으면 — 위쪽 네 줄이 "가지를 잡아 새 가지를 만들어 매단다"이고, 아래 블록이 "그 가지에 클릭이 오면 이걸 해라"를 표준 방식으로 등록하는 것이다.

> 표준 DOM 이전의 크로스 브라우저 분열은 jQuery(2006) 같은 라이브러리가 추상화로 메웠다.\
> DOM·이벤트 모델이 표준화되고 `querySelector`(Selectors API, 2008년경)가 들어오면서 jQuery의 존재 이유는 점차 옅어졌다.

### 2. AJAX — 페이지를 새로고침하지 않는 비동기 통신

#### XMLHttpRequest: 우연히 표준이 된 Microsoft의 사내 기술

**무엇** — 웹 애플리케이션의 결정적 도약은 **페이지 전체를 다시 받지 않고 서버와 데이터만 주고받는** 능력에서 나왔다.

전과 후를 나란히 놓으면 차이가 바로 보인다.

```text
풀 리로드 (AJAX 이전)              부분 갱신 (AJAX 이후)
+---------------------------+      +---------------------------+
| 버튼 클릭                 |      | 버튼 클릭                 |
|   -> 페이지 전체 재요청   |      |   -> 목록 데이터만 요청   |
|   -> 화면이 하얗게 깜빡   |      |   -> 목록 부분만 다시 그림|
|                           |      |   -> 화면은 그대로 유지   |
+---------------------------+      +---------------------------+
```

> **비동기(asynchronous)** — 요청을 보내 놓고 답을 기다리지 않은 채 다른 일을 계속하는 방식.\
> 예: 주문을 넣고 번호표를 받은 뒤 자리에 앉아 다른 일을 하다가, 호출되면 그때 받으러 가는 것.

**언제·왜** — 이 기술의 기원은 의외로 Microsoft다.\
Outlook Web Access 팀(Exchange 2000)이 웹에서 데스크톱 메일 같은 경험을 만들기 위해 백그라운드 HTTP 요청 객체를 만들었고, 이것이 **1999년 3월 IE5에 ActiveX 객체 `Microsoft.XMLHTTP`로 탑재**됐다.\
Mozilla가 2002년 네이티브 `XMLHttpRequest`로 이식했고, Safari·Opera가 뒤따랐다.

수년간 잘 알려지지 않던 이 기술은 **2004~2005년 Google이 Gmail과 Google Maps**에서 전면 활용하면서 폭발했다.\
새로고침 없이 지도를 끌고, 메일이 실시간으로 도착하는 경험은 "웹도 데스크톱 앱처럼 될 수 있다"는 증거였다.\
**2005년 2월 18일 Jesse James Garrett가 "Ajax: A New Approach to Web Applications**"라는 글에서 이 기법 묶음(Asynchronous JavaScript + XML)을 **AJAX**로 명명했다.\
W3C는 2006년부터 `XMLHttpRequest`를 표준화하기 시작했다.

```javascript
// XMLHttpRequest — 콜백 기반, 장황하고 상태코드 분기를 수동 처리
const xhr = new XMLHttpRequest();
xhr.open("GET", "/api/users");
xhr.onreadystatechange = function () {
  if (xhr.readyState === 4) {           // 4 = DONE
    if (xhr.status === 200) {
      const users = JSON.parse(xhr.responseText);
      render(users);
    }
  }
};
xhr.send();
```

**왜 fetch가 나왔나** — 코드에서 보이듯 `readyState === 4`(끝났나)와 `status === 200`(성공인가)을 사람이 손으로 갈라 줘야 한다.\
원문의 표현으로는 "콜백·`readyState`·이벤트가 뒤엉켜 쓰기 불편"했다.

> **콜백(callback)** — 나중에 어떤 일이 일어나면 불러 달라고 미리 넘겨 두는 함수.\
> 예: `onreadystatechange`에 함수를 꽂아 두면, 상태가 바뀔 때마다 브라우저가 그 함수를 대신 불러 준다.

#### fetch: Promise 기반의 현대적 후계자

**무엇** — 2015년 **WHATWG Fetch Standard**가 `fetch()`를 도입했다.\
Promise를 반환해 `async/await`와 자연스럽게 맞물리고, 요청·응답·헤더·CORS·캐시를 `Request`/`Response`/`Headers` 객체로 일급화했다.\
AJAX의 *개념*은 같지만 *API*가 현대화된 것이다.

> **Promise** — "결과는 나중에 준다"는 약속을 값처럼 들고 다닐 수 있게 만든 객체.\
> 예: `await fetch(...)`라고 쓰면 이 함수 안에서만 다음 줄을 미뤄 두고, 브라우저는 그동안 다른 일을 계속한다.

```javascript
// fetch — Promise 기반, async/await와 결합
async function loadUsers() {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const users = await res.json();
  render(users);
}
```

두 코드를 나란히 읽으면 차이가 분명하다 — 위쪽은 "상태가 바뀔 때마다 불러 줘"이고, 아래쪽은 "답이 오면 이 함수의 다음 줄부터 이어서 해"다.\
아래쪽도 브라우저를 멈춰 세우지 않는다 — 기다리는 동안 브라우저는 다른 일을 계속한다.

원문의 계보 도식을 세로로 옮기면 이렇다.

```text
XMLHTTP
IE5 ActiveX (1999)
    |
    v
XMLHttpRequest
Mozilla 네이티브 (2002)
    |
    v
Gmail/Maps 활용
+ 'AJAX' 명명 (2004-05)
    |
    v
W3C 표준화
(2006~)
    |
    v
fetch + Promise
WHATWG (2015)
```

**대가는 무엇인가** — XHR과 fetch는 둘 다 동일 출처 정책(Same-Origin Policy)과 **CORS** 위에서 동작한다.\
비동기 통신의 자유는 곧 교차 출처 보안 모델의 정교화를 요구했다.

> **동일 출처 정책(Same-Origin Policy)** — 한 사이트의 스크립트가 다른 사이트의 데이터를 함부로 읽지 못하게 막는 브라우저의 기본 규칙.\
> 예: 은행 사이트를 열어 둔 채 악성 사이트를 열어도, 악성 사이트 스크립트가 은행 응답을 읽지 못한다.

> **CORS(교차 출처 리소스 공유)** — 위 규칙에 예외를 열어 주는 절차. 서버가 "이 출처는 읽어도 된다"고 헤더로 허락한다.\
> 예: `api.example.com` 이 `www.example.com` 의 요청을 허용한다고 응답 헤더에 적어 주는 것.

### 3. 멀티미디어 — 플러그인 없이 그리고, 재생하고, 계산한다

#### `<video>`/`<audio>`: Flash를 대체한 선언적 미디어

**무엇** — 2000년대 웹 동영상은 사실상 Flash 독점이었다.\
HTML5는 **`<video>`·`<audio>` 엘리먼트**를 도입해 플러그인 없이 `<img>`처럼 선언적으로 미디어를 넣게 했다.

> **선언적(declarative)** — "무엇을 원한다"만 적고 방법은 브라우저에 맡기는 방식.\
> 예: `<video src="...">` 한 줄이면 재생기·버퍼링·디코딩을 브라우저가 알아서 한다.

**왜 이게 나은가** — 자막(`<track>`), 미디어 제어 JS API, 그리고 이후 **Media Source Extensions(MSE)**·**EME**가 더해지며 YouTube·Netflix급 적응형 스트리밍·DRM까지 표준 브라우저 기능으로 들어왔다.\
2010년 Apple이 iOS에서 Flash를 거부한 사건이 HTML5 비디오 전환을 결정적으로 가속했다.

> **적응형 스트리밍(adaptive streaming)** — 네트워크 상태에 따라 화질을 자동으로 올렸다 내렸다 하는 재생 방식.\
> 예: 지하철에서 화질이 잠깐 떨어졌다가 신호가 좋아지면 다시 또렷해지는 것.

> **DRM(디지털 저작권 관리)** — 유료 콘텐츠를 아무나 복제하지 못하게 거는 잠금 장치. 브라우저 쪽 규격이 EME다.\
> 예: 유료 스트리밍 영상을 브라우저가 재생은 하되, 그대로 복제해 가져가지는 못하게 한다.

```html
<video src="movie.mp4" controls width="640">
  <track kind="subtitles" src="ko.vtt" srclang="ko" label="한국어" />
</video>
```

이 세 줄이 예전에는 Flash 플레이어 설치 안내와 플러그인 로딩이 필요하던 자리다.

#### Canvas: 픽셀을 직접 그리는 2D 표면

**무엇** — **Canvas**는 2004년 **Apple이 Safari**(WebKit)에서 대시보드 위젯용으로 처음 도입했고, WHATWG가 HTML5 표준으로 받아들였다.\
`<canvas>`는 스크립트로 픽셀을 직접 그리는 **즉시 모드(immediate-mode)** 표면으로, 차트·이미지 편집·게임·시각화의 토대가 됐다.

> **즉시 모드(immediate-mode)** — 그린 도형을 기억해 두지 않고, 그리라고 할 때마다 그 자리에서 칠해 버리는 방식.\
> 예: 사각형을 그린 뒤 "그 사각형만 옮겨 줘"는 안 되고, 지우고 처음부터 다시 그려야 한다.

```javascript
const ctx = document.querySelector("canvas").getContext("2d");
ctx.fillStyle = "tomato";
ctx.fillRect(10, 10, 120, 80);
ctx.beginPath();
ctx.arc(200, 50, 40, 0, Math.PI * 2);
ctx.fill();
```

코드가 그리는 것을 좌표로 옮기면 이렇다.

```text
(0,0)
  +-------------------------------------------+
  |                                           |
  |   (10,10)                                 |
  |     +-----------+          .-----.        |
  |     |  120x80   |        (  r=40  )       |
  |     |  tomato   |          '-----'        |
  |     +-----------+        중심 (200,50)    |
  |                                           |
  +-------------------------------------------+
   fillRect(10,10,120,80)   arc(200,50,40,...)
```

#### WebGL: 브라우저 안의 GPU 3D

**무엇** — 2D Canvas로는 부족한 3D·고성능 그래픽을 위해, Mozilla의 Vladimir Vukićević가 2006년 시연한 **Canvas 3D 실험**이 출발점이 됐다.\
**Khronos Group**(OpenGL 표준 단체)이 2009년 WebGL 워킹 그룹을 꾸렸고(Apple·Google·Mozilla·Opera 참여), **2011년 3월 WebGL 1.0** 명세를 발표했다.\
WebGL은 **OpenGL ES 2.0을 JavaScript에 바인딩**한 저수준 API로, Canvas 엘리먼트에서 `getContext("webgl")`로 GPU 렌더링 컨텍스트를 얻는다.\
Three.js 같은 라이브러리가 그 위에서 3D를 대중화했다.\
(명세를 W3C가 아닌 Khronos가 호스팅하는 이유는 OpenGL ES 바인딩이라는 출신 때문이다.)

> **GPU(그래픽 처리 장치)** — 같은 계산을 수천 개씩 동시에 처리하도록 만든 칩.\
> 예: 화면의 픽셀 수백만 개 색을 한꺼번에 계산할 때 CPU보다 훨씬 빠르다.

> **저수준(low-level) API** — 편의 기능을 걷어내고 하드웨어에 가까운 조작을 직접 시키는 인터페이스.\
> 예: "정육면체를 그려 줘"가 아니라 "버퍼를 만들고 셰이더를 컴파일해 삼각형을 그려라"까지 직접 써야 한다.

> **셰이더(shader)** — GPU에서 도는 작은 프로그램. 각 점과 픽셀의 위치·색을 계산한다.\
> 예: WebGL에서는 GLSL이라는 언어로 셰이더를 써서 컴파일해 넘긴다.

```javascript
const gl = canvas.getContext("webgl");
gl.clearColor(0, 0, 0, 1);
gl.clear(gl.COLOR_BUFFER_BIT);
// 실제로는 셰이더(GLSL) 컴파일 → 버퍼 바인딩 → drawArrays 호출
```

주석이 말하듯, 실제 3D 한 장면을 그리려면 이 세 줄 뒤로 셰이더 컴파일과 버퍼 바인딩이 줄줄이 따라온다 — 그래서 Three.js 같은 라이브러리가 그 위에 올라앉았다.

#### WebGPU: 현대 GPU와 범용 연산(2023)

**무엇** — WebGL은 10년 이상 표준이었지만, 내부적으로 노후한 OpenGL ES 모델에 묶여 있었고 **GPU 범용 연산**(GPGPU)을 일급으로 지원하지 못했다.\
W3C의 **"GPU for the Web" 그룹**이 2017년부터 Apple·Google·Mozilla·Microsoft·Intel과 함께 차세대 API를 설계했고, **2023년 5월 2일 Chrome 113에 WebGPU가 정식 탑재**됐다.

> **GPGPU(GPU 범용 연산)** — 그래픽이 아닌 일반 계산을 GPU에 시키는 것.\
> 예: 머신러닝 학습이나 물리 시뮬레이션처럼 같은 계산을 수만 번 반복하는 일을 GPU에 맡긴다.

> **컴퓨트 셰이더(compute shader)** — 화면에 그리는 것이 목적이 아니라 계산만 하는 셰이더.\
> 예: 행렬 곱셈을 GPU에 던져 결과 숫자만 돌려받는 용도.

**왜 이게 나은가** — WebGPU는 Vulkan/Direct3D 12/Metal 같은 현대 그래픽 API에 대응하며, **컴퓨트 셰이더**(compute shader)로 GPU를 그래픽뿐 아니라 머신러닝·물리 시뮬레이션 같은 범용 병렬 계산에 쓰게 한다.\
즉 브라우저가 GPU 컴퓨팅 플랫폼이 된 것이다.

원문의 그래픽 계보 도식을 세로로 옮기면 이렇다.

```text
Canvas 2D
Apple, 2004
    |
    v
WebGL 1.0
Khronos, 2011
(OpenGL ES 2.0)
    |
    v
WebGPU
Chrome 113, 2023
(Vulkan/D3D12/Metal · compute)
```

### 4. 통신 — 서버가 먼저 말하고, 브라우저끼리 직접 연결한다

#### WebSocket: 양방향 영속 연결

**무엇** — AJAX·폴링은 "클라이언트가 묻고 서버가 답하는" 단방향 모델이라, 채팅·주식 시세·실시간 알림처럼 **서버가 먼저 푸시**해야 하는 경우엔 잦은 폴링으로 낭비가 컸다.\
**WebSocket**은 단일 TCP 연결 위에서 **양방향·전이중(full-duplex)** 통신을 제공한다.

> **폴링(polling)** — 새 소식이 있는지 클라이언트가 주기적으로 계속 물어보는 방식.\
> 예: 1초마다 "새 메시지 있어요?"를 서버에 묻는 것 — 대부분의 답은 "없어요"라 낭비가 크다.

> **전이중(full-duplex)** — 양쪽이 동시에 말할 수 있는 연결.\
> 예: 무전기(한 번에 한 쪽)가 아니라 전화기(둘 다 동시에)에 가깝다.

폴링과 WebSocket을 나란히 놓으면 낭비가 보인다.

```text
폴링                                WebSocket
클라 --"새 거 있어?"--> 서버        클라 ====== 연결 유지 ====== 서버
클라 <--"없어"--------- 서버              <-- 생기면 서버가 먼저 보냄
클라 --"새 거 있어?"--> 서버              <-- 또 보냄
클라 <--"없어"--------- 서버
클라 --"새 거 있어?"--> 서버
클라 <--"있어!"-------- 서버
  위 그림에서 6번 중 5번이 헛걸음     연결 1번, 소식 있을 때만 전송
```

**언제·왜** — HTTP 핸드셰이크로 시작해 프로토콜을 업그레이드하는 방식이며, 표준화가 W3C/WHATWG에서 **IETF로 이관**(2010년 2월)되어 **2011년 12월 RFC 6455**로 확정됐다.\
브라우저 API는 같은 시기 W3C가 정의했다.

> **핸드셰이크(handshake)** — 본 통신을 시작하기 전에 규칙을 맞추는 짧은 인사 절차.\
> 예: WebSocket은 평범한 HTTP 요청으로 시작해 "이 연결을 WebSocket으로 바꾸자"고 합의한 뒤 전환한다.

> **RFC** — IETF가 인터넷 표준을 번호를 붙여 펴내는 문서 형식.\
> 예: WebSocket 프로토콜의 정본은 RFC 6455 문서다.

```javascript
const ws = new WebSocket("wss://example.com/chat");
ws.onopen = () => ws.send(JSON.stringify({ join: "room-1" }));
ws.onmessage = (e) => appendMessage(JSON.parse(e.data)); // 서버가 먼저 푸시
```

주석이 붙은 마지막 줄이 핵심이다 — 클라이언트가 묻지 않았는데도 서버가 보낸 메시지가 여기로 들어온다.

#### WebRTC: 브라우저 간 P2P 실시간 미디어

**무엇** — 화상회의·음성통화는 오랫동안 플러그인(Flash/Skype 등)의 영역이었다.\
**WebRTC**는 브라우저끼리(또는 디바이스끼리) **서버를 거치지 않는 P2P로 오디오·비디오·임의 데이터**를 주고받게 한다.

> **P2P(peer-to-peer)** — 가운데 서버를 두지 않고 참가자끼리 직접 연결하는 방식.\
> 예: 화상통화 영상이 상대 브라우저로 곧장 가면, 서버를 거칠 때보다 지연이 줄고 서버 비용도 준다.

플러그인 시대와 표준 API 시대를 나란히 놓으면 이렇다.

```text
플러그인 (브라우저 밖 바이너리)      표준 API (WebRTC)
+-----------------------------+      +-----------------------------+
| Flash/Skype 같은 프로그램을 |      | 브라우저에 이미 들어 있다   |
| 따로 깔아야 화상회의가 됐다 |      | 나 <---- 영상 ----> 상대    |
|                             |      | (서버를 거치지 않는 P2P)    |
+-----------------------------+      +-----------------------------+
```

**언제·왜** — 뿌리는 Google이 2010년 인수한 **Global IP Solutions**의 코덱·미디어 엔진이며, Google이 이를 **2011년 오픈소스로 공개**하고 Mozilla·W3C·IETF와 표준화를 추진했다.

**왜 오래 걸렸나** — NAT 통과(ICE/STUN/TURN)·미디어 협상이 얽힌 복잡한 표준이라 시간이 걸렸고, **WebRTC 1.0은 2021년 1월 26일에야 W3C 권고**가 됐다(동시에 IETF 표준군으로도 확정).

> **NAT 통과(NAT traversal)** — 공유기 뒤에 숨은 두 컴퓨터가 서로를 찾아 직접 연결하게 돕는 기법.\
> 예: 집 공유기와 회사 공유기 뒤에 있는 두 사람이 통화하려면 ICE/STUN/TURN이 중간에서 길을 찾아 준다.

2020년 팬데믹기의 Google Meet·화상수업·디스코드 음성 채널이 모두 이 기술 위에 선다.

```javascript
const pc = new RTCPeerConnection();
const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
stream.getTracks().forEach((t) => pc.addTrack(t, stream)); // 내 미디어를 P2P로 송신
pc.ontrack = (e) => (remoteVideo.srcObject = e.streams[0]); // 상대 미디어 수신
```

네 줄을 흐름으로 읽으면 — 연결을 만들고(1행), 카메라·마이크를 허락받아 얻고(2행), 그것을 상대에게 보내고(3행), 상대 것을 받아 화면에 붙인다(4행).

### 5. 오프라인·앱화 — 네트워크가 끊겨도, 홈 화면에서 실행된다

#### Web Storage(localStorage): 쿠키를 넘어선 클라이언트 저장소

**무엇** — HTML5 이전, 클라이언트 측 영속 데이터는 **쿠키**뿐이었고 모든 HTTP 요청에 실려 다녀 용량·성능 모두 비효율적이었다.\
**Web Storage**(처음엔 "DOM Storage")는 키–값 저장소를 제공한다.\
`localStorage`(만료 없음·영속)와 `sessionStorage`(탭 세션 한정)로 나뉘며, 서버로 전송되지 않고 수 MB를 저장한다.\
구조화된 대용량 데이터에는 이후 **IndexedDB**가 더해졌다.

> **쿠키(cookie)** — 서버가 브라우저에 맡겨 두고 매 요청마다 자동으로 되돌려받는 작은 데이터.\
> 예: 로그인 세션 식별자가 여기 담기는데, 요청마다 따라다니므로 용량이 커지면 전부 느려진다.

전후를 나란히 놓으면 이렇다.

```text
쿠키만 있던 시절                    Web Storage 이후

요청 1 --[쿠키 동봉]--> 서버        요청 1 --[쿠키만]--> 서버
요청 2 --[쿠키 동봉]--> 서버        요청 2 --[쿠키만]--> 서버
요청 3 --[쿠키 동봉]--> 서버        요청 3 --[쿠키만]--> 서버

저장할 데이터까지 쿠키에 담아       theme 등 큰 데이터는 브라우저에만
매 요청마다 실려 다닌다             남고 요청에 실리지 않는다
                                    (세션 쿠키는 그대로 실려 다닌다)
```

```javascript
localStorage.setItem("theme", "dark");          // 영속 저장
const theme = localStorage.getItem("theme");     // 다음 방문에도 유지
```

#### Service Worker: 네트워크를 가로채는 프로그래머블 프록시

**무엇** — 오프라인 동작의 핵심은 **Service Worker**다.\
페이지와 분리된 백그라운드 스크립트로, 페이지의 모든 네트워크 요청을 **가로채는 프로그래머블 프록시**처럼 동작한다.\
캐시에서 응답하거나, 백그라운드 동기화·푸시 알림을 처리한다.

> **프록시(proxy)** — 요청이 목적지로 가기 전에 중간에서 받아 대신 처리하거나 넘겨 주는 중계자.\
> 예: 페이지가 이미지를 요청하면 Service Worker가 먼저 받아, 캐시에 있으면 네트워크에 나가지 않고 그걸 돌려준다.

요청이 지나가는 길을 세로로 그리면 이렇다.

```text
페이지가 /logo.png 를 요청
        |
        v
Service Worker 의 fetch 이벤트가 먼저 받는다
        |
        +-- 캐시에 있나? --예--> 캐시에 있는 응답을 돌려준다 (네트워크 안 감)
        |
        +-- 없으면 -----------> fetch(event.request) 로 네트워크에 나간다
```

**언제·왜** — (실패했던 AppCache의 후계로) **2014~2015년 Chrome 40에 탑재**(2015년 1월 안정화)됐다.\
이 한 조각이 "웹은 항상 온라인이어야 한다"는 전제를 깼다.

```javascript
// 등록 (페이지 측)
navigator.serviceWorker.register("/sw.js");

// sw.js — fetch 가로채 캐시 우선 응답 → 오프라인 동작
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
```

마지막 줄의 `cached || fetch(...)`가 위 그림의 두 갈래를 그대로 옮긴 것이다.

#### PWA와 Web App Manifest: 웹을 설치 가능한 앱으로

**무엇** — Service Worker(오프라인·재방문성)와 **Web App Manifest**(앱 이름·아이콘·시작 URL·표시 모드를 담은 JSON)를 결합하면, 웹사이트를 **홈 화면에 설치하고 전체화면 독립 앱처럼 실행**할 수 있다.\
**2015년 6월 15일 Google의 Alex Russell과 디자이너 Frances Berriman이 이 부류를 "Progressive Web App(PWA)"으로 명명**했다.

**왜 이게 나은가** — 핵심 속성은 신뢰 가능(HTTPS)·설치 가능·오프라인 동작·재참여(푸시) 등이다.\
PWA는 별도 신기술이 아니라 **Service Worker + Manifest + HTTPS의 조합에 붙인 이름**이며, 앱스토어 없이 배포되는 설치형 웹앱의 표준 경로가 됐다.

원문 도식대로, 셋이 모여 하나가 된다.

```text
HTTPS                 Service Worker        Web App Manifest
(보안 출처)           (오프라인·푸시)       (아이콘·시작 URL)
     |                       |                      |
     +-----------------------+----------------------+
                             |
                             v
                            PWA
                     설치 가능한 웹앱
```

```json
// manifest.json — 설치 메타데이터
{
  "name": "My App",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "icons": [{ "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" }]
}
```

`"display": "standalone"`이 주소창 없는 독립 창으로 뜨게 하는 스위치이고, `icons`가 홈 화면에 박히는 아이콘이다.

### 6. 컴포넌트 — 캡슐화된 재사용 UI를 브라우저 표준으로

**무엇** — 프레임워크(React·Angular 등)는 컴포넌트화를 라이브러리로 풀었지만, **브라우저 네이티브** 재사용 컴포넌트를 향한 표준도 따로 자랐다.\
**Web Components**는 **2011년 Alex Russell이 Fronteers 컨퍼런스에서 처음 제안**했고, Google의 **Polymer**(2013) 폴리필이 초기 실험을 이끌었다.

> **폴리필(polyfill)** — 아직 브라우저에 없는 표준 기능을 JS로 흉내 내 미리 쓰게 해 주는 코드.\
> 예: Shadow DOM이 없던 시절 Polymer가 그 동작을 비슷하게 흉내 내 줬다.

세 가지 표준의 묶음이다.

- **Custom Elements**: `<my-card>` 같은 자기 정의 HTML 태그를 생애주기 콜백과 함께 등록.
- **Shadow DOM**: 컴포넌트 내부 DOM·스타일을 **외부와 격리**(캡슐화)해, 전역 CSS 충돌을 차단.
- **HTML Templates**: `<template>`로 렌더링되지 않는 재사용 마크업 조각을 선언.

> **캡슐화(encapsulation)** — 안쪽 사정을 바깥에서 보거나 건드리지 못하게 벽을 두르는 것.\
> 예: 컴포넌트 안의 `p { color: tomato; }`가 페이지 전체의 `<p>`를 물들이지 않는다.

격리의 효과를 나란히 놓으면 이렇다.

```text
격리 없음 (전역 CSS)                  Shadow DOM 격리
+------------------------------+      +------------------------------+
| 페이지 CSS: p { color:red }  |      | 페이지 CSS: p { color:red }  |
|   -> 컴포넌트 안 <p> 까지    |      |   -> 벽에 막혀 안 들어감     |
|      빨갛게 물든다           |      |   -> 안쪽은 tomato 유지      |
+------------------------------+      +------------------------------+
```

**언제 쓸 수 있게 됐나** — 브라우저 구현은 표준 협상(v0→v1)으로 시간이 걸려 **Chrome·Safari에 2016년경(v1)**, Firefox 2018년, Edge는 Chromium 전환(2020) 이후 들어왔다.

```javascript
class MyCard extends HTMLElement {
  connectedCallback() {
    const shadow = this.attachShadow({ mode: "open" }); // 격리된 Shadow DOM
    shadow.innerHTML = `
      <style>p { color: tomato; }</style>   <!-- 외부 CSS와 충돌하지 않음 -->
      <p><slot></slot></p>`;
  }
}
customElements.define("my-card", MyCard); // <my-card>여기 내용</my-card>
```

마지막 줄의 `customElements.define`이 브라우저에 새 태그 이름을 등록하는 자리다.

### 7. 네이티브 코드와 디바이스 — WebAssembly, 그리고 하드웨어 접근

#### WebAssembly: 브라우저에서 거의 네이티브 속도로

**무엇** — JavaScript는 유연하지만, 게임 엔진·영상 인코딩·CAD·암호화처럼 **연산이 무거운** 작업엔 한계가 있었다.\
**WebAssembly**(Wasm)는 브라우저가 실행하는 **이식 가능한 저수준 바이너리 명령 형식**이다.\
C/C++/Rust 등으로 컴파일한 코드를 거의 네이티브에 가까운 속도로 돌리며, JavaScript와 같은 샌드박스·같은 메모리 모델 안에서 상호 운용한다.

> **바이너리 명령 형식(binary instruction format)** — 사람이 읽는 소스가 아니라 기계가 바로 읽는 압축된 명령 묶음.\
> 예: 텍스트 JS 파일과 달리 `.wasm` 은 해석 없이 곧장 기계어로 옮기기 좋은 형태다.

> **컴파일(compile)** — 사람이 쓴 소스 코드를 기계가 실행할 형태로 미리 번역하는 것.\
> 예: Rust로 쓴 계산 코드를 `.wasm` 파일로 번역해 두고, 브라우저는 그것을 적재해 호출한다.

경로를 세로로 그리면 이렇다.

```text
C / C++ / Rust 로 쓴 코드
        |
        v  컴파일
calc.wasm  (바이너리 명령 형식)
        |
        v  브라우저가 적재
WebAssembly.instantiateStreaming(fetch("calc.wasm"))
        |
        v
instance.exports.fibonacci(40)  <- JS 에서 함수처럼 호출
```

**언제·왜** — asm.js(2013, Mozilla)와 Google PNaCl의 경험을 모아, **4개 브라우저(Chrome·Edge·Firefox·WebKit)가 2017년 3월 MVP 설계 합의**에 도달했고 그달에 줄줄이 기본 탑재됐다(Firefox 52·Chrome 57, 이후 Safari 11·Edge 16).

> **MVP(Minimum Viable Product)** — 일단 쓸 만한 최소한의 범위로 먼저 확정한 1차 규격.\
> 예: 기능을 다 넣지 않고 "이만큼은 네 브라우저가 똑같이 지원한다"를 먼저 못박은 것.

**왜 이게 나은가** — Figma·AutoCAD 웹·게임 엔진이 Wasm 위에서 돈다.\
**브라우저가 JavaScript 전용 런타임에서 다언어 실행 플랫폼이 된 분기점**이다.

```javascript
// Rust/C++ → .wasm 으로 컴파일한 모듈을 적재해 호출
const { instance } = await WebAssembly.instantiateStreaming(fetch("calc.wasm"));
const result = instance.exports.fibonacci(40); // 네이티브에 가까운 속도
```

#### 디바이스·시스템 API: OS 기능을 표준 권한 모델로

**무엇** — 앱화의 마지막 조각은 **하드웨어·OS 기능 접근**이다.\
브라우저는 네이티브 앱이 쓰던 기능들을 **사용자 권한(permission) 모델** 위에서 하나씩 표준 API로 열었다.

- **Geolocation API**: 위치 정보(`navigator.geolocation`) — 지도·배달 앱.
- **File API / File System Access**: 로컬 파일 읽기·쓰기 — 웹 기반 에디터·이미지 편집.
- **Notification API**: OS 알림 센터에 푸시 — Service Worker의 백그라운드 푸시와 결합.
- 그 밖에 **MediaDevices**(카메라·마이크), **Web Bluetooth / WebUSB / WebSerial**(주변기기), **Clipboard**, **Gamepad**, **Sensor**(가속도·자이로) 등.

> **권한 모델(permission model)** — 위험한 기능은 사용자가 명시적으로 허락해야만 열리게 만든 구조.\
> 예: 사이트가 위치를 요청하면 "허용/차단" 팝업이 먼저 뜨고, 차단하면 코드가 실패한다.

> **보안 컨텍스트(secure context)** — HTTPS처럼 도청·변조가 막힌 연결에서만 기능을 열어 주는 조건.\
> 예: `http://` 로 열린 페이지에서는 카메라나 Service Worker가 아예 동작하지 않는다.

```javascript
// 권한 요청 → 승인 시에만 기능 사용 (사용자 동의 게이트)
const perm = await Notification.requestPermission();
if (perm === "granted") new Notification("작업이 완료되었습니다");

navigator.geolocation.getCurrentPosition((pos) =>
  console.log(pos.coords.latitude, pos.coords.longitude)
);
```

**공통 설계 원칙** — 이 API들의 공통 설계 원칙은 "**강력함은 명시적 사용자 동의와 보안 컨텍스트(HTTPS) 뒤에**"다.\
네이티브급 권한을 열되, 출처별 권한·사용자 제스처 요구·보안 출처 제한으로 남용을 막는다.

관문을 세로로 그리면 이렇다.

```text
코드가 카메라를 요청
        |
        v
HTTPS 인가? ---- 아니오 ----> 거부 (보안 컨텍스트 아님)
        |
       예
        |
        v
사용자가 허용했나? -- 아니오 --> 거부
        |
       예
        |
        v
    카메라 스트림을 받는다
```

## 왜 그렇게 갔나 — 남은 선택지와 트레이드오프

### 플러그인이냐 표준 API냐

이 문서 전체를 관통하는 갈림길은 하나다 — 새 능력을 **브라우저 밖 플러그인으로 넣을 것인가, 브라우저의 표준 기능으로 넣을 것인가**.\
원문이 두 쪽에 대해 실제로 서술한 내용만 마주 놓으면 이렇다.

| | 플러그인 (Flash·Java Applet·ActiveX) | 표준 API (HTML5 이후) |
|---|---|---|
| 강점 | 강력했다 — 동영상·게임·애니메이션·엔터프라이즈 위젯·Windows 통합을 담당 | 표준·오픈·크로스플랫폼 |
| 약점 | 브라우저 외부의 바이너리라 보안 구멍·크래시·배터리 소모·모바일 미지원 | (원문에 별도 서술 없음) |

표준이 플러그인이 하던 일을 하나씩 흡수한 결과 **Flash·Silverlight·Java Applet·ActiveX는 사실상 소멸**했다.\
그중 비디오 전환은 2010년 Apple의 iOS Flash 거부가 결정적으로 가속했다.

### 표준을 누가 만드는가 — 단일 벤더에서 다자 모델로

표준화 거버넌스의 변화도 본질적이다.\
IE6 시절의 사실상 단일 벤더 통제에서, **WHATWG(HTML/DOM Living Standard)·W3C·Khronos(WebGL/WebGPU)·IETF**(WebSocket/WebRTC 프로토콜)가 분담하고 4대 브라우저 엔진이 합의로 출시하는 다자 모델로 옮겨갔다.

```text
IE6 시절                            오늘
+---------------------------+      +---------------------------+
| 한 회사가 사실상 결정     |      | WHATWG   — HTML/DOM       |
|                           |      | W3C      — 다수 API 권고  |
|                           |      | Khronos  — WebGL/WebGPU   |
|                           |      | IETF     — WebSocket/RTC  |
+---------------------------+      +---------------------------+
                                    4대 엔진이 합의로 출시
```

WebAssembly의 "4개 브라우저 동시 합의"(2017)나 WebGPU의 6년 합의 설계(2017→2023)가 그 성숙의 상징이다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다)*

웹 플랫폼 API의 25년은 "**문서 뷰어 → 애플리케이션 플랫폼 → 범용 런타임**"으로의 단계적 이동이다.\
각 API는 독립적으로 보이지만, 큰 그림에선 **플러그인이 하던 일(미디어=Flash, 3D·게임=Java/Flash, 화상=Skype, 네이티브 연산=ActiveX)을 표준·오픈·크로스플랫폼 API로 흡수·대체**하는 하나의 전략이었다.

오늘날 브라우저는 **운영체제의 많은 부분을 추상화한 가상 플랫폼**이다.\
무엇이 어디에 대응되는지 짝지으면 이렇다.

```text
운영체제가 주던 것              브라우저가 표준 API 로 주는 것
--------------------------     ------------------------------
네트워킹                       fetch · WebSocket · WebRTC
GPU                            WebGPU
영속 저장                      localStorage · IndexedDB · Cache
백그라운드 실행                Service Worker
설치·재참여                    PWA (Manifest + 푸시)
다언어 네이티브 코드           WebAssembly
하드웨어                       파일 · 카메라 · 블루투스
```

"Write once, run anywhere"의 약속을 Java가 JVM으로 좇았다면, 웹은 **모두가 이미 깔아둔 런타임인 브라우저**를 통해 그것을 실현했다 — 설치도, 배포 채널의 허가도 없이 URL 하나로.

## 용어 풀이

- **API(Application Programming Interface)** — 기능을 쓰라고 정해 놓은 호출 규격.
- **DOM(Document Object Model)** — 문서를 객체 트리로 표현해 스크립트가 조작하게 하는 인터페이스. 1998-10-01 Level 1 권고.
- **DOM Living Standard** — 오늘날 DOM 명세의 단일 출처. WHATWG가 관리한다.
- **권고(Recommendation)** — W3C가 표준을 확정 발표하는 최종 단계.
- **플러그인(plugin)** — 브라우저 밖에서 돌며 화면을 끼워 넣던 외부 프로그램(Flash·Java Applet·ActiveX).
- **XMLHttpRequest / XMLHTTP** — 페이지를 새로 받지 않고 서버와 데이터만 주고받는 요청 객체. 1999-03 IE5의 ActiveX가 기원.
- **AJAX** — Asynchronous JavaScript + XML. 2005-02-18 Jesse James Garrett이 명명한 기법 묶음.
- **fetch** — 2015년 WHATWG Fetch Standard가 도입한 Promise 기반 후계 API.
- **Promise** — "결과는 나중에" 라는 약속을 값처럼 다루는 객체.
- **동일 출처 정책(Same-Origin Policy)** — 다른 출처의 데이터를 함부로 읽지 못하게 막는 기본 규칙.
- **CORS** — 그 규칙에 서버가 명시적으로 예외를 열어 주는 절차.
- **`<video>` / `<audio>`** — 플러그인 없이 선언적으로 미디어를 넣는 HTML5 엘리먼트.
- **MSE(Media Source Extensions) / EME** — 적응형 스트리밍과 DRM을 표준 브라우저 기능으로 만든 확장.
- **Canvas** — 2004년 Apple이 Safari에 도입한 즉시 모드 2D 그리기 표면.
- **즉시 모드(immediate-mode)** — 그린 도형을 기억하지 않고 그 자리에서 칠해 버리는 방식.
- **WebGL** — OpenGL ES 2.0을 JavaScript에 바인딩한 저수준 3D API. 2011년 3월 1.0, Khronos 호스팅.
- **Khronos Group** — OpenGL 계열 표준을 만드는 단체. WebGL·WebGPU 명세를 맡는다.
- **셰이더(shader) / GLSL** — GPU에서 도는 작은 프로그램과 그것을 쓰는 언어.
- **WebGPU** — Vulkan/Direct3D 12/Metal에 대응하는 차세대 API. 2023-05-02 Chrome 113 탑재.
- **GPGPU / 컴퓨트 셰이더** — GPU를 그래픽이 아닌 범용 병렬 계산에 쓰는 것과 그 전용 셰이더.
- **WebSocket** — 단일 TCP 연결 위의 양방향·전이중 통신. 2011년 12월 RFC 6455.
- **폴링(polling)** — 새 소식이 있는지 주기적으로 계속 물어보는 방식.
- **WebRTC** — 브라우저 간 P2P 오디오·비디오·데이터 전송. 2021-01-26 W3C 권고.
- **NAT 통과(ICE/STUN/TURN)** — 공유기 뒤의 두 기기가 직접 연결하도록 돕는 기법들.
- **Web Storage(localStorage/sessionStorage)** — 서버로 전송되지 않는 브라우저 측 키–값 저장소.
- **IndexedDB** — 구조화된 대용량 데이터를 위한 브라우저 내장 데이터베이스.
- **Service Worker** — 네트워크 요청을 가로채는 백그라운드 프로그래머블 프록시. 2015년 1월 Chrome 40 안정화.
- **AppCache** — Service Worker 이전의 오프라인 캐시 방식. 실패한 선행 기술로 원문에 언급된다.
- **Web App Manifest** — 앱 이름·아이콘·시작 URL·표시 모드를 담은 JSON 파일.
- **PWA(Progressive Web App)** — Service Worker + Manifest + HTTPS의 조합에 붙인 이름. 2015-06-15 명명.
- **Web Components** — Custom Elements · Shadow DOM · HTML Templates 세 표준의 묶음.
- **Shadow DOM** — 컴포넌트 내부 DOM·스타일을 외부와 격리하는 장치.
- **폴리필(polyfill)** — 아직 없는 표준 기능을 JS로 흉내 내 주는 코드. Polymer(2013)가 초기 사례.
- **WebAssembly(Wasm)** — 브라우저가 실행하는 이식 가능한 저수준 바이너리 명령 형식. 2017년 3월 MVP 합의.
- **asm.js / PNaCl** — Wasm 이전에 같은 문제를 노렸던 Mozilla·Google의 선행 기술.
- **권한 모델(permission model)** — 위험한 기능을 사용자 동의 뒤에 두는 구조.
- **보안 컨텍스트(secure context)** — HTTPS 등 안전한 연결에서만 기능을 여는 조건.
- **WHATWG / W3C / Khronos / IETF** — 오늘날 웹 표준을 분담하는 네 조직.

## 참고 출처

- [Document Object Model (DOM) Level 1 Specification — W3C Recommendation, 1998-10-01](https://www.w3.org/TR/1998/REC-DOM-Level-1-19981001/)
- [W3C Press Release: DOM Level 1 as a W3C Recommendation (1998)](https://www.w3.org/Press/1998/DOM-REC)
- [Ajax (programming) — Wikipedia](https://en.wikipedia.org/wiki/Ajax_(programming))
- [XMLHttpRequest — Wikipedia](https://en.wikipedia.org/wiki/XMLHttpRequest)
- [Fetch Standard — WHATWG](https://fetch.spec.whatwg.org/)
- [Fetch API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [WebGL — Wikipedia](https://en.wikipedia.org/wiki/WebGL)
- [Khronos Releases Final WebGL 1.0 Specification](https://www.khronos.org/news/press/khronos-releases-final-webgl-1.0-specification)
- [Chrome ships WebGPU — Chrome for Developers Blog](https://developer.chrome.com/blog/webgpu-release)
- [WebGPU — Wikipedia](https://en.wikipedia.org/wiki/WebGPU)
- [RFC 6455 — The WebSocket Protocol (IETF, 2011)](https://datatracker.ietf.org/doc/html/rfc6455)
- [WebSocket — Wikipedia](https://en.wikipedia.org/wiki/WebSocket)
- [WebRTC 1.0 is a W3C Recommendation (2021-01-26)](https://www.w3.org/blog/news/archives/8897)
- [WebRTC — Wikipedia](https://en.wikipedia.org/wiki/WebRTC)
- [Web Storage — Wikipedia](https://en.wikipedia.org/wiki/Web_storage)
- [Service Worker API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Progressive web app — Wikipedia](https://en.wikipedia.org/wiki/Progressive_web_app)
- [Progressive Apps: Escaping Tabs Without Losing Our Soul — Infrequently Noted (Alex Russell, 2015)](https://infrequently.org/2015/06/progressive-apps-escaping-tabs-without-losing-our-soul/)
- [Web Components — Wikipedia](https://en.wikipedia.org/wiki/Web_Components)
- [Shadow DOM v1 — web.dev](https://web.dev/articles/shadowdom-v1)
- [WebAssembly — Wikipedia](https://en.wikipedia.org/wiki/WebAssembly)
- [WebAssembly consensus and end of Browser Preview (public-webassembly@w3.org, 2017-02)](https://lists.w3.org/Archives/Public/public-webassembly/2017Feb/0002.html)
- [WebAssembly browser preview — V8 Blog](https://v8.dev/blog/webassembly-browser-preview)
