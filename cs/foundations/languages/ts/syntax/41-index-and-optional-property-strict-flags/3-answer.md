# ts/syntax/41 — 인덱스·선택 프로퍼티 엄격 플래그 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 9번의 도움말 대조만 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 2창 변형(`symbol` 탐침 격자)이고, 둘째 기둥은 3창(`{ a: undefined }` 대 `{}` 의 방출물 + `node`)이다.**\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 끔 — 19행(`.at`)만 `number | undefined`, 나머지 **`number`** · 켬 — **6·7·8·9·16·18·21행**이 `number | undefined` 로 바뀐다 — **`7 / 11`**

**출력**

```ts
// idx41.ts
declare const arr: number[];
declare const dict: { [k: string]: number };
declare const rec: Record<string, number>;
declare const fixed: Record<"a" | "b", number>;
declare const pair: [number, string];
const p1: symbol = arr[0];
const p2: symbol = dict["k"];
const p3: symbol = dict.k;
const p4: symbol = rec.k;
const p5: symbol = fixed.a;
const p6: symbol = pair[0];
for (const v of arr) {
    const p7: symbol = v;
}
const [first] = arr;
const p8: symbol = first;
const { k } = dict;
const p9: symbol = k;
const p10: symbol = arr.at(0);
for (let i = 0; i < arr.length; i++) {
    const p11: symbol = arr[i];
}
export {};
```

```bash
# ts38b-idx41.sh
#!/usr/bin/env bash
# idx41.ts 의 symbol 탐침을 noUncheckedIndexedAccess 끔/켬 으로 두 번 -- 줄마다 진단 문구에서 타입만 뽑아 나란히
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
types() { grep "^idx41.ts(" | sed "s/^idx41.ts(\([0-9]*\),[0-9]*): error TS2322: Type '\(.*\)' is not assignable to type 'symbol'\./\1$(printf '\t')\2/"; }
tsc --pretty false --noEmit -t es2022 idx41.ts > "$D/off.raw" 2>&1; r1=$?
tsc --pretty false --noEmit -t es2022 --noUncheckedIndexedAccess idx41.ts > "$D/on.raw" 2>&1; r2=$?
case "$(cat "$D/off.raw" "$D/on.raw")" in *"error TS5"*) echo "★ 설정 진단이 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac
types < "$D/off.raw" > "$D/off"; types < "$D/on.raw" > "$D/on"
echo "tsc 종료 코드 -- 끔 $r1 · 켬 $r2 · 탐침 줄 수 -- 끔 $(wc -l < "$D/off") · 켬 $(wc -l < "$D/on")"
if [ "$(wc -l < "$D/off")" -ne "$(wc -l < "$D/on")" ]; then echo "★ 두 판의 탐침 줄 수가 다르다 -- 멈춘다"; exit 3; fi
printf '%-4s %-12s %-24s %s\n' "행" "끔" "켬" "갈림"
split=0; total=0
while IFS=$'\t' read -r l1 t1 && IFS=$'\t' read -r l2 t2 <&3; do
  if [ "$l1" != "$l2" ]; then echo "★ 행이 어긋났다($l1 ≠ $l2)"; exit 3; fi
  mark=""; [ "$t1" != "$t2" ] && { mark="★"; split=$((split+1)); }
  printf '%-4s %-12s %-24s %s\n' "$l1" "$t1" "$t2" "$mark"
  total=$((total+1))
done < "$D/off" 3< "$D/on"
if [ "$total" -eq 0 ]; then echo "★ 탐침 줄이 하나도 없다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
if [ "$split" -eq 0 ] || [ "$split" -eq "$total" ]; then echo "★ 갈린 칸이 0 이거나 전부다 -- 격자를 다시 봐라"; fi
echo
echo "갈린 칸 $split / $total"
```

```text
===== bash ts38b-idx41.sh (sh exit=0) =====
tsc 종료 코드 -- 끔 1 · 켬 1 · 탐침 줄 수 -- 끔 11 · 켬 11
행  끔          켬                      갈림
6    number       number | undefined       ★
7    number       number | undefined       ★
8    number       number | undefined       ★
9    number       number | undefined       ★
10   number       number                   
11   number       number                   
13   number       number                   
16   number       number | undefined       ★
18   number       number | undefined       ★
19   number | undefined number | undefined       
21   number       number | undefined       ★

갈린 칸 7 / 11
```

```text
===== tsc --pretty false --noEmit -t es2022 --noUncheckedIndexedAccess idx41.ts (tsc exit=1) =====
idx41.ts(6,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(7,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(8,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(9,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(10,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
idx41.ts(11,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
idx41.ts(13,11): error TS2322: Type 'number' is not assignable to type 'symbol'.
idx41.ts(16,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(18,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(19,7): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
idx41.ts(21,11): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
```

**왜 그런가**

- ★★★ 바뀐 것은 **키·자리가 타입에 안 적힌** 접근이다 — 배열 인덱스 · 인덱스 시그니처(`["k"]`·`.k`) · `Record<string, …>` · 그 둘의 **구조 분해** · 루프 안의 `arr[i]`.
- ★★ 안 바뀐 것 — `Record<"a" | "b", …>` · 튜플 `pair[0]` · `for…of` 의 원소(6번). `.at()` 은 **끔에서도** `| undefined`.
- ★ 스크립트는 두 판의 탐침 줄 수가 다르거나 행이 어긋나면 멈추고, 갈린 칸이 0 이거나 전부면 경고를 찍게 되어 있다.

### 2. ★★ 끔 — **10행 탐침만**(`number | undefined`) · 켬 — 5행 **`TS2375`** · 7행 **`TS2412`** · 8행 `delete` **통과** · 10행 **그대로 `number | undefined`** · 15행 `Loose` **통과**

**출력**

```ts
// eopt41.ts
interface Opts {
    retries?: number;
}
const a: Opts = {};
const b: Opts = { retries: undefined };
const c: Opts = {};
c.retries = undefined;
delete c.retries;
function read(o: Opts) {
    const p1: symbol = o.retries;
}
interface Loose {
    retries?: number | undefined;
}
const d: Loose = { retries: undefined };
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 eopt41.ts ; 이어서 --exactOptionalPropertyTypes 를 붙여 한 번 더 (sh exit=0) =====
eopt41.ts(10,11): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
(exit 1)
eopt41.ts(5,7): error TS2375: Type '{ retries: undefined; }' is not assignable to type 'Opts' with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the types of the target's properties.
  Types of property 'retries' are incompatible.
    Type 'undefined' is not assignable to type 'number'.
eopt41.ts(7,1): error TS2412: Type 'undefined' is not assignable to type 'number' with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the type of the target.
eopt41.ts(10,11): error TS2322: Type 'number | undefined' is not assignable to type 'symbol'.
  Type 'undefined' is not assignable to type 'symbol'.
(exit 1)
```

**왜 그런가**

- ★★★ 켜면 `retries?: number` 는 「**없음** 또는 `number`」 — `undefined` 를 **쓰는** 두 꼴이 막힌다. 리터럴은 `TS2375`, 대입은 `TS2412` 로 **코드가 다르다.**
- ★★ `delete` 는 「없게 만드는 것」이라 허락된다. 읽기(10행)는 키가 없을 수 있으니 여전히 `| undefined`(8번).
- ★★ `retries?: number | undefined` 로 **적으면** 켜도 받는다 — 문구의 「Consider adding 'undefined'」.

### 3. ★★★ 검사 — **12행 탐침만**(`number`) · node — **`[1] true false`** · **`[2] 1 0`** · **`[3] {} {}`** · **`[4] undefined undefined`** · **`[5] 3`** · 켜면 **5행 `TS2375`**

**출력**

```ts
// eoptrun41.ts
interface Opts {
    retries?: number;
}
const defaults = { retries: 3 };
const given: Opts = { retries: undefined };
const empty: Opts = {};
const merged = { ...defaults, ...given };
console.log("[1]", "retries" in given, "retries" in empty);
console.log("[2]", Object.keys(given).length, Object.keys(empty).length);
console.log("[3]", JSON.stringify(given), JSON.stringify(empty));
console.log("[4]", merged.retries, typeof merged.retries);
const p1: symbol = merged.retries;
console.log("[5]", { ...defaults, ...empty }.retries);
```

```text
===== tsc --pretty false --noEmit -t es2022 eoptrun41.ts ; 이어서 --exactOptionalPropertyTypes 를 붙여 한 번 더 (sh exit=0) =====
eoptrun41.ts(12,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
(exit 1)
eoptrun41.ts(5,7): error TS2375: Type '{ retries: undefined; }' is not assignable to type 'Opts' with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the types of the target's properties.
  Types of property 'retries' are incompatible.
    Type 'undefined' is not assignable to type 'number'.
eoptrun41.ts(12,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
(exit 1)
```

```text
===== tsc --pretty false -t es2022 --outDir e41 eoptrun41.ts (tsc exit=2) =====
eoptrun41.ts(12,7): error TS2322: Type 'number' is not assignable to type 'symbol'.
===== 방출된 e41/eoptrun41.js =====
"use strict";
const defaults = { retries: 3 };
const given = { retries: undefined };
const empty = {};
const merged = { ...defaults, ...given };
console.log("[1]", "retries" in given, "retries" in empty);
console.log("[2]", Object.keys(given).length, Object.keys(empty).length);
console.log("[3]", JSON.stringify(given), JSON.stringify(empty));
console.log("[4]", merged.retries, typeof merged.retries);
const p1 = merged.retries;
console.log("[5]", { ...defaults, ...empty }.retries);
```

```text
===== node e41/eoptrun41.js (node exit=0) =====
[1] true false
[2] 1 0
[3] {} {}
[4] undefined undefined
[5] 3
```

**왜 그런가**

- ★★★ `given` 은 키가 **있고** 값이 `undefined`, `empty` 는 키가 **없다** — `in`·`Object.keys` 가 그것을 가른다(7번).
- ★★★ 스프레드는 `undefined` 값도 **복사해서** 기본값 `3` 을 덮었다(`[4]`). 키가 없는 `empty` 는 `3` 을 남겼다(`[5]`). 그런데 **타입은 둘 다 `number`** 라고 말한다(12행).
- ★★ 켜면 `given` 을 **만드는 5행**이 막힌다 — 12행의 `number` 가 거짓이 될 값이 **애초에 못 생긴다.**

### 4. ★★ 끔 **0건** · `noUnchecked…` **5건**(11·14·18행 `TS2532` · 28행 `TS2345` 둘) · `exactOptional…` **2건**(22행 `TS2375` · 25행 `TS2412`) · 둘 다 **7건**

**출력**

```ts
// cost41.ts
// 두 플래그 없이 통과하던 코드를 흉내 낸 한 장
interface Row {
    id: string;
    note?: string;
}
const rows: Row[] = [{ id: "a" }, { id: "b", note: "x" }];
const byId: Record<string, Row> = {};
for (const r of rows) byId[r.id] = r;

function firstId(list: Row[]): string {
    return list[0].id;
}
function noteOf(id: string): string {
    return byId[id].note ?? "";
}
function total(xs: number[]): number {
    let t = 0;
    for (let i = 0; i < xs.length; i++) t += xs[i];
    return t;
}
function update(r: Row, note: string | undefined): Row {
    return { ...r, note: note };
}
function clear(r: Row) {
    r.note = undefined;
}
const [head] = rows;
console.log(firstId(rows), noteOf("a"), total([1, 2]), update(head, undefined), clear(head));
export {};
```

```bash
# ts38b-cost41.sh
#!/usr/bin/env bash
# cost41.ts 한 장을 두 플래그의 네 조합으로 -- 진단 수와 (행:코드)
set -u -o pipefail
short() { grep -o '^cost41.ts([0-9]*,[0-9]*): error TS[0-9]*' | sed 's/^cost41.ts(\([0-9]*\),[0-9]*): error /\1:/' | tr '\n' ' '; }
T=$'\t'
combos=(
  "(둘 다 끔)${T}"
  "noUncheckedIndexedAccess${T}--noUncheckedIndexedAccess"
  "exactOptionalPropertyTypes${T}--exactOptionalPropertyTypes"
  "둘 다 켬${T}--noUncheckedIndexedAccess --exactOptionalPropertyTypes"
)
printf '%-28s %-4s %s\n' "조합" "수" "행:코드"
for c in "${combos[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$c"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $c"; exit 3; fi
  IFS="$T" read -r name fl <<< "$c"
  # shellcheck disable=SC2086
  out=$(tsc --pretty false --noEmit -t es2022 $fl cost41.ts 2>&1)
  case $out in *"error TS5"*) echo "★ 설정 진단이 들었다 -- 수를 믿지 마라"; exit 4 ;; esac
  printf '%-28s %-4s %s\n' "$name" "$(grep -c '^cost41.ts(' <<< "$out")" "$(short <<< "$out")"
done
```

```text
===== bash ts38b-cost41.sh (sh exit=0) =====
조합                       수  행:코드
(둘 다 끔)                0    
noUncheckedIndexedAccess     5    11:TS2532 14:TS2532 18:TS2532 28:TS2345 28:TS2345 
exactOptionalPropertyTypes   2    22:TS2375 25:TS2412 
둘 다 켬                  7    11:TS2532 14:TS2532 18:TS2532 22:TS2375 25:TS2412 28:TS2345 28:TS2345 
```

**왜 그런가**

- ★★ 인덱스 접근 셋(`list[0]` · `byId[id]` · 루프의 `xs[i]`)과 구조 분해 하나(`const [head] = rows`)가 첫째 플래그에 걸렸다 — 구조 분해 하나가 **인자 둘**로 번져 28행에 둘.
- ★★ 선택 프로퍼티에 `undefined` 를 쓰는 둘(`note: note` · `r.note = undefined`)이 둘째 플래그에 걸렸다.
- ★ 두 플래그의 진단은 **줄이 겹치지 않았다**(5 + 2 = 7). ★ 수는 **이 한 장**의 것이다 — 코드베이스의 비율을 말하지 않는다.

### 5. ★★★ **`number | undefined`** — 플래그는 **루프 조건을 좁히기에 쓰지 않는다**

- ★★ 1번 21행 · 4번 18행 — 둘 다 `i < length` 안인데 붙었다.
- ★★ 고치는 길 — `for…of` 로 바꾸면 **안 붙는다**(1번 13행). 아니면 `??`·`!==` 로 좁힌다(40편 3절). `!` 는 40편의 끈 판으로 돌아간다(10번).

### 6. ★★★ 튜플 `pair[0]` · `Record<"a" | "b", …>` 의 `fixed.a` · `for…of` 의 원소 — **켬·끔 모두 `number`** · `.at()` — **켬·끔 모두 `number | undefined`**

- ★★★ 「**un-declared field**」 — 레퍼런스의 문장 그대로, **타입에 선언된 키·자리**(튜플의 0번, 유니온 키 `"a"`)에는 안 붙는다. 이름을 안 적은 키(인덱스 시그니처·`string` 키·배열 번호)에만 붙는다.
- ★★ `for…of` 는 **있는 원소를 도는** 것이라 번호를 안 쓴다.
- ★ `.at()` 은 메서드의 **반환 타입**에 이미 `undefined` 가 있어 플래그와 무관하다.

### 7. ★★★ `JSON.stringify` 만 같고(`{}` · `{}`) · `in`·`Object.keys`·스프레드는 다르다 — **`undefined` 값은 직렬화에서 빠지지만 키는 남아 있기 때문** · 사고는 **`[4]` — 기본값을 `undefined` 가 덮는데 12행 타입은 `number`**

- ★★★ `in`·`Object.keys` 는 **키의 존재**를 본다 — `true false` · `1 0`.
- ★★★ 스프레드는 **있는 키를 복사한다** — 값이 `undefined` 여도. 그래서 `merged.retries` 는 `undefined` 인데 타입은 `number`. 이 칸이 `exactOptionalPropertyTypes` 가 지키는 곳이다(3번의 켠 판 5행).
- ★ 로그를 `JSON.stringify` 로만 찍는 습관이면 두 값이 **같아 보여** 원인을 못 찾는다.

### 8. ★★★ **쓰기만** 바꾼다 — 읽기는 여전히 `T | undefined` · 받게 하려면 **`a?: T | undefined`** 로 적는다

- ★★ 2번 10행 — 켬에서도 `number | undefined`. 키가 **없을 수 있으니** 읽기는 그대로다.
- ★★ 2번 15행 `Loose` — 켬에서도 `{ retries: undefined }` 통과.

### 9. ★★ **안 켜진다** — 세 판 모두 도움말 「default: false」에 「unless `strict`」가 **없다** · 07편 4절이 **기본값에서 진단 0건**을 던져 보였다

**출력**

```text
===== tsc --help --all 에서 두 플래그의 기본값 줄 ; 이어서 "$TSC_OLD" · "$TSC_49" 로 같은 것 (sh exit=0) =====
---- 7.0.2
--exactOptionalPropertyTypes  default: false
--noUncheckedIndexedAccess  default: false
---- 5.9.3
--exactOptionalPropertyTypes  default: false
--noUncheckedIndexedAccess  default: false
---- 4.9.5
--exactOptionalPropertyTypes  default: false
--noUncheckedIndexedAccess  default: false
```

- ★★ 39편의 하위 플래그들은 「unless `strict` is …」가 붙었다(39편 1절). 이 둘은 **묶음 밖**이다.
- ★ 도움말 문구는 틀릴 수도 있다(39편 7번 — 4.9.5 의 `useUnknownInCatchVariables`). 이 둘은 07편 4절의 **실측**이 받쳐 준다.

### 10. ★★ 07편 4절의 **`TS2375`**(`{ host: "a", port: undefined }`) · 40편 3절 「**`!` 는 방출에서 지워지고 끈 판과 같은 `TypeError`**」 · 39편 격자는 **`strict` 가 켜는** 것을 봤고 이 둘은 **`strict` 가 안 켠다**

- ★★ [**07번 주제**](../07-object-type-details/) 4절 — 같은 코드, 같은 문구 꼴(「… with 'exactOptionalPropertyTypes: true'.」).
- ★★ [**40번 주제**](../40-strict-null-checks-ripple/) 3절 — `hit!` 이 `hit` 로 방출되고 `[2] TypeError`. 4번의 진단을 `!` 로 없애면 **검사만 사라진** 그 판이다.
- ★★ [**39번 주제**](../39-strict-bundle/) 2절 — 하위 여덟(아홉)은 「키없음」·`true` 열에서 켜졌다. 이 둘은 그 격자에 **없다.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `"$NODE20" --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `v20.19.6` · `Python 3.12.3` |
| ★★★ 인덱스 격자 | `bash ts38b-idx41.sh` — 끔/켬 | **`7 / 11`** |
| ★★ 선택 프로퍼티 진단 | `eopt41.ts` 끔/켬 | `TS2375` · `TS2412` · `delete`·`Loose` 통과 |
| ★★★ 런타임 | `eoptrun41.ts` 검사 둘 · 방출 · `node` | `true false` · `1 0` · `{} {}` · `undefined` · `3` |
| ★★ 비용 | `bash ts38b-cost41.sh` — 네 조합 | 0 · 5 · 2 · 7 |
| ★ 도움말 | 세 판 `--help --all` | 모두 「default: false」 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **스프레드 결과의 타입**(3번 12행 `number`) — 이 판의 계산이다.
- ★ **진단 코드**(`TS2375`·`TS2412`·`TS2532`) — 7.0.2 의 것이다.

**안 돌려 본 것**

- ★ **`Object.assign`·`Partial<T>`·`noPropertyAccessFromIndexSignature`** — 던지지 않았다.
- ★ **검사 시간** · **코드베이스의 진단 비율** — 재지 않았다.
