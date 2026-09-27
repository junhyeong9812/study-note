# ts/syntax/18 — `this` 매개변수 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·`.d.ts` 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 2번의 `tsc` 와 3번의 끈 판은 **진단이 0줄인 것이 결론**이다. 그 블록도 **명령과 종료 코드까지** 캡처했다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **4건** — 막히는 것은 **대입이 아니라 호출**이다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 17 | `rect.area()` | `number` — 정상 호출은 통과한다 |
| 19 | ★★★ `const detached = rect.area;` | **진단 없음** — 대입은 조용하다 |
| 20 | ★★★ `detached();` | **`TS2684`** — 「The 'this' context of type 'void' …」 |
| 25 | 탐침 — `areaOf` 자체 | `(this: Rect, scale: number) => number` |
| 26 | 탐침 — `rect.area` 자체 | `(this: Rect) => number` |

- ★★★ 19행에 진단이 **없다**는 것이 이 문항의 전부다. `const detached = rect.area;` 는 **합법적인 JS** 이고,\
  그 뒤에 `detached.call(rect)` 로 제대로 부를 수도 있다. 그래서 TS 는 **가장 늦은 시점(호출)** 에만 막는다.
- ★★ 20행의 문구가 「of type **'void'**」다. **점 왼쪽이 아예 없는 호출**을 컴파일러가 `void` 로 읽은 것이다.
- ★★★ 25·26행의 탐침이 보여 주듯 **타입 층에서는 `this` 가 매개변수 목록 안에 그대로 보인다.**\
  그런데 **인자 개수에는 안 센다** — 그 증거는 2번의 방출물이다.
- ★ 이 자리가 [JS 갈래의 `this` 바인딩 네 규칙](../../../js/syntax/07-this-binding-four-rules/)이 「런타임에 `undefined`」로 보여 준 그 자리다.\
  **JS 는 터질 때까지 모르고, TS 는 부르기 전에 안다.**

### 2. ★★★ 진단 **0줄 · exit 0** — 방출물에 `this` 칸이 **없다**

**출력**

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

**왜 그런가**

- ★★★ `tsc` 종료 코드가 **`0`** 이고 진단이 **0줄**이다. 이 파일에는 타입 오류가 하나도 없다.
- ★★★ 방출된 `.js` 의 첫 줄이 `function area(scale) { … }` 다 — **매개변수가 하나**다.\
  `this: Rect` 는 **한 글자도 남지 않았다.** 이것이 18 의 본체다.
- ★★ 몸통의 `this.w` 는 **아무 선언에도 안 묶인 채** 그대로 남는다. 그냥 JS 의 `this` 다.
- 실행 출력 네 줄의 대응은 이렇다.

| 줄 | 호출식 | 값 | JS 의 어느 규칙인가 |
|---|---|---|---|
| 1 | `area.call(rect, 2)` | `24` | **명시적** 바인딩 |
| 2 | `holder.area(1)` | `30` | **암시적** 바인딩 — `5 × 6 × 1` |
| 3 | ★★★ 떼어내 호출 | `TypeError` | **기본** 바인딩 — 엄격 모드라 `this` 가 `undefined` |
| 4 | `area.bind(rect)` 뒤 | `120` | **`bind`** — `3 × 4 × 10` |

- ★★★ 세 번째 줄이 결정적이다. `as unknown as` 로 **타입만 벗겨** 부르니 `TypeError` 다.\
  방출물이 `"use strict"` 라 `this` 가 `undefined` 이고 `undefined.w` 를 읽다 터졌다.\
  **`this` 매개변수는 런타임 보호를 하나도 안 한다** — 컴파일 타임에만 있는 것이다.
- ★ 예외의 **메시지 본문은 안 실었다**(판마다 바뀐다). `constructor.name` 만 찍어 **흔들리지 않는 칸**으로 만들었다.

### 3. ★★ **`strictBindCallApply`** — 켠 판 **6건**, 끈 판 **0건**

**출력**

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

**왜 그런가**

| 줄 | 자리 | 코드 |
|---|---|---|
| 15 | `area.call(notRect, 2)` | `TS2741` — `this` 인자가 `Rect` 를 못 채운다 |
| 16 | `area.call(rect, "두 배")` | ★★ `TS2345` — **나머지 인자도 검사한다** |
| 18 | `area.apply(rect, ["두 배"])` | ★★ `TS2322` — 배열 원소라 **코드가 다르다** |
| 19 | `area.bind(notRect)` | `TS2769` — `bind` 가 **오버로드**라서 |
| 24·25 | ★★★ `plain.call/apply` | `TS2345`·`TS2322` — **`this` 매개변수가 없는 함수인데도** 걸린다 |

- ★★★ 끈 판은 **진단이 0줄**이고 종료 코드가 **`0`** 이다. **한 파일의 진단이 통째로 사라진다.**\
  이 주제에서 설정이 답을 바꾸는 **유일한 칸**이다.
- ★★★ 24·25행이 이 문항의 핵심이다. `strictBindCallApply` 는 **`this` 전용 플래그가 아니다** —\
  `call`·`apply`·`bind` 의 **인자 전체**를 검사하게 만드는 플래그다. 끄면 그 셋이 `any` 를 받는 옛 시그니처로 돌아간다.
- ★★ 16행과 18행의 코드가 다른 이유는 **인자를 주는 꼴**이 달라서다. `call` 은 인자를 **나열**하므로 `TS2345`(인자 불일치),\
  `apply` 는 **배열로 묶어** 주므로 배열 원소의 대입 검사(`TS2322`)가 된다.
- ★ 19행이 `TS2769` 인 것은 `bind` 의 선언이 **오버로드 묶음**이기 때문이다([**16번 주제**](../16-function-types-and-overloads/)).

### 4. ★★★ 진단 **4건** — `this: void` 는 「금지」이지 「없음」이 아니다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 8 | ★★ `this` 를 **안 적은** 익명 함수 | **통과** |
| 12 | `this: Tick` 인 익명 함수 | `TS2345` — 「The 'this' types … incompatible」 |
| 19 | `this: Tick` 인 이름 있는 함수 | `TS2345` — 같은 연쇄 |
| 22 | ★★ `this: void` 인 함수 | **통과** |
| 26 | ★★★ 화살표에 `this` 매개변수 | **`TS2730`** |
| 36 | 떼어낸 클래스 메서드 호출 | `TS2684` — 1번 20행과 같은 코드 |

- ★★★ 8행과 22행이 **둘 다 통과**한다는 것이 이 문항의 값이다.\
  `this: void` 는 「`this` 칸이 **없어야** 한다」가 아니라 「**`void` 로 받아라**」이고,\
  `this` 를 안 적은 함수는 **아무 `this` 나 받는 꼴**이라 그 자리에 들어간다.
- ★★ 반대로 `this: Tick` 은 **더 좁은 요구**라 못 들어간다. 연쇄 설명 줄이 그 방향을 그대로 적는다 —\
  「Type 'void' is not assignable to type 'Tick'.」 **`this` 칸은 매개변수처럼 반공변**이다([**17번 주제**](../17-variance-and-parameter-compatibility/)).
- ★★★ 26행 `TS2730` — 화살표 함수는 **자기 `this` 를 아예 안 만든다.** 적을 칸 자체가 없다.
- ★ 36행은 1번과 같은 사건이다 — 클래스 메서드에 `this: Counter` 를 달면 **떼어낸 호출이 막힌다.**

### 5. ★★ `Rect` · **`unknown`** · `(scale: number) => number`

**출력**

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

**왜 그런가**

| 줄 | 탐침 | 답 |
|---|---|---|
| 23 | `ThisParameterType<typeof area>` | **`Rect`** |
| 24 | ★★★ `ThisParameterType<typeof plain>` | **`unknown`** — `void` 가 아니다 |
| 25 | `OmitThisParameter<typeof area>` | `(scale: number) => number` |
| 26 | ★★ `area.bind({ w: 3, h: 4 })` | `(scale: number) => number` — **25행과 같은 글자** |

- ★★★ 24행이 던져 보기 전에는 못 맞히는 자리다. `this` 매개변수가 **없는** 함수에 `ThisParameterType` 을 씌우면 **`unknown`** 이 나온다.\
  「`this` 가 없다」를 `void` 로 답할 것 같지만 아니다.
- ★★ 25행과 26행의 글자가 같다는 것은 **`bind` 의 결과 타입이 곧 `OmitThisParameter`** 라는 뜻이다.\
  그래서 `this` 가 걸린 함수를 감싸는 도우미를 쓸 때 이 둘을 바꿔 쓸 수 있다.
- ★ 오버로드된 함수에 씌우면 어느 시그니처가 잡히는지는 **안 던졌다.**

### 6. ★★★ `.d.ts` 에는 **남고** `.js` 에는 **없다** — 같은 소스, 반대 답

**출력**

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

**왜 그런가**

| 방출물 | `area` 가 어떻게 적히나 |
|---|---|
| `.d.ts` | `export declare function area(this: Rect, scale: number): number;` — ★ **`this` 칸이 그대로** |
| `.js` | `export function area(scale) { … }` — ★★★ **`this` 칸이 없다** |

- ★★★ **같은 소스 하나에서 두 방출물이 나오는데 답이 정반대다.** `.d.ts` 는 **타입 층의 사본**이고 `.js` 는 **값 층의 사본**이다.
- ★★ `interface Handler` 의 `onTick(this: void, n: number): void;` 와 객체 리터럴 메서드의 `read(this: { v: number })` 도\
  `.d.ts` 에 **적은 그대로** 실리고 `.js` 에서는 사라진다.
- ★★★ 그런데 `.d.ts` 는 **계산하지 않는다.** `rectOnly` 가 `ThisParameterType<typeof area>` 라고 **적은 그대로** 남았다 —\
  5번의 탐침은 같은 것을 **`Rect`** 라고 답했다. **둘이 다르면 탐침 쪽이 계산된 것**이다.
- ★ `bound` 만 계산돼 있다 — `(scale: number) => number`. **이름이 안 붙은 자리는 펴서 적는다.**
- ★★ 그래서 이 배치의 판정은 「**추론 결과를 볼 때는 탐침, 여러 줄을 한 번에 훑을 때는 `.d.ts`**」다.

### 7. ★★ 대입은 **합법적인 JS** 이기 때문이다

**왜 그런가**

- `const detached = rect.area;` 자체는 아무 잘못이 없다. 그 뒤에 `detached.call(rect)` 로 제대로 부를 수 있다.
- ★★ 대입을 막으면 그런 쓰임이 통째로 죽는다. 그래서 TS 는 **가장 늦은 시점인 호출식**에서만 막는다.
- ★ 대가가 있다 — **떼어내 어딘가에 넘기는 코드는 못 잡는다.** 넘긴 곳에서 부를 때 비로소 잡힌다.

### 8. ★★★ 화살표 함수는 **자기 `this` 를 안 만들기** 때문이다

**왜 그런가**

- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **07번**이 그 예외를 정본으로 다룬다 —\
  네 규칙 중 **화살표만** 호출식을 안 보고 **바깥의 `this` 를 그대로 쓴다.**
- ★★ 그러므로 화살표에 `this: T` 를 다는 것은 **채워질 일이 없는 칸을 여는 것**이다. `TS2730` 이 그것을 막는다.
- ★ 반대로 **화살표는 `this: void` 자리에 잘 맞는다** — 자기 `this` 가 없으니 계약을 어길 수 없다.

### 9. ★★ 「**떼어 쓸 위험이 있는가**」로 가른다

**왜 그런가**

| `this` 매개변수를 쓴다 | 안 쓴다 |
|---|---|
| 메서드를 떼어 쓸 위험이 있는 공개 API | 화살표로만 쓰는 콜백 |
| 콜백에 **`this` 금지**를 박을 때(`this: void`) | 클래스 안에서만 도는 도우미 |
| 호출자가 `this` 를 주는 API(이벤트 핸들러 등)를 타이핑할 때 | 이미 `bind` 한 함수 |
| `.d.ts` 로 **제약을 내보낼** 때 | `this` 를 안 쓰는 순수 함수 |

- ★ **런타임 보호가 필요하면 이 도구가 아니다**(2번). 그때는 생성자에서 `bind` 하거나 클래스 필드 화살표를 쓴다.

### 10. ★★ `this` 뿐이 아니다 — **인자 전체**다

**왜 그런가**

- 3번 24·25행이 근거다. `plain(x: number)` 에는 `this` 매개변수가 **없는데도** `plain.call(undefined, "문자열")` 이 걸린다.
- ★★ 끄면 **6건이 0건**이 된다 — `call`·`apply`·`bind` 가 인자를 **하나도** 안 본다.
- ★ 기존 코드베이스에 켤 때 **`call`·`apply` 자리가 대량으로 빨개지는** 플래그다. 순서는 [목록의 **39번 주제**](../39-strict-bundle/).

### 11. ★★★ 네 줄이 네 규칙과 **1:1** 이다

**왜 그런가**

| 실행 출력 | 호출식 | JS 의 규칙 |
|---|---|---|
| `24` | `area.call(rect, 2)` | **명시적** |
| `30` | `holder.area(1)` | **암시적** |
| `TypeError` | 떼어내 호출 | **기본**(엄격 모드 → `undefined`) |
| `120` | `bound(10)` | **`bind`** |

- ★★★ 네 값이 전부 **JS 규칙 그대로**다. TS 는 그중 **세 번째를 컴파일에서 미리 막을 뿐**이고,\
  `as` 로 타입을 벗기면 그 보호가 사라진다.
- ★★ 그러므로 18 을 한 줄로 줄이면 「**규칙은 JS 가 정하고, TS 는 그 규칙을 어기는 호출을 먼저 잡는다**」다.

### 12. ★★ 세 층

**왜 그런가**

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `this` 매개변수는 **인자가 아니다** · 검사 지점은 **호출식** · 화살표에는 **못 단다**(`TS2730`) · `this: void` 계약 · `.d.ts` 에는 **남는다** |
| **설정에 달린 것** | ★★★ `strictBindCallApply` — 켠 판 **6건** · 끈 판 **0건**(3번). `strict` 에 딸려 켜진다 |
| **이 판(7.0.2)의 관찰** | 진단 **문구** 전문 — 코드가 더 오래 간다 · `bind` 가 **`TS2769`** 로 보고되는 것 · `apply` 가 **`TS2322`** 인 것 · `.d.ts` 의 들여쓰기 4칸 · `ThisParameterType` 이 **`unknown`** 을 주는 것 |
| **런타임(JS·node 18)의 사실** | 떼어내 부르면 `this` 가 **`undefined`** · 예외 **메시지 본문**은 판에 매여 안 실었다 |

- ★★★ 「**진단 0줄」이 결론인 블록이 둘**이다(2번의 `tsc` · 3번의 끈 판). 둘 다 **명령과 종료 코드까지** 캡처했다.
- ★★ 이 주제의 창 넷이 **같은 사실을 네 방향에서** 말한다 — 진단·탐침·`.d.ts`·방출 `.js`.\
  그중 **`.js` 만이 「런타임에 없다」를 증명**한다. 나머지 셋은 전부 타입 층의 이야기다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 떼어낸 호출 | `--noEmit ex.18a.ts` | exit 1 · **4건** · ★ 19행 **없음** · 20행 `TS2684` |
| 방출과 실행 | `tsc --outDir ex.18b.ts` + `node` | ★ **tsc exit 0 · 진단 0줄** · `.js` 의 `area` 가 **매개변수 1개** · node exit 0 |
| `strictBindCallApply` 켠 판 | `--noEmit ex.18c.ts` | exit 1 · **6건** · `TS2741`·`TS2345`·`TS2322`·`TS2769` |
| 끈 판 | `--strictBindCallApply false ex.18c.ts` | ★★ **exit 0 · 진단 0줄** |
| `this: void` 와 화살표 | `--noEmit ex.18d.ts` | exit 1 · **4건** · 8·22행 **통과** · 26행 `TS2730` |
| 유틸리티 둘 | `--noEmit ex.18e.ts` | exit 1 · **4건** · ★ `ThisParameterType<typeof plain>` = **`unknown`** |
| 두 방출물 | `--declaration --outDir ex.18f.ts` | ★ **exit 0** · `.d.ts` 에 `this` **있음** · `.js` 에 **없음** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ 진단 **문구** 전문 — `TS2684`·`TS2730`·`TS2345`·`TS2741`·`TS2769`·`TS2322` 라는 **코드**가 더 오래 간다.
- ★★ `bind` 가 `TS2769`(오버로드)로, `apply` 가 `TS2322` 로 보고되는 **분류 방식**.
- ★★ `ThisParameterType<typeof plain>` 이 **`unknown`** 인 것 — `lib` 의 정의에 달렸다.
- `.d.ts` 의 들여쓰기 4칸·줄 순서 — 방출기의 형식이다.
- `node` 예외의 **메시지 본문** — 안 실었다. `constructor.name` 만 찍었다.

**안 돌려 본 것**

- **다형 `this` 타입**(`: this` 반환) — **안 던졌다.** [목록의 **32번 주제**](../32-class-type-aspects/).
- **오버로드에 `this` 칸을 다는 것** · `ThisParameterType` 이 어느 시그니처를 잡는지 — **안 던졌다.**
- **`noImplicitThis`** 단독으로 끈 판 — **안 던졌다.** 이 배치는 `--strict` 묶음으로만 던졌다.
- **`this` 매개변수가 검사 시간에 주는 영향** — **재지 않았고 수치를 적지 않았다.**
