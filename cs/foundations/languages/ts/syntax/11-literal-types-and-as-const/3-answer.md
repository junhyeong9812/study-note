# ts/syntax/11 — 리터럴 타입과 `as const` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★ 이 주제에도 「**진단 목록에 없는 줄**」이 근거인 자리가 있다 — 3번의 11\~16행이 통째로 그렇다.\
> 그래서 **모든 진단 블록 옆에 소스 전문**을 뒀다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.** 템플릿 리터럴 타입은 백틱을 포함하므로 **겹백틱**으로 적었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **14건** — 넓어지는 자리가 **다섯 곳**이다

**출력**

```ts
// ex.11a.ts
// 리터럴 추론이 어디서 넓어지나 — 자리마다 컴파일러에게 캐묻는다
const cStr = "circle";
let lStr = "circle";
const cNum = 1;
let lNum = 1;
const cBool = true;
var vStr = "circle";

const obj = { a: 1, s: "circle", b: true };
const arr = [1, 2, 3];
const mixed = ["a", 1];

const annotated: "circle" = "circle";
let lAnnotated: "circle" = "circle";
const fromCall = String("circle");

const p1: null = cStr;
const p2: null = lStr;
const p3: null = cNum;
const p4: null = lNum;
const p5: null = cBool;
const p6: null = vStr;
const p7: null = obj;
const p8: null = obj.a;
const p9: null = arr;
const p10: null = mixed;
const p11: null = annotated;
const p12: null = lAnnotated;
const p13: null = fromCall;

lAnnotated = "square";
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13);
```

```text
===== tsc --pretty false --noEmit ex.11a.ts (tsc exit=1) =====
ex.11a.ts(17,7): error TS2322: Type '"circle"' is not assignable to type 'null'.
ex.11a.ts(18,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.11a.ts(19,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.11a.ts(20,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.11a.ts(21,7): error TS2322: Type 'true' is not assignable to type 'null'.
ex.11a.ts(22,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.11a.ts(23,7): error TS2322: Type '{ a: number; s: string; b: boolean; }' is not assignable to type 'null'.
ex.11a.ts(24,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.11a.ts(25,7): error TS2322: Type 'number[]' is not assignable to type 'null'.
ex.11a.ts(26,7): error TS2322: Type '(string | number)[]' is not assignable to type 'null'.
ex.11a.ts(27,7): error TS2322: Type '"circle"' is not assignable to type 'null'.
ex.11a.ts(28,7): error TS2322: Type '"circle"' is not assignable to type 'null'.
ex.11a.ts(29,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.11a.ts(31,1): error TS2322: Type '"square"' is not assignable to type '"circle"'.
```

**왜 그런가**

| 적은 것 | 탐침이 답한 것 | 넓어졌나 |
|---|---|---|
| `const cStr = "circle"` | **`"circle"`** | 아니다 |
| `let lStr = "circle"` | **`string`** | ★ **넓어졌다** |
| `const cNum = 1` | **`1`** | 아니다 |
| `let lNum = 1` | **`number`** | ★ **넓어졌다** |
| `const cBool = true` | **`true`** | 아니다 |
| `var vStr = "circle"` | **`string`** | ★ **넓어졌다** |
| `const obj = { a: 1, s: "circle", b: true }` | **`{ a: number; s: string; b: boolean; }`** | ★★★ **프로퍼티가 넓어졌다** |
| `obj.a` | **`number`** | ★ 〃 |
| `const arr = [1, 2, 3]` | **`number[]`** | ★ **요소가 넓어졌다** |
| `const mixed = ["a", 1]` | **`(string \| number)[]`** | ★ 〃 + 유니온이 생겼다 |
| `const annotated: "circle"` | **`"circle"`** | 주석이 막았다 |
| `let lAnnotated: "circle"` | **`"circle"`** | ★ 주석이 있으면 `let` 도 안 넓어진다 |
| `const fromCall = String("circle")` | **`string`** | 함수 반환은 리터럴이 아니다 |

- ★★★ **넓어지는 자리는 다섯이다** — `let` · `var` · **객체 프로퍼티** · **배열 요소** · **함수 반환**.\
  `const` 가 막아 주는 것은 **그 변수 자신 하나뿐**이다.
- ★★★ 가장 자주 걸리는 것이 `const obj = { a: 1 }` 이다. 「`const` 로 선언했으니 안도 고정」은 틀린 믿음이다.
- ★ 31행 `lAnnotated = "square"` 가 `TS2322` 인 것이 12번째 줄의 답을 못 박는다 — 타입이 정말 `"circle"` 로 남았다.
- ★ 이유는 7번에서 — **넓히기는 재대입 가능성의 그림자**다.

### 2. ★★★ 진단 **15건** — `as const` 는 **세 가지**를 한꺼번에 한다

**출력**

```ts
// ex.11b.ts
// as const 가 바꾸는 것 셋 — 리터럴 고정·readonly·배열을 튜플로
const plain = { mode: "dark", retries: 3, deep: { x: 1 }, list: [1, 2] };
const frozen = { mode: "dark", retries: 3, deep: { x: 1 }, list: [1, 2] } as const;

const p1: null = plain;
const p2: null = frozen;
const p3: null = frozen.deep;
const p4: null = frozen.list;

const plainArr = [1, 2, 3];
const frozenArr = [1, 2, 3] as const;
const p5: null = plainArr;
const p6: null = frozenArr;

let lFrozen = "circle" as const;
const p7: null = lFrozen;

declare const n: number;
const partial = { a: n } as const;
const partialArr = [n] as const;
const p8: null = partial;
const p9: null = partialArr;

frozen.retries = 4;
frozenArr[0] = 9;
frozenArr.push(4);
lFrozen = "square";

const copied = [...frozenArr];
const p10: null = copied;
const spread = { ...frozen };
const p11: null = spread.mode;
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11);
```

```text
===== tsc --pretty false --noEmit ex.11b.ts (tsc exit=1) =====
ex.11b.ts(5,7): error TS2322: Type '{ mode: string; retries: number; deep: { x: number; }; list: number[]; }' is not assignable to type 'null'.
ex.11b.ts(6,7): error TS2322: Type '{ readonly mode: "dark"; readonly retries: 3; readonly deep: { readonly x: 1; }; readonly list: readonly [1, 2]; }' is not assignable to type 'null'.
ex.11b.ts(7,7): error TS2322: Type '{ readonly x: 1; }' is not assignable to type 'null'.
ex.11b.ts(8,7): error TS2322: Type 'readonly [1, 2]' is not assignable to type 'null'.
ex.11b.ts(12,7): error TS2322: Type 'number[]' is not assignable to type 'null'.
ex.11b.ts(13,7): error TS2322: Type 'readonly [1, 2, 3]' is not assignable to type 'null'.
ex.11b.ts(16,7): error TS2322: Type '"circle"' is not assignable to type 'null'.
ex.11b.ts(21,7): error TS2322: Type '{ readonly a: number; }' is not assignable to type 'null'.
ex.11b.ts(22,7): error TS2322: Type 'readonly [number]' is not assignable to type 'null'.
ex.11b.ts(24,8): error TS2540: Cannot assign to 'retries' because it is a read-only property.
ex.11b.ts(25,11): error TS2540: Cannot assign to '0' because it is a read-only property.
ex.11b.ts(26,11): error TS2339: Property 'push' does not exist on type 'readonly [1, 2, 3]'.
ex.11b.ts(27,1): error TS2322: Type '"square"' is not assignable to type '"circle"'.
ex.11b.ts(30,7): error TS2322: Type '(1 | 2 | 3)[]' is not assignable to type 'null'.
ex.11b.ts(32,7): error TS2322: Type '"dark"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 적은 것 | 답한 것 |
|---|---|---|
| 5 | `plain`(그냥 리터럴) | `{ mode: string; retries: number; deep: { x: number; }; list: number[]; }` |
| 6 | `frozen`(`as const`) | ★★★ `{ readonly mode: "dark"; readonly retries: 3; readonly deep: { readonly x: 1; }; readonly list: readonly [1, 2]; }` |
| 7 | `frozen.deep` | `{ readonly x: 1; }` — **재귀로 들어간다** |
| 8 | `frozen.list` | `readonly [1, 2]` — **튜플이 됐다** |
| 12·13 | `plainArr` / `frozenArr` | `number[]` / ★ **`readonly [1, 2, 3]`** |
| 16 | `let lFrozen = "circle" as const` | **`"circle"`** — `let` 이어도 안 넓어진다 |
| 21·22 | `{ a: n } as const` / `[n] as const` | ★★ **`{ readonly a: number }`** / **`readonly [number]`** |
| 24 | `frozen.retries = 4` | **TS2540** — read-only property |
| 25 | `frozenArr[0] = 9` | **TS2540** — read-only property `'0'` |
| 26 | `frozenArr.push(4)` | **TS2339** — `push` **가 아예 없다** |
| 27 | `lFrozen = "square"` | **TS2322** — 타입이 `"circle"` 이라 |
| 30 | `[...frozenArr]` | ★★★ **`(1 \| 2 \| 3)[]`** — 튜플도 `readonly` 도 잃었다 |
| 32 | `{ ...frozen }.mode` | ★★ **`"dark"`** — 리터럴은 남고 `readonly` 는 잃었다 |

- ★★★ 6행 한 줄에 **세 가지**가 다 들어 있다 —

| 무엇 | 증거 |
|---|---|
| ① **리터럴 고정** | `mode: "dark"`(`string` 이 아니라) · `retries: 3` |
| ② **`readonly`** | 모든 칸에 `readonly` · 24·25행이 `TS2540` |
| ③ **배열 → 튜플** | `list: readonly [1, 2]`(`number[]` 가 아니라) · 26행이 `TS2339` |

- ★★ 21행이 경계다. **`as const` 가 값을 리터럴로 만들어 주지는 않는다** — `n` 이 `number` 이므로 고정할 리터럴이 없고, `readonly` 만 붙는다.
- ★★★ 30·32행이 실무의 함정이다. **사본은 잃는다.** 「한 번 굳히면 끝」이 아니다.
- ★ 26행의 `TS2339` 가 `TS2540` 이 아닌 것에 주의하라 — `readonly` 튜플에는 **`push` 라는 멤버 자체가 없다.**

### 3. ★★ 진단 **11건** 중 `TS1355` 가 **4건** — **통과한 여섯 줄이 허용 목록의 실증**이다

**출력**

```ts
// ex.11c.ts
// as const 가 안 되는 자리 — 에러 전문이 허용 목록을 통째로 읽어 준다
declare const n: number;
declare const s: string;
let v = 1;

const bad1 = n as const;
const bad2 = (1 + 2) as const;
const bad3 = (() => 1) as const;
const bad4 = v as const;

const ok1 = -1 as const;
const ok2 = `a` as const;
const ok3 = `a${s}` as const;
const ok4 = `a${1}` as const;
const ok5 = { a: n } as const;
const ok6 = [n] as const;

enum E {
    X = 1,
}
const ok7 = E.X as const;

const p1: null = ok1;
const p2: null = ok2;
const p3: null = ok3;
const p4: null = ok4;
const p5: null = ok5;
const p6: null = ok6;
const p7: null = ok7;
console.log(bad1, bad2, bad3, bad4, p1, p2, p3, p4, p5, p6, p7);
```

```text
===== tsc --pretty false --noEmit ex.11c.ts (tsc exit=1) =====
ex.11c.ts(6,14): error TS1355: A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.
ex.11c.ts(7,14): error TS1355: A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.
ex.11c.ts(8,14): error TS1355: A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.
ex.11c.ts(9,14): error TS1355: A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.
ex.11c.ts(23,7): error TS2322: Type '-1' is not assignable to type 'null'.
ex.11c.ts(24,7): error TS2322: Type '"a"' is not assignable to type 'null'.
ex.11c.ts(25,7): error TS2322: Type '`a${string}`' is not assignable to type 'null'.
ex.11c.ts(26,7): error TS2322: Type '"a1"' is not assignable to type 'null'.
ex.11c.ts(27,7): error TS2322: Type '{ readonly a: number; }' is not assignable to type 'null'.
ex.11c.ts(28,7): error TS2322: Type 'readonly [number]' is not assignable to type 'null'.
ex.11c.ts(29,7): error TS2322: Type 'E' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 식 | 결과 | 답한 타입 |
|---|---|---|---|
| 6 | `n as const`(`declare const n: number`) | **TS1355** | — |
| 7 | `(1 + 2) as const` | **TS1355** | — |
| 8 | `(() => 1) as const` | **TS1355** | — |
| 9 | `v as const`(`let v = 1`) | **TS1355** | — |
| 11 | `-1 as const` | ★ **통과** | **`-1`** |
| 12 | `` `a` as const `` | 통과 | **`"a"`** |
| 13 | `` `a${s}` as const `` | ★★★ **통과** | **`` `a${string}` ``** |
| 14 | `` `a${1}` as const `` | 통과 | **`"a1"`** — 컴파일 시각에 이어 붙는다 |
| 15 | `{ a: n } as const` | 통과 | **`{ readonly a: number; }`** |
| 16 | `[n] as const` | 통과 | **`readonly [number]`** |
| 21 | `E.X as const` | 통과 | **`E`** |

- ★★★ **에러 문구가 규칙 자체다** —\
  「A 'const' assertion can only be applied to references to **enum members**, or **string, number, boolean, array, or object literals**.」
- ★★ 가르는 기준은 「**식의 껍데기가 리터럴인가**」다. 안에 무엇이 들어 있는지는 상관없다 —\
  `{ a: n }` 은 통과하고(**객체 리터럴**), `n` 은 막힌다(**참조**).
- ★★ 그래서 **계산된 값을 리터럴로 굳히는 길은 없다.** `(1 + 2)` 도 막힌다 — 답이 `3` 인 것을 알면서도.
- ★★★ 13행이 그 빈자리를 메운다 — 값이 안 정해진 조각은 **템플릿 리터럴 타입**(`` `a${string}` ``)으로 남는다.\
  14행과 대조하면 분명하다. **상수만 들어가면 `"a1"` 로 접히고, 변수가 들어가면 패턴이 된다.**
- ★ 11행 `-1 as const` 가 통과하는 것은 단항 부호가 **숫자 리터럴의 일부**로 취급되기 때문이다.

### 4. ★★ 진단 **8건** — `Handler` 는 **2개**, `Pair` 는 **4개**로 펼쳐진다

**출력**

```ts
// ex.11d.ts
// 템플릿 리터럴 타입 맛보기 — 리터럴 유니온이 곱해진다
type Dir = "up" | "down";
type Handler = `on${Capitalize<Dir>}`;
type CssVar = `--${string}`;
type Pair = `${Dir}-${Dir}`;

declare const h: Handler;
declare const c: CssVar;
declare const pr: Pair;

const p1: null = h;
const p2: null = c;
const p3: null = pr;

const okHandler: Handler = "onUp";
const badHandler: Handler = "onup";
const okCss: CssVar = "--brand";
const badCss: CssVar = "brand";
const okPair: Pair = "up-down";
const badPair: Pair = "up-left";

declare const s: string;
const built = `on${s}` as const;
const p4: null = built;
const putBuilt: CssVar = built;
console.log(p1, p2, p3, p4, okHandler, badHandler, okCss, badCss, okPair, badPair, putBuilt);
```

```text
===== tsc --pretty false --noEmit ex.11d.ts (tsc exit=1) =====
ex.11d.ts(11,7): error TS2322: Type '"onDown" | "onUp"' is not assignable to type 'null'.
  Type '"onDown"' is not assignable to type 'null'.
ex.11d.ts(12,7): error TS2322: Type '`--${string}`' is not assignable to type 'null'.
ex.11d.ts(13,7): error TS2322: Type '"down-down" | "down-up" | "up-down" | "up-up"' is not assignable to type 'null'.
  Type '"down-down"' is not assignable to type 'null'.
ex.11d.ts(16,7): error TS2820: Type '"onup"' is not assignable to type '"onDown" | "onUp"'. Did you mean '"onUp"'?
ex.11d.ts(18,7): error TS2322: Type '"brand"' is not assignable to type '`--${string}`'.
ex.11d.ts(20,7): error TS2322: Type '"up-left"' is not assignable to type '"down-down" | "down-up" | "up-down" | "up-up"'.
ex.11d.ts(24,7): error TS2322: Type '`on${string}`' is not assignable to type 'null'.
ex.11d.ts(25,7): error TS2322: Type '`on${string}`' is not assignable to type '`--${string}`'.
```

**왜 그런가**

| 타입 | 펼쳐진 결과 | 멤버 수 |
|---|---|---|
| `` Handler = `on${Capitalize<Dir>}` `` | **`"onDown" \| "onUp"`** | **2** |
| `` Pair = `${Dir}-${Dir}` `` | **`"down-down" \| "down-up" \| "up-down" \| "up-up"`** | ★ **4**(2 × 2) |
| `` CssVar = `--${string}` `` | **`` `--${string}` ``** — 안 펼쳐진다 | 무한 |

| 줄 | 무엇 | 결과 |
|---|---|---|
| 15 `okHandler: Handler = "onUp"` | 멤버다 | ★ **통과** |
| 16 `badHandler: Handler = "onup"` | 대소문자 틀림 | ★★ **TS2820** — 「Did you mean '"onUp"'?」 |
| 17 `okCss: CssVar = "--brand"` | 패턴에 맞는다 | ★ **통과** |
| 18 `badCss: CssVar = "brand"` | 패턴에 안 맞는다 | **TS2322** |
| 19 `okPair: Pair = "up-down"` | 조합에 있다 | ★ **통과** |
| 20 `badPair: Pair = "up-left"` | 조합에 없다 | **TS2322** |
| 24 `` built = `on${s}` as const `` | 값에서 패턴이 나왔다 | **`` `on${string}` ``** |
| 25 `putBuilt: CssVar = built` | 패턴끼리 대조 | **TS2322** — 통과 **안 한다** |

- ★★ **16행만 코드가 다르다.** `TS2820` 은 **후보를 짚어 주는** 진단이다 — 멤버가 **유한하게 펼쳐져 있어야** 가능하다.\
  18·20행은 `TS2322` 다. `CssVar` 는 무한이라 후보를 못 고른다.
- ★★★ **펼쳐지는 이유**는 리터럴 유니온을 넣었기 때문이다. `string` 을 넣으면 값이 무한하니 **패턴 그대로** 남는다.
- ★★ **조합은 곱해진다.** 조각이 둘이면 2 × 2 = 4, 셋이면 8 — 조각이 늘면 멤버가 폭발한다(목록의 **45번 주제**).
- ★ 25행이 한계를 보여 준다. `` `on${string}` `` 은 `` `--${string}` `` 의 부분집합이 아니므로 막힌다 — **패턴도 타입으로 대조된다.**
- ★ 멤버 순서(`"onDown" | "onUp"`)는 [**09번 주제**](../09-union-types/)와 같은 **이 판의 관찰**이다. 대조 기준으로 쓰지 않는다.

### 5. ★★★ **0글자** — `Object.isFrozen` 이 `false` 이고 `push` 가 그냥 된다

**출력**

```ts
// ex.11e.ts
// as const 는 방출에 한 글자도 안 남는다 — readonly 도 런타임에는 없다
type Dir = "up" | "down";

const dir = "up" as const;
const conf = { mode: "dark", retries: 3 } as const;
const list = [1, 2, 3] as const;

function move(d: Dir): string {
    return `move ${d}`;
}

console.log("move      :", move(dir));
console.log("conf      :", conf.mode, conf.retries);
console.log("list      :", list.length, list[0]);

const escaped = list as unknown as number[];
escaped.push(9);
console.log("push 뒤   :", list.join(","));
console.log("frozen?   :", Object.isFrozen(conf), Object.isFrozen(list));
```

```text
===== tsc --pretty false ex.11e.ts (tsc exit=0) =====
===== 방출된 ex.11e.js =====
"use strict";
const dir = "up";
const conf = { mode: "dark", retries: 3 };
const list = [1, 2, 3];
function move(d) {
    return `move ${d}`;
}
console.log("move      :", move(dir));
console.log("conf      :", conf.mode, conf.retries);
console.log("list      :", list.length, list[0]);
const escaped = list;
escaped.push(9);
console.log("push 뒤   :", list.join(","));
console.log("frozen?   :", Object.isFrozen(conf), Object.isFrozen(list));
```

```text
===== node ex.11e.js (node exit=0) =====
move      : move up
conf      : dark 3
list      : 3 1
push 뒤   : 1,2,3,9
frozen?   : false false
```

**왜 그런가**

| 확인 | 값 |
|---|---|
| 방출된 파일에 `as const` | ★★★ **0번** — `const dir = "up";` 뿐 |
| 방출된 파일에 `type Dir` | **없다** — `"use strict";` 다음이 곧장 `const dir = "up";` |
| `Object.isFrozen(conf)` · `Object.isFrozen(list)` | ★★★ **`false` `false`** — 얼려 주지 않는다 |
| `escaped.push(9)` 뒤 `list.join(",")` | ★★★ **`1,2,3,9`** — 런타임은 막지 않는다 |
| `move(dir)` | `move up` — 리터럴 고정 덕에 `"up" \| "down"` 자리에 들어갔다 |

- ★★★ `as const` 는 **타입 검사기 안에서만 사는 표시**다. `Object.freeze` 를 넣어 주지도, 다른 코드를 만들지도 않는다.
- ★★ `push` 를 부르려면 `as unknown as number[]` 라는 **두 단 단언**을 거쳐야 했다. 단언 없이는 `TS2339` 로 막힌다(2번의 26행).\
  **막는 것은 타입이고, 막지 못하는 것은 런타임이다** — [**07번 주제**](../07-object-type-details/)의 `readonly` 와 같은 경계다.
- ★ 뒤집으면 좋은 소식이다 — `as const` 를 아무리 써도 **번들이 한 글자도 안 커진다.**

### 6. ★★ `.d.ts` 는 **값은 추론 결과로, 타입 별칭은 적은 그대로**

**출력**

```ts
// ex.11f.ts
// 선언 방출은 값 쪽 추론 결과를 적는다 — 여기서는 as const 가 글자로 드러난다
export const cStr = "circle";
export let lStr = "circle";
export const frozen = { mode: "dark", retries: 3 } as const;
export const plain = { mode: "dark", retries: 3 };
export const frozenArr = [1, 2, 3] as const;
export const plainArr = [1, 2, 3];
export type Handler = `on${Capitalize<"up" | "down">}`;
export const picked: "a" | "b" = "a";
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.11f.ts (tsc exit=0) =====
===== 방출된 ex.11f.d.ts =====
export declare const cStr = "circle";
export declare let lStr: string;
export declare const frozen: {
    readonly mode: "dark";
    readonly retries: 3;
};
export declare const plain: {
    mode: string;
    retries: number;
};
export declare const frozenArr: readonly [1, 2, 3];
export declare const plainArr: number[];
export type Handler = `on${Capitalize<"up" | "down">}`;
export declare const picked: "a" | "b";
```

**왜 그런가**

| 선언 | `.d.ts` | 읽는 법 |
|---|---|---|
| `export const cStr = "circle"` | ★ **`= "circle"`** | **`:` 가 아니라 `=`** — 값 하나로 고정됐다 |
| `export let lStr = "circle"` | **`: string`** | 넓어진 결과 |
| `export const frozen = { … } as const` | **`readonly` 포함 전문** | 2번의 탐침과 같다 |
| `export const plain = { … }` | `{ mode: string; retries: number; }` | 1번의 탐침과 같다 |
| `export const frozenArr = [1,2,3] as const` | **`readonly [1, 2, 3]`** | 튜플이 그대로 실린다 |
| `export const plainArr = [1,2,3]` | `number[]` | — |
| `` export type Handler = `on${…}` `` | ★★★ **적은 그대로** | 4번의 탐침은 `"onDown" \| "onUp"` 이었다 |
| `export const picked: "a" \| "b" = "a"` | 그대로 | 주석을 적었으니 보존된다 |

- ★★★ **한 파일 안에서 두 규칙이 같이 돈다** — **값 선언은 추론 결과**를, **타입 별칭은 표기**를 적는다.\
  [**09번 주제**](../09-union-types/)·[**10번 주제**](../10-intersection-types/)에서 본 것과 같은 성질이다.
- ★★ 그래서 `Handler` 만 「계산 전」 모습으로 나온다. **`.d.ts` 를 읽고 「멤버가 둘이구나」를 알 수는 없다.**
- ★ `= "circle"` 과 `: string` 의 차이가 **리터럴 고정의 표시**다. 라이브러리 소비자가 보는 계약이 그만큼 달라진다.

### 7. ★★★ **재대입될 수 있는 자리라서** 넓어진다

**왜 그런가**

- `let lStr = "circle"` 은 「이 변수는 **앞으로 다른 문자열이 들어올 수 있다**」는 선언이다.\
  그러니 추론기는 「이 변수가 **가질 수 있는 값의 집합**」을 적어야 하고, 그것이 `string` 이다.
- `const cStr = "circle"` 은 **그 값 하나로 끝난다.** 집합이 하나라 리터럴 타입으로 남는다.
- ★★ 같은 논리가 **객체 프로퍼티**에도 걸린다 — `const obj = { a: 1 }` 의 `obj.a` 는 `const` 가 아니다. **`obj.a = 2` 가 된다.**\
  그래서 `number` 로 넓어진다. **`as const` 로 `readonly` 를 붙이면 그 가능성이 사라져 리터럴이 남는다.**
- ★★★ 즉 **넓히기와 `readonly` 는 한 뿌리다.** `as const` 가 둘을 동시에 바꾸는 것은 우연이 아니다.
- ★ 반례가 1번의 12번째 줄이다 — `let lAnnotated: "circle"` 은 주석으로 집합을 직접 적었으므로 넓히기가 개입하지 않는다.

### 8. ★★ **리터럴이 아닌 식에는 「굳힐 리터럴」이 없기** 때문이다

**왜 그런가**

- `as const` 가 하는 일은 「이 **리터럴 식**의 추론을 넓히지 마라」다. 리터럴 식이 아니면 **넓히기가 일어나는 지점 자체가 없다.**
- `n as const` 에서 `n` 은 이미 `number` 다. 굳혀도 `number` 다 — **아무 일도 안 하는 단언**이 된다.
- `(1 + 2) as const` 는 답이 `3` 인 것을 사람은 알지만, **`as const` 는 계산기가 아니다.** 추론을 막는 스위치일 뿐이다.
- ★★ 그래서 허용 목록이 **「추론이 넓히는 자리」의 목록과 같다** — 문자열·숫자·불리언 리터럴 · 배열 리터럴 · 객체 리터럴, 그리고 enum 멤버 참조.
- ★ 3번의 통과한 여섯 줄이 그 실증이다. `{ a: n }` 은 **껍데기가 객체 리터럴**이라 통과하고, 안의 `n` 은 굳힐 것이 없어 `number` 로 남는다.
- ★ 계산된 값을 타입에 담고 싶으면 `as const` 가 아니라 **템플릿 리터럴 타입**이나 타입 주석을 쓴다(3번의 13행).

### 9. ★★ 세 수단이 **고정하는 것과 남기는 것**이 다르다

**왜 그런가**

| 수단 | 타입을 고정하나 | 초과 프로퍼티 검사 | 추론을 남기나 | 이 배치에서 던졌나 |
|---|---|---|---|---|
| **타입 주석** `: "circle"` | ★ **그 타입으로 고정** | 돈다 | 아니다 — 적은 타입이 전부다 | 1번(13·14행) |
| **`as const`** | ★ **리터럴 + `readonly` + 튜플** | 돈다 | 그렇다 — 굳힌 채로 | 2번 전체 |
| **`satisfies`** | 고정하지 않는다 — **검사만** | ★ **돈다**([**06번 주제**](../06-excess-property-checks/) 실측) | ★ **그렇다 — 넓히지도 좁히지도 않는다** | ★ **안 던졌다**(목록의 **29번 주제**) |

- ★★ 고르는 기준은 「**이 값의 타입을 내가 정할 것인가, 확인만 받을 것인가**」다.
- ★★ 타입 주석은 **넓은 타입으로 덮어쓴다** — `const conf: Record<string, string> = { … }` 로 적으면 키의 리터럴이 사라진다.\
  그 자리를 메우려고 나온 것이 `satisfies` 다.
- ★ `as const` 와 `satisfies` 는 **같이 쓸 수 있다.** 다만 이 배치에서는 **안 던졌으므로 형태도 적지 않는다** — 목록의 **29번 주제**에서 던진다.
- ★ 셋 다 **방출에는 한 글자도 안 남는다**(5번).

### 10. ★★★ **타입 검사만 막고 런타임은 못 막는다**

**왜 그런가**

| 무엇 | `readonly` 가 막나 | 근거 |
|---|---|---|
| `frozen.retries = 4` | ★ **막는다**(컴파일 시각) | 2번의 24행 `TS2540` |
| `frozenArr.push(4)` | ★ **막는다** — 멤버 자체가 없다 | 2번의 26행 `TS2339` |
| 단언으로 빠져나간 뒤의 `push` | ★★★ **못 막는다** | 5번의 실행 `1,2,3,9` |
| 다른 모듈이 같은 객체를 바꾸는 것 | **못 막는다** | 런타임에 표시가 없다 |
| `Object.isFrozen` | ★ **`false`** | 5번의 실행 출력 |

- ★★★ 한 줄로 — 「**`readonly` 는 계약이지 자물쇠가 아니다.**」
- ★★ 자물쇠가 필요하면 `Object.freeze` 를 **직접 불러야** 한다. `as const` 는 그것을 안 넣어 준다.
- ★ 같은 경계를 [**07번 주제**](../07-object-type-details/)가 `readonly` 프로퍼티로 이미 세웠다. 여기서는 **`as const` 로 붙인 `readonly` 도 예외가 아니라는 것**을 확인했다.

### 11. ★★ **다른 일이다** — 넓히기는 **추론**의 일, 흡수는 **유니온 정규화**의 일

**왜 그런가**

| | 넓히기(이 주제) | 리터럴 흡수([**09번 주제**](../09-union-types/)) |
|---|---|---|
| 언제 일어나나 | **추론할 때** — 주석이 없을 때 | **유니온을 만들 때** — 주석에 적어도 일어난다 |
| 예 | `let x = "a"` → `string` | `"x" \| "y" \| string` → `string` |
| 막는 법 | `const` · 타입 주석 · `as const` | ★ **막을 수 없다** — `string` 을 안 섞는 수밖에 |
| 증거 | 1번의 탐침 열세 개 | 09 의 2번 15행 |

- ★★★ 헷갈리는 이유는 **결과가 똑같이 `string`** 이기 때문이다. 그러나 **원인이 다르니 고치는 법도 다르다.**
- ★★ `"asc" | "desc" | string` 은 `as const` 로도 못 고친다 — 이미 **타입 자리에 `string` 을 적었기** 때문이다.
- ★ 반대로 `let sort = "asc"` 는 `as const` 나 주석으로 고쳐진다 — **추론 단계의 문제**이기 때문이다.
- ★ 둘을 잇는 관용구가 `"asc" | "desc" | (string & {})` 다. [**10번 주제**](../10-intersection-types/)의 3절이 `A & string` 이 **줄지 않는다**는 것을 확인했고,\
  그 성질이 이 관용구의 토대다. 다만 **이 배치에서 이 관용구 자체는 안 던졌다.**

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `const` 는 리터럴을 고정하고 `let`·`var`·프로퍼티·배열 요소·함수 반환은 **넓어진다** · `as const` 는 **세 가지**를 재귀로 한다 · `as const` 는 **리터럴 식에만** 붙는다(`TS1355`) · 템플릿 리터럴 타입은 **조합으로 펼쳐진다** · **방출에 안 남는다** |
| **설정에 달린 것** | ★ **없다**. 네 파일을 `--strict false` 로 다시 던져 **종료 코드와 출력이 전부 같은 것**을 확인했다(아래 블록) |
| **이 판(7.0.2)의 관찰** | ★★ 펼쳐진 템플릿 리터럴 유니온의 **멤버 순서**(`"onDown" \| "onUp"`) · `TS2820` 이 **오타 후보를 고르는 방식** · `.d.ts` 가 객체 타입을 여러 줄로 펼쳐 적는 서식 · 진단 문구 전문 |

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.11a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.11b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.11c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.11d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★ 「**에러가 안 난 줄」도 근거다** — 3번의 11\~16행이 통째로 그렇다. `TS1355` 가 **안 난 여섯 줄**이 허용 목록의 실증이다.
- ★ **멤버 순서는 대조 기준으로 쓰지 않는다.** 「같은 집합으로 펼쳐진다」는 성질만 읽는다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 넓히기 | `--noEmit ex.11a.ts` | exit 1 · **14건** · 넓어지는 자리 **다섯 곳** 확인 |
| `as const` 세 가지 | `--noEmit ex.11b.ts` | exit 1 · **15건** · `readonly [1, 2, 3]` · 사본은 `(1 \| 2 \| 3)[]` |
| `TS1355` | `--noEmit ex.11c.ts` | exit 1 · **11건**(그중 `TS1355` **4건**) · 통과한 여섯 줄이 허용 목록 |
| 템플릿 리터럴 타입 | `--noEmit ex.11d.ts` | exit 1 · **8건** · `Pair` 가 **4멤버** · `TS2820` 이 후보를 짚음 |
| 방출·실행 | `tsc ex.11e.ts` + `node ex.11e.js` | tsc exit 0 · node exit 0 · `as const` **0글자** · `isFrozen` **false** · `push` 뒤 `1,2,3,9` |
| 선언 방출 | `--declaration --emitDeclarationOnly ex.11f.ts` | exit 0 · 값은 추론 결과 · **`Handler` 는 적은 그대로** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★ **전부 동일** — 종료 코드도 출력도 같다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **펼쳐진 템플릿 리터럴 유니온의 멤버 순서** — 09 의 유니온 정렬과 같은 성질이다. **이 문서의 대조 기준으로 쓰지 않는다.**
- `TS2820` 이 「Did you mean …?」로 **어느 후보를 고르는가** — 보고기의 구현이다.
- `.d.ts` 가 객체 타입을 **여러 줄로 펼쳐 적는 서식** — 선언 방출기의 구현이다.
- `TS1355` 의 **문구 전문** — 코드가 더 오래 간다. 다만 이 문구는 **규칙 자체를 읽어 주므로** 인용할 값이 있다.

**안 돌려 본 것**

- **`satisfies`** — 9번 표의 한 칸을 차지하지만 **이 배치에서 안 던졌다.** 형태도 적지 않았다. 목록의 **29번 주제**에서 던진다.
- **`as const` 로 enum 을 대신하는 관용구**(`typeof Color[keyof typeof Color]`) — **안 던졌다.** [목록의 **23번**](../23-typeof-type-operator/)·**31번 주제**.
- **`"asc" | "desc" | (string & {})` 관용구** — 11번에서 **형태만** 적었고 던지지 않았다.
- **템플릿 리터럴 조합이 커질 때의 검사 시간** — **재지 않았고 수치를 적지 않았다.** 목록의 **45번 주제**에서 잰다.
- **7.0 이 바꾼 템플릿 리터럴 타입의 유니코드 취급** — ASCII 만 던졌다. 목록의 **27번 주제**에서 던진다.
