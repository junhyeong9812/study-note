# ts/syntax/11 — 리터럴 타입과 `as const` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types: Literal Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types) ·
> [Handbook — Everyday Types: `const` assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-inference) ·
> [Handbook — Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로
> 이 블록들은 설정 파일 없이도 그대로 재현된다.
> **버전** — 리터럴 타입은 TS 2.0(문자열)·2.1(숫자·불리언), `as const` 는 3.4, 템플릿 리터럴 타입은 4.1 부터다.
> 7.0 은 템플릿 리터럴 타입의 **유니코드 코드 포인트 취급**을 바꿨다 — 이 문서는 ASCII 만 던졌다([목록의 **27번 주제**](../27-template-literal-types/)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**`.d.ts` 전문**·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★ `TS1355` 의 **허용 목록 문구** — 이 주제의 규칙을 통째로 읽어 준다 | 문구는 판마다 바뀔 수 있다. **코드가 더 오래 간다** |
| **흔들린다** | 템플릿 리터럴 타입이 펼쳐질 때의 **멤버 순서** | 09 에서 본 유니온 정렬과 같은 성질이다. **집합만 성질로 읽는다** |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제에도 「**에러가 안 난 줄**」이 근거인 자리가 있다 — 3절의 11\~16행이 그렇다.
> 그래서 **모든 진단 블록 옆에 소스 전문**을 뒀다.
> ★★★ 템플릿 리터럴 타입은 **타입 이름에 백틱이 들어간다.** 본문에서는 겹백틱으로 적었다 — 예: `` `--${string}` ``.

## 한눈에 — 쉽게 말하면

**리터럴 타입은 「값 하나만 허용하는 타입」이고, 넓히기는 그것을 놓치는 기본 동작이다.**

| 비유 | 실체 |
|---|---|
| 「이 칸에는 **`"circle"` 만**」 | **리터럴 타입** — 값 하나가 곧 타입이다 |
| 상자를 봉해 두면 안의 물건이 그대로 | **`const`** — 리터럴이 고정된다 |
| 뚜껑이 열리는 상자면 「**그 종류의 아무 것**」으로 적어 둔다 | **`let`·`var`** — `string` 으로 **넓어진다** |
| ★ 상자 안의 **작은 칸들은 여전히 열린다** | `const obj = { a: 1 }` 의 `a` 는 **`number`** 다 |
| 통째로 봉인 테이프를 붙인다 | **`as const`** — 리터럴 고정 + `readonly` + 배열을 **튜플**로 |
| 테이프는 **종이에만** 붙는다 | `as const` 는 **리터럴 식에만** 붙는다(`TS1355`) |
| ★ 테이프는 **배송 중에 떨어진다** | 방출된 JS 에 **한 글자도 안 남는다** — `Object.isFrozen` 이 `false` |

- ★★★ 한 줄로 — 「**넓히기는 기본값이고, `as const` 는 그 기본값을 끄는 스위치다. 다만 런타임에는 아무것도 안 한다.**」
- ★★ 그리고 `as const` 는 **한 가지가 아니라 세 가지**를 동시에 한다 — 그 셋을 따로 셀 수 있어야 한다.

```text
  넓히기 — 어디서 일어나나

  const cStr = "circle"        ->  "circle"     ★ 고정
  let   lStr = "circle"        ->  string       ★ 넓어진다
  var   vStr = "circle"        ->  string       ★ 넓어진다
  const obj  = { a: 1 }        ->  { a: number } ★ 프로퍼티는 넓어진다
  const arr  = [1, 2, 3]       ->  number[]     ★ 배열도 넓어진다
  const annotated: "circle"    ->  "circle"     주석이 막는다
```

```text
  as const 가 한꺼번에 하는 세 가지

  { mode: "dark", retries: 3, list: [1, 2] } as const
        │
        ├─① 리터럴 고정   mode: "dark"   (string 이 아니라)
        ├─② readonly      readonly mode  (재대입 금지)
        └─③ 배열→튜플     readonly [1, 2] (number[] 가 아니라)
                │
                ▼  ★ 방출된 JS 에는 셋 다 흔적이 없다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어디서 넓어지나** — `const`·`let`·객체 프로퍼티·배열을 **탐침으로 전수 확인**한다.
2. **`as const` 가 정확히 무엇을 바꾸나** — 셋을 따로 세고, **안 되는 자리**의 에러 전문을 읽는다.
3. **런타임에는 무엇이 남나** — 방출된 `.js` 와 `Object.isFrozen` 으로 확인한다.

★ [**03번 주제**](../03-basic-type-annotations/)가 「추론에 맡길 자리와 명시할 자리」를 세웠다면, 여기는 **추론이 기본으로 넓히는 자리**를 전수로 짚는다.
[**09번 주제**](../09-union-types/)의 「리터럴이 기반 타입에 흡수된다」와는 **다른 일**이다 — 11번 질문에서 가른다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`null` 탐침** | **넓어진 타입인지 리터럴인지**를 글자로 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| ★★ **`.d.ts` 덤프** | 「적은 것」과 「추론된 것」이 값 선언에서 갈리는 자리 | [**09번 주제**](../09-union-types/)에서 이어받음 |
| ★★★ **방출 `.js` + `node`** | `as const` 가 **런타임에 아무것도 안 하는 것** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

비용 — 컴파일 한 번.

### (1) ★★★ 넓히기는 기본값이다

**언제 쓰나** — 「분명히 `"circle"` 이라고 적었는데 왜 `string` 이라고 하지」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **열네 건**이다 — 탐침 열세 개가 전부 답했고, 31행 재대입이 하나 더 났다.
- 17행 `const cStr` 은 **`"circle"`** 이다 — `const` 는 **리터럴을 고정**한다.
- ★★★ 18행 `let lStr` 은 **`string`** 이다. 같은 초기값인데 **선언 키워드가 타입을 바꾼다.**
- 19·20행이 숫자로 같은 일을 확인한다 — `const cNum` 은 **`1`**, `let lNum` 은 **`number`**.
- 21행 `const cBool` 은 **`true`** 다 — 불리언도 리터럴 타입이 있다.
- 22행 `var vStr` 은 **`string`** 이다 — `var` 는 `let` 과 같은 쪽이다.
- ★★★ 23·24행이 가장 자주 걸리는 자리다. `const obj = { a: 1, s: "circle", b: true }` 가\
  **`{ a: number; s: string; b: boolean; }`** 이다. **`const` 는 변수만 고정하고 프로퍼티는 못 고정한다.**
- 25·26행 — 배열도 같다. `[1, 2, 3]` 은 **`number[]`**, `["a", 1]` 은 **`(string | number)[]`** 다(09 의 유니온이 여기서 나온다).
- ★ 27·28행 — **타입 주석을 적으면 `let` 도 리터럴로 남는다**(`lAnnotated` 가 `"circle"`). 31행이 그것을 확인한다 — 재대입이 `TS2322` 로 막힌다.
- ★ 29행 `String("circle")` 은 **`string`** 이다 — 함수 반환은 리터럴이 아니다.

> **리터럴 타입(literal type)** — 값 하나만 허용하는 타입.\
> 예: `"circle"` · `1` · `true`. 유니온과 묶어 `"up" | "down"` 처럼 쓴다.

> **넓히기(widening)** — 리터럴 타입을 그 **기반 타입**으로 올려 추론하는 기본 동작.\
> 예: `let x = "circle"` 의 `x` 가 `string` 이 된다.

비용 — 없음. 다만 **어디서 넓어지는지 외우지 말고 탐침으로 물어라** — 자리가 다섯 곳이다.

### (2) ★★★ `as const` 는 한꺼번에 세 가지를 한다

**언제 쓰나** — 설정 객체·상수 테이블을 리터럴로 고정하고 싶을 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **열다섯 건**이다 — 탐침 열한 개 + 24\~27행 네 건.
- ★★★ 5행과 6행을 나란히 읽어라. 같은 리터럴인데 —\
  `plain` 은 **`{ mode: string; retries: number; deep: { x: number; }; list: number[]; }`**,\
  `frozen` 은 **`{ readonly mode: "dark"; readonly retries: 3; readonly deep: { readonly x: 1; }; readonly list: readonly [1, 2]; }`** 다.
- ★★ 그 한 줄에 **세 가지**가 다 들어 있다 — ①`"dark"`·`3` 으로 **리터럴 고정** ②`readonly` **전부 붙음** ③`list` 가 **`readonly [1, 2]` 튜플**.
- 7·8행 — **깊이 들어간다.** `frozen.deep` 도 `frozen.list` 도 안쪽까지 얼었다.
- ★★ 12·13행 — `plainArr` 는 `number[]` 인데 `frozenArr` 는 **`readonly [1, 2, 3]`** 이다.\
  「`readonly number[]`」가 **아니다** — **길이와 각 칸의 값까지 고정된 튜플**이다.
- ★ 16행 — `let lFrozen = "circle" as const` 도 **`"circle"`** 이다. `as const` 는 `let` 의 넓히기도 막는다.\
  다만 27행이 보여 주듯 **재대입 자체는 `let` 이라 가능해야 하는데** 타입이 `"circle"` 이라 `TS2322` 로 막힌다.
- ★★ 21·22행이 경계다 — `{ a: n } as const` 는 **`{ readonly a: number }`** 다.\
  **`readonly` 는 붙지만 `n` 이 리터럴이 아니라 고정할 것이 없다.** `as const` 가 값을 리터럴로 만들어 주지는 않는다.
- 24·25·26행 — `TS2540`(프로퍼티) · `TS2540`(인덱스) · `TS2339`(`push` 가 없다). **`readonly` 튜플에는 `push` 자체가 없다.**
- ★★★ 30·32행이 실무의 함정이다 — 복사하면 **잃는다.** `[...frozenArr]` 는 **`(1 | 2 | 3)[]`**(튜플도 `readonly` 도 잃고 리터럴만 남는다),\
  `{ ...frozen }.mode` 는 **`"dark"`**(리터럴은 남고 `readonly` 는 잃는다).

> **`as const`(const 단언)** — 리터럴 식의 추론을 **넓히지 않고** 그대로 굳히는 단언(TS 3.4).\
> 예: `{ mode: "dark" } as const`. 리터럴 고정 · `readonly` · 배열을 튜플로 — **셋을 한꺼번에** 한다.

비용 — **사본에는 안 따라간다.** 스프레드로 복사하면 일부를 잃는다.

### (3) ★★ `as const` 가 안 되는 자리 — 에러가 규칙을 통째로 읽어 준다

**언제 쓰나** — 「왜 여기엔 `as const` 를 못 붙이지」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **열한 건**이고 그중 `TS1355` 가 **네 건**(6·7·8·9행)이다. **11\~16행은 전부 통과했다.**
- ★★★ `TS1355` 의 문구가 허용 목록을 통째로 읽어 준다 —\
  「A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.」
- 6행 `n as const` — `n` 은 `declare const n: number` 다. **`const` 변수여도 리터럴 식이 아니면 막힌다.**
- 7행 `(1 + 2) as const` — **계산식은 리터럴이 아니다.**
- 8행 `(() => 1) as const` — 함수 식도 아니다.
- 9행 `v as const` — `let v = 1` 을 가리키는 참조도 아니다.
- ★★ 11행 `-1 as const` 는 **통과한다.** 숫자 리터럴 앞의 단항 부호는 리터럴의 일부로 친다 — **23행이 `-1` 이라고 답한다.**
- 12·14행 — 치환이 없는 템플릿(`` `a` ``)은 **`"a"`**, 상수만 넣은 것(`` `a${1}` ``)은 **`"a1"`** 이다. **컴파일 시각에 이어 붙는다.**
- ★★★ 13행이 이 절의 별이다 — `` `a${s}` as const `` 가 **`` `a${string}` ``** 이다.\
  값이 안 정해진 조각은 **템플릿 리터럴 타입**으로 남는다(다음 절).
- 15·16행 — `{ a: n } as const` 와 `[n] as const` 는 통과하고 **`{ readonly a: number }`·`readonly [number]`** 가 된다.\
  **객체·배열 리터럴 「껍데기」가 리터럴이면 되고, 안의 값은 리터럴이 아니어도 된다.**
- ★ 21행 `E.X as const` 도 통과하고 **`E`** 로 답한다 — 허용 목록의 「references to enum members」다.

> **`TS1355`** — `as const` 를 리터럴이 아닌 식에 붙였을 때의 진단.\
> 붙일 수 있는 것: **enum 멤버 참조 · 문자열·숫자·불리언 리터럴 · 배열 리터럴 · 객체 리터럴**.

비용 — 없음. 다만 **계산된 값을 리터럴로 굳히는 길은 없다** — 그것이 다음 절의 템플릿 리터럴 타입으로 이어진다.

### (4) ★★ 템플릿 리터럴 타입 — 리터럴 유니온이 곱해진다

**언제 쓰나** — 문자열 **패턴**을 타입으로 적고 싶을 때. 이 절은 **맛보기**다(전면 서술은 [목록의 **27번 주제**](../27-template-literal-types/)).

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **여덟 건**이다. `okHandler`·`okCss`·`okPair`(15·17·19행)는 **통과했다.**
- ★★ 11행 — `` `on${Capitalize<Dir>}` `` 가 **`"onDown" | "onUp"`** 으로 **펼쳐진다.** 리터럴 유니온을 넣으면 **각 멤버마다** 만들어진다.
- ★★★ 13행 — `` `${Dir}-${Dir}` `` 는 **`"down-down" | "down-up" | "up-down" | "up-up"`** 이다. **곱해진다**(2 × 2 = 4).
- 12행 — `` `--${string}` `` 는 **안 펼쳐진다.** `string` 이 무한하니 **패턴 그대로** 남는다.
- ★ 16행만 `TS2820` 이다 — 「Did you mean '"onUp"'?」 **오타 후보를 짚어 준다.** 유한한 리터럴 유니온이라 가능한 일이다.
- 18·20행은 평범한 `TS2322` 다 — `"brand"` 는 `` `--${string}` `` 패턴에 안 맞고, `"up-left"` 는 네 값 중에 없다.
- ★★ 24행 — 3절에서 본 `` `on${s}` as const `` 가 **`` `on${string}` ``** 이다. **값에서 타입 패턴이 나왔다.**
- ★ 25행이 그 한계를 보여 준다 — `` `on${string}` `` 을 `` `--${string}` `` 자리에 넣으면 `TS2322` 다. **패턴끼리도 대조한다.**

```text
  type Dir = "up" | "down"

  `on${Capitalize<Dir>}`   ->  "onDown" | "onUp"                     2개
  `${Dir}-${Dir}`          ->  "down-down" | "down-up" |
                               "up-down" | "up-up"                    4개  ★ 곱해진다
  `--${string}`            ->  `--${string}`                          펼칠 수 없다
```

> **템플릿 리터럴 타입(template literal type)** — 문자열 패턴을 타입으로 적는 문법(TS 4.1).\
> 예: `` `--${string}` `` · `` `on${Capitalize<Dir>}` ``. 리터럴 유니온을 넣으면 **각 조합으로 펼쳐진다.**

비용 — ★★ **조합이 곱으로 는다.** 조각이 셋만 돼도 멤버가 수백 개가 된다 — 검사 시간이 여기서 샌다([목록의 **45번 주제**](../45-type-level-performance/)).

### (5) ★★★ 방출에는 한 글자도 안 남는다

**언제 쓰나** — 「`as const` 니까 런타임에도 못 바꾸겠지」를 의심할 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 방출된 파일에 `as const` 가 **한 번도 안 나온다.** `const dir = "up";` · `const conf = { mode: "dark", retries: 3 };` 뿐이다.
- `type Dir` 선언도 통째로 없다 — `"use strict";` 다음이 곧장 `const dir = "up";` 이다.
- ★★ `Object.freeze` 같은 것도 **안 넣어 준다.** 실행 결과의 마지막 줄이 **`false false`** 다.
- ★★★ `escaped.push(9)` 가 런타임에 **그냥 된다** — `push 뒤 : 1,2,3,9`. `readonly` 는 **타입 검사기 안에서만** 산다([**07번 주제**](../07-object-type-details/)).
- ★ 그 줄이 `as unknown as number[]` 라는 **두 단 단언**을 거친 것에 주의하라. 단언 없이 `push` 를 부르면 `TS2339` 로 막힌다(2절의 26행).\
  **막는 것은 타입이고, 막지 못하는 것은 런타임이다.**
- `move(dir)` 이 통과한 것이 리터럴 고정의 값이다 — `dir` 이 `string` 이었다면 `"up" | "down"` 자리에 못 들어간다.

비용 — 0. 방출에 한 글자도 안 남는다. **안전은 전부 컴파일 시각에만 있다.**

### (6) ★★ 선언 방출은 값 쪽 추론 결과를 적는다

**언제 쓰나** — 라이브러리 소비자가 볼 계약이 무엇인지 확인할 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★ `export const cStr = "circle"` 이 **`export declare const cStr = "circle";`** 로 나온다 — **`:` 가 아니라 `=` 다.**\
  값이 리터럴 하나로 고정됐다는 뜻이다.
- `export let lStr` 은 **`: string`** 이다 — 넓어진 결과가 그대로 실린다.
- ★★★ `frozen` 이 **`readonly` 까지 포함한 전문**으로 풀려 나온다. `plain` 은 `{ mode: string; retries: number; }` 다.\
  **1절·2절의 탐침 결과가 `.d.ts` 에도 그대로 적힌다** — 값 선언은 「추론 결과」를 적기 때문이다.
- `frozenArr` 는 **`readonly [1, 2, 3]`**, `plainArr` 는 `number[]` 다.
- ★★★ 그런데 **타입 별칭은 다르다.** `Handler` 가 **`` `on${Capitalize<"up" | "down">}` ``** 로 **적은 그대로** 나온다 —\
  4절의 탐침은 **`"onDown" | "onUp"`** 이라고 답했다. **같은 선언이 두 창에서 다르게 보인다**([**09번 주제**](../09-union-types/)·[**10번 주제**](../10-intersection-types/)).
- ★ `export const picked: "a" | "b" = "a"` 는 주석을 적었으니 **그대로 보존**된다.

비용 — 없음. 두 창을 **같이** 써야 답이 온전해진다.

### (7) ★ `strict` 를 꺼도 답이 같다

**언제 쓰나** — 「이 결과가 `strict` 덕분 아닌가」를 의심할 때.

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.11a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.11b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.11c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.11d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★★ 네 파일이 **종료 코드도 출력도 글자 하나까지 같다.** 넓히기와 `as const` 는 **`strict` 묶음과 무관**하다.
- ★ 그래서 이 문서에도 **「설정에 달린 칸」이 0개**다. [**10번 주제**](../10-intersection-types/)와 같다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  const cStr = "circle"              -> "circle"     ★ 고정
  let   lStr = "circle"              -> string       ★ 넓어진다
  const obj  = { a: 1 }              -> { a: number } ★ 프로퍼티는 넓어진다
  const annotated: "circle" = "circle"               주석이 막는다

  { mode: "dark" } as const          -> { readonly mode: "dark" }
  [1, 2, 3] as const                 -> readonly [1, 2, 3]   ★ 튜플
  `a${s}` as const                   -> `a${string}`         ★ 템플릿 리터럴 타입

  type Handler = `on${Capitalize<Dir>}`              패턴을 타입으로
  type Pair    = `${Dir}-${Dir}`                     ★ 조합이 곱해진다
```

**규칙 불릿**

- ★★★ **넓히기는 기본값이다** — `let`·`var`·**객체 프로퍼티**·**배열 요소**에서 일어난다. `const` 변수 하나만 고정된다.
- ★★★ **`as const` 는 세 가지를 한꺼번에** 한다 — 리터럴 고정 · `readonly` · 배열을 **튜플**로. 안쪽까지 재귀로 간다.
- ★★ **`as const` 가 값을 리터럴로 만들지는 않는다** — `{ a: n } as const` 는 `{ readonly a: number }` 다.
- ★★ **`as const` 는 리터럴 식에만 붙는다**(`TS1355`). 허용 목록: enum 멤버 참조 · 문자열·숫자·불리언 리터럴 · 배열 리터럴 · 객체 리터럴.
- ★★ **사본은 잃는다** — `[...frozenArr]` 는 `(1 | 2 | 3)[]`, `{ ...frozen }` 은 `readonly` 를 잃는다.
- ★★ **템플릿 리터럴 타입은 리터럴 유니온을 곱한다.** `string` 을 넣으면 펼치지 않고 패턴으로 남는다.
- ★★★ **방출에 한 글자도 안 남는다.** `Object.isFrozen` 이 `false` 이고 `push` 가 런타임에 그냥 된다.
- ★ **`.d.ts` 는 값 선언의 추론 결과를 적고, 타입 별칭의 표기는 그대로 옮긴다** — 한 파일 안에서 두 규칙이 같이 돈다.

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 리터럴이 아닌 식에 as const   ->  TS1355  A 'const' assertion can only be applied to references to
                                             enum members, or string, number, boolean, array, or object literals.
2) readonly 프로퍼티에 대입       ->  TS2540  Cannot assign to 'retries' because it is a read-only property.
3) readonly 튜플에 push           ->  TS2339  Property 'push' does not exist on type 'readonly [1, 2, 3]'.
4) 패턴에 안 맞는 문자열          ->  TS2820  Type '"onup"' is not assignable to type '"onDown" | "onUp"'. Did you mean '"onUp"'?
```

## 어디서 틀리나

- ★★★ 「**`const` 로 선언했으니 안이 다 고정된다**」 — 변수만 고정된다. `const obj = { a: 1 }` 의 `obj.a` 는 **`number`** 다.
- ★★★ 「**`as const` 를 붙이면 런타임에도 못 바꾼다**」 — `Object.isFrozen` 이 **`false`** 다. 방출에 한 글자도 안 남는다.
- ★★ 「**`[1,2,3] as const` 는 `readonly number[]`**」 — **`readonly [1, 2, 3]`** 이다. **길이와 각 칸의 값까지** 고정된 튜플이다.
- ★★ 「**`as const` 로 복사본도 고정된다**」 — 스프레드는 잃는다. `[...frozenArr]` 는 `(1 | 2 | 3)[]` 다.
- ★★ 「**`{ a: n } as const` 면 `a` 가 리터럴**」 — `n` 이 리터럴이 아니면 **고정할 것이 없다.** `readonly` 만 붙는다.
- ★★ 「**`as const` 는 아무 식에나 붙는다**」 — `TS1355` 다. `(1 + 2)` 도 `n` 도 막힌다.
- ★ 「**`let x = "a" as const` 는 `let` 이라 넓어진다**」 — 안 넓어진다. **`"a"`** 이고, 그래서 재대입이 막힌다.
- ★ 「**템플릿 리터럴 타입은 그냥 문자열**」 — 유한한 유니온이면 **펼쳐지고 오타 후보까지 짚어 준다**(`TS2820`).
- ★ 「**`.d.ts` 를 보면 계산된 타입을 알 수 있다**」 — **값 선언은 그렇고 타입 별칭은 아니다.** `Handler` 가 적은 그대로 나온다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `const` 는 리터럴을 고정하고 `let`·`var`·프로퍼티·배열 요소는 **넓어진다** | 핸드북 「Literal Inference」. `ex.11a.ts` 의 탐침 열세 개 |
| **언어 보장** | `as const` 는 **리터럴 고정 · `readonly` · 배열을 튜플로**, 안쪽까지 | `frozen` 의 타입 전문(2절 6행) |
| **언어 보장** | `as const` 는 **리터럴 식에만** 붙는다 | `TS1355` 의 문구가 허용 목록 자체다 |
| **언어 보장** | 템플릿 리터럴 타입은 **리터럴 유니온을 조합으로 펼친다** | `Pair` 가 네 멤버(4절 13행) |
| **언어 보장** | 리터럴·`readonly`·튜플은 **방출에 안 남는다** | `ex.11e.js` 전문 · `Object.isFrozen` 이 `false` |
| **설정에 달림** | ★ **없다** | 네 파일을 `--strict false` 로 다시 던져 **종료 코드와 출력이 전부 같은 것**을 확인했다((7)절) |
| **이 판(7.0.2)의 관찰** | ★★ 펼쳐진 템플릿 리터럴 유니온의 **멤버 순서**(`"onDown" \| "onUp"`) | 09 의 유니온 정렬과 같다. **대조 기준으로 쓰지 않는다** |
| **이 판의 관찰** | `TS2820` 이 **오타 후보를 고르는 방식** | 보고기의 구현이다. 코드가 `TS2820` 이라는 것만 성질로 읽는다 |
| **이 판의 관찰** | `.d.ts` 가 객체 타입을 **여러 줄로 펼쳐 적는 것** | 선언 방출기의 서식이다 |
| **안 잰 것** | 템플릿 리터럴 조합이 커질 때의 **검사 시간** | 아래 「더 들어가면」을 보라 |

★ 「**에러가 안 난 줄」도 근거다** — 3절의 11\~16행이 통째로 그렇다. **`TS1355` 가 안 난 여섯 줄**이 허용 목록의 실증이다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 설정·상수 테이블을 **통째로** 고정 — `{ … } as const` | 런타임 불변을 기대하는 자리 — `Object.freeze` 가 필요하다 |
| 문자열 유니온의 값 목록 — `["up","down"] as const` | 계산된 값을 고정하려는 시도 — `TS1355` 로 막힌다 |
| 함수 인자로 넘길 리터럴 — `move(dir)` 이 통과하게 | 자주 바뀌는 객체 — `readonly` 가 거추장스러워진다 |
| 패턴이 있는 문자열 키 — `` `--${string}` `` | 조각이 셋 이상인 템플릿 조합 — 멤버가 곱으로 는다 |
| 값 하나만 고정하면 될 때 — **타입 주석**(`: "circle"`) | 타입까지 좁히고 싶은데 주석을 쓰는 것 — [목록의 **29번 주제**](../29-satisfies/)(`satisfies`)를 본다 |

## 핵심 문장

1. **넓히기가 기본값이다** — `const` 변수 하나만 고정되고 프로퍼티·배열 요소는 넓어진다.
2. **`as const` 는 세 가지를 한꺼번에 한다** — 리터럴 고정 · `readonly` · 배열을 튜플로.
3. **`as const` 가 값을 리터럴로 만들지는 않는다** — 고정할 리터럴이 있어야 고정된다.
4. **`as const` 는 리터럴 식에만 붙는다** — `TS1355` 의 문구가 곧 규칙이다.
5. **사본은 잃는다** — 스프레드로 복사하면 튜플성과 `readonly` 가 빠진다.
6. **템플릿 리터럴 타입은 조합을 곱한다** — `string` 이 섞이면 패턴으로 남는다.
7. **방출에 한 글자도 안 남는다** — `Object.isFrozen` 이 `false` 이고 `push` 가 그냥 된다.

## 관련 자료

- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — 「추론에 맡길 자리와 명시할 자리」는 그쪽. `null` 탐침도 그쪽에서 세웠다.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — **`readonly` 가 런타임을 못 막는다**는 것은 그쪽이 정본이다. 5절이 그것을 다시 확인한다.
- [**09번 주제** — 유니온 타입](../09-union-types/) — `"x" | "y" | string` 의 **리터럴 흡수**는 그쪽. 이 주제의 **넓히기**와는 다른 일이다.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — `satisfies` 가 그 검사를 **안 끈다**는 실측은 그쪽.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「방출에 안 남는다」의 근거는 그쪽.
- [**12번 주제** — 좁히기](../12-narrowing/) — 리터럴 유니온을 `===` 로 가르는 것은 그쪽.
- [목록의 **23번 주제**](../23-typeof-type-operator/)(`typeof` 타입 연산자) — `as const` 로 굳힌 값에서 타입을 끌어오는 `typeof conf` 관용구는 그쪽.
- [목록의 **27번 주제**](../27-template-literal-types/)(템플릿 리터럴 타입) — 4절은 **맛보기**다. `Capitalize` 계열과 7.0 의 유니코드 변경은 그쪽.
- [목록의 **29번 주제**](../29-satisfies/)(`satisfies`) — 「검사는 받고 추론은 넓히지 않는다」의 전면 서술은 그쪽. 9번 질문이 그 자리를 비워 둔다.
- [목록의 **31번 주제**](../31-enum-pitfalls/)(열거형의 함정) — `as const` 객체가 enum 의 대안이 되는 자리는 그쪽.

## 용어 풀이

> **리터럴 타입(literal type)** — 값 하나만 허용하는 타입.\
> 예: `"circle"` · `1` · `true`.

> **넓히기(widening)** — 리터럴 타입을 기반 타입으로 올려 추론하는 기본 동작.\
> 예: `let x = "circle"` 의 `x` 가 `string` 이 된다.

> **`as const`(const 단언)** — 리터럴 식의 추론을 넓히지 않고 굳히는 단언(TS 3.4).\
> 예: `[1, 2, 3] as const` 가 `readonly [1, 2, 3]` 이 된다.

> **튜플(tuple)** — 길이가 정해지고 칸마다 타입이 다를 수 있는 배열 타입.\
> 예: `readonly [1, 2, 3]`. `number[]` 와 달리 **길이가 타입의 일부**다.

> **템플릿 리터럴 타입(template literal type)** — 문자열 패턴을 타입으로 적는 문법(TS 4.1).\
> 예: `` `--${string}` ``.

> **`TS1355`** — `as const` 를 리터럴이 아닌 식에 붙였을 때의 진단.\
> 허용 목록: enum 멤버 참조 · 문자열·숫자·불리언 리터럴 · 배열 리터럴 · 객체 리터럴.

## 더 들어가면

- **왜 `let` 만 넓어지나** — `let` 은 재대입될 수 있으니 「이 변수가 앞으로 가질 값」을 적어야 한다. `const` 는 그 값 하나로 끝난다. **넓히기는 재대입 가능성의 그림자**다.
- **`as const` 대 `satisfies`** — `as const` 는 **추론을 굳히고**, `satisfies` 는 **검사만 하고 추론을 살린다.** 둘을 같이 쓰는 관용구도 있다. [목록의 **29번 주제**](../29-satisfies/)에서 던진다 — 여기서는 **형태도 적지 않았다.**
- **`as const` 로 enum 을 대신하기** — `const Color = { Red: "red" } as const` 와 `typeof Color[keyof typeof Color]` 조합. [목록의 **23번**](../23-typeof-type-operator/)·**31번 주제**와 엮인다. 이 배치에서는 **안 던졌다.**
- **템플릿 리터럴 조합의 비용** — `` `${A}-${B}-${C}` `` 처럼 조각이 늘면 멤버가 곱으로 는다. 이 배치에서는 **재지 않았다** — [목록의 **45번 주제**](../45-type-level-performance/)에서 잰다.
