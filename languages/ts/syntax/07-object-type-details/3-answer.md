# ts/syntax/07 — 객체 타입 세부 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ **설정이 답을 바꾸는 주제**라 옵션이 매 블록의 배너에 있고, 설정 파일로 던진 판은 그 전문도 같은 블록에 있다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **3건**(8·13·14행) — 타입은 「`string | undefined`」다

**출력**

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

```text
===== tsc --pretty false --noEmit ex.07a.ts (tsc exit=1) =====
ex.07a.ts(8,16): error TS18048: 'u.nickname' is possibly 'undefined'.
ex.07a.ts(13,7): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.07a.ts(14,7): error TS2322: Type 'string | undefined' is not assignable to type 'string'.
  Type 'undefined' is not assignable to type 'string'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `u.nickname.length` | 그냥 쓴다 | **TS18048** — possibly 'undefined' |
| `u.nickname === undefined ? 0 : u.nickname.length` | 비교로 좁힌다 | **통과** |
| `u.nickname?.length` | 옵셔널 체이닝 | **통과** |
| `(u.nickname ?? "").length` | 널 병합 | **통과** |
| `const probe: null = u.nickname` | ★ 탐침 | **TS2322** — 「Type 'string \| undefined' …」 |
| `const asString: string = u.nickname` | `string` 자리 | **TS2322** |
| `const partial: User = { id: "a" }` | 키를 아예 뺀다 | **통과** — `?` 의 목적 |

- ★★★ 탐침이 답을 글자로 적어 준다 — **`?` 는 타입에 `| undefined` 를 더한 것**이다(`strictNullChecks` 아래에서).
- ★★ 그래서 「**있을 수도 없을 수도 있다**」가 **값의 타입**으로 내려온다. 쓰는 자리마다 좁히기가 필요한 이유다.
- ★ 푸는 길이 셋이고 **셋 다 진단 목록에 없다** — 비교 · `?.` · `??`.

### 2. ★★★ 진단 **3건** — 두 대입은 **양방향으로 통과**한다

**출력**

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

```text
===== tsc --pretty false --noEmit ex.07b.ts (tsc exit=1) =====
ex.07b.ts(11,4): error TS2540: Cannot assign to 'a' because it is a read-only property.
ex.07b.ts(19,7): error TS4104: The type 'readonly number[]' is 'readonly' and cannot be assigned to the mutable type 'number[]'.
ex.07b.ts(21,7): error TS2339: Property 'push' does not exist on type 'readonly number[]'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `ro.a = 1` | `readonly` 에 대입 | **TS2540** |
| `const roToRw: RW = ro` | `readonly` → 보통 | ★★ **통과** |
| `const rwToRo: RO = rw` | 보통 → `readonly` | ★★ **통과** |
| `roToRw.a = 2` | 벗겨 낸 별칭에 대입 | ★★★ **통과** |
| `const arrToMutable: number[] = roArr` | `readonly T[]` → `T[]` | **TS4104** |
| `const arrToReadonly: readonly number[] = rwArr` | `T[]` → `readonly T[]` | **통과** |
| `roArr.push(1)` | `readonly` 배열에 `push` | **TS2339** |

- ★★★ **`readonly` 프로퍼티 수정자는 할당 가능성 판정에 안 들어간다.** 그래서 `RW` 로 받아 그 자리에서 대입하면 된다 — **우회가 한 줄**이다.
- ★★ 배열은 다르다. `readonly T[]` 는 `T[]` 자리에 **못 들어간다**(`TS4104`). `push` 는 **타입에 아예 없다**(`TS2339` — 「does not exist」).
- ★ 왜 갈리나 — 프로퍼티 `readonly` 는 **한 칸**의 규칙이고, `readonly T[]` 는 **메서드 목록이 다른 별개 타입**(`ReadonlyArray<T>`)이기 때문이다.
- ★ 그래서 `readonly` 는 **의도 표시로는 좋고 보증으로는 약하다.**

### 3. ★★★ 진단 **2건**(`Bad` 와 `Clash`) — 없는 키 읽기는 **통과**한다

**출력**

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

```text
===== tsc --pretty false --noEmit ex.07c.ts (tsc exit=1) =====
ex.07c.ts(11,5): error TS2411: Property 'name' of type 'string' is not assignable to 'string' index type 'number'.
ex.07c.ts(26,5): error TS2413: 'number' index type 'number' is not assignable to 'string' index type 'string'.
```

**왜 그런가**

| 인터페이스 | 무엇 | 결과 |
|---|---|---|
| `Bag` + `bag.nothing.toFixed(2)` | 선언에 없는 키를 읽는다 | ★★★ **통과** |
| `Bad { [k: string]: number; name: string }` | 프로퍼티가 인덱스 타입과 어긋남 | **TS2411** |
| `Widened { [k: string]: number \| string; … }` | 인덱스 타입을 넓혔다 | **통과** |
| `TwoKinds { [i: number]: string; [k: string]: string }` | 두 인덱스가 같은 타입 | **통과** |
| `Clash { [i: number]: number; [k: string]: string }` | 숫자 인덱스가 문자열 인덱스에 안 맞음 | **TS2413** |

- ★★ **인덱스 시그니처는** 「**이 객체의 모든 값이 만족해야 할 조건**」이다. 그래서 선언된 프로퍼티도 그 타입이어야 한다.
- ★★ 숫자 인덱스가 문자열 인덱스에 맞아야 하는 이유는 **JS 규칙**이다 — `obj[0]` 은 `obj["0"]` 과 같은 자리다.
- ★★★ 그리고 7행이 **진단 목록에 없다.** 인덱스 시그니처가 「모르는 키도 `number` 다」라고 약속했으므로 컴파일러는 **있다고 믿는다.**\
  실행하면 `undefined` 이고, `undefined.toFixed` 는 터진다 — **이 구멍을 메우는 것이 4번의 플래그**다.
- ★ 즉 인덱스 시그니처는 **확장성을 얻는 대신 「없는 키」 검사를 포기**하는 거래다.

### 4. ★★★ 기본값 **0건** → 두 플래그를 켜면 **2건**

**출력**

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

```text
===== tsc --pretty false --noEmit ex.07e.ts (tsc exit=0) =====
```

```text
===== tsconfig.07.json =====
{
    "compilerOptions": {
        "exactOptionalPropertyTypes": true,
        "noUncheckedIndexedAccess": true,
        "noEmit": true
    },
    "files": ["ex.07e.ts"]
}
===== tsc --pretty false -p tsconfig.07.json (tsc exit=1) =====
ex.07e.ts(11,7): error TS2375: Type '{ host: string; port: undefined; }' is not assignable to type 'Conf' with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the types of the target's properties.
  Types of property 'port' are incompatible.
    Type 'undefined' is not assignable to type 'number'.
ex.07e.ts(13,17): error TS18048: 'bag.missing' is possibly 'undefined'.
```

**왜 그런가**

| 판 | 종료 코드 | 진단 |
|---|---|---|
| 옵션 없음(`strict` 만 기본 `true`) | **0** | **없음** |
| `exactOptionalPropertyTypes` + `noUncheckedIndexedAccess` | **1** | `TS2375`(11행) · `TS18048`(13행) |

- ★★★ **같은 파일이 0건과 2건 사이를 오간다.** 그래서 이 주제는 **설정을 안 밝히면 본문 전체가 검증 불가**다.
- `TS2375` — `exactOptionalPropertyTypes` 가 켜지면 `port?: number` 는 「**키를 빼거나 `number` 를 넣어라**」가 되고,\
  명시적 `undefined` 는 거절된다. 허용하려면 `port?: number | undefined` 로 적어야 한다(진단이 그렇게 권한다).
- `TS18048` — `noUncheckedIndexedAccess` 가 켜지면 `bag.missing` 이 `number | undefined` 가 된다. 3번에서 통과한 그 줄이다.

| 플래그 | `strict` 포함? | 기본값 | 도입 |
|---|---|---|---|
| `strictNullChecks` | **포함** | `true`(7.0) | 2.0 |
| `exactOptionalPropertyTypes` | 아니다 | `false` | 4.4 |
| `noUncheckedIndexedAccess` | 아니다 | `false` | 4.1 |

### 5. ★★ 수정자는 **적은 그대로** 남고, `pick` 의 `port` 는 **`number | undefined`** 가 된다

**출력**

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

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.07d.ts (tsc exit=0) =====
===== 방출된 ex.07d.d.ts =====
export interface Conf {
    readonly host: string;
    port?: number;
    readonly tags?: readonly string[];
    [extra: string]: unknown;
}
export declare const conf: Conf;
export declare const frozen: {
    readonly a: 1;
    readonly b: readonly [2, 3];
};
export declare function pick(c: Conf): {
    host: string;
    port: number | undefined;
};
```

**왜 그런가**

| 선언 | `.d.ts` |
|---|---|
| `readonly host: string` | 그대로 |
| `port?: number` | 그대로 |
| `readonly tags?: readonly string[]` | ★ 그대로 — 셋이 겹쳐도 보존된다 |
| `[extra: string]: unknown` | 그대로 |
| `frozen = { a: 1, b: [2, 3] } as const` | `readonly a: 1` · `readonly b: readonly [2, 3]` |
| `pick(c)` 의 반환 | ★★★ `{ host: string; port: number \| undefined }` |

- ★★★ `pick` 의 반환에서 **`?` 가 사라지고 `| undefined` 만 남았다.**\
  `{ host: c.host, port: c.port }` 는 **키가 반드시 있는 새 리터럴**이고, 값이 `undefined` 일 수 있을 뿐이다.
- ★★ 즉 `?` 는 「**키의 유무**」라는 정보이고, 읽어서 새 객체를 만들면 그 정보가 **안 따라온다.**\
  4번의 `exactOptionalPropertyTypes` 가 갈라 주는 것이 정확히 이 차이다.
- ★ `as const` 는 `readonly` 를 **재귀적으로** 붙이고 배열을 튜플로 만든다([**03번 주제**](../03-basic-type-annotations/)).

### 6. ★★★ `readonly host` 가 **`바뀜`** 으로 찍히고, `"port" in` 이 **`false` 와 `true`** 로 갈린다

**출력**

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

```text
===== tsc --pretty false ex.07f.ts (tsc exit=0) =====
===== 방출된 ex.07f.js =====
"use strict";
const c = { host: "처음", port: 80 };
const loose = c;
loose.host = "바뀜";
const omitted = { host: "b" };
const explicitUndefined = { host: "b", port: undefined };
console.log("readonly host :", c.host);
console.log("없는 키 읽기  :", c.nothing);
console.log("키 목록       :", Object.keys(c));
console.log("빠뜨린 쪽     :", omitted.port, JSON.stringify(omitted), "port" in omitted);
console.log("undefined 쪽  :", explicitUndefined.port, JSON.stringify(explicitUndefined), "port" in explicitUndefined);
```

```text
===== node ex.07f.js (node exit=0) =====
readonly host : 바뀜
없는 키 읽기  : undefined
키 목록       : [ 'host', 'port' ]
빠뜨린 쪽     : undefined {"host":"b"} false
undefined 쪽  : undefined {"host":"b"} true
```

**왜 그런가**

| 확인 | 값 |
|---|---|
| `c.host`(`readonly`) | ★★★ **`바뀜`** |
| `c.nothing`(인덱스 시그니처) | `undefined` |
| `Object.keys(c)` | `[ 'host', 'port' ]` |
| `omitted.port` · `JSON` · `"port" in` | `undefined` · `{"host":"b"}` · **`false`** |
| `explicitUndefined.port` · `JSON` · `"port" in` | `undefined` · `{"host":"b"}` · **`true`** |

- ★★★ 방출된 파일에 수정자가 **한 글자도 없다.** `const loose = c;` 는 `as` 가 사라진 자리이고, 그 다음 줄에서 값이 **그대로 바뀌었다**.
- ★★ 인덱스 시그니처도 런타임 보호가 아니다 — `c.nothing` 은 그냥 `undefined` 다.
- ★★★ 마지막 두 줄이 `exactOptionalPropertyTypes` 의 존재 이유다. **`JSON.stringify` 로는 둘이 똑같고 `in` 으로만 갈린다.**\
  「키가 없다」와 「키가 `undefined`」는 **JS 에서 다른 객체**인데, 기본 설정의 타입은 그 차이를 못 적는다.
- ★ 그래서 `in` 이나 `Object.keys` 로 동작이 갈리는 API 를 다룬다면 그 플래그를 켜는 것이 값을 한다.

### 7. ★★ 「없을 수도 있다」가 **값의 타입으로 내려오기** 때문이다

**왜 그런가**

- `?` 는 두 가지를 한 번에 말한다 — ① **키가 없어도 된다** ② 그래서 **읽으면 `undefined` 일 수 있다**.
- `strictNullChecks` 아래에서 `undefined` 는 **`string` 에 안 들어가는 별개의 타입**이다([**04번 주제**](../04-any-unknown-never-void/)).\
  그러니 `string | undefined` 를 `string` 처럼 쓰려면 **한 갈래를 잘라 내야** 한다.
- ★★ 1번의 탐침이 그것을 글자로 보여 준다 — 「Type 'string \| undefined' is not assignable to type 'null'.」
- ★ 그래서 「표시일 뿐」이 아니다. **타입이 바뀌고, 그 결과로 검사가 생긴다.**
- ★★ 뒤집어서 **직접 던져 봤다** — `strictNullChecks` 를 끄면 1번의 진단이 **3건에서 1건**으로 줄고, 탐침이 말하는 타입이 그냥 「`string`」이 된다.

```text
===== tsc --pretty false --noEmit --strictNullChecks false ex.07a.ts (tsc exit=1) =====
ex.07a.ts(13,7): error TS2322: Type 'string' is not assignable to type 'null'.
```

- ★★★ 같은 판에서 선언 방출도 달라진다 — `pick` 의 반환이 **`port: number`** 다. `| undefined` 가 사라졌다.

```text
===== tsc --pretty false --declaration --emitDeclarationOnly --strictNullChecks false ex.07d.ts (tsc exit=0) =====
===== 방출된 ex.07d.d.ts =====
export interface Conf {
    readonly host: string;
    port?: number;
    readonly tags?: readonly string[];
    [extra: string]: unknown;
}
export declare const conf: Conf;
export declare const frozen: {
    readonly a: 1;
    readonly b: readonly [2, 3];
};
export declare function pick(c: Conf): {
    host: string;
    port: number;
};
```

- ★ 즉 `?` 가 타입을 바꾸는 것은 **`strictNullChecks` 가 켜져 있을 때의 이야기**다. 끄면 거의 표시로만 남는다.

### 8. ★★★ 우회 둘 — **넓은 타입으로 받기**와 **런타임에 그냥 쓰기**

**왜 그런가**

| 우회 | 근거 |
|---|---|
| **넓은 타입으로 받는다** | 2번의 `const roToRw: RW = ro; roToRw.a = 2;` — 두 줄 다 통과한다 |
| **런타임에서는 그냥 바뀐다** | 6번의 실행 출력 — `readonly host` 가 `바뀜` 이다 |

- ★★ 그래도 쓸 값이 있는 이유 —

| 이유 | 설명 |
|---|---|
| **의도 표시** | 「이 칸은 내가 안 바꾼다」가 코드에 남는다. 리뷰가 읽는다 |
| **실수 잡기** | 직접 대입은 `TS2540` 으로 확실히 잡힌다. **우회는 의도해야 일어난다** |
| **배열은 진짜 막는다** | `readonly T[]` 는 `TS4104`·`TS2339` 로 한 방향이 잠긴다 |

- ★ 진짜 불변이 필요하면 **`Object.freeze` 같은 런타임 수단**을 같이 쓴다 — 타입과 실행을 둘 다 잠근다.

### 9. ★★★ **「선언에 없는 키」 검사를 포기한다**

**왜 그런가**

- 3번의 7행이 그 증거다 — `bag.nothing.toFixed(2)` 가 **아무 말 없이 통과**했다. 실행하면 `undefined` 라 터진다.
- 인덱스 시그니처는 「모르는 키도 이 타입이다」라는 **약속**이라, 컴파일러는 그 약속을 믿고 있다고 친다.
- ★★ 덤으로 따라오는 대가가 하나 더 있다 — **선언된 프로퍼티가 인덱스 타입에 맞아야 한다**(`TS2411`). 넓히면 그만큼 검사가 약해진다.
- ★ 메우는 길 둘 —

| 길 | 무엇 |
|---|---|
| `noUncheckedIndexedAccess` | 인덱스 접근에 `\| undefined` 를 붙여 좁히기를 강제한다(4번) |
| 유니온 키 `Record` | `Record<"a" \| "b", number>` 로 적으면 없는 키 접근이 **`TS2339`** 로 잡힌다 |

### 10. ★★ **기존 코드에 진단이 쏟아지기 때문이다**

**왜 그런가**

- 4번에서 **같은 여섯 줄짜리 파일**이 0건에서 2건이 됐다. 인덱스 접근과 선택 프로퍼티는 **어느 코드베이스에나 널려 있다.**
- `strict` 는 「이걸 켜면 대부분의 프로젝트가 켤 만하다」는 묶음이다. 두 플래그는 그 기준에 못 미친다 —

| 플래그 | 왜 부담이 큰가 |
|---|---|
| `noUncheckedIndexedAccess` | 배열 인덱싱(`arr[i]`)까지 전부 `\| undefined` 가 된다 — 루프 안에서도 좁혀야 한다 |
| `exactOptionalPropertyTypes` | `{ ...opts, port: maybe }` 같은 **스프레드 조립 관용구**가 전부 걸린다 |

- ★★ 그래서 읽는 법은 「**엄격도가 낮은 플래그**」가 아니라 「**마이그레이션 비용이 큰 플래그**」다.
- ★ 고르는 기준 — 6번처럼 **`in` 이나 `Object.keys` 로 동작이 갈리는 경계**가 있으면 `exactOptionalPropertyTypes` 가 값을 하고,\
  배열·맵을 많이 훑는 코드면 `noUncheckedIndexedAccess` 가 값을 한다.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `?` 는 `\| undefined` 를 더한다 · `readonly` 프로퍼티는 **대입문만** 막는다 · 인덱스 시그니처는 선언된 프로퍼티에 **조건을 건다** · 세 수정자는 **방출에 안 남는다** |
| **설정에 달린 것** | ★★ **이 주제의 본체다** — `strictNullChecks`(`strict` 에 딸려 기본 `true`) · `exactOptionalPropertyTypes`(기본 `false`) · `noUncheckedIndexedAccess`(기본 `false`). **두 판을 다 실었고 설정 전문도 같은 블록에 있다** |
| **이 판(7.0.2)의 관찰** | 진단 문구와 코드 배정(`TS18048`·`TS2540`·`TS4104`·`TS2411`·`TS2413`·`TS2375`) · `.d.ts` 가 수정자를 **적은 그대로** 싣는 것 · `pick` 의 반환이 `port: number \| undefined` 로 적히는 것 |

- ★ 이 주제에서 **「설정에 달린 것」 칸이 가장 두껍다.** [**06번 주제**](../06-excess-property-checks/)가 정반대였다 — 거기는 `strict` 를 꺼도 결과가 같았다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 선택 프로퍼티 | `--noEmit ex.07a.ts` | exit 1 · **3건**(8·13·14행) · 탐침이 `string \| undefined` |
| `readonly` | `--noEmit ex.07b.ts` | exit 1 · `TS2540`·`TS4104`·`TS2339` **3건** · 양방향 대입 2줄 통과 |
| 인덱스 시그니처 | `--noEmit ex.07c.ts` | exit 1 · `TS2411`·`TS2413` **2건** · 없는 키 읽기 통과 |
| 같은 파일 기본값 | `--noEmit ex.07e.ts` | exit **0** · 진단 **0건** |
| 같은 파일 설정 | `-p tsconfig.07.json` | exit 1 · `TS2375`·`TS18048` **2건** |
| `strictNullChecks` 끔 | `--noEmit --strictNullChecks false ex.07a.ts` | exit 1 · **1건**으로 줄고 탐침이 `string` |
| 〃 선언 방출 | `--declaration --emitDeclarationOnly --strictNullChecks false ex.07d.ts` | exit 0 · `pick` 반환이 `port: number` |
| 선언 방출 | `--declaration --emitDeclarationOnly ex.07d.ts` | exit 0 · 수정자 보존 · `pick` 반환이 `port: number \| undefined` |
| 방출·실행 | `tsc ex.07f.ts` + `node ex.07f.js` | tsc exit 0 · node exit 0 · `readonly` 가 `바뀜` · `"port" in` 이 `false`/`true` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- 두 플래그의 **기본값이 `false`** 라는 것 — `tsc --help --all` 에서 확인했고 실행으로 재확인했다. 판이 오르면 `strict` 묶음이 바뀔 수 있다.
- `.d.ts` 가 `readonly tags?: readonly string[]` 를 적은 그대로 싣는 것 — 선언 방출기의 구현이다.
- `pick` 의 반환이 `port: number | undefined` 로 적히는 것 — 「선택성이 안 따라간다」만 성질로 읽는다.
- 진단 문구 전문 — 코드가 더 오래 간다.

**안 돌려 본 것**

- `Object.freeze` 를 같이 쓴 판 — 8번 표의 마지막 줄. **형태만 적고 돌리지 않았다.**
