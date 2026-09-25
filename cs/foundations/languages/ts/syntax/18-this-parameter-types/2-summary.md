# ts/syntax/18 — `this` 매개변수 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — More on Functions: Declaring `this` in a Function](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function) ·
> [TSConfig — `strictBindCallApply`](https://www.typescriptlang.org/tsconfig/#strictBindCallApply) ·
> [Handbook — Utility Types: `ThisParameterType`·`OmitThisParameter`](https://www.typescriptlang.org/docs/handbook/utility-types.html).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version (sh exit=0) =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 블록은 **옵션을 배너에 적힌 것만** 준 결과다.
> 이 배치는 `-t es2022 --strict` 를 **전부 명시**했다 — 7.0 의 기본값에 기대지 않고 배너만 보고 다시 던질 수 있게 했다.
> `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로 이 블록들은 설정 파일 없이 그대로 재현된다.
> **버전** — `this` 매개변수는 TS 2.0, `strictBindCallApply` 는 TS 3.2, `ThisParameterType`·`OmitThisParameter` 는 TS 3.3 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 배치가 쓰는 탐침 — 「컴파일러가 타입을 말하게 하는 법」

**추론된 타입은 눈에 안 보인다.** 그래서 이 갈래는 **일부러 틀린 주석을 달아 컴파일러가 답을 뱉게** 한다.

```text
  const probe: null = 무엇인가;
                      └─ 이 자리의 타입이 X 라면

  error TS####: Type 'X' is not assignable to type 'null'.   <- 실제 코드는 TS2322
                      ↑ 여기서 X 를 읽는다
```

- ★ `null` 은 **거의 아무것도 안 받는 타입**이라(`strictNullChecks` 가 켜진 판에서) 무엇을 넣어도 `TS2322` 가 난다.
- ★★ 그래서 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★★★ 창이 하나 더 있다 — **`--declaration` 으로 뽑은 `.d.ts`** 다. 6절에서 둘을 나란히 놓고 **어느 쪽이 나은지** 가린다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 방출된 `.js` 전문 · `.d.ts` 전문 | 방출기의 고정 형식이다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **★ 설정에 달렸다** | ★★★ 3절 — `strictBindCallApply` | 켠 판 **6건**, 끈 판 **0건**. 둘 다 실었다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | ★ `node` 의 예외 **메시지 본문** | 그래서 `e.constructor.name` **만** 찍었다 — 이름은 안 흔들린다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **안 잰 것** | `this` 매개변수가 검사 시간에 주는 영향 | 재지 않았다 |
| **★ 부적용** | 「여러 번 돌려 본다」 | 이 주제에는 난수·시각·순서 비보장이 **한 칸도 없다** |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ 3절의 끈 판은 **진단이 0줄**이다 — 그 블록도 **명령과 종료 코드까지** 캡처했다.

## 한눈에 — 쉽게 말하면

**`this` 매개변수는 「이 함수는 점 왼쪽에 무엇이 와야 한다」를 적는 칸이다. 그 칸은 컴파일이 끝나면 사라진다.**

| 비유 | 실체 |
|---|---|
| 식당 예약표의 **「동반자 란」** | `function f(this: T, …)` 의 첫 칸 |
| 동반자 란은 **인원수에 안 들어간다** | 인자 개수·`length` 에 안 센다 |
| 예약표는 **입장할 때 회수된다** | 방출된 `.js` 에 한 글자도 안 남는다 |
| 종업원이 **입구에서 확인**한다 | `tsc` 가 호출식에서 확인한다(`TS2684`) |
| 표를 안 내고 들어가면 | JS 규칙 그대로 — `this` 는 `undefined` 다 |

- ★★★ 한 줄로 — 「**JS 의 `this` 규칙은 하나도 안 바뀐다. 타입만 얹힌다.**」
- ★★ 네 규칙은 [JS 갈래의 `this` 바인딩 네 규칙](../../../js/syntax/07-this-binding-four-rules/)이 정본이다.
  여기서 새로 배우는 것은 **「그 규칙을 어길 때 컴파일이 먼저 잡아 준다」** 하나다.

```text
  같은 함수, 두 층

  ① 소스
     function area(this: Rect, scale: number) { return this.w * this.h * scale; }
                   └──────┬──────┘
                    타입 층에만 있는 칸
            │
            ▼  tsc 가 호출식을 검사한다
     rect.area(2)        통과 — 점 왼쪽이 Rect 다
     const f = rect.area; f()   TS2684 — 점 왼쪽이 없다

            │
            ▼  방출
  ② .js
     function area(scale) { return this.w * this.h * scale; }
                   └─ 칸이 통째로 사라졌다. 인자가 하나로 밀린다
```

```text
  검사가 걸리는 자리와 안 걸리는 자리

     const detached = rect.area;      ← 조용하다 (대입은 검사 안 함)
     detached();                      ← TS2684 (호출이 검사 지점이다)
          ▲
          └─ 실측: 19행은 진단이 없고 20행에만 있다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **`this` 매개변수는 런타임에 있나** — 컴파일한 `.js` 를 꺼내 **직접 확인**한다(2절). 이 주제의 본체다.
2. **어디서 막히나** — 떼어낸 메서드·`call`/`bind`·콜백·화살표를 전부 던져 **코드 번호**를 받는다(1·3·4절).
3. **`this` 를 타입으로 꺼낼 수 있나** — `ThisParameterType`·`OmitThisParameter` 를 탐침과 `.d.ts` 두 창으로 본다(5·6절).

★ [**16번 주제**](../16-function-types-and-overloads/)가 함수 타입 표기를 세웠다면 여기는 **그 표기의 첫 칸**이다.
★★ 앞 묶음(함수·`this`)의 꼬리이고, 다음은 **제네릭 사슬**([**19번 주제**](../19-generics-basics/) → [**20번 주제**](../20-generic-constraints-and-defaults/) → [**21번 주제**](../21-inference-control-const-and-noinfer/))이다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 성질 |
|---|---|---|
| ★★★ **진단 전문** | 어디서 막히나 — `TS2684`·`TS2730`·`TS2345`·`TS2741` | 사실 |
| ★★ **`null` 탐침** | 컴파일러가 **계산한** 타입 글자 | **계산된 것** |
| ★★ **`--declaration` 의 `.d.ts`** | 방출기가 **적은** 타입 글자 | **적은 것** — 정규화하지 않는다 |
| ★★★ **방출 `.js` + `node` 실행** | 런타임에 **무엇이 남는가** | 사실 — 이 주제의 본체 |

★★★ 뒤의 둘이 다른 답을 주면 **어느 쪽이 「적은 것」이고 어느 쪽이 「계산된 것」인지부터** 갈라라(6절).

비용 — 컴파일 세 번 + 실행 한 번.

### (1) ★★★ `this` 는 첫 매개변수 자리의 가짜 칸이다

**언제 쓰나** — 「메서드를 변수에 담아 넘겼더니 런타임에 터진다」를 **컴파일에서 잡고 싶을 때.**

```ts
// ex.18a.ts
// this 매개변수는 첫 매개변수 자리에만 오는 가짜 매개변수다 -- 떼어내 부르면 막힌다
interface Rect {
    w: number;
    h: number;
    area(this: Rect): number;
}

const rect: Rect = {
    w: 3,
    h: 4,
    area(this: Rect) {
        return this.w * this.h;
    },
};

const byMethod = rect.area();
const p1: null = byMethod;

const detached = rect.area;
detached();

function areaOf(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}
const p2: null = areaOf;
const p3: null = rect.area;

declare const noThis: { w: number; h: number };
areaOf.call(rect, 2);
console.log(byMethod, p1, p2, p3, noThis);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.18a.ts (tsc exit=1) =====
ex.18a.ts(17,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.18a.ts(20,1): error TS2684: The 'this' context of type 'void' is not assignable to method's 'this' of type 'Rect'.
ex.18a.ts(25,7): error TS2322: Type '(this: Rect, scale: number) => number' is not assignable to type 'null'.
ex.18a.ts(26,7): error TS2322: Type '(this: Rect) => number' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이다 — 17·20·25·26행.
- 17행은 탐침이다. `rect.area()` 가 **`number`** 다 — 정상 호출은 통과한다.
- ★★★ **19행에는 진단이 없다.** `const detached = rect.area;` 는 **조용히 통과**한다.\
  막히는 것은 **20행의 호출**이다 — 「The 'this' context of type 'void' is not assignable to method's 'this' of type 'Rect'.」
- ★★ 즉 **검사 지점은 대입이 아니라 호출식**이다. 「점 왼쪽이 없는 호출」이 `void` 로 읽힌다.
- ★★★ 25·26행이 이 절의 별이다. 탐침이 뱉은 타입에 **`this: Rect` 가 그대로 들어 있다** —\
  `(this: Rect, scale: number) => number` · `(this: Rect) => number`.\
  **타입 층에서는 매개변수처럼 보인다.** 그런데 인자 개수에는 안 센다(2절 실행 출력).
- ★ [JS 갈래의 `this` 바인딩 네 규칙](../../../js/syntax/07-this-binding-four-rules/)이 「런타임에 `undefined` 가 된다」로 보여 준 그 자리다.\
  **JS 는 터질 때까지 모르고, TS 는 부르기 전에 안다.**

> **`this` 매개변수(`this` parameter)** — 매개변수 목록의 **첫 자리에만** 올 수 있는 타입 전용 칸.\
> 이름이 `this` 여야 하고, **인자를 하나 더 받는 것이 아니다.**

비용 — 없다. 다만 **떼어 쓰는 관용구가 막히므로** 그럴 때는 `bind` 하거나 화살표로 감싸야 한다.

### (2) ★★★ 방출물에는 한 글자도 안 남는다 — 이 주제의 본체

**언제 쓰나** — 「`this` 매개변수가 런타임에 무엇을 하나」라는 질문을 **지울 때.**

```ts
// ex.18b.ts
// this 매개변수가 방출물에 남는가 -- 남지 않는다. 타입을 벗기면 JS 규칙이 그대로 돌아온다
interface Rect {
    w: number;
    h: number;
}

function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

const rect: Rect = { w: 3, h: 4 };
console.log("1) area.call(rect, 2) :", area.call(rect, 2));

const holder = { w: 5, h: 6, area };
console.log("2) holder.area(1)     :", holder.area(1));

const detached = area as unknown as (scale: number) => number;
try {
    detached(2);
} catch (e) {
    console.log("3) 떼어내 호출        :", (e as Error).constructor.name);
}

const bound = area.bind(rect);
console.log("4) bind 한 뒤         :", bound(10));
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e18b ex.18b.ts (tsc exit=0) =====
===== 방출된 ex.18b.js =====
"use strict";
function area(scale) {
    return this.w * this.h * scale;
}
const rect = { w: 3, h: 4 };
console.log("1) area.call(rect, 2) :", area.call(rect, 2));
const holder = { w: 5, h: 6, area };
console.log("2) holder.area(1)     :", holder.area(1));
const detached = area;
try {
    detached(2);
}
catch (e) {
    console.log("3) 떼어내 호출        :", e.constructor.name);
}
const bound = area.bind(rect);
console.log("4) bind 한 뒤         :", bound(10));
```

```text
===== node e18b/ex.18b.js (node exit=0) =====
1) area.call(rect, 2) : 24
2) holder.area(1)     : 30
3) 떼어내 호출        : TypeError
4) bind 한 뒤         : 120
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `tsc` 종료 코드가 **`0`** 이고 **진단이 0줄**이다. 이 파일에는 타입 오류가 없다.
- ★★★ 방출된 `.js` 의 첫 함수가 `function area(scale) { … }` 다 — **`this: Rect` 가 통째로 사라졌다.**\
  남은 매개변수는 `scale` **하나**다. **이것이 18 의 본체다.**
- ★★ 그래서 몸통의 `this.w` 는 **아무 선언에도 안 묶인 채** 그대로 남는다 — JS 의 평범한 `this` 다.
- ★ 실행 출력 네 줄이 [JS 갈래의 네 규칙](../../../js/syntax/07-this-binding-four-rules/)을 그대로 재현한다 —\
  `call` 로 주면 **24**, 점 왼쪽에 담아 부르면 **30**(`5 × 6 × 1`), `bind` 하면 **120**.
- ★★★ 세 번째 줄이 결정적이다. `as unknown as` 로 **타입을 벗겨** 떼어내 부르니 **`TypeError`** 다.\
  방출물이 `"use strict"` 라 `this` 가 `undefined` 이고, `undefined.w` 를 읽다 터진 것이다.\
  **타입을 벗기면 JS 규칙이 그대로 돌아온다** — `this` 매개변수는 **컴파일 타임에만 있는 것**이다.
- ★ 예외의 **메시지 본문은 안 실었다** — 판마다 문구가 바뀐다. `constructor.name` 만 찍었다.

비용 — 없다. 대신 **런타임 보호는 0**이다. `as` 하나로 뚫린다(목록의 **30번 주제**).

### (3) ★★ `strictBindCallApply` — 이 주제의 설정 칸

**언제 쓰나** — 「`call`·`apply`·`bind` 에 아무거나 넣어도 안 잡힌다」일 때.

```ts
// ex.18c.ts
// strictBindCallApply -- call / apply / bind 의 인자를 검사하게 만드는 플래그
interface Rect {
    w: number;
    h: number;
}

function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

const rect: Rect = { w: 3, h: 4 };
declare const notRect: { w: number };

area.call(rect, 2);
area.call(notRect, 2);
area.call(rect, "두 배");
area.apply(rect, [2]);
area.apply(rect, ["두 배"]);
area.bind(notRect);

function plain(x: number): number {
    return x;
}
plain.call(undefined, "문자열");
plain.apply(undefined, ["문자열"]);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.18c.ts (tsc exit=1) =====
ex.18c.ts(15,11): error TS2741: Property 'h' is missing in type '{ w: number; }' but required in type 'Rect'.
ex.18c.ts(16,17): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
ex.18c.ts(18,19): error TS2322: Type 'string' is not assignable to type 'number'.
ex.18c.ts(19,11): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Property 'h' is missing in type '{ w: number; }' but required in type 'Rect'.
ex.18c.ts(24,23): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
ex.18c.ts(25,25): error TS2322: Type 'string' is not assignable to type 'number'.
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --strictBindCallApply false ex.18c.ts (tsc exit=0) =====
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 켠 판은 **6건**, 끈 판은 **0건**이고 종료 코드가 **1 대 0**이다.\
  **한 파일의 진단이 통째로 사라진다** — 이 주제에서 설정이 답을 바꾸는 유일한 칸이다.
- 15행 — `area.call(notRect, 2)` 가 `TS2741` 이다. **`this` 인자가 `Rect` 를 못 채운다.**
- ★★ 16행 — `area.call(rect, "두 배")` 가 `TS2345` 다. **`call` 은 `this` 만 보는 게 아니라 나머지 인자도 본다.**
- ★★ 18행 — `apply` 는 `TS2322` 다. 인자를 **배열로** 주므로 배열 원소의 타입이 안 맞는 꼴이 된다. **코드가 다르다.**
- 19행 — `bind` 는 `TS2769` 다. 「No overload matches this call.」 — `bind` 의 시그니처가 **오버로드**라서 그렇다([**16번 주제**](../16-function-types-and-overloads/)).
- ★★★ 24·25행이 중요하다. `plain` 에는 **`this` 매개변수가 아예 없는데도** 인자 검사가 걸린다.\
  **`strictBindCallApply` 는 `this` 전용 플래그가 아니다** — `call`·`apply`·`bind` 의 **인자 전체**를 검사하게 하는 플래그다.
- ★ 끈 판에서는 이 여섯이 전부 조용하다. 그 판의 `call`·`apply`·`bind` 는 `any` 를 받는 옛 시그니처를 쓴다.

> **`strictBindCallApply`** — `strict` 에 딸려 켜진다(TS 3.2). 끄면 `call`·`apply`·`bind` 가 **인자를 검사하지 않는다.**

비용 — 켜면 **기존 코드의 `call`·`apply` 자리가 대량으로 빨개진다.** 단계적으로 켜는 순서는 목록의 **39번 주제**.

### (4) ★★ `this: void` 로 금지하고, 화살표에는 못 단다

**언제 쓰나** — 콜백 API 를 만들면서 「**이 콜백 안에서는 `this` 를 쓰지 마라**」를 타입으로 못 박을 때.

```ts
// ex.18d.ts
// this: void 는 "이 함수 안에서 this 를 쓰지 마라"는 계약이다 -- 그리고 화살표에는 this 매개변수를 못 단다
interface Tick {
    n: number;
}

declare function onTick(cb: (this: void, n: number) => void): void;

onTick(function (n) {
    console.log(n);
});

onTick(function (this: Tick, n) {
    console.log(this.n + n);
});

function useThis(this: Tick, n: number): void {
    console.log(this.n + n);
}
onTick(useThis);

function noThis(this: void, n: number): void {
    console.log(n, this);
}
onTick(noThis);

const arrowWithThis = (this: Tick, n: number) => n;

class Counter {
    n = 0;
    inc(this: Counter): void {
        this.n += 1;
    }
}
const counter = new Counter();
const incDetached = counter.inc;
incDetached();
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.18d.ts (tsc exit=1) =====
ex.18d.ts(12,8): error TS2345: Argument of type '(this: Tick, n: number) => void' is not assignable to parameter of type '(this: void, n: number) => void'.
  The 'this' types of each signature are incompatible.
    Type 'void' is not assignable to type 'Tick'.
ex.18d.ts(19,8): error TS2345: Argument of type '(this: Tick, n: number) => void' is not assignable to parameter of type '(this: void, n: number) => void'.
  The 'this' types of each signature are incompatible.
    Type 'void' is not assignable to type 'Tick'.
ex.18d.ts(26,24): error TS2730: An arrow function cannot have a 'this' parameter.
ex.18d.ts(36,1): error TS2684: The 'this' context of type 'void' is not assignable to method's 'this' of type 'Counter'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이다 — 12·19·26·36행.
- ★★★ 12행과 19행이 같은 말을 두 꼴로 한다. `(this: Tick, …)` 를 `(this: void, …)` 자리에 넣으면 `TS2345` 이고,\
  연쇄 설명이 「The 'this' types of each signature are incompatible.」 → 「Type 'void' is not assignable to type 'Tick'.」이다.
- ★★ **8행과 22행은 조용하다.** `this` 를 안 적은 익명 함수와 `this: void` 를 적은 함수는 **둘 다 통과**한다.\
  즉 `this: void` 는 **「없어야 한다」가 아니라 「`void` 로 받아라」** 이고, 안 적은 함수는 그 자리에 맞는다.
- ★★★ 26행 — 「An arrow function cannot have a 'this' parameter.」 **`TS2730`** 이다.\
  화살표 함수는 **자기 `this` 를 아예 안 만들므로**(JS 갈래의 네 규칙) 적을 칸이 없다.
- ★★ 36행 — 클래스 메서드에 `this: Counter` 를 달아 두면 **떼어낸 호출이 `TS2684`** 다. 1절과 같은 코드다.
- ★ 즉 이 주제의 진단은 **네 코드로 끝난다** — `TS2684`(호출) · `TS2345`(콜백 대입) · `TS2730`(화살표) · 그리고 3절의 `strictBindCallApply` 묶음.

비용 — `this: void` 를 박으면 **메서드를 그대로 넘길 수 없다.** 넘기려면 화살표로 감싸거나 `bind` 해야 한다.

### (5) ★★ `ThisParameterType` 과 `OmitThisParameter`

**언제 쓰나** — `this` 가 걸린 함수를 **감싸는 도우미**를 쓸 때.

```ts
// ex.18e.ts
// ThisParameterType 와 OmitThisParameter -- this 매개변수를 타입으로 꺼내고 지운다
export interface Rect {
    w: number;
    h: number;
}

export function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

export function plain(scale: number): number {
    return scale;
}

export type AreaThis = ThisParameterType<typeof area>;
export type PlainThis = ThisParameterType<typeof plain>;
export type AreaWithout = OmitThisParameter<typeof area>;
export const boundArea = area.bind({ w: 3, h: 4 });

declare const t1: AreaThis;
declare const t2: PlainThis;
declare const t3: AreaWithout;
const probe1: null = t1;
const probe2: null = t2;
const probe3: null = t3;
const probe4: null = boundArea;
console.log(probe1, probe2, probe3, probe4);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.18e.ts (tsc exit=1) =====
ex.18e.ts(23,7): error TS2322: Type 'Rect' is not assignable to type 'null'.
ex.18e.ts(24,7): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.18e.ts(25,7): error TS2322: Type '(scale: number) => number' is not assignable to type 'null'.
ex.18e.ts(26,7): error TS2322: Type '(scale: number) => number' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이고 전부 탐침이다.
- 23행 — `ThisParameterType<typeof area>` 가 **`Rect`** 다. `this` 칸의 타입만 뽑아낸다.
- ★★★ 24행이 뜻밖이다. `this` 매개변수가 **없는** 함수에 같은 걸 씌우면 **`unknown`** 이다 — `void` 가 아니다.\
  「`this` 가 없다」를 **`unknown` 으로 답한다**는 것은 던져 보기 전에는 못 맞힌다.
- 25행 — `OmitThisParameter<typeof area>` 가 **`(scale: number) => number`** 다. `this` 칸만 지운다.
- ★★ 26행이 그 쓸모를 보인다. `area.bind({w:3,h:4})` 의 타입이 **25행과 글자까지 같다** —\
  즉 **`bind` 의 결과 타입이 곧 `OmitThisParameter`** 다. 두 줄이 같은 답을 준다.

> **`ThisParameterType<T>`** — `T` 의 `this` 칸 타입. **없으면 `unknown`** 이다(실측).\
> **`OmitThisParameter<T>`** — `T` 에서 `this` 칸만 지운 함수 타입. `bind` 의 결과와 같다.

비용 — 오버로드된 함수에는 **마지막 시그니처만** 잡힌다. 이 배치에서는 **안 던졌다.**

### (6) ★★★ 두 창 대조 — `.d.ts` 에는 남고 `.js` 에는 없다

**언제 쓰나** — 라이브러리로 내보낼 때 **소비자가 `this` 제약을 보게 되는지** 확인할 때.

```ts
// ex.18f.ts
// 두 번째 창 -- .d.ts 에는 this 매개변수가 남고, 방출된 .js 에는 없다
export interface Rect {
    w: number;
    h: number;
}

export function area(this: Rect, scale: number): number {
    return this.w * this.h * scale;
}

export const bound = area.bind({ w: 3, h: 4 });
export const rectOnly = null as unknown as ThisParameterType<typeof area>;
export const without = null as unknown as OmitThisParameter<typeof area>;

export interface Handler {
    onTick(this: void, n: number): void;
}

export const method = {
    v: 1,
    read(this: { v: number }): number {
        return this.v;
    },
};
```

```text
===== tsc --pretty false -t es2022 --strict --declaration --outDir d18f ex.18f.ts (tsc exit=0) =====
===== 방출된 ex.18f.d.ts =====
export interface Rect {
    w: number;
    h: number;
}
export declare function area(this: Rect, scale: number): number;
export declare const bound: (scale: number) => number;
export declare const rectOnly: ThisParameterType<typeof area>;
export declare const without: OmitThisParameter<typeof area>;
export interface Handler {
    onTick(this: void, n: number): void;
}
export declare const method: {
    v: number;
    read(this: {
        v: number;
    }): number;
};
===== 방출된 ex.18f.js =====
export function area(scale) {
    return this.w * this.h * scale;
}
export const bound = area.bind({ w: 3, h: 4 });
export const rectOnly = null;
export const without = null;
export const method = {
    v: 1,
    read() {
        return this.v;
    },
};
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **같은 소스 하나에서 두 방출물이 나오는데 답이 정반대다.**\
  `.d.ts` 에는 `export declare function area(this: Rect, scale: number): number;` — **`this` 칸이 그대로** 있다.\
  `.js` 에는 `export function area(scale) { … }` — **없다.**
- ★★ `interface Handler` 의 `onTick(this: void, n: number): void;` 도 `.d.ts` 에 **적은 그대로** 실린다.
- ★★ 객체 리터럴의 메서드 `read(this: { v: number })` 도 `.d.ts` 에는 남고, `.js` 에서는 `read() { … }` 가 된다.
- ★★★ 그런데 `.d.ts` 는 **계산하지 않는다.** `rectOnly` 가 `ThisParameterType<typeof area>` 라고 **적은 그대로** 남았다 —\
  5절의 탐침은 같은 것을 **`Rect`** 라고 답했다. **둘이 다르면 탐침 쪽이 계산된 것**이다.
- ★ `bound` 만은 계산돼 있다 — `(scale: number) => number`. **이름이 안 붙은 자리는 펴서 적는다.**

★★★ **그래서 이 배치의 결론은 「탐침이 낫다」** — `.d.ts` 는 **적은 것**을 보여 주고, 탐침은 **계산된 것**을 보여 준다.
`.d.ts` 가 나은 자리는 하나다 — **여러 줄을 한 번에 훑을 때**(19·21 에서 그렇게 썼다).

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function f(this: T, x: number) { … }       ★ 첫 칸에만. 이름이 this 여야 한다
  interface I { m(this: I): void }            ★ 인터페이스 메서드에도
  const o = { v: 1, read(this: {v:number}) {} }  ★ 객체 리터럴 메서드에도
  function cb(this: void, n: number) { … }    ★ "this 를 쓰지 마라"
  const bad = (this: T) => 1;                 ✗ TS2730 — 화살표에는 못 단다

  ThisParameterType<typeof f>    ->  T      (없으면 unknown)
  OmitThisParameter<typeof f>    ->  (x: number) => void
```

**규칙 불릿**

- ★★★ **`this` 매개변수는 방출물에 한 글자도 안 남는다**(2절). 인자 개수에도 안 센다.
- ★★★ **검사 지점은 대입이 아니라 호출식**이다 — 19행은 조용하고 20행이 `TS2684` 다(1절).
- ★★ **점 왼쪽이 없는 호출은 `this` 가 `void`** 로 읽힌다 — 그래서 문구가 「of type 'void'」다.
- ★★ **`this: void` 는 「`this` 를 쓰지 마라」** 이고, `this` 를 안 적은 함수는 그 자리에 **맞는다**(4절 8·22행).
- ★★★ **화살표 함수에는 `this` 매개변수를 못 단다** — `TS2730`(4절 26행).
- ★★ **`strictBindCallApply` 가 `call`·`apply`·`bind` 를 검사한다** — 끄면 **6건이 0건**이 된다(3절).
- ★★ 그 플래그는 **`this` 전용이 아니다** — `this` 매개변수가 없는 함수의 **인자도** 검사한다(3절 24·25행).
- ★ **`ThisParameterType` 은 `this` 가 없으면 `unknown`** 이다(5절 24행). `void` 가 아니다.
- ★ **`bind` 의 결과 타입 = `OmitThisParameter`** 다(5절 25·26행).
- ★★ **`.d.ts` 에는 `this` 칸이 남는다**(6절) — 소비자도 그 제약을 본다.

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 떼어낸 메서드를 호출        ->  TS2684  The 'this' context of type 'void' is not assignable to
                                           method's 'this' of type 'Rect'.
2) this 가 필요한 함수를        ->  TS2345  Argument of type '(this: Tick, n: number) => void' is not
   this: void 콜백 자리에                   assignable to parameter of type '(this: void, n: number) => void'.
3) 화살표에 this 매개변수      ->  TS2730  An arrow function cannot have a 'this' parameter.
4) call 에 안 맞는 this        ->  TS2741  Property 'h' is missing in type '{ w: number; }' but
   (strictBindCallApply 켠 판)             required in type 'Rect'.
```

## 어디서 틀리나

- ★★★ 「**`this` 매개변수를 적으면 인자가 하나 늘겠지**」 — 안 는다. 방출물에 **아예 없다**(2절).
- ★★★ 「**떼어내 담는 순간 막히겠지**」 — 대입은 **조용하다.** 막히는 것은 **호출**이다(1절 19·20행).
- ★★ 「**`this: void` 면 `this` 를 안 적은 함수는 못 넣겠지**」 — **넣을 수 있다**(4절 8·22행).
- ★★ 「**화살표에도 `this: T` 를 달면 되겠지**」 — `TS2730` 이다(4절 26행).
- ★★ 「**`call` 검사는 `this` 만 보겠지**」 — **나머지 인자도 본다**(3절 16행). `this` 가 없는 함수도 검사한다(24·25행).
- ★★ 「**`apply` 와 `call` 은 같은 코드가 나오겠지**」 — `TS2322` 대 `TS2345` 로 **다르다**(3절 16·18행).
- ★★ 「**`ThisParameterType` 은 없으면 `void` 를 주겠지**」 — **`unknown`** 이다(5절 24행).
- ★ 「**타입을 달았으니 런타임도 안전하겠지**」 — `as` 하나로 뚫리고 **`TypeError`** 가 난다(2절 세 번째 줄).
- ★ 「**`.d.ts` 에서도 사라지겠지**」 — **남는다**(6절). 사라지는 것은 `.js` 다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `this` 매개변수는 **첫 칸 전용**이고 **인자가 아니다** | 2절 방출 전문 |
| **언어 보장** | 점 왼쪽이 없는 호출은 **`TS2684`** | 1절 20행 · 4절 36행 |
| **언어 보장** | 화살표에는 **못 단다**(`TS2730`) | 4절 26행 |
| **언어 보장** | `this: void` 콜백에 `this` 가 필요한 함수를 못 넣는다 | 4절 12·19행 |
| **★ 설정에 달림** | ★★★ `call`·`apply`·`bind` **인자 검사** | 3절 — 켠 판 **6건** · 끈 판 **0건** |
| **`.d.ts` 방출** | `this` 칸이 **남는다** · 별칭을 **정규화하지 않는다** | 6절 전문 |
| **방출된 JS** | ★★★ `this` 칸이 **한 글자도 안 남는다** | 2절 방출 전문 |
| **런타임(JS 규칙)** | 떼어내 부르면 `this` 는 **`undefined`**(엄격 모드) | 2절 실행 출력 3번 줄 |
| **이 판(7.0.2)의 관찰** | 진단 **문구** 전문 | 코드(`TS2684`·`TS2730`·`TS2345`·`TS2741`)가 더 오래 간다 |
| **이 판의 관찰** | `bind` 가 `TS2769`(오버로드)로 보고되는 것 | 3절 19행 |
| **이 판의 관찰** | `.d.ts` 의 들여쓰기 4칸과 줄 순서 | 방출기의 형식이다 |
| **이 판(node 18)의 관찰** | 예외 **메시지 본문** | 안 실었다 — `constructor.name` 만 찍었다 |
| **안 잰 것** | `this` 매개변수가 검사 시간에 주는 영향 | 재지 않았다 |

★★★ 「**진단 0줄」이 결론인 블록이 둘**이다(2절의 `tsc` · 3절의 끈 판). 둘 다 **명령과 종료 코드까지** 캡처했다.

## 언제 쓰고 언제 안 쓰나

| `this` 매개변수를 쓴다 | 안 쓴다 |
|---|---|
| 메서드를 **떼어 쓸 위험**이 있는 API | 화살표로만 쓰는 콜백 — 애초에 `this` 가 없다 |
| 콜백 계약에 **`this` 를 금지**하고 싶을 때(`this: void`) | 클래스 안에서만 도는 private 도우미 |
| jQuery·이벤트 핸들러처럼 **호출자가 `this` 를 주는** API 를 타이핑할 때 | `bind` 로 이미 고정한 함수 |
| `.d.ts` 로 내보내 **소비자에게 제약을 알릴** 때 | `this` 를 안 쓰는 순수 함수 |
| `OmitThisParameter` 로 **감싸는 도우미**를 만들 때 | 런타임 보호가 필요할 때 — **타입은 못 막는다**(2절) |

## 핵심 문장

1. **`this` 매개변수는 컴파일 타임에만 있다** — 방출된 `.js` 에 한 글자도 안 남는다.
2. **검사 지점은 호출식이다** — 떼어내 담는 것은 조용하고, 부르는 자리가 `TS2684` 다.
3. **JS 의 네 규칙은 하나도 안 바뀐다** — TS 는 그 규칙을 어기는 호출을 **미리** 잡을 뿐이다.
4. **`this: void` 는 금지 계약이고, 화살표에는 아예 못 단다**(`TS2730`).
5. **`strictBindCallApply` 가 `call`·`apply`·`bind` 를 검사한다** — 끄면 6건이 0건이 된다.
6. **`.d.ts` 에는 남고 `.js` 에는 없다** — 두 방출물이 정반대 답을 준다.

## 관련 자료

- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **07번** — [`this` 바인딩 네 규칙](../../../js/syntax/07-this-binding-four-rules/). **`this` 의 런타임 규칙은 전부 그쪽이 정본**이다. 여기는 **그 규칙에 타입을 거는 것**까지다.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **09번**(`call`·`apply`·`bind`) — 세 메서드의 **런타임 의미**는 그쪽. 여기는 **그 셋의 타입 검사**(3절)까지다.
- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) — `this` 칸은 그 표기의 **첫 칸**이다. `bind` 가 `TS2769` 로 보고되는 이유도 그쪽.
- [**17번 주제** — 변성과 매개변수 양립성](../17-variance-and-parameter-compatibility/) — 4절의 「`this` types … incompatible」는 그쪽 규칙이 `this` 칸에 적용된 것이다.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 2절의 「방출에 안 남는다」는 그쪽 규칙이다.
- [**19번 주제** — 제네릭 기본](../19-generics-basics/) — **같은 배치의 다음 주제.** 「런타임에 없는 것」이라는 축을 그대로 잇는다.
- 목록의 **30번 주제**(타입 단언과 non-null `!`) — 2절이 `as unknown as` 로 타입을 벗긴 자리.
- 목록의 **39번 주제**(`strict` 묶음) — `strictBindCallApply` 를 단계적으로 켜는 순서는 그쪽.
- 목록의 **32번 주제**(클래스의 타입 측면) — 4절의 클래스 메서드 `this: Counter` 는 그쪽에서 더 본다.

## 용어 풀이

> **`this` 매개변수(`this` parameter)** — 매개변수 목록의 **첫 자리**에만 올 수 있는 타입 전용 칸.\
> 예: `function f(this: Rect, n: number)`. **인자가 아니다** — 방출물에 안 남는다.

> **`TS2684`** — 「The 'this' context of type 'X' is not assignable to method's 'this' of type 'Y'.」\
> 점 왼쪽이 맞지 않는 호출. **점 왼쪽이 아예 없으면 `X` 가 `void`** 로 나온다.

> **`this: void`** — 「이 함수 안에서 `this` 를 쓰지 마라」는 계약.\
> `this` 를 **안 적은** 함수는 이 자리에 **맞는다**(실측 4절).

> **`strictBindCallApply`** — `strict` 에 딸려 켜지는 플래그(TS 3.2).\
> `call`·`apply`·`bind` 의 **`this` 와 나머지 인자 전부**를 검사하게 만든다.

> **`ThisParameterType<T>` · `OmitThisParameter<T>`** — `this` 칸을 **뽑는** 유틸리티와 **지우는** 유틸리티(TS 3.3).\
> 앞엣것은 `this` 가 없으면 **`unknown`** 을 준다.

## 더 들어가면

- **왜 첫 칸인가** — 매개변수 목록 안에 두면 **문법을 새로 만들지 않아도 된다.** `this` 는 JS 에서 **매개변수 이름으로 쓸 수 없는 예약어**이므로 첫 칸의 `this: T` 는 기존 JS 와 충돌하지 않는다. 그래서 파서를 안 고치고 타입만 얹을 수 있었다 — TS 설계의 전형이다([**01번 주제**](../01-what-ts-adds-and-erases/)).
- **왜 대입은 안 막나** — `const f = rect.area;` 자체는 **합법적인 JS** 이고, 그 뒤에 `f.call(rect)` 로 제대로 부를 수도 있다. 대입을 막으면 그런 쓰임이 통째로 죽는다. 그래서 TS 는 **가장 늦은 시점(호출)** 에만 막는다 — 대신 **떼어내 어딘가에 넘기는 코드는 못 잡는다**(넘긴 곳에서 부르면 그때 잡는다).
- **`this: void` 가 「없음」이 아닌 이유** — 함수 타입의 `this` 칸은 **매개변수처럼 반공변**이다([**17번 주제**](../17-variance-and-parameter-compatibility/)). `this` 를 안 적은 함수는 「아무 `this` 나 받는다」에 가까워서 `void` 자리에 **들어갈 수 있다.** 반대로 `this: Tick` 은 더 좁은 요구라 못 들어간다 — 4절의 연쇄 설명 줄이 그 방향을 그대로 적어 준다.
- **`this` 타입(`this` type)은 다른 것이다** — 클래스 안에서 반환 타입으로 쓰는 `: this`(다형 `this` 타입)는 **이 주제가 아니다.** 이 배치에서는 **안 던졌다.** 목록의 **32번 주제**에서 볼 자리다.
- **오버로드와 `this`** — 오버로드마다 `this` 칸을 다르게 적을 수 있는지, `ThisParameterType` 이 어느 시그니처를 잡는지는 **안 던졌다.** [**16번 주제**](../16-function-types-and-overloads/)와 함께 다시 볼 자리다.
