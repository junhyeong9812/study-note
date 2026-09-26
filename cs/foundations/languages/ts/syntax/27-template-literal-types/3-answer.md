# ts/syntax/27 — 템플릿 리터럴 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자는 `tsc` **7.0.2** · `node` **v18.19.1** 에서, 판 대조는 이 머신에 이미 있던 `tsc` **5.9.3** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★ 3·4번은 탐침이 **글자를 직접 찍지 않게** `Same<A, B>` 로 바꿔 물었다 — 이모지 글자를 문서에 싣지 않기 위해서다(제5의 상태).\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 4행은 **네 개**, 7행은 **패턴으로 남는다** — 진단은 **11·13행**

**출력**

```ts
// ex.27a.ts
// 템플릿 리터럴 타입 -- 유니온을 끼우면 · 넓은 타입을 끼우면
type Side = "top" | "bottom";
type Edge = "left" | "right";
const t1: null = null as unknown as `${Side}-${Edge}`;
const t2: null = null as unknown as `${Side | Edge}!`;
const t3: null = null as unknown as `id-${1 | 2 | true | null}`;
const t4: null = null as unknown as `${string}-${Side}`;

type NumId = `id-${number}`;
const n1: NumId = "id-42";
const n2: NumId = "id-abc";
let loose: string = "id-7";
const n3: NumId = loose;
console.log(t1, t2, t3, t4, n1, n2, n3);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.27a.ts (tsc exit=1) =====
ex.27a.ts(4,7): error TS2322: Type '"bottom-left" | "bottom-right" | "top-left" | "top-right"' is not assignable to type 'null'.
  Type '"bottom-left"' is not assignable to type 'null'.
ex.27a.ts(5,7): error TS2322: Type '"bottom!" | "left!" | "right!" | "top!"' is not assignable to type 'null'.
  Type '"bottom!"' is not assignable to type 'null'.
ex.27a.ts(6,7): error TS2322: Type '"id-1" | "id-2" | "id-null" | "id-true"' is not assignable to type 'null'.
  Type '"id-1"' is not assignable to type 'null'.
ex.27a.ts(7,7): error TS2322: Type '`${string}-bottom` | `${string}-top`' is not assignable to type 'null'.
  Type '`${string}-bottom`' is not assignable to type 'null'.
ex.27a.ts(11,7): error TS2322: Type '"id-abc"' is not assignable to type '`id-${number}`'.
ex.27a.ts(13,7): error TS2322: Type 'string' is not assignable to type '`id-${number}`'.
```

**왜 그런가**

| 줄 | 물은 꼴 | 답 |
|---|---|---|
| 4 | `` `${Side}-${Edge}` `` | **`"bottom-left" \| "bottom-right" \| "top-left" \| "top-right"`** — 2 × 2 |
| 5 | `` `${Side \| Edge}!` `` | 네 개 — 빈칸 **하나**라 곱이 아니다 |
| 6 | `` `id-${1 \| 2 \| true \| null}` `` | `"id-1" \| "id-2" \| "id-null" \| "id-true"` — 리터럴이 **글자로** 바뀐다 |
| 7 | ★★ `` `${string}-${Side}` `` | **`` `${string}-bottom` \| `${string}-top` ``** — `string` 쪽은 펼치지 않는다 |
| 10 | `"id-42"` | 진단 없음 |
| 11 | `"id-abc"` | **`TS2322`** |
| 13 | ★★ `string` 변수 `loose` | **`TS2322`** — 값이 `"id-7"` 이어도 **타입이 `string`** 이다 |

- ★★ 빈칸이 **유한하면 곱으로 펼치고**(4행), **무한하면 패턴·검사기**로 남는다(7·10·11행).
- ★ 6행은 `--strict` 에 달렸다 — 8번.

### 2. ★★ `"Hello world"` · 두 글자는 **두 글자씩으로 늘고**(`"SS"`·`"FI"`) · 막히는 쪽은 **13행**

**출력**

```ts
// ex.27b.ts
// 내장 문자열 조작 -- Uppercase · Lowercase · Capitalize · Uncapitalize
const c1: null = null as unknown as Uppercase<"hello">;
const c2: null = null as unknown as Capitalize<"hello world">;
const c3: null = null as unknown as Uncapitalize<"URL">;
const c4: null = null as unknown as Lowercase<"MiXeD">;
const c5: null = null as unknown as Capitalize<"get" | "set">;
const c6: null = null as unknown as Uppercase<"\u00DF">;
const c7: null = null as unknown as Uppercase<"\uFB01">;
const c8: null = null as unknown as Capitalize<"가나">;
const c9: null = null as unknown as Uppercase<string>;

let shout: Uppercase<string> = "ABC";
shout = "abc";
console.log(c1, c2, c3, c4, c5, c6, c7, c8, c9, shout);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.27b.ts (tsc exit=1) =====
ex.27b.ts(2,7): error TS2322: Type '"HELLO"' is not assignable to type 'null'.
ex.27b.ts(3,7): error TS2322: Type '"Hello world"' is not assignable to type 'null'.
ex.27b.ts(4,7): error TS2322: Type '"uRL"' is not assignable to type 'null'.
ex.27b.ts(5,7): error TS2322: Type '"mixed"' is not assignable to type 'null'.
ex.27b.ts(6,7): error TS2322: Type '"Get" | "Set"' is not assignable to type 'null'.
  Type '"Get"' is not assignable to type 'null'.
ex.27b.ts(7,7): error TS2322: Type '"SS"' is not assignable to type 'null'.
ex.27b.ts(8,7): error TS2322: Type '"FI"' is not assignable to type 'null'.
ex.27b.ts(9,7): error TS2322: Type '"가나"' is not assignable to type 'null'.
ex.27b.ts(10,7): error TS2322: Type 'Uppercase<string>' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.27b.ts(13,1): error TS2322: Type 'string' is not assignable to type 'Uppercase<string>'.
```

**왜 그런가**

- ★★ 3행 — **`"Hello world"`**. `Capitalize` 는 **첫 글자 하나만** 바꾼다. 단어마다가 아니다.
- ★★★ 7·8행 — **`"SS"`·`"FI"`**. 한 글자가 **두 글자**가 됐다. 대소문자 변환은 「글자마다 한 글자」가 아니다.
- ★ 9행 — 한글은 대소문자가 없어 **그대로**.
- ★★ 10행 — `Uppercase<string>` 은 펼칠 것이 없으니 **그 이름 그대로** 남는다.
  12행 `"ABC"` 는 통과, **13행 `"abc"` 는 `TS2322`** — 「대문자로만 된 문자열」이라는 **검사기**다.

### 3. ★★★ `3 · 3 · 1 · 2` 그리고 `"same" · "different" · "same"`

**출력**

```ts
// ex.27c.ts
// infer 로 문자열 쪼개기 -- 한 글자는 무엇인가
type Head<S extends string> = S extends `${infer C}${string}` ? C : never;
type Tail<S extends string> = S extends `${string}${infer R}` ? R : never;
type Len<S extends string, A extends unknown[] = []> =
    S extends `${string}${infer R}` ? Len<R, [...A, 1]> : A["length"];
type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? "same" : "different") : "different";

const n1: null = null as unknown as Len<"abc">;
const n2: null = null as unknown as Len<"가나다">;
const n3: null = null as unknown as Len<"\u{1F600}">;
const n4: null = null as unknown as Len<"e\u0301">;
const h1: null = null as unknown as Same<Head<"\u{1F600}x">, "\u{1F600}">;
const h2: null = null as unknown as Same<Head<"\u{1F600}x">, "\uD83D">;
const h3: null = null as unknown as Same<Tail<"\u{1F600}x">, "x">;
console.log(n1, n2, n3, n4, h1, h2, h3);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.27c.ts (tsc exit=1) =====
ex.27c.ts(8,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(10,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.27c.ts(11,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(12,7): error TS2322: Type '"same"' is not assignable to type 'null'.
ex.27c.ts(13,7): error TS2322: Type '"different"' is not assignable to type 'null'.
ex.27c.ts(14,7): error TS2322: Type '"same"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 물은 것 | 7.0.2 의 답 |
|---|---|---|
| 8 | `Len<"abc">` | `3` |
| 9 | `Len<"가나다">` | `3` — BMP 글자라 어느 단위로도 같다 |
| 10 | ★★★ `Len<U+1F600>` | **`1`** — JS `.length` 는 `2` 인데 |
| 11 | ★★★ `Len<e + U+0301>` | **`2`** — 눈에는 한 글자인데 |
| 12 | 머리가 온전한 U+1F600 인가 | **`"same"`** |
| 13 | 머리가 앞쪽 반쪽 U+D83D 인가 | **`"different"`** |
| 14 | 꼬리가 `"x"` 인가 | **`"same"`** |

- ★★★ 10·12·13·14행이 한목소리로 말한다 — **7.0.2 의 `infer` 는 서로게이트 쌍을 안 가른다.** 「한 글자」가 **코드 포인트**다.
- ★★★ 11행은 **반대편 경계**다 — 코드 포인트로는 둘이라 `2`. 7.0 이 맞춘 것은 **그래핌이 아니다.**
- ★ 이 문항을 탐침으로 **글자를 직접** 물으면 이모지 글자가 찍혀 나온다 — 그래서 `Same` 으로 바꿔 물었다(제5의 상태).

### 4. ★★★ **10·12·13·14행**이 바뀐다 — 종료 코드도 **1 대 2**

**출력**

```bash
# ts26b-cmp59.sh
#!/usr/bin/env bash
# 같은 파일을 두 판의 tsc 로 던진다 -- 7.0.2 와, 이 머신의 다른 프로젝트에 깔려 있던 5.9.3
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
echo "== tsc $(tsc --version)"
tsc --pretty false --noEmit -t es2022 --strict ex.27c.ts
echo "(exit $?)"
echo "== node OLD $(node "$OLD" --version)"
node "$OLD" --pretty false --noEmit -t es2022 --strict ex.27c.ts
echo "(exit $?)"
```

```text
===== bash ts26b-cmp59.sh (sh exit=0) =====
== tsc Version 7.0.2
ex.27c.ts(8,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(10,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.27c.ts(11,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(12,7): error TS2322: Type '"same"' is not assignable to type 'null'.
ex.27c.ts(13,7): error TS2322: Type '"different"' is not assignable to type 'null'.
ex.27c.ts(14,7): error TS2322: Type '"same"' is not assignable to type 'null'.
(exit 1)
== node OLD Version 5.9.3
ex.27c.ts(8,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.27c.ts(10,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(11,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.27c.ts(12,7): error TS2322: Type '"different"' is not assignable to type 'null'.
ex.27c.ts(13,7): error TS2322: Type '"same"' is not assignable to type 'null'.
ex.27c.ts(14,7): error TS2322: Type '"different"' is not assignable to type 'null'.
(exit 2)
```

**왜 그런가**

| 줄 | 7.0.2 | 5.9.3 |
|---|---|---|
| 8 · 9 · 11 | `3` · `3` · `2` | **같다** |
| 10 | `1` | ★★★ **`2`** |
| 12 | `"same"` | ★★★ **`"different"`** |
| 13 | `"different"` | ★★★ **`"same"`** — 머리가 **앞쪽 반쪽**이었다 |
| 14 | `"same"` | ★★ **`"different"`** — 꼬리에 **뒤쪽 반쪽**이 남았다 |

- ★★★ 갈린 네 줄이 **전부 서로게이트 쌍이 걸린 줄**이다. 결합 문자(11행)는 두 판이 같다.
- ★★ 이것이 [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) 의
  「Template Literal Types Now Preserve Unicode Code Points」 절이 말한 변경이다 — **이 판에서 실제로 그렇게 돈다.**
- ★★ 종료 코드가 **7.0.2 는 `1`, 5.9.3 은 `2`**. 같은 「진단 있음」인데 값이 다르다. **`0` 이냐 아니냐**로만 읽어라.

### 5. ★★ 막히는 줄은 **10×5 · 2×17 · 47×3 · 317×2** — 축은 **곱**이다

**출력**

```bash
# ts26b-union.sh
#!/usr/bin/env bash
# 템플릿 리터럴이 유니온을 곱할 때 -- 원소 수 x 자리 수를 바꿔 가며 TS2590 을 받는다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
blocked=0; total=0
printf '%-6s %-6s %-8s %s\n' 원소 자리 곱 결과
for pair in 10:4 10:5 2:16 2:17 46:3 47:3 316:2 317:2; do
  b=${pair%:*}; n=${pair#*:}
  u=$(for ((i=0;i<b;i++)); do printf '"k%d"' "$i"; ((i<b-1)) && printf ' | '; done)
  t='`'; for ((i=0;i<n;i++)); do t="$t\${U}"; done; t="$t\`"
  { echo "type U = $u;"; echo "type P = $t;"; echo 'declare const p: P;'; echo 'export { p };'; } > "$D/p.ts"
  out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/p.ts" 2>&1); rc=$?
  case "$out" in *TS2590*) mark="TS2590 exit=$rc"; blocked=$((blocked+1));; '') mark="OK     exit=$rc";; *) mark="OTHER  exit=$rc";; esac
  total=$((total+1))
  printf '%-6s %-6s %-8s %s\n' "$b" "$n" "$((b**n))" "$mark"
done
echo "막힌 칸 $blocked / $total"
```

```text
===== bash ts26b-union.sh (sh exit=0) =====
원소 자리 곱      결과
10     4      10000    OK     exit=0
10     5      100000   TS2590 exit=1
2      16     65536    OK     exit=0
2      17     131072   TS2590 exit=1
46     3      97336    OK     exit=0
47     3      103823   TS2590 exit=1
316    2      99856    OK     exit=0
317    2      100489   TS2590 exit=1
막힌 칸 4 / 8
```

**왜 그런가**

- ★★★ **원소 10 개 × 5 자리가 먼저 막힌다.** 원소 2 개 × 16 자리는 **통과**한다 — 자리 수는 훨씬 많은데도.
- ★★★ 통과·막힘을 가르는 것은 넷째 칸 **곱**이다. 네 쌍이 전부 **곱이 선을 넘는 자리**에서 한 줄씩 갈렸다.
- ★★ 마지막 줄 **막힌 칸 4 / 8**.
- ★★ 정확한 선은 **블록 안에만** 둔다 — 그 수는 **구현(tsc 7.0.2) 층**이다(10번).

### 6. ★★ 넷 중 **`""` 만 막힌다** — 그리고 그 칸이 **`Number()` 와 갈리는 유일한 칸**이다

**출력**

```bash
# ts26b-numstr.sh
#!/usr/bin/env bash
# `${number}` 에 드는 문자열 -- tsc 의 멤버십 대입과 JS 의 Number() 를 나란히 둔다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
samples=('42' '1e3' '0x1F' '0b11' '.5' '-0' ' 7' '7 ' ' ' '' 'abc' 'Infinity' 'NaN' '1_000')
{ echo 'type N = `${number}`;'
  i=0; for s in "${samples[@]}"; do printf 'export const v%d: N = "%s";\n' "$i" "$s"; i=$((i+1)); done; } > "$D/n.ts"
out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/n.ts" 2>&1)
split=0; total=0; i=0
printf '%-12s %-8s %s\n' '문자열' 'tsc' 'Number.isFinite(Number(s))'
for s in "${samples[@]}"; do
  line=$((i+2))
  case "$out" in *"n.ts($line,"*) t=TS2322;; *) t=OK;; esac
  j=$(node -e 'console.log(Number.isFinite(Number(process.argv[1])))' -- "$s")
  if [ "$t" = OK ]; then tv=true; else tv=false; fi
  total=$((total+1)); if [ "$tv" != "$j" ]; then split=$((split+1)); fi
  printf '%-12s %-8s %s\n' "\"$s\"" "$t" "$j"
  i=$((i+1))
done
echo "tsc 와 Number() 가 갈린 칸 $split / $total"
```

```text
===== bash ts26b-numstr.sh (sh exit=0) =====
문자열    tsc      Number.isFinite(Number(s))
"42"         OK       true
"1e3"        OK       true
"0x1F"       OK       true
"0b11"       OK       true
".5"         OK       true
"-0"         OK       true
" 7"         OK       true
"7 "         OK       true
" "          OK       true
""           TS2322   true
"abc"        TS2322   false
"Infinity"   TS2322   false
"NaN"        TS2322   false
"1_000"      TS2322   false
tsc 와 Number() 가 갈린 칸 1 / 14
```

**왜 그런가**

- ★★★ `" 7"`·`" "`·`"0x1F"` 는 **통과**한다. `Number(" ")` 는 `0` 이다 — **공백만 있어도** 숫자로 읽힌다.
- ★★★ **`""` 는 막힌다.** 그런데 `Number("")` 도 `0` 이라 JS 쪽은 `true` — **갈린 칸 1 / 14** 의 그 한 칸이다.
- ★★ 그래서 이 판의 관찰로는 「**비어 있지 않고, `Number()` 가 유한한 수를 내는 문자열**」이 든다.
  ★ **열네 칸에서 읽은 규칙**이지 명세 문장이 아니다.

### 7. ★★ 빈칸마다 **분배**되기 때문이다 — `string` 은 **펼칠 목록이 없다**

- ★★ 빈칸 하나하나에 유니온이 **멤버마다 따로** 들어가고, 두 빈칸의 조합이 **전부** 만들어진다 — 2 × 2 = 4(1번 4행).
  [**24번 주제**](../24-conditional-types-and-distribution/)의 **분배**(유니온이 멤버마다 조건부를 따로 탄다)와 같은 집안이다.
- ★★ `string`·`number` 는 **멤버를 나열할 수 없는** 타입이다. 그래서 펼치지 않고 **패턴**으로 남긴다(1번 7행).
  그 패턴은 값이 들어올 때 **모양을 검사하는** 쪽으로 쓰인다(1번 10·11행).

### 8. ★★ **`"id-null"` 이 사라진다** — `null` 이 따로 서는 타입이 아니게 되어 흡수된다

```text
===== diff <(tsc --pretty false --noEmit -t es2022 --strict ex.27a.ts) <(tsc --pretty false --noEmit -t es2022 --strict false ex.27a.ts) (sh exit=1) =====
5c5
< ex.27a.ts(6,7): error TS2322: Type '"id-1" | "id-2" | "id-null" | "id-true"' is not assignable to type 'null'.
---
> ex.27a.ts(6,7): error TS2322: Type '"id-1" | "id-2" | "id-true"' is not assignable to type 'null'.
```

- ★★ `strictNullChecks`(= `--strict` 에 딸린 설정)가 꺼지면 `null` 은 **모든 타입에 이미 들어 있는 값**처럼 취급된다.
  그래서 유니온 `1 | 2 | true | null` 에서 `null` 이 **따로 적히지 않고**, 끼워 넣을 글자 `"null"` 이 없어진다.
- ★ 이 해석은 **`diff` 한 줄에서 읽은 것**이다. 명세 문장으로 확인하지 않았다.

### 9. ★★★ **코드 포인트**다 — 그래핌이 아니라서 **결합 문자에서 어긋난다**

- ★★★ 7.0 의 `infer` 는 **코드 포인트** 단위다 — JS 의 `for...of`·스프레드와 같은 단위(3번 10행 · 11번의 `spread`).
- ★★ 코드 유닛(`.length`)이 아니다 — 이모지 하나가 `1` 이다.
- ★★★ 그래핌도 아니다 — `e` + U+0301 은 **눈에는 한 글자**인데 `2` 다(3번 11행). 국기·가족 이모지처럼 **여러 코드 포인트를 잇는 글자**도 같은 이유로 여럿으로 센다.
  ★ 국기·가족 이모지는 **안 던졌다** — 결합 악센트 한 칸이 근거다.

### 10. ★★ 경계는 **구현 층**이다 — 그리고 `TS2590` 은 **거부**이지 속도가 아니다

- ★★★ 5번의 선은 **명세가 정한 수가 아니다.** tsc 7.0.2 의 한계이고, **판이 오르면 다시 재야** 한다.
  그래서 본문은 수를 외우라고 하지 않고 **「축은 곱이다」라는 성질**만 주장한다.
- ★★★ **「느리다」는 뜻이 아니다.** `TS2590` 의 문구는 「**표현하기에 너무 복잡하다**」이고, 이 문서는 **시간을 재지 않았다.**
  「템플릿 리터럴 타입이 컴파일을 느리게 한다」는 말은 **근거가 없어 적지 않는다.** [목록의 **45번 주제**](../45-type-level-performance/)의 몫이다.

### 11. ★★ **`spread`** 가 7.0 과 같다 — 대소문자 두 글자도 **같은 답**이었다

**출력**

```js
// cp27.mjs
// 같은 글자를 JS 는 몇 개로 세나
const samples = [["smile", "\u{1F600}"], ["accent", "e\u0301"], ["hangul", "가나다"]];
const seg = new Intl.Segmenter("en", { granularity: "grapheme" });
for (const [name, s] of samples) {
    const graphemes = [...seg.segment(s)].length;
    console.log(name, "length", s.length, "spread", [...s].length, "graphemes", graphemes);
}
```

```text
===== node cp27.mjs (node exit=0) =====
smile length 2 spread 1 graphemes 1
accent length 2 spread 2 graphemes 1
hangul length 3 spread 3 graphemes 3
```

```js
// case27.mjs
// 같은 글자를 JS 의 toUpperCase 에 넣으면
for (const s of ["hello", "\u00DF", "\uFB01"]) {
    const up = s.toUpperCase();
    console.log(JSON.stringify(up), "length", s.length, "->", up.length);
}
```

```text
===== node case27.mjs (node exit=0) =====
"HELLO" length 5 -> 5
"SS" length 1 -> 2
"FI" length 1 -> 2
```

**왜 그런가**

- ★★★ `smile length 2 spread 1` — 7.0 의 `Len` 은 **`spread`(코드 포인트)** 와 같고 `length`(코드 유닛)와 다르다.
- ★★ `accent … graphemes 1` — **그래핌**은 `Intl.Segmenter` 만 센다. 타입 쪽에는 그 단위가 없다.
- ★★ 대소문자 — JS 도 `"SS" length 1 -> 2`·`"FI" length 1 -> 2`. **2번 7·8행과 같은 글자**다.
- ★ 경계 선언 — **값을 만드는** 템플릿 리터럴과 `toUpperCase` 의 정본은
  `` JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **28번**([`String` 메서드와 템플릿 리터럴](../../../js/syntax/28-string-methods-and-template-literals/)) `` 이고,
  세 단위의 정본은 **04번**([문자열과 UTF-16](../../../js/syntax/04-strings-and-utf16/))이다.

### 12. ★ 세 층

| 층 | 이 주제의 예 |
|---|---|
| **언어 보장(4.1)** | 템플릿 리터럴 타입 · 빈칸의 분배 · 내장 네 조작 |
| **★★★ 언어 판의 변경(7.0)** | `infer` 가 **코드 포인트** 단위 — 릴리스 노트 + 4번 실측 |
| **★★★ 구현(tsc 7.0.2) 층** | **`TS2590` 의 경계 크기**(5번) |
| **이 판의 관찰** | 결합 문자는 여럿(3번 11행) · `Uppercase` 가 JS 와 같은 글자(2번) · `${number}` 의 문턱(6번) · 표시 순서 |
| **판에 달렸다** | 진단 있음의 **종료 코드 값**(4번) |
| **설정에 달렸다** | `null` 원소가 흡수된다(8번) |

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| 곱과 검사기 | `--noEmit ex.27a.ts` | exit 1 · **6건** · 4행 네 개 · 7행 패턴 |
| 내장 조작 | `--noEmit ex.27b.ts` | exit 1 · **10건** · ★ 7·8행 `"SS"`·`"FI"` |
| JS 대소문자 | `node case27.mjs` | exit 0 · **같은 글자** |
| ★★★ 한 글자 | `--noEmit ex.27c.ts` | exit 1 · **7건** · 10행 `1` · 11행 `2` |
| JS 세 단위 | `node cp27.mjs` | exit 0 · `length`·`spread`·`graphemes` |
| ★★★ 판 대조 | `bash ts26b-cmp59.sh` (7.0.2 · 5.9.3) | exit 0 · ★ **네 줄이 갈렸다** · 종료 코드 `1` 대 `2` |
| ★★ `TS2590` 격자 | `bash ts26b-union.sh` (**8회 컴파일**) | exit 0 · **막힌 칸 4 / 8** |
| ★★ `${number}` 격자 | `bash ts26b-numstr.sh` (컴파일 1회 + `node` 14회) | exit 0 · **갈린 칸 1 / 14** |
| `strict` 대조 | 세 파일을 `--strict false` 로 재실행 | ★ **27a 하나**가 갈렸다 — `"id-null"` |
| 반복 실행 | 같은 명령 **5회** | md5 **가짓수 1** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`TS2590` 의 경계 크기**(5번) — 격자를 다시 돌려라.
- ★★★ **코드 포인트 단위**(3·4번) — 7.0 의 언어 판 변경이지만 **이 판에서 확인한 것**이다. 다음 판에서도 4번 스크립트로 다시 재라.
- ★★ **`${number}` 의 문턱**(6번) — 열네 칸의 관찰이다.
- ★★ **`Uppercase` 와 JS 의 일치**(2번) — 두 글자에서 본 것이다.
- ★ 진단 **종료 코드 값** — 판마다 다를 수 있다(4번).

**안 돌려 본 것**

- ★★★ **검사 시간·메모리** — **재지 않았고 수치를 한 줄도 적지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/)의 몫이다.
- ★★ **5.9.3 에서의 `TS2590` 경계** — 판 대조는 3번 파일 하나만 했다.
- ★★ **국기·가족 이모지·ZWJ 연쇄** — 결합 악센트 한 칸으로 「그래핌이 아니다」를 보였을 뿐이다.
- ★ **로케일에 따라 갈리는 대소문자**(터키어의 I 등) — 안 던졌다.
- ★ `` `${bigint}` ``·`` `${boolean}` `` 의 문턱 — `${number}` 만 격자로 쳤다.
