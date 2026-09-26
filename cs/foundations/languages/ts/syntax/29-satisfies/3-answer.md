# ts/syntax/29 — `satisfies` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★ 이 주제의 **본체 창은 네 가지 비교 격자다** — 1번이 결론을 낸다. 2번은 **3창(방출 `.js` + `node`)** 이 결론을 낸다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `satisfies` 는 **검사 칸에서 주석과 같고, 추론 칸에서 주석과 다르다** — 갈린 칸 **15 / 21**

**출력**

```bash
# ts26b-four.sh
#!/usr/bin/env bash
# 같은 객체 리터럴을 네 가지로 적는다 -- 칸마다 파일 하나씩 따로 던진다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
decl='type Color = "red" | "green";
type Palette = Record<Color, string | [number, number, number]>;'
good='{ red: [255, 0, 0], green: "#0f0" }'
wrong='{ red: [255, 0, 0], green: 42 }'
missing='{ green: "#0f0" }'
extra='{ red: [255, 0, 0], green: "#0f0", blue: "#00f" }'
write() { # write <모드> <객체> -> 선언 한 줄
  case $1 in
    annot) echo "const x: Palette = $2;" ;;
    as)    echo "const x = $2 as Palette;" ;;
    sat)   echo "const x = $2 satisfies Palette;" ;;
    none)  echo "const x = $2;" ;;
  esac
}
cell() { # cell <모드> <열> -> 칸 하나
  local mode=$1 col=$2 obj=$good tail='' out
  case $col in
    green) tail='const probe: null = x.green;' ;;
    red)   tail='const probe: null = x.red;' ;;
    wrong) obj=$wrong ;;
    missing) obj=$missing ;;
    extra) obj=$extra ;;
    upper) tail='x.green.toUpperCase();' ;;
    assign) tail='x.green = [0, 0, 255];' ;;
  esac
  { echo "$decl"; write "$mode" "$obj"; echo "$tail"; echo 'export {};'; } > "$D/c.ts"
  out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/c.ts" 2>&1)
  case $col in
    green|red) printf '%s\n' "$out" | sed -n "s/.*error TS2322: Type '\(.*\)' is not assignable to type 'null'\./\1/p" | head -1 ;;
    *) codes=$(printf '%s\n' "$out" | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
       echo "${codes:-OK}" ;;
  esac
}
declare -A got
for col in green red wrong missing extra upper assign; do
  case $col in
    green) title='[1] x.green 의 타입' ;;
    red) title='[2] x.red 의 타입' ;;
    wrong) title='[3] green 에 42 를 적으면' ;;
    missing) title='[4] red 를 빼면' ;;
    extra) title='[5] blue 를 더하면' ;;
    upper) title='[6] x.green.toUpperCase() 를 부르면' ;;
    assign) title='[7] x.green 에 [0, 0, 255] 를 대입하면' ;;
  esac
  echo "$title"
  for mode in annot as sat none; do
    v=$(cell "$mode" "$col"); got[$mode.$col]=$v
    case $mode in annot) lab=': Palette';; as) lab='as Palette';; sat) lab='satisfies';; none) lab='(plain)';; esac
    printf '  %-11s %s\n' "$lab" "$v"
  done
done
diff=0; total=0
for mode in annot as none; do
  for col in green red wrong missing extra upper assign; do
    total=$((total+1)); if [ "${got[$mode.$col]}" != "${got[sat.$col]}" ]; then diff=$((diff+1)); fi
  done
done
echo
echo "satisfies 행과 갈린 칸 $diff / $total"
```

```text
===== bash ts26b-four.sh (sh exit=0) =====
[1] x.green 의 타입
  : Palette   string | [number, number, number]
  as Palette  string | [number, number, number]
  satisfies   string
  (plain)     string
[2] x.red 의 타입
  : Palette   string | [number, number, number]
  as Palette  string | [number, number, number]
  satisfies   [number, number, number]
  (plain)     number[]
[3] green 에 42 를 적으면
  : Palette   TS2322
  as Palette  TS2352
  satisfies   TS2322
  (plain)     OK
[4] red 를 빼면
  : Palette   TS2741
  as Palette  OK
  satisfies   TS2741
  (plain)     OK
[5] blue 를 더하면
  : Palette   TS2353
  as Palette  OK
  satisfies   TS2353
  (plain)     OK
[6] x.green.toUpperCase() 를 부르면
  : Palette   TS2339
  as Palette  TS2339
  satisfies   OK
  (plain)     OK
[7] x.green 에 [0, 0, 255] 를 대입하면
  : Palette   OK
  as Palette  OK
  satisfies   TS2322
  (plain)     TS2322

satisfies 행과 갈린 칸 15 / 21
```

**왜 그런가**

| 질문 | `: Palette` | `as Palette` | `satisfies` | `(plain)` |
|---|---|---|---|---|
| [1] `x.green` | `string \| [number, number, number]` | 같다 | ★ **`string`** | `string` |
| [2] `x.red` | `string \| [number, number, number]` | 같다 | ★★ **`[number, number, number]`** | `number[]` |
| [3] 틀린 값 | `TS2322` | ★ **`TS2352`** | `TS2322` | 통과 |
| [4] 빠진 키 | `TS2741` | ★★ **통과** | `TS2741` | 통과 |
| [5] 더한 키 | `TS2353` | ★★ **통과** | `TS2353` | 통과 |
| [6] `toUpperCase()` | `TS2339` | `TS2339` | ★★★ **통과** | 통과 |
| [7] 튜플 대입 | 통과 | 통과 | ★★★ **`TS2322`** | `TS2322` |

- ★★★ **[1]·[6] 이 `satisfies` 를 쓰는 이유**다 — 검사는 주석과 똑같이 받고([3]\~[5]), 타입은 **값 자신의 것**이라 `toUpperCase` 가 된다.
- ★★★ **[7] 은 거꾸로다** — `satisfies` 의 `x.green` 이 `string` 이라 규격이 허락하는 튜플도 **못 넣는다.** [6] 의 이득이 [7] 의 대가다.
- ★★ **[2] 에서 `satisfies` 와 `(plain)` 은 같지 않다** — `satisfies` 가 **더 좁다**(튜플). 5번.
- ★★ `as` 는 [3] 에서만 막고 [4]·[5] 는 통과시켰다 — 6번.
- ★ 마지막 줄 **15 / 21** 은 **이 `Palette` 하나**에서 센 수다 — 11번.

### 2. ★★★ 진단 **0줄**(`exit=0`) · `.js` 에서 **`as` 가 사라진다** · 두 줄 다 **`TypeError`**

**출력**

```ts
// ex.29a.ts
// as 로 적은 타입과 실제로 들어 있는 값
interface User {
    id: number;
    name: string;
}
const empty = {} as User;
const half = { id: 1 } as User;

for (const [label, u] of [["empty", empty], ["half", half]] as const) {
    try {
        console.log(label, u.name.toUpperCase());
    } catch (e) {
        console.log(label, (e as Error).constructor.name, (e as Error).message);
    }
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.29a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e29a ex.29a.ts (tsc exit=0) =====
===== 방출된 e29a/ex.29a.js =====
"use strict";
const empty = {};
const half = { id: 1 };
for (const [label, u] of [["empty", empty], ["half", half]]) {
    try {
        console.log(label, u.name.toUpperCase());
    }
    catch (e) {
        console.log(label, e.constructor.name, e.message);
    }
}
```

```text
===== node e29a/ex.29a.js (node exit=0) =====
empty TypeError Cannot read properties of undefined (reading 'toUpperCase')
half TypeError Cannot read properties of undefined (reading 'toUpperCase')
```

**왜 그런가**

- ★★★ **컴파일러는 아무 말도 안 했다**(빈 블록 + `exit=0`). `{}` 와 `{ id: 1 }` 은 `User` 의 **부분 모양**이라 `as` 가 통과시킨다.
- ★★★ 방출된 `.js` 는 `const empty = {};` — **`as User` 가 흔적도 없다.** `as` 는 **런타임에 아무것도 안 한다.**
- ★★ `node` — `empty TypeError Cannot read properties of undefined (reading 'toUpperCase')` 와 `half` 의 같은 줄.
  타입은 `name: string` 이라 했는데 **값에 `name` 이 없다.** 틀린 단언은 **쓰는 줄에서** 터진다.

### 3. ★★ `readonly` 리터럴 · **`string` 으로 넓어짐** · `"a"` — 막히는 쪽은 **9행(`TS1355`)과 10행(`TS2322`) 둘 다**

**출력**

```ts
// ex.29b.ts
// satisfies 와 as const -- 붙이는 순서와 문맥 타입
const routes = { home: "/", user: "/u" } as const satisfies Record<string, string>;
const p1: null = null as unknown as typeof routes;
const loose = { home: "/", user: "/u" } satisfies Record<string, string>;
const p2: null = null as unknown as typeof loose;
const picked = { mode: "a" } satisfies Record<string, "a" | "b">;
const p3: null = null as unknown as typeof picked;

const flipped = { home: "/" } satisfies Record<string, string> as const;
const wrong = { home: 1 } as const satisfies Record<string, string>;
console.log(p1, p2, p3, flipped, wrong);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.29b.ts (tsc exit=1) =====
ex.29b.ts(3,7): error TS2322: Type '{ readonly home: "/"; readonly user: "/u"; }' is not assignable to type 'null'.
ex.29b.ts(5,7): error TS2322: Type '{ home: string; user: string; }' is not assignable to type 'null'.
ex.29b.ts(7,7): error TS2322: Type '{ mode: "a"; }' is not assignable to type 'null'.
ex.29b.ts(9,31): error TS1355: A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.
ex.29b.ts(10,17): error TS2322: Type 'number' is not assignable to type 'string'.
```

**왜 그런가**

| 줄 | 꼴 | 답 |
|---|---|---|
| 3 | `as const satisfies Record<string, string>` | **`{ readonly home: "/"; readonly user: "/u"; }`** |
| 5 | ★★★ `satisfies Record<string, string>` 만 | **`{ home: string; user: string; }`** — ★ 넓어졌다 |
| 7 | `satisfies Record<string, "a" \| "b">` | **`{ mode: "a"; }`** — 규격이 리터럴이라 좁게 남았다 |
| 9 | ★★ `satisfies … as const` | **`TS1355`** — `as const` 가 리터럴 아닌 식에 붙었다 |
| 10 | `as const satisfies` 인데 `home: 1` | **`TS2322`** — 굳혀도 검사는 돈다 |

- ★★★ 5행이 요점이다 — **`satisfies` 는 리터럴 넓히기를 막지 않는다.** [**21번 주제**](../21-inference-control-const-and-noinfer/) 4절이 같은 답(`string`)을 먼저 받았다.

### 4. ★★★ **11·12행이 한 글자도 같다** — 15행은 **막힌다(`TS2322`)**

**출력**

```ts
// ex.29c.ts
// const 타입 매개변수와 satisfies -- 누가 적나
function define<const T extends Record<string, string>>(t: T): T {
    return t;
}
function plain<T extends Record<string, string>>(t: T): T {
    return t;
}
const byCallee = define({ home: "/", user: "/u" });
const byValue = { home: "/", user: "/u" } as const satisfies Record<string, string>;
const byNeither = plain({ home: "/", user: "/u" });
const p1: null = null as unknown as typeof byCallee;
const p2: null = null as unknown as typeof byValue;
const p3: null = null as unknown as typeof byNeither;

const w1 = define({ home: 1 });
console.log(p1, p2, p3, w1);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.29c.ts (tsc exit=1) =====
ex.29c.ts(11,7): error TS2322: Type '{ readonly home: "/"; readonly user: "/u"; }' is not assignable to type 'null'.
ex.29c.ts(12,7): error TS2322: Type '{ readonly home: "/"; readonly user: "/u"; }' is not assignable to type 'null'.
ex.29c.ts(13,7): error TS2322: Type '{ home: string; user: string; }' is not assignable to type 'null'.
ex.29c.ts(15,21): error TS2322: Type 'number' is not assignable to type 'string'.
```

**왜 그런가**

```text
  11행  define({ … })                          { readonly home: "/"; readonly user: "/u"; }
  12행  { … } as const satisfies Record<…>     { readonly home: "/"; readonly user: "/u"; }   ★ 같다
  13행  plain({ … })                           { home: string; user: string; }
```

- ★★ 15행 `define({ home: 1 })` — **`TS2322`**. 제약 `extends Record<string, string>` 이 `satisfies` 의 몫을 한다.
- ★★★ 같은 결과, **다른 손** — 10번.

### 5. ★★ `satisfies` 가 **더 좁다** — 규격이 **문맥 타입**으로 흘러 들어가기 때문이다

- ★★★ `(plain)` 은 `[255, 0, 0]` 을 문맥 없이 추론해 **`number[]`**. `satisfies Palette` 는 규격의 `[number, number, number]` 가
  **문맥 타입**이 되어 **튜플로** 추론했다.
- ★★ 그러니 「검사만 한다」는 「**식의 타입을 규격으로 넓히지 않는다**」는 뜻이지 「**추론에 전혀 손대지 않는다**」는 뜻이 아니다.
  3번 7행의 `"a"` 도 같은 기제다 — 규격의 리터럴 유니온이 문맥이 되어 `"a"` 를 지켰다.
- ★ 이 해석은 **출력에서 읽은 것**이다. 명세 문장으로 확인하지 않았다.

### 6. ★★ **「두 타입이 겹칠 수 있나」** 하나 — 부분 모양이면 통과시킨다

- ★★★ [3] `{ green: 42 }` 은 `green` 이 `string | [number, number, number]` 와 **겹칠 수 없어** `TS2352`
  「neither type sufficiently overlaps with the other」. [4]·[5] 는 **빠지거나 더한 것**일 뿐 겹칠 수 있어 **통과**.
- ★★ 2번의 `{}` 와 `{ id: 1 }` 은 `User` 의 **부분 모양**이다 — 겹칠 수 있으니 통과. 그리고 런타임에 터졌다.
- ★ `as unknown as T` 로 이 겹침 검사마저 넘는 법은 목록의 **30번 주제**가 정본이다.

### 7. ★★★ **같은 말이 아니다** — 남는 경우 3번 **7행**, 안 남는 경우 3번 **5행**

- ★★★ 「추론을 넓히지 않는다」는 **규격(`T`)으로 넓히지 않는다**는 뜻이다(1번 [1]). **리터럴 넓히기**와는 다른 축이다.
- ★★ 리터럴이 **안 남는다** — 3번 5행 `satisfies Record<string, string>` → `home: string`.
- ★★ 리터럴이 **남는다** — 3번 7행 `satisfies Record<string, "a" | "b">` → `mode: "a"`. 규격이 **리터럴을 담고 있을 때**뿐이다.
- ★★★ 그러므로 「`satisfies` 와 `<const T>` 는 **둘 다** 넓히기를 막는다」는 **반만 맞다.** 리터럴 넓히기를 막는 것은 **`as const` 와 `<const T>`** 다.

### 8. ★★ **`as const satisfies T`** 만 된다 — 반대는 `as const` 가 **리터럴 아닌 식**에 붙어 `TS1355`

- ★★ `… satisfies T as const` 는 `(… satisfies T) as const` 로 읽힌다. `as const` 는 **리터럴에만** 붙을 수 있는데, 그 앞은 **`satisfies` 식**이다(3번 9행).
- ★ `… as const satisfies T` 는 먼저 리터럴을 굳히고, **굳힌 것**을 검사한다(3번 3행).

### 9. ★★ 값을 바꿔 넣을 객체는 **`: T` 주석** — `as` 는 **내가 더 아는 것이 확실할 때만**

- ★★ `satisfies` 는 변수의 타입이 **값의 추론된 모양**이라, 나중에 규격이 허락하는 **다른 값**을 넣을 자리가 타입에 없다 —
  1번 [7] 에서 `x.green = [0, 0, 255]` 가 **`satisfies` 행에서만(과 `(plain)`) `TS2322`** 였다. 주석은 변수를 **규격 그 자체**로 만들어 통과시켰다.
- ★★★ `as` 는 **빠짐·더함을 안 보고 런타임에 사라진다**(1번 [4]·[5] · 2번). 외부 데이터의 모양을 **다른 수단으로 이미 확인한** 자리처럼,
  컴파일러보다 **내가 더 아는 것이 확실할 때**에만 쓴다.

### 10. ★★ **`<const T>` 는 정의자가, `as const satisfies` 는 값을 쓰는 사람이** 적었다 — 결과는 **같다** · 06 과도 **같은 답**

- ★★★ 11행은 **함수를 정의한 사람**이 `<const T extends Record<string, string>>` 을 **한 번** 적었고 호출자는 아무것도 안 적었다.
  12행은 **값을 쓰는 사람**이 `as const satisfies Record<string, string>` 을 **그 자리에서** 적었다. 결과는 **한 글자도 같다.**
- ★★ [**11번 주제**](../11-literal-types-and-as-const/) — `as const` 의 정본. 3번 3행이 그 위에 선다.
- ★★ [**21번 주제**](../21-inference-control-const-and-noinfer/) — `<const T>` 의 정본. 「누가 적느냐」의 축도 그쪽 3절에서 왔다.
- ★★ 1번 [5] — `satisfies` 행이 **`TS2353`**. [**06번 주제**](../06-excess-property-checks/)가 「`satisfies` 도 초과 프로퍼티 검사를 받는다」로 먼저 받은 답과 **같다.**

### 11. ★ 세 층 — 그리고 15 / 21 은 **이 객체의 성질**이다

| 층 | 이 주제의 예 |
|---|---|
| **언어 보장(4.9)** | `satisfies` 가 검사하고 식의 타입을 규격으로 바꾸지 않는다 · `as` 는 겹침만 보고 방출에 흔적이 없다 |
| **이 판의 관찰** | 규격이 문맥 타입이 되어 튜플로 추론(1번 [2]) · `satisfies` 만으로는 리터럴이 넓어진다(3번 5행) · 갈린 칸 15 / 21 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 세 파일 전부 같다 |

- ★★★ **15 / 21 은 `Palette` 라는 객체 하나의 수**다. 규격이 유니온이 아니면 [1]·[6] 의 갈림이 **생기지 않는다.**
  `satisfies` 의 성질은 수가 아니라 「**검사 칸은 주석과 같고, 추론 칸은 값 쪽**」이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ 네 가지 격자 | `bash ts26b-four.sh` (4 × 7 = **28회 컴파일**) | exit 0 · **갈린 칸 15 / 21** |
| `as` 의 침묵 | `--noEmit ex.29a.ts` | ★ **exit 0 · 진단 0줄** |
| `as` 의 방출 | `--outDir e29a ex.29a.ts` | exit 0 · `as User` 가 **사라졌다** |
| `as` 의 실행 | `node e29a/ex.29a.js` | exit 0 · ★ 두 줄 다 **`TypeError`** |
| `as const` 조합 | `--noEmit ex.29b.ts` | exit 1 · **5건** · `TS1355` · `TS2322` |
| `<const T>` 대비 | `--noEmit ex.29c.ts` | exit 1 · **4건** · 11·12행 **같은 글자** |
| `strict` 대조 | 세 파일을 `--strict false` 로 재실행 | **하나도 안 갈림** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **규격이 문맥 타입으로 흘러 튜플·리터럴로 추론되는 것**(1번 [2] · 3번 7행) — 출력에서 읽은 것이다.
- ★ 진단 **문구** 전문 — `TS2352`·`TS1355` 의 긴 문구는 판본에 매인다. 코드가 더 오래 간다.
- ★ `node` 의 **`TypeError` 메시지 문구** — 엔진 판에 매인다.

**안 돌려 본 것**

- ★★ **격자를 `--strict false` 로** — 세 소스 파일만 대조했다.
- ★★ **규격에 없는 키를 나중에 더하는 코드** — 격자 [7] 은 **있는 키의 값 바꾸기**만 던졌다.
- ★ **`as unknown as T`·`!`** — 목록의 **30번 주제**.
- ★ **규격이 유니온이 아닌 객체로 돌린 격자** — 15 / 21 이 객체에 달렸다는 것은 **추론**이다. 다른 객체로는 안 돌렸다.
