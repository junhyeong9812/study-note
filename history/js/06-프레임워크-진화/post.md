# 06. 프론트엔드 프레임워크 진화

> 원본: `~/project/js-history/06-프레임워크-진화.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-19).\
> 연도·인명·버전·코드·표는 원문 그대로다.\
> ASCII 도식 7개(그중 3개는 원문 mermaid 그림을 글자로 옮긴 것)와 「한눈에」의 통증 비유(대응표 포함), 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 브라우저 호환성을 통일한 jQuery에서, 양방향 바인딩의 AngularJS, 가상 DOM·단방향·컴포넌트의 React를 거쳐, 시그널·서버 컴포넌트·아일랜드로 이어지는 약 20년의 흐름. 매 단계는 **직전 시대가 만든 고통**에 대한 응답이었고, 그 해법은 다시 새로운 고통(반작용)을 낳아 다음 단계를 불렀다. 이 문서는 "왜 등장했나 / 무엇을 풀었나 / 어떤 반작용을 남겼나"의 사슬로 그 진화를 읽는다.

이 문서의 주 비유는 **아픈 곳을 고치면 다른 곳이 아파지는 몸**이다 — 아래 대응표에서만 쓰고, 본문은 원문의 낱말(고통·해법·반작용)을 그대로 쓴다.\
용어 블록에서만 잠깐 쓰는 국소 비유(설계도·배선 등)가 몇 개 더 있다.

| 비유 | 실체 |
|------|------|
| 지금 아픈 곳 | 직전 시대의 고통 |
| 통증을 없애려고 바꾼 자세·도구 | 새 추상화(프레임워크) |
| 그 때문에 새로 아파진 곳 | 해법이 만든 새 비용 — 원문의 「반작용」 |
| 그래서 또 자세를 바꾼다 | 다음 세대의 등장 |

- 이 20년은 매번 **"직전 것이 만든 고통"에 응답한 역사**다.\
  원문이 "매 단계는 직전 시대가 만든 고통에 대한 응답이었다"고 적은 그대로다.
- 그래서 각 절의 골격이 항상 같다 — **왜 등장했나 / 무엇을 풀었나 / 반작용.**\
  이 세 소제목은 원문이 절마다 직접 반복해 쓴 것이다.
- 원문은 이 흐름을 관통하는 축이 **둘**이라고 말한다.\
  ① 반응성을 어떻게 추적하나 ② JS를 어디서·얼마나 실행하나.
- 그리고 원문의 결론은 한 문장이다.\
  모든 프레임워크는 "상태가 진실이고 화면은 그 함수"(`UI = f(state)`)라는 한 점으로 수렴해 왔다.

> **프레임워크 / 라이브러리** — 화면을 만드는 일의 뼈대를 정해 주는 도구. 원문은 React를 "의도적으로 뷰 라이브러리일 뿐"이라고 구분해 적는다.\
> 예: 뷰 라이브러리 위에 라우팅·데이터 로딩·SSR/SSG·번들링까지 묶어 주면 메타프레임워크(Next.js), 화면 그리는 부분만 주면 뷰 라이브러리(React)다.

> **상태(state)** — 화면에 보여야 할 값들. "지금 로그인했나", "장바구니에 몇 개인가" 같은 것.\
> 예: 원문 코드의 `count`가 상태이고, 화면에 찍히는 `클릭 수: {count}`가 그 상태의 결과다.

> **반응성(reactivity)** — 상태가 바뀌었을 때 화면의 어디를 다시 그릴지 찾아내는 장치.\
> 예: `count`가 0에서 1로 바뀌면 화면이 그에 따라 바뀌는 것. 얼마나 좁은 범위만 다시 그리는지는 시대마다 다르다 — 원문의 축①이 수동 조작 → 더티 체킹 → 가상 DOM → 시그널로 점점 좁혀 온 역사다.

## 한눈에 보는 타임라인

원문의 mermaid 타임라인을 글자 도식으로 옮기면 이렇다(제목·연도·항목 문구는 그대로다).

```text
프론트엔드 프레임워크 변천사

2006     jQuery — DOM·브라우저 통일
2010     Backbone / Knockout — 구조(MVC·MVVM) 도입
         AngularJS — 양방향 바인딩·DI
2013     React — 가상 DOM·단방향·컴포넌트
2014     Vue — 점진적 채택 가능한 절충
         Flux — 단방향 데이터 흐름 패턴
2015     Redux — 단일 스토어·시간여행 디버깅
2016     Angular 2 — 전면 재작성·TypeScript
         Next.js / Nuxt — 메타프레임워크·SSR
2020-23  RSC — React 서버 컴포넌트
2021-24  Solid / Svelte / Angular — 시그널 세분 반응성
         Astro — 아일랜드·기본 JS 0
```

- 왼쪽 열이 연도, 오른쪽이 그 해의 항목이다. 연도가 빈 줄은 **바로 위 연도에 속한 두 번째 항목**이다(원문 타임라인의 표기 그대로다).
- 이 그림은 **연도와 항목만** 보여 준다. 항목끼리의 파생·인과 관계는 여기서 표시하지 않는다.

이 진화를 관통하는 두 개의 큰 축이 있다고 원문은 적는다.

1. **반응성을 어떻게 추적하나** — 수동 DOM 조작(jQuery) → 양방향 바인딩의 더티 체킹(AngularJS) → 가상 DOM 재조정(React) → 컴파일·시그널 기반 세분 추적(Svelte·Solid). "무엇이 바뀌었으니 화면의 어디를 다시 그릴까"를 점점 **정밀하게·자동으로** 좁혀온 역사다.
2. **JS를 어디서·얼마나 실행하나** — 전부 클라이언트(SPA) → 서버 렌더 후 전체 hydration → 서버 컴포넌트·아일랜드로 **상호작용이 실제 필요한 만큼만** 클라이언트로. 이 축은 corpus의 「렌더링 전략」 문서와 직접 맞닿는다.\
(corpus 경로: `~/project/local-llm/corpus/frontend/렌더링-전략.md`)

---

## 1. jQuery (2006) — DOM과 브라우저를 통일하다

*(여기 1절부터 7절까지가 이 편의 「무엇이 바뀌었나」다. 아래 세 소제목 「왜 등장했나 / 무엇을 풀었나 / 반작용」은 원문이 1~6절에서 소제목으로, 7절에서는 굵은 글씨로 반복해 쓴 것이다 — 그중 「반작용」이 이 편의 「대가는 무엇인가」에 해당한다.)*

### 왜 등장했나
2000년대 중반의 웹은 IE6·Firefox·Safari·Opera가 제각기 다른 DOM API와 이벤트 모델을 가진 전쟁터였다.\
`attachEvent`(IE) vs `addEventListener`(표준), `document.all` vs `getElementById`처럼 같은 일을 하는 코드를 브라우저마다 분기해야 했다.\
John Resig는 이 반복을 없애기 위해 jQuery를 만들어 **2006년 1월 14일 BarCamp NYC에서 공개**했다.\
슬로건은 "Write Less, Do More."

> **DOM(Document Object Model)** — 브라우저가 화면의 HTML을 프로그램이 다룰 수 있는 객체 트리로 만들어 둔 것.\
> 예: `document.getElementById('save')`로 버튼 하나를 집어 오는 그 트리가 DOM이다.

### 무엇을 풀었나
- **브라우저 호환성 추상화**: 같은 jQuery 코드가 모든 브라우저에서 동일하게 동작했다. 개발자는 더 이상 브라우저 분기를 직접 짜지 않았다.
- **CSS 셀렉터 기반 DOM 질의**: `$('.item')`로 요소를 모아 한 번에 조작하는 직관적 모델.
- **체이닝·간결한 Ajax**: `$.ajax`로 비동기 요청을, 메서드 체이닝으로 선언적 조작을 제공했다.

```javascript
// jQuery 이전: 브라우저 분기 + 명령형 DOM 조작
var btn = document.getElementById('save');
if (btn.addEventListener) btn.addEventListener('click', onSave);
else btn.attachEvent('onclick', onSave);          // IE 분기

// jQuery: 통일된 한 줄
$('#save').on('click', function () {
  $('.message').fadeIn().text('저장되었습니다');   // 셀렉터 + 체이닝
});
```

### 반작용
jQuery의 모델은 **DOM이 곧 상태**였다.\
화면에 표시된 값이 진실의 원천이고, 상호작용마다 개발자가 손으로 DOM을 갱신했다.\
앱이 커지면 "지금 이 `<span>`의 텍스트가 맞는 값인가?"를 추적하기가 불가능해졌다 — 상태가 DOM 곳곳에 흩어지고, 어떤 이벤트가 어디를 바꾸는지 한눈에 보이지 않는 **스파게티**가 됐다.\
데이터와 화면을 분리할 **구조**가 필요해졌다.

---

## 2. MVC/MVVM의 등장 — Backbone·Knockout (2010)

### 왜 등장했나
jQuery 코드의 무구조성에 대한 응답으로, 데스크톱·서버에서 검증된 **MVC(Model-View-Controller)** 와 **MVVM(Model-View-ViewModel)** 패턴을 브라우저로 들여왔다.

- **Backbone.js** (2010, Jeremy Ashkenas/DocumentCloud): Model·Collection·View·Router라는 최소 골격만 제공. 모델이 바뀌면 이벤트를 발행하고, 뷰가 그 이벤트를 구독해 다시 렌더하도록 **데이터와 DOM을 분리**했다.
- **Knockout.js** (2010, Steve Sanderson): MVVM과 **선언적 데이터 바인딩**을 도입. `observable`로 감싼 값이 바뀌면 바인딩된 DOM이 자동 갱신됐다.

### 무엇을 풀었나
"DOM이 곧 상태"에서 벗어나 **모델을 진실의 원천**으로 삼았다.\
상태는 한 곳(Model/ViewModel)에 모이고, 뷰는 그 상태의 투영이 됐다.\
이 "상태가 진실, 뷰는 그 함수"라는 발상이 이후 모든 프레임워크의 토대가 된다.

```text
진실의 원천이 옮겨간 자리 — 원문의 대비 그대로다

jQuery 시대                             Backbone / Knockout 이후
DOM이 곧 상태                           모델이 진실의 원천

  화면의 <span> 텍스트                  Model / ViewModel
  = 지금 값이 무엇인지의 근거           = 지금 값이 무엇인지의 근거
        ^                               |
        | 상호작용마다 손으로 갱신      | 뷰는 그 상태의 투영
        |                               v
     개발자                             화면
```

- 왼쪽이 1절의 「반작용」, 오른쪽이 이 절의 「무엇을 풀었나」다.
- 바뀐 것은 **"지금 값이 무엇인지"를 어디에 물어보느냐**다 — 화면에서 모델로 옮겨갔다.

> **진실의 원천(source of truth)** — "지금 값이 무엇인가"를 물어볼 단 하나의 자리.\
> 예: 화면의 글자를 읽어 확인하면 DOM이 진실의 원천, 모델 객체를 읽어 확인하면 모델이 진실의 원천이다.

### 반작용
Backbone은 너무 최소주의였다 — 뷰가 바뀔 때 DOM을 다시 그리는 일은 여전히 개발자 몫이라 보일러플레이트가 많았다.\
Knockout의 자동 바인딩은 편했지만 의존성 추적이 암묵적이라 디버깅이 어려웠다.\
"최소 골격(수동)"과 "마법 같은 바인딩(불투명)" 사이에서, **더 완결적인 풀스택 프레임워크**에 대한 갈증이 커졌다.

---

## 3. AngularJS (2010) — 양방향 바인딩의 시대

### 왜 등장했나
Google의 Miško Hevery가 만든 AngularJS는 **2010년 10월** 공개됐다(1.0은 2012년).\
일화에 따르면 그는 동료 팀이 6개월·1만 7천 줄로 만든 앱을, Angular의 원형으로 3주·1,500줄에 다시 만들어 보였다.\
핵심 무기는 **양방향 데이터 바인딩(two-way binding)** 이었다.

### 무엇을 풀었나
- **양방향 바인딩**: 모델 ↔ 뷰가 자동으로 동기화. 입력칸에 타이핑하면 모델이 바뀌고, 모델이 바뀌면 화면이 갱신된다 — 그 연결 코드를 개발자가 한 줄도 쓰지 않는다.
- **선언적 HTML(디렉티브)**: `ng-model`·`ng-repeat`·`ng-click`처럼 HTML 속성으로 동작을 선언. 커스텀 디렉티브로 자기만의 태그도 만들 수 있었다.
- **의존성 주입(DI)·테스트 용이성**: 서버 프레임워크(Spring 등)의 DI를 프론트로 가져와, 서비스를 주입·모킹해 단위 테스트가 가능해졌다.

```html
<!-- 양방향 바인딩: 입력과 화면이 코드 없이 동기화 -->
<div ng-app ng-init="name='세계'">
  <input ng-model="name">
  <h1>안녕, {{name}}!</h1>   <!-- 타이핑하면 즉시 반영 -->
</div>
```

> **양방향 데이터 바인딩(two-way binding)** — 모델과 뷰가 서로를 자동으로 따라가게 묶어 두는 것. 어느 쪽이 바뀌어도 반대쪽이 맞춰진다.\
> 예: 위 코드에서 `<input>`에 타이핑하면 `name`이 바뀌고, `name`이 바뀌면 `<h1>`이 갱신된다.

내부적으로는 **다이제스트 루프(digest loop)** 가 모든 바인딩된 값을 직전 값과 비교(dirty checking)해 바뀐 것을 찾아 DOM에 반영했다.

> **더티 체킹(dirty checking) / 다이제스트 루프(digest loop)** — 바인딩된 값을 하나씩 직전 값과 비교해 바뀐 것을 찾아내는 방식 / 그 비교를 도는 루프.\
> 예: 원문이 든 대로 바인딩(watcher)이 수천 개로 늘면, 그 수천 개를 전부 직전 값과 대 보는 식이다.

### 반작용
양방향 바인딩은 작은 앱에선 마법이지만 큰 앱에선 **데이터 흐름이 미궁**이 됐다.\
어떤 변경이 어떤 변경을 연쇄로 부르는지 추적 불가 — A를 바꾸면 B가 바뀌고 B가 다시 A를 바꾸는 식.\
더티 체킹은 바인딩(watcher)이 수천 개로 늘면 **성능 절벽**을 만들었다.\
"데이터가 어디로 흐르는지 예측할 수 없다"는 이 고통이, 곧 **단방향 흐름**이라는 반대 방향의 해법을 불렀다.\
(참고: corpus 「상태 관리」 — 단방향 흐름이 산 것은 "예측가능성")

---

## 4. React (2013) — 가상 DOM·단방향·컴포넌트

### 왜 등장했나
Facebook의 Jordan Walke가 만든 React는 **2013년 5월(JSConf US)** 오픈소스로 공개됐다(내부 사용은 2011년부터).\
광고 시스템처럼 상태가 복잡한 UI에서 양방향 바인딩의 예측 불가능성을 겪은 끝에 나온, 정반대 철학의 설계였다.

### 무엇을 풀었나
- **가상 DOM(Virtual DOM)**: 상태가 바뀌면 화면 전체를 "다시 그린다"고 선언하되, 실제로는 메모리상의 가상 트리를 만들어 직전과 **diff(재조정, reconciliation)** 한 뒤 바뀐 최소 부분만 실제 DOM에 반영. 개발자는 "어디를 갱신할까"가 아니라 "이 상태면 화면은 이렇다"만 기술한다.
- **단방향 데이터 흐름(one-way)**: 데이터는 부모 → 자식으로만 props로 흐른다. 자식은 콜백으로 위에 변경을 *요청*할 뿐 직접 위를 바꾸지 못한다. AngularJS의 양방향 미궁을 끊어, "상태가 왜·언제 바뀌나"를 한 방향으로 고정했다.
- **컴포넌트 + JSX**: UI를 재사용 가능한 컴포넌트의 합성으로 구성. 로직과 마크업을 한 곳에 두는 JSX는 처음엔 "관심사 분리 위반"이라 비판받았지만, **렌더는 상태의 순수 함수** `UI = f(state)`라는 모델을 정착시켰다.

```text
핵심 차이 — 원문이 대비한 축은 "데이터가 어느 방향으로 흐르나"이다

양방향 바인딩 (AngularJS)           단방향 흐름 (React)

  모델  <-------->  뷰              부모 상태 <--------+
    (어느 쪽이 바뀌어도               |  props         |
     반대쪽이 자동으로 맞춰진다)      v                |  콜백으로 "바꿔 달라"고 요청
                                    자식 컴포넌트 -----+

  A를 바꾸면 B가 바뀌고             props는 아래로만 내려간다
  B가 다시 A를 바꾼다               콜백은 위로 돌아가 부모에게 요청만 한다
  -> 연쇄를 추적할 수 없다          -> 데이터는 늘 부모에서 자식으로 흐른다
```

- 왼쪽 칸의 문구(모델 ↔ 뷰 자동 동기화, A→B→A 연쇄)는 3절 원문에서, 오른쪽 칸(부모→자식 props, 자식은 콜백으로 *요청*)은 이 절 원문에서 가져왔다.
- 오른쪽에서 props는 **아래로만** 흐르고, 콜백은 **위로 돌아가는 화살표**다 — 자식이 부모를 직접 바꾸지는 못하고, 원문의 표현 그대로 "요청할 뿐"이다.

> **가상 DOM(Virtual DOM) / 재조정(diff, reconciliation)** — 메모리 안에 만들어 두는 화면의 사본 트리 / 그 사본을 직전 것과 비교해 바뀐 최소 부분만 실제 DOM에 반영하는 일.\
> 예: 설계도를 두 장 놓고 달라진 곳만 표시한 뒤, 건물에서는 그 부분만 고치는 것.

> **단방향 데이터 흐름(one-way)** — 데이터가 부모에서 자식으로만 흐르고, 자식은 콜백으로 변경을 요청만 하는 규칙.\
> 예: 위 도식의 오른쪽 칸 — 자식은 콜백으로 "바꿔 달라"고 요청할 뿐, 부모의 상태를 직접 바꾸지 못한다.

> **`UI = f(state)`** — 화면은 상태를 넣으면 나오는 함수의 결과라는 모델.\
> 예: 같은 `count`면 언제 그려도 같은 화면이 나온다.

```jsx
// 상태의 함수로서의 UI. 단방향: state → 화면, 이벤트 → setState
function Counter() {
  const [count, setCount] = useState(0);          // 상태는 컴포넌트가 소유
  return (
    <button onClick={() => setCount(count + 1)}>   {/* 변경은 명시적 호출로만 */}
      클릭 수: {count}
    </button>
  );
}
```

- 이 코드에는 부모·자식이 없다 — 상태를 소유한 `Counter`가 자기 상태를 직접 바꾼다. 위 도식의 부모/자식 관계는 이 코드가 아니라 원문의 「단방향 데이터 흐름」 설명에서 온 것이다.

원문의 mermaid 순환 그림을 글자 도식으로 옮기면 이렇다(노드 문구·화살표 라벨·방향은 그대로다).

```text
state (단일 진실)
      |
      |  f(state)
      v
가상 DOM 트리
      |
      |  diff (재조정)
      v
바뀐 최소 부분만
      |
      v
실제 DOM
      |
      |  이벤트
      v
setState / dispatch
      |
      |  새 state
      +----> 맨 위 state (단일 진실)로 돌아간다
```

- 다섯 칸의 이름과 네 개의 화살표 라벨(`f(state)`·`diff (재조정)`·`이벤트`·`새 state`)은 원문 그림 그대로다.
- 맨 아래에서 맨 위로 돌아가는 화살표가 있어 **닫힌 고리**다 — 원문 그림도 `handler → state`로 닫혀 있다.

### 반작용
React는 의도적으로 **뷰 라이브러리**일 뿐이었다(라우팅·상태관리·빌드는 미포함).\
자유의 대가는 **결정 피로**와 생태계 파편화 — 라우터·상태관리·스타일링을 매번 골라 조립해야 했다.\
특히 컴포넌트를 가로지르는 **전역 상태**를 어떻게 단방향으로 다룰지가 다음 숙제가 됐다.\
또한 가상 DOM의 diff 자체가 공짜가 아니어서, 훗날 "diff 없이 컴파일 타임에 정확히 추적하자"는 시그널 진영의 반작용을 낳는다.

원문이 이 절 끝에 나란히 붙인 상자는 이것이다.

> **경쟁 절충안 — Vue (2014)**: 전 Google 엔지니어 Evan You가 **2014년 2월** 공개. AngularJS의 선언적 템플릿·디렉티브의 친숙함과 React의 가상 DOM·컴포넌트를 결합하고, `<script src>` 한 줄로 기존 페이지에 **점진적으로** 얹을 수 있게 했다. 반응성은 (당시) 속성 접근을 가로채 의존성을 자동 추적하는 방식으로, "Angular의 편함 + React의 구조"라는 절충 포지션을 차지했다.

---

## 5. 상태 관리 — Flux(2014)·Redux(2015)

### 왜 등장했나
React가 뷰는 단방향으로 정리했지만, **여러 컴포넌트가 공유하는 전역 상태**는 여전히 흩어졌다.\
Facebook은 채팅 알림 카운트가 계속 어긋나는 버그를 겪으며, MVC의 양방향 연쇄가 원인이라 진단했다.\
그 응답이 **Flux**(2014, F8 컨퍼런스) — 라이브러리가 아니라 **단방향 데이터 흐름 아키텍처 패턴**이었다: `Action → Dispatcher → Store → View → (Action)`.

이 패턴을 가장 단순하고 강력하게 구현한 것이 Dan Abramov의 **Redux**(2015) — 원래는 컨퍼런스 발표용 **시간여행 디버깅(time-travel debugging)** 데모로 만들어졌다.

### 무엇을 풀었나
- **단일 스토어 + 불변 업데이트**: 앱 상태 전체를 하나의 객체 트리로. 변경은 오직 **순수 함수 reducer** `(state, action) => newState`를 통해서만, 그것도 새 객체를 반환하는 불변 방식으로.
- **예측가능성·디버깅**: 모든 변경이 명시적 action으로 기록되니, 상태 변화를 재생·되감기할 수 있다(시간여행). "지금 상태가 왜 이런가"를 action 로그로 역추적 가능.

```javascript
// 순수 함수 reducer: 같은 입력이면 항상 같은 출력, 부수효과 없음
function counter(state = { count: 0 }, action) {
  switch (action.type) {
    case 'INCREMENT': return { count: state.count + 1 };  // 새 객체 반환(불변)
    default:          return state;
  }
}
// 변경은 dispatch를 통해서만 — 단방향
store.dispatch({ type: 'INCREMENT' });
```

> **reducer(리듀서)** — `(state, action) => newState` 꼴의 순수 함수. 같은 입력이면 항상 같은 출력이고 부수효과가 없다.\
> 예: 위 코드의 `counter`가 그것이다 — `'INCREMENT'`를 받으면 새 객체 `{ count: state.count + 1 }`을 돌려준다.

> **불변 업데이트(immutable update)** — 기존 객체를 고치지 않고 새 객체를 만들어 돌려주는 방식.\
> 예: 위 코드가 `state.count++`가 아니라 `{ count: state.count + 1 }`을 반환하는 것.

> **시간여행 디버깅(time-travel debugging)** — 기록된 action을 따라 상태 변화를 재생하거나 되감아 보는 것.\
> 예: "이 값이 왜 이렇게 됐나"를 action 로그를 거슬러 올라가 찾는다.

### 반작용
Redux는 예측가능성을 샀지만 **보일러플레이트**라는 비싼 값을 치렀다 — action 타입·action 생성자·reducer를 매번 손으로 엮는 의식.\
또한 "모든 것을 전역 스토어에" 넣는 오용이 퍼지며, **서버에서 온 데이터(캐시)** 까지 스토어에 손수 복사·동기화하는 안티패턴이 만연했다.\
이 두 반작용이 각각 ① 보일러플레이트를 줄인 **Redux Toolkit·Zustand·Jotai**, ② 서버상태를 캐시로 분리해 소유하는 **React Query·SWR**를 불렀다.\
(corpus 「상태 관리」: "서버 캐시 ≠ UI 상태 — 둘을 합치는 게 실수")

원문이 이 절 끝에 나란히 붙인 상자는 이것이다.

> **Angular 2 (2016)**: AngularJS의 더티 체킹 성능 한계와 미궁 같은 양방향 흐름을 버리고 **전면 재작성**한 별개 프레임워크(2016년 9월). TypeScript 일급 채택·컴포넌트 기반·RxJS 반응형·모듈/DI 체계를 갖춘 풀스택 프레임워크로 노선을 바꿨다. AngularJS와 호환되지 않는 단절적 전환이라 마이그레이션 고통을 남겼지만, 대규모 엔터프라이즈 앱의 구조화된 선택지로 자리 잡았다.

---

## 6. SSR·메타프레임워크 — Next.js·Nuxt (2016)

### 왜 등장했나
React·Vue로 만든 **SPA(클라이언트 렌더)** 가 보편화되자 그 약점이 드러났다 — 첫 응답이 빈 HTML이라 **SEO에 불리**하고, 거대한 JS를 받아 실행해야 첫 화면이 떠 **초기 로딩이 느렸다**.\
또한 라우팅·번들링·SSR 설정을 매 프로젝트마다 조립하는 피로가 컸다.\
그 응답이 **메타프레임워크**다 — 뷰 라이브러리 위에 라우팅·데이터 로딩·SSR/SSG·번들링을 묶어 **합의된 구조(convention)** 로 제공.

- **Next.js** (Zeit/Vercel, 2016년 10월): React용. 파일 시스템 기반 라우팅, 페이지별 SSR·SSG 선택.
- **Nuxt** (Chopin 형제, 2016년 10월): Vue용. Next.js의 발상을 Vue 생태계로.

> **SPA(Single Page Application) / 클라이언트 렌더** — 서버가 빈 HTML을 주고 브라우저의 JS가 화면을 만드는 방식.\
> 예: 원문의 표현대로 첫 응답이 빈 HTML이라 SEO에 불리하다.

> **SSR / SSG / ISR** — 요청마다 서버가 HTML을 만드는 것 / 빌드 타임에 미리 만들어 두는 것 / 증분 재생성.\
> 예: 요청마다 새로 만들어야 하는 페이지는 SSR로, 빌드 타임에 미리 만들어 둬도 되는 페이지는 SSG로 — 원문의 표현으로 "페이지 성격에 따라" 고른다.

### 무엇을 풀었나
- **렌더링 전략의 선택지**: 페이지 성격에 따라 SSR(요청마다)·SSG(빌드 타임)·ISR(증분 재생성)을 고를 수 있게 — corpus 「렌더링 전략」의 다섯 전략이 여기서 제품화됐다.
- **SEO·초기 로딩 회복**: 서버/빌드에서 HTML을 미리 만들어 첫 화면(FCP)과 크롤러 친화성을 되찾고, 그 위에 클라이언트가 **hydration**으로 상호작용을 입혔다.

> **hydration(하이드레이션)** — 서버가 보낸 HTML 위에 클라이언트가 같은 컴포넌트 트리를 다시 그려 이벤트를 붙이는 일.\
> 예: 이미 인쇄된 종이 위에 버튼이 눌리도록 배선을 다시 까는 것 — 그 배선이 끝나야 눌린다.

### 반작용
SSR + **전체 hydration**은 "서버가 HTML을 줬는데, 똑같은 컴포넌트 트리를 클라이언트가 다시 그려 이벤트를 붙이는" 중복 비용을 만들었다 — 화면은 **보이지만 안 눌리는** 구간(FCP는 빠른데 TTI는 느린 *uncanny valley*).\
페이지가 클수록 hydration용 JS가 비대해졌다.\
"HTML은 서버가, 그런데 hydration은 *필요한 만큼만*"이라는 다음 과제가 여기서 출발한다.

```text
전체 hydration이 만드는 중복 — 원문의 서술 그대로다

서버                                  브라우저
  HTML을 만들어 보낸다 -------------> 화면이 보인다 (FCP는 빠르다)
                                      |
                                      |  같은 컴포넌트 트리를 다시 그려
                                      |  이벤트를 붙인다 = hydration
                                      v
                                      이제 눌린다 (TTI)

  그 사이 구간: 보이지만 안 눌린다 (uncanny valley)
  페이지가 클수록 hydration용 JS가 비대해진다
```

- 위 두 줄이 원문의 "중복 비용"이다 — 서버가 만든 것과 **똑같은** 트리를 클라이언트가 다시 그린다.
- 가운데 구간이 원문이 적은 "보이지만 안 눌리는" 자리다.

---

## 7. 최근 — 시그널·서버 컴포넌트·아일랜드 (2021~)

세 갈래의 반작용이 동시에 진행 중이다.\
공통 목표는 **불필요한 일을 컴파일·아키텍처 차원에서 제거**하는 것이다.

### 7-1. 시그널 — 세분 반응성 (Solid·Svelte·Angular)
**왜**: 가상 DOM의 diff와 컴포넌트 단위 리렌더는, "정말 바뀐 한 값" 때문에 그 값을 쓰는 컴포넌트 전체를 다시 실행한다.\
**무엇을 풀었나**: **시그널(signal)** 은 값과 그 값을 읽는 곳들의 의존 그래프를 정밀하게 추적해, 바뀐 값이 닿는 **바로 그 DOM 노드만** 갱신한다(가상 DOM diff 없이).

```text
갱신 범위 — 원문이 대비한 축은 "무엇을 다시 실행하나"이다

가상 DOM, 컴포넌트 단위 리렌더                시그널, 세분 반응성

  한 값이 바뀐다                              한 값이 바뀐다
        |                                     |
        v                                     v
  그 값을 쓰는 컴포넌트 전체를 다시 실행      그 값을 읽는 곳만 정확히 재실행
        |                                     |
        v                                     v
  가상 DOM을 만들어 직전과 diff               바뀐 값이 닿는 바로 그 DOM 노드만 갱신
        |                                     (가상 DOM diff 없이)
        v
  바뀐 최소 부분만 실제 DOM에 반영
```

- 두 칸 모두 원문 문장에서 가져왔다 — 왼쪽은 4절과 이 절의 「왜」, 오른쪽은 이 절의 「무엇을 풀었나」다.
- 두 칸 모두 마지막에는 실제 DOM을 최소로만 고친다 — 원문이 각각 "바뀐 최소 부분만 실제 DOM에 반영"(4절)과 "바로 그 DOM 노드만 갱신"(이 절)이라 적었다.\
  차이는 그 앞에서 무엇을 다시 실행하느냐다.

- **Solid** (Ryan Carniato, 1.0 — 2021): React를 닮은 JSX·컴포넌트 문법이지만, 컴포넌트는 **한 번만 실행**되고 이후는 시그널이 직접 DOM을 갱신.
- **Svelte** (Rich Harris): **컴파일러**가 빌드 타임에 반응성 코드를 생성 — 런타임 프레임워크를 거의 들고 다니지 않는다. Svelte 5(2024년 10월)의 **runes**(`$state`·`$derived`·`$effect`)로 시그널 모델을 명시화했다.
- **Angular signals** (Angular 16, 2023): 옛 Zone.js 기반 변경 감지를 시그널로 대체하는 길을 열어, 세분 반응성·옵셔널 zoneless로 이동 중.

```javascript
// 시그널: 값을 읽는 곳을 추적해 "그곳만" 갱신 (Solid 예시)
const [count, setCount] = createSignal(0);
createEffect(() => console.log('현재:', count()));  // count를 읽음 → 의존 등록
setCount(1);   // count를 읽는 effect/DOM만 정확히 재실행 (컴포넌트 전체 X)
```

> **시그널(signal) / 세분 반응성(fine-grained reactivity)** — 값과 그 값을 읽는 곳들의 의존 그래프를 추적하는 장치 / 그 덕에 컴포넌트 전체가 아니라 닿는 자리만 갱신하는 방식.\
> 예: 위 코드에서 `setCount(1)`은 `count()`를 읽은 effect와 DOM만 다시 돌린다.

**반작용**: 모델이 여럿(가상 DOM vs 시그널)으로 갈리며 멘탈 모델 파편화가 생겼고, React 진영은 이에 대해 **React Compiler**(자동 메모이제이션)로 "수동 최적화 없이 리렌더 줄이기"로 응수하는 중이다.

### 7-2. React Server Components (RSC, 2020 발표 → 2023~ 안정화)
**왜**: hydration 세금을 근본부터 줄이려면, 애초에 **클라이언트로 JS를 안 보내는** 컴포넌트가 있어야 한다.\
**무엇을 풀었나**: 서버 컴포넌트는 **서버에서만 렌더**되고 클라이언트 번들을 만들지 않으며 **hydrate할 것이 없다(비용 0)**.\
상호작용이 필요한 부분만 `"use client"` 경계 안으로 격리한다.\
Next.js의 App Router(2023)가 이를 제품화했다.

> **서버 컴포넌트 / `"use client"` 경계** — 서버에서만 렌더되고 클라이언트 번들을 만들지 않는 컴포넌트 / 상호작용이 필요한 부분을 따로 격리하는 표시.\
> 예: 상품 설명 문단은 서버 컴포넌트로 두고, 장바구니 버튼만 `"use client"` 안쪽에 둔다.

**반작용**: 서버/클라이언트 경계라는 새 멘탈 모델이 진입 장벽을 높였고, "어디가 서버고 어디가 클라이언트인가"의 혼란·러닝커브 논쟁을 낳았다.

### 7-3. 아일랜드 아키텍처 (Astro, 2021~)
**왜**: 블로그·문서·커머스처럼 **대부분 정적**인데 상호작용은 위젯 몇 개뿐인 콘텐츠 사이트에, SPA의 거대 JS는 과잉이다.\
**무엇을 풀었나**: Astro는 **기본 JS 0** — 정적 HTML을 내고, 상호작용이 필요한 영역만 독립 "**섬(island)**"으로 hydrate한다.\
각 섬은 `client:load`·`client:idle`·`client:visible` 디렉티브로 로딩 시점을 **위젯 단위**로 제어한다.\
React·Vue·Svelte 컴포넌트를 섬 안에 섞어 쓸 수도 있다.

> **아일랜드(island)** — 정적 HTML 바다 위에서 상호작용이 필요한 영역만 따로 hydrate하는 단위.\
> 예: 문서 페이지 전체는 정적이고, 검색창 위젯 하나만 섬으로 살아난다.

**공통 귀결**: 세 갈래 모두 "**JS를 상호작용이 실제 필요한 만큼만**"이라는 한 방향을 향한다.\
corpus 「렌더링 전략」의 결론 — "기본은 정적·서버 렌더, 클라이언트 JS는 필요한 만큼만" — 이 현재의 합의다.

---

## 진화의 논리 — 무엇이 매번 반복되나

*(이 편의 「왜 그렇게 갔나 — 남은 선택지와 트레이드오프」에 해당한다)*

원문의 mermaid 순환 그림을 글자 도식으로 옮기면 이렇다(노드 문구와 방향은 그대로다).

```text
직전 시대의 고통
      |
      v
새 추상화로 해결
      |
      v
해법이 만든 새 비용(반작용)
      |
      +----> 다시 "직전 시대의 고통"으로
```

- 세 칸의 이름은 원문 그림 그대로이고, 맨 아래에서 맨 위로 돌아가는 화살표도 원문 그림에 있다(`tax --> pain`).
- 이 편의 절마다 반복된 세 소제목(왜 등장했나 / 무엇을 풀었나 / 반작용)이 정확히 이 세 칸이다.

원문의 정리 표를 그대로 옮긴다.

| 시대 | 고통 | 해법 | 남긴 반작용 |
|------|------|------|------------|
| jQuery | 브라우저 분기·DOM 스파게티 | 호환성 추상화·셀렉터 | DOM이 곧 상태 → 추적 불가 |
| MVC/MVVM·AngularJS | 무구조·DOM=상태 | 모델 분리·양방향 바인딩 | 양방향 데이터 미궁·더티체킹 성능 |
| React | 양방향 예측 불가 | 가상 DOM·단방향·컴포넌트 | 전역 상태 숙제·생태계 파편화 |
| Flux/Redux | 흩어진 전역 상태 | 단일 스토어·단방향·시간여행 | 보일러플레이트·서버상태 오용 |
| Next.js/Nuxt | SPA의 SEO·초기 로딩 | SSR/SSG·합의된 구조 | 전체 hydration 세금 |
| 시그널·RSC·아일랜드 | hydration 비용·과한 리렌더 | 세분 반응성·서버 컴포넌트·섬 | 멘탈 모델 파편화·경계 러닝커브 |

- 표를 읽는 법: 한 행의 **「남긴 반작용」이 아래 행의 「고통」으로 이어지는 자리**가 네 군데 있다.\
  1행의 "DOM이 곧 상태"가 2행의 "DOM=상태"로, 2행의 "양방향 데이터 미궁"이 3행의 "양방향 예측 불가"로, 3행의 "전역 상태 숙제"가 4행의 "흩어진 전역 상태"로, 5행의 "전체 hydration 세금"이 6행의 "hydration 비용"으로 이어진다.
- **4행과 5행 사이는 그렇지 않다.**\
  4행의 반작용(보일러플레이트·서버상태 오용)은 원문 본문에서 Redux Toolkit·Zustand·Jotai와 React Query·SWR로 이어지고, 5행의 고통(SPA의 SEO·초기 로딩)은 그와 다른 줄기다.\
  원문은 이 진화를 "왜 등장했나 / 무엇을 풀었나 / 어떤 반작용을 남겼나"의 **사슬**로 읽는다 — 다만 이 표에서는 4행→5행만 그 고리가 표 위에 드러나지 않는다.

원문이 이 절을 맺는 문장은 이것이다.

> 핵심 통찰: **모든 프레임워크는 "상태가 진실이고 화면은 그 함수"라는 한 점으로 수렴**해 왔다(`UI = f(state)`). 차이는 ① 그 함수를 *언제·어디서* 실행하나(클라/서버/빌드)와 ② 상태 변화를 *얼마나 정밀하게* 추적하나(diff vs 시그널)일 뿐이다. 새 도구를 만날 때 이 두 질문으로 위치를 잡으면, 유행이 아니라 **트레이드오프**로 읽을 수 있다.

---

## corpus 연결 (더 깊이 보기)

*(원문에는 별도의 「영향과 의의」 절이 없다. 이 편의 결론은 바로 위 「진화의 논리」의 마지막 문장이고, 이 절은 원문이 "지금 무엇을 고르나"로 잇는 대목이다. corpus 문서는 링크가 아니라 이름으로 적고, 실체 경로(`~/project/local-llm/corpus/…`)를 함께 적었다.)*

이 문서가 "역사(왜 이렇게 됐나)"라면, corpus/frontend는 "설계(지금 무엇을 고르나)"다.\
진화의 각 분기점은 corpus의 트레이드오프 문서로 이어진다.

- 단방향 흐름·서버상태 분리·전역 스토어 선택 → corpus 「상태 관리」 (corpus 경로: `~/project/local-llm/corpus/frontend/상태-관리.md`)
- SSR/SSG/ISR/스트리밍·RSC·아일랜드의 선택 기준 → corpus 「렌더링 전략」 (corpus 경로: `~/project/local-llm/corpus/frontend/렌더링-전략.md`)
- 컴포넌트 합성·컨테이너/프레젠테이셔널 → corpus 「컴포넌트 아키텍처」 (corpus 경로: `~/project/local-llm/corpus/frontend/컴포넌트-아키텍처.md`)
- 서버 캐시·무효화·낙관적 업데이트(React Query/SWR) → corpus 「데이터 페칭·캐싱」 (corpus 경로: `~/project/local-llm/corpus/frontend/데이터-페칭-캐싱.md`)
- hydration 세금·번들·코드스플리팅·CWV → corpus 「성능·최적화」 (corpus 경로: `~/project/local-llm/corpus/frontend/성능-최적화.md`)
- 전체 인덱스 → corpus/frontend INDEX (corpus 경로: `~/project/local-llm/corpus/frontend/INDEX.md`)

## 용어 풀이

- **DOM(Document Object Model)** — 화면의 HTML을 프로그램이 다룰 수 있게 만든 객체 트리.
- **상태(state) / 진실의 원천(source of truth)** — 화면에 보여야 할 값들 / "지금 값이 무엇인가"를 물어볼 단 하나의 자리.
- **반응성(reactivity)** — 상태가 바뀌었을 때 화면의 어디를 다시 그릴지 찾아내는 장치.
- **MVC / MVVM** — Model-View-Controller / Model-View-ViewModel. 2010년 Backbone·Knockout이 브라우저로 들여왔다.
- **양방향 데이터 바인딩(two-way binding)** — 모델과 뷰가 서로를 자동으로 따라가게 묶는 것(AngularJS).
- **더티 체킹(dirty checking) / 다이제스트 루프(digest loop)** — 바인딩된 값을 직전 값과 하나씩 비교해 변경을 찾는 방식 / 그 루프.
- **디렉티브(directive) / 의존성 주입(DI)** — `ng-model`처럼 HTML 속성으로 동작을 선언하는 것 / 서비스를 주입·모킹해 단위 테스트를 가능하게 한 체계.
- **가상 DOM(Virtual DOM) / 재조정(diff, reconciliation)** — 메모리 안의 화면 사본 트리 / 직전 사본과 비교해 바뀐 최소 부분만 실제 DOM에 반영하는 일.
- **단방향 데이터 흐름(one-way)** — 데이터는 부모→자식 props로만 흐르고, 자식은 콜백으로 변경을 요청만 하는 규칙.
- **컴포넌트 / JSX** — 재사용 가능한 UI 조각 / 로직과 마크업을 한 곳에 두는 문법.
- **`UI = f(state)`** — 화면은 상태를 넣으면 나오는 함수의 결과라는 모델. 원문이 "모든 프레임워크가 수렴한 한 점"이라 부르는 것.
- **Flux** — `Action → Dispatcher → Store → View → (Action)`의 단방향 데이터 흐름 아키텍처 패턴(2014).
- **reducer / 불변 업데이트** — `(state, action) => newState` 꼴의 순수 함수 / 기존 객체를 고치지 않고 새 객체를 반환하는 방식.
- **시간여행 디버깅(time-travel debugging)** — 기록된 action을 따라 상태 변화를 재생·되감는 것.
- **보일러플레이트(boilerplate)** — 매번 손으로 똑같이 엮어야 하는 반복 코드. Redux의 대가로 원문이 든 것.
- **SPA(Single Page Application) / 클라이언트 렌더** — 서버가 빈 HTML을 주고 브라우저 JS가 화면을 만드는 방식.
- **메타프레임워크** — 뷰 라이브러리 위에 라우팅·데이터 로딩·SSR/SSG·번들링을 묶어 합의된 구조로 주는 것(Next.js·Nuxt).
- **SSR / SSG / ISR** — 요청마다 서버가 HTML 생성 / 빌드 타임에 미리 생성 / 증분 재생성.
- **hydration** — 서버가 보낸 HTML 위에 클라이언트가 같은 트리를 다시 그려 이벤트를 붙이는 일. FCP와 TTI 사이의 "보이지만 안 눌리는" 구간을 만든다.
- **시그널(signal) / 세분 반응성** — 값과 그 값을 읽는 곳의 의존 그래프를 추적하는 장치 / 닿는 자리만 갱신하는 방식(Solid·Svelte runes·Angular signals).
- **서버 컴포넌트(RSC) / `"use client"`** — 서버에서만 렌더되고 클라이언트 번들을 만들지 않는 컴포넌트 / 상호작용 부분을 격리하는 경계 표시.
- **아일랜드(island)** — 정적 HTML 위에서 상호작용이 필요한 영역만 따로 hydrate하는 단위(Astro).

## 참고 출처
- [John Resig — Annotated Version of the Original jQuery Release](https://johnresig.com/blog/annotated-version-of-the-original-jquery-release/) · [10th Anniversary of jQuery](https://johnresig.com/blog/10th-anniversary-of-jquery/)
- [John Resig — Wikipedia](https://en.wikipedia.org/wiki/John_Resig)
- [What is AngularJS? Complete Guide — History & Facts](https://www.articsledge.com/post/angularjs)
- [Virtual DOM — Wikipedia](https://en.wikipedia.org/wiki/Virtual_DOM)
- [Angular vs React vs Vue: Core Differences — BrowserStack](https://www.browserstack.com/guide/angular-vs-react-vs-vue)
- [The History of Redux — Redux Docs](https://redux.js.org/understanding/history-and-design/history-of-redux) · [Redux — Three Principles](https://redux.js.org/understanding/thinking-in-redux/three-principles)
- [The Rise of Flux — Wix Engineering (Medium)](https://medium.com/wix-engineering/the-rise-of-flux-how-facebooks-shift-away-from-mvc-led-to-a-new-era-of-ui-architecture-61d78b4377b0)
- [Redux (software) — Wikipedia](https://en.wikipedia.org/wiki/Redux_(software))
- [What is Nuxt: Review and Features — Bejamas](https://bejamas.com/hub/web-frameworks/nuxtjs)
- [JavaScript Frameworks — Heading into 2024 (Playful Programming)](https://playfulprogramming.com/posts/javascript-frameworks-heading-into-2024-i3l/)
- [web.dev — Rendering on the Web (Miller·Osmani)](https://web.dev/articles/rendering-on-the-web)
- [Astro — Islands Architecture](https://docs.astro.build/en/concepts/islands/)
- [SolidJS — Resources](https://www.solidjs.com/resources) · [Next-Gen Reactivity: SolidJS Signals vs Svelte 5 Runes — Leapcell](https://leapcell.io/blog/next-gen-reactivity-rethink-preact-solidjs-signals-vs-svelte-5-runes)
