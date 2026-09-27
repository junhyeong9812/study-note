# ts/syntax/46 — 가변 튜플 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·타입 글자는 `tsc` **7.0.2** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5 · 3.9.3** 을 환경변수(`TSC_OLD`·`TSC_49`·`TSC_39`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체는 추론 격자다** — `TS2322 … is not assignable to type 'null'` 은 에러가 아니라 **출력**이다. 세지 말고 읽어라.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 튜플 **`11 / 15`** · 배열 **`4 / 15`** — 배열은 `f(...arr)` · `g([1, "a"])` · `c1([1], ["a"])` · `[...ro, "x"]`

**출력**

```bash
# ts46b-infer46.sh
#!/usr/bin/env bash
# 가변 튜플 추론 격자 -- 선언 × 호출 한 칸마다 파일 한 장(앞머리 두 줄 + 선언 + 탐침 한 줄) · 판 넷
# 탐침은 `const p: null = <호출>;` -- 추론된 타입을 TS2322 의 메시지에서 읽는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"; V49="${TSC_49:?4.9.5 판을 TSC_49 로 준다}"; V39="${TSC_39:?3.9.3 판을 TSC_39 로 준다}"
EXTRA=${EXTRA:-}   # 자기검사용 -- 비워 두면 아무것도 안 더한다
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\x1f'   # 구분자는 US(0x1f) -- 탭은 IFS 공백이라 빈 칸이 접힌다(규칙 32)
F='declare function f<T extends unknown[]>(...args: T): T;'
G='declare function g<T extends unknown[]>(arr: T): T;'
H='declare function h<T extends unknown[]>(arr: [...T]): T;'
C1='declare function c1<A extends unknown[], B extends unknown[]>(a: A, b: B): [...A, ...B];'
C2='declare function c2<A extends unknown[], B extends unknown[]>(a: [...A], b: [...B]): [...A, ...B];'
M='declare function m(...args: [string, ...number[], boolean]): void;'
P='declare function pe(...args: [name: string, age?: number]): void;'
rows=(
  "r01${T}$F${T}f(1, \"a\")"
  "r02${T}$F${T}f(...arr)"
  "r03${T}$F${T}f(...ro)"
  "r04${T}$F${T}f(...arr, \"x\")"
  "r05${T}$G${T}g([1, \"a\"])"
  "r06${T}$G${T}g([1, \"a\"] as const)"
  "r07${T}$H${T}h([1, \"a\"])"
  "r08${T}$H${T}h([...arr, \"x\"])"
  "r09${T}$C1${T}c1([1], [\"a\"])"
  "r10${T}$C2${T}c2([1], [\"a\"])"
  "r11${T}$C2${T}c2(arr, [\"a\"])"
  "r12${T}$M${T}null as unknown as Parameters<typeof m>"
  "r13${T}$P${T}null as unknown as Parameters<typeof pe>"
  "r14${T}${T}[...ro, \"x\"]"
  "r15${T}${T}[...ro, \"x\"] as const"
)
run() { case $1 in 7.0.2) tsc "${@:2}" ;; 5.9.3) node "$OLD" "${@:2}" ;; 4.9.5) node "$V49" "${@:2}" ;; 3.9.3) node "$V39" "${@:2}" ;; esac; }
tuple=0; arrayish=0; other=0; split=0; split3=0; i=0
for r in "${rows[@]}"; do
  n=$(awk -F'\x1f' '{print NF}' <<< "$r"); if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $r"; exit 3; fi
  IFS="$T" read -r id decl call <<< "$r"
  i=$((i+1)); d="$D/$id"; mkdir -p "$d" || exit 3
  { echo 'const arr = [1, 2];'; echo 'const ro = [1, 2] as const;'; [ -n "$decl" ] && echo "$decl"; echo "const p: null = $call;"; } > "$d/c.ts" || exit 3
  line=$(wc -l < "$d/c.ts")
  echo "[$id] ${decl:-(선언 없음)}"
  echo "      p = $call"
  declare -A got=()
  for v in 7.0.2 5.9.3 4.9.5 3.9.3; do
    raw=$(cd "$d" && run $v --pretty false --noEmit --strict -t es2020 $EXTRA c.ts 2>&1)
    if grep -qE '^error TS' <<< "$raw"; then echo "★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: $(grep -oE '^error TS[0-9]+' <<< "$raw" | sed 's/^error //' | sort -u | tr '\n' ' ')"; exit 4; fi
    ty=$(sed -n "s/^c\.ts($line,7): error TS2322: Type '\(.*\)' is not assignable to type 'null'\.\$/\1/p" <<< "$raw")
    rest=$(grep -o '^c\.ts([0-9]*,[0-9]*): error TS[0-9]*' <<< "$raw" | grep -v "^c\.ts($line,7): error TS2322" | sed 's/.*error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
    got[$v]="${ty:-(탐침 진단 없음)}${rest:+   + $rest}"
    printf '      %-6s %s\n' "$v" "${got[$v]}"
  done
  case ${got[7.0.2]} in "["*|"readonly ["*) tuple=$((tuple+1)); k=튜플 ;; *"[]") arrayish=$((arrayish+1)); k=배열 ;; *) other=$((other+1)); k=기타 ;; esac
  echo "      7.0.2 의 모양: $k"
  if [ "${got[7.0.2]}" != "${got[5.9.3]}" ] || [ "${got[7.0.2]}" != "${got[4.9.5]}" ] || [ "${got[7.0.2]}" != "${got[3.9.3]}" ]; then split=$((split+1)); fi
  if [ "${got[7.0.2]}" != "${got[5.9.3]}" ] || [ "${got[7.0.2]}" != "${got[4.9.5]}" ]; then split3=$((split3+1)); fi
  unset got
done
if [ $tuple -eq 0 ] || [ $arrayish -eq 0 ]; then echo "★ 한쪽 모양만 나왔다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "7.0.2 에서 튜플로 추론된 칸 $tuple / $i · 배열로 넓혀진 칸 $arrayish / $i · 기타 $other · 네 판이 한 글자도 같지 않은 칸 $split / $i · 그중 4.0 이후 세 판(4.9.5·5.9.3·7.0.2)끼리 갈린 칸 $split3 / $i"
```

```text
===== bash ts46b-infer46.sh (sh exit=0) =====
[r01] declare function f<T extends unknown[]>(...args: T): T;
      p = f(1, "a")
      7.0.2  [number, string]
      5.9.3  [number, string]
      4.9.5  [number, string]
      3.9.3  [number, string]
      7.0.2 의 모양: 튜플
[r02] declare function f<T extends unknown[]>(...args: T): T;
      p = f(...arr)
      7.0.2  number[]
      5.9.3  number[]
      4.9.5  number[]
      3.9.3  number[]
      7.0.2 의 모양: 배열
[r03] declare function f<T extends unknown[]>(...args: T): T;
      p = f(...ro)
      7.0.2  [1, 2]
      5.9.3  [1, 2]
      4.9.5  [1, 2]
      3.9.3  [1, 2]
      7.0.2 의 모양: 튜플
[r04] declare function f<T extends unknown[]>(...args: T): T;
      p = f(...arr, "x")
      7.0.2  [...number[], string]
      5.9.3  [...number[], string]
      4.9.5  [...number[], string]
      3.9.3  (string | number)[]
      7.0.2 의 모양: 튜플
[r05] declare function g<T extends unknown[]>(arr: T): T;
      p = g([1, "a"])
      7.0.2  (string | number)[]
      5.9.3  (string | number)[]
      4.9.5  (string | number)[]
      3.9.3  (string | number)[]
      7.0.2 의 모양: 배열
[r06] declare function g<T extends unknown[]>(arr: T): T;
      p = g([1, "a"] as const)
      7.0.2  [1, "a"]
      5.9.3  [1, "a"]
      4.9.5  unknown[]   + TS2345
      3.9.3  unknown[]   + TS2345
      7.0.2 의 모양: 튜플
[r07] declare function h<T extends unknown[]>(arr: [...T]): T;
      p = h([1, "a"])
      7.0.2  [number, string]
      5.9.3  [number, string]
      4.9.5  [number, string]
      3.9.3  unknown[]   + TS2574
      7.0.2 의 모양: 튜플
[r08] declare function h<T extends unknown[]>(arr: [...T]): T;
      p = h([...arr, "x"])
      7.0.2  [...number[], string]
      5.9.3  [...number[], string]
      4.9.5  [...number[], string]
      3.9.3  unknown[]   + TS2574
      7.0.2 의 모양: 튜플
[r09] declare function c1<A extends unknown[], B extends unknown[]>(a: A, b: B): [...A, ...B];
      p = c1([1], ["a"])
      7.0.2  (string | number)[]
      5.9.3  (string | number)[]
      4.9.5  (string | number)[]
      3.9.3  [any, ...any[]]   + TS1256
      7.0.2 의 모양: 배열
[r10] declare function c2<A extends unknown[], B extends unknown[]>(a: [...A], b: [...B]): [...A, ...B];
      p = c2([1], ["a"])
      7.0.2  [number, string]
      5.9.3  [number, string]
      4.9.5  [number, string]
      3.9.3  [any, ...any[]]   + TS1256 TS2574
      7.0.2 의 모양: 튜플
[r11] declare function c2<A extends unknown[], B extends unknown[]>(a: [...A], b: [...B]): [...A, ...B];
      p = c2(arr, ["a"])
      7.0.2  [...number[], string]
      5.9.3  [...number[], string]
      4.9.5  [...number[], string]
      3.9.3  [any, ...any[]]   + TS1256 TS2574
      7.0.2 의 모양: 튜플
[r12] declare function m(...args: [string, ...number[], boolean]): void;
      p = null as unknown as Parameters<typeof m>
      7.0.2  [string, ...number[], boolean]
      5.9.3  [string, ...number[], boolean]
      4.9.5  [string, ...number[], boolean]
      3.9.3  [string, number, boolean]   + TS1256
      7.0.2 의 모양: 튜플
[r13] declare function pe(...args: [name: string, age?: number]): void;
      p = null as unknown as Parameters<typeof pe>
      7.0.2  [name: string, age?: number | undefined]
      5.9.3  [name: string, age?: number | undefined]
      4.9.5  [name: string, age?: number | undefined]
      3.9.3  (탐침 진단 없음)   + TS1005
      7.0.2 의 모양: 튜플
[r14] (선언 없음)
      p = [...ro, "x"]
      7.0.2  (string | 1 | 2)[]
      5.9.3  (string | 2 | 1)[]
      4.9.5  (string | 2 | 1)[]
      3.9.3  (string | 2 | 1)[]
      7.0.2 의 모양: 배열
[r15] (선언 없음)
      p = [...ro, "x"] as const
      7.0.2  readonly [1, 2, "x"]
      5.9.3  readonly [1, 2, "x"]
      4.9.5  readonly [1, 2, "x"]
      3.9.3  readonly [1, 2, "x"]
      7.0.2 의 모양: 튜플

7.0.2 에서 튜플로 추론된 칸 11 / 15 · 배열로 넓혀진 칸 4 / 15 · 기타 0 · 네 판이 한 글자도 같지 않은 칸 10 / 15 · 그중 4.0 이후 세 판(4.9.5·5.9.3·7.0.2)끼리 갈린 칸 2 / 15
```

**왜 그런가**

- ★★★ 튜플로 잡히는 문은 셋 — **나머지 매개변수 자리**(`r01`·`r03`·`r04`) · **`[...T]` 로 적은 매개변수**(`r07`·`r08`·`r10`·`r11`) · **`as const` 값**(`r03`·`r06`·`r15`). `Parameters<…>` 는 선언된 튜플을 그대로 꺼낸다(`r12`·`r13`).
- ★★★ **`r02` 는 `number[]`** — 펼친 `arr` 가 이미 `number[]` 다.
- ★★ `r04`·`r08`·`r11` 의 `[...number[], string]` — 길이는 몰라도 **끝 칸은 안다.**

### 2. ★★ 4.0 이후 세 판끼리 갈린 칸 **`2 / 15`**(`r06` 4.9.5 `TS2345` · `r14` 유니온 표시 순서) · 3.9.3 까지 넣으면 **`10 / 15`** — 3.9.3 은 `TS2574`(`[...T]`) · `TS1256`(가운데 나머지) · `TS1005`(레이블)

**출력** — 1번과 같은 블록이다. 읽을 곳은 칸마다 판 네 줄과 마지막 줄.

**왜 그런가**

- ★★★ 3.9.3 은 **가변 튜플도 레이블도 가운데 나머지도 모른다** — 4.0 전후가 이 격자에서 보인다. 4.0·4.2 판 자체는 이 머신에 없어 **경계 양쪽만** 쟀다.
- ★ `r14` 는 `(string | 1 | 2)[]` 대 `(string | 2 | 1)[]` — **뜻은 같고 표시 순서만** 다르다.

### 3. ★★ 세 판 모두 `TS1257` · `TS1265` · `TS1266` — **4.9.5 만** `T4` 에 `TS5084` 를 더 낸다

**출력**

```ts
// vt46a.ts
// 튜플 꼴 넷 -- 선택 요소 · 나머지 요소 · 레이블의 자리
type T1 = [a?: string, b: number];
type T2 = [...string[], ...number[]];
type T3 = [...number[], string?];
type T4 = [a: string, number];
export {};
```

```text
===== tsc · "$TSC_OLD" · "$TSC_49" --pretty false --noEmit --strict -t es2022 vt46a.ts (sh exit=0) =====
---- 7.0.2
vt46a.ts(2,24): error TS1257: A required element cannot follow an optional element.
vt46a.ts(3,25): error TS1265: A rest element cannot follow another rest element.
vt46a.ts(4,25): error TS1266: An optional element cannot follow a rest element.
(exit 1)
---- 5.9.3
vt46a.ts(2,24): error TS1257: A required element cannot follow an optional element.
vt46a.ts(3,25): error TS1265: A rest element cannot follow another rest element.
vt46a.ts(4,25): error TS1266: An optional element cannot follow a rest element.
(exit 2)
---- 4.9.5
vt46a.ts(2,24): error TS1257: A required element cannot follow an optional element.
vt46a.ts(3,25): error TS1265: A rest element cannot follow another rest element.
vt46a.ts(4,25): error TS1266: An optional element cannot follow a rest element.
vt46a.ts(5,23): error TS5084: Tuple members must all have names or all not have names.
(exit 2)
```

**왜 그런가**

- ★★★ 레이블 섞기는 4.9.5 의 규칙이었다 — 5.9.3·7.0.2 는 받는다.
- ★ 종료 코드는 판에 매인다 — 7.0.2 `1` · 5.9.3·4.9.5 `2`.

### 4. ★★★ 세 판 모두 **진단 0줄 · `exit 0`**

**출력**

```text
===== tsc · "$TSC_OLD" · "$TSC_49" --pretty false --noEmit --strict -t es2022 vt46b.ts (sh exit=0) =====
---- 7.0.2
(exit 0)
---- 5.9.3
(exit 0)
---- 4.9.5
(exit 0)
```

**왜 그런가**

- ★★★ 레이블은 **모양이 아니다** — 이름이 달라도, 없어도 서로 대입된다. 표시용 이름이다(1번 `r13` 이 레이블째 찍힌다).

### 5. ★★★ `two(...arr)` **`TS2556`** · `m("a", 1)` **`TS2345`** — 나머지 넷은 통과 · 세 판의 표준 출력이 **한 글자도 같다**

**출력**

```ts
// vt46c.ts
// 고정 길이 나머지 매개변수와 가운데 나머지 요소에 넘기는 여섯 호출
declare function two(...a: [number, number]): void;
declare function m(...args: [string, ...number[], boolean]): void;
const arr = [1, 2];
const ro = [1, 2] as const;
two(...arr);
two(...ro);
m("a", true);
m("a", 1, 2, true);
m("a", 1);
m("a", ...arr, true);
export {};
```

```text
===== tsc --pretty false --noEmit --strict -t es2022 vt46c.ts ; 이어서 "$TSC_OLD"·"$TSC_49" 의 표준 출력을 cmp (sh exit=0) =====
vt46c.ts(6,5): error TS2556: A spread argument must either have a tuple type or be passed to a rest parameter.
vt46c.ts(10,8): error TS2345: Argument of type '[1]' is not assignable to parameter of type '[...number[], boolean]'.
  Type at position 0 in source is not compatible with type at position 1 in target.
    Type 'number' is not assignable to type 'boolean'.
(7.0.2 exit 1)
Version 5.9.3 의 출력: 한 글자도 같다 (exit 2)
Version 4.9.5 의 출력: 한 글자도 같다 (exit 2)
```

**왜 그런가**

- ★★★ `arr` 는 `number[]` 라 「두 개」인지 모른다 — 1번 `r02` 의 진단 쪽 얼굴이다. `as const` 인 `ro` 는 통과한다.
- ★★ 가운데 나머지는 **0개도** 받는다(`m("a", true)`) · 길이 모르는 배열도 가운데 칸에는 들어간다(`m("a", ...arr, true)`).

### 6. ★★ 방출물에 **타입 매개변수·반환 타입·`type Pair`·레이블이 전부 없다** — `node` 는 `["k",1,true] 3`

**출력**

```ts
// vt46d.ts
// 두 튜플을 잇는 함수 -- 방출물과 실행
function concat<A extends unknown[], B extends unknown[]>(a: [...A], b: [...B]): [...A, ...B] {
    return [...a, ...b];
}
type Pair = [label: string, n: number];
const pair: Pair = ["k", 1];
const r = concat(pair, [true]);
console.log(JSON.stringify(r), r.length);
```

```text
===== tsc --pretty false -t es2022 --outDir e46 vt46d.ts ; 방출물 ; node e46/vt46d.js (sh exit=0) =====
(tsc exit 0)
===== 방출된 e46/vt46d.js =====
"use strict";
// 두 튜플을 잇는 함수 -- 방출물과 실행
function concat(a, b) {
    return [...a, ...b];
}
const pair = ["k", 1];
const r = concat(pair, [true]);
console.log(JSON.stringify(r), r.length);
===== node =====
["k",1,true] 3
(node exit 0)
```

**왜 그런가**

- ★★ 남은 것은 JS 스프레드 `[...a, ...b]` 뿐이다 — [01번 주제](../01-what-ts-adds-and-erases/)의 「지우는 것」.
- ★ 타입이 말한 `[string, number, boolean]` 을 런타임은 확인하지 않는다.

### 7. ★★★ **펼친 값의 선언**이 갈랐다 — `const arr = [1, 2]` 는 선언에서 이미 `number[]`, `as const` 인 `ro` 는 `readonly [1, 2]`

- ★★ 호출 `f(...x)` 는 두 칸이 같다. `f` 는 **받은 타입의 칸 수를 그대로 본뜰** 뿐이라, 칸 수가 없는 `number[]` 에서는 `number[]` 가 나온다.

### 8. ★★★ 「이 자리의 배열 리터럴을 **튜플로** 추론해 달라」 — `r05` 는 `(string | number)[]`, `r07` 은 `[number, string]`

- ★★ 제약 `T extends unknown[]` 은 **상한**일 뿐 추론 방향을 정하지 않는다. `[...T]` 가 **칸 단위로 보라**는 신호다. 3.9.3 은 이 표기 자체를 못 읽어 `TS2574` 를 냈다.

### 9. ★★★ **매개변수 자리** — `c1(a: A, b: B)` 는 `(string | number)[]`, `c2(a: [...A], b: [...B])` 는 `[number, string]`

- ★★ 반환 타입 `[...A, ...B]` 는 **추론이 끝난 뒤 조립**할 뿐이다. `A` 가 배열로 잡히면 조립된 것도 배열이다.

### 10. ★★ **`TS5084` 는 `TS5` 로 시작하지만 파일에 붙은 진단**이다(3번 `vt46a.ts(5,23)`) — `error TS5` 글자로 멈추게 짜면 그런 칸이 격자에 들었을 때 **거짓으로 멈춘다**

- ★★ 설정 진단(`TS5023`·`TS5112`)은 **파일 이름 없이** `error TS…` 로 시작한다. 격자는 그 모양만 보고 멈춘다 — 가짜 옵션 `--bogusOpt` 이 `TS5023`(모르는 옵션)을 내자 `exit 4` 로 멈췄다. 멈출 때는 **코드만** 찍는다.

```text
===== EXTRA=--bogusOpt bash ts46b-infer46.sh -- 가짜 옵션을 끼운 판 (sh exit=4) =====
[r01] declare function f<T extends unknown[]>(...args: T): T;
      p = f(1, "a")
★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: TS5023 
```

### 11. ★★ 「**펼친 것의 길이를 타입이 아나**」 — 03편은 튜플을 **적는 법**을, JS 11편은 런타임에 **늘 배열**임을 쟀다. 그 사이의 **제네릭 추론**(언제 칸 수가 살아남고 언제 사라지나)이 이 주제다

- ★★ [**03번 주제**](../03-basic-type-annotations/) 4절 — 모양의 정본. JS 갈래 [**11번**](../../../js/syntax/11-spread-and-rest/) — 값의 정본. 여기서는 `T` 가 튜플로 잡히는 **세 문**과, `as const` 없는 스프레드가 **이미 배열**이라는 것을 더했다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `"$TSC_OLD"`·`"$TSC_49"`·`"$TSC_39"` · `node` · `"$NODE20"` · Chrome | `7.0.2` · `5.9.3` · `4.9.5` · `3.9.3` · `v18.19.1` · `v20.19.6` |
| ★★★ 추론 격자 | `bash ts46b-infer46.sh` — 15칸 × 판 넷 | 튜플 **`11 / 15`** · 배열 **`4 / 15`** · 세 판 **`2 / 15`** · 네 판 **`10 / 15`** |
| ★ 자기검사 | `EXTRA=--bogusOpt` | **`exit 4`** 로 멈췄다 |
| ★★ 튜플 꼴 | `vt46a.ts` × 세 판 | `TS1257`·`TS1265`·`TS1266` · 4.9.5 만 `TS5084` |
| ★★ 레이블 | `vt46b.ts` × 세 판 | 진단 0줄 · `exit 0` |
| ★★ 스프레드 | `vt46c.ts` × 세 판 | `TS2556`·`TS2345` · 표준 출력 동일 |
| ★ 방출 | `vt46d.ts` → `node` | 흔적 0 · `["k",1,true] 3` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **레이블 섞기 규칙 · `readonly` 튜플을 `unknown[]` 제약에**(2·3번) — 4.9.5 에서 막혔고 5.9.3 부터 풀렸다. 어느 판에서 풀렸는지는 **좁히지 못했다.**
- ★ **유니온 표시 순서**(2번 `r14`) — 판마다 다르다.

**안 돌려 본 것**

- ★★ **4.0 · 4.2 그 판** — 이 머신에 없다(3.9.3 과 4.9.5 사이).
- ★ 릴리스 노트의 문장 — **출처를 확인하지 못했다**(외부 네트워크 금지).
