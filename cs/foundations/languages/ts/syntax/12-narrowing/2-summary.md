# ts/syntax/12 — 좁히기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) ·
> [Handbook — Narrowing: `typeof` type guards](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#typeof-type-guards) ·
> [TSConfig — `strictNullChecks`](https://www.typescriptlang.org/tsconfig/#strictNullChecks).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로
> 이 블록들은 설정 파일 없이도 그대로 재현된다.
> ★★★ 이 주제는 [**10번**](../10-intersection-types/)·[**11번 주제**](../11-literal-types-and-as-const/)와 달리 **`strict` 에 기댄다.**
> 네 파일 중 **셋이 `--strict false` 에서 답이 갈렸고**, 그 세 자리는 **양쪽 판을 다 실었다.**
> **버전** — `typeof`·`instanceof` 좁히기는 TS 1.x, `in` 좁히기는 2.0, 판별 유니온은 2.0,
> **조건을 `const` 에 담아도 좁혀지는 것**(별칭 조건)은 **4.4** 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★ **진단이 나지 않은 줄** — `never` 로 좁혀진 자리다 | 소스 전문을 진단 옆에 뒀으니 다시 던질 수 있다 |
| **★ 설정에 달렸다** | `null`·`undefined` 가 **분기에 남는가** | `strictNullChecks`. **네 파일 중 셋이 갈렸다** — 양쪽을 다 실었다 |
| **흔들린다** | 좁혀진 유니온을 진단이 찍을 때의 **멤버 순서** | 09 에서 본 정렬과 같은 성질이다. **집합만 성질로 읽는다** |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 「**에러가 안 난 줄**」이 근거인 자리가 둘 있다 — 1절의 16·17·23행, 3절의 36행.
> 그래서 **모든 진단 블록 옆에 소스 전문**을 뒀다.

## 한눈에 — 쉽게 말하면

**좁히기는 「이 줄에 오기까지 무슨 일이 있었나」를 읽어서 타입을 줄이는 것이다.**

| 비유 | 실체 |
|---|---|
| 「이 상자에는 신발 **또는** 모자」 | **유니온** — 열기 전에는 모른다([**09번 주제**](../09-union-types/)) |
| 상자를 흔들어 **소리로 확인**한다 | **좁히기 검사** — `typeof`·`instanceof`·`in`·진릿값·`===` |
| 소리를 들은 **뒤부터** 한 종류로 다룬다 | 분기 안에서 타입이 줄어든다 |
| ★ 확인한 사람은 **나뿐**이다 | **다른 함수 안으로는 안 따라간다** — 클로저에서 풀린다 |
| ★ 상자를 다시 채우면 소용없다 | **재대입하면 풀린다** |
| ★ 소리를 「**들었다**」고 쪽지에 적어 두면 인정해 준다 | **`const` 에 담은 조건은 인정**된다(4.4). **`let` 은 아니다** |
| 확인할 소리가 **없는 상자**도 있다 | `typeof` 로는 객체끼리·`null` 을 못 가른다 |

- ★★★ 한 줄로 — 「**좁히기를 하는 것은 JS 연산자이고, 컴파일러는 그 연산자를 읽고 따라갈 뿐이다.**」
- ★★ 그래서 **런타임에 확인할 수단이 없으면 좁힐 수도 없다.** 방출된 `.js` 에 남는 것이 곧 좁히기의 근거다.

```text
  좁히기 수단 — 무엇을 가르나

  typeof v === "string"     원시 타입 6가지 + "object"·"function"
  v instanceof Dog          클래스(프로토타입 체인)
  "fly" in p                프로퍼티 유무
  if (v)                    진릿값 — ★ 거짓 갈래는 거의 안 줄어든다
  v === "up"                리터럴 값
  s.kind === "circle"       ★ 판별 유니온 — 09 의 본 용도
  Array.isArray(v)          술어 함수 — 13번 주제
```

```text
  typeof 의 구멍

  typeof null      ===  "object"    ★ null 이 객체 쪽에 섞인다
  typeof []        ===  "object"    배열과 객체를 못 가른다
  typeof new Dog() ===  "object"    클래스끼리 못 가른다
        │
        ▼  그래서 instanceof · in · Array.isArray 가 따로 필요하다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **분기마다 무엇이 남나** — 수단 여섯 가지를 각각 던지고 **분기마다 탐침으로 찍는다**.
2. **언제 풀리나** — 함수 호출 뒤·클로저 안·재대입 뒤를 **따로 던져** 확인한다.
3. **누가 실제로 좁히나** — 방출된 `.js` 로 「좁히기 = JS 연산자」를 확인한다.

★ [**09번 주제**](../09-union-types/)가 판별 유니온까지 세웠다면 여기는 **좁히기 수단 전부**를 본다.
[**13번 주제**](../13-type-guards-and-predicates/)는 그 수단을 **함수로 포장**하는 법이다 — 12 → 13 은 한 사슬이다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **분기마다 박은 `null` 탐침** | **그 분기에서 남은 타입**을 글자로 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| ★★ **같은 파일을 `--strict false` 로 다시** | `null`·`undefined` 가 **설정에 달린 것**임을 | [**07번 주제**](../07-object-type-details/)에서 이어받음 |
| ★★★ **방출 `.js` + `node`** | 좁히기가 **JS 연산자 그대로**인 것 | [**09번 주제**](../09-union-types/)에서 이어받음 |

비용 — 컴파일 두 번(`strict` 양쪽).

### (1) ★★★ `typeof` 사다리 — 분기마다 찍어 본다

**언제 쓰나** — 원시 타입이 섞인 유니온을 다룰 때.

```ts
// ex.12a.ts
// typeof 로 갈라 놓고 분기마다 무엇이 남는지 탐침으로 찍는다
type Mixed = string | number | boolean | object | null | undefined;

function byTypeof(v: Mixed) {
    if (typeof v === "string") {
        const inString: null = v;
    } else if (typeof v === "number") {
        const inNumber: null = v;
    } else if (typeof v === "boolean") {
        const inBoolean: null = v;
    } else if (typeof v === "object") {
        const inObject: null = v;
    } else if (typeof v === "undefined") {
        const inUndefined: null = v;
    } else {
        const rest: null = v;
        const exhaustive: never = v;
    }
}

function nullTrap(v: string | null) {
    if (typeof v === "object") {
        const caught: null = v;
    }
    if (v !== null) {
        const excluded: null = v;
    }
}

function noNarrow(v: string | number) {
    const t = typeof v;
    if (t === "string") {
        const notNarrowed: null = v;
    }
}
console.log(byTypeof, nullTrap, noNarrow);
```

```text
===== tsc --pretty false --noEmit ex.12a.ts (tsc exit=1) =====
ex.12a.ts(6,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(8,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12a.ts(10,15): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.12a.ts(12,15): error TS2322: Type 'object | null' is not assignable to type 'null'.
  Type 'object' is not assignable to type 'null'.
ex.12a.ts(14,15): error TS2322: Type 'undefined' is not assignable to type 'null'.
ex.12a.ts(26,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(33,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **열 개**인데 진단은 **일곱 건**이다 — 6·8·10·12·14·26·33행. **침묵한 것은 16·17·23행**이다.
- 6·8·10행은 예상대로다 — `string` · `number` · `boolean`.
- ★★★ 12행이 이 절의 별이다. `typeof v === "object"` 분기에서 `v` 가 **`object | null`** 이다.\
  **`typeof null` 이 `"object"` 이기 때문**에 `null` 이 같이 걸려 들어온다.
- 14행 — `typeof v === "undefined"` 분기는 **`undefined`** 다.
- ★★ 16·17행이 침묵한다. 다섯 갈래를 다 걷어냈으니 마지막 `else` 에서 `v` 는 **`never`** 다 —\
  `const exhaustive: never = v` 가 통과하는 것이 **전수 검사 성공**의 모양이다([**09번 주제**](../09-union-types/)).
- ★★★ 23행도 침묵한다. `v: string | null` 에 `typeof v === "object"` 를 걸면 남는 것이 **`null` 하나**다.\
  탐침이 `null` 이니 통과한다 — **함정이 그대로 드러난 자리**다.
- 26행 — `v !== null` 쪽은 **`string`** 이다. 이쪽이 의도한 검사다.
- ★★ 33행 — `const t = typeof v; if (t === "string")` 은 **안 좁힌다**(`string | number`).\
  **`typeof` 의 결과를 변수에 담으면 그 연결이 끊긴다.** 3절에서 이것과 갈리는 경우를 본다.

> **좁히기(narrowing)** — 제어 흐름을 따라가며 그 자리에서 가능한 타입을 줄이는 것.\
> 예: `if (typeof v === "string")` 안에서 `string | number` 가 `string` 이 된다.

> **전수 검사(exhaustiveness checking)** — 모든 갈래를 처리했는지 `never` 대입으로 확인하는 수법.\
> 예: `const exhaustive: never = v;` — **진단이 안 나면 성공**이다.

비용 — 없음. 다만 **`typeof` 는 객체끼리를 못 가른다** — 다음 절이 그 자리를 메운다.

### (2) ★★★ 나머지 네 수단 — `instanceof`·`in`·진릿값·동등성

**언제 쓰나** — 객체를 가르거나, 「값이 있나」를 물을 때.

```ts
// ex.12b.ts
// typeof 말고 나머지 넷 — instanceof · in · 진릿값 · 동등성
class Dog {
    bark(): void {}
}
class Cat {
    meow(): void {}
}
function byInstance(p: Dog | Cat) {
    if (p instanceof Dog) {
        const inDog: null = p;
    } else {
        const inCat: null = p;
    }
}

interface Bird {
    fly(): void;
}
interface Fish {
    swim(): void;
}
function byIn(p: Bird | Fish) {
    if ("fly" in p) {
        const inBird: null = p;
    } else {
        const inFish: null = p;
    }
}

function byTruth(v: string | number | null | undefined) {
    if (v) {
        const truthy: null = v;
    } else {
        const falsy: null = v;
    }
}

function byEquality(a: string | number, b: string | boolean) {
    if (a === b) {
        const inA: null = a;
        const inB: null = b;
    }
}

function byLiteral(v: "up" | "down" | 1) {
    if (v === "up") {
        const up: null = v;
    } else {
        const rest: null = v;
    }
}

function unknownIn(u: unknown) {
    if (typeof u === "object" && u !== null && "x" in u) {
        const shaped: null = u;
    }
}
console.log(byInstance, byIn, byTruth, byEquality, byLiteral, unknownIn);
```

```text
===== tsc --pretty false --noEmit ex.12b.ts (tsc exit=1) =====
ex.12b.ts(10,15): error TS2322: Type 'Dog' is not assignable to type 'null'.
ex.12b.ts(12,15): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.12b.ts(24,15): error TS2322: Type 'Bird' is not assignable to type 'null'.
ex.12b.ts(26,15): error TS2322: Type 'Fish' is not assignable to type 'null'.
ex.12b.ts(32,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12b.ts(34,15): error TS2322: Type 'string | number | null | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.12b.ts(40,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(41,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(47,15): error TS2322: Type '"up"' is not assignable to type 'null'.
ex.12b.ts(49,15): error TS2322: Type '"down" | 1' is not assignable to type 'null'.
  Type '"down"' is not assignable to type 'null'.
ex.12b.ts(55,15): error TS2322: Type 'object & Record<"x", unknown>' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **열한 건**이다. 탐침 열한 개가 **전부 답했다** — 이 파일에는 `never` 로 좁혀지는 자리가 없다.
- 10·12행 — `p instanceof Dog` 가 `Dog` 와 `Cat` 으로 깔끔하게 가른다. **클래스는 이것이 정석이다.**
- 24·26행 — `"fly" in p` 가 `Bird` 와 `Fish` 로 가른다. **인터페이스에는 `instanceof` 를 못 쓰므로** 이 수단이 필요하다.
- ★★★ 32·34행이 이 절에서 가장 많이 틀리는 자리다. `v: string | number | null | undefined` 에 `if (v)` 를 걸면 —\
  참 갈래는 **`string | number`**(널만 빠졌다), 거짓 갈래는 **`string | number | null | undefined`** 로 **하나도 안 줄었다.**
- ★★ 왜인가 — `""` 와 `0` 도 거짓이기 때문이다. 타입에는 「빈 문자열이 아닌 `string`」을 적을 수 없으므로 **`string` 이 그대로 남는다.**
- ★ 40·41행 — `a === b` 가 **양쪽을 동시에** 좁힌다. `string | number` 와 `string | boolean` 의 공통이 `string` 하나라서다.
- 47·49행 — 리터럴 유니온도 `===` 로 갈린다. 거짓 갈래는 **`"down" | 1`** 로 **그 값만 빠진다.**
- ★★★ 55행이 [**10번 주제**](../10-intersection-types/)와 이어진다. `typeof u === "object" && u !== null && "x" in u` 뒤의 `u` 가\
  **`object & Record<"x", unknown>`** 다 — **좁히기가 교차를 만든다.** 세 검사의 결과가 `&` 로 합쳐진 것이다.

> **진릿값 좁히기(truthiness narrowing)** — `if (v)` 로 거짓 값(`0`·`""`·`null`·`undefined`·`NaN`·`false`)을 걸러내는 것.\
> ★ **참 갈래만 좁아지고 거짓 갈래는 거의 안 줄어든다.**

비용 — ★ 둘 다 **런타임 의미가 따라온다** — `in` 은 프로토타입 체인까지 보고, `instanceof` 는 realm 이 다르면 실패한다.
**이 둘은 JS 쪽 성질이라 이 배치에서 던지지 않았다** — `../../js/syntax/README.md` 의 **01번 주제**가 정본이다.

### (3) ★★ 조건을 변수에 담으면 — `const` 는 되고 `let` 은 안 된다

**언제 쓰나** — 조건이 길어서 이름을 붙이고 싶을 때.

```ts
// ex.12c.ts
// 조건을 변수에 담아도 좁혀지나 — const 와 let 이 갈린다
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number }
    | { kind: "tri"; base: number; h: number };

function byConstAlias(v: string | number) {
    const isStr = typeof v === "string";
    if (isStr) {
        const narrowed: null = v;
    }
}

function byLetAlias(v: string | number) {
    let isStr = typeof v === "string";
    if (isStr) {
        const notNarrowed: null = v;
    }
}

function bySwitch(s: Shape) {
    switch (s.kind) {
        case "circle": {
            const inCircle: null = s;
            return;
        }
        case "square": {
            const inSquare: null = s;
            return;
        }
        case "tri": {
            const inTri: null = s;
            return;
        }
        default: {
            const exhaustive: never = s;
            return exhaustive;
        }
    }
}

function afterEarlyReturn(s: Shape) {
    if (s.kind === "circle") return;
    const rest: null = s;
}

function byDiscriminantAlias(s: Shape) {
    const k = s.kind;
    if (k === "circle") {
        const viaAlias: null = s;
    }
}
console.log(byConstAlias, byLetAlias, bySwitch, afterEarlyReturn, byDiscriminantAlias);
```

```text
===== tsc --pretty false --noEmit ex.12c.ts (tsc exit=1) =====
ex.12c.ts(10,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12c.ts(17,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12c.ts(24,19): error TS2322: Type '{ kind: "circle"; r: number; }' is not assignable to type 'null'.
ex.12c.ts(28,19): error TS2322: Type '{ kind: "square"; side: number; }' is not assignable to type 'null'.
ex.12c.ts(32,19): error TS2322: Type '{ kind: "tri"; base: number; h: number; }' is not assignable to type 'null'.
ex.12c.ts(44,11): error TS2322: Type '{ kind: "square"; side: number; } | { kind: "tri"; base: number; h: number; }' is not assignable to type 'null'.
  Type '{ kind: "square"; side: number; }' is not assignable to type 'null'.
ex.12c.ts(50,15): error TS2322: Type '{ kind: "circle"; r: number; }' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **여덟 개**인데 진단은 **일곱 건**이다 — 침묵한 것은 **36행** 하나다.
- ★★★ 10행과 17행이 갈린다. `const isStr = typeof v === "string"` 은 **좁히고**(`string`),\
  `let isStr = …` 는 **안 좁힌다**(`string | number`). **선언 키워드 하나가 갈랐다.**
- ★★ 이유는 `let` 이 **재대입될 수 있어서** 그 조건이 아직 참인지 컴파일러가 보장 못 하기 때문이다.\
  같은 논리가 [**11번 주제**](../11-literal-types-and-as-const/)의 넓히기에도 있었다 — **`const` 와 `let` 은 계속 갈린다.**
- 24·28·32행 — `switch (s.kind)` 가 세 갈래를 각각 **`{ kind: "circle"; r: number; }`** 꼴로 좁힌다.
- ★★★ 36행이 침묵한다 — 세 `case` 를 다 적었으니 `default` 에서 `s` 는 **`never`** 다. **전수 검사 성공.**\
  09 에서는 한 갈래를 빼서 **`'Tri'` 라는 이름이 진단에 찍혔다.** 여기서는 반대로 **침묵이 성공의 증거**다.
- 44행 — 이른 `return` 뒤에도 좁혀진다. 남은 것은 **`{ kind: "square" … } | { kind: "tri" … }`** 유니온이다.
- ★★★ 50행이 1절의 33행과 갈리는 자리다. `const k = s.kind; if (k === "circle")` 은 **`s` 까지 좁힌다.**\
  `const t = typeof v; if (t === "string")` 은 **안 좁혔다.** **판별 프로퍼티를 담은 `const` 는 인정되고, `typeof` 의 결과를 담은 `const` 는 인정되지 않는다.**

```text
  조건을 담아도 좁혀지나 — 이 판에서 던진 세 모양

  const isStr = typeof v === "string";  if (isStr)   ->  ★ 좁힌다   (4.4 별칭 조건)
  let   isStr = typeof v === "string";  if (isStr)   ->  안 좁힌다
  const t     = typeof v;               if (t === "string") -> 안 좁힌다
  const k     = s.kind;                 if (k === "circle") -> ★ 좁힌다 (판별 프로퍼티)
```

> **별칭 조건(aliased condition)** — 좁히기 검사의 **결과**를 `const` 에 담아도 그 이름으로 좁힐 수 있게 한 기능(TS 4.4).\
> 예: `const ok = typeof v === "string";` 뒤의 `if (ok)`. **`let` 에는 적용되지 않는다.**

비용 — 없음. 다만 **어떤 모양이 인정되는지는 외우지 말고 탐침으로 확인하라** — 네 모양 중 둘만 된다.

### (4) ★★★ 좁히기가 풀리는 자리와 안 풀리는 자리

**언제 쓰나** — 「분명히 체크했는데 또 `undefined` 일 수 있다고 한다」에서 막힐 때. **이 절이 이 주제의 본체다.**

```ts
// ex.12d.ts
// 좁히기가 어디서 풀리나 — 함수 호출 뒤·클로저 안·재대입 뒤를 각각 던진다
interface Box {
    v?: string;
}
declare function touch(): void;

function afterCall(b: Box) {
    if (b.v) {
        touch();
        const stillNarrow: null = b.v;
    }
}

function insideClosure(b: Box) {
    if (b.v) {
        const cb = () => {
            const inClosure: null = b.v;
        };
        cb();
    }
}

function fixedByLocal(b: Box) {
    const v = b.v;
    if (v) {
        const cb = () => {
            const inClosure: null = v;
        };
        cb();
    }
}

function afterReassign(v: string | number) {
    if (typeof v === "string") {
        const before: null = v;
        v = 1;
        const after: null = v;
    }
}

let outer: string | number = "s";
function overLet() {
    if (typeof outer === "string") {
        const here: null = outer;
        const cb = () => {
            const inClosure: null = outer;
        };
        cb();
    }
}

function byIndex(xs: (string | number)[], i: number) {
    if (typeof xs[i] === "string") {
        const elem: null = xs[i];
    }
}

function byGetter(o: { get v(): string | number }) {
    if (typeof o.v === "string") {
        const got: null = o.v;
    }
}
console.log(afterCall, insideClosure, fixedByLocal, afterReassign, overLet, byIndex, byGetter);
```

```text
===== tsc --pretty false --noEmit ex.12d.ts (tsc exit=1) =====
ex.12d.ts(10,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(17,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.12d.ts(27,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(35,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(37,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12d.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(46,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12d.ts(54,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **아홉 건**이고 탐침도 아홉 개다 — **전부 답했다.** 읽을 것은 「몇 건」이 아니라 「**무엇이라고**」다.
- ★★★ 10행 — **함수를 호출해도 안 풀린다.** `touch()` 뒤에도 `b.v` 가 **`string`** 이다.\
  「함수 호출이 좁히기를 지운다」는 흔한 믿음이 **이 판에서는 틀렸다.**
- ★★★ 17행 — **클로저 안에서는 풀린다.** 같은 `b.v` 가 **`string | undefined`** 로 돌아간다.
- ★★ 27행이 고치는 법이다 — `const v = b.v` 로 **지역 변수에 담아 두면** 클로저 안에서도 **`string`** 이다.
- 35·37행 — 재대입은 당연히 바꾼다. `string` → `v = 1` → **`number`**.
- ★★ 44행과 46행이 짝이다 — 모듈 수준 `let outer` 는 그 자리에서는 **`string`** 인데 클로저 안에서는 **`string | number`** 다.
- ★ 54행 — `typeof xs[i] === "string"` 뒤의 `xs[i]` 가 **`string`** 이다. **인덱스 접근도 좁혀진다**(`i` 가 재대입되지 않는 매개변수라서).
- ★ 60행 — **게터도 좁혀진다.** `o.v` 가 `string` 이다. 게터는 부를 때마다 다른 값을 줄 수 있는데도 그렇다.

```text
  좁히기가 살아남나 — 이 판에서 던진 일곱 자리

  touch() 호출 뒤의 b.v              ->  ★ 살아 있다 (string)
  클로저 안의 b.v                    ->  ★ 풀린다   (string | undefined)
  const v = b.v 로 담은 뒤 클로저     ->  ★ 살아 있다 (string)
  v = 1 재대입 뒤                    ->  풀린다     (number)
  모듈 let 을 그 자리에서             ->  살아 있다  (string)
  모듈 let 을 클로저 안에서           ->  ★ 풀린다   (string | number)
  xs[i] · 게터 o.v                   ->  ★ 살아 있다 (string)
```

- ★★★ 마지막 세 줄이 **안전하지 않은 쪽**이다. 함수 호출·인덱스·게터는 **그 사이에 값이 바뀔 수 있는데도** 컴파일러가 믿어 준다.\
  **편의를 위해 일부러 낮춘 안전선**이고, 실제로 깨질 수 있는 자리다.

비용 — **클로저를 쓸 거면 먼저 지역 변수에 담아라.** 그것이 유일하게 확실한 수다.

### (5) ★★★ 같은 파일을 `--strict false` 로 다시 던진다

**언제 쓰나** — 「우리 팀은 왜 이게 에러가 안 나지」에서 막힐 때. **이 주제는 여기가 갈린다.**

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.12a.ts    exit 1 / exit 1 · ★ 다르다
ex.12b.ts    exit 1 / exit 1 · ★ 다르다
ex.12c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.12d.ts    exit 1 / exit 1 · ★ 다르다
```

- ★★★ **네 파일 중 셋이 갈린다.** [**10번**](../10-intersection-types/)·[**11번 주제**](../11-literal-types-and-as-const/)가 **0개**였던 것과 대비된다.

1절의 파일을 끈 채로 다시 던지면 —

```text
===== tsc --pretty false --noEmit --strict false ex.12a.ts (tsc exit=1) =====
ex.12a.ts(6,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(8,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12a.ts(10,15): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.12a.ts(12,15): error TS2322: Type 'object' is not assignable to type 'null'.
ex.12a.ts(26,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(33,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

- ★★★ **12행이 `object | null` 이 아니라 그냥 `object`** 다 — `null` 이 유니온에서 흡수돼 **함정이 사라진다.**
- ★★★ **14행의 진단이 통째로 없다.** `undefined` 도 흡수됐으니 그 갈래에 남는 것이 `never` 라 탐침이 침묵한다.
- ★ 나머지 다섯 줄은 글자 하나까지 같다.

2절의 파일도 갈린다.

```text
===== tsc --pretty false --noEmit --strict false ex.12b.ts (tsc exit=1) =====
ex.12b.ts(10,15): error TS2322: Type 'Dog' is not assignable to type 'null'.
ex.12b.ts(12,15): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.12b.ts(24,15): error TS2322: Type 'Bird' is not assignable to type 'null'.
ex.12b.ts(26,15): error TS2322: Type 'Fish' is not assignable to type 'null'.
ex.12b.ts(32,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12b.ts(34,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12b.ts(40,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(41,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(47,15): error TS2322: Type '"up"' is not assignable to type 'null'.
ex.12b.ts(49,15): error TS2322: Type '"down" | 1' is not assignable to type 'null'.
  Type '"down"' is not assignable to type 'null'.
ex.12b.ts(55,15): error TS2322: Type 'object & Record<"x", unknown>' is not assignable to type 'null'.
```

- ★★ **34행이 `string | number` 로 바뀐다** — 거짓 갈래에서 `null`·`undefined` 가 사라졌다.
- ★ 55행의 `object & Record<"x", unknown>` 은 **그대로**다. 교차를 만드는 쪽은 그 플래그와 무관하다.

4절의 파일도 갈린다.

```text
===== tsc --pretty false --noEmit --strict false ex.12d.ts (tsc exit=1) =====
ex.12d.ts(10,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(27,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(35,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(37,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12d.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(46,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12d.ts(54,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

- ★★★ **17행이 `string` 이다.** 클로저에서 좁히기가 풀리는 것은 **그대로인데**,\
  `v?: string` 이 플래그를 끄면 그냥 `string` 이라 **잃을 `undefined` 가 없다.**
- ★★ 즉 **플래그를 끄면 이 주제의 사고가 덜 보이는 것이지 없어지는 것이 아니다.** 런타임의 `undefined` 는 그대로 온다.

> **`strictNullChecks`** — `null`·`undefined` 를 **별도 타입으로 분리**하는 플래그. `strict` 에 딸려 7.0 기본 `true` 다.\
> 끄면 둘이 다른 타입에 **흡수**되어 좁히기가 할 일이 줄어든다([**04번 주제**](../04-any-unknown-never-void/)).

비용 — 끄면 진단이 줄지만 **버그가 줄지는 않는다.**

### (6) ★★★ 좁히기는 방출에 JS 연산자로 남는다

**언제 쓰나** — 「타입으로 갈랐으니 런타임에도 갈리겠지」를 의심할 때.

```ts
// ex.12e.ts
// 좁히기는 방출에 한 글자도 안 남는다 — 남는 것은 JS 연산자뿐이다
type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number };

class Dog {
    bark(): string {
        return "왈";
    }
}
class Cat {
    meow(): string {
        return "야옹";
    }
}

function describe(v: string | number | null): string {
    if (typeof v === "string") return `문자열 ${v.length}자`;
    if (typeof v === "number") return `숫자 ${v.toFixed(1)}`;
    return "null";
}

function area(s: Shape): number {
    if (s.kind === "circle") return 3 * s.r * s.r;
    return s.side * s.side;
}

function speak(p: Dog | Cat): string {
    if (p instanceof Dog) return p.bark();
    return p.meow();
}

console.log("describe  :", describe("abc"), "/", describe(4), "/", describe(null));
console.log("area      :", area({ kind: "circle", r: 2 }), "/", area({ kind: "square", side: 3 }));
console.log("speak     :", speak(new Dog()), "/", speak(new Cat()));
console.log("typeof null:", typeof null);
```

```text
===== tsc --pretty false ex.12e.ts (tsc exit=0) =====
===== 방출된 ex.12e.js =====
"use strict";
class Dog {
    bark() {
        return "왈";
    }
}
class Cat {
    meow() {
        return "야옹";
    }
}
function describe(v) {
    if (typeof v === "string")
        return `문자열 ${v.length}자`;
    if (typeof v === "number")
        return `숫자 ${v.toFixed(1)}`;
    return "null";
}
function area(s) {
    if (s.kind === "circle")
        return 3 * s.r * s.r;
    return s.side * s.side;
}
function speak(p) {
    if (p instanceof Dog)
        return p.bark();
    return p.meow();
}
console.log("describe  :", describe("abc"), "/", describe(4), "/", describe(null));
console.log("area      :", area({ kind: "circle", r: 2 }), "/", area({ kind: "square", side: 3 }));
console.log("speak     :", speak(new Dog()), "/", speak(new Cat()));
console.log("typeof null:", typeof null);
```

```text
===== node ex.12e.js (node exit=0) =====
describe  : 문자열 3자 / 숫자 4.0 / null
area      : 12 / 9
speak     : 왈 / 야옹
typeof null: object
```

그림 해설 — 한 단계에 한 문장.

- 방출된 파일에 `type Shape` 선언이 **통째로 없다.** `class Dog` 는 값이라 남는다.
- ★★★ 좁히기를 하는 코드는 **`typeof v === "string"` · `s.kind === "circle"` · `p instanceof Dog`** — **전부 JS 연산자**다.
- 즉 **좁히기를 가능하게 한 코드가 곧 런타임에 도는 코드**다. 타입은 그것을 **읽고 따라간** 것뿐이다.
- 실행 결과가 확인한다 — `문자열 3자` · `숫자 4.0` · `null` · `12` / `9` · `왈` / `야옹`.
- ★★★ 마지막 줄이 1절의 함정을 런타임에서 다시 보여 준다 — **`typeof null` 이 `object`** 다.
- ★ 그래서 **런타임에 확인할 수단이 없으면 좁힐 수도 없다.** 인터페이스를 `instanceof` 로 못 가르는 이유가 그것이다.

비용 — 0. 좁히기 자체는 **한 글자도 안 더한다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  typeof v === "string"                 원시 타입
  p instanceof Dog                      클래스
  "fly" in p                            프로퍼티 유무
  if (v)                                ★ 진릿값 — 거짓 갈래는 거의 안 줄어든다
  a === b                               ★ 양쪽을 동시에 좁힌다
  s.kind === "circle"                   판별 유니온
  const ok = typeof v === "string";     ★ 별칭 조건 (4.4) — const 만
  const exhaustive: never = s;          ★ 전수 검사 — 진단이 없으면 성공
```

**규칙 불릿**

- ★★★ **좁히기를 하는 것은 JS 연산자다.** 런타임에 확인할 수단이 없으면 좁힐 수 없다.
- ★★★ **`typeof null` 이 `"object"`** 라서 `typeof v === "object"` 분기에는 `null` 이 섞인다.
- ★★★ **진릿값의 거짓 갈래는 거의 안 줄어든다** — `""` 와 `0` 이 거짓이기 때문이다.
- ★★ **`in` 과 `instanceof` 가 `typeof` 의 구멍을 메운다** — 인터페이스는 `in`, 클래스는 `instanceof`.
- ★★ **조건을 `const` 에 담으면 좁혀지고 `let` 에 담으면 안 된다**(4.4 별칭 조건). **`typeof` 의 결과를 담은 `const` 는 안 된다.**
- ★★★ **클로저 안에서는 풀린다.** 함수 호출 뒤·인덱스·게터는 **안 풀린다**(안전선을 낮춘 자리다).
- ★★ **전수 검사는 `never` 대입이고, 성공하면 진단이 없다** — 「에러가 안 난 줄」이 답이다.
- ★★ **여러 검사를 `&&` 로 이으면 결과가 교차(`&`)로 합쳐진다**([**10번 주제**](../10-intersection-types/)).
- ★ **`strictNullChecks` 를 끄면 좁히기가 할 일이 줄어든다** — 진단이 줄 뿐 버그가 주는 것은 아니다.

**금지 사례** — 이 주제는 「막히는 것」보다 「**조용히 안 좁혀지는 것**」이 사고다. 셋을 나란히 둔다.

```text
1) const t = typeof v; if (t === "string")   ->  진단 없음. 안 좁혀진다     (1절 33행)
2) let ok = typeof v === "string"; if (ok)   ->  진단 없음. 안 좁혀진다     (3절 17행)
3) if (b.v) { () => b.v }                    ->  클로저 안에서 풀린다        (4절 17행)
```

## 어디서 틀리나

- ★★★ 「**`typeof v === "object"` 면 객체다**」 — **`null` 도 걸린다.** 1절 12행이 `object | null` 이라고 답한다.
- ★★★ 「**`if (v)` 의 `else` 에서는 `null`·`undefined` 만 남는다**」 — 아무것도 안 준다. 2절 34행이 **원래 타입 그대로**다.
- ★★★ 「**함수를 부르면 좁히기가 풀린다**」 — 이 판에서는 **안 풀린다**(4절 10행). 풀리는 것은 **클로저 안**이다.
- ★★ 「**`let` 에 조건을 담아도 되겠지**」 — 안 된다. 3절의 10행과 17행이 갈린다.
- ★★ 「**`const t = typeof v` 로 줄여 쓰면 편하겠지**」 — 그 순간 좁히기가 끊긴다(1절 33행).
- ★★ 「**`interface` 도 `instanceof` 로 가른다**」 — 못 가른다. **방출에 안 남으므로**(6절) `in` 을 쓴다.
- ★ 「**전수 검사는 진단이 나야 성공**」 — 반대다. **진단이 없어야 성공**이다(3절 36행).
- ★ 「**`strictNullChecks` 를 끄면 좁히기를 안 해도 된다**」 — 진단만 줄어든다. 런타임의 `undefined` 는 그대로 온다.
- ★ 「**게터는 부를 때마다 달라지니 안 좁혀지겠지**」 — 좁혀진다(4절 60행). **안전선이 낮은 자리**다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `typeof`·`instanceof`·`in`·진릿값·`===` 가 **분기 안에서 타입을 줄인다** | 핸드북 「Narrowing」. 1·2절의 탐침 스물한 개 |
| **언어 보장** | `typeof null === "object"` 라서 **그 분기에 `null` 이 섞인다** | 1절 12행 · 6절의 `node` 출력 마지막 줄 |
| **언어 보장** | 진릿값의 **거짓 갈래는 거의 안 줄어든다** | 2절 34행 |
| **언어 보장** | 조건을 **`const` 에 담아도 좁혀진다**(4.4) | 3절 10행 대 17행 |
| **언어 보장** | **전수 검사**는 `never` 대입이고 성공하면 침묵한다 | 1절 17행 · 3절 36행 |
| **언어 보장** | 좁히기는 **방출에 JS 연산자로** 남는다 | `ex.12e.js` 전문과 `node` 출력 |
| **★ 설정에 달림** | `null`·`undefined` 가 **분기에 남는가** | `strictNullChecks`. **네 파일 중 셋이 갈렸다** — 5절에 양쪽을 다 실었다 |
| **이 판(7.0.2)의 관찰** | ★★ **함수 호출 뒤에 프로퍼티 좁히기가 살아남는 것** | 편의를 위한 설계다. **안전 보장이 아니다** |
| **이 판의 관찰** | ★★ **인덱스 접근과 게터가 좁혀지는 것** | 같은 성질이다. 「믿어 준다」이지 「안전하다」가 아니다 |
| **이 판의 관찰** | 좁혀진 유니온을 진단이 찍을 때의 **멤버 순서** | 09 의 정렬과 같다. **대조 기준으로 쓰지 않는다** |
| **안 잰 것** | 분기가 많을 때의 **검사 시간** | 아래 「더 들어가면」을 보라 |

★ 「**에러가 안 난 줄」도 근거다** — 1절의 16·17·23행과 3절의 36행이 그렇다.
특히 **전수 검사는 침묵이 곧 성공**이라 진단 목록만 보면 아무것도 안 보인다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 원시 타입 유니온 — **`typeof`** | 객체끼리 가르기에 `typeof` — 전부 `"object"` 다 |
| 클래스 — **`instanceof`** | realm 이 다른 자리(iframe·워커)에 `instanceof` |
| 인터페이스·판별 칸 없는 객체 — **`in`** | 프로토타입에 같은 이름이 있는 객체에 `in` |
| 종류가 정해진 데이터 — **판별 유니온**([**09번 주제**](../09-union-types/)) | 판별 칸 없이 구조만으로 가르려는 시도 |
| 긴 조건에 이름 붙이기 — **`const` 별칭** | `let` 별칭 · `const t = typeof v` — 조용히 안 좁혀진다 |
| 클로저를 쓸 자리 — **먼저 `const` 지역 변수에 담기** | 클로저 안에서 프로퍼티를 다시 읽는 것 |
| 검사를 재사용 — **술어 함수**([**13번 주제**](../13-type-guards-and-predicates/)) | 같은 `in` 검사를 여러 곳에 흩뿌리는 것 |

## 핵심 문장

1. **좁히기를 하는 것은 JS 연산자다** — 런타임에 확인할 수단이 없으면 좁힐 수 없다.
2. **`typeof null` 이 `"object"`** 다 — 그 분기에는 `null` 이 섞인다.
3. **진릿값의 거짓 갈래는 거의 안 줄어든다** — `""` 와 `0` 때문이다.
4. **조건은 `const` 에 담아야 인정된다** — `let` 도, `typeof` 의 결과도 안 된다.
5. **클로저 안에서 풀린다** — 함수 호출·인덱스·게터에서는 안 풀린다(안전선이 낮은 자리다).
6. **전수 검사는 침묵이 성공**이다 — 진단 목록만 보면 안 보인다.
7. **`strictNullChecks` 를 끄면 이 주제의 절반이 조용해진다** — 버그가 아니라 진단이 주는 것이다.

## 관련 자료

- [**09번 주제** — 유니온 타입](../09-union-types/) — **판별 유니온**과 `never` 전수 검사는 그쪽에서 세웠다. 여기서는 **수단 전부**를 본다.
- [**13번 주제** — 타입 가드와 타입 술어](../13-type-guards-and-predicates/) — 이 수단들을 **함수로 포장**하는 법. **12 → 13 은 한 사슬**이다.
- [**10번 주제** — 인터섹션 타입](../10-intersection-types/) — 2절 55행의 `object & Record<"x", unknown>` 과 분배된 교차의 좁히기는 그쪽.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — `never` 의 성질과 `unknown` 을 받아 좁히는 설계는 그쪽.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — 판별 칸이 **리터럴 타입**이어야 하는 이유는 그쪽.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — 「같은 파일을 옵션만 바꿔 두 번 던진다」는 방식은 그쪽에서 세웠다.
- 목록의 **14번 주제**(단언 시그니처 `asserts`) — 좁힘을 **함수가 단언**하게 만드는 길.
- 목록의 **15번 주제**(제어 흐름 분석의 한계) — 4절의 전면 서술은 그쪽이다. 여기서는 **일곱 자리를 던져 본 것**까지.
- 목록의 **40번 주제**(`strictNullChecks` 의 파급) — 5절의 전면 서술은 그쪽.
- `../../js/syntax/README.md` 의 **01번 주제**(값의 종류와 `typeof`) — `typeof` 의 **런타임 의미는 JS 갈래가 정본**이다.

## 용어 풀이

> **좁히기(narrowing)** — 제어 흐름을 따라가며 그 자리에서 가능한 타입을 줄이는 것.\
> 예: `if (typeof v === "string")` 안에서 `string \| number` 가 `string` 이 된다.

> **타입 가드(type guard)** — 좁히기를 일으키는 검사. `typeof`·`instanceof`·`in`·진릿값·`===` 가 내장 가드다.\
> 직접 만드는 법은 [**13번 주제**](../13-type-guards-and-predicates/).

> **진릿값 좁히기(truthiness narrowing)** — `if (v)` 로 거짓 값을 걸러내는 것.\
> ★ **참 갈래만 좁아진다.**

> **별칭 조건(aliased condition)** — 검사 결과를 `const` 에 담아도 그 이름으로 좁힐 수 있게 한 기능(TS 4.4).\
> 예: `const ok = typeof v === "string";`. **`let` 에는 안 된다.**

> **전수 검사(exhaustiveness checking)** — 모든 갈래를 처리했는지 `never` 대입으로 확인하는 수법.\
> **진단이 없으면 성공**이다.

> **`strictNullChecks`** — `null`·`undefined` 를 별도 타입으로 분리하는 플래그. `strict` 에 딸려 7.0 기본 `true`.

## 더 들어가면

- **왜 클로저에서만 풀리나** — 클로저는 **나중에** 실행될 수 있고, 그 사이에 값이 바뀔 수 있다. 컴파일러는 「언제 불릴지 모르는 코드」에서는 좁힘을 못 믿는다. 반대로 같은 함수 안의 직선 코드는 순서가 정해져 있다.
- **왜 함수 호출 뒤에는 안 풀리나** — 풀면 실무 코드의 대부분이 에러가 난다. **편의를 위해 일부러 낮춘 안전선**이고, 실제로 `touch()` 가 `b.v` 를 지우면 런타임에 깨진다. 「보장」이 아니라 「믿어 준다」로 읽어야 한다.
- **`in` 의 함정** — `in` 은 프로토타입 체인까지 보는 JS 연산자다(`"toString" in obj`). **이 배치에서 던지지 않았으므로** 성질만 적어 둔다 — 판별 칸을 따로 두는 편이 안전하다([**09번 주제**](../09-union-types/)).
- **분기가 많을 때의 검사 시간** — 제어 흐름 분석은 분기마다 타입을 다시 계산한다. 이 배치에서는 **재지 않았다** — 목록의 **45번 주제**에서 잰다.
