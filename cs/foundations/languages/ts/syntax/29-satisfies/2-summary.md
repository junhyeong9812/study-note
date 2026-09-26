# ts/syntax/29 — `satisfies` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TypeScript 4.9 릴리스 노트 — The `satisfies` Operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html) ·
> [Handbook — Everyday Types (Type Assertions)](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html).
> 위는 **규칙 확인용 링크**이고, 본문의 진단·출력은 **전부 이 판에서 직접 던져 받은 것**이다. 릴리스 노트 예제를 옮기지 않았다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 네 가지 비교 격자다.**
> 같은 객체 리터럴을 **`: T` 주석 / `as T` / `satisfies T` / 아무것도 없음** 넷으로 적고, 일곱 가지를 물어 **칸마다 파일 하나씩** 던졌다(1절).
> ★★ 둘째 기둥은 **3창(방출된 `.js` + `node`)** 이다 — 이 갈래의 순수 타입 주제들과 달리, 여기서는 `as` 가 **런타임에 무엇을 남기는지**가 결론이다(2절).
> ★★★ **29 는 11 에서 온다.** [**11번 주제**](../11-literal-types-and-as-const/)의 「리터럴이 넓어지는 자리」와 `as const` 가 이 주제의 바닥이고,
> [**21번 주제**](../21-inference-control-const-and-noinfer/)의 `const` 타입 매개변수가 **넓히기를 막는 다른 손**이다(4절).
> [**06번 주제**](../06-excess-property-checks/)가 「`satisfies` 도 초과 프로퍼티 검사를 받는다」를 이미 실측했다 — 여기서는 격자의 한 칸으로 **인용한다.**
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — `satisfies` 는 **TS 4.9** 다. `as const` 는 **3.4**, `const` 타입 매개변수는 **5.0** 이다. ★ **7.0.2 에서 도는지는 던져서 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 주제가 쓰는 탐침 — 그리고 칸을 파일로 쪼갠 이유

```text
  const probe: null = x.green;
                      └─ 이 자리의 타입이 X 라면
  TS2322  「Type 'X' is not assignable to type 'null'.」   ← 여기서 X 를 읽는다
```

- ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★★★ **격자의 칸마다 파일 하나씩** 던졌다. 한 파일에 스물여덟 칸을 몰면 **한 칸의 에러가 옆 칸의 추론에 섞일 수** 있다 —
  「여러 탐침을 한 프로세스에서 돌리면 서로 샌다」는 원고 규칙 22 의 교훈을 **타입 쪽에 옮긴 것**이다.
  ★ 칸 하나 = 선언 두 줄(`Color`·`Palette`) + 적는 법 한 줄 + 묻는 줄 한 줄이다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다 |
| **안 흔들린다** | ★★★ 1절 격자의 스물여덟 칸과 마지막 줄의 **갈린 칸 수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 2절 — 방출기의 고정 형식 · 예외 **메시지만** 찍었다(경로가 박히는 스택은 안 찍었다) |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **세 파일 전부 한 글자도 같다** | 5절 |
| **★ 부적용 — 5창(`.d.ts`)** | 이 주제는 **값에 붙는 연산자**라 `.d.ts` 로 물을 것이 **없다** | `.d.ts` 블록이 **하나도 없다** |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **안 잰 것** | 검사 **시간** | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**`satisfies` 는 「규격 검사 도장」이다. 규격에 맞는지 검사만 하고, 물건에 붙은 원래 라벨은 떼지 않는다.**

| 비유 | 실체 |
|---|---|
| 물건을 **규격 상자에 담아** 버린다 — 상자 라벨만 남는다 | `const x: Palette = …` — 추론이 **`Palette` 로 넓어진다** |
| **「이건 규격품입니다」라고 적힌 스티커를 붙인다** — 검사는 대충 | `… as Palette` — ★ **빠진 것·더한 것을 안 본다** |
| ★★★ **규격 검사만 받고** 물건은 **제 라벨 그대로** 둔다 | `… satisfies Palette` — **검사는 주석만큼, 추론은 자기 것** |
| 아무 검사 없이 **제 라벨 그대로** | 아무것도 없음 — 추론만 있고 검사는 없다 |
| ★★ 검사 도장이 **라벨을 좁혀 주지는 않는다** — 라벨을 **굳히는 것**은 따로다 | `satisfies` 만으로는 `"#0f0"` 이 `string` 으로 넓어진다 · 굳히는 건 `as const` |

- ★★★ 한 줄로 — 「**`satisfies` 는 주석만큼 검사하고, 타입은 값 자신의 추론을 남긴다. 그러나 리터럴을 굳히지는 않는다.**」

```text
  같은 객체, 네 가지로 적는다 — 무엇이 남나

                    검사                     x.green 의 타입
  : Palette         빠짐·틀림·더함 다 본다     string | [number, number, number]   ← 넓어졌다
  as Palette        틀림만 (그것도 반쯤)       string | [number, number, number]   ← 넓어졌다
  satisfies         빠짐·틀림·더함 다 본다     string                               ★ 자기 것
  (plain)           안 본다                    string                               자기 것
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 넷은 정확히 어디서 갈리나** — 추론 두 칸 · 검사 세 칸 · 좁은 접근 한 칸을 **격자로** 센다(1절).
2. **`as` 는 무엇을 통과시키고 무엇을 막나** — 격자 두 칸 + **런타임에 실제로 터지는 것**(2절).
3. **`satisfies` 는 넓히기를 막는가** — `as const` 와 붙이는 순서, 그리고 [**21번 주제**](../21-inference-control-const-and-noinfer/)의 `const` 타입 매개변수와 견준다(3·4절).

★★ 3번은 **브리핑의 전제 하나가 뒤집히는 자리**다 — 「`satisfies` 와 `const` 타입 매개변수는 둘 다 넓히기를 막는다」가 **반만 맞다**(3절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **네 가지 비교 격자** | 적는 법 넷 × 질문 일곱 | 칸마다 파일 하나 | **본체**(1절) |
| ★★ **3창 — 방출된 `.js` + `node`** | `as` 가 **런타임에 남긴 것** | 실행 결과 | 2절 — ★ 이 배치에서 **3창이 쓰이는 유일한 주제** |
| ★★ **2창 — `null` 탐침** | 추론된 타입 | 계산된 것 | 1·3·4절 |
| ★ **진단이 0줄인 것** | 컴파일러가 **아무 말도 안 한 것** | 빈 블록 + `exit=0` | 2절 |
| ★ **부적용 — 5창(`.d.ts`)** | 값 쪽 연산자라 물을 것이 **없다** | — | — |

비용 — 격자 스물여덟 번 + 컴파일 세 번 + 방출 한 번 + `node` 한 번 + `--strict` 대조 여섯 번.

```text
  두 축으로 놓으면 — 검사하나 × 타입을 규격으로 넓히나

                         타입을 규격으로 넓힌다       값 자신의 추론을 둔다
  검사한다(빠짐·더함까지)   : T 주석                     ★ satisfies
  겹침만 본다              as T                         —
  검사 안 한다             —                            (plain)
```

### (1) ★★★ 네 가지 비교 격자 — 같은 객체를 네 가지로 적는다

**언제 쓰나** — 「주석을 달까, `as` 를 쓸까, `satisfies` 를 쓸까」를 고를 때. 이 주제의 전부가 이 격자에 있다.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **[1] `x.green` 의 타입** — `: Palette` 와 `as Palette` 는 **`string | [number, number, number]`** 로 **넓어졌다.**
  `satisfies` 와 `(plain)` 은 **`string`** — 값 자신의 추론이 남았다. 여기가 README 의 「**넓히지 않는다**」다.
- ★★★ **[2] `x.red` 의 타입** — 넷이 **세 가지로** 갈렸다. 주석·`as` 는 유니온, **`satisfies` 는 `[number, number, number]`(튜플)**, `(plain)` 은 **`number[]`**.
  ★ `satisfies` 가 **`(plain)` 보다도 좁다.** 규격(`Palette`)이 **문맥 타입**으로 흘러 들어가 `[255, 0, 0]` 을 **튜플로 추론**하게 했다.
  「검사만 한다」는 말이 **추론에 전혀 손대지 않는다**는 뜻은 아니다.
- ★★ **[3] `green` 에 `42`** — 주석·`satisfies` 는 **`TS2322`**, `as` 는 **`TS2352`**, `(plain)` 은 통과.
  ★ **`as` 도 막을 때가 있다** — 2절에서 푼다.
- ★★★ **[4] `red` 를 빼면** — 주석·`satisfies` 는 **`TS2741`**, **`as` 는 통과**, `(plain)` 도 통과.
- ★★★ **[5] `blue` 를 더하면** — 주석·`satisfies` 는 **`TS2353`**(초과 프로퍼티), **`as` 는 통과.**
  ★ `satisfies` 도 초과 프로퍼티 검사를 받는다는 것은 [**06번 주제**](../06-excess-property-checks/)가 먼저 실측했다 — **같은 답**이다.
- ★★★ **[6] `x.green.toUpperCase()`** — 주석·`as` 는 **`TS2339`**(유니온이라 `toUpperCase` 가 없다), **`satisfies` 는 통과.**
  이것이 `satisfies` 를 쓰는 **실무 이유**다 — 검사를 받고도 **좁은 타입으로 계속 쓴다.**
- ★★★ **[7] `x.green` 에 `[0, 0, 255]` 대입** — 이번에는 **거꾸로**다. 주석·`as` 는 **통과**, **`satisfies`·`(plain)` 은 `TS2322`**.
  `satisfies` 의 `x.green` 은 **`string`** 이라(1절 [1]) 규격이 허락하는 튜플도 **못 넣는다.** [6] 의 이득이 [7] 의 대가다.
- ★★ 마지막 줄 **`satisfies` 행과 갈린 칸 15 / 21** — 다른 세 행 × 일곱 질문 중 열다섯 칸이 `satisfies` 와 다른 답을 냈다.

```text
  네 가지 × 일곱 질문 — 이 판의 격자를 그림으로

                 [1]green  [2]red      [3]틀림  [4]빠짐  [5]더함  [6]좁은 접근  [7]튜플 대입
  : Palette      유니온    유니온      TS2322   TS2741   TS2353   TS2339        ✓
  as Palette     유니온    유니온      TS2352   ✓        ✓        TS2339        ✓
  satisfies      string    [n, n, n]   TS2322   TS2741   TS2353   ✓             TS2322
  (plain)        string    number[]    ✓        ✓        ✓        ✓             TS2322

  ★ satisfies 행 = 검사 칸은 : Palette 와 같고, 추론 칸은 (plain) 쪽 — 단 [2] 는 둘 다와 다르다
```

비용 — `satisfies` 는 **타입을 규격으로 넓히지 않으므로**, 나중에 **규격이 허락하는 다른 값을 넣는 코드**가 막힌다([7]). 값을 바꿔 가며 쓸 객체면 주석이 낫다.

### (2) ★★★ `as` 는 거짓말을 통과시킨다 — 그리고 런타임에서 터진다

**언제 쓰나** — `as` 를 「타입을 **바꾸는** 연산자」로 오해하고 있지 않은지 확인할 때.

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

- ★★★ **진단이 0줄이고 `exit=0`** 이다. 필드가 하나도 없는 `{}` 와 `name` 이 없는 `{ id: 1 }` 을 `User` 라고 **적었는데 아무 말이 없다.**

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

- ★★★ 방출된 `.js` 에서 **`as User` 가 흔적도 없이 사라졌다** — `const empty = {};`. **`as` 는 런타임에 아무것도 안 한다.** 변환도 검사도 없다.

```text
===== node e29a/ex.29a.js (node exit=0) =====
empty TypeError Cannot read properties of undefined (reading 'toUpperCase')
half TypeError Cannot read properties of undefined (reading 'toUpperCase')
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 두 줄 다 **`TypeError`「Cannot read properties of undefined (reading 'toUpperCase')」.** 타입은 `name: string` 이라고 했는데 **값에는 `name` 이 없다.**
- ★★ 컴파일러는 **`as` 를 믿었다.** 그 믿음이 틀린 값은 **실행해야** 드러난다.
- ★★ 그러면 1절 [3] 의 `TS2352` 는 무엇인가 — `{ green: 42 }` 를 `Palette` 로 단언하자 「**neither type sufficiently overlaps**」라며 막았다.
  **`as` 는 두 타입이 「비교 가능」한지만 본다.** 한쪽이 다른 쪽의 **부분 모양**이면(빠진 것·더한 것) 통과시키고,
  `number` 와 `string | [number, number, number]` 처럼 **겹칠 수 없는 값**이면 막는다.

```text
  as 가 보는 것 — "둘이 겹칠 수 있나" 하나뿐

  {} as User                         {} 는 User 의 부분 모양     → 통과   → 런타임 TypeError
  { id: 1 } as User                  부분 모양                    → 통과   → 런타임 TypeError
  { red, green, blue } as Palette    Palette 보다 더 많다         → 통과   (1절 [5])
  { green: 42 } as Palette           green 이 겹칠 수 없다        → TS2352 (1절 [3])

  방출된 .js 에는 as 가 없다 — 런타임에 아무 일도 안 한다
```

★ `as unknown as T` 처럼 **두 번 단언해 겹침 검사까지 우회하는 법**과 `!` 는 [목록의 **30번 주제**](../30-type-assertions-and-non-null/)(타입 단언과 non-null `!`)가 정본이다.
**여기는 「`satisfies` 와 나란히 놓았을 때 무엇을 안 보나」까지**다.

비용 — `as` 로 적은 타입이 틀리면 **컴파일은 조용하고 런타임에 터진다.** 그리고 터지는 자리는 **단언한 줄이 아니라 쓰는 줄**이다.

### (3) ★★ `satisfies` 와 `as const` — 붙이는 순서와 문맥 타입

**언제 쓰나** — 「검사도 받고 **리터럴도 굳히고** 싶다」일 때. 라우트 표·설정 표가 대표다.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 3행 — `as const satisfies Record<string, string>` 은 **`{ readonly home: "/"; readonly user: "/u"; }`** — 리터럴이 **굳었고** 검사도 받았다.
- ★★★ **5행이 전제를 뒤집는다.** `satisfies` **만** 붙인 `loose` 는 **`{ home: string; user: string; }`** — **리터럴이 넓어졌다.**
  **`satisfies` 는 리터럴 넓히기를 막지 않는다.** 1절 [1] 의 `x.green` 이 `"#0f0"` 이 아니라 `string` 인 것도 같은 이야기다.
  ★ [**21번 주제**](../21-inference-control-const-and-noinfer/) 4절이 `satisfies Config` 로 **같은 답**(`string`)을 먼저 받았다 — 인용한다.
- ★★ 7행 — 그런데 규격이 **리터럴을 담고 있으면**(`Record<string, "a" | "b">`) **`{ mode: "a"; }`** 로 좁게 남는다.
  규격이 **문맥 타입**으로 흘러 들어가 리터럴을 **지켜 준 것**이다. 1절 [2] 의 튜플과 같은 기제다.
- ★★★ 9행 — **순서를 뒤집으면 `TS1355`** 「A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.」
  `… satisfies X as const` 에서 `as const` 는 **`satisfies` 식 전체**에 붙는데, 그것은 **리터럴이 아니다.**
- ★★ 10행 — `as const` 로 굳혀도 **검사는 돈다.** `home: 1` 은 **`TS2322`**.

```text
  넓히기를 막는 것과 안 막는 것

  { home: "/" } satisfies Record<string, string>           home: string   ← 넓어졌다
  { mode: "a" } satisfies Record<string, "a" | "b">        mode: "a"      ← 규격이 리터럴이라 지켜졌다
  { home: "/" } as const satisfies Record<string, string>  readonly home: "/"   ★ 굳힌 것은 as const

  { home: "/" } satisfies Record<string, string> as const  → TS1355  순서가 틀렸다
```

비용 — 「`satisfies` 를 썼으니 리터럴이 살아 있겠지」는 **규격이 리터럴일 때만** 맞다. 굳히려면 **`as const` 를 앞에** 둔다.

### (4) ★★ `const` 타입 매개변수와의 관계 — 누가 적나

**언제 쓰나** — 「라우트 표를 **함수로 받을까**(`define(…)`), **값에 붙일까**(`as const satisfies`)」를 고를 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 11·12행이 **같은 글자**다 — `{ readonly home: "/"; readonly user: "/u"; }`. 두 길이 **같은 곳**에 닿았다.
- ★★ 13행 — `const` 없는 `plain` 은 **`{ home: string; user: string; }`**. 넓어졌다.
- ★★ 15행 — `define({ home: 1 })` 은 **`TS2322`**. 제약 `extends Record<string, string>` 이 **검사를 맡는다** — `satisfies` 의 몫을 **제약이** 한다.
- ★★★ 갈리는 것은 **누가 적느냐**다. `<const T>` 는 **함수를 정의한 사람**이 한 번 적고 호출자는 **아무것도 안 적는다.**
  `as const satisfies` 는 **값을 쓰는 사람**이 **매번** 적는다.

```text
  같은 결과, 다른 손

  define({ … })                        정의자가 <const T extends …> 를 한 번 적는다
                                        호출자는 잊을 수 없다
  { … } as const satisfies Record<…>   값을 쓰는 사람이 매번 적는다
                                        함수가 필요 없다 — 모듈 최상단의 표에 쓴다

  둘 다 → { readonly home: "/"; readonly user: "/u"; }
```

★★ 브리핑의 전제 「둘 다 넓히기를 막는다」는 **이렇게 고쳐 읽는다** — **넓히기를 막는 것은 `as const` 와 `<const T>`** 이고,
**`satisfies` 는 검사를 붙일 뿐 넓히기는 규격이 리터럴일 때만 막힌다**(3절 5·7행).

비용 — `<const T>` 는 **라이브러리 저자의 결정**이라 호출자가 넓히고 싶어도 못 한다(21편). `as const satisfies` 는 **매번 잊을 수 있다.**

### (5) ★ 설정 대조

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.29a.ts    exit 0 = exit 0 · 출력 한 글자도 같다
ex.29b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.29c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```


```text
  as 의 한살이 — 적은 줄에서 쓴 줄까지

  const empty = {} as User;         tsc: 진단 0줄 · exit=0         ← 컴파일은 믿는다
         │ 방출
  const empty = {};                  .js 에 as 가 없다              ← 런타임엔 아무 일도 없다
         │ 실행
  empty.name.toUpperCase()           TypeError                      ← 쓰는 줄에서 터진다
```
- ★★ `--strict` 를 꺼도 **세 파일이 한 글자도 안 갈렸다.** 29a 는 두 판 다 **`exit 0`** — `as` 의 침묵은 **설정과 무관**하다.
- ★ 격자 스크립트(1절)는 `--strict` 로만 돌렸다. **꺼진 쪽 격자는 안 돌렸다.**

비용 — 없다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  const x: T = 값;                       검사 + 추론을 T 로 넓힌다          (1절)
  const x = 값 as T;                     겹침만 본다 · 런타임에 사라진다     (1·2절)
  const x = 값 satisfies T;              검사 + 추론은 값 자신의 것          (1절)   ★ 4.9
  const x = 값 as const satisfies T;     굳히고 + 검사                       (3절)
  function f<const T extends X>(t: T)    정의자가 굳히고 제약이 검사          (4절)   ★ 5.0
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `satisfies` 인데 값이 틀림 | `TS2322` | 1절 [3] · 3절 10행 |
| `satisfies` 인데 필드가 빠짐 | `TS2741` | 1절 [4] |
| `satisfies` 인데 필드가 더 있음 | `TS2353` | 1절 [5] |
| `as` 인데 겹칠 수 없는 값 | `TS2352` | 1절 [3] |
| 주석·`as` 뒤에 좁은 메서드 | `TS2339` | 1절 [6] |
| `satisfies`·`(plain)` 뒤에 규격의 다른 값 대입 | `TS2322` | 1절 [7] |
| `… satisfies T as const` | `TS1355` | 3절 9행 |

**규칙 불릿**

- ★★★ **`satisfies` 는 주석만큼 검사한다** — 틀림·빠짐·더함을 다 본다(1절 [3]\~[5]).
- ★★★ **`satisfies` 는 타입을 규격으로 바꾸지 않는다** — 값 자신의 추론이 남는다(1절 [1]·[6]).
- ★★ **규격은 문맥 타입으로 흘러 들어간다** — 튜플·리터럴 유니온이면 그쪽으로 좁게 추론된다(1절 [2] · 3절 7행).
- ★★★ **`satisfies` 는 리터럴 넓히기를 막지 않는다** — 굳히려면 `as const` 를 **앞에** 붙인다(3절 3·5행).
- ★★★ **`as` 는 겹침만 본다** — 빠진 것·더한 것을 통과시키고, **런타임에 사라진다**(2절).
- ★★ **`as const satisfies` 와 `<const T>` 는 같은 결과를 다른 손으로 낸다**(4절).

## 어디서 틀리나

- ★★★ 「**`satisfies` 는 넓히기를 막으니 리터럴이 남겠지**」 — **안 남는다.** `{ home: string }` 이다(3절 5행). 남는 것은 **규격이 리터럴일 때**뿐이다.
- ★★★ 「**`as` 는 검사를 받은 뒤 타입을 바꿔 준다**」 — **겹침만** 본다. `{} as User` 가 통과하고 **런타임에 터진다**(2절).
- ★★★ 「**`as` 는 아무것도 안 막는다**」 — 겹칠 수 없는 값은 **`TS2352`** 로 막는다(1절 [3]). 「아무것도」가 아니라 「**부분 모양이면**」이다.
- ★★ 「**`satisfies` 는 추론에 손대지 않는다**」 — 규격이 **문맥 타입**이 되어 `[255, 0, 0]` 을 **튜플로** 추론하게 했다(1절 [2]). `(plain)` 보다 좁다.
- ★★ 「**`satisfies` 는 초과 프로퍼티를 안 본다**」 — **본다**(1절 [5]) — 06편과 같은 답.
- ★★ 「**`satisfies X as const` 도 되겠지**」 — **`TS1355`**. 순서가 반대다(3절 9행).
- ★ 「**주석을 달면 나중에 좁게 쓸 수 있다**」 — 주석은 **규격으로 넓힌다.** `toUpperCase` 가 막힌다(1절 [6]).
- ★★ 「**`satisfies` 는 주석의 상위 호환이다**」 — **아니다.** 규격이 허락하는 튜플을 **나중에 넣지 못한다**(1절 [7]).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(4.9)** | `satisfies` 가 검사하고 **식의 타입은 바꾸지 않는다** | 릴리스 노트 · 1절 [1] |
| **언어 보장** | `as` 는 **겹침**(비교 가능성)만 보고 방출에 흔적이 없다 | 1절 [3]\~[5] · 2절 |
| **언어 보장(3.4 · 5.0)** | `as const` 와 `<const T>` 가 리터럴을 굳힌다 | 3·4절 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ `satisfies` 의 규격이 문맥 타입이 되어 **튜플로 추론** | 1절 [2] — **던져서** 얻었다 |
| **★ 이 판의 관찰** | ★★ `satisfies` 만으로는 리터럴이 넓어진다 · 규격이 리터럴이면 좁게 남는다 | 3절 5·7행 |
| **★ 이 판의 관찰** | 네 가지 격자의 **갈린 칸 15 / 21** | 1절 — **이 객체 하나**에서 센 것이다 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **세 파일 전부 같다** | 5절 |
| **★ 부적용 — 5창(`.d.ts`)** | 값 쪽 연산자라 물을 것이 없다 | — |
| **안 잰 것** | 검사 **시간** | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| **`satisfies`** — 설정·라우트·팔레트 표처럼 **규격 검사**를 받으면서 **좁은 타입으로 계속 쓸** 값 | 나중에 **값을 바꿔 넣을** 객체 — 추론된 모양에 갇힌다(1절 [7]). **주석**이 낫다 |
| **`as const satisfies`** — 리터럴까지 **굳혀야** 할 표 | 값을 **바꿔야** 하는 객체 — `readonly` 가 된다 |
| **`: T` 주석** — 변수의 타입이 **규격 그 자체**여야 할 때(함수 인자·확장될 객체) | 좁은 메서드를 **바로 써야** 할 때 — `TS2339`(1절 [6]) |
| **`as`** — 컴파일러보다 **내가 더 아는 것이 확실할 때**만 | ★★★ **검사를 받고 싶을 때** — `as` 는 빠진 것·더한 것을 **안 본다** |

## 핵심 문장

1. **`satisfies` 는 주석만큼 검사하고, 식의 타입은 값 자신의 추론으로 남긴다.**
2. **그래도 추론에 손은 댄다** — 규격이 문맥 타입이 되어 튜플·리터럴 쪽으로 좁힐 수 있다.
3. **★★★ `satisfies` 는 리터럴 넓히기를 막지 않는다** — 굳히는 것은 `as const`(값 쪽)와 `<const T>`(정의 쪽)다.
4. **`as` 는 겹침만 본다** — 부분 모양이면 통과시키고, 방출된 `.js` 에서 사라지며, 틀리면 런타임에 터진다.

## 관련 자료

- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — ★★★ **README 의 선행.** 리터럴이 넓어지는 자리와 `as const` 의 정본. 3절이 그 위에 선다.
- [**21번 주제** — 추론 제어](../21-inference-control-const-and-noinfer/) — ★★ `<const T>` 의 정본. 그쪽 4절이 `satisfies` 만으로는 `string` 이 된다는 것을 **먼저** 받았다 — 이 문서 3절 5행과 같은 답.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — `satisfies` 가 그 검사를 **안 끈다**는 실측은 그쪽. 1절 [5] 가 같은 답이다.
- [**28번 주제** — 유틸리티 타입](../28-utility-types/) — 격자의 규격 `Record<Color, …>` 는 그쪽의 유틸리티다.
- [**12번 주제** — 좁히기](../12-narrowing/) — 1절 [6] 의 「유니온이라 메서드가 없다」는 좁히기의 출발점이다.
- [목록의 **30번 주제**](../30-type-assertions-and-non-null/)(타입 단언과 non-null `!`) — ★★ `as`·`as unknown as`·`!` 의 정본. **여기는 `satisfies` 와 나란히 놓았을 때 `as` 가 무엇을 안 보나**까지.

## 용어 풀이

> **`satisfies`** — `값 satisfies T` 꼴로 **값이 `T` 에 맞는지 검사만** 하고, 식의 타입은 **값 자신의 추론**으로 두는 연산자(TS 4.9).\
> 예: `{ green: "#0f0" } satisfies Palette` 의 `green` 은 `string` 으로 남는다.

> **타입 주석(annotation)** — `const x: T = …` 처럼 **변수에 타입을 적는 것**. 검사하고, 변수의 타입은 **`T` 가 된다.**\
> 예: 1절 [1] 의 `: Palette` 행.

> **타입 단언(assertion)** — `값 as T`. 컴파일러에게 「**이건 `T` 다**」라고 **알려 주는** 것. 검사는 **겹침**뿐이다.\
> 예: `{} as User` 는 통과한다(2절).

> **겹침·비교 가능(comparable)** — 두 타입 중 **한쪽이 다른 쪽으로 좁혀질 여지**가 있는가. `as` 가 보는 유일한 조건이다.\
> 예: `{ green: 42 }` 과 `Palette` 는 `green` 이 겹칠 수 없어 **`TS2352`**(1절 [3]).

> **문맥 타입(contextual type)** — 식이 놓인 **자리가 기대하는 타입**. 추론이 그쪽으로 끌려간다.\
> 예: `satisfies Palette` 가 `[255, 0, 0]` 을 **튜플로** 추론하게 했다(1절 [2]).

> **리터럴 넓히기(widening)** — `"#0f0"` 같은 리터럴이 변경 가능한 자리에서 **`string` 으로 넓어지는 것**.\
> 예: 3절 5행 — `satisfies` 로는 안 막힌다.

> **`TS1355`** — 「A 'const' assertion can only be applied to references to enum members, or string, number, boolean, array, or object literals.」\
> 예: `… satisfies T as const` — `as const` 가 리터럴이 아닌 식에 붙었다(3절 9행).

> **`TS2352`** — 「Conversion of type … may be a mistake because neither type sufficiently overlaps with the other.」\
> 예: 1절 [3] 의 `as Palette` — `as` 가 막는 **유일한** 경우다.

## 더 들어가면

- **왜 `satisfies` 가 `(plain)` 보다 좁게 추론하나** — 1절 [2] 에서 `(plain)` 은 `number[]`, `satisfies` 는 튜플이었다.
  규격이 **문맥 타입**으로 들어가기 때문으로 읽힌다. 릴리스 노트는 「식의 타입을 바꾸지 않는다」고 적는데,
  그 「바꾸지 않는다」의 **기준**이 「문맥 없이 추론했을 때」가 아니라 「**규격으로 넓히지 않는다**」라는 것을 이 칸이 보인다.
  ★ 명세 문장으로 확인하지는 않았다 — **던져서 본 것**이다.
- **격자를 다른 객체로 돌리면** — 1절은 **`Palette` 하나**로 센 것이다. 규격이 유니온이 아니면 [1]·[6] 의 갈림이 **안 생긴다**(넓어질 곳이 없다).
  **15 / 21 이라는 수는 이 객체의 것**이지 `satisfies` 의 성질이 아니다. 성질은 「**검사 칸은 주석과 같고, 추론 칸은 값 쪽**」이다.
- **`satisfies` 를 함수 인자에 쓰면** — 21편 4절이 `takePlain({…} satisfies Config)` 로 던졌다 — 인자의 추론은 **함수의 타입 매개변수**가 정한다.
- **`as` 의 겹침 검사를 우회하는 `as unknown as T`** — [목록의 **30번 주제**](../30-type-assertions-and-non-null/)가 정본이다. **여기서는 안 던졌다.**
