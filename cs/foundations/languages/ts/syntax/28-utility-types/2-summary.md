# ts/syntax/28 — 유틸리티 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html) ·
> [TypeScript 3.5 릴리스 노트 — The `Omit` helper type](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-5.html) ·
> [TypeScript 4.5 릴리스 노트 — The `Awaited` Type](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-5.html) ·
> 그리고 ★★ **tsc 패키지가 싣고 다니는 `lib.es5.d.ts` 그 자체**(3절 — `grep` 으로 직접 읽었다).
> 위는 **규칙 확인용 링크**이고, 본문의 진단·출력은 **전부 이 판에서 직접 던져 받은 것**이다. 핸드북 표를 옮기지 않았다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 격자(직접 다시 만들기)다.**
> 유틸리티 열한 개를 **손으로 다시 만들어** 내장과 **탐침 글자가 같은지** 스크립트가 센다(2절). 「이것들이 무엇으로 만들어졌나」는 그 격자가 답한다.
> 값을 읽는 창은 2창(`null` 탐침 + [**26번 주제**](../26-mapped-types/)의 `Show` 조수)이고, **정의를 읽는 창**(`lib.es5.d.ts` 를 `grep`)이 셋째다.
> ★★★ **26 → 28 은 한 사슬이고 여기가 급소다.** 유틸리티 타입은 **26 의 매핑과 24 의 조건부와 25 의 `infer`** 로 만들어져 있다.
> 그리고 급소 — **`Omit` 이 유니온에서 무너지는 것** — 은 [**22번 주제**](../22-keyof-and-indexed-access-types/)의 「**유니온의 `keyof` 는 교집합**」이
> `Omit` 안에서 **먼저 계산되기 때문**이다(1절). [**24번 주제**](../24-conditional-types-and-distribution/)의 **분배**로 고친다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — `Partial`·`Readonly`·`Pick`·`Record` 는 **TS 2.1**, `Required` 는 **2.8**, `Exclude`·`Extract`·`ReturnType` 은 **2.8**,
> `Parameters` 는 **3.1**, `Omit` 은 **3.5**, `Awaited` 는 **4.5** 다. ★ **7.0.2 에서 도는지는 던져서 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 주제가 쓰는 탐침 — 두 조수

```text
  const probe: null = null as unknown as X;
                                         └─ 이 자리의 타입이 X 라면
  TS2322  「Type 'X' is not assignable to type 'null'.」   ← 여기서 X 를 읽는다
```

- ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★★★ **조수 하나 — `Show<T>`.** `Partial<User>` 를 물으면 `Partial<User>` 라고 **메아리**만 돌아온다.
  [**26번 주제**](../26-mapped-types/) 1절이 찾은 대로 **매핑 한 겹 + `& {}`** 를 씌워야 펼쳐진다.
  ★ `Show` 는 **동형 매핑**이라 **유니온을 멤버마다 따로** 펼친다 — 1·2절에서 유니온의 모양을 볼 수 있는 까닭이다.
- ★★★ **조수 둘 — `[ … ]`(튜플로 감싸기).** 결과가 `never` 면 `never` 는 `null` 에도 할당되어 **탐침이 침묵한다**
  ([**24번 주제**](../24-conditional-types-and-distribution/)·[**25번 주제**](../25-infer-and-recursive-conditional-types/)가 겪은 일이다).
  2절 격자는 조건부 쪽 유틸리티를 **`[X]` 로 감싸** 물었다 — `never` 가 **`[never]` 라는 글자로** 나온다.

> ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**\
> 24·25 는 침묵을 `IsNever` 로 바꿔 물었다. 이 주제는 **튜플 한 겹**으로 바꿨다 — `never` 인지뿐 아니라 **무엇인지도** 글자로 나온다.\
> ★ **바꾼 창이 못 보는 것** — 튜플로 감싸면 **분배가 꺼진다**. 그래서 감싸는 것은 **결과를 다 계산한 뒤의 바깥**이지, 유틸리티의 인자가 아니다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다 |
| **안 흔들린다** | ★★★ 2절 격자의 **「글자 같음/다름」·`Eq`** 와 마지막 줄의 수 | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 유니온 원소의 **표시 순서** | 8절 — 5회 md5 **가짓수 1**. **관찰이지 보장이 아니다** |
| **★ 판에 달렸다** | 3절 `lib.es5.d.ts` 의 **줄 번호** | tsc 판마다 파일이 다르다. **정의의 모양**을 읽어라 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** | 8절 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — `Omit<User, "id">`·`Partial<User>` 가 **적은 그대로** 방출된다 | [**26번 주제**](../26-mapped-types/) 0절의 블록 |
| **★ 부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** — 유틸리티 타입은 **전부 타입 층**이다 | `.js` 블록이 **하나도 없다** |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**유틸리티 타입은 「표준 서식 도장 세트」다. 도장마다 안쪽을 뜯어 보면 26·24·25 에서 만든 부품이 그대로 들어 있다.**

| 비유 | 실체 |
|---|---|
| **「전부 선택 항목으로」** 도장 | `Partial` = `{ [K in keyof T]?: T[K] }` — 26 의 매핑 한 줄 |
| **「전부 필수로」·「전부 수정 금지로」** 도장 | `Required`(`-?`) · `Readonly`(`readonly`) |
| 항목 **골라 남기기 / 골라 지우기** | `Pick` · `Omit` |
| **이름 목록 × 같은 내용**으로 새 서류 | `Record<K, V>` |
| 목록에서 **빼기 / 남기기** | `Exclude` · `Extract` — 24 의 분배 조건부 |
| 서류의 **답란 / 입력란** 베끼기 | `ReturnType` · `Parameters` — 25 의 `infer` |
| 봉투를 **끝까지 뜯기** | `Awaited` — 25 의 재귀 조건부 |
| ★★★ **여러 종류가 섞인 서류 뭉치**에 「이 항목 지우기」 도장을 한 번 찍으면 | `Omit<Cat \| Dog, "id">` — **공통 항목만 남은 한 장**이 된다(1절) |
| ★★ 한 장씩 **따로** 찍으면 | `DistributiveOmit` — **종류가 살아 있다**(1절) |

- ★★★ 한 줄로 — 「**유틸리티 타입은 매핑·조건부·`infer` 로 만든 한두 줄짜리 타입이고, `Omit` 은 그 한 줄이 유니온을 먼저 합쳐 버린다.**」

```text
  도장 세트를 뜯어 보면 — 무엇으로 만들어졌나

   26 매핑            Partial · Required · Readonly · Pick · Record
   24 분배 조건부     Exclude · Extract
   25 infer           ReturnType · Parameters
   25 재귀 조건부     Awaited
   ─────────────────────────────────────────────────────────
   조합               Omit = Pick< T, Exclude<keyof T, K> >
                                      └──── ★ keyof T 를 여기서 먼저 계산한다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ `Omit` 은 유니온에서 왜 무너지고, 어떻게 고치나** — 판별 유니온에 걸어 **실출력**을 받고, 분배로 고친다(1절).
2. **★★ 열한 개가 정말 매핑·조건부·`infer` 로 만들어졌나** — 손으로 다시 만들어 **내장과 같은 글자인지** 격자로 센다(2절). 정의 파일을 직접 읽는다(3절).
3. **어디서 비대칭·특례가 나오나** — `Pick` 과 `Omit` 의 키 검사, `Awaited` 와 thenable, `Record` 와 인덱스 시그니처, `Readonly` 의 깊이(4\~6절).

★★ 1번이 README 의 과녁이고 이 주제의 급소다.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **격자 — 직접 다시 만들기** | 내장과 손으로 만든 것의 **탐침 글자**·`Eq` | 같음/다름 | **본체**(2절) |
| ★★ **2창 — `null` 탐침 + `Show`** | 계산된 객체 모양 | 계산된 것 | 1·4\~6절 |
| ★★ **2창 + `[ … ]`** | `never` 를 글자로 | **제5의 상태** | 2절 |
| ★★ **정의를 읽는 창 — `lib.es5.d.ts`** | 내장이 **실제로 무엇이라 적혀 있나** | 선언 | 3절 |
| ★ **진단이 나는 것 자체** | 막혀야 할 자리가 막혔나 | 에러 코드 | 1절 `TS2339` · 4절 `TS2344` · 6절 `TS2540` |
| ★ **Python 대비 — 런타임 속성** | `TypedDict` 가 들고 있는 키 목록 | 실행 결과 | 7절 |
| ★ **부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | `Omit<User, "id">` 가 **적은 그대로** | 26편 0절 |
| ★ **부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** | 전부 타입 층 | `.js` 블록 **없음** |

비용 — 컴파일 다섯 번 + 격자 스물두 번 + `grep` 한 번 + `python3` 한 번 + `--strict` 대조 열 번 + 순서 확인 열 번.

### (1) ★★★ `Omit` 을 유니온에 걸면 — 그리고 분배로 고치면

**언제 쓰나** — 판별 유니온(`kind` 로 갈리는 `Cat | Dog`)에서 **공통 필드 하나만 빼고** 싶을 때. 실무에서 가장 자주 밟는 자리다.

```ts
// ex.28a.ts
// Omit 을 유니온에 걸면
type Show<T> = { [K in keyof T]: T[K] } & {};
interface Cat {
    kind: "cat";
    id: number;
    meows: boolean;
}
interface Dog {
    kind: "dog";
    id: number;
    barks: boolean;
}
type Pet = Cat | Dog;

const k1: null = null as unknown as keyof Pet;
const o1: null = null as unknown as Show<Omit<Pet, "id">>;
const o2: null = null as unknown as Show<Omit<Cat, "id">>;

declare const pet: Omit<Pet, "id">;
if (pet.kind === "cat") {
    console.log(pet.meows);
}
const lit: Omit<Pet, "id"> = { kind: "cat", meows: true };
console.log(k1, o1, o2, lit);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.28a.ts (tsc exit=1) =====
ex.28a.ts(15,7): error TS2322: Type '"id" | "kind"' is not assignable to type 'null'.
  Type '"id"' is not assignable to type 'null'.
ex.28a.ts(16,7): error TS2322: Type '{ kind: "cat" | "dog"; }' is not assignable to type 'null'.
ex.28a.ts(17,7): error TS2322: Type '{ kind: "cat"; meows: boolean; }' is not assignable to type 'null'.
ex.28a.ts(21,21): error TS2339: Property 'meows' does not exist on type 'Omit<Pet, "id">'.
ex.28a.ts(23,45): error TS2353: Object literal may only specify known properties, and 'meows' does not exist in type 'Omit<Pet, "id">'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 15행 — `keyof Pet` 이 **`"id" | "kind"`** 다. `meows`·`barks` 가 없다 — **유니온의 `keyof` 는 공통 키**(교집합)다.
  [**22번 주제**](../22-keyof-and-indexed-access-types/) 1절 39행이 실측한 그 성질이다. 여기서는 **인용한다.**
- ★★★ **16행이 이 절의 과녁이다.** `Omit<Pet, "id">` 가 **`{ kind: "cat" | "dog"; }`** 이다.
  ① `meows`·`barks` 가 **사라졌고** ② `kind` 는 남았지만 **`"cat" | "dog"` 으로 합쳐졌고** ③ 결과가 **유니온이 아니라 객체 한 장**이다.
- ★ 17행 — `Cat` 하나에 걸면 멀쩡하다(`{ kind: "cat"; meows: boolean; }`). **유니온에 걸 때만** 무너진다.
- ★★★ 21행 — **`TS2339`** 「Property 'meows' does not exist on type 'Omit<Pet, "id">'.」
  `pet.kind === "cat"` 으로 좁혔는데도 `meows` 가 없다 — **좁힐 멤버가 이미 없기 때문**이다. 판별 필드는 남았는데 **판별 능력을 잃었다.**
- ★★ 23행 — 올바른 `Cat` 모양 `{ kind: "cat", meows: true }` 을 넣었더니 **`TS2353`**(초과 프로퍼티) — `meows` 가 **없는 속성**이 됐다.

```ts
// ex.28b.ts
// 멤버마다 따로 Omit 하면
type Show<T> = { [K in keyof T]: T[K] } & {};
interface Cat {
    kind: "cat";
    id: number;
    meows: boolean;
}
interface Dog {
    kind: "dog";
    id: number;
    barks: boolean;
}
type Pet = Cat | Dog;
type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never;

const d1: null = null as unknown as Show<DistributiveOmit<Pet, "id">>;

declare const pet: DistributiveOmit<Pet, "id">;
if (pet.kind === "cat") {
    console.log(pet.meows);
}
const lit1: DistributiveOmit<Pet, "id"> = { kind: "cat", meows: true };
const lit2: DistributiveOmit<Pet, "id"> = { kind: "cat", barks: true };
console.log(d1, lit1, lit2);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.28b.ts (tsc exit=1) =====
ex.28b.ts(16,7): error TS2322: Type '{ kind: "cat"; meows: boolean; } | { kind: "dog"; barks: boolean; }' is not assignable to type 'null'.
  Type '{ kind: "cat"; meows: boolean; }' is not assignable to type 'null'.
ex.28b.ts(23,58): error TS2353: Object literal may only specify known properties, and 'barks' does not exist in type 'Omit<Cat, "id">'.
```

- ★★★ 16행 — 멤버마다 따로 `Omit` 하니 **`{ kind: "cat"; meows: boolean; } | { kind: "dog"; barks: boolean; }`**. **유니온이 살았다.**
- ★★★ 20행에 **진단이 없다** — `pet.kind === "cat"` 뒤에서 `meows` 가 **읽힌다.** 판별이 돌아왔다.
- ★★ 22행도 **진단이 없고**, 23행 `{ kind: "cat", barks: true }` 는 **`TS2353`** — 이번에는 **막혀야 할 것이 막혔다**(`'Omit<Cat, "id">'` 라고 **멤버 이름으로** 말한다).
- ★★ `T extends unknown ? Omit<T, K> : never` 는 `T` 가 **네이키드**라 **분배된다** — [**24번 주제**](../24-conditional-types-and-distribution/)의 그 규칙이다. **조건 자체는 늘 참**이고, 목적은 **분배만** 켜는 것이다.

```text
  Omit 이 유니온을 무너뜨리는 순서

  Omit<Cat | Dog, "id">
    = Pick< Cat | Dog,  Exclude< keyof (Cat | Dog), "id" > >
                                 └─ ① 여기서 먼저 계산된다
                                    keyof (Cat | Dog) = "id" | "kind"     ← 교집합 (22편)
                        Exclude<"id" | "kind", "id"> = "kind"
    = Pick< Cat | Dog, "kind" >
    = { kind: (Cat | Dog)["kind"] } = { kind: "cat" | "dog" }            ← ② 한 장으로 합쳐졌다

  DistributiveOmit<Cat | Dog, "id">
    = Omit<Cat, "id"> | Omit<Dog, "id">                                   ← ★ 멤버마다 따로
    = { kind: "cat"; meows: boolean } | { kind: "dog"; barks: boolean }
```

> **분배형 `Omit`(DistributiveOmit)** — `T extends unknown ? Omit<T, K> : never` 로 **유니온의 멤버마다 따로** `Omit` 하는 흔한 관용구. 표준 라이브러리에는 **없다.**\
> 예: 이 문서 1절 16행.

비용 — 무너진 `Omit` 은 **에러를 한참 뒤에서** 낸다(21·23행). `Omit` 을 쓴 자리가 아니라 **그 값을 쓰는 자리**에서 터진다.

### (2) ★★★ 열한 개를 직접 다시 만들면 — 격자

**언제 쓰나** — 「유틸리티 타입은 매핑·조건부·`infer` 로 만들어져 있다」를 **믿지 말고 세어 보고** 싶을 때.

```bash
# ts26b-diy.sh
#!/usr/bin/env bash
# 유틸리티 열한 개를 직접 다시 만들어 내장과 탐침 글자를 견준다 -- 보통 인자 한 벌, 모서리 인자 한 벌
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
prelude='type Show<T> = { [K in keyof T]: T[K] } & {};
type Eq<A, B> = (<X>() => X extends A ? 1 : 2) extends (<X>() => X extends B ? 1 : 2) ? "eq" : "ne";
interface User { id: number; readonly name: string; email?: string; }
interface Opt { id?: number; readonly name?: string; }
interface Cat { kind: "cat"; id: number; meows: boolean; }
interface Dog { kind: "dog"; id: number; barks: boolean; }
interface Thenable { then(cb: (v: number) => void): void; }
declare function over(x: string): string;
declare function over(x: number): number;
type MyPartial<T> = { [K in keyof T]?: T[K] };
type MyRequired<T> = { [K in keyof T]-?: T[K] };
type MyReadonly<T> = { readonly [K in keyof T]: T[K] };
type MyPick<T, K extends keyof T> = { [P in K]: T[P] };
type MyExclude<T, U> = T extends U ? never : T;
type MyExtract<T, U> = T extends U ? T : never;
type MyOmit<T, K extends PropertyKey> = MyPick<T, MyExclude<keyof T, K>>;
type MyRecord<K extends PropertyKey, V> = { [P in K]: V };
type MyReturnType<F extends (...args: never[]) => unknown> = F extends (...args: never[]) => infer R ? R : never;
type MyParameters<F extends (...args: never[]) => unknown> = F extends (...args: infer P) => unknown ? P : never;
type MyAwaited<T> = T extends Promise<infer U> ? MyAwaited<U> : T;
type Fn = (x: number, y: string) => boolean;'
# 이름 ; 보통 인자 ; 모서리 인자 ; 감싸기 -- show 는 Show<…>, raw 는 [ … ] (never 도 글자로 나오게)
rows='Partial;User;Cat | Dog;show
Required;Opt;Partial<[1, 2]>;show
Readonly;User;string[];show
Pick;User, "id" | "name";Cat | Dog, "kind";show
Omit;User, "email";Cat | Dog, "id";show
Record;"a" | "b", number;string, number;show
Exclude;"a" | "b" | "c", "a";"a" | "b", string;raw
Extract;"a" | 1 | true, string | boolean;"a" | 1, never;raw
ReturnType;Fn;typeof over;raw
Parameters;Fn;typeof over;raw
Awaited;Promise<Promise<number>>;Thenable;raw'
probe() { # probe <이름> <인자> <감싸기> -> 내장 · 직접 · Eq 세 줄
  local name=$1 args=$2 wrap=$3 b m
  if [ "$wrap" = show ]; then b="Show<$name<$args>>"; m="Show<My$name<$args>>"; else b="[$name<$args>]"; m="[My$name<$args>]"; fi
  { echo "$prelude"; echo "const pb: null = null as unknown as $b;"; echo "const pm: null = null as unknown as $m;"
    echo "const pe: null = null as unknown as Eq<$name<$args>, My$name<$args>>;"; echo 'export {};'; } > "$D/p.ts"
  tsc --pretty false --noEmit -t es2022 --strict "$D/p.ts" 2>&1 \
    | sed -n "s/.*error TS2322: Type '\(.*\)' is not assignable to type 'null'\./\1/p"
}
for set in 보통 모서리; do
  same=0; eqn=0; total=0
  echo "== $set 인자"
  while IFS=';' read -r name args edge wrap; do
    if [ "$set" = 보통 ]; then a=$args; else a=$edge; fi
    ts=$(probe "$name" "$a" "$wrap")
    tb=$(printf '%s\n' "$ts" | sed -n 1p); tm=$(printf '%s\n' "$ts" | sed -n 2p); te=$(printf '%s\n' "$ts" | sed -n 3p)
    total=$((total+1))
    if [ "$tb" = "$tm" ]; then g="글자 같음"; same=$((same+1)); else g="글자 다름"; fi
    if [ "$te" = '"eq"' ]; then eqn=$((eqn+1)); fi
    printf '%-10s <%s> %s · Eq %s\n' "$name" "$a" "$g" "$te"
    printf '    내장  %s\n    직접  %s\n' "$tb" "$tm"
  done <<< "$rows"
  echo "$set 인자 -- 글자가 같은 칸 $same / $total · Eq 가 \"eq\" 인 칸 $eqn / $total"
  echo
done
```

```text
===== bash ts26b-diy.sh (sh exit=0) =====
== 보통 인자
Partial    <User> 글자 같음 · Eq "eq"
    내장  { id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }
    직접  { id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }
Required   <Opt> 글자 같음 · Eq "eq"
    내장  { id: number; readonly name: string; }
    직접  { id: number; readonly name: string; }
Readonly   <User> 글자 같음 · Eq "eq"
    내장  { readonly id: number; readonly name: string; readonly email?: string | undefined; }
    직접  { readonly id: number; readonly name: string; readonly email?: string | undefined; }
Pick       <User, "id" | "name"> 글자 같음 · Eq "eq"
    내장  { id: number; readonly name: string; }
    직접  { id: number; readonly name: string; }
Omit       <User, "email"> 글자 같음 · Eq "eq"
    내장  { id: number; readonly name: string; }
    직접  { id: number; readonly name: string; }
Record     <"a" | "b", number> 글자 같음 · Eq "eq"
    내장  { a: number; b: number; }
    직접  { a: number; b: number; }
Exclude    <"a" | "b" | "c", "a"> 글자 같음 · Eq "eq"
    내장  ["b" | "c"]
    직접  ["b" | "c"]
Extract    <"a" | 1 | true, string | boolean> 글자 같음 · Eq "eq"
    내장  ["a" | true]
    직접  ["a" | true]
ReturnType <Fn> 글자 같음 · Eq "eq"
    내장  [boolean]
    직접  [boolean]
Parameters <Fn> 글자 같음 · Eq "eq"
    내장  [[x: number, y: string]]
    직접  [[x: number, y: string]]
Awaited    <Promise<Promise<number>>> 글자 같음 · Eq "eq"
    내장  [number]
    직접  [number]
보통 인자 -- 글자가 같은 칸 11 / 11 · Eq 가 "eq" 인 칸 11 / 11

== 모서리 인자
Partial    <Cat | Dog> 글자 같음 · Eq "eq"
    내장  { kind?: "cat" | undefined; id?: number | undefined; meows?: boolean | undefined; } | { kind?: "dog" | undefined; id?: number | undefined; barks?: boolean | undefined; }
    직접  { kind?: "cat" | undefined; id?: number | undefined; meows?: boolean | undefined; } | { kind?: "dog" | undefined; id?: number | undefined; barks?: boolean | undefined; }
Required   <Partial<[1, 2]>> 글자 같음 · Eq "eq"
    내장  [1, 2]
    직접  [1, 2]
Readonly   <string[]> 글자 같음 · Eq "eq"
    내장  readonly string[]
    직접  readonly string[]
Pick       <Cat | Dog, "kind"> 글자 같음 · Eq "eq"
    내장  { kind: "cat" | "dog"; }
    직접  { kind: "cat" | "dog"; }
Omit       <Cat | Dog, "id"> 글자 같음 · Eq "eq"
    내장  { kind: "cat" | "dog"; }
    직접  { kind: "cat" | "dog"; }
Record     <string, number> 글자 같음 · Eq "eq"
    내장  { [x: string]: number; }
    직접  { [x: string]: number; }
Exclude    <"a" | "b", string> 글자 같음 · Eq "eq"
    내장  [never]
    직접  [never]
Extract    <"a" | 1, never> 글자 같음 · Eq "eq"
    내장  [never]
    직접  [never]
ReturnType <typeof over> 글자 같음 · Eq "eq"
    내장  [number]
    직접  [number]
Parameters <typeof over> 글자 같음 · Eq "eq"
    내장  [[x: number]]
    직접  [[x: number]]
Awaited    <Thenable> 글자 다름 · Eq "ne"
    내장  [number]
    직접  [Thenable]
모서리 인자 -- 글자가 같은 칸 10 / 11 · Eq 가 "eq" 인 칸 10 / 11

```

그림 해설 — 한 단계에 한 문장.

- 격자의 읽는 법 — 줄마다 **내장**과 **직접 만든 것**의 탐침 글자를 나란히 찍고, **`Eq`**(두 타입이 서로 같은가를 묻는 흔한 비교형)를 덧붙였다.
  객체 쪽은 `Show<…>` 로, 조건부 쪽은 `[ … ]` 로 감쌌다(머리의 두 조수).
- ★★★ **보통 인자 — 글자가 같은 칸 11 / 11 · `Eq` 11 / 11.** 열한 개가 **전부** 매핑 한 줄·조건부 한 줄·`infer` 한 줄로 **다시 만들어진다.**
- ★★ **모서리 인자에서 딱 한 칸이 갈렸다 — `Awaited<Thenable>`.** 내장은 **`[number]`**, 직접 만든 것은 **`[Thenable]`**.
  손으로 만든 `MyAwaited` 는 **`Promise` 만** 벗기는데, 내장은 **`then` 메서드가 있는 아무 객체**(thenable)나 벗긴다(5절).
- ★★★ 모서리의 **`Partial<Cat | Dog>`** 는 **유니온 그대로** 두 멤버를 따로 선택화했다 — `[K in keyof T]` 가 **동형이라 분배된다.**
- ★★★ 모서리의 **`Omit<Cat | Dog, "id">`** 는 **내장도 직접 만든 것도 똑같이 무너졌다**(`{ kind: "cat" | "dog"; }`).
  ★ 즉 1절의 붕괴는 **tsc 의 버그가 아니라 정의의 모양**에서 나온다 — 같은 모양으로 만들면 **같이 무너진다.**
- ★★ 모서리의 `Exclude<"a" | "b", string>`·`Extract<"a" | 1, never>` 는 **`[never]`** — 튜플 조수가 없었으면 **탐침이 침묵했을** 칸이다.
- ★★ 모서리의 `ReturnType<typeof over>`·`Parameters<typeof over>` 는 **`[number]`·`[[x: number]]`** — 오버로드가 둘인데 **마지막 것 하나**만 봤다(5절).
- ★ 마지막 두 줄 — **보통 11 / 11 · 모서리 10 / 11**.

```text
  직접 다시 만들기 — 스물두 칸에서 갈린 것은 하나

                     보통 인자            모서리 인자
  Partial            같음                 같음  ★ 유니온도 멤버마다 (동형 → 분배)
  Required·Readonly  같음                 같음
  Pick               같음                 같음
  Omit               같음                 같음  ★ 둘 다 무너진다 — 정의의 모양 탓
  Record             같음                 같음
  Exclude·Extract    같음                 같음  ([never] 로 물었다)
  ReturnType·Param.  같음                 같음  (오버로드는 마지막 하나)
  Awaited            같음                 ★ 다름 — thenable
```

비용 — 격자가 **「같다」를 보인 것은 이 인자들에서**다. 다른 인자에서 갈릴 수 있고, 그러면 **칸을 더해 다시 돌리면** 된다.

### (3) ★★ 정의를 직접 읽는다 — `lib.es5.d.ts`

**언제 쓰나** — 격자의 「같다」를 **정의 문장으로** 확인하고 싶을 때. `Omit` 이 왜 키를 검사하지 않는지(4절)도 여기서 나온다.

```text
===== (tsc 패키지의 lib 디렉토리에서) grep -n -A2 '^type \(Pick\|Omit\|Record\)<' lib.es5.d.ts && grep -n '^type \(Exclude\|Extract\|ReturnType\|Parameters\)<' lib.es5.d.ts && grep -n -A5 '^type Awaited<' lib.es5.d.ts (sh exit=0) =====
1604:type Pick<T, K extends keyof T> = {
1605-    [P in K]: T[P];
1606-};
--
1611:type Record<K extends keyof any, T> = {
1612-    [P in K]: T;
1613-};
--
1628:type Omit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>;
1629-
1630-/**
1618:type Exclude<T, U> = T extends U ? never : T;
1623:type Extract<T, U> = T extends U ? T : never;
1638:type Parameters<T extends (...args: any) => any> = T extends (...args: infer P) => any ? P : never;
1648:type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any;
1568:type Awaited<T> = T extends null | undefined ? T : // special case for `null | undefined` when not in `--strictNullChecks` mode
1569-    T extends object & { then(onfulfilled: infer F, ...args: infer _): any; } ? // `await` only unwraps object types with a callable `then`. Non-object types are not unwrapped
1570-        F extends ((value: infer V, ...args: infer _) => any) ? // if the argument to `then` is callable, extracts the first argument
1571-            Awaited<V> : // recursively unwrap the value
1572-        never : // the argument to `then` was not callable
1573-    T; // non-object or non-thenable
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `type Pick<T, K extends keyof T>` 와 **`type Omit<T, K extends keyof any>`** — **제약이 다르다.**
  `Pick` 의 `K` 는 「`T` 의 키」여야 하고, `Omit` 의 `K` 는 **아무 키(`string | number | symbol`)나** 된다. 4절의 비대칭이 이 한 줄이다.
- ★★★ `Omit` 의 몸통이 **`Pick<T, Exclude<keyof T, K>>`** — 1절의 그림 그대로다. **`keyof T` 가 유니온 전체에 대해 먼저 계산된다.**
- ★★ `Record<K extends keyof any, T> = { [P in K]: T; }` — **`keyof` 가 없는 매핑**이라 동형이 아니다(26편 3절).
- ★★ `Exclude`·`Extract` 는 **분배 조건부 한 줄**, `ReturnType`·`Parameters` 는 **`infer` 한 줄**이다.
- ★★★ **`Awaited` 는 여섯 줄**이다 — `T extends object & { then(onfulfilled: infer F, ...args: infer _): any; }` 가 핵심이다.
  **`Promise` 라는 이름을 한 번도 안 쓴다.** `then` 이 있으면 벗긴다 — 2절 격자의 유일한 「다름」이 이 줄에서 나온다.
- ★ 줄 번호(1568·1604 …)는 **이 판의 파일**의 것이다. **판에 달린 칸**이다.


```text
  정의 한 줄이 무엇을 정하나

  type Pick<T, K extends keyof T>     = { [P in K]: T[P] }            K 가 T 의 키여야 한다 → 오타를 잡는다
  type Omit<T, K extends keyof any>   = Pick<T, Exclude<keyof T, K>>  K 는 아무 키나 → 오타를 못 잡는다
                                                   └ keyof T 를 먼저 → 유니온이 합쳐진다
```
비용 — 정의는 **판마다 바뀔 수 있다.** 모양이 바뀌면 격자도 다시 돌려라.

### (4) ★★ `Pick` 은 키를 검사하고 `Omit` 은 안 한다

**언제 쓰나** — 키 이름에 **오타**가 났을 때 무엇이 잡아 주는지 알아 둘 때. 유명한 비대칭이라 던져서 확인한다.

```ts
// ex.28c.ts
// 없는 키를 넘기면 -- Pick 과 Omit
type Show<T> = { [K in keyof T]: T[K] } & {};
interface User {
    id: number;
    name: string;
}
type P = Pick<User, "nmae">;
type O = Omit<User, "nmae">;
const o: null = null as unknown as Show<O>;

type StrictOmit<T, K extends keyof T> = Omit<T, K>;
type S = StrictOmit<User, "nmae">;
console.log(o);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.28c.ts (tsc exit=1) =====
ex.28c.ts(7,21): error TS2344: Type '"nmae"' does not satisfy the constraint 'keyof User'.
ex.28c.ts(9,7): error TS2322: Type '{ id: number; name: string; }' is not assignable to type 'null'.
ex.28c.ts(12,27): error TS2344: Type '"nmae"' does not satisfy the constraint 'keyof User'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 7행 — `Pick<User, "nmae">` 는 **`TS2344`** 「Type '"nmae"' does not satisfy the constraint 'keyof User'.」 **오타를 잡았다.**
- ★★★ **8행에 진단이 없다.** `Omit<User, "nmae">` 는 **조용히 통과**하고, 9행 탐침이 말하듯 **`{ id: number; name: string; }`** — **아무것도 안 뺐다.**
- ★★ 12행 — `K extends keyof T` 로 **제약만 바꾼 `StrictOmit`** 은 **`TS2344`** 로 잡는다. 3절의 제약 한 줄이 **정확히 이 차이**다.

```text
  같은 오타, 다른 결과

  Pick<User, "nmae">          K extends keyof T      →  TS2344   잡는다
  Omit<User, "nmae">          K extends keyof any    →  (없음)   ★ 아무것도 안 빼고 통과
  StrictOmit<User, "nmae">    K extends keyof T      →  TS2344   제약만 바꾸면 잡는다
```

비용 — `Omit` 의 오타는 **「빼려던 필드가 그대로 남는」** 모양으로 드러난다. 컴파일은 조용하다.

### (5) ★★ `Awaited` 는 thenable 을 벗기고, `ReturnType` 은 마지막 오버로드만 본다

**언제 쓰나** — `Promise` 가 아닌 비동기 객체를 다루거나, **오버로드된 함수**의 반환 타입을 뽑을 때.

```ts
// ex.28d.ts
// Awaited 와 thenable · 오버로드의 ReturnType · Parameters
type SimpleAwaited<T> = T extends Promise<infer U> ? SimpleAwaited<U> : T;
interface Thenable {
    then(cb: (v: number) => void): void;
}
const a1: null = null as unknown as Awaited<Promise<Promise<string>>>;
const a2: null = null as unknown as Awaited<Thenable>;
const a3: null = null as unknown as SimpleAwaited<Thenable>;
const a4: null = null as unknown as Awaited<Promise<Thenable>>;

declare function over(x: string): string;
declare function over(x: number): number;
const r1: null = null as unknown as ReturnType<typeof over>;
const r2: null = null as unknown as Parameters<typeof over>;
console.log(a1, a2, a3, a4, r1, r2);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.28d.ts (tsc exit=1) =====
ex.28d.ts(6,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.28d.ts(7,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.28d.ts(8,7): error TS2322: Type 'Thenable' is not assignable to type 'null'.
ex.28d.ts(9,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.28d.ts(13,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.28d.ts(14,7): error TS2322: Type '[x: number]' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 6행 — `Awaited<Promise<Promise<string>>>` 가 **`string`**. **재귀로 끝까지** 벗긴다 — [**25번 주제**](../25-infer-and-recursive-conditional-types/) 4절이 실측한 그 성질이다. **인용한다.**
- ★★★ 7행과 8행 — `then` 만 가진 객체 `Thenable` 을 내장 `Awaited` 는 **`number`** 로 벗기고, `Promise` 만 보는 `SimpleAwaited` 는 **`Thenable` 그대로** 둔다.
  2절 격자의 유일한 「다름」이다. **`await` 가 thenable 을 벗기는 JS 규칙**을 타입이 따라간 것이다.
- ★ 9행 — `Promise<Thenable>` 은 **두 겹 다** 벗긴다(`number`).
- ★★★ 13·14행 — 오버로드가 `string → string`·`number → number` **둘인데** `ReturnType` 은 **`number`**, `Parameters` 는 **`[x: number]`**.
  **마지막 오버로드 하나**만 봤다. 「가능한 모든 반환의 유니온」이 **아니다.**


```text
  Awaited 는 이름이 아니라 모양을 본다

  내장 Awaited      T extends object & { then(onfulfilled: infer F, …): any }
                    → then 이 있으면 벗긴다 → Thenable → number
  SimpleAwaited     T extends Promise<infer U>
                    → Promise 라는 이름이어야 벗긴다 → Thenable 그대로

  ReturnType<typeof over>     over(x: string): string    ← 안 본다
                              over(x: number): number    ← ★ 이것 하나만
```
비용 — 오버로드 함수에 `ReturnType` 을 쓰면 **앞의 오버로드가 조용히 빠진다.**

### (6) ★★ `Record<string, T>` 와 인덱스 시그니처 · `Readonly` 의 깊이

**언제 쓰나** — 「`Record<string, number>` 와 `{ [k: string]: number }` 는 같은 것」이라고 쓰기 전에.

```ts
// ex.28e.ts
// Record 와 인덱스 시그니처 · Readonly 의 깊이
type Show<T> = { [K in keyof T]: T[K] } & {};
interface Dict {
    [k: string]: number;
}
type Rec = Record<string, number>;
const k1: null = null as unknown as keyof Rec;
const k2: null = null as unknown as keyof Dict;
const k3: null = null as unknown as keyof Show<Rec>;
const s1: null = null as unknown as Show<Rec>;
const both: Record<"a" | "b", number> = { a: 1 };

interface Deep {
    name: string;
    tags: string[];
    inner: { n: number };
}
const frozen: Readonly<Deep> = { name: "가", tags: [], inner: { n: 1 } };
frozen.name = "나";
frozen.tags.push("다");
frozen.inner.n = 2;
console.log(k1, k2, k3, s1, both, frozen);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.28e.ts (tsc exit=1) =====
ex.28e.ts(7,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.28e.ts(8,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.28e.ts(9,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.28e.ts(10,7): error TS2322: Type '{ [x: string]: number; }' is not assignable to type 'null'.
ex.28e.ts(11,7): error TS2741: Property 'b' is missing in type '{ a: number; }' but required in type 'Record<"a" | "b", number>'.
ex.28e.ts(19,8): error TS2540: Cannot assign to 'name' because it is a read-only property.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **7행과 8행이 갈렸다.** `keyof Record<string, number>` 는 **`string`**, 인터페이스의 인덱스 시그니처 `keyof Dict` 는 **`string | number`**.
  22편이 실측한 「문자열 인덱스 시그니처의 `keyof` 는 `string | number`」가 **`Record` 쪽에서는 안 일어났다.**
- ★★★ 10행 — 그런데 `Show<Rec>` 를 탐침하면 **`{ [x: string]: number; }`** 로, **인덱스 시그니처와 똑같은 글자**로 찍힌다.
  9행 `keyof Show<Rec>` 는 여전히 **`string`**. **찍힌 모양이 같아도 `keyof` 는 다르다** — 겉모양으로는 못 가른다.
- ★★ 11행 — `Record<"a" | "b", number>` 에 `a` 만 주면 **`TS2741`**「Property 'b' is missing …」. **키가 유한하면 전부 필수**다.
- ★★ 19행 — `Readonly<Deep>` 의 `name` 대입은 **`TS2540`** 으로 막힌다.
- ★★★ **20·21행에 진단이 없다.** `frozen.tags.push("다")` 와 `frozen.inner.n = 2` 가 **통과**한다. `Readonly` 는 **한 층만** 막는다 — 26편의 매핑이 **한 층만 돌기** 때문이다.

```text
  겉모양은 같은데 keyof 가 다르다

  interface Dict { [k: string]: number }     keyof → string | number   (22편과 같다)
  Record<string, number>                      keyof → string            ★
  Show<Record<string, number>>                모양  { [x: string]: number; }   keyof → string

  Readonly<Deep> — 한 층만
  frozen.name = …          TS2540   막힌다
  frozen.tags.push(…)      (없음)   ★ 속은 그대로 열려 있다
  frozen.inner.n = …       (없음)
```

비용 — `keyof` 를 다시 매핑에 쓰는 코드에서 두 꼴을 **섞어 쓰면 `number` 키가 한쪽에만** 생긴다.

### (7) ★ Python 의 `TypedDict` — `total=False` 가 `Partial` 과 닮았다

**언제 쓰나** — 「다른 언어는 **선택 필드 서식**을 어떻게 만드나」를 견줄 때.

```python
# td28.py
# 파이썬 TypedDict -- total=False 와 Required, 그리고 런타임은 무엇을 막나
from typing import Required, TypedDict


class User(TypedDict):
    id: int
    name: str


class UserPatch(TypedDict, total=False):
    id: int
    name: str


class Mixed(TypedDict, total=False):
    id: Required[int]
    name: str


for t in (User, UserPatch, Mixed):
    print(t.__name__, "required", sorted(t.__required_keys__), "optional", sorted(t.__optional_keys__))

made = User(name="x")
print(type(made).__name__, made)
```

```text
===== python3 td28.py (python3 exit=0) =====
User required ['id', 'name'] optional []
UserPatch required [] optional ['id', 'name']
Mixed required ['id'] optional ['name']
dict {'name': 'x'}
```

그림 해설 — 한 단계에 한 문장.

- ★★ `UserPatch`(`total=False`)는 **필수 키 `[]` · 선택 키 `['id', 'name']`** — `Partial<User>` 와 **같은 모양**이다.
- ★★ `Mixed` 는 `Required[int]` 로 **한 키만 되살렸다** — `total=False` 속에서 `-?` 한 칸을 쓴 셈이다.
- ★★★ 그런데 **`UserPatch` 는 `User` 에서 파생되지 않았다.** 필드를 **손으로 다시 적었다.** TS 의 `Partial<User>` 는 **원본을 받아 계산**한다 — 이것이 26·28 이 하는 일이다.
- ★★★ 마지막 줄 — `User(name="x")` 가 **`dict {'name': 'x'}`** 로 **그냥 만들어졌다.** 필수 키 `id` 가 없는데도. **런타임은 아무것도 검사하지 않는다** —
  `__required_keys__` 는 **정적 검사기가 읽으라고 둔 목록**이다. ★ 정적 검사기(mypy 등)는 **이 머신에 없어** 돌리지 않았다.

★ 정본 경계 — `TypedDict` 자체는
`` Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **38번** `` 이 정본이다(폴더가 아직 없다).
**그쪽은 세 구조체의 런타임 정체까지, 여기는 「원본에서 선택 서식을 계산하느냐 손으로 적느냐」까지**다.
★ Kotlin 에는 **타입에서 타입을 찍어 내는 틀 자체가 없다** — `data class` 의 `copy` 처럼 **컴파일러가 멤버를 생성**하는 쪽이다([**26번 주제**](../26-mapped-types/) 관련 자료).


```text
  선택 서식을 만드는 두 길

  TS       type UserPatch = Partial<User>        원본을 받아 계산한다 → User 가 바뀌면 따라간다
  Python   class UserPatch(TypedDict, total=False):
               id: int                           필드를 다시 적는다   → User 가 바뀌어도 그대로
               name: str
           런타임   User(name="x")  → 그냥 dict — 아무것도 안 막는다
```
비용 — 손으로 적은 선택 서식은 **원본이 바뀌어도 안 따라간다.**

### (8) ★ 설정 대조와 표시 순서 — 근거로 쓸 칸을 먼저 못 박는다

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.28a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.28b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.28c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.28d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.28e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.26c.ts    5회 md5 가짓수 1
ex.27a.ts    5회 md5 가짓수 1
ex.28a.ts    5회 md5 가짓수 1
ex.28b.ts    5회 md5 가짓수 1
```

그림 해설 — 한 단계에 한 문장.

- ★★ `--strict` 를 꺼도 **다섯 파일이 한 글자도 안 갈렸다.** 26편(셋이 갈림)과 다르다 — 이 주제의 탐침에는 **`?` 속성이 찍히는 줄이 없다.**
- ★★ 같은 명령을 5회 돌려 md5 **가짓수가 1** 이다(28a·28b 줄). 유니온 원소의 **표시 순서가 안 흔들렸다.** ★ **관찰이지 보장이 아니다.**

비용 — 없다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것 (정의는 3절 블록)
  Partial<T> · Required<T> · Readonly<T>    26 의 동형 매핑 한 줄          (2절)
  Pick<T, K extends keyof T>                키를 검사한다                  (4절)
  Omit<T, K extends keyof any>              ★ 키를 검사하지 않는다          (4절)
                                            ★ 유니온을 먼저 합친다          (1절)
  Record<K, V>                              동형이 아니다 · keyof 는 K     (6절)
  Exclude<T, U> · Extract<T, U>             24 의 분배 조건부              (2절)
  ReturnType<F> · Parameters<F>             25 의 infer — 마지막 오버로드  (5절)
  Awaited<T>                                25 의 재귀 — thenable 까지     (5절)
  T extends unknown ? Omit<T, K> : never    분배형 Omit — 표준에 없다      (1절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `Omit` 한 판별 유니온에서 좁힌 뒤 멤버 전용 필드 | `TS2339` | 1절 21행 |
| `Omit` 한 판별 유니온에 멤버 모양 리터럴 | `TS2353` | 1절 23행 |
| `Pick<User, "nmae">` | `TS2344` | 4절 7행 |
| `Record<"a" \| "b", number>` 에 `a` 만 | `TS2741` | 6절 11행 |
| `Readonly<Deep>` 의 겉 필드 대입 | `TS2540` | 6절 19행 |

**규칙 불릿**

- ★★★ **유틸리티 타입은 매핑·조건부·`infer` 한두 줄이다** — 열한 개를 다시 만들어 보통 인자 11 / 11 이 같았다(2절).
- ★★★ **`Omit` 은 `keyof T` 를 유니온 전체에서 먼저 계산해 공통 키만 남긴다** — 판별 능력을 잃는다(1절).
- ★★★ **분배형 `Omit` 으로 고친다** — `T extends unknown ? Omit<T, K> : never`(1절 16행).
- ★★ **`Pick` 은 키를 검사하고 `Omit` 은 안 한다** — 제약 한 줄 차이다(3·4절).
- ★★ **`Awaited` 는 thenable 을 끝까지 벗긴다** — `Promise` 라는 이름을 안 본다(3·5절).
- ★★ **`ReturnType`·`Parameters` 는 마지막 오버로드만 본다**(5절).
- ★★ **`keyof Record<string, T>` 는 `string` — 인덱스 시그니처와 다르다**(6절 7·8행).
- ★★ **`Readonly` 는 한 층만 막는다**(6절 20·21행).

## 어디서 틀리나

- ★★★ 「**`Omit` 은 필드 하나만 빼니 유니온도 그대로 두겠지**」 — **한 장으로 합친다**(1절 16행). 판별 필드는 남지만 **판별 능력을 잃는다.**
- ★★★ 「**판별 필드가 남았으니 좁히면 되겠지**」 — **좁힐 멤버가 없다**(1절 21행 `TS2339`).
- ★★★ 「**`Omit` 의 붕괴는 tsc 의 버그겠지**」 — **정의의 모양**이다. 같은 모양으로 직접 만들어도 **똑같이 무너졌다**(2절 모서리).
- ★★ 「**`Omit` 도 `Pick` 처럼 오타를 잡겠지**」 — **안 잡는다.** 아무것도 안 빼고 통과한다(4절 8행).
- ★★ 「**`Partial` 도 유니온에서 무너지겠지**」 — **안 무너진다.** 동형 매핑이라 멤버마다 돈다(2절 모서리).
- ★★ 「**`ReturnType` 은 오버로드의 반환을 다 모아 주겠지**」 — **마지막 하나**다(5절 13행).
- ★★ 「**`Awaited` 는 `Promise` 만 벗기겠지**」 — **thenable 이면 다 벗긴다**(5절 7행).
- ★★ 「**`Record<string, T>` 는 인덱스 시그니처와 완전히 같겠지**」 — **`keyof` 가 다르다**(6절 7·8행). 찍힌 모양은 같아서 **눈으로는 못 가른다.**
- ★★ 「**`Readonly` 면 속까지 못 바꾸겠지**」 — **한 층만**(6절 20·21행).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(표준 라이브러리 선언)** | 열한 개의 정의 — `lib.es5.d.ts` 에 **적힌 그대로** | 3절 — 정의를 직접 읽었다 |
| **언어 보장** | 유니온의 `keyof` 는 교집합 · 네이키드 조건부는 분배 | 22편 1절 · 24편 — 인용 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ `Omit<Cat \| Dog, "id">` = `{ kind: "cat" \| "dog"; }` | 1절 16행 — **던져서** 얻었다 |
| **★ 이 판의 관찰** | ★★ 직접 다시 만든 열한 개가 **보통 11 / 11 · 모서리 10 / 11** 같다 | 2절 — **이 인자들에서** 본 것이다 |
| **★ 이 판의 관찰** | 오버로드는 마지막 하나 · `keyof Record<string, T>` 는 `string` | 5·6절 |
| **★ 판에 달렸다** | `lib.es5.d.ts` 의 **줄 번호와 주석** | 3절 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 같다** | 8절 |
| **이 판의 관찰** | 유니온 원소의 **표시 순서** | 8절 — 5회 md5 가짓수 1 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | 26편 0절 |
| **★ 부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** | `.js` 블록 **없음** |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다** |

★★ 이 주제는 **「구현 층」 칸이 비어 있다** — 격자의 결론이 **선언 파일의 모양**에서 곧바로 나오기 때문이다.
25 처럼 **컴파일러의 한계 수**에 기댄 결론이 **하나도 없다.**

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| `Partial`·`Required`·`Readonly` — **유니온에도** 안전하다(동형) | 속까지 막아야 할 때의 `Readonly` — **한 층만** 막는다 |
| `Pick` — 키 오타를 **잡아 준다** | — |
| `Omit` — **단일 객체 타입**에서 | ★★★ **판별 유니온**에서 — **분배형 `Omit`** 을 쓴다 |
| `Omit` 에 **오타가 없다는 확신**이 있을 때 | 키 오타가 두려우면 — `K extends keyof T` 로 **제약을 좁힌** `StrictOmit` |
| `ReturnType` — **오버로드 없는** 함수 | 오버로드 함수 — **마지막 것만** 나온다 |
| `Record<"a" \| "b", V>` — 키가 **유한**하고 전부 필수일 때 | `Record<string, V>` 를 인덱스 시그니처와 **섞어 쓸** 때 — `keyof` 가 다르다 |

## 핵심 문장

1. **유틸리티 타입은 매핑·조건부·`infer` 로 만든 한두 줄이다** — 직접 다시 만들면 같은 글자가 나온다.
2. **★★★ `Omit` 은 유니온의 `keyof` 를 먼저 계산해 공통 키만 남긴다** — 결과는 한 장이고 판별 능력이 없다.
3. **분배형 `Omit`(`T extends unknown ? Omit<T, K> : never`)으로 고친다** — 분배만 켜는 조건부다.
4. **`Pick` 은 키를 검사하고 `Omit` 은 안 한다** — 제약 한 줄의 차이다.
5. **`Awaited` 는 thenable 까지, `ReturnType` 은 마지막 오버로드만, `Readonly` 는 한 층만.**

## 관련 자료

- [**26번 주제** — 매핑 타입](../26-mapped-types/) — ★★★ **선행이자 사슬의 앞.** `Partial`·`Required`·`Readonly`·`Pick`·`Record` 가 그쪽의 매핑 한 줄이다. **동형 매핑이 유니온에 분배되는 것**도 그쪽 3절에서 나온다. `Show` 조수도 그쪽.
- [**22번 주제** — `keyof` 와 인덱스 접근 타입](../22-keyof-and-indexed-access-types/) — ★★★ **「유니온의 `keyof` 는 교집합」의 정본.** 1절의 붕괴가 그 성질 위에 서 있다.
- [**24번 주제** — 조건부 타입과 분배](../24-conditional-types-and-distribution/) — ★★ `Exclude`·`Extract` 를 **이미 직접 다시 만들었다**(그쪽 5절). 분배형 `Omit` 의 기제도 그쪽이다.
- [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) — `ReturnType`·`Parameters` 가 `infer` 한 줄이고 `Awaited` 가 재귀라는 것은 그쪽에서 확인했다.
- [**27번 주제** — 템플릿 리터럴 타입](../27-template-literal-types/) — `Uppercase` 등 **문자열 조작 유틸리티**는 그쪽. `lib.es5.d.ts` 에는 `intrinsic` 으로만 적혀 있다.
- [**12번 주제** — 좁히기](../12-narrowing/) — 1절 21행의 「좁혔는데 필드가 없다」는 **판별 유니온 좁히기**가 전제다.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — 1절 23행의 `TS2353` 은 그쪽의 검사다.
- [**29번 주제**](../29-satisfies/)(`satisfies`) — `Record<K, V>` 를 **검사용 틀**로 쓰는 자리가 그쪽에 나온다.
- [목록의 **45번 주제**](../45-type-level-performance/)(타입 수준 성능) — 검사 시간은 그쪽이다.
- `` Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **38번** `` — `TypedDict` 의 정본(7절).

## 용어 풀이

> **유틸리티 타입(utility type)** — 표준 라이브러리가 미리 적어 둔 **타입을 받아 타입을 돌려주는** 제네릭 별칭.\
> 예: `Partial<User>` 는 `User` 의 필드를 전부 선택으로 만든다.

> **판별 유니온(discriminated union)** — 멤버마다 **리터럴 값이 다른 공통 필드**(`kind`)를 가져 그것으로 좁힐 수 있는 유니온.\
> 예: `Cat | Dog` 에서 `kind === "cat"` 이면 `Cat` 으로 좁혀진다.

> **분배형 `Omit`** — `T extends unknown ? Omit<T, K> : never`. 조건은 늘 참이고 **분배만 켜서** 멤버마다 `Omit` 한다.\
> 예: 1절 16행 — 유니온이 살아남는다.

> **thenable** — **`then` 메서드**를 가진 아무 객체. `await` 가 `Promise` 처럼 다룬다.\
> 예: `{ then(cb: (v: number) => void): void }` — `Awaited` 가 `number` 로 벗긴다(5절 7행).

> **오버로드(overload)** — 한 함수에 **서명을 여러 개** 적는 것.\
> 예: 5절의 `over` — `ReturnType` 은 **마지막 서명**만 본다.

> **`keyof any`** — `string | number | symbol`. **키가 될 수 있는 모든 것.**\
> 예: `Omit` 의 `K extends keyof any` 가 **오타를 못 잡는** 까닭이다(3·4절).

> **`Eq<A, B>`** — 두 타입이 **서로 같은지**를 묻는 흔한 비교형. 두 제네릭 함수 타입의 할당 가능성으로 견준다.\
> 예: 2절 격자의 `Eq` 열.

> **`TypedDict`(Python)** — 키와 값 타입이 정해진 `dict` 를 **정적 검사기에게** 알리는 선언. 런타임은 그냥 `dict` 다.\
> 예: `total=False` 면 모든 키가 선택이다(7절).

## 더 들어가면

- **왜 표준 `Omit` 은 분배형이 아닌가** — 3.5 릴리스 노트는 `Omit` 을 `Pick<T, Exclude<keyof T, K>>` 로 **추가했다**고만 적는다.
  분배형이 아닌 까닭을 **공식 문장으로 확인하지는 않았다.** 이 문서가 말할 수 있는 것은 「**정의의 모양이 그렇고, 그 모양이면 무너진다**」까지다(2절 모서리).
- **`StrictOmit` 을 유니온에 쓰면** — `K extends keyof T` 인데 `keyof (Cat | Dog)` 는 공통 키뿐이라 **멤버 전용 키는 넘길 수조차 없다.**
  분배형과 엄격형을 **둘 다** 원하면 `T extends unknown ? Omit<T, K> : never` 에 `K extends keyof T` 를 **따로** 걸어야 하는데, 그 조합은 **안 던졌다.**
- **`Readonly` 를 깊게** — 재귀 매핑이 흔한 답이다. [**26번 주제**](../26-mapped-types/) 「더 들어가면」에 형태만 적었고, **안 던졌다.**
- **`Parameters` 가 레이블을 살리는 것** — 2절 격자에서 `[x: number, y: string]` 처럼 **이름이 남았다.** [**25번 주제**](../25-infer-and-recursive-conditional-types/) 1절 12행과 같은 현상이다.
