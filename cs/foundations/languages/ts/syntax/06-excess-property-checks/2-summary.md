# ts/syntax/06 — 초과 프로퍼티 검사 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Object Types: Excess Property Checks](https://www.typescriptlang.org/docs/handbook/2/objects.html#excess-property-checks) ·
> [Handbook — Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) ·
> [Handbook — Everyday Types: Type Assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions) ·
> [TSConfig — `strict`](https://www.typescriptlang.org/tsconfig/#strict).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 모든 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로
> 이 블록들은 설정 파일 없이도 그대로 재현된다.
> **버전** — 초과 프로퍼티 검사는 TS 1.6, 약한 타입 검사(`TS2559`)는 2.4, 오타 제안(`TS2561`)은 2.7,
> `satisfies` 는 4.9 부터다. 7.0 에서 이 넷 중 **사라진 것은 없다**(전부 이 판에서 받았다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**방출된 JS 전문**·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | `Object.keys` 의 순서 | 전부 문자열 키라 **삽입 순서**가 보장된다(JS 규칙) |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제는 **「진단이 안 난 줄」이 절반의 근거**다. 그래서 소스 전문을 진단과 같은 자리에 실었다.

## 한눈에 — 쉽게 말하면

**창구에 직접 내민 서류만 한 장씩 넘겨 본다.**

| 비유 | 실체 |
|---|---|
| 서류를 **방금 이 창구용으로 썼다** | **객체 리터럴을 타입이 정해진 자리에 직접 놓는 것** |
| 창구 직원이 「이 칸은 뭐죠?」라고 묻는다 | **초과 프로퍼티 검사** — `TS2353` |
| 「혹시 이거 쓰려던 거 아니에요?」 | **오타 제안** — `TS2561`, 「Did you mean to write …」 |
| 서류철에서 한 장 뽑아 내민다 | **변수에 담았다가 넘기는 것** — 검사가 **안 돈다** |
| ★ 칸이 **전부 선택**인 양식은 다르다 | **약한 타입 검사** — `TS2559`. **변수로 넘겨도 막는다** |
| 검사를 통과하든 말든 서류의 칸은 그대로다 | **런타임에 여분 키가 남는다** — 지워 주지 않는다 |

- ★★★ 한 줄로 — 「**같은 값인데 문법 형태로 갈린다. 그리고 갈라 낸 뒤에 아무것도 지우지 않는다.**」
- ★★ 그래서 이 검사는 **타입 시스템의 규칙이 아니라 오타 잡이**다. 빠져나가는 길이 **다섯이나** 있는 이유다.

```text
                          { x: 1, y: 2, z: 3 }
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
  변수에 담았다가 넘긴다                            리터럴을 직접 놓는다
  const v = { x, y, z };                            take({ x, y, z })
  take(v);                                          const p: Point = { x, y, z }
         │                                          [{ x, y, z }]
         │                                          return { x, y, z }
         ▼                                                   │
       통과                                                  ▼
   (모양이 더 많아도                                TS2353 — 'z' 가 없다
    할당은 된다)
```

```text
  검사 결과와 런타임이 서로 무관하다

    검사 시각                              실행 시각
  +--------------------+               +--------------------------+
  | take({x,y,z})      |               | Object.keys(...)         |
  |   -> TS2353        |               |   -> ['x','y','z']       |
  | take(v)            |               | JSON.stringify(...)      |
  |   -> 통과          |               |   -> {"x":1,"y":2,"z":3} |
  +--------------------+               +--------------------------+
        ↑ 막든 안 막든                        ↑ z 는 **언제나 거기 있다**
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **언제 도는 검사인가** — 「객체 리터럴을 직접 놓을 때」가 정확히 어느 자리들인가. 변수를 거치면 왜 안 도나.
2. **어디로 빠져나가나** — 통과시키는 길이 몇 개이고, **빠져나가지 못하는 것**은 무엇인가.
3. **무엇을 막아 주지 않나** — 이 검사를 통과했을 때와 걸렸을 때 **런타임 객체가 다른가**.

★ [**05번 주제**](../05-structural-typing/)가 「모양이 맞으면 들어간다」를 세웠다면, 여기는 **그 규칙 위에 덧붙은 예외 하나**를 끝까지 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **진단이 안 난 줄** | 「어디는 통과하는가」 — 빠져나가는 길이 전부 여기 있다 | [**05번 주제**](../05-structural-typing/)에서 이어받음 |
| ★★ **에러 코드 셋을 가르기** | `TS2353`·`TS2559`·`TS2561` 이 **서로 다른 검사**다 | ★ 이 주제의 고유 창 |
| ★★★ **방출된 `.js` + `node`** | 검사와 **무관하게** 여분 키가 남는 것 | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |
| **진단이 가리키는 타입 이름** | 유니온일 때 **어느 멤버 이름**이 나오나 | ★ 이 주제의 고유 창 |

★ **에러 코드를 가르는 것이 이 주제의 값이다.** 셋을 한 덩어리로 외우면 「변수로 넘기면 항상 통과한다」로 틀린다.

비용 — 컴파일 한 번.

### (1) ★★★ 리터럴을 직접 놓는 자리 — 여섯 군데

**언제 쓰나** — 「같은 값인데 왜 여기선 되고 저기선 안 되지」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **여섯 건**이고 전부 `TS2353` 이다. 소스의 **리터럴을 직접 놓은 자리도 정확히 여섯**이다.
- 14행 `const bad1: Point = { …, z: 3 }` — **변수 선언의 표기 자리**.
- 15행 `take({ …, z: 3 })` — **인자 자리**.
- 17행 `const inArray: Point[] = [{ …, z: 3 }]` — ★ **배열 원소**도 걸린다. 배열 리터럴이 한 겹 끼어도 통과 못 한다.
- 19행 `return { …, z: 3 }` — ★ **반환문**도 걸린다(단 **조건이 있다** — 5절을 보라).
- 25행 `{ inner: { a: 1, b: 2 } }` — ★ **중첩 리터럴**도 걸린다. 진단이 안쪽 타입을 익명으로 적는다 — 「does not exist in type '{ a: number; }'」.
- 28행 `later = { …, z: 3 }` — **이미 선언된 변수에 대입**하는 자리.
- ★★★ 그리고 **11·12행이 통과했다.** `const ok1: Point = viaVar` 와 `take(viaVar)` 는 **같은 값**인데 진단 목록에 없다.

```text
  리터럴을 직접 놓는 자리 — 이 판에서 전수로 받은 여섯
  ┌───────────────────────────────────────────────┬──────────┐
  │ const p: Point = { … }          변수 표기     │  TS2353  │
  │ take({ … })                     인자          │  TS2353  │
  │ const a: Point[] = [{ … }]      배열 원소     │  TS2353  │
  │ function f(): Point { return { … } }  반환문  │  TS2353  │
  │ { inner: { … } }                중첩          │  TS2353  │
  │ later = { … }                   대입          │  TS2353  │
  └───────────────────────────────────────────────┴──────────┘
    const v = { … };  take(v);   ← 변수를 거치면 **검사가 아예 안 돈다**
```

★★ 같은 파일을 **`--strict false`** 로 던지면 어떻게 되나. 파일은 한 글자도 안 바꿨다.

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
===== tsc --pretty false --noEmit --strict false ex.06a.ts (tsc exit=1) =====
ex.06a.ts(14,35): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(15,20): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(17,41): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(19,26): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.06a.ts(25,40): error TS2353: Object literal may only specify known properties, and 'b' does not exist in type '{ a: number; }'.
ex.06a.ts(28,23): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
```

- ★★★ **여섯 건이 글자 하나까지 같다.** 이 검사는 `strict` 묶음과 **무관한 상시 검사**다.
- ★ 그래서 이 주제는 「설정에 달린 칸」이 거의 없다 — 07·09 와 대비된다.

비용 — 없음. 검사 한 번이다.

### (2) ★★★ 빠져나가는 길 다섯 — 그리고 안 빠져나가는 하나

**언제 쓰나** — 「이 검사에 기대도 되나」를 판정할 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**뿐이다 — 18행과 19행. 앞의 여섯 줄이 전부 통과했다.
- `const byVar: Point = src` — **변수**. `const bySpread: Point = { ...src }` — **스프레드**.
- `{ … } as Point` — **단언**. `Point & Record<string, unknown>` — **인덱스 시그니처**.
- ★★ `byGeneric({ x: 1, y: 2, z: 3 })` 도 **통과했다**. 매개변수가 `T extends Point` 라 **`T` 가 `{ x; y; z }` 로 추론**되고, 그러면 여분이 아니다 — **다섯째 길**이다.
- ★★★ 18행 `satisfies Point` 는 **막힌다.** 「검사만 하고 넓히지 않는다」는 연산자인데도 **초과 프로퍼티 검사는 그대로 돈다**.
- ★★ 19행 `{ ...src, w: 4 }` 가 재미있다 — 진단이 **`w` 만** 짚는다. 스프레드로 들어온 `z` 는 **같은 리터럴 안인데도 조용하다**.

```text
  { ...src, w: 4 }        src = { x, y, z }
      │        │
      │        └── 직접 적은 키   -> 검사 대상  -> TS2353 'w'
      └─────────── 스프레드로 온 키 -> 검사 대상 아님 -> 'z' 는 조용하다

  한 리터럴 안에서 **검사 대상이 갈린다.**
```

> **초과 프로퍼티 검사(excess property check)** — 객체 리터럴을 타입이 정해진 자리에 **직접** 놓을 때만 도는 추가 검사.\
> 예: `take({ x: 1, y: 2, z: 3 })` 은 `TS2353` 인데, 같은 객체를 변수에 담아 `take(v)` 로 넘기면 통과한다.

> **신선도(freshness)** — 「방금 이 자리에 맞추려고 쓴 리터럴인가」를 컴파일러가 들고 다니는 표시.\
> 예: 변수에 한 번 담기면 이 표시가 사라져 검사가 안 돈다. 이 문서에서는 「**직접 놓았나**」로 읽으면 된다.

비용 — 없음. 다만 **빠져나가는 길이 다섯**이라 이 검사에 기대면 안 된다.

### (3) ★★★ 전부 선택인 타입은 변수도 막는다 — 다른 검사다

**언제 쓰나** — 「변수로 넘기면 항상 통과한다」를 의심할 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**인데 **코드가 서로 다르다** — `TS2559` 와 `TS2561` 이다.
- 11행 `draw(wrong)` 은 **변수를 넘겼는데도** 막혔다. 문구가 「has no properties in common with type 'Opts'」다.\
  ★★★ `Opts` 는 **프로퍼티가 전부 선택**이라 **모양으로는 `{}` 도 통과**한다 — 그러면 오타가 전부 새어 나간다. 그래서 **따로 만든 검사**다.
- 12행 `draw({ colour: "red" })` 는 리터럴이라 초과 프로퍼티 검사가 먼저 잡고, 「**Did you mean to write 'color'?**」까지 붙는다.
- ★★ 15행 `draw(mixed)` 는 **통과했다.** `mixed` 에 `width` 가 있어 **공통 프로퍼티가 하나 생겼기 때문**이다 — `colour` 오타는 그대로 새어 나간다.
- ★★ 25행 `half(forHalf)` 도 **통과했다.** `Half` 에 **필수 프로퍼티 `id` 가 있어** 약한 타입이 아니다.

```text
  세 검사의 발동 조건이 다르다
  ┌──────────┬────────────────────────────┬───────────────────────────┐
  │ TS2353   │ 리터럴을 직접 놓았다       │ 모르는 키가 하나라도 있다 │
  │ TS2561   │ 〃 + 이름이 비슷한 키가 있다│ 「Did you mean …」이 붙는다│
  │ TS2559   │ ★ 변수여도 된다            │ 대상이 **전부 선택**이고   │
  │          │                            │ **공통 키가 0개**다       │
  └──────────┴────────────────────────────┴───────────────────────────┘
```

> **약한 타입(weak type)** — 프로퍼티가 **전부 선택**인 객체 타입. 모양으로만 보면 아무것이나 들어간다.\
> 예: `interface Opts { color?: string; width?: number }`. 공통 키가 하나도 없는 값을 넣으면 `TS2559` 다.

비용 — 없음. 대신 **공통 키가 하나만 생겨도 검사가 풀린다** — 그것이 이 검사의 한계다.

### (4) ★★ 유니온이 대상일 때 — 키의 합집합으로 본다

**언제 쓰나** — 판별 유니온에 리터럴을 넘기다가 「이 키가 왜 안 되지」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 10행 `const bothKeys: AB = { a: 1, b: 2 }` 가 **통과했다.** `a` 는 `A` 의 키, `b` 는 `B` 의 키다 — **어느 멤버의 키든 되면 된다**.
- 11행 `{ a: 1, c: 3 }` 은 막힌다. 진단이 **유니온 별칭 이름**을 쓴다 — 「does not exist in type 'AB'」.
- ★★ 23행 `{ kind: "circle", r: 1, side: 2 }` 는 막히는데 진단이 **`'Circle'`** 을 짚는다 — `AB` 때와 이름이 다르다.\
  판별 필드 `kind: "circle"` 이 **멤버 하나를 골라 준 뒤**에 검사가 돌았기 때문이다.
- ★ 즉 진단에 나오는 타입 이름이 **유니온 전체인지 한 멤버인지**가 「판별이 먹혔나」를 알려 준다.

```text
  { a: 1, b: 2 }  ──▶  A | B      통과 — 키의 **합집합**으로 본다
  { a: 1, c: 3 }  ──╳─▶ A | B      TS2353  "… in type 'AB'"

  { kind:"circle", r, side } ──╳─▶ Circle | Square
                                    TS2353  "… in type 'Circle'"
                                                    ↑ 판별 필드가 멤버를 고른 뒤였다
```

비용 — 없음. 다만 **합집합으로 보기 때문에 판별 유니온에서 남의 멤버 키가 조용히 통과**한다(10행).

### (5) ★★★ 반환 자리의 비대칭 — 표기를 어디에 쓰느냐로 갈린다

**언제 쓰나** — 「반환문도 검사한다」를 외웠는데 안 걸릴 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**이다 — 8행과 10행. 12·13행은 **통과했다.**
- `function onFunction(): Point { return { …z } }` — 반환 타입을 **함수에 적었다** → `TS2353`.
- `const onArrow = (): Point => ({ …z })` — 화살표에 적어도 같다 → `TS2353`.
- ★★★ `const fromContext: () => Point = () => ({ …z })` — **변수 쪽에 함수 타입을 적었다** → **통과**.
- ★★★ `const fromContextFn: () => Point = function () { return { …z } }` — 함수 표현식도 **통과**.
- ★★ 왜 갈리나 — 반환 타입을 **함수에 직접 적으면** 리터럴이 그 타입과 **직접** 맞춰진다. 반면 변수 쪽 표기는\
  함수의 **추론된 반환 타입**(`{ x; y; z }`)을 만든 뒤 **함수끼리** 비교한다 — 그때 리터럴은 이미 「직접 놓인 것」이 아니다.

```text
  function f(): Point { return { x, y, z } }
                  ↑ 리터럴이 Point 와 **직접** 맞붙는다        -> TS2353

  const f: () => Point = () => ({ x, y, z })
                             ↑ 먼저 () => { x; y; z } 가 만들어지고
                               그 다음 () => Point 와 **함수끼리** 비교된다  -> 통과
```

비용 — 없음. 대신 **콜백·핸들러를 문맥 타입으로 쓰는 코드에서는 이 검사가 사실상 꺼진다.**

### (6) ★★★ 검사를 통과하든 말든 런타임 객체는 같다

**언제 쓰나** — 「이 검사가 여분 키를 걸러 준다」를 의심할 때. **이 절이 이 주제의 마무리다.**

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

그림 해설 — 한 단계에 한 문장.

- 방출된 파일에 **검사가 한 줄도 없다.** `as Point` 는 사라졌고 `{ ...src }` 는 그대로 남았다.
- `keysOf(src)` 와 `keysOf({ … } as Point)` 가 **둘 다 `[ 'x', 'y', 'z' ]`** 다.
- ★★★ `const bySpread: Point = { ...src }` 의 키도 **셋**이다 — 타입은 `Point` 인데 **객체에는 `z` 가 있다.**
- `JSON.stringify` 가 `{"x":1,"y":2,"z":3}` 이고 `"z" in bySpread` 가 **`true`** 다.
- ★★ 즉 이 검사는 **아무것도 지우지 않는다.** 여분 키를 진짜로 없애려면 **런타임에서 직접 골라 담아야** 한다.

비용 — 0. 방출에 한 글자도 안 남는다. **그래서 보호도 0이다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  const p: Point = { x, y, z }        리터럴 직접   ★ 검사 돈다
  take({ x, y, z })                   인자          ★ 검사 돈다
  [{ x, y, z }]  ·  return { x, y, z } 배열·반환문  ★ 검사 돈다
  { inner: { a, b } }                 중첩          ★ 검사 돈다

  const v = { x, y, z }; take(v)      변수          검사 안 돈다
  { ...v }                            스프레드      검사 안 돈다
  { x, y, z } as Point                단언          검사 안 돈다
  Point & Record<string, unknown>     인덱스 시그니처 검사 안 돈다
  f<T extends Point>({ x, y, z })     제네릭 추론   검사 안 돈다

  { x, y, z } satisfies Point         ★ **검사 돈다**
```

**규칙 불릿**

- ★★★ **「직접 놓았나」가 기준이고 「값이 무엇인가」가 아니다.** 같은 값이 자리에 따라 갈린다.
- ★★ **자리는 여섯이다** — 변수 표기 · 인자 · 배열 원소 · 반환문 · 중첩 · 대입. 이 판에서 전수로 받았다.
- ★★ **빠져나가는 길은 다섯이다** — 변수 · 스프레드 · 단언 · 인덱스 시그니처 · **제네릭 추론**.
- ★★★ **`satisfies` 는 안 빠져나간다.** 「검사만 한다」는 연산자인데 이 검사는 그대로 돈다.
- ★★ **에러 코드가 셋이다** — `TS2353`(모르는 키) · `TS2561`(+ 오타 제안) · `TS2559`(**약한 타입**, 변수도 막는다).
- ★★ **대상이 유니온이면 키의 합집합으로 본다.** 판별 필드가 멤버를 고르면 진단이 **그 멤버 이름**을 쓴다.
- ★★★ **반환 자리는 표기 위치로 갈린다** — 함수에 적으면 걸리고, 변수의 함수 타입으로 주면 안 걸린다.
- ★★★ **검사는 아무것도 지우지 않는다.** 런타임 객체에 여분 키가 그대로 있다.

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 리터럴에 모르는 키          ->  TS2353  Object literal may only specify known properties, and 'z' …
2) 리터럴에 오타 난 키         ->  TS2561  … but 'colour' does not exist in type 'Opts'. Did you mean to write 'color'?
3) 전부 선택인 타입에 남의 객체 ->  TS2559  Type '{ colour: string; }' has no properties in common with type 'Opts'.
```

## 어디서 틀리나

- ★★★ 「**변수로 넘기면 언제나 통과한다**」 — 아니다. 대상이 **약한 타입**이면 `TS2559` 로 막힌다.
- ★★★ 「**이 검사가 여분 키를 걸러 준다**」 — 안 걸러 준다. `Object.keys` 가 `[ 'x', 'y', 'z' ]` 다.
- ★★ 「**`satisfies` 를 쓰면 통과한다**」 — 막힌다. `as` 와 헷갈리기 쉬운 자리다.
- ★★ 「**반환문은 무조건 검사한다**」 — 반환 타입을 **변수 쪽 함수 타입**으로 주면 안 걸린다.
- ★★ 「**유니온이면 어느 멤버든 키가 딱 맞아야 한다**」 — 아니다. **키의 합집합**이라 `{ a, b }` 가 `A | B` 에 들어간다.
- ★ 「**스프레드를 섞은 리터럴은 통째로 안 걸린다**」 — 직접 적은 키는 걸린다(`{ ...src, w: 4 }` 의 `w`).
- ★ 「**중첩 객체는 안 본다**」 — 본다. 진단이 안쪽 익명 타입을 그대로 적는다.
- ★ 「**제네릭 함수에도 걸린다**」 — 타입 매개변수가 리터럴로 추론되면 여분이 아니게 되어 안 걸린다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 객체 리터럴을 **직접 놓을 때만** 초과 프로퍼티 검사가 돈다 | 핸드북 「Excess Property Checks」. 같은 값이 변수 경유로 통과한 것이 결과다 |
| **언어 보장** | 할당 가능성 자체는 「**더 많아도 된다**」 그대로다 | 이 검사는 그 위에 **덧붙은** 것이다([**05번 주제**](../05-structural-typing/)) |
| **언어 보장** | **약한 타입**에는 별도 검사가 있다 | `TS2559` 의 문구가 그 규칙이다. `width` 를 하나 더하니 풀렸다 |
| **언어 보장** | 검사는 **방출을 바꾸지 않는다** | `ex.06f.js` 전문과 `node` 출력 — 여분 키가 그대로다 |
| **이 판(7.0.2)의 관찰** | 진단이 가리키는 **타입 이름**(`'AB'` 대 `'Circle'`) | 유니온을 얼마나 좁혀 놓고 검사하느냐에 달렸다 |
| **이 판의 관찰** | **반환 자리의 비대칭** — 문맥 반환 타입에서는 안 걸린다 | 이 판에서 네 벌을 던져 갈랐다. 판이 오르면 다시 던진다 |
| **이 판의 관찰** | 제네릭 추론이 검사를 통과시키는 것 | 추론기의 동작이다. 「여분이 아니게 된다」만 성질로 읽는다 |
| **설정에 달림** | `strict` 자체는 **이 검사를 켜고 끄지 않는다** | 이 문서의 블록은 전부 기본값(`strict` 켜짐)이다. 이 검사는 `strict` 와 무관한 상시 검사다 |

★ 「**에러가 안 난 줄도 근거다**」 — 이 주제에서는 **진단 목록에 없는 줄**을 세는 것이 절반이다.

## 언제 쓰고 언제 안 쓰나

| 기대도 되는 것 | 기대면 안 되는 것 |
|---|---|
| 설정 객체 리터럴의 **오타** 잡기 — `TS2561` 이 이름까지 짚어 준다 | **경계 밖에서 온 객체**의 여분 키 — 스키마 검증이 필요하다 |
| 약한 타입(전부 선택) 옵션 객체에 **엉뚱한 객체**가 들어오는 것 | 여분 키를 **지워 주는 것** — 아무것도 안 지운다 |
| 새로 쓴 리터럴이 **의도한 타입에 맞는지** 확인 | 콜백·핸들러의 반환 리터럴 — 문맥 타입이면 안 걸린다 |

| 쓴다 | 안 쓴다 |
|---|---|
| 리터럴을 **직접** 넘겨 검사를 받는다 | 중간 변수를 넣어 검사를 우회하는 것(의도치 않게 생긴다) |
| `satisfies` — 검사도 받고 추론도 살린다 | `as` — 이 검사를 포함해 **전부** 끈다 |
| 여분 키를 진짜로 막아야 하면 **런타임에서 골라 담는다** | 이 검사를 보안·계약 경계로 쓰는 것 |

## 핵심 문장

1. **「직접 놓았나」가 기준이다** — 값이 같아도 문법 형태로 갈린다.
2. **자리는 여섯, 빠져나가는 길은 다섯이다** — 그래서 이 검사는 규칙이 아니라 오타 잡이다.
3. **`satisfies` 는 빠져나가지 않는다** — `as` 와 다르다.
4. **약한 타입에는 별도 검사가 있다** — `TS2559` 는 **변수도 막는다.** 단 공통 키가 하나만 생겨도 풀린다.
5. **유니온 대상은 키의 합집합으로 본다** — 진단의 타입 이름이 좁힘 여부를 알려 준다.
6. **검사는 아무것도 지우지 않는다** — `Object.keys` 에 여분 키가 그대로 있다.

## 관련 자료

- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — 「**모양으로 정해진다**」는 그쪽이 정본이다. 여기는 **그 위에 덧붙은 예외 하나**만 끝까지 본다.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「검사가 방출에 안 남는다」의 근거는 그쪽.
- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — 객체 타입 **표기 형태**는 그쪽.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — 인덱스 시그니처가 **무엇인가**는 그쪽. 여기서는 **빠져나가는 길**로서만 썼다.
- [**09번 주제** — 유니온 타입](../09-union-types/) — 유니온의 일반 규칙은 그쪽. 여기서는 **검사 대상이 유니온일 때**만 본다.
- 목록의 **29번 주제**(`satisfies`) — `satisfies` 의 전면 서술은 그쪽. 여기서는 **이 검사를 안 끈다**는 한 칸만.
- 목록의 **30번 주제**(타입 단언과 non-null `!`) — `as` 가 무엇을 끄는지는 그쪽.
- [목록의 **19번 주제**](../19-generics-basics/)(제네릭 기본) — 타입 매개변수 추론은 그쪽. 여기서는 **다섯째 빠져나가는 길**로서만.

## 용어 풀이

> **초과 프로퍼티 검사(excess property check)** — 객체 리터럴을 타입이 정해진 자리에 **직접** 놓을 때만 도는 추가 검사.\
> 예: `take({ x: 1, y: 2, z: 3 })` 은 `TS2353`, 같은 객체를 변수로 넘기면 통과.

> **객체 리터럴(object literal)** — 중괄호로 그 자리에서 바로 쓴 객체 표현식.\
> 예: `{ x: 1, y: 2 }`. 변수에 담긴 뒤에는 이름으로 부르므로 리터럴이 아니다.

> **신선도(freshness)** — 「방금 이 자리에 맞추려고 쓴 리터럴인가」라는 표시. 변수에 담기면 사라진다.\
> 예: `const v = { x, y, z }` 뒤의 `v` 에는 이 표시가 없다.

> **약한 타입(weak type)** — 프로퍼티가 **전부 선택**인 객체 타입. 모양만으로는 아무것이나 들어간다.\
> 예: `interface Opts { color?: string; width?: number }`.

> **약한 타입 검사(weak type detection)** — 약한 타입 자리에 **공통 키가 하나도 없는** 값이 오면 막는 검사.\
> 예: `draw(wrong)` 이 `TS2559`. `width` 를 하나 더하면 통과한다.

> **판별 필드(discriminant)** — 유니온 멤버를 갈라 주는 리터럴 타입 프로퍼티.\
> 예: `kind: "circle"`. 이 값이 멤버를 고른 뒤에 초과 프로퍼티 검사가 돈다.

> **스프레드(spread)** — `...` 로 다른 객체의 키를 펼쳐 담는 문법.\
> 예: `{ ...src, w: 4 }`. 펼쳐 온 키는 이 검사의 대상이 아니다.

## 더 들어가면

- **이 검사를 진짜 강제로 만들고 싶으면** — 타입만으로는 안 된다. 목록의 **26번 주제**(매핑 타입)에서 「선언되지 않은 키는 `never`」를 만드는 수법이 있지만, 그것도 **리터럴 자리에서만** 돈다.
- **왜 `satisfies` 에서는 도는가** — `satisfies` 의 설계 목적이 「**리터럴을 이 타입에 맞게 썼는지 확인**」이라서, 그 확인에 오타 잡이가 포함되는 것이 일관적이다. `as` 는 반대로 「내가 책임진다」는 선언이라 전부 끈다.
- **약한 타입 검사의 한계** — 「공통 키 하나」가 기준이라 `{ colour, width }` 처럼 **반은 맞고 반은 오타**인 경우를 못 잡는다. 이 판에서 직접 확인했다(15행 통과).
- **`Exact<T>` 가 없는 이유** — 「정확히 이 키들만」을 표현하는 타입 연산자는 TS 에 없다. 이 검사가 그 자리를 **문법 형태로** 메우고 있고, 그래서 구멍이 많다.
