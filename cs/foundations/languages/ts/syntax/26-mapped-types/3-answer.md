# ts/syntax/26 — 매핑 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자는 `tsc` **7.0.2** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★★ **매핑 타입 앞에서 탐침은 메아리만 돌려준다.** 그래서 소스마다 `Show<T>` 조수가 끼어 있다(1번).\
> ★★ 이 주제의 **본체 창은 2창(`null` 탐침 + `Show` 조수)이다** — 2번은 격자 스크립트가 센다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `& {}` 도, 매핑 한 겹도 혼자서는 못 펼친다 — **둘을 합친 `Show` 만** 펼친다

**출력**

```ts
// ex.26a.ts
// 탐침이 매핑 타입을 어떻게 말하나 -- 별칭 이름 · & {} · 매핑으로 한 번 더 감싸기
interface User {
    id: number;
    readonly name: string;
    email?: string;
}
type Same<T> = { [K in keyof T]: T[K] };
type Show<T> = { [K in keyof T]: T[K] } & {};

const byAlias: null = null as unknown as Partial<User>;
const byIntersect: null = null as unknown as Partial<User> & {};
const byRemap: null = null as unknown as Same<Partial<User>>;
const byShow: null = null as unknown as Show<Partial<User>>;
const inline: null = null as unknown as { [K in keyof User]?: User[K] };
const identity: null = null as unknown as Show<User>;
console.log(byAlias, byIntersect, byRemap, byShow, inline, identity);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26a.ts (tsc exit=1) =====
ex.26a.ts(10,7): error TS2322: Type 'Partial<User>' is not assignable to type 'null'.
ex.26a.ts(11,7): error TS2322: Type 'Partial<User>' is not assignable to type 'null'.
ex.26a.ts(12,7): error TS2322: Type 'Same<Partial<User>>' is not assignable to type 'null'.
ex.26a.ts(13,7): error TS2322: Type '{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }' is not assignable to type 'null'.
ex.26a.ts(14,7): error TS2322: Type '{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }' is not assignable to type 'null'.
ex.26a.ts(15,7): error TS2322: Type '{ id: number; readonly name: string; email?: string | undefined; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 물은 꼴 | 답 |
|---|---|---|
| 10 | `Partial<User>` | **`Partial<User>`** — 메아리 |
| 11 | ★★★ `Partial<User> & {}` | **`Partial<User>`** — ★ **22편의 조수가 안 듣는다** |
| 12 | `Same<Partial<User>>` | **`Same<Partial<User>>`** — 별칭이 한 겹 늘 뿐 |
| 13 | ★★ `Show<Partial<User>>` | **`{ id?: number \| undefined; readonly name?: string \| undefined; email?: string \| undefined; }`** |
| 14 | 소스에 직접 적은 매핑 | 13행과 같은 글자 — 이름이 없으니 처음부터 펼쳐진다 |
| 15 | ★★ `Show<User>` | **원본 `User` 와 같은 글자** — 조수가 결과를 **안 바꾼다**는 확인 |

- ★★★ 22편에서는 `keyof User & {}` 가 펼쳐졌다. **키 유니온**에는 `& {}` 가 먹혔는데 **객체 모양의 별칭**에는 안 먹힌다.
  빈 객체와의 교차가 **그냥 지워지고** 별칭 이름이 살아남는다.
- ★★ `Show<T> = { [K in keyof T]: T[K] } & {}` 는 **매핑으로 새 익명 객체를 만들고**, `& {}` 로 **그 결과에 이름을 못 붙이게** 한다.
  둘 중 하나만으로는 안 된다(11·12행).
- ★★ 15행을 먼저 물어 두는 까닭 — `Show` 도 **매핑 타입**이다. 조수가 수정자를 떨어뜨리면 **모든 탐침이 거짓말**을 한다.
  `readonly name`·`email?` 이 그대로 나왔으니 이 조수는 **적어도 이 모양에서는** 믿을 수 있다.
- ★★★ 이 모든 것은 **tsc 7.0.2 의 「표시」 방식**이다. 명세가 정한 것이 아니다 — **구현 층**이다.

### 2. ★★ `keep` 은 원본을 지키고, `-?` 는 **`undefined` 까지** 지운다 — 갈린 칸 **20 / 36**

**출력**

```bash
# ts26b-modgrid.sh
#!/usr/bin/env bash
# 수정자 격자 -- readonly 3가지 x ? 3가지 = 매핑 아홉 벌, 필드 네 개씩
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
src='interface Src { a: number; readonly b: number; c?: number; readonly d?: number; }'
show='type Show<T> = { [K in keyof T]: T[K] } & {};'
mods() { # mods <type text> <field> -> r?(readonly) o?(optional)
  local t=$1 n=$2 ro=. op=.
  case "$t" in *"readonly $n"[?:]*) ro=r;; esac
  case "$t" in *"$n?:"*) op=o;; esac
  printf '%s%s' "$ro" "$op"
}
changed=0; total=0; texts=""
printf '%-10s %-5s | %-3s %-3s %-3s %-3s\n' readonly '?' a b c d
for r in keep + -; do
  for q in keep + -; do
    case $r in keep) rr='';; +) rr='+readonly ';; -) rr='-readonly ';; esac
    case $q in keep) qq='';; +) qq='+?';; -) qq='-?';; esac
    { echo "$src"; echo "$show"; echo "type M = { ${rr}[K in keyof Src]${qq}: Src[K] };"
      echo 'const probe: null = null as unknown as Show<M>;'; echo 'export {};'; } > "$D/p.ts"
    out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/p.ts" 2>&1)
    t=$(printf '%s\n' "$out" | sed -n "s/.*error TS2322: Type '\(.*\)' is not assignable to type 'null'\./\1/p" | head -1)
    row=""
    for n in a b c d; do
      m=$(mods "$t" "$n")
      row="$row $(printf '%-3s' "$m")"
      if [ "$r$q" = keepkeep ]; then eval "orig_$n=$m"; fi
      eval "o=\$orig_$n"
      total=$((total+1)); if [ "$m" != "$o" ]; then changed=$((changed+1)); fi
    done
    printf '%-10s %-5s |%s\n' "$r" "$q" "$row"
    texts="$texts$(printf '%-4s %-4s %s' "$r" "$q" "$t")"$'\n'
  done
done
echo
echo "탐침이 말한 글자 --"
printf '%s' "$texts"
echo
echo "원본(keep keep)과 갈린 칸 $changed / $total"
```

```text
===== bash ts26b-modgrid.sh (sh exit=0) =====
readonly   ?     | a   b   c   d  
keep       keep  | ..  r.  .o  ro 
keep       +     | .o  ro  .o  ro 
keep       -     | ..  r.  ..  r. 
+          keep  | r.  r.  ro  ro 
+          +     | ro  ro  ro  ro 
+          -     | r.  r.  r.  r. 
-          keep  | ..  ..  .o  .o 
-          +     | .o  .o  .o  .o 
-          -     | ..  ..  ..  .. 

탐침이 말한 글자 --
keep keep { a: number; readonly b: number; c?: number | undefined; readonly d?: number | undefined; }
keep +    { a?: number | undefined; readonly b?: number | undefined; c?: number | undefined; readonly d?: number | undefined; }
keep -    { a: number; readonly b: number; c: number; readonly d: number; }
+    keep { readonly a: number; readonly b: number; readonly c?: number | undefined; readonly d?: number | undefined; }
+    +    { readonly a?: number | undefined; readonly b?: number | undefined; readonly c?: number | undefined; readonly d?: number | undefined; }
+    -    { readonly a: number; readonly b: number; readonly c: number; readonly d: number; }
-    keep { a: number; b: number; c?: number | undefined; d?: number | undefined; }
-    +    { a?: number | undefined; b?: number | undefined; c?: number | undefined; d?: number | undefined; }
-    -    { a: number; b: number; c: number; d: number; }

원본(keep keep)과 갈린 칸 20 / 36
```

**왜 그런가**

- ★★★ `readonly` 칸이 `keep` 인 세 줄(`keep keep`·`keep +`·`keep -`)에서 **`b`·`d` 의 `r` 가 그대로**다.
  `?` 칸이 `keep` 인 세 줄에서도 **`c`·`d` 의 `o` 가 그대로**다. 격자의 `[K in keyof Src]` 가 **동형**이라 원본 수정자가 따라왔다.
- ★★ `+` 는 **전부에** 붙이고 `-` 는 **전부에서** 뗀다. 원본에 있었는지 따지지 않는다.
- ★★★ 「탐침이 말한 글자」에서 `keep -` 줄을 보라 — **`c: number; readonly d: number;`** 이다.
  `?` 를 떼면 **`| undefined` 도 같이** 떨어진다. `+` 줄에서는 거꾸로 **같이 붙는다.**
- ★★ 마지막 줄 **원본과 갈린 칸 20 / 36** — 스크립트가 센 것이다. 나머지 16 칸은 **`keep` 이 지킨 칸**과 **`+`/`-` 가 원래 값과 우연히 같은 칸**이다.
- ★ 두 축은 **서로 모른다.** `readonly` 를 떼는 것이 `?` 에 아무 영향도 안 준다 — 아홉 벌이 전부 두 축의 곱이다.

### 3. ★★★ 따라오는 줄은 14·16·17·18행 — **18과 19는 키가 같은데 갈린다**

**출력**

```ts
// ex.26b.ts
// 동형 매핑 -- 원본의 수정자가 따라오는 자리와 안 따라오는 자리
type Show<T> = { [K in keyof T]: T[K] } & {};
interface Src {
    a: number;
    readonly b: number;
    c?: number;
}
type ByKeyof<T> = { [K in keyof T]: string };
type ByList<T> = { [K in "a" | "b" | "c"]: string };
type ByParam<T, Keys extends keyof T> = { [K in Keys]: string };
type ByAs<T> = { [K in keyof T as K]: string };
type SrcKeys = keyof Src;

const h1: null = null as unknown as Show<ByKeyof<Src>>;
const h2: null = null as unknown as Show<ByList<Src>>;
const h3: null = null as unknown as Show<ByParam<Src, "a" | "b" | "c">>;
const h4: null = null as unknown as Show<ByAs<Src>>;
const h5: null = null as unknown as Show<{ [K in keyof Src]: string }>;
const h6: null = null as unknown as Show<{ [K in SrcKeys]: string }>;
console.log(h1, h2, h3, h4, h5, h6);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26b.ts (tsc exit=1) =====
ex.26b.ts(14,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(15,7): error TS2322: Type '{ a: string; b: string; c: string; }' is not assignable to type 'null'.
ex.26b.ts(16,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(17,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(18,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(19,7): error TS2322: Type '{ a: string; b: string; c: string; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | `in` 뒤 | 수정자 |
|---|---|---|
| 14 | `keyof T` | **따라온다** |
| 15 | `"a" \| "b" \| "c"` | **안 따라온다** |
| 16 | `Keys` (`Keys extends keyof T`) | **따라온다** — ★ `Pick` 의 꼴 |
| 17 | `keyof T as K` | **따라온다** |
| 18 | `keyof Src` (제네릭 아님) | **따라온다** |
| 19 | ★★★ `SrcKeys` (= `keyof Src` 의 별칭) | **안 따라온다** |

- ★★★ 18행과 19행은 **키 목록이 한 글자도 같다.** 그런데 결과가 갈린다.
  갈리는 축은 「무엇이 키냐」가 아니라 「**`keyof 무엇` 이라고 소스에 적혀 있느냐**」다.
- ★★ 별칭 `SrcKeys` 는 **계산이 끝난 키 유니온**이라, 컴파일러가 거기서 원본 `Src` 를 되짚을 길이 없다 — 출력에서 읽은 해석이다.
- ★★ 진단이 **어디에도 없다.** 수정자가 빠진 것은 **탐침으로 모양을 봐야만** 드러난다.

### 4. ★★ 6행은 **배열**이고, `length` 는 **`2` · `{ v: 2; }` · `{ v: 2; }`** 다

**출력**

```ts
// ex.26d.ts
// 매핑 타입을 배열 · 튜플에 걸면
type Boxed<T> = { [K in keyof T]: { v: T[K] } };
type BoxedAs<T> = { [K in keyof T as K]: { v: T[K] } };
type Tup = [1, "가"];

const m1: null = null as unknown as Boxed<string[]>;
const m2: null = null as unknown as Boxed<Tup>;
const m3: null = null as unknown as Boxed<readonly [1, 2]>;
const m4: null = null as unknown as Partial<Tup>;
const m5: null = null as unknown as Boxed<Tup>["length"];
const m6: null = null as unknown as BoxedAs<Tup>["length"];
const m7: null = null as unknown as { [K in keyof Tup]: { v: Tup[K] } }["length"];
console.log(m1, m2, m3, m4, m5, m6, m7);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26d.ts (tsc exit=1) =====
ex.26d.ts(6,7): error TS2322: Type '{ v: string; }[]' is not assignable to type 'null'.
ex.26d.ts(7,7): error TS2322: Type '[{ v: 1; }, { v: "가"; }]' is not assignable to type 'null'.
ex.26d.ts(8,7): error TS2322: Type 'readonly [{ v: 1; }, { v: 2; }]' is not assignable to type 'null'.
ex.26d.ts(9,7): error TS2322: Type '[(1 | undefined)?, ("가" | undefined)?]' is not assignable to type 'null'.
ex.26d.ts(10,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.26d.ts(11,7): error TS2322: Type '{ v: 2; }' is not assignable to type 'null'.
ex.26d.ts(12,7): error TS2322: Type '{ v: 2; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 물은 꼴 | 답 |
|---|---|---|
| 6 | `Boxed<string[]>` | **`{ v: string; }[]`** — 배열로 남는다 |
| 7 | `Boxed<Tup>` | **`[{ v: 1; }, { v: "가"; }]`** — 튜플로 남는다 |
| 8 | `Boxed<readonly [1, 2]>` | **`readonly [{ v: 1; }, { v: 2; }]`** |
| 9 | `Partial<Tup>` | **`[(1 \| undefined)?, ("가" \| undefined)?]`** — 선택 칸 튜플 |
| 10 | `Boxed<Tup>["length"]` | **`2`** |
| 11 | ★★★ `BoxedAs<Tup>["length"]` | **`{ v: 2; }`** — ★ `as` 가 튜플을 **객체로 펼쳤다** |
| 12 | ★★ 튜플에 **직접** 적은 매핑의 `["length"]` | **`{ v: 2; }`** — 제네릭을 안 거치면 특례가 없다 |

- ★★★ 특례의 조건은 **둘**이다 — **제네릭 동형 매핑**이어야 하고, **`as` 가 없어야** 한다. 11·12행이 각각 한쪽을 어겼다.
- ★★ 탐침을 `Show` 로 안 감싼 까닭 — `Show` 도 매핑이라 **배열에서는 배열로 남는다.**
  그래서 이 문항은 `["length"]` **한 칸**으로 물었다(제5의 상태 — 같은 질문을 다른 창으로).

### 5. ★★ 15·17행은 `password`·`save` 가 빠지고, 18행은 **`{}`**, 19행은 **에러 없이 한 줄로 합쳐진다**

**출력**

```ts
// ex.26c.ts
// as 로 키를 다시 짓는다 -- 거르기 · 이름 바꾸기 · 값으로 거르기 · 전부 never · 한 이름으로
type Show<T> = { [K in keyof T]: T[K] } & {};
interface User {
    id: number;
    name: string;
    password: string;
    save(): void;
}
type Without<T, X> = { [K in keyof T as Exclude<K, X>]: T[K] };
type Getters<T> = { [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] };
type ByValue<T> = { [K in keyof T as T[K] extends Function ? never : K]: T[K] };
type AsNever<T> = { [K in keyof T as never]: T[K] };
type AsSame<T> = { [K in keyof T as "same"]: T[K] };

const r1: null = null as unknown as Show<Without<User, "password">>;
const r2: null = null as unknown as Show<Getters<Pick<User, "id" | "name">>>;
const r3: null = null as unknown as Show<ByValue<User>>;
const r4: null = null as unknown as Show<AsNever<User>>;
const r5: null = null as unknown as Show<AsSame<Pick<User, "id" | "name">>>;
console.log(r1, r2, r3, r4, r5);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26c.ts (tsc exit=1) =====
ex.26c.ts(15,7): error TS2322: Type '{ id: number; name: string; save: () => void; }' is not assignable to type 'null'.
ex.26c.ts(16,7): error TS2322: Type '{ getId: () => number; getName: () => string; }' is not assignable to type 'null'.
ex.26c.ts(17,7): error TS2322: Type '{ id: number; name: string; password: string; }' is not assignable to type 'null'.
ex.26c.ts(18,7): error TS2322: Type '{}' is not assignable to type 'null'.
ex.26c.ts(19,7): error TS2322: Type '{ same: string | number; }' is not assignable to type 'null'.
```

**왜 그런가**

- ★★★ 15행 — `as Exclude<K, "password">` 가 `"password"` 를 **`never`** 로 보내고, **키가 `never` 면 그 줄이 사라진다.**
  `Exclude` 가 분배 조건부라는 것은 [**24번 주제**](../24-conditional-types-and-distribution/)가 직접 다시 만들어 확인했다.
- ★★ 16행 — `getId`·`getName` 으로 **이름이 바뀌었다.** `string & K` 는 `K` 가 `symbol` 일 수 있어 끼운 것이다.
- ★★ 17행 — **값 모양으로** 거른다. `save(): void` 가 `Function` 에 들어 `never` → 사라졌다.
- ★ 18행 — 전부 `never` 면 **`{}`**.
- ★★★ 19행 — **진단이 없다.** `id`·`name` 이 둘 다 `"same"` 으로 가서 **한 줄로 합쳐지고 값은 `string | number`** 가 됐다.
  덮어쓰기도 에러도 아니고 **유니온**이다.

### 6. ★★ `?` 는 **`| undefined` 를 데리고 다닌다** — 그 표시가 `strictNullChecks` 에 달렸다

- ★★ `?` 가 붙은 속성을 탐침하면 값 타입에 **`| undefined` 가 함께** 찍힌다(1번 13행 `id?: number | undefined`).
  2번 격자에서 `+?` 는 그것을 **같이 붙이고**, `-?` 는 **같이 뗐다**(`keep -` 줄의 `c: number`).
- ★★★ `--strict` 를 끄면 그 **`| undefined` 가 표시에서 사라진다** — 요약 7절의 `diff` 블록이 근거다.
  `strictNullChecks` 가 꺼지면 `undefined` 를 **따로 적지 않기** 때문이다. **`?` 자체와 `readonly` 는 그대로다.**
- ★ 그래서 이 주제의 `--strict` 대조는 **네 파일 중 셋이 갈렸고**, 갈리지 않은 26c 에는 `?` 속성이 **하나도 없다.**

### 7. ★★ 5창은 **부적용** — 잴 것이 없다

- 방출기는 **계산하지 않는다.** `{ [K in keyof User]?: User[K]; }` 를 `{ id?: number; name?: string; }` 로 펼쳐 적지 않고 **적은 그대로** 남긴다.
- ★★ 그러므로 「`.d.ts` 로 재 봤더니 같았다」가 아니라 「**잴 것이 없다**」다(제4의 상태). 값을 읽는 창은 **탐침**뿐이다.
- ★ 같은 블록에 `Uppercase<"ab">`·`` `${"a" | "b"}-${"x" | "y"}` ``·`Omit<User, "id">` 도 **안 풀린 채** 있다 — 27·28 도 같은 이유로 5창이 부적용이다.

### 8. ★★★ `in` 뒤에 **`keyof T` 가 글자 그대로** 있어야 한다 — `Pick` 은 제약이 그것을 대신 말한다

- ★★★ 3번 18·19행 — 키 목록이 같아도 **`keyof Src` 라고 적은 쪽만** 수정자가 따라왔다.
- ★★ `Pick<T, K extends keyof T>` 의 `[P in K]` 는 `K` 가 **「`T` 의 키」라고 제약돼 있어서** 동형으로 친다(3번 16행이 같은 꼴).
  그래서 `Pick<User, "name">` 은 `readonly name` 을 **지킨다** — [**28번 주제**](../28-utility-types/)의 직접 다시 만들기 격자가 그것을 확인한다.
- ★ 거꾸로 **리터럴 키 목록**(`"a" | "b" | "c"`)이나 **별칭으로 빼 둔 키**는 동형이 아니다.

### 9. ★★ 수정자는 **지키고**, 배열 특례는 **깬다**

- ★★ 3번 17행 — `[K in keyof T as K]` 는 `readonly b`·`c?` 를 **지켰다.**
- ★★★ 4번 11행 — 같은 `as K` 가 튜플을 **객체로 펼쳤다.** `length` 까지 `{ v: 2; }` 로 감쌌다.
- ★★ 그래서 튜플의 칸을 `as` 로 거르려 하면 **튜플을 통째로 잃는다** — 배열 메서드까지 감싼 **평범한 객체**가 된다.
  칸을 거르려면 매핑 대신 **재귀 조건부로 다시 쌓는** 쪽이 흔하다([**25번 주제**](../25-infer-and-recursive-conditional-types/)). **이 문서에서는 안 던졌다.**

### 10. ★★★ 넷 다 **매핑 한 줄**이다 — 그리고 실마리는 **3번 16행과 19행 사이**에 있다

```text
  Partial<T>   = { [P in keyof T]?: T[P] }             2번 격자의 keep + 줄
  Readonly<T>  = { readonly [P in keyof T]: T[P] }     2번 격자의 + keep 줄
  Pick<T, K>   = { [P in K]: T[P] }   (K extends keyof T)   3번 16행의 꼴
  Record<K, V> = { [P in K]: V }                        3번 15행의 꼴 — 동형이 아니다
```

- ★★ 위 네 줄은 **tsc 가 싣고 다니는 `lib.es5.d.ts` 의 정의와 같은 꼴**이다 — [**28번 주제**](../28-utility-types/)가 그 파일을 직접 `grep` 해서 싣는다.
- ★★★ `Partial<Cat | Dog>` 는 `[P in keyof T]` 라 **유니온의 멤버마다 따로** 돈다(동형 매핑은 유니온에 분배된다).
  `Omit` 은 `Pick<T, Exclude<keyof T, K>>` 라 **`keyof (Cat | Dog)` 를 먼저 계산**한다 — 그것이 **교집합**이다([**22번 주제**](../22-keyof-and-indexed-access-types/) 1절).
  ★ 즉 실마리는 3번의 「**`keyof T` 를 직접 보느냐, 계산이 끝난 키 목록을 받느냐**」다. 붕괴 자체의 실측은 28 이 한다.

### 11. ★ 세 층

| 층 | 이 주제의 예 |
|---|---|
| **언어 보장** | `+`/`-` 수정자(2.8) · 동형 매핑의 수정자 보존 · 배열·튜플 특례(3.1) · `as` 가 `never` 면 키가 사라진다(4.1) |
| **★★★ 구현(tsc 7.0.2) 층** | ★★★ **1번 — 탐침이 별칭으로 답하고 `& {}` 가 안 듣는 것.** 표시의 문제다 |
| **이 판의 관찰** | 별칭을 거친 `keyof` 는 동형이 아니다(3번 19행) · `as K` 가 배열 특례를 깬다(4번 11행) · 이름 충돌이 유니온이 된다(5번 19행) · 유니온 표시 순서 |
| **설정에 달렸다** | `--strict` 를 끄면 `\| undefined` 표시가 사라진다(6번) |

- ★★★ 1번의 「조수가 바뀐 일」은 **구현 층**이다. 판이 오르면 `& {}` 가 다시 들을 수도 있다 — **다시 던져라.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| 탐침과 조수 | `--noEmit ex.26a.ts` | exit 1 · **6건** · ★ `& {}` 만으로는 **메아리**(11행) |
| ★★ 수정자 격자 | `bash ts26b-modgrid.sh` (아홉 벌 = **9회 컴파일**) | exit 0 · **갈린 칸 20 / 36** |
| ★★★ 동형 조건 | `--noEmit ex.26b.ts` | exit 1 · **6건** · ★ 18·19행이 **키가 같은데 갈린다** |
| `as` 리매핑 | `--noEmit ex.26c.ts` | exit 1 · **5건** · 19행 충돌이 **유니온** |
| 배열 특례 | `--noEmit ex.26d.ts` | exit 1 · **7건** · ★ 10행 `2` 대 11·12행 `{ v: 2; }` |
| 5창 부적용 | `--declaration --emitDeclarationOnly ex.26f.ts` | exit 0 · 매핑·템플릿·`Omit` 이 **적은 그대로** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★★ **셋이 갈렸다** — `\| undefined` 표시 |
| 반복 실행 | 같은 명령 **5회** | md5 **가짓수 1** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **탐침이 별칭으로 답하는 것과 `& {}` 가 안 듣는 것**(1번) — 표시 방식이다. **조수의 모양은 판마다 다시 확인하라.**
- ★★ **별칭을 거친 `keyof` 가 동형이 아닌 것**(3번 19행)·**`as K` 가 배열 특례를 깨는 것**(4번 11행) — 출력에서 읽은 것이다.
- ★ 유니온 원소의 **표시 순서** — 5회 동일했지만 **관찰이지 보장이 아니다.**
- ★ 진단 **문구** 전문 — 이 주제는 진단이 전부 `TS2322` 탐침이다.

**안 돌려 본 것**

- ★★★ **검사 시간·메모리** — **재지 않았고 수치를 한 줄도 적지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/)의 몫이다.
- ★★ **깊은 `Readonly`(재귀 매핑)** — 형태만 적었다. **안 던졌다.**
- ★★ **`as` 없이 튜플 칸만 거르는 법** — 재귀 조건부로 다시 쌓는 수. **안 던졌다.**
- ★ **`symbol` 키가 섞인 매핑** — `string & K` 로 걸렀을 뿐 `symbol` 키를 직접 넣어 보지 않았다.
