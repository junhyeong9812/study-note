# JavaScript — 문법·API 주제 목록

> 1단계 리스트업이다. 아래 주제들의 3파일(질문·서머리·정답)은 **아직 없다**.
> 기준 소스: [ECMA-262 최신 초안](https://tc39.es/ecma262/) (2026-09-20 확인 시점 ES2027 초안) · [ECMA-262 판별 아카이브](https://262.ecma-international.org/) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) · 호스트 API 한정으로 [MDN](https://developer.mozilla.org/)
> 실행 검증: **가능**. 이 머신에 Node `v18.19.1`(기본 PATH)과 `v20.19.6`(nvm)이 있어 두 버전으로 돌려 차이를 확인한다. 다만 **ES2025~ES2027 기능 일부는 Node 18/20 에 없어 실행 검증이 불가**하고, 그런 행은 「미실행 — 명세로만 접지」로 표기한다. 브라우저 전용 API 는 실행하지 않는다.
> 기준일 2026-09-20.

## 이 언어에서 무엇을 자르는 축

JS 는 **값의 의미(강제 변환)·함수(스코프·`this`·클로저)·객체(프로토타입)·비동기(이벤트 루프)** 네 덩어리에서 사고가 나고, 표준 라이브러리는 그 위에 얇게 얹혀 있다.
그래서 축을 ①**값과 강제 변환** ②**선언·스코프·클로저** ③**함수와 `this`** ④**객체·프로토타입·클래스** ⑤**구조 분해/스프레드 같은 문법 편의** ⑥**이터레이션 프로토콜** ⑦**내장 객체 API(Array·Object·String·Map/Set·JSON·RegExp)** ⑧**오류 처리** ⑨**비동기 — 이벤트 루프에서 `async`/`await` 까지** ⑩**모듈** ⑪**메타 프로그래밍(Symbol·Proxy·Reflect)** 으로 자른다.
명세의 절 구분(식·문·함수와 클래스·내장 객체)은 분류에만 참고하고, 학습 단위는 **한 번에 인출할 기능 하나**로 잡았다.
언어 자체는 ECMA-262 를 우선하고, MDN 은 호스트 API(`AbortController`·`structuredClone`)에서만 근거로 쓴다.
「언제 들어왔나」는 [history/js](../../../../../history/js/)의 몫이고, 여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다. TS 목록은 이 목록을 **선행으로 전제**하고 타입 시스템만 다룬다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 우선 |
|---|------|------|----------------------|------|-----------|------|
| 01 | 값의 종류와 `typeof` | 문법 | 원시 7종과 객체를 구분하고 `typeof null`·`typeof function` 의 결과, 원시 값에 메서드를 부르면 일어나는 임시 래핑을 설명할 수 있다 | — | — | A |
| 02 | 강제 변환과 `==` 대 `===` | 문법 | ToPrimitive·ToNumber 규칙으로 헷갈리는 비교식의 결과를 예측하고 `==` 를 써도 되는 좁은 경우를 판단할 수 있다 | 01 | — | A |
| 03 | 숫자와 `BigInt` | 문법 | 배정밀도 부동소수점이 만드는 `0.1 + 0.2`·안전 정수 한계·`NaN` 의 성질을 설명하고 `BigInt` 를 숫자와 섞었을 때의 `TypeError` 를 예측할 수 있다 | 01 | `cs/foundations/data-representation/` | A |
| 04 | 문자열과 UTF-16 | 문법 | `length` 가 코드 유닛이라는 것과 서로게이트 페어·이모지 처리, `codePointAt`·well-formed 메서드(ES2024)·`Intl.Segmenter` 를 설명할 수 있다 | 01 | `cs/foundations/data-representation/` | A |
| 05 | `var`·`let`·`const` 와 TDZ | 문법 | 호이스팅과 TDZ 를 구분해 선언 전 참조가 `undefined` 인지 `ReferenceError` 인지 예측하고 `const` 가 무엇을 고정하는지 설명할 수 있다 | — | `history/js/02-ES6-모던.md` (도입 역사) | A |
| 06 | 스코프와 클로저 | 문법 | 함수가 생성 시점의 환경을 붙들고 있다는 것을 설명하고 루프 변수 캡처가 `var` 와 `let` 에서 갈리는 이유를 예측할 수 있다 | 05 | — | A |
| 07 | `this` 바인딩 네 규칙 | 문법 | 기본·암시적·명시적·`new` 바인딩과 화살표 함수의 렉시컬 `this` 로 임의의 호출식에서 `this` 가 무엇인지 판정할 수 있다 | 06 | — | A |
| 08 | 함수 정의 형태와 매개변수 | 문법 | 선언·표현식·화살표의 호이스팅·`this`·`arguments` 차이를 설명하고 기본값·나머지 매개변수·`length` 의 규칙을 예측할 수 있다 | 07 | — | A |
| 09 | `call`·`apply`·`bind` | 표준 API | 세 메서드로 `this` 와 인자를 바꿔 호출하고 `bind` 가 만든 함수의 성질(재바인딩 불가)을 설명할 수 있다 | 07 | — | B |
| 10 | 구조 분해 할당 | 문법 | 배열·객체·중첩·기본값·이름 바꾸기를 읽고 쓰며, `undefined` 와 `null` 에서 갈리는 실패를 예측할 수 있다 | 01 | — | A |
| 11 | 스프레드와 나머지 | 문법 | 배열·객체·호출 세 자리의 의미를 구분하고 얕은 복사라는 사실이 중첩 구조에서 만드는 결과를 예측할 수 있다 | 10 | — | A |
| 12 | 옵셔널 체이닝·널 병합·논리 할당 | 문법 | `?.`·`??`(ES2020)·`??=`(ES2021)가 단축 평가하는 지점과 `\|\|` 와 갈리는 falsy 케이스를 설명할 수 있다 | 2 | — | A |
| 13 | 객체 리터럴과 프로퍼티 | 문법 | 계산된 키·단축 표기·`get`/`set`·정수 키가 앞서는 열거 순서 규칙을 설명할 수 있다 | 01 | — | A |
| 14 | 프로퍼티 디스크립터와 동결 | 표준 API | `writable`·`enumerable`·`configurable` 을 읽고 `freeze`·`seal` 이 어디까지(얕게) 막는지 판단할 수 있다 | 13 | — | B |
| 15 | 프로토타입 체인 | 문법 | 프로퍼티 조회가 체인을 타는 경로를 그리고 `Object.create`·`__proto__`·`instanceof` 의 관계를 설명할 수 있다 | 13 | — | A |
| 16 | `class` 문법 | 문법 | 필드·정적 멤버·프라이빗 `#`(ES2022)·`static {}` 초기화 블록이 프로토타입과 인스턴스 중 어디에 붙는지 판정할 수 있다 | 15 | `cs/foundations/oop-basics/` | A |
| 17 | 상속과 `super` | 문법 | `extends`·`super`·`new.target` 의 동작과 내장 객체를 상속했을 때의 제약을 설명할 수 있다 | 16 | — | B |
| 18 | `for...in` 과 열거 | 문법 | 열거 가능 프로퍼티와 체인 순회를 설명하고 배열에 `for...in` 을 쓸 때 생기는 문제를 예측할 수 있다 | 15 | — | B |
| 19 | 이터러블 프로토콜과 `for...of` | 문법 | `Symbol.iterator` 계약을 구현하고 `for...of`·스프레드·구조 분해가 같은 프로토콜을 쓴다는 것을 설명할 수 있다 | 11 | — | A |
| 20 | 제너레이터 | 문법 | `function*`·`yield`·`yield*`·`next(값)` 의 흐름을 추적하고 지연 시퀀스를 만들 수 있다 | 19 | — | B |
| 21 | 이터레이터 헬퍼 | 표준 API | ES2025 `map`·`filter`·`take`·`drop`·`toArray` 로 지연 파이프라인을 쓰고 배열 메서드와의 평가 시점 차이를 설명할 수 있다 | 20 | — | C |
| 22 | `Symbol` 과 잘 알려진 심볼 | 문법 | 심볼 키의 성질과 `Symbol.iterator`·`toPrimitive`·`hasInstance` 가 언어 동작 자체를 바꾸는 지점을 설명할 수 있다 | 19 | — | B |
| 23 | `Map`·`Set` 과 약한 컬렉션 | 표준 API | 객체 키·삽입 순서·SameValueZero 비교를 근거로 `Map` 과 객체를 고르고 `WeakMap` 의 수명 의미를 설명할 수 있다. 집합 연산 메서드는 ES2025, `getOrInsert` 계열(Upsert)은 ES2026 | 22 | `cs/data-structure/05-hashmap/` | A |
| 24 | 배열 변형 메서드 | 표준 API | `push`·`splice`·`sort`·`reverse`·`fill` 이 원본을 바꾼다는 것과 `sort` 의 기본 문자열 비교·안정 정렬 보장을 설명할 수 있다 | 01 | `cs/foundations/data-structures-basics/` | A |
| 25 | 배열 비변형·복사 메서드 | 표준 API | `map`·`filter`·`reduce`·`slice`·`concat` 과 ES2024 `toSorted`·`toReversed`·`toSpliced`·`with` 를 구분해 불변 변환을 쓸 수 있다 | 24 | — | A |
| 26 | 배열 탐색·평탄화·생성 | 표준 API | `indexOf` 와 `includes` 가 `NaN` 에서 갈리는 것, `find`/`findLast`·`at`·`flat`/`flatMap`·`Array.from`·`fromAsync`(ES2026)를 골라 쓸 수 있다 | 24 | — | B |
| 27 | `Object` 정적 메서드 | 표준 API | `keys`/`values`/`entries`·`assign`·`fromEntries`·`Object.groupBy`(ES2024)로 객체를 변환하고 `assign` 의 얕은 복사와 getter 호출을 설명할 수 있다 | 13 | — | A |
| 28 | `String` 메서드와 템플릿 리터럴 | 표준 API | 자주 쓰는 문자열 메서드와 태그 템플릿·`String.raw` 를 쓰고 `replace` 의 `$` 치환 규칙을 설명할 수 있다 | 04 | — | A |
| 29 | 정규식 기본 | 표준 API | 리터럴·플래그·`match`/`matchAll`/`replace`/`replaceAll` 을 쓰고 `g` 플래그와 `lastIndex` 가 만드는 상태 버그를 설명할 수 있다 | 28 | `cs/algorithm/25-string-matching/` (알고리즘 쪽) | A |
| 30 | 정규식 심화 | 표준 API | 캡처·명명 그룹·룩어라운드·유니코드 속성 이스케이프·`v` 플래그(ES2024)·`RegExp.escape`(ES2025)를 쓰고 백트래킹 폭발을 판단할 수 있다 | 29 | — | B |
| 31 | `JSON` | 표준 API | `stringify` 의 타입 매핑(`undefined`·함수·순환 참조)과 `replacer`/`reviver`·`toJSON` 을 설명하고 깊은 복사 대용으로 쓸 때의 손실을 판단할 수 있다 | 27 | — | A |
| 32 | 오류 처리와 `Error` | 문법 | `throw`/`try`/`catch`/`finally` 흐름과 `Error` 계층·`cause`(ES2022)·`Error.isError`(ES2026)를 설명하고 `finally` 의 `return` 이 예외를 삼키는 경우를 예측할 수 있다 | 01 | — | A |
| 33 | 동등성 세 종류 | 관용구 | `===`·`Object.is`·SameValueZero 가 `NaN`·`±0` 에서 갈리는 것을 설명하고 `includes`/`indexOf`·`Map` 키 비교 결과를 예측할 수 있다 | 02 | — | B |
| 34 | 타입 검사 관용구 | 관용구 | `Array.isArray`·`Object.prototype.toString`·`instanceof`·덕 타이핑 중 어느 검사가 realm·프로토타입 조작에서 깨지는지 판단할 수 있다 | 15 | — | B |
| 35 | 엄격 모드 | 문법 | strict 가 바꾸는 규칙(암시적 전역 금지·`this` 가 `undefined`·중복 매개변수)과 모듈이 항상 strict 라는 것을 설명할 수 있다 | 05 | — | B |
| 36 | 이벤트 루프와 마이크로태스크 | 관용구 | 동기 코드·마이크로태스크·매크로태스크의 실행 순서를 출력 순서로 예측하고 마이크로태스크 기아를 설명할 수 있다 | 32 | `history/js/04-비동기-진화.md` · `cs/foundations/process-thread/` | A |
| 37 | Promise 상태 모델 | 표준 API | pending·fulfilled·rejected 전이와 `then` 체인의 값·예외 전파를 추적하고 미처리 거부가 언제 보고되는지 설명할 수 있다 | 36 | `history/js/04-비동기-진화.md` | A |
| 38 | Promise 조합기 | 표준 API | `all`·`allSettled`·`race`·`any` 를 상황에 맞게 고르고 `withResolvers`(ES2024)·`try`(ES2025)의 쓰임을 설명할 수 있다 | 37 | — | A |
| 39 | `async`/`await` | 문법 | async 함수가 항상 Promise 를 반환한다는 것, `await` 가 중단·재개하는 지점, 순차와 병렬 실행의 차이를 설명할 수 있다 | 37 | `history/js/04-비동기-진화.md` | A |
| 40 | 비동기 이터레이션 | 문법 | `for await...of` 와 async generator 로 스트림을 소비하고 동기 이터러블과의 차이를 설명할 수 있다 | 20, 39 | — | B |
| 41 | 취소와 타임아웃 | 표준 API | `AbortController`/`AbortSignal`(호스트 API)로 중단을 전파하고 Promise 자체에는 취소가 없다는 사실이 만드는 제약을 판단할 수 있다 | 39 | `cs/ops-patterns/deadline-propagation.md` | B |
| 42 | ESM 모듈 | 문법 | `import`/`export` 의 정적 구조·라이브 바인딩·호이스팅을 설명하고 순환 의존에서 무엇이 `undefined` 인지 예측할 수 있다 | 35 | `history/js/02-ES6-모던.md` | A |
| 43 | CJS 와 ESM 상호운용 | 관용구 | `require`/`module.exports` 와 `import` 의 차이, `type` 필드·확장자 해석, 서로 부를 때 막히는 지점을 판단할 수 있다 | 42 | `history/js/03-Node-런타임.md` | A |
| 44 | 동적 `import`·top-level `await`·import attributes | 문법 | 지연 로딩과 모듈 평가 순서를 설명하고 import attributes·JSON 모듈(ES2025)의 쓰임을 판단할 수 있다 | 42 | — | B |
| 45 | `Proxy` | 표준 API | 트랩으로 조회·대입·삭제를 가로채고 대상의 불변식을 어겼을 때 `TypeError` 가 나는 경우를 설명할 수 있다 | 14 | — | C |
| 46 | `Reflect` | 표준 API | `Reflect` 메서드가 Proxy 트랩과 1:1 로 대응하는 구조와 기존 `Object` 메서드·연산자와의 차이를 설명할 수 있다 | 45 | — | C |
| 47 | `WeakRef`·`FinalizationRegistry` | 표준 API | 약한 참조로 관찰 가능한 것과 GC 시점에 기대면 안 되는 이유를 설명할 수 있다 (ES2021) | 23 | `cs/foundations/memory-management/` | C |
| 48 | 깊은 복사 수단 비교 | 관용구 | JSON 왕복·스프레드·`structuredClone`(호스트 API)이 각각 보존하지 못하는 것을 비교해 고를 수 있다 | 31 | — | B |
| 49 | `Date` 와 Temporal | 표준 API | `Date` 의 0 기반 월·파싱 불안정·가변성을 설명하고 Temporal(ES2027)이 무엇을 바꾸는지 판단할 수 있다 | 01 | — | B |
| 50 | `Intl` 국제화 포맷 | 표준 API | 숫자·날짜·목록·상대 시간 포맷과 로케일 비교(ECMA-402)를 쓰고 수동 포맷이 깨지는 자리를 설명할 수 있다 | 49 | — | C |
| 51 | 명시적 자원 관리 `using` | 문법 | `using`/`await using` 과 `Symbol.dispose`(ES2027)가 해제 순서를 어떻게 보장하는지 설명하고 런타임 지원 여부를 판단할 수 있다 | 32 | — | C |
| 52 | `switch`·라벨·흐름 제어 세부 | 문법 | `switch` 가 `===` 로 비교한다는 것과 fallthrough·라벨 `break`/`continue` 의 동작을 설명할 수 있다 | 32 | — | C |

## 기존 주제와 겹치는 것

- **`history/js/` 7편** — 「언제 들어왔나」는 전부 그쪽이다. #5·#42(ES6 도입), #36·#37·#39(콜백→Promise→async 진화), #43(Node 런타임)은 역사 서술을 링크만 하고, 여기서는 **현재 규칙과 실패 모드**만 다룬다.
- **`cs/foundations/data-representation/`** — 부동소수점·문자 인코딩 일반론. #3·#4 는 그 일반론을 **JS 의 double 단일 수 타입과 UTF-16 문자열**이라는 구체 제약으로 좁혀 받는다.
- **`cs/foundations/oop-basics/`** — OOP 일반론. #16 은 프로토타입 위에 얹힌 `class` 라는 JS 고유 구조만 본다.
- **`cs/data-structure/05-hashmap/`·`cs/foundations/data-structures-basics/`** — 해시맵·배열의 원리는 그쪽. #23·#24 는 **어떤 내장을 고르고 어떤 메서드가 원본을 바꾸는가**만 다룬다.
- **`cs/foundations/process-thread/`** — 스레드·스케줄링 일반론. #36 은 단일 스레드 + 큐라는 JS 실행 모델로 좁힌다.
- **`cs/ops-patterns/deadline-propagation.md`** — 데드라인 전파 패턴은 그쪽. #41 은 `AbortSignal` API 사용법에 한정한다.

## 뺀 것과 이유

- **DOM·브라우저 API(이벤트·fetch·스토리지·Web Workers)** — 언어가 아니라 호스트다. `AbortController`·`structuredClone` 만 언어 기능과 맞물리는 자리라 예외로 남겼고 「호스트 API」로 표기했다.
- **Node 런타임 API(fs·http·stream·worker_threads)** — 런타임 표준 라이브러리다. 필요하면 별도 갈래로 제안한다.
- **빌드 도구·번들러·트랜스파일(webpack·vite·Babel)** — `history/js/05-빌드-생태계.md` 의 몫.
- **프레임워크(React·Vue 등)** — `history/js/06-프레임워크-진화.md`.
- **타입 관련 일체** — TS 목록으로 보낸다. 이 목록에는 타입 표기가 한 줄도 없다.
- **`eval`·`with`·레거시 8진 리터럴** — 엄격 모드에서 막히거나 쓰지 않는다. #35 에서 한 줄로만 언급한다.
- **버전별 신기능 나열** — `history/js/`.

## 버전 기준

기준은 **ES2024~ES2026 에서 이미 확정(stage 4)된 것**이며, 각 기능이 **어느 판에 들어갔는지 행마다 적었다**. ES2027 은 아직 초안이라 그 표시를 붙여 구분한다.

| 판 | 이 목록에서 해당하는 것 |
|---|---|
| ES2020~2022 | 옵셔널 체이닝·널 병합(#12), 논리 할당(ES2021, #12), `WeakRef`(ES2021, #47), 프라이빗 필드·`static {}`·`Error.cause`(ES2022, #16·#32) |
| ES2024 | `toSorted` 계열 변경 없는 배열 메서드(#25), `Object.groupBy`(#27), 정규식 `v` 플래그(#30), `Promise.withResolvers`(#38), well-formed 문자열 메서드(#4) |
| ES2025 | 이터레이터 헬퍼(#21), 집합 연산 메서드(#23), `RegExp.escape`(#30), `Promise.try`(#38), import attributes·JSON 모듈(#44) |
| ES2026 | `Error.isError`(#32), `Array.fromAsync`(#26), Upsert(`getOrInsert` 계열, #23) |
| ES2027 초안 | Temporal(#49), 명시적 자원 관리 `using`(#51) — **초안 단계이고 Node 18/20 에 없어 실행 검증 불가** |

실행 검증은 **Node 18.19.1 과 20.19.6** 두 버전으로 한다. ES2025 이후 기능은 이 두 런타임에서 대부분 돌지 않으므로, 해당 주제의 3파일에는 **「명세로만 접지 — 이 머신에서 미실행」**을 명시한다.
