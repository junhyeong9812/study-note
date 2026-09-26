# ts/syntax/28 — 유틸리티 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **26 → 28 은 한 사슬이고 여기가 급소다** —
> [**26번 주제**](../26-mapped-types/)의 매핑, [**22번 주제**](../22-keyof-and-indexed-access-types/)의 `keyof`,
> [**24번 주제**](../24-conditional-types-and-distribution/)의 분배를 떠올리지 못하면 1·2번이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · `python3` **3.12.3**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
>
> ★★★ **계산된 타입을 눈으로 보는 법** — 블록에 `const probe: null = null as unknown as X;` 가 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ 소스마다 `type Show<T> = …` 가 끼어 있다 — 유틸리티 타입의 **별칭 이름 대신 펼친 모양**을 찍게 하는 조수다(26편 1절).
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> ★★ 이 주제의 **본체 창은 격자(직접 다시 만들기)다** — 4번이 그 자리다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. `Omit` 을 판별 유니온에 걸면 (예측)

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

- 15행 `keyof Pet` 은 무엇인가?
- 16행 `Show<Omit<Pet, "id">>` 는 무엇인가? 17행과 **어떻게 다른가**?
- 20·21행과 23행에서 **진단이 나는가**? 난다면 어떤 코드인가?

### 2. 멤버마다 따로 하면 (예측)

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

- 16행은 무엇인가? 1번 16행과 나란히 적어라.
- 20·22·23행 중 **진단이 나는 줄**은 어느 것인가?

### 3. 없는 키를 넘기면 (예측)

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

- 7·8·12행 중 **진단이 나는 줄**은 어느 것인가?
- 9행의 탐침은 무엇을 말하는가?

### 4. 열한 개를 손으로 다시 만들면 (예측)

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

- **보통 인자**에서 「글자가 같은 칸」은 몇 / 11 인가?
- **모서리 인자**에서 갈리는 칸이 있다면 어느 것이고, 내장과 직접 만든 것이 각각 무엇을 뱉는가?
- 모서리의 `Omit<Cat | Dog, "id">` 는 내장과 직접 만든 것이 **같은가**?

### 5. `Awaited` 와 오버로드 (예측)

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

- 7행과 8행의 답을 나란히 적어라.
- 13·14행 — 오버로드가 둘인데 무엇이 나오는가?

### 6. `Record` 와 `Readonly` (예측)

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

- 7행과 8행은 같은가?
- 10행이 찍는 모양은 `Dict` 와 **어떻게 보이는가**? 그렇다면 9행은?
- 19·20·21행 중 **막히는 줄**은 어느 것인가?

### 7. `Pick` 과 `Omit` 의 선언 (왜)

- `lib.es5.d.ts` 의 `Pick` 과 `Omit` 선언에서 **어느 한 조각**이 3번의 결과를 가르는가?

### 8. `Omit<Cat | Dog, "id">` 를 손으로 풀기 (왜)

- `Omit<T, K> = Pick<T, Exclude<keyof T, K>>` 에 `T = Cat | Dog` 를 넣고 **한 단계씩** 풀 수 있는가?
- 그 순서의 어느 단계가 [**22번 주제**](../22-keyof-and-indexed-access-types/)의 실측과 같은가?

### 9. `Partial` 과 `Omit` 을 유니온에 걸 때 (경계)

- 둘 다 매핑으로 만들어졌다. 유니온 앞에서 **결과의 모양이 같은가 다른가**? [**26번 주제**](../26-mapped-types/)의 어느 성질이 그것을 가르는가?
- 분배형 `Omit` 이 `T extends unknown ? … : never` 인 까닭 — 조건이 늘 참인데 **왜 쓰는가**?

### 10. Python 의 `TypedDict` 와 잇기 (연결)

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

- `UserPatch` 는 TS 의 어느 유틸리티와 닮았는가? **무엇이 다른가**?
- 마지막 줄 `User(name="x")` 는 런타임에 **막히는가**?

### 11. 세 층 가르기 (연결)

- 이 주제의 결론 중 **선언 파일의 모양**에서 나오는 것과 **이 판에서 던져서 본 것**을 하나씩 댈 수 있는가?
- 이 주제에 **「구현 층」 칸이 비어 있는** 까닭은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
