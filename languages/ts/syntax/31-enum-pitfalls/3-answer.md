# ts/syntax/31 — 열거형의 함정 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`)이다** — 1번 방출물 격자와 4번 플래그 판 격자가 결론을 낸다.\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 5 · 5 · 0 · 0 · 0 · 1줄 — 숫자 enum 은 `n99` 가 막히고 **`nvar` 가 통과** · 키는 **넷 대 둘** · **19 / 30**

**출력**

```text
===== bash ts30b-enumgrid.sh (sh exit=0) =====
         | emit | lit | n99 | nvar | keys | rev
[num] enum Dir { Up, Down }
    emit  5줄
    lit   OK
    n99   TS2322
    nvar  OK
    keys  ["0","1","Up","Down"]
    rev   "Up"
[str] enum Dir { Up = "UP", Down = "DOWN" }
    emit  5줄
    lit   TS2322
    n99   TS2322
    nvar  TS2322
    keys  ["Up","Down"]
    rev   (TS7053) undefined
[const] const enum Dir { Up, Down }
    emit  0줄
    lit   OK
    n99   TS2322
    nvar  OK
    keys  (TS2475) ReferenceError
    rev   (TS2476) ReferenceError
[declare] declare enum Dir { Up, Down }
    emit  0줄
    lit   OK
    n99   OK
    nvar  OK
    keys  ReferenceError
    rev   ReferenceError
[union] type Dir = 0 | 1;
    emit  0줄
    lit   OK
    n99   TS2322
    nvar  TS2322
    keys  (TS2693) ReferenceError
    rev   (TS2693) ReferenceError
[asconst] const Dir = { Up: 0, Down: 1 } as const; type Dir = (typeof Dir)[keyof typeof Dir];
    emit  1줄
    lit   OK
    n99   TS2322
    nvar  TS2322
    keys  ["Up","Down"]
    rev   (TS7053) undefined

숫자 enum 행과 갈린 칸 19 / 30
```

**왜 그런가**

| 행 | emit | `n99` | `nvar` | `keys` |
|---|---|---|---|---|
| `[num]` | 5줄 | `TS2322` | ★★★ **`OK`** | ★★★ **`["0","1","Up","Down"]`** |
| `[str]` | 5줄 | `TS2322` | `TS2322` | `["Up","Down"]` |
| `[const]` | **0줄** | `TS2322` | ★ `OK` | `(TS2475) ReferenceError` |
| `[declare]` | **0줄** | ★★★ **`OK`** | `OK` | ★★★ **진단 없이 `ReferenceError`** |
| `[union]` | **0줄** | `TS2322` | `TS2322` | `(TS2693) ReferenceError` |
| `[asconst]` | 1줄 | `TS2322` | `TS2322` | `["Up","Down"]` |

- ★★ `[str]` 은 **자기 값 `"UP"` 도** `TS2322`(`lit` 열) — 문자열 enum 은 명목적으로 군다.

### 2. ★★ 진단 **0줄** · `enum Dir` 은 **5줄짜리 즉시 실행 함수**가 된다 · `label(7)` 은 **`undefined`**

**출력**

```ts
// ex.31a.ts
// 숫자 enum 의 방출물 -- 그리고 number 로 들어온 값
enum Dir {
    Up,
    Down,
}
function label(d: Dir): string {
    switch (d) {
        case Dir.Up:
            return "up";
        case Dir.Down:
            return "down";
    }
}
const fromNetwork: number = 7;
console.log("[1]", Object.keys(Dir));
console.log("[2]", Object.values(Dir));
console.log("[3]", Dir[Dir.Up], Dir[fromNetwork]);
console.log("[4]", label(fromNetwork));
console.log("[5]", fromNetwork in Dir, "Up" in Dir, 0 in Dir);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.31a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e31a ex.31a.ts (tsc exit=0) =====
===== 방출된 e31a/ex.31a.js =====
"use strict";
// 숫자 enum 의 방출물 -- 그리고 number 로 들어온 값
var Dir;
(function (Dir) {
    Dir[Dir["Up"] = 0] = "Up";
    Dir[Dir["Down"] = 1] = "Down";
})(Dir || (Dir = {}));
function label(d) {
    switch (d) {
        case Dir.Up:
            return "up";
        case Dir.Down:
            return "down";
    }
}
const fromNetwork = 7;
console.log("[1]", Object.keys(Dir));
console.log("[2]", Object.values(Dir));
console.log("[3]", Dir[Dir.Up], Dir[fromNetwork]);
console.log("[4]", label(fromNetwork));
console.log("[5]", fromNetwork in Dir, "Up" in Dir, 0 in Dir);
```

```text
===== node e31a/ex.31a.js (node exit=0) =====
[1] [ '0', '1', 'Up', 'Down' ]
[2] [ 'Up', 'Down', 0, 1 ]
[3] Up undefined
[4] undefined
[5] false true true
```

**왜 그런가**

- ★★★ `Dir[Dir["Up"] = 0] = "Up";` — 한 줄이 이름 → 값과 값 → 이름을 **둘 다** 쓴다. 그래서 `[1]` 이 넷, `[2]` 가 이름·숫자 섞임.
- ★★ `[3] Up undefined` — `Dir[7]` 은 `undefined` 인데 타입은 `string`.
- ★★★ `[4] undefined` — `label` 은 `string` 을 **돌려주지 않았다.** `switch` 가 빠짐없다고 믿은 컴파일러는 반환 누락을 안 냈고, `number` 7 은 두 `case` 를 다 빗나갔다.
- ★ `[5] false true true` — `7 in Dir` 로 런타임 확인은 된다. 단 **`0 in Dir` 과 `"Up" in Dir` 이 둘 다 `true`** 다.

### 3. ★★★ 7.0.2 는 **15·16행**이 막힌다 — 4.9.5 는 **하나도 안 막힌다** · `--erasableSyntaxOnly` 는 **`TS1294` · `TS1294` · `TS5023`**

**출력**

```ts
// ex.31b.ts
// 숫자 enum 에 멤버가 아닌 숫자 리터럴을 넣으면
enum Dir {
    Up,
    Down,
}
enum Flag {
    A = 1,
    B = 2,
    C = 4,
}
declare enum Ambient {
    P,
    Q,
}
let d: Dir = 99;
let f: Flag = 3;
let g: Flag = Flag.A | Flag.B;
let a: Ambient = 99;
console.log(d, f, g, a);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.31b.ts (tsc exit=1) =====
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
```

```text
===== bash ts30b-enumver.sh (sh exit=0) =====
== tsc Version 7.0.2
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 1)
== node OLD Version 5.9.3
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 2)
== node V49 Version 4.9.5
(exit 0)

---- --erasableSyntaxOnly 를 세 판에 ----
== tsc
ex.31b.ts(2,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(6,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 1)
== node OLD
ex.31b.ts(2,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(6,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 2)
== node V49
error TS5023: Unknown compiler option '--erasableSyntaxOnly'.
(exit 1)
```

**왜 그런가**

| 줄 | 4.9.5 | 5.9.3 | 7.0.2 |
|---|---|---|---|
| 15 `let d: Dir = 99` | 통과 | `TS2322` | `TS2322` |
| 16 `let f: Flag = 3` | 통과 | `TS2322` | `TS2322` |
| 17 `Flag.A \| Flag.B` | 통과 | 통과 | 통과 |
| 18 `let a: Ambient = 99` | 통과 | 통과 | 통과 |
| `--erasableSyntaxOnly` | ★ `TS5023` — 옵션 없음 | `TS1294` × 2 | `TS1294` × 2 |

- ★★★ 5.0 릴리스 노트의 「멤버 영역 밖 리터럴 대입이 이제 에러」가 **4.9.5 와 5.9.3 사이**에서 갈렸다. 5.0 그 자체는 이 머신에 없다.
- ★★ `TS1294` 는 `enum Dir`(2행)·`enum Flag`(6행)에만 — **`declare enum Ambient` 는 안 걸렸다.**

### 4. ★★★ 객체 **없음** → JS 소비자 **`SyntaxError`** · `Level.High` **참조로** 바뀌고 `useamb31` 에서 `TS2748` · 갈리는 칸은 **진단·`use31` 줄·`node`** · **11 / 16**

**출력**

```ts
// lib31.mts
export const enum Level {
    Low = 1,
    High = 2,
}
```

```ts
// use31.mts
import { Level } from "./lib31.mjs";
console.log("use31", Level.High);
```

```ts
// amb31.d.ts
declare const enum Amb {
    K = 7,
}
```

```ts
// useamb31.mts
console.log("useamb31", Amb.K);
```

```text
===== bash ts30b-constflags.sh (sh exit=0) =====
[(없음)]
    진단       OK
    Level 객체  lib31.mjs 에 0개
    use31.mjs  console.log("use31", 2 /* Level.High */);
    node       use31 2/useamb31 7/./jsuser31.mjs SyntaxError The requested module './lib31.mjs' does not provide an export named 'Level'
[--isolatedModules]
    진단       useamb31.mts(1,25) TS2748
    Level 객체  lib31.mjs 에 1개
    use31.mjs  console.log("use31", Level.High);
    node       use31 2/./useamb31.mjs ReferenceError Amb is not defined/jsuser31 2
[--verbatimModuleSyntax]
    진단       useamb31.mts(1,25) TS2748
    Level 객체  lib31.mjs 에 1개
    use31.mjs  console.log("use31", Level.High);
    node       use31 2/./useamb31.mjs ReferenceError Amb is not defined/jsuser31 2
[--preserveConstEnums]
    진단       OK
    Level 객체  lib31.mjs 에 1개
    use31.mjs  console.log("use31", 2 /* Level.High */);
    node       use31 2/useamb31 7/jsuser31 2
[--erasableSyntaxOnly]
    진단       lib31.mts(1,19) TS1294
    Level 객체  lib31.mjs 에 0개
    use31.mjs  console.log("use31", 2 /* Level.High */);
    node       use31 2/useamb31 7/./jsuser31.mjs SyntaxError The requested module './lib31.mjs' does not provide an export named 'Level'

플래그 없는 행과 갈린 칸 11 / 16
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e31f lib31.mts use31.mts useamb31.mts amb31.d.ts (tsc exit=0) =====
===== 방출된 e31f/lib31.mjs =====
export {};
===== 방출된 e31f/use31.mjs =====
console.log("use31", 2 /* Level.High */);
export {};
```

```text
===== tsc --pretty false -t es2022 --strict --isolatedModules --outDir e31i lib31.mts use31.mts useamb31.mts amb31.d.ts (tsc exit=2) =====
useamb31.mts(1,25): error TS2748: Cannot access ambient const enums when 'isolatedModules' is enabled.
===== 방출된 e31i/lib31.mjs =====
export var Level;
(function (Level) {
    Level[Level["Low"] = 1] = "Low";
    Level[Level["High"] = 2] = "High";
})(Level || (Level = {}));
===== 방출된 e31i/use31.mjs =====
import { Level } from "./lib31.mjs";
console.log("use31", Level.High);
===== 방출된 e31i/useamb31.mjs =====
console.log("useamb31", Amb.K);
export {};
```

**왜 그런가**

| 판 | `Level` 객체 | `use31.mjs` | JS 소비자 |
|---|---|---|---|
| `(없음)` | ★★★ **0개** | `2 /* Level.High */` — `import` 도 사라짐 | ★★★ **`SyntaxError`** |
| `--isolatedModules` | 1개 | ★★★ **`Level.High`** — 참조 | `2` · 대신 `useamb31` 이 `TS2748`·`ReferenceError` |
| `--verbatimModuleSyntax` | 1개 | `Level.High` | `2` — `--isolatedModules` 와 같다 |
| `--preserveConstEnums` | 1개 | `2 /* Level.High */` — 여전히 인라인 | `2` · 진단 없음 |
| `--erasableSyntaxOnly` | 0개 | `2 /* Level.High */` | `SyntaxError` · 진단 `TS1294` |

- ★★ `--preserveConstEnums` 와 `--isolatedModules` 는 **객체 칸은 같고** 진단 · `use31` 줄 · `node` 세 칸이 갈린다.

### 5. ★★ `Dir[Dir["Up"] = 0] = "Up";` 이 **숫자 키까지** 만든다 — 문자열 enum 방출물에는 **바깥 대입이 없다**

- ★★★ 숫자 enum 의 한 줄은 **`Dir.Up = 0`** 과 **`Dir[0] = "Up"`** 을 함께 한다 → 키 넷.
- ★★ 문자열 enum 은 `Dir["Up"] = "UP";` 만 한다 — 역매핑이 없어 키 둘. 핸드북도 「문자열 enum 멤버는 역매핑을 **전혀** 만들지 않는다」고 적는다.

### 6. ★★★ **경계에서 들어온 숫자**가 그대로 enum 이 되어 `switch` 를 빠져나간다

- ★★ 5.0 이 막은 것은 **리터럴** `99` 다. 타입이 `number` 인 변수는 여전히 **숫자 enum 자리에 들어간다**(1번 `nvar`).
- ★★★ 새는 곳 — 2번 `[4]`. `label(fromNetwork)` 가 **`string` 이라던 반환값으로 `undefined`** 를 냈다. 빠짐없는 `switch` 라는 **컴파일러의 판단**이 런타임 값 앞에서 틀린다.
- ★ 막는 법 — 경계에서 `x in Dir` 같은 **런타임 확인**을 거친다(2번 `[5]` 에서 `7 in Dir` 이 `false`).

### 7. ★★ `n99` — ambient enum 의 멤버는 **계산된 멤버**로 취급 · `keys` — **값을 줄 방출물이 없는데** 선언이라 진단도 없다

- ★★ 핸드북 — 「ambient(non-const) enum 에서 초기자 없는 멤버는 **항상 계산된 것**으로 본다」. 그 결과로 **리터럴 `99` 가 통과**한 것으로 읽힌다(두 문장이 어떻게 맞물리는지는 **던져서 본 것**이다).
- ★★★ `declare` 는 「**값은 다른 곳에 있다**」는 약속이라 컴파일러는 `Object.keys(Dir)` 에 아무 말도 안 한다. 방출물에는 `Dir` 이 **없으니** `ReferenceError`.

### 8. ★★★ **`(없음)` 판의 `Level` 객체 0개**와 **`--isolatedModules` 판의 `use31` 줄**

- ★★ 파일 단위 도구는 `use31.mts` 만 보고 `Level.High` 가 `2` 인지 **알 수 없다** — 인라인할 수 없으니 **참조**를 남긴다.
- ★★★ 그런데 기본 방출의 `lib31.mjs` 에는 **참조할 객체가 없다**(0개). 두 칸을 합치면 — **`lib31` 을 `tsc` 기본으로, `use31` 을 파일 단위 도구로** 만들면 참조가 **없는 export** 를 가리킨다. JS 소비자 칸의 `SyntaxError` 가 바로 그 모양이다.
- ★ `tsc` 는 `--isolatedModules` 에서 **양쪽을 같이** 바꿔(객체를 남기고 참조로) 이 어긋남을 피했다. 이 판의 관찰이다.

### 9. ★★ 얻는 칸 — **`nvar` 가 막힌다**·키가 둘 · 잃는 칸 — **역매핑**(`rev`)

| 대안 | 얻는 칸 | 잃는 칸 |
|---|---|---|
| 유니온 `0 \| 1` | `nvar` `TS2322` · 방출물 0줄 | ★ 런타임 **값이 없다**(`keys`·`rev` 가 `ReferenceError`) |
| `as const` 객체 | `nvar` `TS2322` · `keys` 둘 · 방출물 1줄 평범한 JS | ★ **역매핑**(`rev` 가 `TS7053`·`undefined`) |

### 10. ★★ 23편 — **값 공간과 타입 공간이 따로다** · 가까운 쪽은 **C#**

- ★★★ `const Dir = {…}` 은 **값 공간**, `type Dir = …` 은 **타입 공간**에 산다 — [**23번 주제**](../23-typeof-type-operator/) 1절이 「같은 이름이 두 공간에 따로 산다」로 정본을 세웠다. 4절은 enum 이 **한 선언으로 두 공간을 다 채운다**는 것.
- ★★ C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **20번** — 「정수 위의 얇은 껍데기」. TS 숫자 enum 도 멤버가 **그냥 숫자**이고 `number` 를 받는다. **폴더가 아직 없어** 실측은 인용 못 했다.
- ★ 파이썬 [`../../../python/syntax/37-enum/`](../../../python/syntax/37-enum/) — 멤버가 **싱글턴 객체**라 정수와 비교하면 같지 않다. TS 와 **반대쪽**이다.

### 11. ★★ **4.9.5 까지** — 이 머신에서는 **4.9.5 와 5.9.3 사이**까지 · `--erasableSyntaxOnly` 는 **있다** — 4.9.5 는 `TS5023`

- ★★ 경계 자체(5.0)는 **릴리스 노트의 문장**이고, 이 머신에서 **던져 확인한 것은 양옆 두 판**이다.
- ★ 7.0.2 와 5.9.3 은 `TS1294` — `enum`·`const enum` 을 막고 `declare` 는 안 막는다. 4.9.5 는 「Unknown compiler option」.

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.31a.ts    exit 0 = exit 0 · 출력 한 글자도 같다
ex.31b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.31c.ts    exit 0 = exit 0 · 출력 한 글자도 같다
```

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ 방출물 격자 | `bash ts30b-enumgrid.sh` (6 × 6 칸) | exit 0 · **19 / 30** |
| 숫자 enum 방출 | `--noEmit`·`--outDir e31a`·`node` | 진단 0줄 · 5줄 IIFE · `[4] undefined` |
| ★★ 판 격자 | `bash ts30b-enumver.sh` (세 판 × 두 번) | 7.0.2·5.9.3 **`TS2322` × 2** · 4.9.5 **통과** · `TS5023` |
| ★★★ 플래그 판 격자 | `bash ts30b-constflags.sh` (다섯 판) | exit 0 · **11 / 16** |
| 두 방출물 | `--outDir e31f` · `--isolatedModules --outDir e31i` | 객체 0 / 1 · 인라인 / 참조 |
| `strict` 대조 | 세 파일을 `--strict false` 로 재실행 | **하나도 안 갈림** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ `--isolatedModules` 가 객체를 남기고 참조로 바꾸는 것(4번) — 이 판의 방출기 동작이다.
- ★★ `declare enum` 이 리터럴 `99` 를 받는 것(1번 · 3번) — 핸드북 문장으로 **읽히지만** 판마다 다시 확인할 칸이다.
- ★ 진단이 있을 때의 **종료 코드**(7.0.2 `1` 대 5.9.3 `2`).

**안 돌려 본 것**

- ★★★ **`const enum` 의 실행 속도·번들 크기** — 재지 않았다.
- ★★ **TS 5.0 그 자체** · **5.8 그 자체** — 이 머신에 없다.
- ★★ **실제 파일 단위 트랜스파일러**(esbuild·swc·Babel) — 이 머신에서 안 돌렸다. 8번은 `tsc --isolatedModules` 와 기본 방출을 **맞대어 추론**한 것이다.
