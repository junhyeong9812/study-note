# ts/syntax/08 — `interface` 대 `type` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types: Differences Between Type Aliases and Interfaces](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#differences-between-type-aliases-and-interfaces) ·
> [Handbook — Object Types: Extending Types](https://www.typescriptlang.org/docs/handbook/2/objects.html#extending-types) ·
> [Handbook — Declaration Merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html) ·
> [TSConfig — `declaration`](https://www.typescriptlang.org/tsconfig/#declaration).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문·방출 전문은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**한다.
> ★★ 「어느 쪽이 빠른가」는 **이 배치에서 재지 않았다** — 재는 방법 자체가 전제를 요구한다(맨 아래 「안 잰 것」).
> **버전** — `interface` 와 선언 병합은 TS 1.0, `type` 별칭의 객체 타입은 1.0, **별칭의 재귀 참조는 3.7** 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**`.d.ts` 전문**·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | `TS2739` 가 나열하는 **프로퍼티 순서**(`d, a, b, c`) | 선언 순서를 따른다 — 이 판에서 재실행해도 같았다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **안 잰 것** | 검사 **속도** | 잴 방법이 전제를 요구한다. 아래 「더 들어가면」에 그 이유를 적었다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 한눈에 — 쉽게 말하면

**`interface` 는 계속 덧붙일 수 있는 게시판이고, `type` 은 한 번 붙이고 끝인 라벨이다.**

| 비유 | 실체 |
|---|---|
| 같은 게시판에 쪽지를 계속 붙인다 | **`interface` 는 선언 병합** — 같은 이름을 몇 번이든 쓸 수 있다 |
| 같은 자리에 라벨을 두 번 붙이면 거절당한다 | **`type` 은 중복 선언 불가** — `TS2300` |
| 게시판은 **쪽지끼리 안 맞으면 즉시 지적**한다 | `extends` 충돌 → `TS2430` · 병합 충돌 → `TS2717` |
| 라벨을 겹쳐 붙이면 **겹친 부분이 안 읽힌다** | 교차(`&`)의 충돌은 **조용히 `never`** 가 된다 |
| ★ 게시판은 「이 밖의 칸」을 약속 안 한다 | **`interface` 에는 암묵 인덱스 시그니처가 없다** — `Record` 자리에 못 들어간다 |
| 라벨은 아무것에나 붙는다 | **`type` 은 유니온·원시·튜플·조건부·매핑을 다 적는다** |
| 둘 다 **인쇄물에는 안 나온다** | 방출된 `.js` 에 한 글자도 안 남는다 |

- ★★★ 한 줄로 — 「**`interface` 는 열려 있고 `type` 은 닫혀 있다. 그 차이가 병합·충돌 보고·암묵 인덱스 시그니처에서 드러난다.**」
- ★★ 그래서 고르는 기준은 취향이 아니라 「**나중에 누가 덧붙일 것인가**」와 「**객체 말고 다른 것을 적어야 하나**」다.

```text
  interface Merged { a }        type Aliased = { a }
  interface Merged { b }        type Aliased = { b }
       │                             │
       ▼                             ▼
   하나로 합쳐진다               TS2300 Duplicate identifier
   { a; b }                      (두 줄 다 진단이 난다)
```

```text
  충돌을 만났을 때 — 말하나 침묵하나

  interface Extended extends Base { p: number }      ← Base 는 p: string
        ▼
     TS2430  Interface 'Extended' incorrectly extends interface 'Base'.
       Types of property 'p' are incompatible.          ★ 선언 자리에서 막는다

  type Crossed = { p: string } & { p: number }
        ▼
     (진단 없음)  ...  c.p 의 타입은 never
        ▼
     const putBack: Crossed = { p: "x" }   ->  TS2322 … not assignable to type 'never'
                                               ★ 훨씬 뒤에, 엉뚱한 자리에서 터진다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **무엇이 실제로 다른가** — 「거의 같다」로 뭉개지 말고, **던져서 갈리는 칸**을 전수로 센다.
2. **충돌을 만났을 때 어느 쪽이 더 일찍 말하나** — `extends` 와 교차(`&`)가 같은 실수에 어떻게 반응하나.
3. **그래서 무엇을 기준으로 고르나** — 취향이 아니라 **덧붙일 여지**와 **적어야 할 모양**으로 가른다.

★ [**07번 주제**](../07-object-type-details/)가 「객체 타입 안에 무엇을 적나」를 세웠다면, 여기는 **그 객체 타입을 어느 문법으로 적나**를 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **에러 코드가 나는가 안 나는가** | 같은 실수에 **한쪽만 말한다** | ★ 이 주제의 고유 창 |
| ★★ **진단의 모양(한 줄 대 중첩 줄)** | 같은 내용을 **다르게 보고**한다 | ★ 이 주제의 고유 창 |
| ★★ **`null` 탐침** | 교차가 만든 `never` 를 **글자로** 확인 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| **`.d.ts` + 방출된 `.js`** | 선언 방출에서만 갈리고 **`.js` 에는 둘 다 안 남는다** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

★ **「진단이 안 나는 것」이 이 주제에서 가장 센 근거다** — 교차의 충돌이 그렇다.

비용 — 컴파일 한 번.

### (1) ★★★ 같은 이름을 두 번 — 병합과 중복

**언제 쓰나** — 남의 타입에 칸을 덧붙여야 할 때.

```ts
// ex.08a.ts
// 같은 이름을 두 번 선언하면 — 한쪽은 합쳐지고 한쪽은 막힌다
interface Merged {
    a: number;
}
interface Merged {
    b: string;
}
interface Merged {
    run(): void;
}
const m: Merged = { a: 1, b: "x", run() {} };

type Aliased = {
    a: number;
};
type Aliased = {
    b: string;
};

interface Clashing {
    p: number;
}
interface Clashing {
    p: string;
}

interface Overloaded {
    (x: number): string;
}
interface Overloaded {
    (x: string): string;
}
declare const ov: Overloaded;
console.log(m, ov(1), ov("s"));
```

```text
===== tsc --pretty false --noEmit ex.08a.ts (tsc exit=1) =====
ex.08a.ts(13,6): error TS2300: Duplicate identifier 'Aliased'.
ex.08a.ts(16,6): error TS2300: Duplicate identifier 'Aliased'.
ex.08a.ts(24,5): error TS2717: Subsequent property declarations must have the same type.  Property 'p' must be of type 'number', but here has type 'string'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 13·16행의 `TS2300` 둘과 24행의 `TS2717` 하나.
- ★★★ `interface Merged` 를 **세 번** 선언했는데 **진단이 없다.** 11행 `const m: Merged = { a: 1, b: "x", run() {} }` 가 그대로 통과한다 — **셋이 하나로 합쳐졌다.**
- `type Aliased` 는 두 번째 선언에서 막힌다 — `TS2300`, 「Duplicate identifier 'Aliased'.」 **두 줄 다** 진단이 난다.
- ★★ 병합에도 규칙이 있다 — 24행 `interface Clashing { p: string }` 이 `TS2717` 이다.\
  문구가 「Subsequent property declarations must have the same type.」 — **같은 이름은 같은 타입이어야** 합쳐진다.
- ★ 호출 시그니처는 **겹쳐 쌓인다.** `Overloaded` 를 두 번 선언했더니 `ov(1)` 과 `ov("s")` 가 둘 다 통과한다 — **오버로드가 됐다.**

> **선언 병합(declaration merging)** — 같은 이름의 `interface` 선언 여러 개를 컴파일러가 **하나로 합치는** 것.\
> 예: `interface M { a }` 와 `interface M { b }` 가 `{ a; b }` 가 된다. 호출 시그니처는 오버로드로 쌓인다.

비용 — **열려 있다는 것은 남이 열 수 있다는 뜻**이다. 전역 타입에 쓰면 어디서 덧붙였는지 추적이 어려워진다.

### (2) ★★★ 충돌을 만났을 때 — 한쪽만 말한다

**언제 쓰나** — 「확장할까 교차할까」를 고를 때. **이 절이 이 주제에서 가장 센 자리다.**

```ts
// ex.08b.ts
// 확장과 교차가 충돌을 만났을 때 — 한쪽은 말하고 한쪽은 침묵한다
interface Base {
    p: string;
}
interface Extended extends Base {
    p: number;
}

type TBase = { p: string };
type Crossed = TBase & { p: number };
declare const c: Crossed;

const asString: string = c.p;
const asNumber: number = c.p;
const putBack: Crossed = { p: "x" };

interface Narrowed extends Base {
    p: "literal";
}
type CrossedOk = TBase & { p: "literal" };
declare const ok: CrossedOk;
const okProbe: null = ok.p;
console.log(asString, asNumber, putBack, okProbe);
```

```text
===== tsc --pretty false --noEmit ex.08b.ts (tsc exit=1) =====
ex.08b.ts(5,11): error TS2430: Interface 'Extended' incorrectly extends interface 'Base'.
  Types of property 'p' are incompatible.
    Type 'number' is not assignable to type 'string'.
ex.08b.ts(15,28): error TS2322: Type 'string' is not assignable to type 'never'.
ex.08b.ts(22,7): error TS2322: Type '"literal"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 5행·15행·22행.
- 5행 `interface Extended extends Base { p: number }` 가 `TS2430` — **선언 자리에서 바로** 막는다.\
  들여쓴 줄이 이유를 두 단계로 적는다 — 「Types of property 'p' are incompatible.」 → 「Type 'number' is not assignable to type 'string'.」
- ★★★ **10행 `type Crossed = { p: string } & { p: number }` 에는 진단이 없다.** 선언이 조용히 통과한다.
- ★★★ 13·14행도 통과했다 — `const asString: string = c.p` 와 `const asNumber: number = c.p` 가 **둘 다** 된다.\
  `c.p` 의 타입이 **`never`** 이기 때문이다 — `never` 는 어디로든 들어간다([**04번 주제**](../04-any-unknown-never-void/)).
- ★★ 그래서 터지는 자리가 **15행**이다 — `const putBack: Crossed = { p: "x" }` 가 `TS2322`, 「Type 'string' is not assignable to type 'never'.」\
  **실수는 10행에서 했는데 진단은 다섯 줄 뒤에, 엉뚱한 문구로 난다.**
- ★ 17행 `interface Narrowed extends Base { p: "literal" }` 은 **통과했다.** `"literal"` 은 `string` 에 들어가므로 **좁히는 것은 허용**된다.
- ★ 22행 탐침이 그것을 확인한다 — `CrossedOk` 의 `p` 는 **`"literal"`** 이다. 교차도 **호환되면 좁아진다.**

```text
  { p: string } & { p: number }
          │
          ▼  교차의 규칙대로 성실히 계산
      string & number  =  never
          │
          ▼
      쓸 수도 없고 넣을 수도 없는 칸이 조용히 생긴다
```

★★ 이것이 `strict` 때문인가. 같은 파일을 `--strict false` 로 다시 던졌다 — 파일은 한 글자도 안 바꿨다.

```text
===== tsc --pretty false --noEmit --strict false ex.08b.ts (tsc exit=1) =====
ex.08b.ts(5,11): error TS2430: Interface 'Extended' incorrectly extends interface 'Base'.
  Types of property 'p' are incompatible.
    Type 'number' is not assignable to type 'string'.
ex.08b.ts(15,28): error TS2322: Type 'string' is not assignable to type 'never'.
ex.08b.ts(22,7): error TS2322: Type '"literal"' is not assignable to type 'null'.
```

- ★★★ **세 건이 글자 하나까지 같다.** 이 주제의 차이는 전부 **선언 구조**에서 나오는 것이라 `strict` 묶음과 무관하다.
- ★ 나머지 네 파일도 같은 방식으로 대조했고 **전부 같았다**(아래 「실행 검증」은 3-answer 에 있다).

비용 — 교차는 **더 유연한 대신 실수를 늦게 알려 준다.** `extends` 는 덜 유연한 대신 **선언 자리에서** 막는다.

### (3) ★★★ 암묵 인덱스 시그니처 — `interface` 에는 없다

**언제 쓰나** — 「내 타입이 왜 `Record<string, unknown>` 자리에 안 들어가지」에서 막힐 때.

```ts
// ex.08c.ts
// 암묵 인덱스 시그니처 — interface 에는 없고 type 별칭에는 있다
interface AsInterface {
    a: string;
}
type AsAlias = {
    a: string;
};
declare const i: AsInterface;
declare const t: AsAlias;

const fromInterface: Record<string, unknown> = i;
const fromAlias: Record<string, unknown> = t;

function send(payload: Record<string, unknown>) {
    return Object.keys(payload).length;
}
send(i);
send(t);

const fixed: Record<string, unknown> = i as unknown as Record<string, unknown>;
console.log(fromInterface, fromAlias, fixed);
```

```text
===== tsc --pretty false --noEmit ex.08c.ts (tsc exit=1) =====
ex.08c.ts(11,7): error TS2322: Type 'AsInterface' is not assignable to type 'Record<string, unknown>'.
  Index signature for type 'string' is missing in type 'AsInterface'.
ex.08c.ts(17,6): error TS2345: Argument of type 'AsInterface' is not assignable to parameter of type 'Record<string, unknown>'.
  Index signature for type 'string' is missing in type 'AsInterface'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**이고 **둘 다 `interface` 쪽**이다 — 11행과 17행.
- 문구가 규칙을 그대로 말한다 — 「Index signature for type 'string' is missing in type 'AsInterface'.」
- ★★★ **12·18행은 통과했다.** 글자 하나 안 다른 `type AsAlias = { a: string }` 은 `Record<string, unknown>` 에 **들어간다.**
- ★★ 왜 갈리나 — **`interface` 는 나중에 병합될 수 있다.** 지금 키가 `a` 뿐이어도 **다른 파일이 키를 더할 수 있으므로**\
  컴파일러가 「이 타입의 모든 값이 `unknown` 이다」를 **약속해 줄 수 없다.** `type` 은 닫혀 있어 약속할 수 있다.
- ★ 1절의 병합이 **여기서 대가를 치른다** — 열려 있다는 성질이 이 자리에서 검사를 막는다.
- ★ 20행처럼 `as unknown as` 로 뚫으면 통과한다. 제대로 고치는 법은 **`interface` 에 인덱스 시그니처를 직접 적거나** `type` 으로 바꾸는 것이다.

```text
  type  AsAlias    = { a: string }    ─────▶  Record<string, unknown>   통과
        (닫혀 있다 — 키가 a 뿐임이 확정)

  interface AsInterface { a: string }  ──╳──▶  Record<string, unknown>   TS2322
        (열려 있다 — 다른 파일이 키를 더할 수 있다)
```

> **암묵 인덱스 시그니처(implicit index signature)** — 인덱스 시그니처를 안 적었는데도 컴파일러가 **있는 셈 쳐 주는** 것.\
> 예: `type A = { a: string }` 은 `Record<string, unknown>` 에 들어가고, 같은 모양의 `interface` 는 못 들어간다.

비용 — JSON 을 다루는 코드에서 `interface` 를 쓰면 **이 벽을 자주 만난다.**

### (4) ★★ `type` 만 적을 수 있는 것들

**언제 쓰나** — 객체가 아닌 모양을 이름 붙일 때.

```ts
// ex.08d.ts
// type 별칭만 되는 것들과, interface 가 확장할 수 있는 것의 경계
type Union = string | number;
type Primitive = string;
type Tuple = [string, number];
type Fn = (a: number) => string;
type Conditional<T> = T extends string ? "yes" : "no";
type Mapped<T> = { [K in keyof T]: T[K] };
type Template = `id-${number}`;

interface FromTuple extends Tuple {}
interface FromUnion extends Union {}
interface FromPrimitive extends Primitive {}

interface CallSignature {
    (a: number): string;
}
declare const t: Tuple;
declare const cond: Conditional<string>;
declare const tmpl: Template;
const probe: null = cond;
console.log(t, tmpl, probe);
```

```text
===== tsc --pretty false --noEmit ex.08d.ts (tsc exit=1) =====
ex.08d.ts(11,29): error TS2312: An interface can only extend an object type or intersection of object types with statically known members.
ex.08d.ts(12,33): error TS2312: An interface can only extend an object type or intersection of object types with statically known members.
ex.08d.ts(20,7): error TS2322: Type '"yes"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 11·12행의 `TS2312` 둘과 20행의 탐침 하나.
- 2\~9행의 `type` 선언 여덟 개가 **전부 통과했다** — 유니온 · 원시 · 튜플 · 함수 · 조건부 · 매핑 · 템플릿 리터럴.
- ★★ `interface` 가 확장할 수 있는 것은 **정적으로 멤버가 정해진 객체 타입**뿐이다 — `TS2312` 의 문구 그대로다.
- ★ 그런데 **10행 `interface FromTuple extends Tuple {}` 은 통과했다.** 튜플은 **객체 타입**이기 때문이다(배열도 객체다).
- ★ `interface CallSignature { (a: number): string }` 도 통과한다 — **함수 타입은 호출 시그니처로 적으면 된다.** `interface` 가 함수를 못 적는 게 아니다.
- ★ 20행 탐침은 조건부 타입이 실제로 계산됐음을 확인한다 — `Conditional<string>` 의 타입이 **`"yes"`** 다.

비용 — 없음. **적어야 할 모양이 객체가 아니면 선택지가 하나뿐**이라는 뜻일 뿐이다.

### (5) ★★ 같은 실수, 다른 모양의 진단

**언제 쓰나** — 큰 타입에서 에러 메시지를 읽기 쉬운 쪽을 고를 때.

```ts
// ex.08e.ts
// 같은 실수에 진단의 모양이 갈린다
interface IBase {
    a: number;
    b: number;
    c: number;
}
interface IExt extends IBase {
    d: number;
}

type TBase = {
    a: number;
    b: number;
    c: number;
};
type TExt = TBase & { d: number };

declare const empty: {};
const toInterface: IExt = empty;
const toAlias: TExt = empty;
console.log(toInterface, toAlias);
```

```text
===== tsc --pretty false --noEmit ex.08e.ts (tsc exit=1) =====
ex.08e.ts(19,7): error TS2739: Type '{}' is missing the following properties from type 'IExt': d, a, b, c
ex.08e.ts(20,7): error TS2322: Type '{}' is not assignable to type 'TExt'.
  Type '{}' is missing the following properties from type 'TBase': a, b, c
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**이고 **코드가 다르다** — `TS2739` 와 `TS2322`.
- ★★ `interface IExt extends IBase` 쪽은 **한 줄**이다 — 「missing the following properties from type 'IExt': d, a, b, c」.\
  상속한 것까지 **합쳐서 한 번에** 나열한다. `IExt` 라는 **이름 하나**만 나온다.
- ★★ `type TExt = TBase & { d: number }` 쪽은 **두 줄**이다 — `TExt` 를 말한 뒤 들여쓴 줄에서 **`TBase`** 를 따로 짚는다.\
  교차의 **조각마다** 보고하므로 조각 이름이 드러난다.
- ★ 어느 쪽이 나은지는 상황에 달렸다 — 교차가 깊게 중첩되면 **들여쓴 줄이 계단처럼 쌓인다.** `interface` 쪽은 그 대신 **어느 조각에서 왔는지**를 잃는다.

비용 — 없음. 읽기 쉬움의 문제다.

### (6) ★★ 방출에는 둘 다 안 남는다 — 선언 방출에서만 갈린다

**언제 쓰나** — 「어느 쪽이 번들을 키우나」를 판정할 때.

```ts
// ex.08f.ts
// 둘 다 방출에 한 글자도 안 남는다 — 선언 방출에서만 갈린다
export interface Shape {
    kind: string;
}
export interface Shape {
    area(): number;
}
export type Alias = {
    kind: string;
    area(): number;
};

export const asInterface: Shape = { kind: "c", area: () => 1 };
export const asAlias: Alias = { kind: "c", area: () => 1 };
console.log(asInterface.area(), asAlias.area());
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.08f.ts (tsc exit=0) =====
===== 방출된 ex.08f.d.ts =====
export interface Shape {
    kind: string;
}
export interface Shape {
    area(): number;
}
export type Alias = {
    kind: string;
    area(): number;
};
export declare const asInterface: Shape;
export declare const asAlias: Alias;
```

```text
===== tsc --pretty false --module commonjs ex.08f.ts (tsc exit=0) =====
===== 방출된 ex.08f.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.asAlias = exports.asInterface = void 0;
exports.asInterface = { kind: "c", area: () => 1 };
exports.asAlias = { kind: "c", area: () => 1 };
console.log(exports.asInterface.area(), exports.asAlias.area());
```

```text
===== node ex.08f.js (node exit=0) =====
1 1
```

그림 해설 — 한 단계에 한 문장.

- ★★ `.d.ts` 에서 `interface Shape` 가 **두 덩어리 그대로** 나왔다 — 합쳐서 적지 않는다. **병합 가능성 자체가 계약의 일부**이기 때문이다.
- `type Alias` 는 한 덩어리다.
- ★★★ 방출된 `.js` 에는 **둘 다 한 글자도 없다.** 남은 것은 `exports.asInterface`·`exports.asAlias` 두 값뿐이다.
- 실행 결과가 `1 1` 이다 — 두 값이 똑같이 돈다.
- ★ 즉 **번들 크기·런타임 비용에는 아무 차이가 없다.** 고르는 기준에서 그 축은 빼도 된다.

비용 — 0. 방출에 한 글자도 안 남는다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  interface M { a: number }
  interface M { b: string }            ★ 합쳐진다
  type T = { a: number }
  type T = { b: string }               ★ TS2300

  interface E extends B { p: number }  ★ 충돌이면 TS2430 (선언 자리에서)
  type C = B & { p: number }           ★ 충돌이면 조용히 never

  interface I { (a: number): string }  호출 시그니처 — 함수도 적을 수 있다
  interface I2 extends [string, number] {}   튜플은 객체라 통과
  interface I3 extends (string | number) {}  ★ TS2312

  type U = string | number             ★ type 만
  type P = string                      ★ type 만
  type Cond<T> = T extends string ? 1 : 2    ★ type 만
  type Map<T> = { [K in keyof T]: T[K] }     ★ type 만
```

**규칙 불릿**

- ★★★ **`interface` 는 병합되고 `type` 은 중복 선언이 안 된다**(`TS2300`). 병합도 **같은 이름은 같은 타입**이어야 한다(`TS2717`).
- ★★★ **충돌을 만나면 `extends` 는 선언 자리에서 말하고**(`TS2430`) **교차는 조용히 `never` 를 만든다.**
- ★★★ **`interface` 에는 암묵 인덱스 시그니처가 없다** — `Record<string, unknown>` 자리에 못 들어간다. 같은 모양의 `type` 은 들어간다.
- ★★ **`type` 만 적을 수 있는 것** — 유니온 · 원시 · 조건부 · 매핑 · 템플릿 리터럴.
- ★ **튜플과 함수는 둘 다 된다** — 튜플은 객체 타입이라 `extends` 가 되고, 함수는 호출 시그니처로 적는다.
- ★★ **진단의 모양이 다르다** — `extends` 는 **한 줄에 전부**(`TS2739`), 교차는 **조각마다 들여쓴 줄**(`TS2322`).
- ★ **좁히는 확장은 둘 다 허용된다** — `p: "literal"` 은 `p: string` 을 확장할 수 있다.
- ★★ **방출에는 둘 다 안 남는다.** `.d.ts` 에서만 갈린다 — 병합된 `interface` 는 **덩어리 그대로** 실린다.

**금지 사례** — 이 주제에서 던져 받은 것 다섯이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) type 을 두 번 선언            ->  TS2300  Duplicate identifier 'Aliased'.
2) interface 병합에서 타입 충돌   ->  TS2717  Subsequent property declarations must have the same type. …
3) extends 로 프로퍼티 충돌       ->  TS2430  Interface 'Extended' incorrectly extends interface 'Base'.
4) interface 를 Record 자리에     ->  TS2322  … Index signature for type 'string' is missing in type 'AsInterface'.
5) interface 가 유니온을 확장     ->  TS2312  An interface can only extend an object type or intersection …
```

## 어디서 틀리나

- ★★★ 「**둘은 거의 같으니 아무거나 쓰면 된다**」 — 던져 보면 **다섯 칸**이 갈린다. 특히 `Record` 자리에서 한쪽만 막힌다.
- ★★★ 「**교차(`&`)는 `extends` 의 다른 표기법**」 — 아니다. **충돌을 만났을 때 한쪽만 말한다.** 교차는 `never` 를 만들고 침묵한다.
- ★★ 「**`interface` 로 적었으니 `Record<string, unknown>` 에 들어가겠지**」 — 안 들어간다. **병합 가능성 때문**이다.
- ★★ 「**`interface` 는 함수 타입을 못 적는다**」 — 적는다. 호출 시그니처(`(a: number): string`)로 쓴다.
- ★★ 「**`interface` 는 튜플을 확장 못 한다**」 — 한다. 튜플은 **객체 타입**이다. 못 하는 것은 **유니온과 원시**다.
- ★ 「**`type` 이 방출이 더 가볍겠지**」 — 둘 다 **0**이다. 실행 결과가 같다.
- ★ 「**`interface` 를 두 번 적으면 나중 것이 이긴다**」 — 합쳐진다. 같은 이름의 타입이 다르면 `TS2717` 로 막힌다.
- ★ 「**`extends` 는 프로퍼티 타입을 못 바꾼다**」 — **좁히는 것은 된다.** `p: "literal"` 이 `p: string` 을 확장했다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `interface` 는 **선언 병합**되고 `type` 은 안 된다 | 핸드북 「Declaration Merging」. `TS2300` 이 그 규칙이다 |
| **언어 보장** | 병합은 **같은 이름 같은 타입**이어야 한다 | `TS2717` 의 문구가 그 규칙이다 |
| **언어 보장** | `extends` 는 **호환되지 않는 재선언**을 막는다 | `TS2430`. 좁히는 확장은 통과했다 |
| **언어 보장** | 교차는 프로퍼티를 **교차**한다 — `string & number` 는 `never` | 탐침 대신 **역방향 대입**(`TS2322 … type 'never'`)으로 확인 |
| **언어 보장** | `interface` 에는 **암묵 인덱스 시그니처가 없다** | 핸드북이 「병합 가능성 때문」을 이유로 든다. `TS2322` 의 들여쓴 줄이 그 규칙이다 |
| **언어 보장** | 둘 다 **방출에 안 남는다** | `ex.08f.js` 전문과 `node` 출력 |
| **이 판(7.0.2)의 관찰** | 진단의 **모양**(`TS2739` 한 줄 대 `TS2322` + 중첩 줄) | 보고기의 구현이다. 「조각 이름이 드러나는가」만 성질로 읽는다 |
| **이 판의 관찰** | `TS2739` 가 나열하는 **프로퍼티 순서**(`d, a, b, c`) | 선언 순서를 따른다. 이 판의 관찰이다 |
| **이 판의 관찰** | `.d.ts` 가 병합된 `interface` 를 **덩어리 그대로** 싣는 것 | 선언 방출기의 구현이다 |
| **설정에 달림** | ★ **없다** | 다섯 파일을 `--strict false` 로 다시 던져 **출력과 종료 코드가 전부 같은 것**을 확인했다 |
| **안 잰 것** | 검사 **속도** | 아래 「더 들어가면」을 보라 — 재는 방법이 전제를 요구한다 |

★ 「**에러가 안 난 줄」이 이 주제에서 가장 센 근거다** — 교차의 충돌 선언이 그렇다.

## 언제 쓰고 언제 안 쓰나

| `interface` 를 쓴다 | `type` 을 쓴다 |
|---|---|
| 공개 API 의 객체 모양 — **소비자가 덧붙일 여지**를 남긴다 | **유니온** · 원시 별칭 · 튜플 · 조건부 · 매핑 · 템플릿 리터럴 |
| 클래스가 `implements` 할 계약 | JSON 처럼 **`Record` 자리에 넘겨야 하는** 데이터 |
| 남의 라이브러리 타입을 **보강**해야 할 때(모듈 보강) | 조각을 조합해 만드는 파생 타입(`Omit`·`Pick` 결과) |
| **충돌을 선언 자리에서 잡고 싶을 때**(`extends`) | 재사용 조각을 `&` 로 합치는 경우 — 단 **충돌은 조용하다** |

| 안 쓴다 | 안 쓴다 |
|---|---|
| 전역 `interface` 에 아무나 덧붙이게 두는 것 | 공개 API 객체를 `type` 으로 고정해 **확장 여지를 없애는** 것 |
| 유니온을 `interface` 로 적으려 애쓰는 것(`TS2312`) | 충돌 가능성이 있는 조각을 `&` 로 겹치는 것 — `never` 가 조용히 생긴다 |

## 핵심 문장

1. **`interface` 는 열려 있고 `type` 은 닫혀 있다** — 병합 가능 여부가 나머지 차이의 뿌리다.
2. **충돌에 `extends` 는 말하고 교차는 침묵한다** — `TS2430` 대 조용한 `never`.
3. **`interface` 에는 암묵 인덱스 시그니처가 없다** — 열려 있다는 성질이 여기서 대가를 치른다.
4. **`type` 만 유니온·원시·조건부·매핑을 적는다** — 튜플과 함수는 둘 다 된다.
5. **진단의 모양이 다르다** — 한 줄에 전부인가, 조각마다 들여쓰는가.
6. **방출에는 둘 다 안 남는다** — 번들 크기는 고르는 기준이 아니다.

## 관련 자료

- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — 객체 타입 **안에 무엇을 적나**(`?`·`readonly`·인덱스 시그니처)는 그쪽. 여기는 **어느 문법으로 적나**.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — 「이름이 아니라 모양」은 그쪽. **둘 다 구조로 비교된다**는 전제가 거기서 온다.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — 인덱스 시그니처가 그 검사를 빠져나가는 길인 것은 그쪽.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — `never` 가 **어디로든 들어간다**는 성질은 그쪽. 2절이 그 위에 선다.
- [**09번 주제** — 유니온 타입](../09-union-types/) — 유니온은 `type` 으로만 적는다. 그 규칙의 전면 서술은 그쪽.
- [목록의 **10번 주제**](../10-intersection-types/)(인터섹션 타입) — 교차가 `never` 를 만드는 규칙의 전면 서술은 그쪽. 여기서는 **`extends` 와 대비되는 칸**까지.
- [목록의 **33번 주제**](../33-declaration-merging/)(선언 병합) — 모듈 보강·전역 보강의 전면 서술은 그쪽. 여기서는 **`interface` 가 병합된다**는 사실까지.
- [목록의 **45번 주제**](../45-type-level-performance/)(타입 수준 성능) — 「어느 쪽이 빠른가」는 그쪽에서 **실제로 재고** 판정한다.

## 용어 풀이

> **선언 병합(declaration merging)** — 같은 이름의 `interface` 선언 여러 개를 컴파일러가 하나로 합치는 것.\
> 예: `interface M { a }` 와 `interface M { b }` 가 `{ a; b }` 가 된다.

> **타입 별칭(type alias)** — `type` 으로 어떤 타입에 이름을 붙이는 것. **새 타입을 만드는 게 아니라 이름만** 붙인다.\
> 예: `type Id = string` 은 `string` 의 다른 이름일 뿐이다.

> **교차 타입(intersection type)** — `&` 로 두 타입을 겹쳐 **둘 다 만족**하는 타입을 만드는 것.\
> 예: `{ p: string } & { p: number }` 의 `p` 는 `string & number` 라 `never` 가 된다.

> **암묵 인덱스 시그니처(implicit index signature)** — 안 적었는데도 컴파일러가 있는 셈 쳐 주는 인덱스 시그니처.\
> 예: `type A = { a: string }` 은 `Record<string, unknown>` 에 들어가고, 같은 모양의 `interface` 는 못 들어간다.

> **호출 시그니처(call signature)** — 객체 타입 안에 「이 타입은 이렇게 호출된다」를 적는 멤버.\
> 예: `interface Fn { (a: number): string }`. `interface` 로도 함수 타입을 적을 수 있는 이유다.

> **모듈 보강(module augmentation)** — 남의 모듈이 내보낸 `interface` 에 **내 파일에서 멤버를 덧붙이는** 것.\
> 예: 라이브러리의 `interface Request` 에 `user` 를 더하는 것. `type` 으로는 못 한다.

## 더 들어가면

- ★★ **「어느 쪽이 빠른가」를 이 배치에서 재지 않은 이유** — 널리 도는 이야기는 「`interface` 가 캐시되어 빠르다」인데,\
  그것을 **재려면** ① 타입이 수백 개인 코드베이스 ② 같은 의미를 두 문법으로 쓴 두 벌 ③ `--diagnostics` 로 잰 검사 시간이\
  **잡음보다 크게** 갈리는지가 필요하다. 셋 다 이 주제의 여섯 파일로는 성립하지 않는다.\
  ★ **손으로 유도한 수치를 적는 것도 규칙 위반**이므로, 이 칸은 **「안 잰 것」으로 남긴다.** [목록의 **45번 주제**](../45-type-level-performance/)에서 실제로 잰다.
- **모듈 보강은 `interface` 만 된다** — 남의 라이브러리 타입에 칸을 더하는 유일한 길이다. 그래서 **공개 API 는 `interface` 로** 내는 관행이 있다. [목록의 **33번 주제**](../33-declaration-merging/).
- **교차의 `never` 를 미리 잡는 법** — 조각을 겹치기 전에 `Omit` 으로 충돌 키를 빼거나, `extends` 로 한 번 받아 보면 `TS2430` 이 먼저 말한다.
- **`Record` 벽을 넘는 제대로 된 길** — `as unknown as` 대신 ① `interface` 에 `[k: string]: unknown` 을 직접 적거나 ② 그 자리만 `type` 으로 바꾼다. 단언은 검사를 끄는 것이라 다른 실수까지 덮는다([**01번 주제**](../01-what-ts-adds-and-erases/)).
