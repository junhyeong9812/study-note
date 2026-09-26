# ts/syntax/23 — `typeof` 타입 연산자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** · `node` **v18.19.1** · `javac` **21.0.5** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ **6번이 이 주제의 본체다** — 방출된 `.js` 와 `node` 출력이 두 `typeof` 를 갈라 준다.\
> ★★★ **1번은 「진단이 두 건뿐인 것」이 결론**이다 — 아홉 군데를 물었고 둘이 답했다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **충돌하지 않는다** — 공간이 둘이라 이름이 겹칠 수가 없다

**출력**

```ts
// ex.23a.ts
// 값 공간과 타입 공간은 따로다 -- 같은 이름이 양쪽에 각각 산다
const box = { w: 1, h: 2 };
type box = { deep: true };

const asType: box = { deep: true };
const asValue: typeof box = { w: 1, h: 2 };

interface Only {
    q: 1;
}
const useOnlyAsType: Only = { q: 1 };
const useOnlyAsValue = Only;

const plain = 1;
type FromPlain = plain;

class Both {
    x = 0;
}
const bothAsValue = Both;
const bothAsType: Both = new Both();

const deepPath: typeof box.w = 1;
const arrow = (n: number) => n + 1;
const fromArrow: typeof arrow = (n) => n;
console.log(asType, asValue, useOnlyAsType, useOnlyAsValue, bothAsValue, bothAsType, deepPath, fromArrow, null as unknown as FromPlain);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23a.ts (tsc exit=1) =====
ex.23a.ts(12,24): error TS2693: 'Only' only refers to a type, but is being used as a value here.
ex.23a.ts(15,18): error TS2749: 'plain' refers to a value, but is being used as a type here. Did you mean 'typeof plain'?
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 2·3 | ★★★ `const box` 와 `type box` | **진단 없음** — 두 공간에 각각 등록된다 |
| 5 | `box` 를 타입 자리에 | 통과 — 타입 공간의 `box` |
| 6 | `typeof box` 를 타입 자리에 | 통과 — 값 공간의 `box` 를 다리로 건너왔다 |
| 11 | `Only` 를 타입 자리에 | 통과 |
| 12 | ★★★ `Only` 를 값 자리에 | **`TS2693`** — 「only refers to a type …」 |
| 15 | ★★★ `plain` 을 타입 자리에 | **`TS2749`** — 「refers to a value … Did you mean 'typeof plain'?」 |
| 20·21 | ★★ `Both` 를 값 자리 · 타입 자리 | **둘 다 통과** — 클래스는 양쪽에 산다 |
| 23·25 | `typeof box.w` · `typeof arrow` | 통과 — 이름 경로다 |

- ★★★ **진단이 둘뿐인 것이 이 문항의 답이다.** 이름을 꺼내 쓴 자리 **아홉 군데** 중 **일곱이 조용**하고 **둘만 답했다.**\
  「경고가 안 났다」가 아니라 **「몇 군데 물었고 몇 군데가 답했나」** 로 읽어야 근거가 된다.
- ★★★ 2·3행이 이 주제의 뼈대다. **같은 파일, 같은 스코프에 같은 이름을 둘 선언했는데 충돌이 없다.**\
  `const` 는 **값 공간에만**, `type` 은 **타입 공간에만** 들어가기 때문이다.
- ★★★ 12행 `TS2693` 과 15행 `TS2749` 가 **서로의 거울**이다 — 한쪽은 「타입을 값으로 썼다」, 다른 쪽은 「값을 타입으로 썼다」.\
  ★ **15행이 더 친절하다.** 컴파일러가 **「`typeof plain` 이라고 쓰려던 것 아니냐」** 며 **처방까지** 말한다.
  **그 처방의 이름이 이 주제의 제목이다.**
- ★★ 20·21행이 **예외**다. `class` 는 **두 공간에 동시에 등록**되므로 값으로도 타입으로도 쓸 수 있다.
  `enum` 도 같다(4번).
- ★ 5행과 6행을 나란히 읽어라 — **한 줄 차이로 서로 다른 `box` 를 가리키는데 둘 다 통과한다.**

```text
  값 공간                     타입 공간
  +---------------+           +---------------+
  | box  {w,h}    |           | box {deep}    |   ★ 같은 이름, 충돌 없음
  | plain 1       |           | Only {q}      |
  | Both  class   | <-------> | Both  class   |   ★ 클래스만 양쪽에
  +---------------+           +---------------+
        │  TS2749 (15행)            │  TS2693 (12행)
        └─ 값을 타입 자리에          └─ 타입을 값 자리에
```

### 2. ★★ 이름 경로는 되고 **표현식은 안 된다** — 괄호 하나가 가른다

**출력**

```ts
// ex.23b.ts
// typeof 뒤에 올 수 있는 것과 없는 것 -- 표현식은 안 된다
const box = { w: 1, h: 2 };

type Ok1 = typeof box;
type Ok2 = typeof box.w;
type Ok3 = typeof box["w"];

type No1 = typeof { w: 1 };
type No2 = typeof (box);
type No3 = typeof box.w + 1;
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23b.ts (tsc exit=1) =====
ex.23b.ts(8,19): error TS1003: Identifier expected.
ex.23b.ts(9,19): error TS1003: Identifier expected.
ex.23b.ts(10,25): error TS1005: ';' expected.
```

**왜 그런가**

| 줄 | 형태 | 답 |
|---|---|---|
| 4 | `typeof box` | 통과 |
| 5 | `typeof box.w` | 통과 — **점 경로도 된다** |
| 6 | `typeof box["w"]` | 통과 — **대괄호도 된다** |
| 8 | `typeof { w: 1 }` | **`TS1003`** 「Identifier expected」 |
| 9 | ★★★ `typeof (box)` | **`TS1003`** — **괄호 하나 때문이다** |
| 10 | `typeof box.w + 1` | **`TS1005`** 「';' expected」 |

- ★★ **이 파일만 따로 떼어 던졌다.** 파스 에러가 나면 **같은 파일의 의미 검사가 통째로 멈추기** 때문이다 —
  1번의 `TS2693`·`TS2749` 와 한 파일에 두면 **뒤엣것이 아예 안 나온다.** 그래서 파일을 갈랐다.
- ★★★ **9행이 가장 뜻밖이다.** 4행과 뜻이 완전히 같은데 **괄호 하나 때문에 막힌다.**\
  파서가 `typeof` 뒤에서 **이름 경로 문법**만 읽기 때문이다 — `(` 를 보는 순간 **식별자가 아니라고 판단**한다.
- ★★ 8행과 9행이 **같은 코드**(`TS1003`)이고 10행만 다르다(`TS1005`).\
  앞의 둘은 「식별자가 와야 할 자리에 다른 게 왔다」, 뒤엣것은 「타입이 이미 끝났는데 `+` 가 더 있다」이다.
- ★ **열 번호가 근거다** — `8,19` · `9,19` · `10,25`. 값으로는 못 가르는 것을 `(행,열)` 이 가른다.
- ★ 표현식의 타입이 필요하면 **그 표현식을 `const` 에 먼저 담아야** 한다. 한 줄이 는다.

```text
  파서가 typeof 뒤에서 읽는 문법

  typeof <이름경로>
           ├── box              OK
           ├── box.w            OK   (점 접근)
           ├── box["w"]         OK   (대괄호 접근)
           ├── (               TS1003  ← 여기서 끝
           ├── {               TS1003  ← 여기서 끝
           └── box.w + ...     TS1005  ← 타입이 끝난 줄 알고 ';' 를 찾는다
```

### 3. ★★★ `typeof Point` 는 **정적 쪽**이다 — 인스턴스가 아니다

**출력**

```ts
// ex.23c.ts
// typeof Class 는 인스턴스가 아니라 생성자다 -- 가장 많이 틀리는 자리
class Point {
    x = 0;
    static origin = new Point();
    static make(): Point {
        return new Point();
    }
}

const instanceSide: null = null as unknown as Point;
const staticSide: null = null as unknown as typeof Point;
const backToInstance: null = null as unknown as InstanceType<typeof Point>;

const wrong: typeof Point = new Point();
const right: typeof Point = Point;
const instWrong: Point = Point;

function makeFromCtor(Ctor: typeof Point): Point {
    return new Ctor();
}
function makeFromInstance(Ctor: Point): Point {
    return new Ctor();
}
console.log(instanceSide, staticSide, backToInstance, wrong, right, instWrong, makeFromCtor, makeFromInstance);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23c.ts (tsc exit=1) =====
ex.23c.ts(10,7): error TS2322: Type 'Point' is not assignable to type 'null'.
ex.23c.ts(11,7): error TS2322: Type 'typeof Point' is not assignable to type 'null'.
ex.23c.ts(12,7): error TS2322: Type 'Point' is not assignable to type 'null'.
ex.23c.ts(14,7): error TS2739: Type 'Point' is missing the following properties from type 'typeof Point': origin, make, prototype
ex.23c.ts(16,26): error TS2741: Property 'x' is missing in type 'typeof Point' but required in type 'Point'.
ex.23c.ts(22,16): error TS2351: This expression is not constructable.
  Type 'Point' has no construct signatures.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 10 | `Point` | **`Point`** — 인스턴스 쪽 |
| 11 | ★★★ `typeof Point` | **`typeof Point`** — 정적 쪽 |
| 12 | `InstanceType<typeof Point>` | **`Point`** — 왕복이 닫힌다 |
| 14 | ★★★ `typeof Point` 자리에 `new Point()` | **`TS2739`** — 빠진 것: `origin`·`make`·`prototype` |
| 15 | `typeof Point` 자리에 `Point` | **통과** |
| 16 | ★★ `Point` 자리에 `Point`(값) | **`TS2741`** — 빠진 것: `x` |
| 19 | `Ctor: typeof Point` 에 `new Ctor()` | **통과** |
| 22 | ★★ `Ctor: Point` 에 `new Ctor()` | **`TS2351`** — 「no construct signatures」 |

- ★★★ **14행이 이 문항의 별이다.** 진단이 **빠진 속성을 이름으로 나열한다** — `origin`·`make`·`prototype`.\
  셋 다 **`static` 이거나 생성자 쪽에만** 있는 것이다. **즉 `typeof Point` 는 정적 쪽 + 생성 시그니처다.**\
  ★ 컴파일러가 「정적 쪽이다」라고 말하지는 않지만 **이름 셋으로 증명**해 준다.
- ★★★ **16행이 그 거울**이다. 반대로 넣으면 **인스턴스 필드 `x` 가 없다**고 한다.
  두 진단을 나란히 읽으면 **두 쪽이 완전히 다른 타입**임이 드러난다.
- ★★ 22행 — 인스턴스 타입에는 **생성 시그니처가 없다.** `new` 를 쓰려면 매개변수를 `typeof Cls` 로 적어야 한다(19행).
- ★★ 12행 — `InstanceType<typeof Point>` 가 다시 `Point` 다. **정적 쪽에서 인스턴스 쪽으로 돌아오는 길**이 있다.\
  그 속은 [**25번 주제**](../25-infer-and-recursive-conditional-types/)의 `infer` 다.
- ★ 10·11행의 탐침이 **별칭 이름을 그대로 찍는다**(`Point` · `typeof Point`).
  ★★ 그래도 **두 이름이 다르다는 것**이 이미 답이다 — 펼쳐 보려면 진단 쪽(14·16행)을 읽어야 한다.
  **이것이 「탐침이 늘 펼쳐 주지는 않는다」의 실측 사례다.**

### 4. ★★ enum 하나에서 **네 이름**이 나오고 **전부 다르다**

**출력**

```ts
// ex.23d.ts
// enum 은 값이자 타입이다 -- 그리고 keyof typeof 관용구
enum Color {
    Red,
    Blue,
}
const pick: Color = Color.Red;
const asType: null = null as unknown as Color;
const asValueType: null = null as unknown as typeof Color;
const names: null = null as unknown as keyof typeof Color & {};
const member: null = null as unknown as Color.Red;

const setting = { level: 3, label: "높음", deep: { on: true } };
const settingKeys: null = null as unknown as keyof typeof setting & {};
const settingValue: null = null as unknown as (typeof setting)["level"];
const settingDeep: null = null as unknown as (typeof setting)["deep"];

const frozen = { 가: 1, 나: 2 } as const;
const frozenValues: null = null as unknown as (typeof frozen)[keyof typeof frozen];
console.log(pick, asType, asValueType, names, member, settingKeys, settingValue, settingDeep, frozenValues);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23d.ts (tsc exit=1) =====
ex.23d.ts(7,7): error TS2322: Type 'Color' is not assignable to type 'null'.
ex.23d.ts(8,7): error TS2322: Type 'typeof Color' is not assignable to type 'null'.
ex.23d.ts(9,7): error TS2322: Type '"Blue" | "Red"' is not assignable to type 'null'.
  Type '"Blue"' is not assignable to type 'null'.
ex.23d.ts(10,7): error TS2322: Type 'Color.Red' is not assignable to type 'null'.
ex.23d.ts(13,7): error TS2322: Type '"deep" | "label" | "level"' is not assignable to type 'null'.
  Type '"deep"' is not assignable to type 'null'.
ex.23d.ts(14,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.23d.ts(15,7): error TS2322: Type '{ on: boolean; }' is not assignable to type 'null'.
ex.23d.ts(18,7): error TS2322: Type '1 | 2' is not assignable to type 'null'.
  Type '1' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 6 | `const pick: Color = Color.Red;` | **통과** — 왼쪽은 타입 공간, 오른쪽은 값 공간 |
| 7 | `Color` | **`Color`** — 멤버 전체의 타입 |
| 8 | `typeof Color` | **`typeof Color`** — 값 객체의 타입 |
| 9 | ★★★ `keyof typeof Color & {}` | **`"Blue" \| "Red"`** — 이름 유니온 |
| 10 | `Color.Red` | **`Color.Red`** — 멤버 하나의 타입 |
| 13 | `keyof typeof setting & {}` | **`"deep" \| "label" \| "level"`** |
| 14 | `(typeof setting)["level"]` | **`number`** |
| 15 | `(typeof setting)["deep"]` | **`{ on: boolean; }`** |
| 18 | ★★★ `(typeof frozen)[keyof typeof frozen]` | **`1 \| 2`** — `as const` 덕분이다 |

- ★★★ 7·8·9·10행이 **enum 하나에서 나오는 네 이름**이고 **하나도 같지 않다.**
  「`Color` 하나만 알면 된다」고 생각하면 틀린다.
- ★★ 6행이 재미있다 — **한 줄에 두 공간이 다 나온다.** 왼쪽 `Color` 는 타입, 오른쪽 `Color` 는 값이다.
  `class` 와 마찬가지로 **enum 은 양쪽에 산다.**
- ★★★ 9행의 `keyof typeof Color` 가 **관용구**다. **먼저 `typeof` 가 값을 타입으로 건너오게 하고, 그다음 `keyof` 가 키를 뽑는다.**
  순서를 뒤집을 수 없다 — `typeof` 없이 `keyof Color` 를 쓰면 **멤버 타입의 키**를 묻는 전혀 다른 질문이 된다.
- ★★ 13행이 같은 관용구를 **평범한 객체**에 쓴 것이다. enum 전용이 아니다.
- ★★ 14·15행에는 **괄호가 필요하다.** ★ 2번에서 `typeof (box)` 가 막혔던 괄호와 **자리가 다르다** —
  여기 괄호는 `typeof setting` **전체**를 감싼다.
- ★★★ **18행이 14행과의 대비**다. `as const` 가 붙은 객체에서는 값이 **`1 | 2`** 로 온다.
  `as const` 가 없으면 **`number`** 였다(14행이 그 증거다).
  ★ [**11번 주제**](../11-literal-types-and-as-const/)가 **굳히는 쪽 정본**이고 여기는 **굳힌 것을 꺼내는 쪽**이다.
- ★ 9·13행에 `& {}` 가 붙은 것은 **유니온을 펼쳐 찍게 하려는 장치**다 — [**22번 주제**](../22-keyof-and-indexed-access-types/)가 정본이다.

### 5. ★★★ 키 목록에 **`Opts` 가 없다** — 목록의 공백이 답이다

**출력**

```ts
// mod23.ts
export const version = "1.0";
export function greet(who: string): string {
    return "안녕 " + who;
}
export interface Opts {
    deep: boolean;
}
```

```ts
// ex.23e.ts
// typeof import(...) -- 모듈을 열지 않고 그 모듈의 값 공간을 타입으로 받는다
const moduleKeys: null = null as unknown as keyof typeof import("./mod23") & {};
const oneExport: null = null as unknown as typeof import("./mod23").version;
const fnExport: null = null as unknown as typeof import("./mod23").greet;
const typeExport: null = null as unknown as import("./mod23").Opts;
console.log(moduleKeys, oneExport, fnExport, typeExport);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.23e.ts (tsc exit=1) =====
ex.23e.ts(2,7): error TS2322: Type '"greet" | "version"' is not assignable to type 'null'.
  Type '"greet"' is not assignable to type 'null'.
ex.23e.ts(3,7): error TS2322: Type '"1.0"' is not assignable to type 'null'.
ex.23e.ts(4,7): error TS2322: Type '(who: string) => string' is not assignable to type 'null'.
ex.23e.ts(5,7): error TS2322: Type 'Opts' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 2 | ★★★ `keyof typeof import("./mod23") & {}` | **`"greet" \| "version"`** — ★ **`Opts` 가 없다** |
| 3 | `typeof import("./mod23").version` | **`"1.0"`** |
| 4 | `typeof import("./mod23").greet` | **`(who: string) => string`** |
| 5 | ★★ `import("./mod23").Opts` (`typeof` 없음) | **`Opts`** — 통과한다 |

- ★★★ **2행의 답에 빠진 것이 이 문항의 핵심이다.** `mod23.ts` 는 **셋**을 export 하는데 키는 **둘**이다.\
  **`interface Opts` 는 값 공간에 없으므로 모듈의 값 객체에도 없다.**
  1번의 `TS2693` 과 **같은 사실**을 모듈 단위에서 다시 본 것이다.
- ★★★ **5행이 대비**다. `typeof` 를 **빼면** 같은 모듈의 **타입 공간**이 열리고 `Opts` 가 나온다.\
  **`import(…)` 에는 문이 둘 있고, `typeof` 를 붙이느냐가 어느 문으로 들어가느냐를 정한다.**
- ★★ 3행 — `export const version = "1.0"` 이 **리터럴 타입 그대로** 온다(`const` 라서 안 넓어진다).
- ★★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**\
  `typeof import("./mod23")` 를 **통째로** 탐침하면 진단이 그 모듈을 **절대 경로로** 찍는다.
  그 경로는 **작업 디렉토리에 달려 있어** 다른 머신에서 재현되지 않는다.\
  그래서 그 탐침을 **싣지 않고** `keyof` 를 씌워 **키만** 물었다 — 그런데 **바꿔 물은 쪽이 더 강한 근거**였다.
  「목록에 무엇이 없나」가 「모양이 어떻게 생겼나」보다 이 주제에 잘 맞는다.\
  ★ **바꾼 창이 못 보는 것** — 모듈 타입의 **전체 모양**은 여전히 못 본다. 키 목록과 낱낱의 export 만 안다.

### 6. ★★★ **타입 자리의 `typeof` 는 사라지고 값 자리의 `typeof` 는 남는다**

**출력**

```ts
// ex.23f.ts
// 글자가 같고 하는 일이 다르다 -- 타입 자리의 typeof 와 값 자리의 typeof
const setting = { level: 3, label: "높음" };

type Setting = typeof setting;
const copy: Setting = { level: 9, label: "낮음" };

const runtimeTag: string = typeof setting;

function describe(x: string | number): string {
    if (typeof x === "string") {
        return "문자 " + x.length;
    }
    return "숫자 " + x.toFixed(1);
}

class Shape {}
const ctorTag: string = typeof Shape;

console.log(copy.level, runtimeTag, describe("가나"), describe(3), ctorTag);
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e23f ex.23f.ts (tsc exit=0) =====
===== 방출된 e23f/ex.23f.js =====
"use strict";
// 글자가 같고 하는 일이 다르다 -- 타입 자리의 typeof 와 값 자리의 typeof
const setting = { level: 3, label: "높음" };
const copy = { level: 9, label: "낮음" };
const runtimeTag = typeof setting;
function describe(x) {
    if (typeof x === "string") {
        return "문자 " + x.length;
    }
    return "숫자 " + x.toFixed(1);
}
class Shape {
}
const ctorTag = typeof Shape;
console.log(copy.level, runtimeTag, describe("가나"), describe(3), ctorTag);
```

```text
===== node e23f/ex.23f.js (node exit=0) =====
9 object 문자 2 숫자 3.0 function
```

**왜 그런가**

| 소스 줄 | 방출물 | 답 |
|---|---|---|
| 4 `type Setting = typeof setting;` | ★★★ **줄 자체가 없다** | 타입 공간이 통째로 지워졌다 |
| 5 `const copy: Setting = {…};` | `const copy = {…};` | 주석만 벗겨졌다 |
| 7 `const runtimeTag: string = typeof setting;` | ★★★ `const runtimeTag = typeof setting;` | **`typeof` 가 남았다** |
| 10 `if (typeof x === "string")` | 그대로 | ★ **두 층에 동시에 산다** |
| 17 `const ctorTag: string = typeof Shape;` | `const ctorTag = typeof Shape;` | 남았다 |
| — | `node` 출력 | `9 object 문자 2 숫자 3.0 function` |

- ★★★ **종료 코드가 `0` 이고 진단이 0줄이다.** 이 문항의 근거는 **에러가 아니라 방출물**이다.
- ★★★ 4행과 7행을 나란히 읽어라. **같은 여섯 글자 `typeof` 가 한쪽은 통째로 사라지고 한쪽은 그대로 남았다.**\
  가른 것은 **자리**다 — 타입 자리냐 값 자리냐.
- ★★ `node` 출력의 **`object`** 가 `typeof setting` 의 런타임 답이다.\
  같은 글자를 **타입 자리**에서 물었으면 `{ level: number; label: string; }` 였다. **완전히 다른 답이다.**
- ★★★ `node` 출력의 마지막 **`function`** 이 특히 크다. `typeof Shape` 가 런타임에 **`function`** 이다 —
  **클래스도 런타임에는 함수**다. 타입 자리에서 같은 글자를 물으면 3번에서 본 **정적 쪽**이 나온다.
- ★★ 10행은 **두 층에서 동시에 산다** — 런타임에는 분기이고 검사에서는 좁히기다.
  `문자 2`·`숫자 3.0` 이 **런타임에도 맞게 돌았다**는 증거다.
  좁히기 규칙은 [**12번 주제**](../12-narrowing/)가 정본이다.
- ★ 방출물에 **`Setting` 이라는 이름이 어디에도 없다.** 타입 이름으로는 런타임에 아무것도 못 묻는다.

```text
  같은 글자, 두 운명

   type Setting = typeof setting;     ──X  사라진다
   const runtimeTag = typeof setting; ──>  남는다 -> "object"
   const ctorTag    = typeof Shape;   ──>  남는다 -> "function"

  ★ 자리가 운명을 정한다
```

★★ 런타임 `typeof` 의 정본은
`` JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **01번**([값의 종류와 `typeof`](../../../js/syntax/01-value-types-and-typeof/)) ``다.
돌려주는 문자열의 종류와 `typeof null` 의 함정은 그쪽이고, 여기서는 **글자가 같다는 사실**만 다룬다.

### 7. ★★★ 반대 방향 다리가 있으면 **소거가 깨진다**

**왜 그런가**

- ★★★ 한 문장으로 — **타입을 값으로 만드는 문법이 있으면 타입이 런타임에 남아야 하고, 그러면 「지우기만 하면 JS 가 된다」가 성립하지 않는다.**
- ★★ 그 전제는 [**01번 주제**](../01-what-ts-adds-and-erases/)가 세운 것이고, [**02번 주제**](../02-type-checking-vs-emit/)가
  **검사 패스와 방출 패스가 갈린다**는 구조로 받쳐 준다. 6번의 방출물이 그 전제를 눈으로 보여 준 것이다.
- ★★ **`class` 와 `enum` 이 양쪽에 사는 것은 예외가 아니다.** 그 둘은 **원래 값을 만드는 선언**이라
  값 공간에 들어갈 것이 **처음부터 있다.** `interface` 에는 없다.
- ★ 그래서 실무 처방도 하나다 — 런타임에 필요한 것이면 **값으로 먼저 만들고** `typeof` 로 타입을 끌어와라.
  타입을 먼저 만들고 값을 짜내려고 하면 길이 없다.

**교차 갈래 — 지우개가 닿는 범위가 다르면 무엇이 달라지나**

```java
// Erased.java
import java.util.List;

public class Erased {
    interface Opts {
        boolean deep();
    }

    static boolean isStrings(Object o) {
        return o instanceof List<String>;
    }

    static Object useTypeAsValue() {
        return Opts;
    }
}
```

```text
===== javac -d jout Erased.java (javac exit=1) =====
Erased.java:9: error: Object cannot be safely cast to List<String>
        return o instanceof List<String>;
               ^
Erased.java:13: error: cannot find symbol
        return Opts;
               ^
  symbol:   variable Opts
  location: class Erased
2 errors
```

| 줄 | 자리 | 답 |
|---|---|---|
| 9 | `o instanceof List<String>` | 「Object cannot be safely cast to List<String>」 — **제네릭 인자가 런타임에 없다** |
| 13 | ★★★ `Opts` 를 값 자리에 | 「cannot find symbol」 + **`symbol: variable Opts`** |

- ★★★ 13행이 놀랍다 — **javac 가 「변수 이름 공간에서 찾았다」고 스스로 말한다.**
  TS 의 `TS2693` 과 **같은 사실**이다. **이름 공간이 둘이라는 것은 언어를 안 가린다.**
- ★★★ **그런데 지우개 범위가 다르다.** Java 는 **제네릭 인자만** 지우고 `List` 라는 클래스는 런타임에 **남는다**
  (`instanceof List` 는 된다). TS 는 **타입 층 전체**를 지운다 — `interface Opts` 는 방출물에 흔적이 없다.
- ★★ 그래서 진단의 결이 다르다 — Java 는 「**안전하게 캐스트할 수 없다**」, TS 는 「**그런 값이 없다**」.
  ★ Java 는 **절반만 지워서** 절반짜리 검사가 런타임에 남았고, TS 는 **전부 지워서** 런타임 검사를 아예 포기했다.
- ★ 소거 쪽 정본은
  `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([타입 소거 — 런타임에 없는 것·제네릭 배열 금지·브리지 메서드](../../../java/syntax/19-type-erasure/)) ``다.

### 8. ★★ 파서가 `typeof` 뒤에서 **이름 경로 문법만** 읽기 때문이다

**왜 그런가**

- ★★★ 값 자리와 타입 자리는 **문법 자체가 다르다.** 값 자리의 `(box)` 는 **괄호식**이라는 표현식 문법으로 읽히지만,
  타입 자리에서 `typeof` 뒤는 **식별자로 시작하는 이름 경로**만 받는다.
- ★★ 그 증거가 코드 번호다 — `TS1003` 은 **「Identifier expected」**, 즉 **식별자가 와야 할 자리**라고 말한다.
  의미 검사가 아니라 **파서**가 낸 것이다(코드가 `TS1xxx` 대다).
- ★★ 그래서 2번의 세 줄이 **의미 검사에 도달하지도 못했다.** 같은 파일의 뒤 줄이 통째로 안 보이는 이유도 이것이다.
- ★ 실무 처방 — 표현식의 타입이 필요하면 **`const` 에 담고** 그 이름에 `typeof` 를 건다. 그러면 이름 경로가 된다.

### 9. ★★★ 매개변수에는 **`typeof Cls`** 를 적는다 — 반대로 적으면 `TS2351`

**왜 그런가**

| 적은 것 | 무엇을 받나 | 안에서 `new` 가 되나 |
|---|---|---|
| `Ctor: typeof Point` | **클래스 값 자체** | ★ **된다**(3번 19행) |
| `Ctor: Point` | **인스턴스** | ★★ **안 된다** — `TS2351` 「no construct signatures」(3번 22행) |

- ★★★ 경계를 한 줄로 — **「`new` 를 할 것이냐」로 가른다.** 할 것이면 `typeof Cls`, 이미 만든 것을 받을 것이면 `Cls`.
- ★★ 잘못 적었을 때의 코드가 **자리마다 다르다** —
  값을 넣는 자리면 `TS2739`(정적 멤버가 없다) 또는 `TS2741`(인스턴스 필드가 없다),
  `new` 를 쓰는 자리면 `TS2351`(생성 시그니처가 없다).
- ★ `typeof Cls` 는 **그 클래스에 묶인다.** 아무 클래스나 받으려면 `new (…args: never[]) => T` 꼴을 직접 적어야 한다.
  ★★ 이 배치에서는 **그 꼴을 23 에서 안 던졌다** — [**25번 주제**](../25-infer-and-recursive-conditional-types/)에서 `infer` 와 함께 던졌다.
- ★ 되돌아오는 길은 `InstanceType<typeof Cls>` 다(3번 12행).

### 10. ★★ `typeof import(…)` 는 **값 공간**, `import(…).T` 는 **타입 공간**

**왜 그런가**

- ★★★ 한 줄로 — **`typeof` 가 붙으면 그 모듈이 런타임에 내놓는 객체를 보고, 안 붙으면 그 모듈이 선언한 타입을 본다.**
- ★★ 5번 2행이 값 공간 쪽 증거다 — 키가 **`"greet" | "version"`** 이고 `Opts` 가 **없다.**
- ★★ 5번 5행이 타입 공간 쪽 증거다 — `import("./mod23").Opts` 가 **통과**한다.
- ★ 값 공간 쪽으로 열면 **`keyof` 를 이어 붙일 수 있다**(4번의 관용구와 같은 꼴).
  타입 공간 쪽으로 열면 **그 타입 이름을 바로 쓴다.**
- ★ 대가 — 어느 쪽이든 **경로 문자열이 타입 안에 박힌다.** 파일을 옮기면 타입이 깨진다.
  ★★ 그리고 **진단에 절대 경로가 나올 수 있다**(5번의 제5의 상태).

### 11. ★★ `typeof` 가 **먼저** 돌고 `keyof` 가 나중이다

**왜 그런가**

- ★★★ `keyof typeof x` 는 **`keyof (typeof x)`** 로 읽힌다. **값을 타입으로 건너오게 한 뒤** 그 타입의 키를 뽑는다.
  순서를 뒤집은 것은 **문법상 뜻이 없다**(`typeof` 는 값 이름을 받지 타입을 받지 않는다).
- ★★ 그래서 관용구가 **두 주제를 잇는 자리**가 된다 —
  건너오기는 여기(23), 키 뽑기는 [**22번 주제**](../22-keyof-and-indexed-access-types/)다.
- ★★ **경계 한 줄** — 22 는 「`keyof T` 가 **무엇으로 펼쳐지나**」(인덱스 시그니처·배열·`private`·유니온)를 다루고,
  23 은 「`T` **자리에 값을 어떻게 놓나**」를 다룬다. **`keyof typeof x` 는 둘이 만나는 한 점이다.**
- ★ 실전에서 이 관용구가 가장 많이 쓰이는 곳은 **`as const` 객체의 키 목록**이다(4번 13·18행).
  [**11번 주제**](../11-literal-types-and-as-const/) → 23 → 22 순으로 읽으면 사슬이 닫힌다.

### 12. ★★ 세 층 — 그리고 `strict` 가 [21번](../21-inference-control-const-and-noinfer/)과 달랐다

**왜 그런가**

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 값 공간과 타입 공간의 **분리** · `typeof` 가 **한 방향** 다리 · `class`·`enum` 이 **양쪽에 등록** · `typeof Cls` 가 **정적 쪽** · **소거** |
| **★ 이 판(7.0.2)의 관찰** | 진단 **문구**와 `TS1003`/`TS1005` 같은 **파서 코드** · 진단이 **빠진 속성을 이름으로 나열**하는 것 · 탐침이 **별칭 이름을 그대로 찍는 것** · 유니온 **표시 순서** |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 계산하지 않고 **적은 그대로** 남긴다 |
| **★ 부적용 — 4창(격자)** | 한계를 칠 것이 이 주제에 없다 — [**25번 주제**](../25-infer-and-recursive-conditional-types/)의 창이다 |
| **흔들린다** | `typeof import(…)` 를 통째로 물었을 때의 **절대 경로** — 그래서 **안 실었다** |
| **안 잰 것** | **검사 시간**·메모리 — 재지 않았고 수치를 적지 않았다 |

**5창을 닫는 근거**

```text
===== tsc --pretty false -t es2022 --strict --declaration --emitDeclarationOnly --outDir d22f ex.22f.ts (tsc exit=0) =====
===== 방출된 d22f/ex.22f.d.ts =====
interface User {
    id: number;
    name: string;
}
export type Keys = keyof User;
export declare const oneKey: keyof User;
export type Cond = string extends string ? "가" : "나";
export declare const frozen: readonly ["가", "나"];
export type Elem = (typeof frozen)[number];
export {};
```

- ★★★ `.d.ts` 가 `keyof User` 도, 조건부도, `(typeof frozen)[number]` 도 **풀지 않고 그대로** 남긴다.
  **「무엇으로 계산됐나」를 묻는 질문에 `.d.ts` 는 답하지 않는다.** 그 질문은 **2창(탐침)** 의 몫이다.
- ★ `.d.ts` 가 나은 자리는 **여러 줄을 한 번에 훑을 때**뿐이다. 이 주제에는 그런 자리가 없다.

**`strict` 대조**

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.23a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.23e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★★ **다섯 파일 전부 한 글자도 안 갈렸다.**
- ★★★ **[21번 주제](../21-inference-control-const-and-noinfer/)와 다른 결과**다 — 거기서는 **여섯 중 하나**가 갈렸다
  (제약이 가변 배열인 자리에서 `const` 타입 매개변수의 효과가 사라졌다).
- ★★ 그러므로 「**`--strict` 는 늘 상관없다**」도 「**늘 상관있다**」도 틀렸다. **자리마다 던져 봐야 한다.**
- ★ 여기서 안 갈리는 이유를 한 줄로 — **`typeof` 는 추론을 하지 않는다.** 선언된 타입을 **그대로 가져올 뿐**이다.
  `strict` 가 바꾸는 것은 주로 **추론과 널 취급**인데 이 주제에는 그 둘이 걸린 칸이 없다.
  ★★ 그래도 **이것은 이 판의 관찰이다** — 탐침 자체가 `strictNullChecks` 에 기대는데도 출력이 같았다.

**유니온 표시 순서**

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.22a.ts    5회 md5 가짓수 1
ex.24a.ts    5회 md5 가짓수 1
ex.25b.ts    5회 md5 가짓수 1
```

- ★★ 같은 명령을 5회 돌려 **md5 가짓수가 1** 이다. 4번 9행의 `"Blue" | "Red"` 순서가 **안 흔들렸다.**
- ★★★ 그래도 **관찰이지 보장이 아니다.** 판이 오르면 다시 찍어야 한다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `javac -version` · `rustc --version` | `Version 7.0.2` · `v18.19.1` · `javac 21.0.5` · `rustc 1.92.0` |
| ★★★ 두 공간 | `--noEmit ex.23a.ts` | exit 1 · **2건** — 아홉 군데 중 **둘만** 답했다(`TS2693`·`TS2749`) |
| `typeof` 문법 경계 | `--noEmit ex.23b.ts` | exit 1 · **3건** — `TS1003` 둘 · `TS1005` 하나 |
| ★★★ `typeof Cls` | `--noEmit ex.23c.ts` | exit 1 · **6건** — `TS2739`·`TS2741`·`TS2351` |
| enum 과 `keyof typeof` | `--noEmit ex.23d.ts` | exit 1 · **8건** — 9행이 `"Blue" \| "Red"` |
| `typeof import(…)` | `--noEmit ex.23e.ts` | exit 1 · **4건** — 2행 키 목록에 `Opts` **없음** |
| ★★★ 본체 — 방출 | `--outDir e23f ex.23f.ts` | ★ **exit 0 · 진단 0줄** · `type Setting` 줄이 **사라짐** |
| ★★★ 본체 — 실행 | `node e23f/ex.23f.js` | exit 0 · `9 object 문자 2 숫자 3.0 function` |
| 교차 갈래 | `javac -d jout Erased.java` | exit 1 · **2건** — `symbol: variable Opts` |
| 5창 부적용 | `--declaration --emitDeclarationOnly ex.22f.ts` | ★ exit 0 · `.d.ts` 가 **계산하지 않는다** |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★★★ **하나도 안 갈림**([21번](../21-inference-control-const-and-noinfer/)과 다르다) |
| 반복 실행 | 같은 명령 **5회**(★ `ex.22a.ts`·`ex.24a.ts`·`ex.25b.ts` — **이 주제의 파일은 아니다**) | ★★ md5 **가짓수 1** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **진단 문구 전문** — `TS2693`·`TS2749`·`TS2739`·`TS2741`·`TS2351`·`TS1003`·`TS1005` 라는 **코드**가 더 오래 간다.
- ★★★ **파서 코드와 열 번호**(`TS1003` 이 나는 자리) — 문법 오류의 분류는 판에 매인다.
- ★★ 진단이 **빠진 속성을 이름으로 나열**해 주는 것(`origin, make, prototype`) — 형식이 바뀔 수 있다.
- ★★ 탐침이 **별칭 이름을 그대로 찍는 것**(`typeof Point`·`Color`) — 펼쳐 찍도록 바뀔 수 있다.
- ★★ 유니온 원소의 **표시 순서**(`"Blue" \| "Red"`) — ★ **이 주제의 파일로는 반복 실행을 안 했다.** 배치의 다른 세 파일에서 5회 동일했을 뿐이다.
- ★ 방출된 `.js` 의 **들여쓰기와 줄 순서** — 방출기의 형식이다.
- ★ `--strict` 를 꺼도 안 갈리는 것 — **이 다섯 파일에 한한 관찰**이다.

**안 돌려 본 것**

- **오버로드된 함수에 `typeof`** — **안 던졌다.** [**16번 주제**](../16-function-types-and-overloads/)가 오버로드의 정본이다.
- **제네릭 함수에 `typeof`** — **안 던졌다.**
- **`typeof this`·`typeof globalThis`** — **안 던졌다.**
- **`unique symbol` 과 `typeof`** — **안 던졌다.** README 의 「뺀 것」에 있다.
- **`namespace` 안의 이름에 `typeof`** — **안 던졌다.** 목록의 **34번 주제**.
- **`import type` 과 `typeof import(…)` 의 방출 차이** — **안 던졌다.** 목록의 **36번 주제**.
- **`const enum` 의 방출** — **안 던졌다.** 목록의 **31번 주제**.
- **`typeof` 가 검사 시간에 주는 영향** — **재지 않았고 수치를 적지 않았다.**
