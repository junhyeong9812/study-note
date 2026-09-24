# ts/syntax/07 — 객체 타입 세부 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 「**에러가 안 나는 줄**」까지 세야 답이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**.
> ★★ **설정이 답을 바꾸는 주제**다 — `strict` 는 기본 `true` 지만
> `exactOptionalPropertyTypes` 와 `noUncheckedIndexedAccess` 는 **기본 `false`** 다.
> 옵션은 **배너에 적힌 것만** 줬고, 설정 파일로 던진 판은 그 설정 전문도 같은 블록에 있다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 선택 프로퍼티를 여섯 방법으로 쓰면 (예측)

```ts
// ex.07a.ts
// 선택 프로퍼티는 무엇으로 읽히나 — 그리고 언제 풀리나
interface User {
    id: string;
    nickname?: string;
}
declare const u: User;

const direct = u.nickname.length;
const guarded = u.nickname === undefined ? 0 : u.nickname.length;
const chained = u.nickname?.length;
const fallback = (u.nickname ?? "").length;

const probe: null = u.nickname;
const asString: string = u.nickname;

const full: User = { id: "a", nickname: "n" };
const partial: User = { id: "a" };
console.log(direct, guarded, chained, fallback, probe, asString, full, partial);
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- `null` 탐침(13행)이 말하는 `nickname` 의 타입은 무엇인가?

### 2. `readonly` 를 양쪽으로 넣어 보면 (예측)

```ts
// ex.07b.ts
// readonly 는 무엇을 막고 무엇을 안 막나
interface RO {
    readonly a: number;
}
interface RW {
    a: number;
}
declare const ro: RO;
declare const rw: RW;

ro.a = 1;

const roToRw: RW = ro;
const rwToRo: RO = rw;
roToRw.a = 2;

declare const roArr: readonly number[];
declare const rwArr: number[];
const arrToMutable: number[] = roArr;
const arrToReadonly: readonly number[] = rwArr;
roArr.push(1);
console.log(roToRw, rwToRo, arrToMutable, arrToReadonly);
```

- 진단은 **몇 건**이고, `const roToRw: RW = ro;` 와 `const rwToRo: RO = rw;` 는 각각 어느 쪽인가?
- 프로퍼티의 `readonly` 와 배열의 `readonly` 가 같은 규칙인가?

### 3. 인덱스 시그니처를 넣으면 무엇이 따라오나 (예측)

```ts
// ex.07c.ts
// 인덱스 시그니처가 선언된 프로퍼티에 거는 조건
interface Bag {
    [k: string]: number;
}
declare const bag: Bag;
const hit = bag.known;
const miss = bag.nothing.toFixed(2);

interface Bad {
    [k: string]: number;
    name: string;
}

interface Widened {
    [k: string]: number | string;
    count: number;
    label: string;
}

interface TwoKinds {
    [i: number]: string;
    [k: string]: string;
}

interface Clash {
    [i: number]: number;
    [k: string]: string;
}
console.log(hit, miss);
```

- 진단은 **몇 건**이고 **어느 인터페이스**인가?
- `const miss = bag.nothing.toFixed(2);` 는 어느 쪽인가?

### 4. 같은 파일을 설정 두 판으로 던지면 (예측)

```ts
// ex.07e.ts
// 같은 파일을 기본값과 플래그 두 개를 켠 설정으로 각각 던진다
interface Conf {
    host: string;
    port?: number;
}
interface Bag {
    [k: string]: number;
}
declare const bag: Bag;

const explicitUndefined: Conf = { host: "a", port: undefined };
const omitted: Conf = { host: "a" };
const reading = bag.missing.toFixed(2);
console.log(explicitUndefined, omitted, reading);
```

- 옵션을 안 준 판의 진단은 **몇 건**인가?
- `exactOptionalPropertyTypes` 와 `noUncheckedIndexedAccess` 를 켠 판은 **몇 건**이고 어느 줄인가?

### 5. 선언 방출이 수정자를 어떻게 적나 (예측)

```ts
// ex.07d.ts
// 세 수정자가 선언 방출에 어떻게 남는지 본다
export interface Conf {
    readonly host: string;
    port?: number;
    readonly tags?: readonly string[];
    [extra: string]: unknown;
}
export const conf: Conf = { host: "h" };
export const frozen = { a: 1, b: [2, 3] } as const;
export function pick(c: Conf) {
    return { host: c.host, port: c.port };
}
```

- `.d.ts` 에서 `readonly tags?: readonly string[];` 는 어떻게 나오는가?
- `pick` 의 반환 타입에서 `port` 는 어떻게 적히는가?

### 6. 런타임에 무엇이 남나 (예측)

```ts
// ex.07f.ts
// readonly 와 선택 프로퍼티가 런타임에 무엇을 하나
interface Conf {
    readonly host: string;
    port?: number;
    [k: string]: unknown;
}
const c: Conf = { host: "처음", port: 80 };

const loose = c as { host: string };
loose.host = "바뀜";

const omitted: Conf = { host: "b" };
const explicitUndefined: Conf = { host: "b", port: undefined };

console.log("readonly host :", c.host);
console.log("없는 키 읽기  :", c.nothing);
console.log("키 목록       :", Object.keys(c));
console.log("빠뜨린 쪽     :", omitted.port, JSON.stringify(omitted), "port" in omitted);
console.log("undefined 쪽  :", explicitUndefined.port, JSON.stringify(explicitUndefined), "port" in explicitUndefined);
```

- `readonly host` 는 실행 결과에서 무엇으로 찍히는가?
- 키를 뺀 객체와 `port: undefined` 를 넣은 객체의 `"port" in` 결과는 각각 무엇인가?

### 7. `?` 가 「표시」가 아니라 「타입 변경」인 이유 (왜)

- `?` 를 붙인 뒤 그 프로퍼티를 쓰려면 왜 한 단계가 더 필요한가?

### 8. `readonly` 가 보증이 아닌 이유 (경계)

- `readonly` 를 우회하는 길 **둘**을 대고, 그래도 쓸 값이 있는 이유를 말할 수 있는가?

### 9. 인덱스 시그니처의 대가 (경계)

- 인덱스 시그니처를 넣어서 **포기하게 되는 검사**는 무엇인가?

### 10. 두 플래그가 `strict` 밖인 이유 (연결)

- `exactOptionalPropertyTypes` 와 `noUncheckedIndexedAccess` 가 `strict` 에 안 들어 있는 이유를 실행 결과에 기대어 말할 수 있는가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
