# ts/syntax/10 — 인터섹션 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제에서는 「**진단 목록에 없는 줄**」이 지배적 근거다. 2번은 **열두 줄 중 일곱 줄이 침묵**하고, 그 침묵이 답이다.\
> 그래서 **모든 진단 블록 옆에 소스 전문**을 뒀다 — 무엇이 침묵했는지 세어 볼 수 있어야 하기 때문이다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **6건**(13·16·17·21·23·24행) — **꺼내는 쪽은 넓고 넣는 쪽은 좁다**

**출력**

```ts
// ex.10a.ts
// 교차는 「둘 다」다 — 꺼내는 쪽이 넓어지고 넣는 쪽이 좁아진다
interface Named {
    name: string;
}
interface Aged {
    age: number;
}
type Person = Named & Aged;
declare const p: Person;

const useName = p.name;
const useAge = p.age;
const useNone = p.email;

const putBoth: Person = { name: "a", age: 1 };
const putOne: Person = { name: "a" };
const putExtra: Person = { name: "a", age: 1, email: "e" };

declare const onlyNamed: Named;
const widen: Named = p;
const narrow: Person = onlyNamed;

const probe: null = p;
const probeName: null = p.name;
console.log(useName, useAge, useNone, putBoth, putOne, putExtra, widen, narrow, probe, probeName);
```

```text
===== tsc --pretty false --noEmit ex.10a.ts (tsc exit=1) =====
ex.10a.ts(13,19): error TS2339: Property 'email' does not exist on type 'Person'.
ex.10a.ts(16,7): error TS2322: Type '{ name: string; }' is not assignable to type 'Person'.
  Property 'age' is missing in type '{ name: string; }' but required in type 'Aged'.
ex.10a.ts(17,47): error TS2353: Object literal may only specify known properties, and 'email' does not exist in type 'Person'.
ex.10a.ts(21,7): error TS2322: Type 'Named' is not assignable to type 'Person'.
  Property 'age' is missing in type 'Named' but required in type 'Aged'.
ex.10a.ts(23,7): error TS2322: Type 'Person' is not assignable to type 'null'.
ex.10a.ts(24,7): error TS2322: Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 | 무엇을 말하나 |
|---|---|---|---|
| `p.name` · `p.age` | 양쪽 조각의 멤버 | ★ **둘 다 통과** | 교차는 **멤버를 합친다** |
| `p.email` | 어디에도 없다 | **TS2339** | 없는 멤버는 여전히 없다 |
| `const putBoth: Person = { name, age }` | 양쪽 필수 칸을 채웠다 | **통과** | — |
| `const putOne: Person = { name }` | `age` 가 없다 | **TS2322** | 들여쓴 줄이 **`'Aged'`** 를 짚는다 |
| `const putExtra: … , email: "e" }` | 초과 프로퍼티 | **TS2353** | 그 검사는 교차에서도 돈다 |
| `const widen: Named = p` | 교차 → 조각 | ★ **통과** | 교차한 값은 **각 조각 자리에 들어간다** |
| `const narrow: Person = onlyNamed` | 조각 → 교차 | **TS2322** | 조각은 **교차 자리에 못 들어간다** |
| `const probe: null = p` | 탐침 | **TS2322** | `p` 는 **`Person`** |
| `const probeName: null = p.name` | 탐침 | **TS2322** | `p.name` 은 **`string`** |

- ★★★ 11·12행이 09 와 갈리는 자리다. `string | number` 였다면 `.toFixed` 도 `.length` 도 막혔다.\
  `Named & Aged` 는 **둘 다 준다.** 「**꺼내는 쪽은 합집합**」이다.
- ★★★ 20·21행이 그 대가다. 꺼내는 쪽이 넓어진 만큼 **넣는 쪽이 좁아진다** — 「**넣는 쪽은 교집합**」이다.
- ★★ 16행 진단의 들여쓴 줄이 **`Aged`** 라는 이름을 부른다. **어느 조각이 모자란지**까지 말해 준다.

### 2. ★★★ 열두 줄 중 진단은 **5건** — 침묵한 일곱 줄이 `never` 의 증거다

**출력**

```ts
// ex.10b.ts
// 충돌은 두 종류다 — 타입 전체가 never 가 되는 것과 칸 하나만 never 가 되는 것
type PrimClash = string & number;
declare const prim: PrimClash;

const probePrim: null = prim;
const asString: string = prim;
const asNumber: number = prim;
const putPrim: PrimClash = "x";

type PropClash = { p: string } & { p: number };
declare const obj: PropClash;

const probeObj: null = obj;
const probeProp: null = obj.p;
const propAsString: string = obj.p;
const propAsNumber: number = obj.p;
const putObj: PropClash = { p: "x" };

type OptClash = { q?: string } & { q: number };
declare const opt: OptClash;
const probeOpt: null = opt.q;
const putOpt: OptClash = { q: 1 };

type Narrowing = { r: string } & { r: "lit" };
declare const nar: Narrowing;
const probeNar: null = nar.r;
console.log(prim, asString, asNumber, putPrim, obj, propAsString, propAsNumber, putObj, opt, putOpt, nar);
```

```text
===== tsc --pretty false --noEmit ex.10b.ts (tsc exit=1) =====
ex.10b.ts(8,7): error TS2322: Type '"x"' is not assignable to type 'never'.
ex.10b.ts(13,7): error TS2322: Type 'PropClash' is not assignable to type 'null'.
ex.10b.ts(17,29): error TS2322: Type 'string' is not assignable to type 'never'.
ex.10b.ts(22,28): error TS2322: Type 'number' is not assignable to type 'never'.
ex.10b.ts(26,7): error TS2322: Type '"lit"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 | 읽는 법 |
|---|---|---|---|
| 5 `const probePrim: null = prim` | 탐침 | ★★★ **침묵** | `never` 는 `null` 에도 들어간다 |
| 6 `const asString: string = prim` | 탐침 | ★ **침묵** | `never` 는 `string` 에도 들어간다 |
| 7 `const asNumber: number = prim` | 탐침 | ★ **침묵** | `never` 는 `number` 에도 들어간다 |
| 8 `const putPrim: PrimClash = "x"` | **역방향** | **TS2322** | 「Type '"x"' … to type **'never'**」 ← 여기서 드러난다 |
| 13 `const probeObj: null = obj` | 탐침 | **TS2322** | `obj` 는 **`PropClash`** — **타입은 살아 있다** |
| 14 `const probeProp: null = obj.p` | 탐침 | ★★★ **침묵** | `obj.p` 만 **`never`** 다 |
| 15·16 `obj.p` 를 `string`·`number` 에 | 탐침 | **침묵** | 같은 이유 |
| 17 `const putObj: PropClash = { p: "x" }` | **역방향** | **TS2322** | 「Type 'string' … to type 'never'」 |
| 21 `const probeOpt: null = opt.q` | 탐침 | **침묵** | `{ q?: string } & { q: number }` 의 `q` 도 `never` |
| 22 `const putOpt: OptClash = { q: 1 }` | **역방향** | **TS2322** | 「Type 'number' … to type 'never'」 |
| 26 `const probeNar: null = nar.r` | 탐침 | **TS2322** | **`"lit"`** — 호환되면 **좁아진다**(충돌이 아니다) |

- ★★★ **이 블록의 값은 진단 다섯 줄이 아니라 침묵한 일곱 줄이다.** `never` 는 **어디로든 들어가므로**\
  탐침을 그대로 통과한다([**04번 주제**](../04-any-unknown-never-void/)). 「에러가 없으니 멀쩡하다」가 여기서 무너진다.
- ★★★ **묻는 법은 역방향 대입이다** — `const back: 그타입 = <아무 값>;` 을 한 줄 두면 컴파일러가 `'never'` 라고 말한다.
- ★★ **충돌은 두 얼굴이다.** 13행과 14행을 붙여 읽어라 —

| 충돌의 종류 | 예 | 타입 자체 | 그 칸 |
|---|---|---|---|
| **원시끼리** | `string & number` | ★ **`never`** | — |
| **객체 프로퍼티끼리** | `{ p: string } & { p: number }` | 살아 있다(`PropClash`) | ★ **`never`** |

- ★★ **실수한 줄과 터지는 줄이 다르다.** 잘못은 2행·10행·19행에서 했는데 진단은 8·17·22행에 난다.\
  교차는 **선언 자리에서 아무 말도 안 한다**([**08번 주제**](../08-interface-vs-type/)의 `extends` 와 정반대다).
- ★ 26행이 반례다. `{ r: string } & { r: "lit" }` 은 **호환되는 좁힘**이라 `r` 이 `"lit"` 이 된다 — 모든 겹침이 `never` 는 아니다.

### 3. ★★ 교차도 정규화된다 — 그러나 **순서는 안 바꾼다**

**출력**

```ts
// ex.10c.ts
// 교차도 적은 대로 남나 — 09 의 유니온과 같은 질문을 교차에 던진다
interface A {
    a: string;
}
interface B {
    b: number;
}
interface C {
    c: boolean;
}

declare const dup: A & A;
declare const withNever: A & never;
declare const withAny: A & any;
declare const withUnknown: A & unknown;
declare const nested: (A & B) & C;
declare const reordered: B & A;
declare const litBase: "a" & string;
declare const litClash: "a" & "b";
declare const objPrim: A & string;

const p1: null = dup;
const p2: null = withNever;
const p3: null = withAny;
const p4: null = withUnknown;
const p5: null = nested;
const p6: null = reordered;
const p7: null = litBase;
const p8: null = litClash;
const p9: null = objPrim;

const back2: A & never = { a: "x" };
const back3: A & any = "A 가 아닌 것";
const back8: "a" & "b" = "a";
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, back2, back3, back8);
```

```text
===== tsc --pretty false --noEmit ex.10c.ts (tsc exit=1) =====
ex.10c.ts(22,7): error TS2322: Type 'A' is not assignable to type 'null'.
ex.10c.ts(25,7): error TS2322: Type 'A' is not assignable to type 'null'.
ex.10c.ts(26,7): error TS2322: Type 'A & B & C' is not assignable to type 'null'.
ex.10c.ts(27,7): error TS2322: Type 'B & A' is not assignable to type 'null'.
ex.10c.ts(28,7): error TS2322: Type '"a"' is not assignable to type 'null'.
ex.10c.ts(30,7): error TS2322: Type 'A & string' is not assignable to type 'null'.
ex.10c.ts(32,7): error TS2322: Type '{ a: string; }' is not assignable to type 'never'.
ex.10c.ts(34,7): error TS2322: Type '"a"' is not assignable to type 'never'.
```

**왜 그런가**

| 적은 것 | 답한 것 | 무엇이 일어났나 |
|---|---|---|
| `A & A` | `A` | 중복 제거 |
| `A & never` | ★ **침묵 → 역방향이 `never` 라고 답함** | `never` 가 **전부 삼킨다** |
| `A & any` | ★★★ **침묵 → 역방향도 침묵** | **`any`** 다. `never` 였다면 33행이 막혔다 |
| `A & unknown` | `A` | `unknown` 은 **사라진다** |
| `(A & B) & C` | `A & B & C` | 평탄화 |
| `B & A` | ★★ **`B & A`** | **순서를 안 바꾼다** |
| `"a" & string` | **`"a"`** | **좁은 쪽이 남는다** |
| `"a" & "b"` | ★ **침묵 → 역방향이 `never`** | 리터럴끼리의 충돌 |
| `A & string` | **`A & string`** | 객체와 원시는 **줄지 않는다** |

- ★★★ **24행과 33행이 둘 다 침묵한 것**이 이 블록의 핵심이다. 침묵만 보면 `never` 와 구별이 안 되는데,\
  33행 `const back3: A & any = "A 가 아닌 것"` 이 통과했으므로 **`any` 다**. 역방향 대입 한 줄이 둘을 갈랐다.
- ★★ 09 와 나란히 놓으면 **네 칸이 뒤집힌다** —

| | 유니온 `\|` | 교차 `&` |
|---|---|---|
| `never` | 사라진다 | ★ **전부 삼킨다** |
| `unknown` | 전부 삼킨다 | ★ **사라진다** |
| 리터럴과 기반 타입 | 넓은 쪽(`string`) | ★ **좁은 쪽(`"a"`)** |
| 순서 | ★ **재정렬한다** | ★ **안 바꾼다** |
| `any` · 중복 · 중첩 | 삼킴 · 제거 · 평탄화 | 같다 |

- ★ **순서를 지키는 것은 이 판의 관찰이지 보장이 아니다.** 대조할 것은 「**같은 조각 집합으로 정리된다**」는 성질이다.

### 4. ★★★ 진단 **7건** — 교차한 함수는 **오버로드와 같은 것**이 된다

**출력**

```ts
// ex.10d.ts
// 함수의 교차는 오버로드가 된다 — 09 의 함수 유니온과 정반대다
type CrossFn = ((a: string) => string) & ((a: number) => number);
declare const cross: CrossFn;

const fromString: null = cross("s");
const fromNumber: null = cross(1);
cross(true);

interface OverFn {
    (a: string): string;
    (a: number): number;
}
declare const over: OverFn;
const overString: null = over("s");
over(true);

type UnionFn = ((a: string) => string) | ((a: number) => number);
declare const union: UnionFn;
union("s");

const asStringFn: (a: string) => string = cross;
const asNumberFn: (a: number) => number = cross;
const asBoolFn: (a: boolean) => boolean = cross;
console.log(fromString, fromNumber, overString, asStringFn, asNumberFn, asBoolFn);
```

```text
===== tsc --pretty false --noEmit ex.10d.ts (tsc exit=1) =====
ex.10d.ts(5,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.10d.ts(6,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.10d.ts(7,7): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Argument of type 'boolean' is not assignable to parameter of type 'number'.
ex.10d.ts(14,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.10d.ts(15,6): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Argument of type 'boolean' is not assignable to parameter of type 'number'.
ex.10d.ts(19,7): error TS2345: Argument of type '"s"' is not assignable to parameter of type 'never'.
ex.10d.ts(23,7): error TS2322: Type 'CrossFn' is not assignable to type '(a: boolean) => boolean'.
  Types of parameters 'a' and 'a' are incompatible.
    Type 'boolean' is not assignable to type 'string'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `const fromString: null = cross("s")` | 첫 시그니처로 풀린다 | **TS2322** — 반환이 **`string`** |
| `const fromNumber: null = cross(1)` | 둘째 시그니처로 풀린다 | **TS2322** — 반환이 **`number`** |
| `cross(true)` | 어느 시그니처도 아니다 | **TS2769** — 「No overload matches this call.」 |
| `over(true)` | **손으로 적은 오버로드** | ★★★ **같은 TS2769, 같은 문구** |
| `union("s")` | 같은 두 시그니처를 `\|` 로 | **TS2345** — 「parameter of type **`never`**」 |
| `const asStringFn: (a: string) => string = cross` | 조각 시그니처 자리 | ★ **통과** |
| `const asBoolFn: (a: boolean) => boolean = cross` | 없는 시그니처 | **TS2322** |

- ★★★ **7행과 15행의 진단이 글자 하나까지 같다.** 한쪽은 `&` 로 적었고 다른 쪽은 호출 시그니처 두 줄로 적었는데,\
  컴파일러가 **같은 것으로 취급**한다는 증거다.
- ★★★ **19행이 이 주제와 09 를 잇는 못이다.** 같은 두 함수 타입을 `|` 로 묶으면 **아무것도 못 넣는다**(매개변수가 `never`),\
  `&` 로 묶으면 **둘 다 부를 수 있다**(오버로드).
- ★★ 이유는 7·8번과 같다 — 「**둘 다인 함수**」이므로 어느 시그니처로 불러도 되고, 「**둘 중 하나인 함수**」이므로 어느 쪽에도 안전한 인자만 받아야 한다.
- ★ 5·6행은 **탐침 때문에** 진단이 난 것이다. **호출 자체는 통과했다** — 그 사실이 반환 타입을 알려 준다.

### 5. ★★★ 진단 **9건** — `(A | B) & C` 는 **분배되고**, 진단이 그 조각 이름을 부른다

**출력**

```ts
// ex.10e.ts
// (A | B) & C 는 분배된다 — 진단의 들여쓴 줄이 그 조각 이름을 부른다
interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
interface Tagged {
    id: string;
}

declare const shape: (Circle | Square) & Tagged;

const probeAll: null = shape;
const probeKind: null = shape.kind;
const probeId: null = shape.id;
shape.r;

declare const spelled: (Circle & Tagged) | (Square & Tagged);
const probeSpelled: null = spelled;

const putOk: (Circle | Square) & Tagged = { kind: "circle", r: 1, id: "x" };
const putNoTag: (Circle | Square) & Tagged = { kind: "circle", r: 1 };
const putMixed: (Circle | Square) & Tagged = { kind: "circle", r: 1, side: 2, id: "x" };

function split(s: (Circle | Square) & Tagged) {
    if (s.kind === "circle") {
        const inCircle: null = s;
    } else {
        const inSquare: null = s;
    }
}
console.log(probeAll, probeKind, probeId, probeSpelled, putOk, putNoTag, putMixed, split);
```

```text
===== tsc --pretty false --noEmit ex.10e.ts (tsc exit=1) =====
ex.10e.ts(16,7): error TS2322: Type '(Circle | Square) & Tagged' is not assignable to type 'null'.
  Type 'Circle & Tagged' is not assignable to type 'null'.
ex.10e.ts(17,7): error TS2322: Type '"circle" | "square"' is not assignable to type 'null'.
  Type '"circle"' is not assignable to type 'null'.
ex.10e.ts(18,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.10e.ts(19,7): error TS2339: Property 'r' does not exist on type '(Circle | Square) & Tagged'.
  Property 'r' does not exist on type 'Square & Tagged'.
ex.10e.ts(22,7): error TS2322: Type '(Circle & Tagged) | (Square & Tagged)' is not assignable to type 'null'.
  Type 'Circle & Tagged' is not assignable to type 'null'.
ex.10e.ts(25,7): error TS2322: Type '{ kind: "circle"; r: number; }' is not assignable to type '(Circle | Square) & Tagged'.
  Type '{ kind: "circle"; r: number; }' is not assignable to type 'Circle & Tagged'.
    Property 'id' is missing in type '{ kind: "circle"; r: number; }' but required in type 'Tagged'.
ex.10e.ts(26,70): error TS2353: Object literal may only specify known properties, and 'side' does not exist in type 'Circle & Tagged'.
ex.10e.ts(30,15): error TS2322: Type 'Circle & Tagged' is not assignable to type 'null'.
ex.10e.ts(32,15): error TS2322: Type 'Square & Tagged' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 무엇 | 답 |
|---|---|---|
| `const probeAll: null = shape` | 전체 탐침 | 겉은 `(Circle \| Square) & Tagged`, ★ **들여쓴 줄이 `Circle & Tagged`** |
| `const probeKind: null = shape.kind` | 판별 칸 | **`"circle" \| "square"`** |
| `const probeId: null = shape.id` | 공통 칸 | **`string`** |
| `shape.r` | 한쪽에만 있는 칸 | **TS2339** — 들여쓴 줄이 **`Square & Tagged`** |
| `const probeSpelled: null = spelled` | 손으로 분배해 적은 것 | **같은 모양의 진단** |
| `const putOk = { kind, r, id }` | 한 조각을 채웠다 | ★ **통과** |
| `const putNoTag = { kind, r }` | `id` 가 없다 | **TS2322** — **`Circle & Tagged`** 기준 |
| `const putMixed = { kind, r, side, id }` | 두 조각을 섞었다 | **TS2353** — `'side'` 는 `Circle & Tagged` 에 없다 |
| `if (s.kind === "circle")` 안 / 밖 | 좁히기 | ★★ **`Circle & Tagged`** / **`Square & Tagged`** |

- ★★★ **내가 안 적은 이름이 진단에 나온다.** `Circle & Tagged` 라는 타입을 소스 어디에도 적지 않았는데\
  컴파일러가 그 이름을 부른다 — `(Circle | Square) & Tagged` 를 **멤버마다 따로 교차**해서 다루기 때문이다.
- ★★ 22행이 그것을 확인한다. 손으로 `(Circle & Tagged) | (Square & Tagged)` 라고 적은 값이 **같은 모양으로** 답한다.
- ★★★ 30·32행이 실무에서 가장 쓰이는 칸이다 — **판별 유니온에 공통 칸을 `&` 로 붙여도 좁히기가 그대로 산다.**\
  좁힌 결과가 `Circle` 이 아니라 **`Circle & Tagged`** 라는 점만 다르다([**12번 주제**](../12-narrowing/)).
- ★ 26행은 [**06번 주제**](../06-excess-property-checks/)와 이어진다 — 초과 프로퍼티 검사도 **분배된 조각**을 기준으로 돈다.

### 6. ★★★ `.d.ts` 는 **적은 그대로**, `.js` 에는 **한 글자도 안 남는다**

**출력**

```ts
// ex.10f.ts
// 선언 방출은 교차를 적은 그대로 돌려준다 — 09 의 유니온과 같다
export interface A {
    a: string;
}
export interface B {
    b: number;
}
export type Dup = A & A;
export type WithNever = A & never;
export type PrimClash = string & number;
export type Nested = (A & B) & B;
export type Reordered = B & A;
export type CrossFn = ((a: string) => string) & ((a: number) => number);
export declare const merged: A & B;
export const made = { a: "x", b: 1 } as A & B;
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.10f.ts (tsc exit=0) =====
===== 방출된 ex.10f.d.ts =====
export interface A {
    a: string;
}
export interface B {
    b: number;
}
export type Dup = A & A;
export type WithNever = A & never;
export type PrimClash = string & number;
export type Nested = (A & B) & B;
export type Reordered = B & A;
export type CrossFn = ((a: string) => string) & ((a: number) => number);
export declare const merged: A & B;
export declare const made: A & B;
```

```ts
// ex.10g.ts
// 교차는 방출에 한 글자도 안 남는다 — 합치는 일은 JS 스프레드가 한다
interface A {
    a: string;
}
interface B {
    b: number;
}
type Both = A & B;

function merge(x: A, y: B): Both {
    return { ...x, ...y };
}

const both: Both = merge({ a: "hi" }, { b: 7 });
console.log("merge     :", JSON.stringify(both));
console.log("a / b     :", both.a, "/", both.b);
console.log("런타임 구분:", typeof both, Object.keys(both).join(","));
```

```text
===== tsc --pretty false ex.10g.ts (tsc exit=0) =====
===== 방출된 ex.10g.js =====
"use strict";
function merge(x, y) {
    return { ...x, ...y };
}
const both = merge({ a: "hi" }, { b: 7 });
console.log("merge     :", JSON.stringify(both));
console.log("a / b     :", both.a, "/", both.b);
console.log("런타임 구분:", typeof both, Object.keys(both).join(","));
```

```text
===== node ex.10g.js (node exit=0) =====
merge     : {"a":"hi","b":7}
a / b     : hi / 7
런타임 구분: object a,b
```

**왜 그런가**

| 선언 | `.d.ts` | 3번의 탐침 |
|---|---|---|
| `Dup = A & A` | **그대로** | `A` |
| `WithNever = A & never` | **그대로** | `never` |
| `PrimClash = string & number` | **그대로** | `never` |
| `Nested = (A & B) & B` | **괄호까지 그대로** | (평탄화된다) |
| `Reordered = B & A` | 그대로 | `B & A` |
| `CrossFn = ((a: string) => string) & …` | 그대로 | 오버로드로 해석 |
| `export const made = { … } as A & B` | ★ **`: A & B`** | — |

- ★★★ **같은 선언이 두 창에서 다르게 보인다.** 09 에서 유니온으로 본 것과 **같은 성질**이다 —\
  `.d.ts` 는 「**무엇을 적었나**」, 탐침은 「**무엇이 됐나**」를 답한다.
- ★★ 그래서 **`.d.ts` 만 보고 「충돌이 없다」고 믿으면 틀린다.** `string & number` 가 그대로 실려 있어도 그 타입에는 값이 없다.
- ★ 값 선언은 다르다 — `made` 는 추론 결과(`A & B`)로 적힌다. **타입 별칭만 표기를 옮긴다.**
- ★★★ 방출된 `.js` 에는 `interface`·`type` 이 **통째로 없다.** 합치는 일을 하는 것은 **JS 스프레드 `{ ...x, ...y }`** 뿐이다.
- 실행이 확인한다 — `{"a":"hi","b":7}` · `typeof` 는 `object` · 키는 `a,b`. **런타임에 「교차」라는 개념은 없다.**

### 7. ★★★ **하나의 값이 두 조건을 동시에 만족한다**는 전제에서 둘 다 나온다

**왜 그런가**

- `p: Named & Aged` 는 「이 값은 **`Named` 이면서 동시에 `Aged`**」라는 뜻이다. **어느 쪽인지 모르는 게 아니다.**
- 그러니 **꺼낼 때는** 양쪽 멤버를 다 믿어도 된다 → **합집합**.
- 반대로 **넣을 때는** 양쪽 조건을 다 채운 값만 그 전제를 만족한다 → **교집합**.
- ★★ 09 의 유니온은 전제가 「**어느 한쪽이다(모른다)**」였다. **모름이 꺼내는 쪽을 좁히고 넣는 쪽을 넓혔다.**

```text
    A & B  — "둘 다다"                 A | B  — "둘 중 하나다(모른다)"
  ┌──────────────────────┐          ┌──────────────────────┐
  │ 꺼낸다: 양쪽 멤버    │          │ 꺼낸다: 공통 멤버만  │
  │ 넣는다: 양쪽 조건 충족│         │ 넣는다: 한쪽만 맞으면│
  └──────────────────────┘          └──────────────────────┘
       ★ 아는 것이 많으면 꺼낼 게 많고 만들기가 어렵다
```

### 8. ★★★ **호출은 꺼내는 행위**이기 때문이다

**왜 그런가**

- `cross: ((a: string) => string) & ((a: number) => number)` 는 「이 값은 **두 시그니처를 동시에 갖는다**」는 뜻이다.
- 호출은 **꺼내 쓰는 행위**이므로 7번의 규칙대로 **양쪽을 다 쓸 수 있다** → 인자에 맞는 시그니처가 골라진다 = **오버로드**.
- 반대로 `union: ((a: string) => string) | ((a: number) => number)` 는 「**둘 중 하나**」라 어느 쪽인지 모른다.\
  어느 함수가 들어 있든 안전한 인자만 받아야 하므로 매개변수가 `string & number` = **`never`** 다.
- ★★ **매개변수 자리의 교집합이 곧 이 주제의 `&`** 다 — 09 의 `never` 가 어디서 왔는지 여기서 답이 난다.
- ★ 4번의 진단 두 건이 그대로 근거다 — `TS2769`(교차) 대 `TS2345 … 'never'`(유니온).

### 9. ★★★ **`never` 이거나 `any` 다** — 역방향 대입 한 줄이 가른다

**왜 그런가**

| 탐침 결과 | 가능한 것 | 왜 통과하나 |
|---|---|---|
| `const probe: null = x` 가 **침묵** | **`never`** | `never` 는 **모든 타입에 들어간다** |
| 〃 | **`any`** | `any` 는 **모든 타입에 들어간다** |

- ★★★ 가르는 법은 **방향을 뒤집는 것**이다 —

| 물음 | `never` 라면 | `any` 라면 |
|---|---|---|
| `const back: X = <아무 값>;` | **TS2322** — 「… to type 'never'」 | ★ **침묵** |

- ★★ 3번이 그 대조를 실제로 실었다. `A & never`(23행 침묵 → 32행 **말함**) 과 `A & any`(24행 침묵 → 33행 **침묵**).
- ★ 이 수법은 [**08번 주제**](../08-interface-vs-type/)에서 처음 썼고 여기서 정식 도구가 됐다.\
  「**탐침이 침묵하면 더 물어라**」가 이 갈래의 규칙이다.
- ★ 탐침을 `null` 로 잡는 이유도 같다 — `null` 은 받는 것이 거의 없어 **거의 모든 타입이 걸린다.** 안 걸리는 것이 `never`·`any` 다.

### 10. ★★ `.d.ts` 는 「**적은 것**」, 탐침은 「**계산된 것**」 — 09 와 같은 말이다

**왜 그런가**

| 창 | 무엇을 말하나 | 6번의 예 |
|---|---|---|
| `.d.ts` 덤프 | **소스에 적힌 타입 표기** | `type PrimClash = string & number` 그대로 |
| `null` 탐침 | **계산된 타입** | `never`(침묵 → 역방향으로 확인) |

- ★★ 교차에서는 이 갈림이 **더 위험하다.** 유니온에서는 `.d.ts` 가 좀 지저분해 보이는 정도였지만,\
  교차에서는 `.d.ts` 에 멀쩡히 적힌 타입이 **값이 하나도 없는 타입**일 수 있다.
- ★ 라이브러리를 소비하는 쪽은 `.d.ts` 를 읽는다 — 그래서 공개 API 에 교차를 쓸 때는 **충돌이 없다는 것을 따로 확인**해야 한다.
- ★ 두 창을 같이 써야 답이 온전해진다. 이 문서의 3번과 6번이 정확히 그 짝이다.

### 11. ★★ 네 칸이 전부 뒤집힌다

**왜 그런가**

| 칸 | 유니온 `A \| B` | 교차 `A & B` | 근거 |
|---|---|---|---|
| **꺼내는 쪽** | 공통 멤버만(교집합) | ★ **양쪽 멤버 전부**(합집합) | 1번의 11·12행 |
| **넣는 쪽** | 한쪽만 맞으면(합집합) | ★ **양쪽을 다 채워야**(교집합) | 1번의 16·20·21행 |
| **함수 매개변수** | `never` — 못 부른다 | ★ **오버로드** — 둘 다 부른다 | 4번의 7·15·19행 |
| **함수 반환** | 합집합(`string \| number`) | 고른 시그니처의 반환 | 4번의 5·6행 |

- ★★★ 한 줄로 — 「**`|` 는 모른다는 상태이고 `&` 는 둘 다라는 상태다.**」 나머지는 전부 여기서 따라 나온다.
- ★★ 정규화도 뒤집힌다 — `never`·`unknown`·리터럴 흡수의 방향이 반대다(3번의 표).
- ★ 다만 **뒤집히지 않는 것**도 있다 — `any` 가 전부 삼키는 것, 중복 제거, 평탄화, 그리고 **방출에 한 글자도 안 남는 것**.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 꺼내는 쪽은 **합집합**, 넣는 쪽은 **교집합** · 프로퍼티는 **교차**되고 충돌하면 `never` · 평탄화·중복 제거·흡수로 정규화 · 함수 교차는 **오버로드** · `(A \| B) & C` 는 **분배** · 방출에 안 남는다 |
| **설정에 달린 것** | ★ **없다**. 다섯 파일을 `--strict false` 로 다시 던져 **종료 코드와 출력이 전부 같은 것**을 확인했다(아래 블록) |
| **이 판(7.0.2)의 관찰** | ★★ 교차가 **적은 순서를 지키는 것**(`B & A`) · `TS2769` 가 「The last overload」로 **어느 시그니처를 고르는가** · `.d.ts` 가 괄호까지 그대로 싣는 것 · 진단 문구 전문 |

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.10a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.10e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★★ 「**에러가 안 난 줄」이 이 주제의 지배적 근거다** — 2번에서 **열두 줄 중 일곱 줄**, 3번에서 **열두 줄 중 네 줄**이 침묵했다.
- ★ **순서는 대조 기준으로 쓰지 않는다.** 「같은 조각 집합으로 정리된다」는 성질만 읽는다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 멤버 합치기·대입 방향 | `--noEmit ex.10a.ts` | exit 1 · **6건** · `widen` 통과 / `narrow` **TS2322** |
| 충돌 두 종류 | `--noEmit ex.10b.ts` | exit 1 · 열두 줄에 **5건** · **일곱 줄 침묵** · 역방향 3건이 `'never'` 를 말함 |
| 정규화 | `--noEmit ex.10c.ts` | exit 1 · **8건** · `A & any` 는 침묵 두 번(= `any`) |
| 함수 교차 | `--noEmit ex.10d.ts` | exit 1 · **7건** · `cross(true)` 와 `over(true)` 가 **같은 TS2769** · `union("s")` 만 `TS2345 'never'` |
| 분배 | `--noEmit ex.10e.ts` | exit 1 · **9건** · 들여쓴 줄이 `Circle & Tagged`·`Square & Tagged` 를 부름 |
| 선언 방출 | `--declaration --emitDeclarationOnly ex.10f.ts` | exit 0 · **정규화 안 함** · `made: A & B` |
| 방출·실행 | `tsc ex.10g.ts` + `node ex.10g.js` | tsc exit 0 · node exit 0 · `{"a":"hi","b":7}` · 키 `a,b` |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★ **전부 동일** — 종료 코드도 출력도 같다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **교차가 적은 순서를 지키는 것** — 09 의 유니온은 재정렬했다. **이 문서의 대조 기준으로 쓰지 않는다.**
- `TS2769` 가 「The last overload gave the following error.」로 **어느 시그니처를 고르는가** — 선언 순서를 따른다.
- 진단의 들여쓴 줄이 **분배된 조각 중 어느 것을 대표로** 짚는가 — 보고기의 구현이다.
- `.d.ts` 가 타입 별칭의 표기를 괄호까지 그대로 옮기는 것 — 선언 방출기의 구현이다.
- 진단 문구 전문 — 코드(`TS2339`·`TS2322`·`TS2353`·`TS2769`·`TS2345`)가 더 오래 간다.

**안 돌려 본 것**

- **조각 수에 따른 검사 시간** — 「더 들어가면」의 마지막 줄. **재지 않았고 수치를 적지 않았다.** 목록의 **45번 주제**에서 잰다.
- **브랜드 타입의 전면 서술** — 3절의 `A & string` 이 줄지 않는다는 성질만 확인했다. 관용구 자체는 [**05번 주제**](../05-structural-typing/)가 정본이다.
- **`Omit` 으로 충돌 키를 빼는 관용구** — 형태만 적었고 던지지 않았다. 목록의 **28번 주제**에서 던진다.
