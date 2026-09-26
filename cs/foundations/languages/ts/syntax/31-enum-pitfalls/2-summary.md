# ts/syntax/31 — 열거형의 함정 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Enums](https://www.typescriptlang.org/docs/handbook/enums.html) ·
> [TypeScript 5.0 릴리스 노트 — All `enum`s Are Union `enum`s](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html) ·
> [TypeScript 5.8 릴리스 노트 — `--erasableSyntaxOnly`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 본판은 아래다. ★ 판 비교(3·5절)에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 —
> 경로는 소스에 박지 않고 환경변수 **`TSC_OLD`(5.9.3) · `TSC_49`(4.9.5)** 로 준다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(방출된 `.js` + `node`)이다.**
> TS 문법 대부분은 방출물에서 **사라진다**(30편). **enum 은 드물게 값을 남기는 문법**이라, 「무엇이 남나」를 **방출물 격자**로 센다(1절).
> ★★ 둘째 기둥은 **플래그 판 격자** — `const enum` 이 `--isolatedModules`·`--verbatimModuleSyntax`·`--preserveConstEnums`·`--erasableSyntaxOnly` 에서 **방출이 어떻게 갈리나**(4절).
> ★★★ enum 이 **값이자 타입**이라는 것은 [**23번 주제**](../23-typeof-type-operator/) 4절이 정본이다 — `Color`·`typeof Color`·`keyof typeof Color`·`Color.Red` 네 이름을 거기서 갈랐다. **인용한다.**
> ★ 유니온 리터럴·`as const` 는 [**11번 주제**](../11-literal-types-and-as-const/)가 정본이다.
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — 「모든 enum 이 유니온 enum」은 **5.0**(릴리스 노트), `--erasableSyntaxOnly` 는 **5.8**(릴리스 노트). ★ **이 머신에서 판 경계를 던져 본 것은 4.9.5 · 5.9.3 · 7.0.2 세 판뿐이다** — 5.0 그 자체는 없다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 1절 서른여섯 칸 · 4절 스무 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 방출기의 고정 형식 · 예외는 **타입과 메시지만** 찍었다 |
| **★ 판에 매인다** | 3절 — 같은 파일의 진단이 4.9.5 와 5.9.3·7.0.2 에서 **다르다** | 판 격자 자체가 결론이다 |
| **★ 판에 매인다** | 진단이 있을 때의 **종료 코드** — `--noEmit` 에서 7.0.2 는 `1`, 5.9.3 은 `2` | 3절 블록 — **수를 근거로 쓰지 않는다** |
| **★ 부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 — 이 주제의 질문은 **`.js` 에 무엇이 남나**다 | 4절의 `amb31.d.ts` 는 **입력**이지 방출물이 아니다 |
| **안 잰 것** | ★★★ **`const enum` 이 빠르다** · 검사 시간 · 번들 크기 | **재지 않았다** — 방출물의 **줄 수**만 셌다(1절) |

## 한눈에 — 쉽게 말하면

**enum 은 「번호표 대장」이다. 숫자 enum 은 대장을 양방향으로 찢어 붙여 둔 것이고, `const enum` 은 대장 없이 번호를 손등에 적어 가는 것이다.**

| 비유 | 실체 |
|---|---|
| **양방향 대장** — 「Up → 0」과 「0 → Up」을 한 장에 | 숫자 enum — 방출물이 `Dir[Dir["Up"] = 0] = "Up"`, **`Object.keys` 가 넷** |
| **한 방향 대장** — 이름 → 값만 | 문자열 enum — 역매핑이 **없다** |
| ★★ **대장 없이 손등에 적는다** — 대장을 찾는 사람은 허탕 | `const enum` — 쓰는 자리에 **숫자가 박히고** 객체가 **안 남는다** |
| **「대장은 어딘가 있을 것」이라는 메모** | `declare enum` — 방출물에 **아무것도 없는데** 참조만 남는다 |
| 대장 대신 **허용 목록**만 | 유니온 리터럴 `0 \| 1` — 값이 **없다**(타입뿐) |
| **평범한 쪽지** 한 장 + 목록 | `as const` 객체 — **한 줄** 객체, 역매핑 없음 |

- ★★★ 한 줄로 — 「**enum 은 TS 에서 드물게 값을 남긴다. 무엇이 남는지는 종류와 플래그마다 다르고, 그 차이가 전부 방출물에 있다.**」

```text
  같은 Up·Down 을 적는 여섯 가지 — 방출물에 남는 것

  enum Dir { Up, Down }                 ─> var Dir; (function (Dir) { … })(…)   5줄  양방향
  enum Dir { Up = "UP", Down = "DOWN" } ─> var Dir; (function (Dir) { … })(…)   5줄  한 방향
  const enum Dir { Up, Down }           ─> (없다) · 쓰는 자리에 0 /* Dir.Up */     0줄
  declare enum Dir { Up, Down }         ─> (없다) · 쓰는 자리에 Dir.Up 이 그대로   0줄  ← 누가 채우나
  type Dir = 0 | 1;                     ─> (없다)                                  0줄
  const Dir = {…} as const; type Dir …  ─> const Dir = { Up: 0, Down: 1 };         1줄
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 여섯 가지 선언은 방출물에 무엇을 남기고, 그 차이가 어디로 번지나** — 방출 · 대입 세 칸 · 실행 두 칸을 **격자로** 센다(1절).
2. **숫자 enum 의 함정은 정확히 어디인가** — 역매핑(`Object.keys` 넷) · `number` 통과 · 판마다 다른 리터럴 대입(2·3절).
3. **`const enum` 은 어느 플래그에서 무엇이 되나** — 플래그 판 격자(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — 방출된 `.js` + `node`** | enum 이 **런타임에 남긴 객체** | 실행 결과 | **본체**(1·2·4절) |
| ★★★ **방출물 격자** | 선언 여섯 × (방출 · 대입 셋 · 실행 둘) | 칸마다 파일 하나 | 1절 |
| ★★★ **플래그 판 격자** | `const enum` × 플래그 다섯 | 판마다 방출 + `node` | 4절 |
| ★★ **판 격자** | 같은 파일을 4.9.5 · 5.9.3 · 7.0.2 로 | 진단 대조 | 3절 |
| ★ **설정 대조** | `--strict` 를 끄면 | 글자 단위 대조 | 5절 |
| ★ **부적용 — 5창(`.d.ts`)** | 방출물의 **모양**이 질문이라 선언 방출은 **안 물었다** | — | — |

비용 — 격자 서른여섯 칸(컴파일 마흔여덟 번 — 검사 서른 · 방출 열여덟 — + `node` 열두 번) + 플래그 다섯 판(방출 다섯 · `node` 다섯 번에 모듈 열다섯 개) + 세 판 × 두 번.

```text
  이 주제의 축 — 「값이 있나」 × 「타입이 좁나」

                          런타임 값        number 를 받나     멤버 값 리터럴을 받나
  숫자 enum               ★ 양방향 객체    ★★ 받는다          받는다
  문자열 enum             한 방향 객체     안 받는다          ★ 안 받는다(명목적)
  const enum              없다(인라인)     ★★ 받는다          받는다
  declare enum            없다(참조만)     받는다             받는다   ← 99 까지 받는다
  유니온 0 | 1            없다             안 받는다          받는다
  as const 객체           한 줄 객체       안 받는다          받는다
```

### (1) ★★★ 방출물 격자 — 같은 두 값을 여섯 가지로

**언제 쓰나** — 「enum 을 쓸까, 유니온을 쓸까, `as const` 를 쓸까」를 고를 때. 이 주제의 결론이 전부 이 격자에 있다.

```bash
# ts30b-enumgrid.sh
#!/usr/bin/env bash
# 같은 두 값(Up·Down)을 여섯 가지로 선언한다 -- 칸마다 파일 하나씩 따로 던진다
# 방출 칸은 선언만 컴파일해 .js 의 줄 수를 센다 · 대입 칸은 진단 코드 · 실행 칸은 node 출력(앞에 진단 코드)
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'   # 구분자는 탭 -- 선언 안에 ; 와 | 가 나온다(규칙 32)
kinds=(
  "num${T}enum Dir { Up, Down }${T}0"
  "str${T}enum Dir { Up = \"UP\", Down = \"DOWN\" }${T}\"UP\""
  "const${T}const enum Dir { Up, Down }${T}0"
  "declare${T}declare enum Dir { Up, Down }${T}0"
  "union${T}type Dir = 0 | 1;${T}0"
  "asconst${T}const Dir = { Up: 0, Down: 1 } as const; type Dir = (typeof Dir)[keyof typeof Dir];${T}0"
)
codes() { tsc --pretty false --noEmit -t es2022 --strict "$1" 2>&1 | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
cell() { # cell <열> <선언> <멤버값> -> 칸 하나
  local col=$1 decl=$2 lit=$3 f="$D/c.ts" c out
  case $col in
    emit)  echo "$decl" > "$f"
           rm -rf "$D/o"; tsc --pretty false -t es2022 --strict --outDir "$D/o" "$f" > /dev/null 2>&1
           echo "$(grep -cv '^"use strict";$' "$D/o/c.js" || true)줄" ; return ;;
    lit)   { echo "$decl"; echo "let v: Dir = $lit;"; } > "$f" ;;
    n99)   { echo "$decl"; echo "let v: Dir = 99;"; } > "$f" ;;
    nvar)  { echo "$decl"; echo "const n: number = 99;"; echo "let v: Dir = n;"; } > "$f" ;;
    keys|rev)
      if [ "$col" = keys ]; then probe='JSON.stringify(Object.keys(Dir))'; else probe='JSON.stringify(Dir[0])'; fi
      { echo "$decl"; echo "try {"; echo "    console.log($probe);"; echo "} catch (e) {"
        echo "    console.log((e as Error).constructor.name);"; echo "}"; } > "$f"
      c=$(codes "$f")
      rm -rf "$D/o"; tsc --pretty false -t es2022 --strict --outDir "$D/o" "$f" > /dev/null 2>&1
      out=$(node "$D/o/c.js" 2>&1)
      if [ -n "$c" ]; then echo "($c) $out"; else echo "$out"; fi
      return ;;
  esac
  c=$(codes "$f"); echo "${c:-OK}"
}
cols=(emit lit n99 nvar keys rev)
declare -A got
printf '%-8s' ""; for col in "${cols[@]}"; do printf ' | %s' "$col"; done; echo
for k in "${kinds[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$k")
  if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $k"; exit 3; fi
  IFS="$T" read -r name decl lit <<< "$k"
  echo "[$name] $decl"
  for col in "${cols[@]}"; do
    v=$(cell "$col" "$decl" "$lit"); got[$name.$col]=$v
    printf '    %-5s %s\n' "$col" "$v"
  done
done
diff=0; total=0
for k in "${kinds[@]}"; do
  IFS="$T" read -r name _ _ <<< "$k"
  [ "$name" = num ] && continue
  for col in "${cols[@]}"; do
    total=$((total+1)); if [ "${got[$name.$col]}" != "${got[num.$col]}" ]; then diff=$((diff+1)); fi
  done
done
echo
echo "숫자 enum 행과 갈린 칸 $diff / $total"
```

```text
===== bash ts30b-enumgrid.sh (sh exit=0) =====
         | emit | lit | n99 | nvar | keys | rev
[num] enum Dir { Up, Down }
    emit  5줄
    lit   OK
    n99   TS2322
    nvar  OK
    keys  ["0","1","Up","Down"]
    rev   "Up"
[str] enum Dir { Up = "UP", Down = "DOWN" }
    emit  5줄
    lit   TS2322
    n99   TS2322
    nvar  TS2322
    keys  ["Up","Down"]
    rev   (TS7053) undefined
[const] const enum Dir { Up, Down }
    emit  0줄
    lit   OK
    n99   TS2322
    nvar  OK
    keys  (TS2475) ReferenceError
    rev   (TS2476) ReferenceError
[declare] declare enum Dir { Up, Down }
    emit  0줄
    lit   OK
    n99   OK
    nvar  OK
    keys  ReferenceError
    rev   ReferenceError
[union] type Dir = 0 | 1;
    emit  0줄
    lit   OK
    n99   TS2322
    nvar  TS2322
    keys  (TS2693) ReferenceError
    rev   (TS2693) ReferenceError
[asconst] const Dir = { Up: 0, Down: 1 } as const; type Dir = (typeof Dir)[keyof typeof Dir];
    emit  1줄
    lit   OK
    n99   TS2322
    nvar  TS2322
    keys  ["Up","Down"]
    rev   (TS7053) undefined

숫자 enum 행과 갈린 칸 19 / 30
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`emit` 열** — 숫자·문자열 enum 은 **5줄**, `as const` 는 **1줄**, 나머지 셋(`const`·`declare`·유니온)은 **0줄**. **값을 남기는 것은 셋뿐**이다.
- ★★ **`lit` 열** — 멤버 값 리터럴(`0` 또는 `"UP"`)을 대입. **`[str]` 만 `TS2322`** — 문자열 enum 은 **자기 값 `"UP"` 조차** `Dir` 로 안 받는다.
- ★★★ **`n99` 열** — 리터럴 `99`. 대부분 **`TS2322`** 인데 **`[declare]` 만 `OK`** 다(7절에서 푼다).
- ★★★ **`nvar` 열** — `const n: number = 99; let v: Dir = n;`. **`[num]`·`[const]`·`[declare]` 가 `OK`** — 숫자 enum 은 **`number` 타입이면 무엇이든** 받는다. 유니온·`as const`·문자열 enum 은 막는다.
- ★★★ **`keys` 열** — `[num]` 은 **`["0","1","Up","Down"]`**(넷), `[str]`·`[asconst]` 는 **`["Up","Down"]`**(둘).
  `[const]`·`[union]` 은 컴파일러가 먼저 막고(`TS2475`·`TS2693`) 방출물은 **`ReferenceError`**. ★★ **`[declare]` 는 진단 없이 `ReferenceError`** — 가장 나쁜 칸이다.
- ★★ **`rev` 열** — `Dir[0]`. **`[num]` 만 `"Up"`**(역매핑). `[str]`·`[asconst]` 는 `TS7053` 에 `undefined`.
- ★★ 마지막 줄 **숫자 enum 행과 갈린 칸 19 / 30** — 다른 다섯 행 × 여섯 열 중 열아홉 칸이 숫자 enum 과 다른 답을 냈다.

```text
  여섯 × 여섯 — 이 판의 격자를 그림으로

             emit  lit     n99     nvar    keys                      rev
  [num]      5줄   OK      TS2322  ★OK     ★["0","1","Up","Down"]    ★"Up"
  [str]      5줄   ★TS2322 TS2322  TS2322  ["Up","Down"]             (TS7053) undefined
  [const]    0줄   OK      TS2322  ★OK     (TS2475) ReferenceError   (TS2476) ReferenceError
  [declare]  0줄   OK      ★★OK    ★OK     ★★ ReferenceError(진단 없음)  ReferenceError
  [union]    0줄   OK      TS2322  TS2322  (TS2693) ReferenceError   (TS2693) ReferenceError
  [asconst]  1줄   OK      TS2322  TS2322  ["Up","Down"]             (TS7053) undefined
```

문자열 enum 의 방출물을 따로 찍어 보면 — 1절 `[str]` 행의 5줄이 이것이다.

```ts
// ex.31c.ts
// 문자열 enum 의 방출물
enum Dir {
    Up = "UP",
    Down = "DOWN",
}
console.log(Object.keys(Dir), Object.values(Dir));
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e31c ex.31c.ts (tsc exit=0) =====
===== 방출된 e31c/ex.31c.js =====
"use strict";
// 문자열 enum 의 방출물
var Dir;
(function (Dir) {
    Dir["Up"] = "UP";
    Dir["Down"] = "DOWN";
})(Dir || (Dir = {}));
console.log(Object.keys(Dir), Object.values(Dir));
```

```text
===== node e31c/ex.31c.js (node exit=0) =====
[ 'Up', 'Down' ] [ 'UP', 'DOWN' ]
```

- ★★ `Dir["Up"] = "UP";` — **바깥 대입이 없다.** 이름 → 값 **한 방향**뿐이라 `Object.keys` 가 둘이다.

비용 — 숫자 enum 의 편의(역매핑 `"Up"`)는 **`keys` 열의 넷**과 **`nvar` 열의 구멍**을 함께 가져온다.

### (2) ★★★ 숫자 enum 의 방출물 — 양방향 대장과 `number` 구멍

**언제 쓰나** — 숫자 enum 을 **순회하거나**(`Object.keys`) **바깥 숫자를 받을 때**.

```ts
// ex.31a.ts
// 숫자 enum 의 방출물 -- 그리고 number 로 들어온 값
enum Dir {
    Up,
    Down,
}
function label(d: Dir): string {
    switch (d) {
        case Dir.Up:
            return "up";
        case Dir.Down:
            return "down";
    }
}
const fromNetwork: number = 7;
console.log("[1]", Object.keys(Dir));
console.log("[2]", Object.values(Dir));
console.log("[3]", Dir[Dir.Up], Dir[fromNetwork]);
console.log("[4]", label(fromNetwork));
console.log("[5]", fromNetwork in Dir, "Up" in Dir, 0 in Dir);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.31a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e31a ex.31a.ts (tsc exit=0) =====
===== 방출된 e31a/ex.31a.js =====
"use strict";
// 숫자 enum 의 방출물 -- 그리고 number 로 들어온 값
var Dir;
(function (Dir) {
    Dir[Dir["Up"] = 0] = "Up";
    Dir[Dir["Down"] = 1] = "Down";
})(Dir || (Dir = {}));
function label(d) {
    switch (d) {
        case Dir.Up:
            return "up";
        case Dir.Down:
            return "down";
    }
}
const fromNetwork = 7;
console.log("[1]", Object.keys(Dir));
console.log("[2]", Object.values(Dir));
console.log("[3]", Dir[Dir.Up], Dir[fromNetwork]);
console.log("[4]", label(fromNetwork));
console.log("[5]", fromNetwork in Dir, "Up" in Dir, 0 in Dir);
```

```text
===== node e31a/ex.31a.js (node exit=0) =====
[1] [ '0', '1', 'Up', 'Down' ]
[2] [ 'Up', 'Down', 0, 1 ]
[3] Up undefined
[4] undefined
[5] false true true
```

그림 해설 — 한 단계에 한 문장.

- ★★ 진단 **0줄**이다. `label(fromNetwork)` 에서 **`number` 가 `Dir` 자리에** 들어갔는데 아무 말이 없다.
- ★★★ 방출물의 핵심은 **한 줄**이다 — `Dir[Dir["Up"] = 0] = "Up";`. 안쪽 `Dir["Up"] = 0` 이 **`0` 을 돌려주고**, 바깥이 **`Dir[0] = "Up"`** 을 한다. **한 줄이 두 방향을 만든다.**
- ★★★ `[1]` **`[ '0', '1', 'Up', 'Down' ]`** — 역매핑 키 `"0"`·`"1"` 이 **먼저** 나온다(정수 키가 앞에 오는 JS 순서).
- ★★ `[2]` **`[ 'Up', 'Down', 0, 1 ]`** — `Object.values` 도 **이름과 숫자가 섞인다.** 「멤버 값 목록」으로 쓰면 틀린다.
- ★★ `[3]` **`Up undefined`** — `Dir[Dir.Up]` 은 역매핑, **`Dir[7]` 은 `undefined`**. 그런데 타입은 `string` 이다(`undefined` 가 안 섞인다).
- ★★★ `[4]` **`undefined`** — `label` 의 반환 타입은 `string` 인데, `switch` 가 **`Up`·`Down` 둘 다 빗나가** 아무것도 안 돌려줬다.
  컴파일러는 `switch` 가 **빠짐없다**고 보고 「끝에 `return` 이 없다」를 안 냈다. **`number` 가 들어온 순간 그 판단이 틀린다.**
- ★ `[5]` **`false true true`** — `7 in Dir` 은 `false` 라 **런타임 검사**로는 쓸 수 있다. 단 **`0 in Dir` 과 `"Up" in Dir` 이 둘 다 `true`** — 이름과 값이 한 객체에 섞여 있다.

```text
  Dir[Dir["Up"] = 0] = "Up";   — 한 줄이 두 번 쓴다

      Dir["Up"] = 0        ─> Dir = { Up: 0 }          (식의 값은 0)
      Dir[ 0 ] = "Up"      ─> Dir = { Up: 0, 0: "Up" } ★ 역매핑

  그래서 Object.keys(Dir) = ["0", "1", "Up", "Down"]   (정수 키가 앞)
```

```text
  number 구멍 — 어디로 새나

  const fromNetwork: number = 7
         │  let v: Dir = n  ─ 통과 (nvar 열)
         ▼
  label(7)  switch: case Up? 아니다 · case Down? 아니다 · 끝
         │  컴파일러: 「빠짐없는 switch」라 판단 → 반환 누락 경고 없음
         ▼
  undefined  ← 타입은 string
```

비용 — **숫자 enum 을 받는 함수는 `number` 를 받는 함수다.** 경계(네트워크·DB)에서 들어온 숫자는 `x in Dir` 같은 **런타임 확인**을 거쳐야 한다.

### (3) ★★★ 판 경계 — 멤버가 아닌 숫자 리터럴

**언제 쓰나** — 「숫자 enum 에는 아무 숫자나 들어간다」는 글을 읽었을 때. **언제의 글인지**가 답을 바꾼다.

```ts
// ex.31b.ts
// 숫자 enum 에 멤버가 아닌 숫자 리터럴을 넣으면
enum Dir {
    Up,
    Down,
}
enum Flag {
    A = 1,
    B = 2,
    C = 4,
}
declare enum Ambient {
    P,
    Q,
}
let d: Dir = 99;
let f: Flag = 3;
let g: Flag = Flag.A | Flag.B;
let a: Ambient = 99;
console.log(d, f, g, a);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.31b.ts (tsc exit=1) =====
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
```

```bash
# ts30b-enumver.sh
#!/usr/bin/env bash
# 같은 파일을 세 판의 tsc 로 던진다 -- 7.0.2 와, 이 머신의 다른 프로젝트에 깔려 있던 5.9.3 · 4.9.5 (읽기만 했다)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
for f in ex.31b.ts; do
  echo "== tsc $(tsc --version)"
  tsc --pretty false --noEmit -t es2022 --strict "$f"
  echo "(exit $?)"
  echo "== node OLD $(node "$OLD" --version)"
  node "$OLD" --pretty false --noEmit -t es2022 --strict "$f"
  echo "(exit $?)"
  echo "== node V49 $(node "$V49" --version)"
  node "$V49" --pretty false --noEmit -t es2022 --strict "$f"
  echo "(exit $?)"
done
echo
echo "---- --erasableSyntaxOnly 를 세 판에 ----"
echo "== tsc"
tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.31b.ts
echo "(exit $?)"
echo "== node OLD"
node "$OLD" --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.31b.ts
echo "(exit $?)"
echo "== node V49"
node "$V49" --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.31b.ts
echo "(exit $?)"
```

```text
===== bash ts30b-enumver.sh (sh exit=0) =====
== tsc Version 7.0.2
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 1)
== node OLD Version 5.9.3
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 2)
== node V49 Version 4.9.5
(exit 0)

---- --erasableSyntaxOnly 를 세 판에 ----
== tsc
ex.31b.ts(2,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(6,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 1)
== node OLD
ex.31b.ts(2,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(6,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.31b.ts(15,5): error TS2322: Type '99' is not assignable to type 'Dir'.
ex.31b.ts(16,5): error TS2322: Type '3' is not assignable to type 'Flag'.
(exit 2)
== node V49
error TS5023: Unknown compiler option '--erasableSyntaxOnly'.
(exit 1)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **7.0.2 와 5.9.3** — 15행 `let d: Dir = 99` 와 16행 `let f: Flag = 3` 이 **`TS2322`**. 진단 두 줄이 **한 글자도 같다.**
- ★★★ **4.9.5 — 진단 0줄, `exit 0`.** 같은 파일이 **통과**한다. 「아무 숫자나 들어간다」는 **4.9 까지의 사실**이다.
- ★★ 16행 `Flag = 3` 은 막히는데 **17행 `Flag.A | Flag.B`(값 3)는 통과**한다 — 비트 조합은 **식**으로 만들면 된다. 리터럴 `3` 만 막힌다.
- ★★ **18행 `let a: Ambient = 99` 는 세 판 다 통과**다 — `declare enum` 은 이 변화에서 **빠져 있다**(7절).
- ★★ **`--erasableSyntaxOnly`** — 7.0.2·5.9.3 은 `enum Dir`·`enum Flag` 에 **`TS1294`** 를 낸다. **`declare enum` 은 안 막는다**(지울 수 있는 선언이라). **4.9.5 는 `TS5023` — 그런 옵션이 없다.**
- ★ 종료 코드 — 진단이 있을 때 7.0.2 는 **`exit 1`**, 5.9.3 은 **`exit 2`** 다. **판의 성질이지 이 주제의 결론이 아니다.**

```text
  판 경계 — 이 머신에서 던진 세 판

                         4.9.5        5.9.3        7.0.2
  let d: Dir = 99        통과         TS2322       TS2322     ← 5.0 「모든 enum 이 유니온」(릴리스 노트)
  let f: Flag = 3        통과         TS2322       TS2322
  Flag.A | Flag.B        통과         통과         통과
  declare enum ← 99      통과         통과         통과
  --erasableSyntaxOnly   TS5023(없음) TS1294       TS1294     ← 5.8 (릴리스 노트)

  ★ 5.0 · 5.8 그 자체는 이 머신에 없다 — 경계가 「4.9.5 와 5.9.3 사이」라는 것까지만 던져서 확인했다
```

비용 — 옛 글의 「enum 에 아무 숫자나」는 **리터럴에 대해서는 낡았고, `number` 변수에 대해서는 지금도 맞다**(1절 `nvar`).

### (4) ★★★ `const enum` 플래그 판 격자 — 인라인되느냐, 객체가 남느냐

**언제 쓰나** — 라이브러리가 `const enum` 을 **내보낼 때**, 또는 프로젝트가 **파일 단위 트랜스파일러**(esbuild·swc·Babel 류)를 쓸 때.

```ts
// lib31.mts
export const enum Level {
    Low = 1,
    High = 2,
}
```

```ts
// use31.mts
import { Level } from "./lib31.mjs";
console.log("use31", Level.High);
```

```ts
// amb31.d.ts
declare const enum Amb {
    K = 7,
}
```

```ts
// useamb31.mts
console.log("useamb31", Amb.K);
```

```js
// jsuser31.mjs
import { Level } from "./lib31.mjs";
console.log("jsuser31", Level.High);
```

```js
// run31.mjs
for (const f of ["./use31.mjs", "./useamb31.mjs", "./jsuser31.mjs"]) {
    try {
        await import(f);
    } catch (e) {
        console.log(f, e.constructor.name, e.message);
    }
}
```

```bash
# ts30b-constflags.sh
#!/usr/bin/env bash
# 같은 네 파일(lib31·use31·amb31.d.ts·useamb31)을 플래그 다섯 판으로 방출하고, 방출물을 node 로 부른다
# 칸: 진단 코드 · lib31.mjs 에 Level 객체가 있나 · use31.mjs 의 출력 줄 · 세 모듈의 실행 결과
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
flags=("" "--isolatedModules" "--verbatimModuleSyntax" "--preserveConstEnums" "--erasableSyntaxOnly")
declare -A got
for fl in "${flags[@]}"; do
  name=${fl:-"(없음)"}
  o="$D/o"; rm -rf "$o"
  diag=$(tsc --pretty false -t es2022 --strict $fl --outDir "$o" lib31.mts use31.mts useamb31.mts amb31.d.ts 2>&1 \
         | grep -o '^[a-z0-9.]*([0-9,]*): error TS[0-9]*' | sed 's/: error / /' | tr '\n' ' ' | sed 's/ $//')
  obj=$(grep -c 'var Level' "$o/lib31.mjs" || true)
  line=$(grep 'console.log' "$o/use31.mjs")
  cp jsuser31.mjs run31.mjs "$o/"
  run=$(cd "$o" && node run31.mjs 2>&1 | tr '\n' '/' | sed 's#/$##')
  got[$name.diag]=${diag:-OK}; got[$name.obj]=$obj; got[$name.line]=$line; got[$name.run]=$run
  echo "[$name]"
  printf '    진단       %s\n' "${diag:-OK}"
  printf '    Level 객체  lib31.mjs 에 %s개\n' "$obj"
  printf '    use31.mjs  %s\n' "$line"
  printf '    node       %s\n' "$run"
done
diff=0; total=0
for fl in "${flags[@]:1}"; do
  for col in diag obj line run; do
    total=$((total+1)); if [ "${got[$fl.$col]}" != "${got[(없음).$col]}" ]; then diff=$((diff+1)); fi
  done
done
echo
echo "플래그 없는 행과 갈린 칸 $diff / $total"
```

```text
===== bash ts30b-constflags.sh (sh exit=0) =====
[(없음)]
    진단       OK
    Level 객체  lib31.mjs 에 0개
    use31.mjs  console.log("use31", 2 /* Level.High */);
    node       use31 2/useamb31 7/./jsuser31.mjs SyntaxError The requested module './lib31.mjs' does not provide an export named 'Level'
[--isolatedModules]
    진단       useamb31.mts(1,25) TS2748
    Level 객체  lib31.mjs 에 1개
    use31.mjs  console.log("use31", Level.High);
    node       use31 2/./useamb31.mjs ReferenceError Amb is not defined/jsuser31 2
[--verbatimModuleSyntax]
    진단       useamb31.mts(1,25) TS2748
    Level 객체  lib31.mjs 에 1개
    use31.mjs  console.log("use31", Level.High);
    node       use31 2/./useamb31.mjs ReferenceError Amb is not defined/jsuser31 2
[--preserveConstEnums]
    진단       OK
    Level 객체  lib31.mjs 에 1개
    use31.mjs  console.log("use31", 2 /* Level.High */);
    node       use31 2/useamb31 7/jsuser31 2
[--erasableSyntaxOnly]
    진단       lib31.mts(1,19) TS1294
    Level 객체  lib31.mjs 에 0개
    use31.mjs  console.log("use31", 2 /* Level.High */);
    node       use31 2/useamb31 7/./jsuser31.mjs SyntaxError The requested module './lib31.mjs' does not provide an export named 'Level'

플래그 없는 행과 갈린 칸 11 / 16
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`(없음)`** — `lib31.mjs` 에 **`Level` 객체 0개**. `use31.mjs` 는 **`2 /* Level.High */`** 로 **숫자가 박혔다.**
  그래서 TS 로 컴파일한 `use31` 은 `2` 를 찍지만, **평범한 JS 소비자 `jsuser31.mjs` 는 `SyntaxError … does not provide an export named 'Level'`** — **내보냈다고 적었는데 방출물에 없다.**
- ★★★ **`--isolatedModules`** — `lib31.mjs` 에 `Level` 객체가 **생겼고**(1개), `use31.mjs` 는 **`Level.High`** 로 **객체를 참조**한다. 인라인이 **꺼졌다.**
  `jsuser31` 도 `2` 를 찍는다. 대신 **`useamb31.mts(1,25) TS2748`**(「Cannot access ambient const enums when 'isolatedModules' is enabled.」) — **`.d.ts` 의 `const enum` 은 값을 줄 방법이 없다.**
  진단을 무시하고 방출하면 `useamb31` 은 **`ReferenceError Amb is not defined`**.
- ★★ **`--verbatimModuleSyntax`** — `--isolatedModules` 와 **네 칸이 한 글자도 같다**(진단 칸에는 **코드만** 찍었다 — 문구는 안 견줬다).
- ★★★ **`--preserveConstEnums`** — 객체는 **남기고**(1개) 쓰는 자리는 **여전히 인라인**(`2 /* Level.High */`). 진단 없음. **세 모듈 다 성공.**
  `--isolatedModules` 와 갈리는 칸은 **진단 · `use31.mjs` 줄 · `node`** 셋이다.
- ★★ **`--erasableSyntaxOnly`** — `lib31.mts(1,19) TS1294` 하나. **방출은 `(없음)` 판과 같다** — 이 플래그는 **검사만** 한다.
  ★ `amb31.d.ts` 의 `declare const enum` 은 **안 걸렸다.**
- ★★ 마지막 줄 **플래그 없는 행과 갈린 칸 11 / 16**.

```text
===== tsc --pretty false -t es2022 --strict --outDir e31f lib31.mts use31.mts useamb31.mts amb31.d.ts (tsc exit=0) =====
===== 방출된 e31f/lib31.mjs =====
export {};
===== 방출된 e31f/use31.mjs =====
console.log("use31", 2 /* Level.High */);
export {};
```

```text
===== tsc --pretty false -t es2022 --strict --isolatedModules --outDir e31i lib31.mts use31.mts useamb31.mts amb31.d.ts (tsc exit=2) =====
useamb31.mts(1,25): error TS2748: Cannot access ambient const enums when 'isolatedModules' is enabled.
===== 방출된 e31i/lib31.mjs =====
export var Level;
(function (Level) {
    Level[Level["Low"] = 1] = "Low";
    Level[Level["High"] = 2] = "High";
})(Level || (Level = {}));
===== 방출된 e31i/use31.mjs =====
import { Level } from "./lib31.mjs";
console.log("use31", Level.High);
===== 방출된 e31i/useamb31.mjs =====
console.log("useamb31", Amb.K);
export {};
```

- ★★ 두 방출물을 나란히 보면 — `(없음)` 판의 `use31.mjs` 는 **`import` 문까지 지워졌다.** 쓸 값이 숫자로 바뀌었으니 가져올 것이 없다.
  `--isolatedModules` 판은 **`import { Level } from "./lib31.mjs";`** 가 **남는다.**

```text
  const enum 이 가는 두 길

  (없음)                 lib31.mjs:  export {};                 ← 객체 없음
                         use31.mjs:  console.log(…, 2 /* … */) ← 숫자 박힘 · import 없음
                         → TS 소비자 OK · ★ JS 소비자 SyntaxError

  --isolatedModules      lib31.mjs:  export var Level; (…)      ← 객체 있음
                         use31.mjs:  import { Level } …; Level.High
                         → 둘 다 OK · ★ .d.ts 의 const enum 은 TS2748
```

- ★★★ **왜 `--isolatedModules` 에서 인라인을 끄나** — 이 플래그는 「**파일 하나만 보고 변환할 수 있는 코드**만 쓰라」는 약속이다.
  `use31.mts` 하나만 보는 도구는 `Level.High` 가 **`2` 인 줄 모른다** — 다른 파일(`lib31.mts`)을 읽어야 안다. 그래서 인라인 대신 **참조**를 남기고, 참조할 객체를 `lib31` 에 **남긴다.**
  `.d.ts` 의 `const enum` 은 **참조할 `.js` 가 애초에 없으니** `TS2748` 로 막는다.
- ★★ 이 판(7.0.2)의 관찰 — `--isolatedModules` 가 **`--preserveConstEnums` 까지 켠 것처럼** 객체를 남겼다. 핸드북은 이 둘의 관계를 문장으로 싣지 않았다 — **던져서 본 것**이다.

비용 — **`const enum` 을 `export` 하는 순간 방출물과 타입이 어긋난다.** 소비자가 TS 로 같은 프로젝트에서 컴파일할 때만 맞는다.
★★★ **「`const enum` 이 빠르다」는 재지 않았다** — 여기서 보인 것은 **방출물의 줄 수**(1절 0줄)와 **인라인 여부**(4절)뿐이다.

### (5) ★ 설정 대조

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.31a.ts    exit 0 = exit 0 · 출력 한 글자도 같다
ex.31b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.31c.ts    exit 0 = exit 0 · 출력 한 글자도 같다
```

- ★★ `--strict` 를 꺼도 **세 파일 다 한 글자도 같다.** enum 의 대입 규칙은 **`strict` 에 안 달렸다.**
- ★ 1·4절 격자는 `--strict` 로만 돌렸다.

비용 — 없다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  enum Dir { Up, Down }                    숫자 enum · 양방향 객체를 방출         (1·2절)
  enum Dir { Up = "UP", Down = "DOWN" }    문자열 enum · 한 방향 객체              (1절)
  const enum Dir { Up, Down }              쓰는 자리에 인라인 · 객체 없음(기본)     (1·4절)
  declare enum Dir { Up, Down }            방출 없음 · 값은 다른 곳이 줘야 한다     (1절)
  type Dir = 0 | 1;                        타입뿐                                  (1절)
  const Dir = {…} as const;                값 한 줄 + 같은 이름의 타입              (1절 · 23편)
  type Dir = (typeof Dir)[keyof typeof Dir];
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| 숫자 enum 에 멤버 아닌 리터럴 `99`·`3` | `TS2322` — **5.9.3·7.0.2** (4.9.5 는 통과) | 1절 `n99` · 3절 |
| 문자열 enum 에 `"UP"` | `TS2322` | 1절 `lit` |
| `const enum` 을 값으로 `Object.keys(Dir)` | `TS2475` | 1절 `keys` |
| `const enum` 에 `Dir[0]` | `TS2476` | 1절 `rev` |
| 타입 이름을 값으로 | `TS2693` | 1절 `[union]` |
| `--isolatedModules` 에서 `.d.ts` 의 `const enum` | `TS2748` | 4절 |
| `--erasableSyntaxOnly` 에서 `enum`·`const enum` | `TS1294` | 3·4절 |

**규칙 불릿**

- ★★★ **숫자 enum 은 양방향 객체를 방출한다** — `Object.keys` 가 **이름과 숫자 키를 둘 다** 낸다(1·2절).
- ★★★ **숫자 enum 은 `number` 타입 값을 받는다** — 리터럴만 5.0 부터 막힌다(1절 `nvar` · 3절).
- ★★ **문자열 enum 은 역매핑이 없고, 자기 값 리터럴도 안 받는다**(1절).
- ★★★ **`const enum` 의 방출은 플래그가 정한다** — 기본은 인라인·객체 없음, `--isolatedModules` 는 참조·객체 있음(4절).
- ★★ **`declare enum` 은 방출물이 없고 진단도 없다** — 값을 채울 책임이 **밖에** 있다(1절).

## 어디서 틀리나

- ★★★ 「**`Object.keys(Dir)` 로 멤버 이름을 얻는다**」 — 숫자 enum 이면 **`["0","1","Up","Down"]`** 이다(2절). 문자열 enum 이면 맞다.
- ★★★ 「**enum 타입 매개변수는 멤버만 받는다**」 — **`number` 변수는 통과**한다(1절 `nvar`). 그리고 빠짐없다고 믿은 `switch` 가 **`undefined` 를 돌려준다**(2절 `[4]`).
- ★★★ 「**숫자 enum 에는 아무 숫자 리터럴이나 넣을 수 있다**」 — **4.9.5 까지**다. 5.9.3·7.0.2 는 `TS2322`(3절).
- ★★★ 「**`const enum` 을 `export` 하면 라이브러리 사용자가 쓸 수 있다**」 — TS 로 **같이** 컴파일하는 사용자만. **JS 소비자는 `SyntaxError`**(4절).
- ★★ 「**`--isolatedModules` 에서도 `const enum` 은 인라인된다**」 — **참조로 바뀐다**(4절). 인라인을 기대한 코드가 **객체를 필요로 하게** 된다.
- ★★ 「**`declare enum` 은 안전한 선언일 뿐**」 — 값을 주는 스크립트가 없으면 **진단 없이 `ReferenceError`**(1절). 그리고 **`99` 를 받는다.**
- ★★ 「**문자열 enum 은 문자열이니 `"UP"` 을 넣어도 된다**」 — **`TS2322`**(1절 `lit`). 문자열 enum 은 **명목적**으로 군다.
- ★ 「**`const enum` 이 더 빠르다**」 — 이 문서는 **재지 않았다.** 줄 수가 0이라는 것과 빠르다는 것은 다른 주장이다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(핸드북)** | 숫자 enum 은 역매핑을 만들고 **문자열 enum 멤버는 역매핑을 안 만든다** | 핸드북 · 1절 `rev` |
| **언어 보장(핸드북)** | `const enum` 은 **컴파일 중에 완전히 제거**되고 쓰는 자리에 인라인된다(기본) | 핸드북 · 4절 `(없음)` |
| **언어 보장(핸드북)** | `.d.ts` 의 `const enum` 은 `isolatedModules` 와 **근본적으로 양립하지 않는다** | 핸드북 · 4절 `TS2748` |
| **언어 보장(핸드북)** | ambient(`declare`) enum 의 초기자 없는 멤버는 **항상 계산된(computed) 멤버**로 본다 | 핸드북 · 1절 `[declare]` 의 `n99` 가 이것으로 읽힌다 |
| **언어 보장(5.0 · 5.8)** | 멤버 영역 밖 리터럴 대입이 에러(5.0) · `--erasableSyntaxOnly` 가 `enum` 을 막는다(5.8) | 릴리스 노트 · 3절 |
| **★ 이 판(7.0.2)의 관찰** | `--isolatedModules` 가 `const enum` 객체를 **남기고 참조로 바꾼다** | 4절 — **던져서** 얻었다 |
| **★ 이 판의 관찰** | `--erasableSyntaxOnly` 가 **`declare const enum` 은 안 막는다** | 4절 |
| **★ 판 격자** | 4.9.5 는 리터럴 `99` 통과 · 5.9.3·7.0.2 는 `TS2322` | 3절 |
| **★ 엔진(node v18)의 관찰** | `Object.keys` 가 정수 키를 먼저 — 이것은 **JS 명세의 키 순서**다 | 2절 · JS 갈래 [`../../../js/syntax/18-for-in-and-enumeration/`](../../../js/syntax/18-for-in-and-enumeration/) |
| **★ 부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | ★★★ `const enum` 의 **실행 속도** · 번들 크기 · 검사 시간 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| **유니온 리터럴** — 값이 **문자열 몇 개**이고 순회가 필요 없을 때 | 런타임에 **목록**이 필요할 때 — 값이 없다(1절 `keys`) |
| **`as const` 객체 + 같은 이름 타입** — 목록도 필요하고 **방출물이 평범한 JS** 여야 할 때 | 역매핑이 꼭 필요할 때 — `TS7053`(1절 `rev`) |
| **문자열 enum** — 로그·직렬화에 **이름이 보여야** 하고 명목성이 필요할 때 | `--erasableSyntaxOnly`(타입 지우기만 하는 실행기)를 쓸 때 — `TS1294` |
| **숫자 enum** — 비트 플래그처럼 **숫자 연산**이 본질일 때 | ★★★ **바깥 숫자를 그대로 받을 때** — `number` 구멍(2절) |
| **`const enum`** — 한 프로젝트 **안에서만** 쓰고 `--isolatedModules` 가 **꺼져 있을 때** | ★★★ **`export` 해서 남에게 줄 때** · 파일 단위 트랜스파일러 — 4절 |
| **`declare enum`** — 값을 주는 스크립트가 **확실히 먼저** 로드될 때 | 그 확신이 없을 때 — **진단 없는 `ReferenceError`** |

```text
  무엇으로 적나 — 1절 격자에서 거꾸로 세운 선택

  런타임에 목록·순회가 필요한가?
    아니오 ──> 유니온 리터럴           (방출 0줄 · number 를 막는다)
    예
      역매핑(값 → 이름)이 필요한가?
        아니오 ──> as const 객체       (방출 1줄 · 키 둘 · number 를 막는다)
        예     ──> 숫자 enum           (키 넷 · number 구멍 — 경계에서 in 으로 확인)
  남에게 export 하나 / 파일 단위 트랜스파일러를 쓰나?
    예 ──> const enum 을 쓰지 않는다   (4절 — JS 소비자 SyntaxError)
```

## 핵심 문장

1. **enum 은 TS 에서 드물게 값을 방출한다 — 종류마다 남는 것이 다르다**(5줄 · 1줄 · 0줄).
2. **숫자 enum 은 양방향 객체라 `Object.keys` 가 넷이고, `number` 변수를 그대로 받는다.**
3. **멤버 아닌 리터럴을 막는 것은 5.0 부터다** — 4.9.5 는 통과시켰다.
4. **`const enum` 의 방출은 플래그가 정한다** — 기본은 인라인·객체 없음이라 **JS 소비자에게 `export` 가 거짓말**이 된다.

## 관련 자료

- [**23번 주제** — `typeof` 타입 연산자](../23-typeof-type-operator/) — ★★★ enum 이 **값이자 타입**이라는 것, 네 이름(`Color`·`typeof Color`·`keyof typeof Color`·`Color.Red`)은 그쪽 4절이 정본이다. **여기는 그 값이 방출물에서 어떤 모양인가부터.**
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — ★★ README 의 선행. 유니온 리터럴·`as const` 의 정본.
- [**30번 주제** — 타입 단언과 non-null `!`](../30-type-assertions-and-non-null/) — 「TS 문법 대부분은 방출물에서 사라진다」. enum 은 그 **예외**다.
- [**33번 주제** — 선언 병합](../33-declaration-merging/) — `enum` 에 `namespace` 를 덧붙이면 `Object.keys` 에 **함수 이름까지** 섞인다.
- [목록의 **36번 주제**](../36-type-only-imports-and-exports/)(타입 전용 import·export) — `--verbatimModuleSyntax`·`--erasableSyntaxOnly` 가 **import 방출**에 주는 영향은 그쪽. 여기서는 `const enum` 칸만 봤다.
- [목록의 **43번 주제**](../43-remaining-tsconfig-choices/)(`tsconfig` 의 나머지 선택) — `--isolatedModules` 의 일반론.
- 파이썬 갈래 [`../../../python/syntax/37-enum/`](../../../python/syntax/37-enum/) — 파이썬 `Enum` 의 멤버는 **싱글턴 객체**다. TS 숫자 enum 의 멤버는 **그냥 숫자**다.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **20번**(`enum` 과 `[Flags]`) — 「열거형이 정수 위의 얇은 껍데기」. TS 숫자 enum 의 `number` 구멍과 **같은 집안**이다. 폴더가 아직 없다.
- Kotlin 갈래 [`../../../kotlin/syntax/24-enum-class-vs-sealed/`](../../../kotlin/syntax/24-enum-class-vs-sealed/) — Kotlin `enum class` 는 **클래스**다. 비교 축은 그쪽.

## 용어 풀이

> **숫자 enum** — 멤버 값이 숫자인 enum. 방출물이 **이름 → 값**과 **값 → 이름**을 둘 다 적는다.\
> 예: 2절 `Dir[Dir["Up"] = 0] = "Up";`.

> **역매핑(reverse mapping)** — 값으로 이름을 찾는 방향. 숫자 enum 에만 있다.\
> 예: 1절 `rev` — `Dir[0]` 이 `"Up"`.

> **`const enum`** — 쓰는 자리에 값을 **인라인**하고 객체를 **안 남기는** enum(기본). 플래그가 이것을 바꾼다.\
> 예: 4절 `(없음)` — `2 /* Level.High */`.

> **`declare enum`(ambient enum)** — 「이 enum 은 어딘가 이미 있다」는 선언. 방출물이 **없다.**\
> 예: 1절 `[declare]` — 진단 없이 `ReferenceError`.

> **`--isolatedModules`** — 파일 하나만 보고 변환할 수 있는 코드만 허용하는 플래그. 파일 단위 트랜스파일러와의 약속이다.\
> 예: 4절 — `const enum` 인라인이 **참조**로 바뀌었다.

> **`--preserveConstEnums`** — `const enum` 의 객체를 방출물에 **남긴다.** 인라인은 그대로다.\
> 예: 4절 — `Level` 객체 1개 · `use31` 은 여전히 `2`.

> **`--erasableSyntaxOnly`** — **지우기만 해서 JS 가 되는** 문법만 허용한다(5.8). `enum`·런타임 코드가 있는 `namespace`·매개변수 프로퍼티를 막는다.\
> 예: 3절 `TS1294`.

> **`TS2748`** — 「Cannot access ambient const enums when 'isolatedModules' is enabled.」\
> 예: 4절 `useamb31.mts(1,25)`.

## 더 들어가면

- **`declare enum` 이 `99` 를 받는 이유** — 핸드북은 「ambient(non-const) enum 에서 초기자 없는 멤버는 **항상 계산된 멤버**로 본다」고 적는다. 5.0 릴리스 노트는 「계산된 멤버마다 **고유 타입**을 만든다」고 적는데,
  이 판에서 `let a: Ambient = 99` 가 **통과**했다 — 두 문장이 **어떻게 맞물려 통과가 나오는지**는 명세 문장으로 확인하지 않았다. **던져서 본 것**이다.
- **`[4]` 의 `switch`** — 반환 누락을 잡고 싶으면 `default: { const never: never = d; throw … }` 꼴로 **빠짐없음을 런타임에도** 확인한다. [**12번 주제**](../12-narrowing/)의 `never` 소진 검사와 같은 모양이다. **여기서는 던지지 않았다.**
- **`as const` 객체의 역매핑** — 필요하면 `Object.fromEntries(Object.entries(Dir).map(([k, v]) => [v, k]))` 로 **명시적으로** 만든다. 방출물에 **숨은 키가 안 생긴다.** 던지지 않았다.
- **5.0 과 5.8 을 직접** — 이 머신에 그 판이 없다. 경계가 **4.9.5 와 5.9.3 사이**라는 것까지만 확인했다.
