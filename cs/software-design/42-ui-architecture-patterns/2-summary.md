# software-design/42-ui-architecture-patterns — MVC 계보: Smalltalk MVC에서 단방향 흐름까지 — 정리 (힌트)

## 해결하는 문제

화면 코드는 세 가지를 동시에 한다.

```text
 ① 그리기       (버튼·표·색)
 ② 입력 받기     (클릭·타이핑)
 ③ 규칙·상태     (합계 계산, 할인 판단, 주문 상태)
```

이 셋이 한 클래스(폼·컨트롤러)에 섞이면 두 가지가 안 된다.

- 같은 규칙을 다른 화면·API에서 다시 쓸 수 없다. 화면마다 복사되고 조금씩 달라진다.
- 규칙을 화면 없이 테스트할 수 없다.

UI 아키텍처 패턴은 이 셋을 어떻게 나누고, 나눈 조각끼리 **값을 어떻게 동기화하나**에 대한 답의 계보다.

쉬운 예: 식당에서 주문 받기(입력)·조리(규칙)·플레이팅(그리기)을 한 사람이 다 하면 메뉴를 바꿀 때마다 그 사람만 바쁘다.\
똑같은 구조다: 역할을 나누고, 주문서(상태)가 어떻게 흐를지 정한다.\
실무 예: 장바구니 화면의 할인 규칙이 컨트롤러 메서드 안에 있으면, 모바일 API는 그 규칙을 다시 짠다. 두 규칙이 어긋나 "앱과 웹의 결제 금액이 다르다"는 문의가 온다.

## 동작·원리

### 1. 계보 한 장

```text
 1978-79  Smalltalk MVC (Reenskaug, Xerox PARC)       ── 모델/뷰/컨트롤러, 옵서버 동기화
   │
 1990s    Forms and Controls (VB·Delphi류)            ── 폼이 위젯 이벤트를 받아 직접 처리
   │      MVP (IBM·Taligent, Potel 논문; Dolphin Smalltalk) ── 위젯이 입력을 받아 프레젠터에 넘긴다
   │         ├ Supervising Controller (선언형 바인딩 + 프레젠터는 복잡한 경우만)
   │         └ Passive View (프레젠터가 위젯을 전부 조작, 뷰는 껍데기)
   │      Presentation Model / Application Model (VisualWorks) ── 화면 상태를 담은 모델
 2002     서버 MVC (PoEAA): Front Controller · Page Controller · Template View
 2005     MVVM (Gossman, WPF) ── Presentation Model + 데이터 바인딩(양방향 포함)
 2014~    단방향: Flux (Facebook), Elm Architecture (Model · View · Update)
```

- 연대·출처: Smalltalk MVC는 Reenskaug의 자료 페이지(1978–79 Xerox PARC), Forms and Controls·MVP·Presentation Model은 Fowler "GUI Architectures"(2006-07-18), 서버 패턴은 Fowler PoEAA 카탈로그, MVVM은 John Gossman 블로그(2005년 10월), Flux는 Flux 문서와 React 블로그 "Flux: An Application Architecture for React"(2014-05-06). Elm Architecture의 시작 연도는 이 노트에서 확인하지 않았다("2014~"는 Flux 기준).
- Fowler는 "MVC라고 불리는 것 중 원래 MVC와 전혀 다른 것을 많이 봤다"고 적는다. 이름보다 **무엇이 무엇을 아는가, 값이 어떻게 동기화되나**를 본다.

### 2. 공통 뼈대: 표현 분리

```text
            ┌────────── 프레젠테이션 ──────────┐
 사용자 ──> │ 뷰(그리기) ⇄ 컨트롤러/프레젠터(입력)│ ──> 도메인 모델(규칙·상태)
            └──────────────────────────────────┘        프레젠테이션을 모른다
```

- *표현 분리(Separated Presentation)*: 도메인 코드는 화면을 모르게 둔다. Fowler가 MVC에서 "가장 영향력 있는" 생각으로 꼽는다.
- *옵서버 동기화(Observer Synchronization)*: 모델이 바뀌면 이벤트를 내고, 그것을 구독하는 뷰들이 스스로 다시 그린다.
- *흐름 동기화(Flow Synchronization)*: 바꾼 쪽 코드가 갱신할 화면을 직접 불러 준다.

### 3. 패턴별로 "누가 입력을 받고 누가 그리나"

```text
 Smalltalk MVC   입력 → 컨트롤러 → 모델 변경 → (이벤트) → 뷰가 모델을 읽어 다시 그림
 MVP             입력 → 위젯 → 프레젠터 → 모델 변경 / 뷰 조작   (뷰와 컨트롤러 구분을 없앰)
 MVVM            뷰 ⇄(바인딩)⇄ 뷰모델(화면 상태·명령) → 모델
 서버 MVC        HTTP 요청 → Front Controller(모든 요청의 입구) → 핸들러 → 모델 → Template View(HTML 렌더)
 Flux            뷰 → 액션 → 디스패처(하나) → 스토어들 → 뷰   (한 방향)
 Elm             메시지 → update(model, msg) → 새 model → view(model)
```

- *Front Controller*: "웹 사이트의 모든 요청을 처리하는 컨트롤러"(PoEAA). Spring MVC 문서는 Spring MVC가 front controller 패턴을 따르고 중앙 서블릿 `DispatcherServlet`이 요청 처리를 맡는다고 적는다.
- *Page Controller*: "특정 페이지·액션의 요청을 처리하는 객체"(PoEAA).
- *Template View*: "HTML에 표식을 끼워 정보를 렌더한다"(PoEAA). JSP·Thymeleaf 같은 템플릿이다.
- *뷰모델(ViewModel)*: Gossman의 정의로 "뷰의 모델". 모델 타입을 뷰 타입으로 바꾸는 변환과 뷰가 쓸 명령(Command)을 가진다.
- *디스패처(Dispatcher)*: Flux에서 모든 액션이 지나는 단일 허브. 스토어들이 여기에 콜백을 등록한다.

### 4. 옵서버·양방향 바인딩의 비용

Fowler(2006)는 옵서버 동기화의 단점을 이렇게 적는다: 코드를 읽어서는 무슨 일이 일어나는지 알 수 없고, Smalltalk-80 화면을 이해하려다 결국 디버거와 trace 문으로만 볼 수 있었다. "옵서버 동작은 암묵적이라 이해·디버깅이 어렵다."\
Flux 문서는 같은 문제를 더 크게 본다: 양방향 데이터 바인딩이 **연쇄 갱신(cascading updates)**을 낳아, 앱이 커지면 사용자 행동 하나의 결과를 예측하기 어려웠다고 적는다.

### 실험: 양방향 바인딩 연쇄 vs 단방향 디스패처

규칙 두 개를 서로 다른 사람이 바인딩으로 추가했다고 하자.

```text
 화면 A의 바인딩:  subtotal, discount 가 바뀌면 → total = subtotal - discount
 화면 B의 바인딩:  total 이 바뀌면 → discount = (total >= 10000 ? subtotal의 10% : 0)

        subtotal ──> total ──> discount
                       ^          │
                       └──────────┘   ← 규칙끼리 고리를 이룬다(B가 A의 결과를 다시 입력으로 씀)
```

```js
class Observable {
  set(v, by) {
    if (v === this.v) return;                          // 같은 값이면 멈추는 흔한 가드
    log.push(`${this.name}: ${this.v} → ${v}  (by ${by})`);
    this.v = v; this.subs.forEach(f => f(v));
  }
}
subtotal.on(v => total.set(v - discount.get(), 'subtotal 바인딩'));
discount.on(v => total.set(subtotal.get() - v, 'discount 바인딩'));
total.on(v => discount.set(v >= 10000 ? Math.round(subtotal.get() * 0.1) : 0, 'total 바인딩'));
```

(실험, node v22.23.2 `node:22-alpine`, `scratchpad/sd/40/e42/twoway.js`, 2026-10-02 — 3회 실행 모두 같은 출력)

```text
입력 8000: 갱신 2회, 최종 subtotal=8000 discount=0 total=8000
입력 12000: 갱신 4회, 최종 subtotal=12000 discount=1200 total=10800
입력 10500: RangeError: Maximum call stack size exceeded — 그 전까지 갱신 2058회
  처음 6줄:
   subtotal: 12000 → 10500  (by 사용자 입력)
   total: 10800 → 9300  (by subtotal 바인딩)
   discount: 1200 → 0  (by total 바인딩)
   total: 9300 → 10500  (by discount 바인딩)
   discount: 0 → 1050  (by total 바인딩)
   total: 10500 → 9450  (by discount 바인딩)
```

- 관찰 1 — 8,000원·12,000원에서는 멀쩡했다. **경계 근처 값(10,500원)에서만** 고리가 진동한다. 할인을 적용하면 1만 원 미만이 되고, 할인을 빼면 다시 1만 원 이상이 된다.
- 관찰 2 — "같은 값이면 멈춘다" 가드는 진동을 못 막았다. 값이 둘 사이를 오가며 매번 바뀌기 때문이다. 스택이 넘칠 때까지 2058번 갱신했다(이 환경의 기본 스택 크기에서 여러 번 실행해도 같았다. 스택 크기가 다르면 숫자도 달라진다 — 사실 점검 재실행에서 `node --stack-size=2000`으로 돌리면 4190회였다).
- 관찰 3 — 로그에 `by` 꼬리표를 직접 달아서야 누가 바꿨는지 보였다. 실제 바인딩 프레임워크에서는 이 정보가 호출 스택 속에 흩어진다.

같은 요구를 단방향으로: 상태는 한 곳, 바꾸는 길은 액션 하나, 파생값은 상태에서 한 번에 계산한다. 디스패처는 `flux` 4.0.4 패키지의 실제 `Dispatcher`를 썼다.

```js
const derive = s => {                                       // 파생값은 subtotal만의 함수
  const discount = s.subtotal >= 10000 ? Math.round(s.subtotal * 0.1) : 0;
  return { ...s, discount, total: s.subtotal - discount };
};
dispatcher.register(action => {
  actionLog.push(action);
  if (action.type === 'SET_SUBTOTAL') state = derive({ ...state, subtotal: action.value });
});
// 연쇄 시도: 스토어 콜백 안에서 다시 dispatch
dispatcher.register(action => { if (action.type === 'SET_SUBTOTAL') dispatcher.dispatch({ type: 'RECALC_DISCOUNT' }); });
```

(실험, 같은 환경, flux 4.0.4, `scratchpad/sd/40/e42/oneway.js`, 2026-10-02)

```text
입력 8000: {"subtotal":8000,"discount":0,"total":8000}
입력 12000: {"subtotal":12000,"discount":1200,"total":10800}
입력 10500: {"subtotal":10500,"discount":1050,"total":9450}
액션 기록: SET_SUBTOTAL(8000) from cart-form, SET_SUBTOTAL(12000) from cart-form, SET_SUBTOTAL(10500) from cart-form
연쇄 dispatch → Invariant Violation: Dispatch.dispatch(...): Cannot dispatch in the middle of a dispatch.
```

- 관찰 4 — 파생값을 상태의 함수로 계산하게 짠 단방향 쪽은 "할인 기준이 소계인가 합계인가"를 **정해야만** 코드를 쓸 수 있었다. 파생값을 상태의 함수로 쓰려면 계산 순서가 하나여야 한다. 양방향 바인딩은 이 모순된 명세를 그대로 받아들였다가 실행 중에 진동했다.
  - 단방향 버전은 "소계 1만 원 이상이면 소계의 10%"로 정했다. 양방향 버전과 규칙이 같지 않다. 실험이 보인 것은 "모순이 드러나는 시점"의 차이다. 파생값을 스토어에 따로 저장하는 것은 Flux도 막지 않는다(스토어 여러 개 + `waitFor` 순서로 짜면 진동 대신 순서에 따른 값이 나올 수 있다).
- 관찰 5 — 상태 변경마다 액션 기록이 남는다. "어디서 바뀌었나"는 액션 목록을 보면 된다.
- 관찰 6 — Flux 디스패처는 디스패치 도중 다시 디스패치하면 불변식 위반으로 거부한다(Flux `Dispatcher.js`의 `invariant` 문구 그대로). 연쇄 갱신을 구조로 막는다. 스토어 사이 순서가 필요하면 `waitFor()`로 의존을 선언한다(Flux 문서).

### 5. 서버 MVC에서 깨지는 곳

```text
 요청 → [Front Controller] → [Controller: 검증·규칙·조회·변환·응답 조립 ... 300줄] → [Template: if 등급=='GOLD' ...]
                                    ↑ Massive Controller                                    ↑ 템플릿 속 규칙
```

- 컨트롤러는 "입력을 받아 유스케이스에 넘기고 결과를 표현으로 바꾸는" 얇은 층으로 두는 것이 표현 분리의 의도다(해석).
- 템플릿에 규칙이 들어가면 같은 규칙을 다른 템플릿·API가 따로 구현한다.

## 쓰이는 자료구조·알고리즘

- **옵서버(관찰자) 패턴** — 구독자 목록과 알림. MVC·MVP·MVVM의 데이터 바인딩 바탕이다. 구독 그래프에 고리가 생기면 실험처럼 진동·무한 재귀가 된다. GoF 패턴 정리는 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md).
- **디스패처 + 콜백 레지스트리(Flux)** — 등록된 콜백 배열, 디스패치 중 플래그(`_isDispatching`), 콜백별 처리 중/처리 완료 표시로 `waitFor` 순서를 맞춘다(Flux `Dispatcher.js` 소스). 디스패치가 끝나기 전 새 디스패치는 거부한다.
- **리듀서(update) = 상태 전이 함수** — `(state, action) → state`. Elm의 `update`, Flux 스토어의 액션 처리.
- **파생값 = 상태의 순수 함수** — 계산 순서가 DAG(비순환 그래프)이어야 정의된다. 고리가 있으면 값이 정의되지 않는다(실험의 진동).
- **Front Controller = 요청 라우팅 테이블** — URL·메서드 → 핸들러 매핑. 공통 처리(인증·로깅)는 앞단 체인으로([34-middleware-filter-interceptor-chains](../34-middleware-filter-interceptor-chains/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **규칙을 화면 밖으로**: 할인·상태 전이 같은 규칙은 도메인·유스케이스 쪽 함수로. 컨트롤러·프레젠터·컴포넌트는 그것을 부른다.
2. **동기화 방식을 고른다**: 화면 수가 적고 단순하면 바인딩(MVVM)이 짧다. 파생값이 많고 여러 화면이 같은 상태를 보면 단방향(스토어 + 액션)이 추적하기 쉽다.
3. **파생값은 저장하지 말고 계산한다**: `total`을 상태로 두고 바인딩으로 맞추는 대신 `derive(state)`로 매번 계산한다(실험).
4. **변경 경로를 하나로**: 상태를 바꾸는 길을 액션(또는 프레젠터 메서드)으로 모은다. 로그·되돌리기(undo)도 이 지점에 붙는다(Fowler가 Potel MVP의 명령 묶음이 undo/redo의 기반이 된다고 적음).
5. **서버 MVC 컨트롤러는 얇게**: 요청 → 유스케이스 입력, 결과 → 응답 모델. 규칙은 유스케이스로(44).

### 2. 코드 (TypeScript, 단방향 최소형)

```ts
type State = { subtotal: number };
type Action = { type: 'SET_SUBTOTAL'; value: number; source: string };

const reduce = (s: State, a: Action): State =>
  a.type === 'SET_SUBTOTAL' ? { ...s, subtotal: a.value } : s;

const view = (s: State) => {                         // 파생값은 그릴 때 계산
  const discount = s.subtotal >= 10_000 ? Math.round(s.subtotal * 0.1) : 0;
  return { ...s, discount, total: s.subtotal - discount };
};
```

### 3. 진단

- 브라우저: 상태 변경 로그(액션 목록)가 있으면 그것부터. 없으면 바인딩 setter에 중단점과 호출 스택.
- 서버: 컨트롤러 메서드 길이·분기 수(순환 복잡도, 52 complexity-metrics), 템플릿 안 조건문 수 `grep -c 'th:if' templates/**/*.html`.

## 장애 시나리오와 대처

### 1. Massive Controller — 규칙 재사용·테스트 불가 (⚠ 커리큘럼)

- 현상: 모바일 API를 추가하니 웹 컨트롤러의 할인 규칙을 복사해야 한다. 둘이 어긋나 결제 금액이 다르다.
- 보이는 형태: 컨트롤러 테스트가 HTTP 요청·세션·DB를 다 띄워야 돈다. 컨트롤러 메서드가 수백 줄이고 분기가 많다.
- 원인: 입력 처리와 규칙이 한 클래스에 섞였다(표현 분리 실패).
- 대처: 규칙을 유스케이스·도메인 함수로 꺼내 컨트롤러는 호출만 하게 한다. 컨트롤러 테스트는 얇게, 규칙 테스트는 HTTP 없이.

### 2. 양방향 바인딩 연쇄 — 값이 어디서 바뀌었는지 추적 불가 (⚠ 커리큘럼)

- 현상: 특정 금액(10,500원)에서만 화면이 멈추거나 값이 깜빡인다.
- 보이는 형태: `RangeError: Maximum call stack size exceeded`, 같은 setter가 스택에 수천 번(실험: 2058회).
- 원인: 서로 다른 바인딩 규칙이 고리를 이뤘다. 값이 같으면 멈추는 가드로는 진동을 못 막는다.
- 대처: 파생값을 상태의 함수로 바꾸고 계산 방향을 하나로(실험의 단방향). 그 과정에서 모순된 명세("할인 기준은 소계인가 합계인가")를 결정한다.

### 3. 뷰 템플릿에 로직 → 화면별 규칙 불일치 (⚠ 커리큘럼)

- 현상: 목록 화면과 상세 화면이 "VIP 표시" 조건을 다르게 보여 준다.
- 보이는 형태: 템플릿마다 `th:if="${user.total >= 1000000 and ...}"` 같은 조건이 복사되어 있고 조금씩 다르다.
- 원인: 템플릿(Template View)은 표시만 하라는 경계가 무너졌다.
- 대처: 판단은 뷰모델·응답 모델의 필드(`isVip`)로 계산해 넘기고 템플릿은 그 값만 쓴다.

### 4. 스토어 콜백에서 또 dispatch — 연쇄 갱신 재발

- 현상: Flux 앱에서 액션 처리 중 다른 액션을 내려다 오류가 난다.
- 보이는 형태: `Invariant Violation: Dispatch.dispatch(...): Cannot dispatch in the middle of a dispatch.`(실험)
- 원인: 한 액션의 결과로 다른 상태를 바꾸려는 연쇄를 디스패처가 거부한 것이다.
- 대처: 스토어 사이 순서가 필요하면 `waitFor`로, 이어지는 동작이 필요하면 첫 액션 처리 안에서 함께 계산하거나 비동기 후속 액션을 명시적으로 낸다.

## 핵심 문장

- UI 패턴의 계보는 "그리기·입력·규칙을 어떻게 나누고, 값을 어떻게 동기화하나"에 대한 답들이다. 이름보다 의존과 동기화 방향을 본다.
- 공통 뼈대는 표현 분리다. 도메인 규칙은 화면을 모른다.
- 옵서버·양방향 바인딩은 암묵적이라 추적이 어렵다(Fowler). 실험에서 고리를 이룬 바인딩 두 개가 10,500원에서만 2058번 진동한 뒤 스택 오버플로를 냈다.
- 단방향 흐름에서 파생값을 상태의 함수로 계산하게 설계하면(이 실험의 선택) 계산 순서가 하나여야 해서, 모순된 규칙이 코드 작성 시점에 드러난다. Flux 자체가 강제하는 것은 디스패치 중 디스패치 거부다 — 디스패처는 디스패치 중 디스패치를 거부해 연쇄를 막는다.
- 서버 MVC에서 컨트롤러와 템플릿은 얇게 두고 규칙은 유스케이스로 보낸다.

## 관련 주제·근거

- 선행
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 의존 방향 규칙
- 후속·연결
  - [43-data-across-boundaries](../43-data-across-boundaries/2-summary.md) — 응답 모델·뷰모델을 엔티티와 분리
  - [44-architecture-in-code](../44-architecture-in-code/2-summary.md) — 클린 아키텍처의 프레젠터·뷰모델
  - [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — 옵서버
  - [34-middleware-filter-interceptor-chains](../34-middleware-filter-interceptor-chains/2-summary.md) — 요청 앞단 체인
  - [52 complexity-metrics](../52-complexity-metrics/2-summary.md)
- 글·문서
  - Martin Fowler, "GUI Architectures", 2006-07-18 — Forms and Controls, MVC, 표현 분리, 옵서버/흐름 동기화, MVP(Taligent·Potel·Dolphin), Supervising Controller, Passive View, Presentation Model <https://martinfowler.com/eaaDev/uiArchs.html>
  - Fowler, PoEAA 카탈로그: Model View Controller, Front Controller, Page Controller, Template View <https://martinfowler.com/eaaCatalog/>
  - Trygve Reenskaug, MVC 자료 페이지(Xerox PARC 1978–79) <https://folk.universitetetioslo.no/trygver/themes/mvc/mvc-index.html>
  - John Gossman, "Introduction to Model/View/ViewModel pattern for building WPF apps"(2005년 10월, Microsoft Learn 보관본) <https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps>
  - Flux "In-Depth Overview"(양방향 바인딩의 연쇄 갱신, 단일 디스패처, `waitFor`) <https://github.com/facebookarchive/flux/blob/main/docs/In-Depth-Overview.md> · `Dispatcher.js` 소스 <https://github.com/facebookarchive/flux/blob/main/src/Dispatcher.js> (저장소는 보관(archive) 상태)
  - Spring Framework 문서 "DispatcherServlet"(front controller 패턴) <https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html>
  - React 블로그, Bill Fisher·Jing Chen, "Flux: An Application Architecture for React", 2014-05-06 <https://legacy.reactjs.org/blog/2014/05/06/flux.html>
  - Elm 가이드 "The Elm Architecture"(Model · View · Update) <https://guide.elm-lang.org/architecture/>
- 실험 목록 (코드: scratchpad `sd/40/e42/`, node v22.23.2 `node:22-alpine` 컨테이너 `--cpus=2`)
  - 양방향 바인딩 연쇄 — `node twoway.js` (3회, 출력 동일)
  - 단방향 + flux 4.0.4 `Dispatcher` — `node oneway.js` (npm으로 flux 설치)
