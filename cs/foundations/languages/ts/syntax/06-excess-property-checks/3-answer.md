# ts/syntax/06 — 초과 프로퍼티 검사 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제에서는 「**진단 목록에 없는 줄**」이 근거다. 그래서 소스 전문을 같은 자리에 실었다 — 통과한 줄을 직접 세어 보라.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **6건** — 리터럴을 직접 놓은 자리가 정확히 여섯이다

**출력**

```ts
// ex.06a.ts
// 같은 값이 자리에 따라 갈린다 — 리터럴을 직접 놓는 자리를 전부 모았다
interface Point {
    x: number;
    y: number;
}
function take(pt: Point) {
    return pt.x;
}

const viaVar = { x: 1, y: 2, z: 3 };
const ok1: Point = viaVar;
take(viaVar);

const bad1: Point = { x: 1, y: 2, z: 3 };
take({ x: 1, y: 2, z: 3 });

const inArray: Point[] = [{ x: 1, y: 2, z: 3 }];
function ret(): Point {
    return { x: 1, y: 2, z: 3 };
}

interface Outer {
    inner: { a: number };
}
const nested: Outer = { inner: { a: 1, b: 2 } };

let later: Point;
later = { x: 1, y: 2, z: 3 };
console.log(ok1, bad1, inArray, ret(), nested, later);
```

```text
===== tsc --pretty false --noEmit ex.06a.ts (tsc exit=1) =====
ex.06a.ts(14,35): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(15,20): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(17,41): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(19,26): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(25,40): error TS2353: Object literal may only specify known properties, and 'b' does not exist in type '{ a: number; }'.
ex.06a.ts(28,23): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| `const ok1: Point = viaVar` | **변수**를 넘긴다 | **통과** |
| `take(viaVar)` | **변수**를 넘긴다 | **통과** |
| `const bad1: Point = { …, z: 3 }` | 변수 표기 | **TS2353** |
| `take({ …, z: 3 })` | 인자 | **TS2353** |
| `const inArray: Point[] = [{ …, z: 3 }]` | 배열 원소 | **TS2353** |
| `return { …, z: 3 }` | 반환문 | **TS2353** |
| `const nested: Outer = { inner: { a: 1, b: 2 } }` | 중첩 리터럴 | **TS2353** — 익명 타입 이름 |
| `later = { …, z: 3 }` | 대입 | **TS2353** |

- ★★ 배열 리터럴이 한 겹 끼어도 통과 못 한다 — **원소마다 따로** 검사한다.
- ★★ 중첩도 검사한다. 진단이 안쪽 타입을 익명으로 적는다 — 「does not exist in type '{ a: number; }'」.
- ★★★ 그리고 **11·12행이 진단 목록에 없다.** `viaVar` 는 `{ x: 1, y: 2, z: 3 }` 과 **같은 값**인데 통과했다.
- ★★ 같은 파일을 `--strict false` 로 던지면 **여섯 건이 글자 하나까지 같다** — 이 검사는 `strict` 묶음과 무관한 상시 검사다.

```text
===== tsc --pretty false --noEmit --strict false ex.06a.ts (tsc exit=1) =====
ex.06a.ts(14,35): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(15,20): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(17,41): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(19,26): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(25,40): error TS2353: Object literal may only specify known properties, and 'b' does not exist in type '{ a: number; }'.
ex.06a.ts(28,23): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
```

### 2. ★★★ 진단 **2건** — 막히는 것은 `satisfies` 와 직접 적은 `w` 다

**출력**

```ts
// ex.06b.ts
// 빠져나가는 길 다섯과, 빠져나가지 못하는 하나
interface Point {
    x: number;
    y: number;
}
const src = { x: 1, y: 2, z: 3 };

const byVar: Point = src;
const bySpread: Point = { ...src };
const byAssert: Point = { x: 1, y: 2, z: 3 } as Point;
const byIndex: Point & Record<string, unknown> = { x: 1, y: 2, z: 3 };

function byGeneric<T extends Point>(v: T) {
    return v.x;
}
byGeneric({ x: 1, y: 2, z: 3 });

const bySatisfies = { x: 1, y: 2, z: 3 } satisfies Point;
const spreadPlus: Point = { ...src, w: 4 };
console.log(byVar, bySpread, byAssert, byIndex, bySatisfies, spreadPlus);
```

```text
===== tsc --pretty false --noEmit ex.06b.ts (tsc exit=1) =====
ex.06b.ts(18,35): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06b.ts(19,37): error TS2353: Object literal may only specify known properties, and 'w' does not exist in type 'Point'.
```

**왜 그런가**

| 방법 | 형태 | 결과 |
|---|---|---|
| 변수 | `const byVar: Point = src` | **통과** |
| 스프레드 | `{ ...src }` | **통과** |
| 단언 | `{ … } as Point` | **통과** |
| 인덱스 시그니처 | `Point & Record<string, unknown>` | **통과** |
| ★ 제네릭 추론 | `byGeneric({ x, y, z })` | **통과** — `T` 가 `{ x; y; z }` 로 추론된다 |
| ★★ `satisfies` | `{ … } satisfies Point` | **TS2353** |

- ★★★ `satisfies` 는 「검사만 하고 넓히지 않는다」는 연산자인데 **이 검사는 그대로 돈다.** `as` 와 정반대다.
- ★★ `{ ...src, w: 4 }` 의 진단은 **`w` 하나**뿐이다. 스프레드로 들어온 `z` 는 같은 중괄호 안인데도 조용하다.\
  ★ 즉 **한 리터럴 안에서 검사 대상이 갈린다** — 직접 적은 키만 본다.
- ★ 제네릭이 통과하는 이유 — 타입 매개변수가 인자의 실제 모양으로 추론되므로 **여분이라는 판정 자체가 안 선다**.

### 3. ★★★ 진단 **2건**인데 **코드가 다르다** — `TS2559` 와 `TS2561`

**출력**

```ts
// ex.06c.ts
// 전부 선택인 타입은 변수로 넘겨도 막힌다 — 그리고 오타를 짚어 준다
interface Opts {
    color?: string;
    width?: number;
}
function draw(o: Opts) {
    return o.color;
}

const wrong = { colour: "red" };
draw(wrong);
draw({ colour: "red" });

const mixed = { colour: "red", width: 2 };
draw(mixed);

interface Half {
    id: string;
    color?: string;
}
function half(h: Half) {
    return h.id;
}
const forHalf = { id: "a", colour: "red" };
half(forHalf);
console.log(draw(mixed), half(forHalf));
```

```text
===== tsc --pretty false --noEmit ex.06c.ts (tsc exit=1) =====
ex.06c.ts(11,6): error TS2559: Type '{ colour: string; }' has no properties in common with type 'Opts'.
ex.06c.ts(12,8): error TS2561: Object literal may only specify known properties, but 'colour' does not exist in type 'Opts'. Did you mean to write 'color'?
```

**왜 그런가**

| 줄 | 넘긴 것 | 결과 |
|---|---|---|
| `draw(wrong)` | **변수** `{ colour: "red" }` | ★★ **TS2559** — 변수인데 막혔다 |
| `draw({ colour: "red" })` | 리터럴 | **TS2561** — 「Did you mean to write 'color'?」 |
| `draw(mixed)` | 변수 `{ colour, width }` | **통과** — 공통 키 `width` 가 있다 |
| `half(forHalf)` | 변수 `{ id, colour }` | **통과** — `Half` 에 **필수 키**가 있어 약한 타입이 아니다 |

- ★★★ `Opts` 는 프로퍼티가 **전부 선택**이라 모양으로는 `{}` 조차 통과한다. 그대로 두면 오타가 전부 새어 나가므로 **따로 만든 검사**다.
- ★★ 그래서 「변수로 넘기면 언제나 통과한다」가 **여기서 깨진다.** 초과 프로퍼티 검사와 **다른 검사**이기 때문이다.
- ★ `TS2561` 은 `TS2353` 의 변형이다 — **이름이 비슷한 키가 대상에 있을 때** 제안까지 붙는다.
- ★★ `draw(mixed)` 가 통과하는 것이 이 검사의 한계다 — **반은 맞고 반은 오타**인 객체를 못 잡는다.

### 4. ★★ 진단 **2건** — `{ a: 1, b: 2 }` 는 **통과**하고, 타입 이름이 **서로 다르다**

**출력**

```ts
// ex.06d.ts
// 유니온이 대상일 때 — 어느 타입 이름이 진단에 나오나
interface A {
    a: number;
}
interface B {
    b: number;
}
type AB = A | B;

const bothKeys: AB = { a: 1, b: 2 };
const strayKey: AB = { a: 1, c: 3 };

interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
type Shape = Circle | Square;

const crossed: Shape = { kind: "circle", r: 1, side: 2 };
console.log(bothKeys, strayKey, crossed);
```

```text
===== tsc --pretty false --noEmit ex.06d.ts (tsc exit=1) =====
ex.06d.ts(11,30): error TS2353: Object literal may only specify known properties, and 'c' does not exist in type 'AB'.
ex.06d.ts(23,48): error TS2353: Object literal may only specify known properties, and 'side' does not exist in type 'Circle'.
```

**왜 그런가**

| 줄 | 결과 | 진단이 가리키는 이름 |
|---|---|---|
| `const bothKeys: AB = { a: 1, b: 2 }` | ★★ **통과** | — |
| `const strayKey: AB = { a: 1, c: 3 }` | **TS2353** | **`'AB'`** — 유니온 별칭 |
| `const crossed: Shape = { kind: "circle", r: 1, side: 2 }` | **TS2353** | **`'Circle'`** — 멤버 하나 |

- ★★★ 유니온 대상은 **키의 합집합**으로 본다. `a` 는 `A` 의 키, `b` 는 `B` 의 키라 둘 다 「아는 키」다.
- ★★ 그래서 판별 유니온에서 **남의 멤버 키가 조용히 통과**하는 자리가 생긴다.
- ★★ 세 번째 줄만 멤버 이름이 나온 것은 판별 필드 `kind: "circle"` 이 **먼저 멤버를 골랐기** 때문이다.\
  ★ 즉 진단의 타입 이름이 「**유니온 전체인가 한 멤버인가**」가 좁힘 여부를 알려 준다.

### 5. ★★★ 진단 **2건**(8·10행) — **반환 타입을 함수에 적었을 때만** 걸린다

**출력**

```ts
// ex.06e.ts
// 반환 자리의 비대칭 — 표기를 어디에 쓰느냐로 갈린다
interface Point {
    x: number;
    y: number;
}

function onFunction(): Point {
    return { x: 1, y: 2, z: 3 };
}
const onArrow = (): Point => ({ x: 1, y: 2, z: 3 });

const fromContext: () => Point = () => ({ x: 1, y: 2, z: 3 });
const fromContextFn: () => Point = function () {
    return { x: 1, y: 2, z: 3 };
};
console.log(onFunction(), onArrow(), fromContext(), fromContextFn());
```

```text
===== tsc --pretty false --noEmit ex.06e.ts (tsc exit=1) =====
ex.06e.ts(8,26): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06e.ts(10,45): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
```

**왜 그런가**

| 줄 | 표기를 어디에 썼나 | 결과 |
|---|---|---|
| `function onFunction(): Point { return { …z } }` | **함수**에 | **TS2353** |
| `const onArrow = (): Point => ({ …z })` | **화살표**에 | **TS2353** |
| `const fromContext: () => Point = () => ({ …z })` | **변수**에 | ★★ **통과** |
| `const fromContextFn: () => Point = function () { … }` | **변수**에 | ★★ **통과** |

- ★★★ 반환 타입을 함수에 직접 적으면 리터럴이 `Point` 와 **직접** 맞붙는다 — 그 자리에서 검사가 돈다.
- ★★★ 변수 쪽에 함수 타입을 적으면 먼저 함수의 **추론된 반환 타입**(`{ x; y; z }`)이 만들어지고, 그 다음 **함수끼리** 비교된다.\
  그때 리터럴은 이미 「직접 놓인 것」이 아니라서 검사가 안 돈다.
- ★★ 실무 영향 — **콜백·이벤트 핸들러처럼 문맥 타입으로 쓰는 자리에서는 이 검사가 사실상 꺼진다.**
- ★ 고치는 법도 한 글자다 — 함수 쪽에 반환 타입을 적으면 다시 걸린다.

### 6. ★★★ 방출에 검사가 **한 줄도 없다** — 키는 **셋**, `"z" in` 은 **`true`**

**출력**

```ts
// ex.06f.ts
// 검사를 통과한 뒤 런타임에 여분 키가 남아 있는지 본다
interface Point {
    x: number;
    y: number;
}
function keysOf(pt: Point) {
    return Object.keys(pt);
}

const src = { x: 1, y: 2, z: 3 };
const bySpread: Point = { ...src };

console.log("변수 경유   :", keysOf(src));
console.log("단언 경유   :", keysOf({ x: 1, y: 2, z: 3 } as Point));
console.log("스프레드    :", Object.keys(bySpread));
console.log("JSON        :", JSON.stringify(bySpread));
console.log("'z' in      :", "z" in bySpread);
```

```text
===== tsc --pretty false ex.06f.ts (tsc exit=0) =====
===== 방출된 ex.06f.js =====
"use strict";
function keysOf(pt) {
    return Object.keys(pt);
}
const src = { x: 1, y: 2, z: 3 };
const bySpread = { ...src };
console.log("변수 경유   :", keysOf(src));
console.log("단언 경유   :", keysOf({ x: 1, y: 2, z: 3 }));
console.log("스프레드    :", Object.keys(bySpread));
console.log("JSON        :", JSON.stringify(bySpread));
console.log("'z' in      :", "z" in bySpread);
```

```text
===== node ex.06f.js (node exit=0) =====
변수 경유   : [ 'x', 'y', 'z' ]
단언 경유   : [ 'x', 'y', 'z' ]
스프레드    : [ 'x', 'y', 'z' ]
JSON        : {"x":1,"y":2,"z":3}
'z' in      : true
```

**왜 그런가**

| 확인 | 값 |
|---|---|
| `keysOf(src)` | `[ 'x', 'y', 'z' ]` |
| `keysOf({ … } as Point)` | `[ 'x', 'y', 'z' ]` — 단언은 **사라졌다** |
| `Object.keys(bySpread)` | `[ 'x', 'y', 'z' ]` — 타입은 `Point` 인데 키가 셋이다 |
| `JSON.stringify(bySpread)` | `{"x":1,"y":2,"z":3}` |
| `"z" in bySpread` | **`true`** |

- ★★★ 방출된 파일에 검사 코드가 **한 줄도 없다.** `as Point` 가 사라졌고 `{ ...src }` 는 그대로다.
- ★★ 즉 이 검사는 **막을 뿐 지우지 않는다.** `const bySpread: Point` 라고 적었어도 객체에는 `z` 가 있다.
- ★ 그래서 그 객체를 서버로 보내면 `z` 가 **같이 간다.** 여분 키를 진짜로 없애려면 **런타임에서 골라 담아야** 한다.
- ★ 「타입이 `Point` 니까 `z` 는 없겠지」가 여기서 깨진다 — [**01번 주제**](../01-what-ts-adds-and-erases/)의 결론 그대로다.

### 7. ★★ 「직접 적었다」는 **의도**의 증거이기 때문이다

**왜 그런가**

- 리터럴을 그 자리에 **방금 적었다**는 것은 「이 타입에 맞추려고 쓴 것」이라는 뜻이다.\
  거기 모르는 키가 있으면 **오타이거나 착각**일 확률이 높다 — 잡아 주는 게 이득이다.
- 반대로 **이미 있는 변수**는 다른 데서도 쓰인다. 여분 키가 **정상**일 수 있으므로 막으면 손해다.
- ★★ 그래서 이 검사는 **할당 가능성 규칙을 바꾸지 않는다.** 규칙은 여전히 「더 많아도 된다」이고([**05번 주제**](../05-structural-typing/)),\
  이 검사는 그 위에 **문법 형태로** 덧씌운 별개의 층이다.
- ★ 한 줄로 — **「값이 틀렸다」가 아니라 「방금 쓴 것 같은데 오타 아니냐」를 묻는 것**이다.

### 8. ★★★ 근거 둘 — **값이 같은데 결과가 갈린다** · **빠져나가는 길이 다섯이다**

**왜 그런가**

- 근거 ① — 1번에서 **같은 값**이 변수 경유로는 통과하고 리터럴로는 `TS2353` 이었다.\
  타입 시스템의 규칙이라면 **값이 같으면 결과도 같아야** 한다. 갈리는 것은 **문법 형태**다.
- 근거 ② — 빠져나가는 길이 다섯이다.

```text
  ① 변수에 담았다가 넘긴다        const v = { x, y, z };  take(v);
  ② 스프레드로 만든다             const s: Point = { ...v };
  ③ 단언을 붙인다                 { x, y, z } as Point
  ④ 인덱스 시그니처를 섞는다      Point & Record<string, unknown>
  ⑤ 제네릭으로 추론시킨다         f<T extends Point>({ x, y, z })
```

- ★★ 근거 ③ — 6번에서 본 대로 **방출을 한 글자도 안 바꾼다.** 통과하든 막히든 런타임 객체가 같다.
- ★ 그래서 읽는 법은 하나다 — **오타 잡이**. 여분 키를 진짜로 막아야 하면 런타임 검증이 필요하다.

### 9. ★★★ **`as` 는 끄고 `satisfies` 는 안 끈다**

**왜 그런가**

| | 이 검사 | 넓히기(추론) | 성격 |
|---|---|---|---|
| `{ … } as Point` | **끈다**(통과) | 타입을 `Point` 로 **갈아 치운다** | 「내가 책임진다」는 선언 |
| `{ … } satisfies Point` | ★ **안 끈다**(`TS2353`) | 추론된 리터럴 타입을 **그대로 둔다** | 「이 타입에 맞게 썼는지 확인해 달라」 |

- ★★ 2번의 진단 2건 중 하나가 정확히 이것이다 — `byAssert` 는 통과하고 `bySatisfies` 는 `TS2353` 이다.
- ★ 일관적이다 — `satisfies` 의 목적이 「**리터럴을 이 타입에 맞게 썼는지 확인**」이므로 오타 잡이가 포함되는 것이 맞다.
- ★ 그래서 **리터럴에 `as` 를 붙이는 습관이 위험하다** — 이 검사를 포함해 여러 검사를 한 번에 끈다.

### 10. ★★ **공통 키가 하나만 생겨도 풀린다** — 그래서 「반은 맞는 오타」를 못 잡는다

**왜 그런가**

- `TS2559` 의 발동 조건은 둘이다 — ① 대상이 **약한 타입**(프로퍼티가 전부 선택) ② 원본과 **공통 키가 0개**.
- 3번에서 둘 다 확인했다 —

| 상황 | 결과 |
|---|---|
| `draw(wrong)` · `wrong = { colour }` | **TS2559** — 공통 키 0 |
| `draw(mixed)` · `mixed = { colour, width }` | **통과** — `width` 하나로 풀린다 |
| `half(forHalf)` · `Half` 에 필수 `id` 가 있다 | **통과** — 약한 타입이 아니다 |

- ★★ 그래서 못 잡는 모양은 「**옵션 객체에 맞는 키 하나 + 오타 난 키 하나**」다. 실무에서 가장 흔한 모양이기도 하다.
- ★ 리터럴로 직접 넘기면 그때는 `TS2353`/`TS2561` 이 잡는다 — **변수로 조립하는 습관이 이 검사를 피해 간다.**

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 리터럴을 **직접 놓을 때만** 검사가 돈다 · 약한 타입에는 **별도 검사**가 있다 · 할당 가능성 자체는 「더 많아도 된다」 그대로다 · 검사는 **방출을 바꾸지 않는다** |
| **설정에 달린 것** | ★ **이 주제에는 거의 없다** — `--strict false` 로 다시 던져 **진단 여섯 건이 글자 하나까지 같은 것**을 확인했다(1번의 둘째 블록). 다만 이 문서의 모든 블록은 `tsc` 에 파일을 직접 줘서 `tsconfig.json` 을 안 읽은 상태다 |
| **이 판(7.0.2)의 관찰** | 진단이 가리키는 **타입 이름**(`'AB'` 대 `'Circle'`) · **반환 자리의 비대칭**(문맥 반환 타입에서는 안 걸린다) · **제네릭 추론이 통과시키는 것** · 진단 문구 전문 |

- ★ 「**에러가 안 난 줄」도 이 판의 관찰이다.** 그래서 소스 전문을 같은 자리에 실어 누구나 다시 던질 수 있게 했다.
- ★★ 판이 오르면 다시 던질 1순위는 **5번의 반환 자리 비대칭**이다 — 규칙으로 못 박힌 것이 아니라 검사 순서에서 나온 결과다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 리터럴 여섯 자리 | `--noEmit ex.06a.ts` | exit 1 · `TS2353` **6건**(14·15·17·19·25·28행) · 변수 경유 2줄 통과 |
| 같은 파일 `strict` 끔 | `--noEmit --strict false ex.06a.ts` | exit 1 · **같은 6건** — 글자 하나까지 같다 |
| 빠져나가는 길 | `--noEmit ex.06b.ts` | exit 1 · **2건**(18·19행) · 변수·스프레드·단언·인덱스·제네릭 통과 |
| 약한 타입 | `--noEmit ex.06c.ts` | exit 1 · `TS2559` 1건 + `TS2561` 1건 · `draw(mixed)`·`half(forHalf)` 통과 |
| 유니온 대상 | `--noEmit ex.06d.ts` | exit 1 · `TS2353` **2건** · 이름이 `'AB'` 와 `'Circle'` 로 갈림 · `{ a, b }` 통과 |
| 반환 자리 | `--noEmit ex.06e.ts` | exit 1 · `TS2353` **2건**(8·10행) · 문맥 반환 타입 2벌 통과 |
| 방출·실행 | `tsc ex.06f.ts` + `node ex.06f.js` | tsc exit 0 · node exit 0 · 키 셋 · `"z" in` 이 `true` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- **반환 자리의 비대칭** — 이 판에서 네 벌을 던져 갈랐다. 규칙으로 못 박힌 것이 아니다.
- 유니온 진단이 **유니온 이름을 쓰는가 멤버 이름을 쓰는가** — 좁힘 시점에 달렸다.
- **제네릭 추론이 검사를 통과시키는 것** — 추론기 동작이다. 「여분이라는 판정이 안 선다」만 성질로 읽는다.
- 진단 문구 전문 — 코드(`TS2353`·`TS2559`·`TS2561`)가 더 오래 간다.

**안 돌려 본 것**

- 매핑 타입으로 「정확히 이 키들만」을 만드는 수법 — [목록의 **26번 주제**](../26-mapped-types/)에서 던진다.
