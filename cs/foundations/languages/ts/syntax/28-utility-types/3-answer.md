# ts/syntax/28 — 유틸리티 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자는 `tsc` **7.0.2** · `python3` **3.12.3** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★ 조수는 둘이다 — 객체는 `Show<…>`(26편 1절), `never` 가 나올 수 있는 조건부는 `[ … ]`(튜플로 감싸 **침묵을 글자로**).\
> ★★ 이 주제의 **본체 창은 격자(직접 다시 만들기)다** — 4번이 결론을 낸다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `Omit<Pet, "id">` 는 **`{ kind: "cat" | "dog"; }` 한 장**이다 — 좁혀도 `meows` 가 없다

**출력**

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

**왜 그런가**

| 줄 | 물은 것 | 답 |
|---|---|---|
| 15 | `keyof Pet` | **`"id" \| "kind"`** — 공통 키뿐(교집합) |
| 16 | ★★★ `Show<Omit<Pet, "id">>` | **`{ kind: "cat" \| "dog"; }`** — `meows`·`barks` 가 **사라지고** 결과가 **한 장** |
| 17 | `Show<Omit<Cat, "id">>` | `{ kind: "cat"; meows: boolean; }` — 단일 객체면 멀쩡하다 |
| 21 | ★★★ 좁힌 뒤 `pet.meows` | **`TS2339`** — 좁힐 멤버가 **이미 없다** |
| 23 | `{ kind: "cat", meows: true }` 대입 | **`TS2353`** — `meows` 가 **없는 속성**이 됐다 |

- ★★★ 판별 필드 `kind` 는 **남았다.** 그런데 `"cat" | "dog"` 으로 **합쳐져서** 좁힐 근거가 못 된다 — **판별 능력을 잃었다.**
  「판별 필드를 잃는다」가 아니라 「**필드는 남고 멤버가 사라진다**」가 정확한 그림이다.
- ★★ 에러가 `Omit` 을 쓴 줄이 아니라 **그 값을 쓰는 줄**(21·23행)에서 난다.

### 2. ★★★ **유니온이 살아난다** — 진단은 **23행 하나**

**출력**

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

**왜 그런가**

```text
  1번 16행   { kind: "cat" | "dog"; }                                       한 장
  2번 16행   { kind: "cat"; meows: boolean; } | { kind: "dog"; barks: boolean; }   ★ 두 장
```

- ★★★ 20행 — **진단 없음.** `pet.kind === "cat"` 뒤에서 `meows` 가 읽힌다. 판별이 돌아왔다.
- ★★ 22행 — **진단 없음.** `Cat` 모양이 그대로 들어간다.
- ★★ 23행 — **`TS2353`** — `kind: "cat"` 인데 `barks` 를 준 것은 **막혀야 할 것이 막힌** 자리다.
  진단이 `'Omit<Cat, "id">'` 라고 **멤버 이름으로** 말하는 것이 유니온이 살아 있다는 증거다.
- ★★ `T extends unknown ? Omit<T, K> : never` 의 `T` 가 **네이키드**라 **분배된다**([**24번 주제**](../24-conditional-types-and-distribution/)).

### 3. ★★ 진단은 **7·12행** — **8행은 조용히 통과**하고 아무것도 안 뺀다

**출력**

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

**왜 그런가**

- ★★ 7행 `Pick<User, "nmae">` — **`TS2344`**. 제약 `K extends keyof T` 가 오타를 잡는다.
- ★★★ **8행 `Omit<User, "nmae">` — 진단 없음.** 9행 탐침이 **`{ id: number; name: string; }`** — **아무것도 안 뺐다.**
- ★★ 12행 — 제약만 `K extends keyof T` 로 바꾼 `StrictOmit` 은 **`TS2344`** 로 잡는다. 차이가 **제약 한 줄**이라는 증명이다(7번).

### 4. ★★★ 보통 **11 / 11** — 모서리는 **`Awaited<Thenable>` 한 칸**만 갈린다 — `Omit` 붕괴는 **둘이 같다**

**출력**

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

**왜 그런가**

- ★★★ **보통 인자 — 글자 11 / 11 · `Eq` 11 / 11.** 열한 개가 **매핑·조건부·`infer` 한두 줄**로 전부 다시 만들어진다.
- ★★★ **모서리 — 10 / 11.** 갈린 한 칸은 **`Awaited<Thenable>`** — 내장 **`[number]`**, 직접 만든 것 **`[Thenable]`**.
  내장은 `then` 이 있으면 벗기고(5번), `MyAwaited` 는 **`Promise` 만** 본다.
- ★★★ 모서리의 **`Omit<Cat | Dog, "id">` 는 둘 다 `{ kind: "cat" | "dog"; }`** — **같이 무너졌다.**
  1번의 붕괴는 **정의의 모양**에서 나오는 것이지 tsc 의 버그가 아니다.
- ★★ 모서리의 `Partial<Cat | Dog>` 는 **멤버마다** 선택화된 **유니온**이다 — 9번의 실마리다.
- ★ `Exclude`·`Extract` 의 모서리는 **`[never]`** — 튜플 조수가 없었으면 **탐침이 침묵했을** 칸이다(제5의 상태).

### 5. ★★ **`number` 대 `Thenable`** — 오버로드는 **마지막 하나(`number`·`[x: number]`)**

**출력**

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

**왜 그런가**

- ★★★ 7행 `Awaited<Thenable>` 은 **`number`**, 8행 `SimpleAwaited<Thenable>` 은 **`Thenable`**.
  내장 `Awaited` 의 정의(요약 3절 블록)는 **`Promise` 라는 이름을 한 번도 안 쓰고** `then(onfulfilled: infer F, …)` 모양만 본다 — JS 의 `await` 가 thenable 을 벗기는 것과 맞췄다.
- ★ 6행은 `string` — 여러 겹을 **끝까지** 벗기는 재귀다([**25번 주제**](../25-infer-and-recursive-conditional-types/) 4절 인용).
- ★★★ 13행 `ReturnType<typeof over>` 는 **`number`**, 14행 `Parameters<typeof over>` 는 **`[x: number]`**.
  `string → string` 서명은 **조용히 빠졌다.** `infer` 는 오버로드 중 **마지막 서명 하나**에서 뽑았다.

### 6. ★★ 7·8행은 **다르다**(`string` 대 `string | number`) — 10행은 **같아 보이고** 9행은 여전히 `string` — 막히는 줄은 **19행**

**출력**

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

**왜 그런가**

- ★★★ `keyof Record<string, number>` 는 **`string`**, `keyof Dict`(인덱스 시그니처)는 **`string | number`**.
- ★★★ 10행 — `Show<Rec>` 는 **`{ [x: string]: number; }`** 로 **인덱스 시그니처와 같은 글자**로 찍힌다. 그런데 9행 `keyof Show<Rec>` 는 **`string`** 그대로다.
  **찍힌 모양이 같아도 `keyof` 는 다르다.** 겉모양으로는 못 가른다.
- ★★ 11행 — 키가 유한한 `Record` 는 **전부 필수**라 `b` 가 빠지면 **`TS2741`**.
- ★★★ 19행만 **`TS2540`**. 20행 `tags.push` 와 21행 `inner.n = 2` 는 **통과**한다 — `Readonly` 는 **한 층만** 막는다.

### 7. ★★ **`K extends keyof T`** 대 **`K extends keyof any`**

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

- ★★★ `type Pick<T, K extends keyof T>` — `K` 는 「**`T` 의 키**」여야 한다. 오타는 제약 위반(`TS2344`).
- ★★★ `type Omit<T, K extends keyof any>` — `K` 는 **아무 키**(`string | number | symbol`)나 된다. 오타도 **키 모양**이라 통과한다.
- ★ 그래서 3번 12행처럼 **제약만 좁히면** 잡힌다.

### 8. ★★★ **`keyof (Cat | Dog)` 가 먼저** 계산되고, 거기서 멤버 전용 키가 이미 빠진다

```text
  Omit<Cat | Dog, "id">
    = Pick< Cat | Dog, Exclude< keyof (Cat | Dog), "id" > >
    = Pick< Cat | Dog, Exclude< "id" | "kind", "id" > >        ① keyof (Cat | Dog) = "id" | "kind"
    = Pick< Cat | Dog, "kind" >                                 ② Exclude 가 "id" 를 뺐다
    = { kind: (Cat | Dog)["kind"] }                             ③ Pick 은 [P in K] 한 번만 돈다
    = { kind: "cat" | "dog" }                                   ④ 한 장 — 1번 16행과 같다
```

- ★★★ **①이 22편의 실측이다** — 유니온의 `keyof` 는 **교집합**([**22번 주제**](../22-keyof-and-indexed-access-types/) 1절 39행). 1번 15행이 같은 답을 냈다.
- ★★ ③ — `Pick` 은 `[P in K]` 라 **`T` 를 멤버마다 쪼개지 않는다.** `T[P]` 를 유니온째 읽으니 `"cat" | "dog"` 이 된다.

### 9. ★★★ 모양이 **다르다** — **동형 매핑이냐**가 가른다 · 분배형은 **분배만 켜려고** 조건부를 쓴다

- ★★★ `Partial<T>` 는 `{ [P in keyof T]?: T[P] }` — **`keyof T` 를 글자 그대로 적은 동형 매핑**이다. 동형 매핑은 `T` 가 유니온이면 **멤버마다 따로** 돈다(4번 모서리의 `Partial<Cat | Dog>`).
  [**26번 주제**](../26-mapped-types/) 3절이 「`in` 뒤에 `keyof T` 가 적혀 있느냐」로 수정자 보존이 갈리는 것을 보였다 — 같은 조건이다.
- ★★★ `Omit` 은 `Pick<T, 계산된 키>` 다. 키가 **이미 계산이 끝난 유니온**으로 들어오니 `T` 를 멤버로 쪼갤 계기가 없다(8번 ①).
- ★★ 분배형 `Omit` 의 `T extends unknown ? … : never` 는 **조건이 늘 참**이다. 목적은 조건이 아니라 **분배** —
  네이키드 `T` 가 `extends` 왼쪽에 서면 유니온이 멤버마다 조건부를 탄다([**24번 주제**](../24-conditional-types-and-distribution/)).

### 10. ★★ `Partial` 과 닮았다 — **손으로 다시 적었다**는 것이 다르고, 런타임은 **안 막는다**

**출력**

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

**왜 그런가**

- ★★ `UserPatch` 는 **필수 `[]` · 선택 `['id', 'name']`** — `Partial<User>` 와 같은 모양이다. `Mixed` 의 `Required[int]` 는 `-?` 한 칸 꼴이다.
- ★★★ 그런데 **`User` 에서 계산된 것이 아니다.** 필드를 **다시 적었다.** 원본이 바뀌면 **안 따라간다.**
- ★★★ `User(name="x")` 는 **`dict {'name': 'x'}`** — **막히지 않았다.** `__required_keys__` 는 **정적 검사기가 읽을 목록**이고 런타임은 검사하지 않는다.
  ★ 정적 검사기(mypy 등)는 **이 머신에 없어** 돌리지 않았다.
- ★ 정본 경계 — `` Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **38번** `` 이 `TypedDict` 의 정본이다.

### 11. ★ 세 층

| 층 | 이 주제의 예 |
|---|---|
| **선언 파일의 모양(표준 라이브러리)** | `Omit` 의 `K extends keyof any` · `Pick<T, Exclude<keyof T, K>>` · `Awaited` 의 `then` 모양(7번 블록) |
| **언어 보장(인용)** | 유니온의 `keyof` 는 교집합(22편) · 네이키드 조건부의 분배(24편) · 동형 매핑의 분배(26편) |
| **이 판에서 던져서 본 것** | `Omit<Cat \| Dog, "id">` = `{ kind: "cat" \| "dog"; }`(1번) · 격자 11 / 11 · 10 / 11(4번) · 오버로드는 마지막 하나(5번) · `keyof Record<string, T>` = `string`(6번) |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 다섯 파일 전부 같다 |

- ★★ **「구현 층」 칸이 비어 있다** — 이 주제의 결론은 **선언 파일에 적힌 한두 줄**에서 곧바로 나온다.
  [**25번 주제**](../25-infer-and-recursive-conditional-types/)의 `TS2589` 경계처럼 **컴파일러의 한계 수**에 기댄 결론이 **하나도 없다.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ `Omit` 붕괴 | `--noEmit ex.28a.ts` | exit 1 · **5건** · 16행 `{ kind: "cat" \| "dog"; }` · `TS2339` · `TS2353` |
| ★★★ 분배형 `Omit` | `--noEmit ex.28b.ts` | exit 1 · **2건** · ★ 20·22행 **진단 없음** |
| 키 검사 비대칭 | `--noEmit ex.28c.ts` | exit 1 · **3건** · ★ 8행 **진단 없음** |
| `Awaited`·오버로드 | `--noEmit ex.28d.ts` | exit 1 · **6건** · 7행 `number` 대 8행 `Thenable` |
| `Record`·`Readonly` | `--noEmit ex.28e.ts` | exit 1 · **6건** · ★ 20·21행 **진단 없음** |
| ★★★ 직접 다시 만들기 | `bash ts26b-diy.sh` (열한 개 × 두 인자 = **22회 컴파일**) | exit 0 · **보통 11 / 11 · 모서리 10 / 11** |
| 정의 읽기 | `grep … lib.es5.d.ts` | exit 0 · `Pick`·`Omit`·`Record`·`Exclude`·`Extract`·`ReturnType`·`Parameters`·`Awaited` |
| Python 대비 | `python3 td28.py` | exit 0 · ★ `User(name="x")` 가 **그냥 만들어진다** |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | **하나도 안 갈림** |
| 반복 실행 | 같은 명령 **5회** | md5 **가짓수 1** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **`lib.es5.d.ts` 의 정의**(7번) — 판마다 바뀔 수 있다. 모양이 바뀌면 **격자를 다시 돌려라.**
- ★★ **격자의 「같다」**(4번) — **이 인자들에서** 본 것이다. 다른 인자에서 갈릴 수 있다.
- ★ 유니온 원소의 **표시 순서** — 5회 동일했지만 **관찰이지 보장이 아니다.**

**안 돌려 본 것**

- ★★★ **검사 시간·메모리** — 재지 않았다.
- ★★ **분배형이면서 키를 검사하는 `Omit`** — 형태만 생각했고 **안 던졌다.**
- ★★ **Python 정적 검사기**(mypy·pyright) — 이 머신에 없다. 런타임 속성만 읽었다.
- ★ **`NonNullable`·`InstanceType`·`ConstructorParameters`·`ThisParameterType` 등** — README 가 지정한 열한 개만 격자에 넣었다.
