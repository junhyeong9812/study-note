# ts/syntax/07 — 객체 타입 세부 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html) ·
> [Handbook — Object Types: Index Signatures](https://www.typescriptlang.org/docs/handbook/2/objects.html#index-signatures) ·
> [TSConfig — `exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/#exactOptionalPropertyTypes) ·
> [TSConfig — `noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문·방출 전문은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 주제는 **설정이 답을 바꾸는 주제**다.
> 기본값에서 `strict` 는 **켜져 있고**(7.0 기본 `true`), 그 안에 `strictNullChecks` 가 들어 있다.
> ★★ 반면 `exactOptionalPropertyTypes` 와 `noUncheckedIndexedAccess` 는 **`strict` 에 안 들어 있어 기본 `false`** 다
> (`tsc --help --all` 의 `default: false` 를 확인했고, **켠 판을 따로 던져 두 결과를 나란히 실었다**).
> **버전** — `readonly` 프로퍼티는 TS 2.0, `exactOptionalPropertyTypes` 는 4.4, `noUncheckedIndexedAccess` 는 4.1 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**`.d.ts` 전문**·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | `.d.ts` 안의 **프로퍼티 순서** | 선언 순서를 따른다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ **설정이 답을 바꾸는 주제라 옵션이 매 블록의 배너에 있다.** 설정 파일로 던진 판은 **그 설정 전문도 같은 블록**에 실었다.

## 한눈에 — 쉽게 말하면

**세 수정자는 서로 다른 층에서 일한다.**

| 비유 | 실체 |
|---|---|
| 「이 칸은 비워도 됩니다」 | **선택 프로퍼티 `?`** — 값이 `undefined` 일 수 있다는 뜻이 **타입에 들어간다** |
| 「이 칸은 접수 후 수정 불가」 — **접수 창구에서만** 막는다 | **`readonly`** — **대입문만** 막는다. 넘겨받은 쪽은 그냥 쓴다 |
| 「나머지 칸은 자유 기재, 단 숫자만」 | **인덱스 시그니처** — 모르는 키의 타입을 **미리** 정한다 |
| ★ 자유 기재 칸을 정하면 **정해진 칸도 그 규칙을 따라야 한다** | 선언된 프로퍼티가 인덱스 타입에 **맞아야 한다**(`TS2411`) |
| 창구 규칙은 접수증에 안 적힌다 | **셋 다 방출에 한 글자도 안 남는다** |

- ★★★ 한 줄로 — 「**`?` 는 타입을 바꾸고, `readonly` 는 대입문만 막고, 인덱스 시그니처는 나머지 키의 타입을 미리 정한다.**」
- ★★ 그리고 **셋 다 런타임에 아무 힘이 없다** — `readonly` 객체의 값이 실제로 바뀌는 것을 실행으로 보인다.

```text
  interface Conf {
      readonly host: string;      ← 대입문만 막는다 (할당 가능성은 안 건드린다)
      port?: number;              ← 타입이 number | undefined 가 된다
      [k: string]: unknown;       ← 그 밖의 키를 전부 받는다
  }
                    │
                    ▼  tsc
  const c = { host: "h" };        ← 세 수정자가 한 글자도 안 남는다
```

```text
  세 수정자가 각각 막는 것과 안 막는 것

  ?           막는다: 값 없이 쓰는 것 (TS18048)
              안 막는다: 키를 아예 빼는 것 — 그게 목적이다

  readonly    막는다: c.host = "x" (TS2540)
              ★ 안 막는다: const rw: RW = ro  — **할당 가능성에 영향이 없다**
              ★ 안 막는다: 런타임 변경 — 방출에 안 남는다

  [k: string] 막는다: 선언된 프로퍼티가 인덱스 타입에 안 맞는 것 (TS2411)
              ★ 안 막는다: 없는 키를 읽는 것 — 기본값에서는 조용히 통과한다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`?` 를 붙이면 타입이 무엇이 되나** — 그리고 언제 다시 쓸 수 있게 되나.
2. **`readonly` 는 무엇을 막나** — 막지 **않는** 것이 무엇인지까지 말할 수 있나.
3. **인덱스 시그니처를 쓰면 무엇이 따라오나** — 선언된 프로퍼티에 거는 조건과, **없는 키를 읽을 때**의 기본값.

★ [**05번 주제**](../05-structural-typing/)가 「모양으로 정해진다」를 세웠다면, 여기는 **그 모양을 적는 세 수정자**를 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **같은 파일을 옵션만 바꿔 두 번** | `exactOptionalPropertyTypes`·`noUncheckedIndexedAccess` 로 **갈리는 칸** | ★ 이 주제의 본체 |
| ★★ **`.d.ts` 덤프** | 세 수정자가 **선언 방출에 어떻게 남는지** | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| ★★ **`null` 탐침** | `?` 가 만든 타입을 **컴파일러가 글자로** 말하게 하기 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| ★★★ **방출된 `.js` + `node`** | `readonly` 가 **런타임을 못 막는 것** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

★ 첫째 창이 이 주제의 본체다. **설정을 안 밝히면 본문 전체가 검증 불가**가 된다.

비용 — 컴파일 두 번(기본값 한 번, 설정 한 번).

### (1) ★★★ `?` 는 타입을 바꾼다

**언제 쓰나** — 「`?` 를 붙였더니 쓸 때마다 에러가 난다」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 8행·13행·14행. **9·10·11행은 통과했다.**
- 8행 `u.nickname.length` 가 `TS18048` — 「'u.nickname' is possibly 'undefined'」.
- ★★ 13행의 `null` 탐침이 답을 적어 준다 — `nickname` 의 타입은 「**`string | undefined`**」다. `?` 는 **`| undefined` 를 타입에 더한 것**이다.
- 14행도 같은 근거다 — `string` 자리에 못 들어간다.
- ★ 풀리는 길이 셋이다 — `=== undefined` 비교(9행) · 옵셔널 체이닝 `?.`(10행) · `??` 기본값(11행). **셋 다 진단 목록에 없다.**
- ★ 17행 `const partial: User = { id: "a" }` 도 통과했다 — **키를 아예 빼는 것**이 `?` 의 목적이다.

```text
  nickname?: string
        │
        ▼
  타입:  string | undefined
        │
        ├── 그냥 쓰면              TS18048
        ├── === undefined 로 갈라   통과   (좁히기)
        ├── ?. 로 접근             통과   (결과가 number | undefined)
        └── ?? 로 기본값           통과
```

> **선택 프로퍼티(optional property)** — 이름 뒤에 `?` 를 붙여 **없어도 되는 칸**으로 만드는 것.\
> 예: `nickname?: string` 의 타입은 `string | undefined` 다 — `strictNullChecks` 가 켜져 있을 때.

★★ 「켜져 있을 때」라는 단서를 던져서 확인했다. 같은 파일을 `--strictNullChecks false` 로 다시 준다.

```text
===== tsc --pretty false --noEmit --strictNullChecks false ex.07a.ts (tsc exit=1) =====
ex.07a.ts(13,7): error TS2322: Type 'string' is not assignable to type 'null'.
```

- ★★★ 진단이 **3건에서 1건**으로 줄고, 탐침이 말하는 타입이 그냥 「`string`」이다 — **`| undefined` 가 아예 안 붙는다.**
- ★ 즉 이 절의 모든 이야기는 **`strictNullChecks` 가 켜진 전제** 위에 선다. 7.0 에서는 `strict` 에 딸려 기본으로 켜져 있다.

비용 — 쓰는 자리마다 **좁히기가 필요**하다. 그 비용이 싫어 기본값을 넣는 설계가 흔하다.

### (2) ★★★ `readonly` 가 막는 것과 안 막는 것

**언제 쓰나** — 「`readonly` 를 붙였는데 왜 값이 바뀌지」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 11행·19행·21행.
- 11행 `ro.a = 1` 이 `TS2540` — 「Cannot assign to 'a' because it is a read-only property.」 **대입문은 막는다.**
- ★★★ **13·14행이 진단 목록에 없다.** `const roToRw: RW = ro` 도, `const rwToRo: RO = rw` 도 **양방향으로 통과**한다.\
  즉 **`readonly` 프로퍼티 수정자는 할당 가능성에 영향이 없다.**
- ★★★ 15행 `roToRw.a = 2` 도 통과했다 — **`readonly` 를 벗겨 낸 별칭으로 그냥 쓸 수 있다.**
- ★★ 그런데 **배열은 다르다.** 19행 `const arrToMutable: number[] = roArr` 가 `TS4104` 로 막힌다.
- ★ 20행 `const arrToReadonly: readonly number[] = rwArr` 는 통과했다 — **한 방향만** 된다.
- ★ 21행 `roArr.push(1)` 은 `TS2339` 다 — `readonly` 배열 타입에는 **`push` 자체가 없다**.

```text
  프로퍼티의 readonly                      배열의 readonly
  ┌──────────────────────────┐            ┌──────────────────────────┐
  │ ro.a = 1        TS2540   │            │ readonly number[]        │
  │                          │            │   -> number[]   TS4104   │
  │ RW = ro         통과 ★   │            │ number[]                 │
  │ RO = rw         통과 ★   │            │   -> readonly number[] 통과│
  │ (벗겨서 쓰면 그만이다)   │            │ roArr.push      TS2339   │
  └──────────────────────────┘            └──────────────────────────┘
        빠져나가는 문이 있다                     한 방향으로 잠긴다
```

> **`readonly` 프로퍼티** — 그 프로퍼티에 **대입하는 문**을 금지하는 수정자. 할당 가능성 판정에는 안 들어간다.\
> 예: `readonly a: number` 인 값을 `{ a: number }` 자리에 넣으면 통과하고, 거기서 대입하면 된다.

비용 — **의도 표시로는 좋고 보증으로는 약하다.** 진짜로 막으려면 `Object.freeze` 같은 런타임 수단이 필요하다.

### (3) ★★★ 인덱스 시그니처가 선언된 프로퍼티에 거는 조건

**언제 쓰나** — 「인덱스 시그니처를 넣었더니 멀쩡한 프로퍼티가 에러 난다」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**이다 — 11행과 26행.
- ★★ 11행 `interface Bad { [k: string]: number; name: string }` 이 `TS2411` — 「Property 'name' of type 'string' is not assignable to 'string' index type 'number'.」\
  **인덱스 시그니처를 선언하면 그 타입이 「이 객체의 모든 값이 만족해야 할 조건」이 된다.**
- ★ 그래서 `Widened` 는 통과한다 — 인덱스 타입을 `number | string` 으로 **넓혀** 두 프로퍼티를 다 담았다.
- ★★ 26행 `interface Clash { [i: number]: number; [k: string]: string }` 이 `TS2413` — **숫자 인덱스 타입이 문자열 인덱스 타입에 들어가야 한다.**\
  JS 에서 `obj[0]` 은 `obj["0"]` 과 같은 자리라 그렇다. 둘을 같은 타입으로 맞춘 `TwoKinds` 는 통과했다.
- ★★★ 그리고 **7행이 진단 목록에 없다.** `bag.nothing.toFixed(2)` — **선언에 없는 키를 읽었는데 조용히 통과**한다.\
  인덱스 시그니처는 「모르는 키도 `number` 다」라고 약속했으므로 **컴파일러는 있다고 믿는다.** 실행하면 `undefined` 다.

> **인덱스 시그니처(index signature)** — 「이 이름 꼴의 키는 전부 이 타입」이라고 미리 적어 두는 선언.\
> 예: `[k: string]: number`. 선언된 프로퍼티도 이 타입을 만족해야 한다.

비용 — **없는 키를 읽어도 안 걸린다.** 그 구멍을 메우는 것이 다음 절의 플래그다.

### (4) ★★★ 같은 파일, 설정 두 판

**언제 쓰나** — 「우리 팀은 왜 이게 에러가 안 나지」에서 막힐 때. **이 절이 이 주제의 본체다.**

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

기본값으로 던지면 **진단이 0건**이다.

```text
===== tsc --pretty false --noEmit ex.07e.ts (tsc exit=0) =====
```

같은 파일을 설정 파일로 던진다. 파일은 한 글자도 안 바꿨다.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 기본값에서는 **종료 코드가 0**이고 진단이 하나도 없다. 두 줄 다 아무 말 없이 통과한다.
- 설정을 켜면 **두 건**이 난다.
- 11행 `{ host: "a", port: undefined }` 가 `TS2375` — **`exactOptionalPropertyTypes`** 가 켜지면\
  「`port?: number`」는 「**`port` 를 빼거나 `number` 를 넣어라**」가 되고, **명시적 `undefined` 는 다른 것**이 된다.
- 13행 `bag.missing.toFixed(2)` 가 `TS18048` — **`noUncheckedIndexedAccess`** 가 켜지면 인덱스 접근 결과에 `| undefined` 가 붙는다.
- ★★ 그래서 **설정을 안 밝힌 「객체 타입」 예제는 재현이 안 된다.** 같은 코드가 0건과 2건 사이를 오간다.

| 플래그 | `strict` 에 포함? | 기본값 | 무엇이 달라지나 |
|---|---|---|---|
| `strictNullChecks` | **포함** | `true`(7.0) | `?` 가 `\| undefined` 를 만든다 |
| `exactOptionalPropertyTypes` | **아니다** | `false` | 명시적 `undefined` 를 **키 없음과 구별**한다 |
| `noUncheckedIndexedAccess` | **아니다** | `false` | 인덱스 접근에 `\| undefined` 를 붙인다 |

> **`exactOptionalPropertyTypes`** — `?` 를 「**적힌 그대로**」 읽어, 「키가 없는 것」과 「키가 `undefined` 인 것」을 가른다(4.4).\
> 예: `{ port: undefined }` 가 `TS2375` 가 된다. 허용하려면 `port?: number | undefined` 로 적어야 한다.

> **`noUncheckedIndexedAccess`** — 인덱스 접근의 결과에 `| undefined` 를 붙이는 플래그(4.1).\
> 예: `bag.missing` 이 `number` 가 아니라 `number | undefined` 가 된다.

비용 — 둘 다 **기존 코드에 진단을 왕창 낸다.** 그래서 `strict` 에 안 들어 있다.

### (5) ★★ 선언 방출이 수정자를 어떻게 적나

**언제 쓰나** — 「내가 적은 수정자가 라이브러리 소비자에게 그대로 가나」를 확인할 때.

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

그림 해설 — 한 단계에 한 문장.

- `interface Conf` 가 **적은 그대로** 나왔다 — `readonly host` · `port?` · `readonly tags?: readonly string[]` · 인덱스 시그니처까지.
- ★ `as const` 로 만든 `frozen` 은 **`readonly a: 1` 과 `readonly b: readonly [2, 3]`** 이다 — 재귀적으로 `readonly` 가 붙고 배열이 튜플이 됐다([**03번 주제**](../03-basic-type-annotations/)).
- ★★★ `pick` 의 반환 타입이 재미있다 — `{ host: string; port: number | undefined }`.\
  **`port?` 가 아니라 `port: number | undefined`** 다. 읽어서 새 객체를 만들면 **선택성은 사라지고 유니온만 남는다.**
- ★ 즉 `?` 는 「값의 타입」이 아니라 「**키가 있을 수도 없을 수도 있다**」는 별도 정보이고, 새 리터럴을 만들면 그 정보가 안 따라온다.

★★ 같은 파일을 `--strictNullChecks false` 로 뽑으면 그 자리가 **`port: number`** 가 된다 — `| undefined` 가 사라진다.

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

비용 — `.d.ts` 한 번. 라이브러리를 낼 때는 **이 출력이 계약**이다.

### (6) ★★★ 셋 다 런타임에 아무 힘이 없다

**언제 쓰나** — 「`readonly` 를 붙였으니 안 바뀌겠지」를 의심할 때.

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

그림 해설 — 한 단계에 한 문장.

- 방출된 파일에 **수정자가 한 글자도 없다.** `const loose = c;` 는 `as` 가 사라진 자리다.
- ★★★ `readonly host` 가 **`바뀜`** 으로 찍힌다 — 타입을 넓혀 받은 별칭으로 대입했더니 **그대로 바뀌었다**.
- `c.nothing` 이 `undefined` 다 — 인덱스 시그니처가 「모르는 키도 `unknown`」이라 했지만 **실제로는 없는 키**다.
- ★★ 마지막 두 줄이 `exactOptionalPropertyTypes` 의 이유를 보여 준다 —\
  키를 뺀 쪽은 `JSON.stringify` 가 `{"host":"b"}` 이고 `"port" in` 이 **`false`**,\
  `port: undefined` 를 넣은 쪽은 `JSON` 은 같은데 `"port" in` 이 **`true`** 다.
- ★ 즉 **JS 에서 둘은 다른 객체**다. 기본 설정의 타입은 그 차이를 못 적고, 그 플래그가 적게 해 준다.

```text
  { host: "b" }                    { host: "b", port: undefined }
      키 목록: ['host']                키 목록: ['host','port']
      'port' in -> false               'port' in -> true
      JSON      -> {"host":"b"}        JSON      -> {"host":"b"}
           ↑ JSON 으로는 구별이 안 된다. in 연산자로만 갈린다.
```

비용 — 0. 방출에 한 글자도 안 남는다. **그래서 보호도 0이다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  interface Conf {
      readonly host: string;              대입문만 막는다
      port?: number;                      타입이 number | undefined 가 된다
      readonly tags?: readonly string[];  둘을 같이 쓸 수 있다
      [extra: string]: unknown;           나머지 키의 타입
  }

  interface TwoKinds { [i: number]: string; [k: string]: string }   통과
  interface Clash    { [i: number]: number; [k: string]: string }   ★ TS2413
  interface Bad      { [k: string]: number; name: string }          ★ TS2411
```

**규칙 불릿**

- ★★★ **`?` 는 타입에 `| undefined` 를 더한다**(`strictNullChecks` 아래에서). 쓰려면 좁혀야 한다 — `=== undefined` · `?.` · `??`.
- ★★★ **`readonly` 프로퍼티는 대입문만 막는다.** 할당 가능성에는 **양방향으로 영향이 없다** — 벗겨 낸 별칭으로 그냥 쓸 수 있다.
- ★★ **배열의 `readonly` 는 다르다** — `readonly T[]` 를 `T[]` 자리에 못 넣고(`TS4104`), `push` 자체가 없다(`TS2339`).
- ★★ **인덱스 시그니처는 선언된 프로퍼티에 조건을 건다**(`TS2411`). 숫자 인덱스는 문자열 인덱스에 맞아야 한다(`TS2413`).
- ★★ **없는 키를 읽는 것은 기본값에서 안 걸린다.** `noUncheckedIndexedAccess` 를 켜야 `| undefined` 가 붙는다.
- ★★★ **`exactOptionalPropertyTypes` 는 `strict` 에 없다**(기본 `false`). 켜야 「키 없음」과 「`undefined`」가 갈린다.
- ★ **선언 방출은 수정자를 그대로 싣는다.** 단 **읽어서 새 객체를 만들면 `?` 가 `| undefined` 로 바뀐다.**
- ★★ **셋 다 방출에 안 남는다.** `readonly` 는 런타임 변경을 못 막는다.

**금지 사례** — 이 주제에서 던져 받은 것 다섯이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 선택 프로퍼티를 그냥 쓰기        ->  TS18048  'u.nickname' is possibly 'undefined'.
2) readonly 프로퍼티에 대입         ->  TS2540   Cannot assign to 'a' because it is a read-only property.
3) readonly 배열을 mutable 자리에   ->  TS4104   The type 'readonly number[]' is 'readonly' and cannot be assigned …
4) 인덱스 타입에 안 맞는 프로퍼티   ->  TS2411   Property 'name' of type 'string' is not assignable to 'string' index type 'number'.
5) 숫자·문자열 인덱스가 어긋남      ->  TS2413   'number' index type 'number' is not assignable to 'string' index type 'string'.
```

## 어디서 틀리나

- ★★★ 「**`readonly` 를 붙였으니 안 바뀐다**」 — 바뀐다. 넓은 타입으로 받아 대입하면 그만이고, 실행 출력이 `바뀜` 이다.
- ★★★ 「**`readonly` 가 있는 쪽과 없는 쪽은 호환이 안 되겠지**」 — **양방향으로 통과**한다. 진단 목록에 그 두 줄이 없다.
- ★★ 「**인덱스 시그니처가 있으면 아무 키나 안전하게 읽는다**」 — 읽히기만 한다. 기본값에서는 **`undefined` 를 `number` 라고 믿는다.**
- ★★ 「**`{ port: undefined }` 와 `{}` 는 같은 것**」 — JS 에서 다르다. `"port" in` 이 `true` 와 `false` 로 갈린다.
- ★★ 「**`strict` 를 켰으니 객체 타입 검사는 최대치**」 — 아니다. `exactOptionalPropertyTypes`·`noUncheckedIndexedAccess` 는 **`strict` 밖**이다.
- ★ 「**인덱스 시그니처를 넣어도 기존 프로퍼티는 그대로겠지**」 — `TS2411` 이 난다. 인덱스 타입을 넓히거나 프로퍼티를 빼야 한다.
- ★ 「**`?` 는 그냥 「없어도 된다」는 표시**」 — 표시이자 **타입 변경**이다. `| undefined` 가 붙는다.
- ★ 「**`pick` 의 반환도 `port?` 로 나오겠지**」 — `port: number | undefined` 다. 선택성은 안 따라간다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `?` 는 `strictNullChecks` 아래에서 **`\| undefined` 를 더한다** | 핸드북 「Optional Properties」. `null` 탐침이 `string \| undefined` 를 적어 줬다 |
| **언어 보장** | `readonly` 프로퍼티는 **대입문만** 막는다 | 핸드북이 「할당 가능성에 영향이 없다」를 명시한다. 이 판에서 양방향 통과를 확인 |
| **언어 보장** | 인덱스 시그니처는 선언된 프로퍼티에 **조건을 건다** | `TS2411`·`TS2413` 의 문구가 그 규칙이다 |
| **언어 보장** | 세 수정자는 **방출에 안 남는다** | `ex.07f.js` 전문과 `node` 출력 |
| **설정에 달림** | 「키 없음」과 「`undefined`」의 구별 | `exactOptionalPropertyTypes`(기본 `false`). **두 판을 다 실었다** |
| **설정에 달림** | 없는 키를 읽을 때 `\| undefined` 가 붙는가 | `noUncheckedIndexedAccess`(기본 `false`). **두 판을 다 실었다** |
| **설정에 달림** | `?` 가 애초에 `\| undefined` 를 만드는가 | `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`) |
| **이 판(7.0.2)의 관찰** | 진단 문구와 코드 배정 | 문구는 판마다 바뀐다. 코드(`TS18048`·`TS2540`·`TS4104`·`TS2411`·`TS2413`)가 더 오래 간다 |
| **이 판의 관찰** | `.d.ts` 가 `readonly tags?: readonly string[]` 를 **적은 그대로** 싣는 것 | 선언 방출기의 구현이다. 「보존된다」만 성질로 읽는다 |

★ 「**여러 번 돌려 같았다」는 보장이 아니다.** 이 주제는 특히 **설정이 답을 바꾼다** — 블록의 배너와 설정 전문이 그래서 같은 자리에 있다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| `?` — 진짜로 없어도 되는 칸에 | `?` 를 「기본값이 있다」는 뜻으로 — 기본값은 **값 쪽**에서 준다 |
| `readonly` — **의도 표시**로. 팀이 읽는다 | `readonly` 를 불변 **보증**으로 — 벗겨 내면 그만이다 |
| `readonly T[]` — 여기는 실제로 막힌다 | 프로퍼티 `readonly` 만 믿고 공유 객체를 넘기는 것 |
| 인덱스 시그니처 — 키가 **정말로 열려 있을 때** | 키가 정해져 있는데 편하려고 넣는 것 — `Record` 나 유니온 키가 낫다 |
| `noUncheckedIndexedAccess` — 새 프로젝트에 | 기존 큰 코드베이스에 갑자기 켜는 것 — 진단이 쏟아진다 |
| `exactOptionalPropertyTypes` — API 경계가 `in` 으로 갈릴 때 | 내부 전용 타입에 — 비용 대비 이득이 작다 |

## 핵심 문장

1. **`?` 는 타입을 바꾼다** — `string | undefined`. 쓰려면 좁혀야 한다.
2. **`readonly` 프로퍼티는 대입문만 막는다** — 할당 가능성에 영향이 없고 런타임도 못 막는다.
3. **배열의 `readonly` 는 한 방향으로 잠긴다** — `TS4104` 와 `TS2339` 가 그 경계다.
4. **인덱스 시그니처는 선언된 프로퍼티에 조건을 건다** — `TS2411`·`TS2413`.
5. **없는 키를 읽는 것은 기본값에서 안 걸린다** — `noUncheckedIndexedAccess` 가 그 구멍을 메운다.
6. **`exactOptionalPropertyTypes` 는 `strict` 밖이다** — 같은 파일이 0건과 2건 사이를 오간다.

## 관련 자료

- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — 할당 가능성의 **일반 규칙**은 그쪽. 여기서는 **수정자가 그 규칙에 어떻게 끼어드는지**만.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — 인덱스 시그니처가 **그 검사를 빠져나가는 길**인 것은 그쪽.
- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — 객체 타입 **표기의 기본형**과 `as const` 는 그쪽.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — `undefined` 가 타입 격자에서 어디 있는지는 그쪽.
- [**08번 주제** — `interface` 대 `type`](../08-interface-vs-type/) — **어느 문법으로 적을까**는 그쪽. 여기서는 수정자의 의미만.
- [목록의 **41번 주제**](../41-index-and-optional-property-strict-flags/)(인덱스·선택 프로퍼티 엄격 플래그) — 두 플래그의 **도입 순서·마이그레이션 비용**은 그쪽. 여기서는 **결과가 갈리는 두 판**까지.
- [목록의 **40번 주제**](../40-strict-null-checks-ripple/)(`strictNullChecks` 의 파급) — `?` 가 `| undefined` 를 만드는 전제는 그쪽.
- [목록의 **28번 주제**](../28-utility-types/)(유틸리티 타입) — `Partial`·`Required`·`Readonly` 로 수정자를 **켜고 끄는** 법은 그쪽.

## 용어 풀이

> **선택 프로퍼티(optional property)** — 이름 뒤에 `?` 를 붙여 없어도 되는 칸으로 만드는 것.\
> 예: `port?: number` 의 타입은 `number | undefined` 다.

> **`readonly` 프로퍼티** — 그 프로퍼티에 **대입하는 문**을 금지하는 수정자. 할당 가능성 판정에는 안 들어간다.\
> 예: `readonly host: string` 인 값을 `{ host: string }` 자리에 넣으면 통과하고, 거기서 대입하면 된다.

> **인덱스 시그니처(index signature)** — 「이 꼴의 키는 전부 이 타입」이라고 미리 적어 두는 선언.\
> 예: `[k: string]: number`. 선언된 프로퍼티도 이 타입을 만족해야 한다.

> **`exactOptionalPropertyTypes`** — `?` 를 적힌 그대로 읽어 「키 없음」과 「`undefined`」를 가르는 플래그(4.4, 기본 `false`).\
> 예: `{ port: undefined }` 가 `TS2375` 가 된다.

> **`noUncheckedIndexedAccess`** — 인덱스 접근 결과에 `| undefined` 를 붙이는 플래그(4.1, 기본 `false`).\
> 예: `bag.missing` 이 `number | undefined` 가 된다.

> **옵셔널 체이닝(`?.`)** — 앞이 `null`·`undefined` 면 거기서 멈추고 `undefined` 를 내는 JS 연산자.\
> 예: `u.nickname?.length` 의 타입은 `number | undefined` 다.

> **널 병합(`??`)** — 앞이 `null`·`undefined` 일 때만 뒤를 쓰는 JS 연산자.\
> 예: `(u.nickname ?? "").length` 는 항상 `number` 다.

## 더 들어가면

- **`Readonly<T>` 와 `readonly` 의 차이** — 유틸리티 타입은 **한 겹만** 붙인다. 중첩 객체는 그대로 쓸 수 있다. [목록의 **28번 주제**](../28-utility-types/).
- **`Object.freeze` 와의 관계** — `readonly` 는 검사 시각, `freeze` 는 실행 시각이다. 둘을 같이 쓰면 타입과 런타임이 맞는다. 이 판에서 `readonly` 만으로는 값이 바뀐 것을 확인했다.
- **인덱스 시그니처 대신 `Record`** — `Record<string, number>` 는 매핑 타입으로 같은 것을 만든다. 차이는 **`interface` 안에서 다른 프로퍼티와 같이 쓸 수 있는가**뿐이다. [목록의 **26번 주제**](../26-mapped-types/).
- **키가 정해져 있으면 유니온 키를 쓴다** — `Record<"a" \| "b", number>` 처럼 쓰면 없는 키 접근이 `TS2339` 로 잡힌다. 인덱스 시그니처는 그 검사를 **포기하는 대신** 확장성을 얻는 것이다.
