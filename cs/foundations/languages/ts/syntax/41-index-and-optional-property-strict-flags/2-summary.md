# ts/syntax/41 — 인덱스·선택 프로퍼티 엄격 플래그 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess)(「Turning on `noUncheckedIndexedAccess` will add `undefined` to any un-declared field in the type」 · 4.1) ·
> [`exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/#exactOptionalPropertyTypes)(「Without this flag enabled, there are three values which you can set an optional property to: the declared type, `undefined`, or it can be missing.」 · 4.4).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다.
> **실행 검증** — 본판은 아래다. 5절의 도움말 대조에만 **`tsc` 5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.

```text
===== tsc --version · node --version · "$NODE20" --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
v20.19.6
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 2창 변형(`symbol` 탐침으로 뽑은 요소 타입 격자 — 꼴 열하나 × 켬/끔)이고, 둘째 기둥은 3창(`{ a: undefined }` 대 `{}` 의 방출물 + `node`)이다.** 비용은 **탐침 파일 한 장의 새 진단 수**로만 센다(4절).
> ★ 타입 탐침은 40편과 같은 **`const p: symbol = …`** 이다 — 진단 문구의 `Type '…'` 가 그 식의 타입이다.
> ★★★ **41 은 40 에서 온다.** [**40번 주제**](../40-strict-null-checks-ripple/)가 「`strictNullChecks` 가 `undefined` 를 따로 선 타입으로 만든다 · 끄면 조용해진 칸이 `TypeError`」를 쟀다. 여기의 두 플래그는 그 위에서 **`undefined` 를 더 붙이거나(인덱스) 덜 허락하는(선택 프로퍼티)** 쪽이다.
> ★★★ [**07번 주제**](../07-object-type-details/) 4절이 **이미 쟀다** — 두 플래그를 한 설정으로 켜면 `{ port: undefined }` 가 **`TS2375`**, `bag.missing.toFixed` 가 **`TS18048`**, 둘 다 **`strict` 에 안 든다.** 인용하고, 여기서는 **어느 꼴에 붙고 어느 꼴에 안 붙나**와 **런타임에서 갈리는 것**으로 넓힌다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` · `symbol` 탐침이 말하는 타입 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자의 칸과 마지막 줄의 **수** · 4절의 **진단 수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | `in`·`Object.keys`·`JSON.stringify` 는 값만 찍었다 |
| **★ 탐침 한 장의 수** | 4절의 「비용」 | ★★ **`cost41.ts` 한 장**에서 센 것이다 — 실제 코드베이스에서 몇 % 인지는 **주장하지 않는다** |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | 두 플래그가 검사 **시간**에 주는 영향 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**인덱스 접근은 「사물함 번호로 여는 것」이다. `noUncheckedIndexedAccess` 를 켜면 계산대가 「그 번호의 사물함이 **비어 있을 수 있다**」고 적어 준다 — 번호표만 믿지 말라는 것이다. `exactOptionalPropertyTypes` 는 거꾸로 「**사물함이 없는 것**」과 「**사물함은 있는데 비어 있는 것**」을 다른 것으로 친다 — 선택 프로퍼티에 `undefined` 를 **넣는 것**을 막는다.**

| 비유 | 실체 |
|---|---|
| 번호로 연 사물함에 「비어 있을 수 있음」 | `arr[i]`·`dict[k]` 의 타입에 **`\| undefined`** 가 붙는다(1절) |
| ★★ **번호가 정해진** 사물함은 딱지가 없다 | 튜플 `pair[0]` · `Record<"a" \| "b", T>` · `for…of` 의 원소 — **그대로**(1절) |
| ★★ 「방금 크기를 셌는데도」 딱지 | `for (i < arr.length) arr[i]` — **여전히 `\| undefined`**(1절 21행) |
| **사물함이 없다** vs **비어 있다** | `{}` 대 `{ retries: undefined }` — 켜면 뒤쪽을 막는다(`TS2375`·`TS2412`)(2절) |
| ★★★ 둘은 **런타임에서 정말 다르다** | `"retries" in` 이 `true` 대 `false` · `Object.keys` 가 `1` 대 `0`(3절) |
| ★★★ 비어 있는 사물함이 **기본값을 덮는다** | `{ ...defaults, ...given }` → `retries` 가 **`undefined`** — 타입은 **`number`** 라고 말한다(3절) |

- ★★★ 한 줄로 — 「**`noUncheckedIndexedAccess` 는 개수가 정해지지 않은 인덱스 접근에 `undefined` 를 붙이고, `exactOptionalPropertyTypes` 는 선택 프로퍼티에 `undefined` 를 넣는 것을 막는다. 앞쪽은 `undefined` 를 **읽는** 자리를, 뒤쪽은 **쓰는** 자리를 잡는다.**」

```text
  두 플래그가 서는 자리 — 같은 undefined, 반대 방향

  noUncheckedIndexedAccess     읽기    arr[i] · dict[k]          → T | undefined 를 붙인다
  exactOptionalPropertyTypes   쓰기    { a: undefined } · o.a = undefined  → 막는다 (a?: T 는 「없음」만 허락)
                               ★ 07편 4절이 두 코드를 먼저 쟀다 — TS18048 · TS2375
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ `noUncheckedIndexedAccess` 는 어느 꼴에 `undefined` 를 붙이고 어느 꼴에 안 붙이나** — 꼴 열하나 × 켬/끔(1절).
2. **★★★ `exactOptionalPropertyTypes` 는 무엇을 막고, 그것이 런타임에서 왜 의미가 있나** — 진단(2절) · `in`·`Object.keys`·스프레드(3절).
3. **★★ 켜는 비용** — 탐침 한 장에서 새로 나는 진단 수(4절) · 두 플래그가 `strict` 밖이라는 것(5절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **2창 변형 — `symbol` 탐침 격자** | 꼴 열하나의 요소 타입 × 켬/끔 | 계산된 것 | **본체**(1절) |
| ★★ **진단 대조** | `{ a: undefined }`·`o.a = undefined`·`delete` × 켬/끔 | 에러 코드 | 2절 |
| ★★★ **3창 — 방출물 + `node`** | `{ a: undefined }` 대 `{}` 가 **런타임에서** 갈리나 | 실행 결과 | **둘째 기둥**(3절) |
| ★★ **비용표** | 한 장 × 두 플래그의 네 조합 — 진단 수 | 수 | 4절 |
| ★ **도움말 창** | 세 판의 기본값 문구 | 도움말 | 5절 |
| ★ **부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — | — |

비용 — 격자 한 장 × 두 판(켬/끔) + 진단 대조 넷 · 방출 하나 · `node` 하나 + 비용표 네 조합 + 도움말 세 판.

```text
  이 주제의 축 — 「undefined 가 어디서 오나」

  선언이 말한 것          a?: number          읽으면 number | undefined   (strictNullChecks — 40편)
  인덱스 접근             arr[i] · dict[k]    끔: T  · 켬: T | undefined   ← noUncheckedIndexedAccess
  개수가 정해진 접근       pair[0] · fixed.a   켬이어도 T
  선택 프로퍼티에 쓰기     { a: undefined }    끔: 통과 · 켬: TS2375        ← exactOptionalPropertyTypes
```

### (1) ★★★ `noUncheckedIndexedAccess` 격자 — 어느 꼴에 붙나

**언제 쓰나** — `arr[0].x`·`map[key].y` 가 실행에서 `TypeError` 인데 검사는 조용할 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **갈린 칸 `7 / 11`** — 켜면 **`number | undefined`** 가 되는 꼴: 배열 인덱스(6행) · 인덱스 시그니처의 `["k"]`·`.k`(7·8행) · **`Record<string, number>`**(9행) · **배열 구조 분해**(16행) · **인덱스 시그니처 구조 분해**(18행) · **`for (i < length)` 안의 `arr[i]`**(21행).
- ★★★ **안 갈린 꼴** — **`Record<"a" | "b", number>`**(10행) · **튜플 `pair[0]`**(11행) · **`for…of` 의 원소**(13행). 키·자리가 **타입에 적혀 있는** 접근과 **이미 있는 원소를 도는** 접근이다.
- ★★ **`.at(0)`**(19행) — **끔에서도 `number | undefined`**. 플래그가 붙인 것이 아니다 — 메서드의 **반환 타입**(`lib` 의 선언)에 이미 들어 있는 것으로 읽힌다.
- ★★★ **21행** — `i < arr.length` 를 막 검사했는데도 **`| undefined`**. 플래그는 **길이 검사로 좁히지 않는다** — 40편의 좁히기 수단(`!==`·`??`)이 여기서 **줄마다** 필요해진다.
- ★ 레퍼런스의 「un-declared field」가 이 격자의 경계다 — **선언된 키**(10행)·**선언된 자리**(11행)는 안 붙는다.

```text
  꼴 열하나 — 켰을 때 undefined 가 붙나

  붙는다 (7)                                 안 붙는다 (3)             플래그와 무관 (1)
  arr[0]        dict["k"]    dict.k          fixed.a  (키가 정해진 Record)  arr.at(0)  ← lib 가 늘 붙인다
  rec.k         const [first] = arr          pair[0]  (튜플의 자리)
  const { k } = dict                         for (const v of arr)
  for (i < arr.length) arr[i]   ★ 길이 검사로 안 좁혀진다
```

비용 — **루프 안의 `arr[i]`** 처럼 사람 눈에는 분명히 있는 자리에도 붙는다. 그래서 켜면 `for…of` 로 바꾸거나 `!`·`??` 를 붙이는 수정이 따라온다(4절의 11·18행).

### (2) ★★ `exactOptionalPropertyTypes` — 선택 프로퍼티에 `undefined` 를 넣지 못한다

**언제 쓰나** — `{ ...a, ...b }`·`Object.assign` 처럼 **「없음」과 「`undefined`」가 다르게 동작하는** 코드가 있을 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★ **끔** — `symbol` 탐침(10행) 하나만. 5행 `{ retries: undefined }`·7행 `c.retries = undefined` 는 **통과**했다.
- ★★★ **켬** — 5행 **`TS2375`**(07편 4절과 같은 코드 — 「… with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the types of the target's properties.」) · 7행 **`TS2412`**(「Type 'undefined' is not assignable to type 'number' with 'exactOptionalPropertyTypes: true'.」). **리터럴로 만들 때**와 **대입할 때**가 다른 코드다.
- ★★ **8행 `delete c.retries`** — 켬에서도 **통과**. 「없게 만드는 것」은 허락된다.
- ★★★ **10행 읽기** — 켬에서도 **`number | undefined`**. 이 플래그는 **쓰기만** 막고, 읽을 때 `undefined` 가 오는 것(키가 없으니까)은 그대로다.
- ★★ **15행 `Loose`**(`retries?: number | undefined`) — 켬에서도 **통과**. `undefined` 를 받고 싶으면 **타입에 적으면** 된다 — 문구의 「Consider adding 'undefined'」가 그것이다.

비용 — 켜면 `?:` 가 「**없음만 허락**」으로 뜻이 좁아진다. 기존 코드의 `x.a = undefined` 가 전부 `TS2412` 가 된다(4절의 25행).

### (3) ★★★ `{ a: undefined }` 와 `{}` 는 런타임에서 다르다

**언제 쓰나** — 「`undefined` 나 없는 거나 같지」가 **어디서 틀리는지** 볼 때. 2절의 플래그가 **무엇을 지키는지**가 여기서 드러난다.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **`[1] true false`** — `"retries" in given` 은 **`true`**, `in empty` 는 **`false`**. 키가 **있고 값이 `undefined`** 인 것과 **키가 없는** 것이다.
- ★★★ **`[2] 1 0`** — `Object.keys` 도 갈렸다.
- ★★ **`[3] {} {}`** — `JSON.stringify` 는 **둘을 같게** 적는다 — `undefined` 값은 직렬화에서 빠진다. 여기서만 보면 차이가 **안 보인다.**
- ★★★ **`[4] undefined undefined`** — `{ ...defaults, ...given }` 에서 `given` 의 **`retries: undefined` 가 기본값 `3` 을 덮었다.** 대조 **`[5] 3`** — 키가 **없는** `empty` 를 펼치면 기본값이 남는다.
- ★★★ **그런데 타입은 `number`** — 12행 `symbol` 탐침이 **끔·켬 모두 `Type 'number'`**. 스프레드는 선택 프로퍼티를 「**없으면 앞의 값이 남는다**」로 계산한다 — 값이 **`undefined` 로 있는** 경우를 타입이 못 본다. **타입은 `number`, 실제는 `undefined`** 인 칸이다.
- ★★★ **켜면 5행이 `TS2375`** — `given` 을 그렇게 **만들 수가 없다.** 그래서 12행의 「`number`」가 **거짓이 될 길이 막힌다.** 이 플래그가 지키는 것이 바로 이 칸이다.

```text
  같은 Opts, 두 값 — 런타임의 네 창

                    given = { retries: undefined }    empty = {}
  "retries" in      true                               false
  Object.keys       1                                  0
  JSON.stringify    {}                                 {}          ← 여기서는 같아 보인다
  { ...{retries:3}, ...x }.retries
                    undefined  ★ 기본값을 덮었다          3  (기본값이 남는다 — [5])
  타입(merged.retries)  number   ★ 거짓
  exactOptional 켬   5행 TS2375 — 이 값을 못 만든다
```

비용 — 끄면 **스프레드·`Object.assign` 의 기본값 병합이 `undefined` 에 덮이는 것**을 타입이 못 잡는다. 켜면 그 값을 **만드는 쪽**에서 막는다.

### (4) ★★ 비용 — 탐침 한 장에서 새로 나는 진단 수

**언제 쓰나** — 두 플래그를 켤지 정할 때. ★ 수는 **아래 한 장**의 것이다.

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

그림 해설 — 한 단계에 한 문장.

- ★★ **둘 다 끔 — 0건.** 이 한 장은 두 플래그 없이 **통과하는** 코드다.
- ★★★ **`noUncheckedIndexedAccess` — 5건** — 11행 `list[0].id` · 14행 `byId[id].note` · 18행 `xs[i]`(루프 — 1절 21행과 같은 칸) — 셋이 **`TS2532`**, 28행이 **`TS2345` 둘**(구조 분해 `head` 가 `Row | undefined` 가 되어 **두 함수 인자**에서).
- ★★ **`exactOptionalPropertyTypes` — 2건** — 22행 `{ ...r, note: note }`(`note: string | undefined` 를 `note?: string` 에) **`TS2375`** · 25행 `r.note = undefined` **`TS2412`**.
- ★★ **둘 다 — 7건.** 두 플래그의 진단은 **겹치지 않았다**(5 + 2 — 줄이 서로 다르다).
- ★ 28행의 둘은 **한 원인**(27행 `const [head] = rows` 의 구조 분해)에서 나온 **꼬리**다 — 진단 수는 **고칠 자리 수**와 같지 않다.

```text
  cost41.ts 한 장 — 새 진단이 난 줄

  noUncheckedIndexedAccess     11 · 14 · 18   TS2532   (인덱스 접근 셋)
                               28 · 28        TS2345   (구조 분해 하나가 인자 둘로 번졌다)
  exactOptionalPropertyTypes   22             TS2375   (리터럴의 note: undefined)
                               25             TS2412   (대입 r.note = undefined)
  ★ 수는 이 한 장의 것 — 코드베이스의 비율이 아니다
```

비용 — `noUncheckedIndexedAccess` 는 **인덱스 접근이 많을수록**, `exactOptionalPropertyTypes` 는 **선택 프로퍼티에 `undefined` 를 쓰는 곳이 많을수록** 진단이 는다. 어느 쪽이 더 비싼지는 **코드의 모양에 달렸고**, 이 문서는 그 비율을 재지 않았다.

### (5) ★ 두 플래그는 `strict` 밖이다 — 세 판의 도움말

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

- ★★ 세 판 모두 **「default: false」** — 39편의 하위 플래그들처럼 「unless `strict` …」가 **붙지 않는다.** `strict: true` 로는 안 켜진다(07편 4절의 표와 같다).
- ★ 39편 1절처럼 도움말 문구는 **틀릴 수도** 있다 — 여기서는 07편 4절이 **기본값에서 진단 0건**을 이미 던져 보였다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  --noUncheckedIndexedAccess              인덱스 접근에 | undefined           (1절)
  --exactOptionalPropertyTypes            a?: T 에 undefined 를 쓰지 못한다    (2절)
  a?: T | undefined                       exactOptional 에서도 undefined 를 받는다 (2절 Loose)
  delete o.a                              exactOptional 에서도 된다            (2절)
  for (const v of arr)                    noUnchecked 에서도 T                 (1절)
```

**금지 사례** — 켠 판에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `noUnchecked…` — 인덱스 결과에 곧장 멤버 접근 | `TS2532`(식) · `TS18048`(이름 — 07편 4절) | 4절 |
| `noUnchecked…` — 구조 분해 결과를 `T` 매개변수에 | `TS2345` | 4절 |
| `exactOptional…` — `{ a: undefined }` 를 `{ a?: T }` 에 | `TS2375` | 2·3·4절 |
| `exactOptional…` — `o.a = undefined` | `TS2412` | 2·4절 |

**규칙 불릿**

- ★★★ **`noUncheckedIndexedAccess` 는 개수가 안 정해진 접근에만 붙는다** — 튜플·키가 정해진 `Record`·`for…of` 는 그대로(1절 `7 / 11`).
- ★★ **길이 검사로는 안 좁혀진다** — 루프 안의 `arr[i]` 도 `| undefined`(1절 21행).
- ★★★ **`exactOptionalPropertyTypes` 는 쓰기를 막고 읽기는 그대로 둔다** — 읽으면 여전히 `T | undefined`(2절 10행).
- ★★★ **`{ a: undefined }` 와 `{}` 는 `in`·`Object.keys`·스프레드에서 다르다** — `JSON.stringify` 에서만 같다(3절).
- ★ **두 플래그 다 `strict` 밖**이다(5절 · 07편 4절).

## 어디서 틀리나

- ★★★ 「**`noUncheckedIndexedAccess` 를 켜면 튜플도 `| undefined`**」 — **튜플의 자리**는 그대로다(1절 11행).
- ★★ 「**`for…of` 도 `| undefined` 가 붙어 귀찮아진다**」 — **안 붙는다**(1절 13행). 켜면 오히려 `for…of` 로 옮기는 편이 진단이 준다.
- ★★ 「**길이를 검사했으니 `arr[i]` 는 있다**」 — 플래그는 **그 검사를 안 본다**(1절 21행).
- ★★★ 「**`undefined` 나 키가 없는 거나 같다**」 — `in`·`Object.keys`·**스프레드**에서 다르다(3절). `JSON.stringify` 만 보면 같아 보여서 속는다.
- ★★★ 「**스프레드의 결과 타입이 `number` 면 값도 숫자다**」 — `retries: undefined` 가 덮은 칸에서 타입은 `number`, 값은 `undefined`(3절).
- ★★ 「**`exactOptionalPropertyTypes` 를 켜면 선택 프로퍼티를 읽을 때 `undefined` 걱정이 없다**」 — **읽기는 그대로** `T | undefined`(2절 10행).
- ★ 「**`strict: true` 면 둘 다 켜진다**」 — **안 켜진다**(5절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **문서(TSConfig 레퍼런스)** | 인덱스의 「un-declared field」에 `undefined` · 선택 프로퍼티의 세 값(선언 타입·`undefined`·없음) 중 `undefined` 를 뺀다 | 기준 소스 |
| **컴파일러 동작** | 튜플·키가 정해진 `Record`·`for…of` 는 안 붙는다 · 길이 검사로 안 좁힌다 | 1절 `7 / 11` |
| **컴파일러 동작** | 리터럴 `TS2375` · 대입 `TS2412` · `delete` 는 허락 · 읽기는 그대로 | 2절 |
| **★ 이 판(7.0.2)의 관찰** | 스프레드의 결과 타입이 선택 프로퍼티를 「없으면 앞의 값」으로 계산 — 켬·끔 모두 `number` | 3절 12행 |
| **언어(JS) 의미** | `in`·`Object.keys` 는 **키의 존재**를 본다 · `JSON.stringify` 는 `undefined` 값을 뺀다 · 스프레드는 `undefined` 값도 **복사한다** | 3절 — node v18 |
| **★ 판 격자** | 두 플래그의 기본값 `false` — 세 판 같다 | 5절 |
| **안 잰 것** | 검사 시간 · 실제 코드베이스의 진단 비율 | **재지 않았다** · 탐침 한 장의 수만 |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★ **`noUncheckedIndexedAccess`** — `Record<string, T>`·맵처럼 **없는 키가 실제로 오는** 조회가 많을 때 | 인덱스 루프가 대부분인 수치 코드 — 줄마다 `!` 가 붙어 **40편의 끈 판**으로 돌아간다 |
| ★★★ **`exactOptionalPropertyTypes`** — **기본값 병합**(스프레드·`Object.assign`)·`in` 검사가 있는 설정 객체 | 선택 프로퍼티에 `undefined` 를 **일부러** 쓰는 API — `a?: T \| undefined` 로 **적어 두고** 켠다 |
| ★ 둘 다 **`strict` 와 따로** 켠다 — 묶음에 없다 | 「`strict` 켰으니 됐다」 |

## 핵심 문장

1. **`noUncheckedIndexedAccess` 는 개수가 정해지지 않은 인덱스 접근에 `| undefined` 를 붙인다** — 꼴 열하나 중 일곱이 갈렸고, 튜플·키가 정해진 `Record`·`for…of` 는 그대로다.
2. **그 `| undefined` 는 길이 검사로 좁혀지지 않는다** — 루프 안의 `arr[i]` 도 붙는다.
3. **`exactOptionalPropertyTypes` 는 선택 프로퍼티에 `undefined` 를 쓰는 것을 막는다** — 리터럴은 `TS2375`, 대입은 `TS2412`, 읽기는 그대로다.
4. **`{ a: undefined }` 와 `{}` 는 `in`·`Object.keys`·스프레드에서 다르다** — 스프레드에서 `undefined` 가 기본값을 덮는데 타입은 `number` 라고 말한다. 켜면 그 값을 만들 수 없다.
5. **비용은 코드의 모양에 달린다** — 탐침 한 장에서 5건과 2건, 겹치지 않았다.

## 관련 자료

- [**40번 주제** — `strictNullChecks` 의 파급](../40-strict-null-checks-ripple/) — ★★★ **README 의 선행.** `undefined` 가 따로 선 타입이 되는 것 · 좁히기 네 수단 · `!` 가 지워지는 것. **여기는 그 위에서 `undefined` 를 더 붙이거나 덜 허락하는 두 플래그부터.**
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) 4절 — 두 플래그의 첫 실측(`TS2375`·`TS18048`)과 「`strict` 에 안 든다」 표. 그쪽이 정본이다.
- [**39번 주제** — `strict` 묶음](../39-strict-bundle/) — 묶음 **안**의 플래그들과 도움말 문구의 판 격자.
- [**22번 주제** — `keyof` 와 인덱스 접근 타입](../22-keyof-and-indexed-access-types/) — 인덱스 시그니처가 있을 때의 키 유니온.
- [**28번 주제** — 유틸리티 타입](../28-utility-types/) — `Record<K, T>` 의 `K` 가 유니온이냐 `string` 이냐.
- [목록의 **43번 주제**](../43-remaining-tsconfig-choices/)(`tsconfig` 의 나머지 선택) — `noPropertyAccessFromIndexSignature` 처럼 같은 자리의 다른 플래그.

## 용어 풀이

> **`noUncheckedIndexedAccess`** — 인덱스 접근(`arr[i]`·`dict[k]`)의 결과에 `| undefined` 를 붙이는 플래그(4.1). `strict` 밖.\
> 예: 1절 6행.

> **`exactOptionalPropertyTypes`** — 선택 프로퍼티 `a?: T` 에 `undefined` 를 **쓰는 것**을 막는 플래그(4.4). `strict` 밖.\
> 예: 2절 5·7행.

> **인덱스 시그니처** — `{ [k: string]: T }` — 이름을 미리 안 적은 키의 값 타입.\
> 예: 1절 `dict`.

> **`TS2375`** — 「Type '…' is not assignable to type '…' with 'exactOptionalPropertyTypes: true'. Consider adding 'undefined' to the types of the target's properties.」 — 리터럴로 만들 때.\
> 예: 2절 5행.

> **`TS2412`** — 「Type 'undefined' is not assignable to type '…' with 'exactOptionalPropertyTypes: true'. …」 — 대입할 때.\
> 예: 2절 7행.

> **`in` 연산자** — 객체에 그 **키가 있는지**(프로토타입 포함)를 본다. 값이 `undefined` 여도 키가 있으면 `true`.\
> 예: 3절 `[1] true false`.

## 더 들어가면

- **`noPropertyAccessFromIndexSignature`** — 인덱스 시그니처의 키를 `.k` 로 못 쓰게 하는 플래그. 이 문서의 1절 8행과 같은 자리지만 **던지지 않았다.**
- **`Object.assign` 과 `structuredClone`** — 3절은 스프레드만 찍었다. 둘도 `undefined` 값을 복사하는지 **던지지 않았다.**
- **`Partial<T>` 와 `exactOptionalPropertyTypes`** — `Partial` 이 만드는 `?:` 도 같은 규칙을 따를 것으로 읽히지만 **던지지 않았다.**
