# ts/syntax/22 — `keyof` 와 인덱스 접근 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 **2창**(`null` 탐침)이다 —
> `keyof T` 안에 무엇이 들었는지는 **소스 어디에도 안 적혀 있으므로** 컴파일러에게 물어야 한다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · `javac` **21.0.5**.
> 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — `keyof` 와 인덱스 접근 타입은 **TS 2.1** 부터다.
>
> ★★★ **추론된 타입을 눈으로 보는 법** — 블록에 `const p: null = null as unknown as X;` 가 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ **그런데 이 주제에서는 탐침이 메아리를 돌려주는 자리가 있다** — 1번이 그 자리다. 거기서부터 생각하라.
> ★★ **진단이 안 나는 줄도 답이다.** 「조용하다」가 무슨 뜻인지 매번 따져라.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. `keyof` 를 여섯 가지 타입에 걸면 (예측)

```ts
// ex.22a.ts
// keyof 가 무엇으로 펼쳐지나 -- 인터페이스 · 인덱스 시그니처 · any · 유니온 · 교차
interface User {
    id: number;
    name: string;
    active: boolean;
}
const asName: null = null as unknown as keyof User;
const expanded: null = null as unknown as keyof User & {};

interface StringDict {
    [k: string]: number;
}
const strKeys: null = null as unknown as keyof StringDict;

interface NumberDict {
    [k: number]: number;
}
const numKeys: null = null as unknown as keyof NumberDict;

interface Mixed {
    [k: string]: number;
    fixed: number;
}
const mixedName: null = null as unknown as keyof Mixed;
const mixedKeys: null = null as unknown as keyof Mixed & {};

const anyKeys: null = null as unknown as keyof any;
const unknownKeys: null = null as unknown as keyof unknown;
const neverKeys: null = null as unknown as keyof never;

interface A {
    x: number;
    shared: string;
}
interface B {
    y: boolean;
    shared: string;
}
const unionKeys: null = null as unknown as keyof (A | B);
const interKeys: null = null as unknown as keyof (A & B);
console.log(asName, expanded, strKeys, numKeys, mixedName, mixedKeys, anyKeys, unknownKeys, neverKeys, unionKeys, interKeys);
```

- 7행과 8행은 **같은 `keyof User`** 인데 답이 같은가 다른가?
- 13행·18행·25행 — 인덱스 시그니처가 있을 때 답이 무엇인가? 25행에서 `"fixed"` 는 어디 갔는가?
- 27·28·29행 중 **진단이 안 나는 줄**은 어느 것이고, 그것은 무슨 뜻인가?
- 39행과 40행 중 답이 **더 긴 쪽**은 어느 것인가?

### 2. 배열에 `keyof` 를 걸면 (예측)

```ts
// ex.22b.ts
// 배열의 keyof -- number 만이 아니다. 멤버십으로 하나씩 물어본다
const arrName: null = null as unknown as keyof string[];
const arrKeys: null = null as unknown as keyof string[] & {};
const tupleKeys: null = null as unknown as keyof [1, 2] & {};

const isNumber: keyof string[] = 0;
const isLength: keyof string[] = "length";
const isMap: keyof string[] = "map";
const isDigitString: keyof string[] = "0";

const onlyStringKeys: null = null as unknown as `${keyof string[] & string}`;
console.log(arrName, arrKeys, tupleKeys, isNumber, isLength, isMap, isDigitString, onlyStringKeys);
```

- 3행은 무엇으로 펼쳐지는가? 그 출력에서 **눈에 띄는 것**이 무엇인가?
- 6·7·8·9행 중 **막히는 줄**은 어느 것인가? 진단 코드는?
- 4행(튜플)은 3행(배열)과 무엇이 다른가?

### 3. 클래스와 굳힌 객체에 걸면 (예측)

```ts
// ex.22c.ts
// keyof 는 public 만 본다 -- private · protected · static · as const
class Account {
    id = 1;
    label = "가";
    private secret = "나";
    protected note = "다";
    static bank = "은행";
    static make(): Account {
        return new Account();
    }
    balance(): number {
        return 0;
    }
}
const instanceKeys: null = null as unknown as keyof Account & {};
const staticKeys: null = null as unknown as keyof typeof Account & {};

class Hash {
    #hidden = 1;
    shown = 2;
}
const hashKeys: null = null as unknown as keyof Hash & {};

const frozen = { 가: 1, 나: 2 } as const;
const plainObj = { 가: 1, 나: 2 };
const frozenKeys: null = null as unknown as keyof typeof frozen & {};
const plainKeys: null = null as unknown as keyof typeof plainObj & {};
const frozenValues: null = null as unknown as (typeof frozen)[keyof typeof frozen];
const plainValues: null = null as unknown as (typeof plainObj)[keyof typeof plainObj];
console.log(instanceKeys, staticKeys, hashKeys, frozenKeys, plainKeys, frozenValues, plainValues);
```

- 15행에 `secret`·`note`·`bank`·`balance` 중 무엇이 들어가는가?
- 16행은 15행과 무엇이 다른가? 거기에 **따로 끼어 있는 키**가 하나 있는데 무엇인가?
- 26·27행이 같은가 다른가? 28·29행은?

### 4. 대괄호로 꺼내면 (예측)

```ts
// ex.22d.ts
// T[K] -- 인덱스 접근 타입. 점 표기가 아니라 대괄호다
interface User {
    id: number;
    name: string;
    active: boolean;
}
const one: null = null as unknown as User["id"];
const two: null = null as unknown as User["id" | "name"];
const all: null = null as unknown as User[keyof User];
const missing: null = null as unknown as User["없는키"];

type Tup = readonly ["가", "나"];
const tupAt: null = null as unknown as Tup[0];
const tupAny: null = null as unknown as Tup[number];

const list = ["가", "나"];
const listElem: null = null as unknown as (typeof list)[number];

interface Nested {
    inner: { deep: boolean };
}
const deep: null = null as unknown as Nested["inner"]["deep"];
console.log(one, two, all, missing, tupAt, tupAny, listElem, deep);
```

- 7·8·9행의 답을 나란히 적을 수 있는가?
- 10행은 **진단이 나는가**? 난다면 코드가 무엇인가?
- 17행 `(typeof list)[number]` 는 무엇인가? 괄호를 빼면 어떻게 읽히는가?

### 5. 세 가지로 받은 `obj[key]` (예측)

```ts
// ex.22e.ts
// obj[key] 가 안전해지는 관용구 -- K extends keyof T 와 그 아래 두 단계
interface User {
    id: number;
    name: string;
    active: boolean;
}
const u: User = { id: 1, name: "가", active: true };

function getTight<T, K extends keyof T>(o: T, k: K): T[K] {
    return o[k];
}
const tight: null = getTight(u, "name");
getTight(u, "없는키");

function getLoose<T extends object>(o: T, k: keyof T) {
    return o[k];
}
const loose: null = getLoose(u, "name");

function getWide(o: Record<string, unknown>, k: string) {
    return o[k];
}
const wide: null = getWide(u as unknown as Record<string, unknown>, "없는키");

function setTight<T, K extends keyof T>(o: T, k: K, v: T[K]): void {
    o[k] = v;
}
setTight(u, "id", 2);
setTight(u, "id", "둘");
console.log(tight, loose, wide);
```

- 12행·18행·23행의 답을 나란히 적을 수 있는가?
- 13행은 무슨 진단인가? 진단에 **무엇이 찍히는가**?
- 28행과 29행 중 **막히는 쪽**은 어느 것인가?

### 6. `.d.ts` 에 무엇이 적히나 (예측)

```ts
// ex.22f.ts
// 다섯째 창을 닫는 근거 -- .d.ts 는 계산하지 않는다. 적은 그대로 남긴다
interface User {
    id: number;
    name: string;
}
export type Keys = keyof User;
export const oneKey: keyof User = "id";
export type Cond = string extends string ? "가" : "나";
export const frozen = ["가", "나"] as const;
export type Elem = (typeof frozen)[number];
```

- `Keys` 가 **펼쳐져서** 적히는가, **적은 그대로** 적히는가?
- `Cond`(조건부)는 어떤가?
- `frozen` 은 어떤가 — 이 줄만 다른 이유가 무엇인가?

### 7. 인덱스 시그니처가 이름 있는 키를 삼키는 이유 (왜)

- `interface Mixed { [k: string]: number; fixed: number }` 의 `keyof` 에서 `"fixed"` 가 사라지는 이유를 **유니온의 성질**로 설명할 수 있는가?

### 8. 유니온과 교차에서 방향이 뒤집히는 이유 (왜)

- `keyof (A | B)` 가 **교집합**이고 `keyof (A & B)` 가 **합집합**인 이유를 「값이 무엇인지 아느냐」로 설명할 수 있는가?

### 9. 탐침이 조용할 때 (경계)

- 1번 28행처럼 **진단이 안 나는** 탐침은 무엇을 뜻하는가? 그 답을 읽으려면 창을 어떻게 바꿔야 하는가?

### 10. `keyof` 를 쓸 자리와 안 쓸 자리 (경계)

- 키가 **런타임 문자열**로 들어오는 API 에 `K extends keyof T` 를 달면 어떻게 되는가?
- 그 타입에 **인덱스 시그니처가 하나 있으면** 이 주제의 값이 어떻게 되는가?

### 11. 20·23·24 와 잇기 (연결)

- [**20번 주제**](../20-generic-constraints-and-defaults/)의 `get(obj, key)` 관용구와 이 주제 5절은 **같은 코드**를 다른 쪽에서 본다. 각각 무엇을 정본으로 다루는가?
- [**23번 주제**](../23-typeof-type-operator/)는 **사슬이 아니라 직교하는 축**인데, 이 주제와 **어디서 한 번 만나는가**?
- 여기서 만든 **키 유니온**이 [**24번 주제**](../24-conditional-types-and-distribution/)에서 무엇이 되는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **tsc 7.0.2 구현** · **부적용인 창**에 해당하는 항목을 하나씩 댈 수 있는가?
- `--strict` 를 끄면 이 주제의 결론 중 무엇이 바뀌는가? [**21번 주제**](../21-inference-control-const-and-noinfer/)와 견주면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
