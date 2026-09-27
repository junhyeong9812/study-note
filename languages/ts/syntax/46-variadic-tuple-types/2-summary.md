# ts/syntax/46 — 가변 튜플 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TypeScript 4.0 릴리스 노트 — Variadic Tuple Types · Labeled Tuple Elements](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-0.html) · [4.2 릴리스 노트 — Leading/Middle Rest Elements](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-2.html).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** 「4.0 에 들어왔다」·「4.2 에 들어왔다」는 **이 머신의 3.9.3 · 4.9.5 가 갈리는 모양**으로만 뒷받침한다(4.0·4.2 판 자체는 없다).
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5 · 3.9.3** 을 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`·`TSC_39`** · node 20 은 **`NODE20`**.

```text
===== tsc --version · "$TSC_OLD" · "$TSC_49" · "$TSC_39" --version · node · "$NODE20" --version · google-chrome --version (sh exit=0) =====
Version 7.0.2
Version 5.9.3
Version 4.9.5
Version 3.9.3
v18.19.1
v20.19.6
Google Chrome 151.0.7922.173 
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 「추론 격자」(선언 × 호출 15칸 × 판 넷 — 칸마다 파일 한 장)이다.** 추론된 타입은 눈에 안 보이므로 `const p: null = <호출>;` 로 **일부러 틀리게 받아** `TS2322` 메시지에서 읽는다([19번 주제](../19-generics-basics/)의 탐침).
> ★★ 둘째 창은 **진단 전문**(튜플 꼴의 금지 자리 · 고정 길이에 스프레드) · 셋째는 **방출물 + `node`**(흔적 0).
> ★★★ **46 의 선행은 19 가 아니라 03 이다** — README 는 19(제네릭 기본)를 선행으로 적었지만, **튜플 네 꼴(고정 · 선택 · 나머지 · 레이블)** 은 [03번 주제](../03-basic-type-annotations/) 4절이 이미 쟀다. 여기서는 다시 재지 않고 「**제네릭 `T` 가 튜플로 잡히나 배열로 넓혀지나**」 로 넓힌다 — 그 넓힘을 다루는 것이 19편 2절(「추론은 리터럴로 좁혀지지 않는다」)이라 두 편이 **둘 다** 앞에 선다.
> ★★ JS 쪽 사실 — **나머지 매개변수는 늘 진짜 배열이고 스프레드는 이터러블을 펼친다** — 는 JS 갈래 [11번](../../../js/syntax/11-spread-and-rest/)이 쟀다. 여기서는 그 위에서 「**펼친 것의 길이를 타입이 아나**」 만 본다.
> ★★ 격자 스크립트는 **파일에 안 붙은 진단(`error TS5023` 같은 설정 진단)이 칸에 들면 멈추고, 한쪽 모양만 나오면 멈춘다.** ★ 제출 전에 **가짜 옵션을 끼운 판으로 실제로 멈추는지** 돌렸다(`exit 4`, 1절 끝).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·메시지 속 타입 글자 | 같은 입력·같은 판이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | `node` 출력(3절) | 값만 찍었다 |
| **판에 매인다** | ★ 종료 코드 — 진단 있는 `--noEmit` 이 7.0.2 는 `1`, 5.9.3·4.9.5 는 `2` | 격자는 **타입 글자와 진단 코드로** 갈랐다 |
| **판에 매인다** | ★ 유니온의 **표시 순서** — `(string \| 1 \| 2)[]` 대 `(string \| 2 \| 1)[]` | 뜻은 같다 · 1절 `r14` |
| **★ 부적용 — 실행 창의 값** | 튜플은 **타입만** 있다 — 방출물에 흔적이 없어 `node` 가 볼 것이 **길이와 값뿐**이다(3절) | — |
| **못 잰 것** | 4.0 · 4.2 **바로 그 판**의 동작 | 이 머신에 없다 — 3.9.3(전)과 4.9.5(후)로 **경계 양쪽만** 쟀다 |

## 한눈에 — 쉽게 말하면

가변 튜플은 「칸 수가 정해지지 않은 도시락」이 아니라 「칸 모양을 받는 대로 본뜨는 틀」이다. 넘겨받은 것이 **칸이 나뉜 도시락**(튜플)이면 칸 수와 칸마다의 반찬까지 본뜨고, **한 통에 담긴 반찬**(배열)이면 「몇 칸인지 모름」으로 본뜬다. 틀이 본뜨려면 넘기는 쪽이 **칸을 보여 줘야** 한다 — 그게 `as const` 와 `[...T]` 다.

| 비유 | 실체 |
|---|---|
| 칸 모양을 **본뜨는 틀** | `function f<T extends unknown[]>(...args: T): T` — 인자 목록이 곧 튜플 `[number, string]`(1절 `r01`) |
| ★★★ **한 통에 담긴 반찬**을 부으면 칸 수를 모른다 | `f(...arr)` — `arr` 가 `number[]` 라 결과도 `number[]`(1절 `r02`) |
| ★★★ **칸이 보이는 통**을 부으면 칸째 본뜬다 | `f(...ro)` — `ro` 가 `as const` 라 `[1, 2]`(1절 `r03`) |
| ★★ 틀에 **「칸을 봐라」 표시**를 붙인다 | `arr: [...T]` — 배열 리터럴이 `[number, string]` 로 잡힌다(`r07` 대 `r05`) |
| 칸마다 붙인 **이름 스티커** | 레이블 `[name: string, age?: number]` — 읽기 돕기일 뿐 **모양이 아니다**(2절) |
| 도시락 **뚜껑을 열면** 그냥 반찬들 | 방출물 — `concat(a, b)` 와 `[...a, ...b]` 만 남는다(3절) |

- ★★★ 한 줄로 — 「`T` 가 튜플로 잡히는 것은 인자가 **나머지 매개변수 자리**로 들어오거나, 매개변수 타입이 **`[...T]`** 로 적혔거나, 값이 **`as const`** 일 때다. 셋 다 아니면 배열로 넓혀진다. 그리고 **`as const` 없는 배열을 펼치면 길이 정보가 이미 없다**.」

```text
  T 가 무엇으로 잡히나 — 들어오는 문 셋

  f(1, "a")            나머지 매개변수 자리 ─> 인자 하나하나가 칸 ─> [number, string]
  g([1, "a"])          보통 매개변수 T      ─> 배열 리터럴은 배열 ─> (string | number)[]
  h([1, "a"])          [...T] 로 적은 자리   ─> 칸을 보라는 표시  ─> [number, string]
  f(...arr)            펼친 것이 number[]   ─> 칸 수를 모른다    ─> number[]
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 가변 인자 함수에서 `T` 는 언제 튜플로, 언제 배열로 추론되나** — 선언 × 호출 15칸 × 판 넷(1절).
2. **★★ 튜플 꼴에서 무엇이 막히고 레이블은 무엇을 바꾸나** — 선택 뒤 필수 · 나머지 둘 · 레이블 섞기(2절) · 레이블만 다른 대입.
3. **★★ 이 타입들은 런타임에 무엇을 남기나** — 방출물과 `node`(3절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **추론 격자** | 선언 × 호출 15칸 × 7.0.2 · 5.9.3 · 4.9.5 · 3.9.3 | `TS2322` 메시지 속 타입 글자 | **본체**(1절) |
| ★★ **진단 전문** | 튜플 꼴 넷 · 고정 길이에 스프레드 · 가운데 나머지 호출 | 진단 코드 · `(행,열)` | 2절 |
| ★ **방출물 + `node`** | 가변 튜플을 쓴 함수 하나 | 방출 글자 · 실행 값 | 3절 — **흔적 0** |
| ★ **부적용** | 런타임 값으로 튜플/배열을 가르기 — 둘 다 그냥 배열이다 | — | — |

비용 — 격자 60칸(15 × 판 넷) + 자기검사 · 튜플 꼴 세 판 · 레이블 대입 세 판 · 스프레드 세 판 · 방출 한 판.

### (1) ★★★ 추론 격자 — 선언 × 호출 × 판 넷

**언제 쓰나** — 가변 인자 함수·`concat`·`pipe` 류의 **반환 타입이 튜플로 나올지** 미리 알고 싶을 때. 그리고 **어느 판부터** 그렇게 되는지.

탐침 — 칸마다 파일 한 장이다: 앞머리 두 줄(`const arr = [1, 2];` · `const ro = [1, 2] as const;`) + 선언 한 줄 + `const p: null = <호출>;`.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **마지막 줄 — 7.0.2 에서 튜플 `11 / 15` · 배열 `4 / 15`.** 배열로 넓혀진 넷은 `r02`·`r05`·`r09`·`r14` 다.
- ★★★ **`r02` — `f(...arr)` 는 `number[]`.** `arr` 가 이미 `number[]` 라 펼쳐도 **칸 수가 없다.** 같은 함수에 `as const` 값을 펼친 `r03` 은 `[1, 2]` 다.
- ★★★ **`r05` 대 `r07`** — 같은 배열 리터럴 `[1, "a"]` 가 매개변수를 `T` 로 적으면 `(string | number)[]`, **`[...T]`** 로 적으면 `[number, string]`. 적은 쪽이 「**칸을 봐라**」 를 말한다.
- ★★ **`r09` 대 `r10`** — `concat` 도 같다. 매개변수가 `A`·`B` 면 결과가 `(string | number)[]`, `[...A]`·`[...B]` 면 `[number, string]`.
- ★★ **`r04`·`r08`·`r11` — `[...number[], string]`.** 길이는 몰라도 **끝 칸이 `string`** 인 것은 안다 — 앞 나머지(4.2)가 이 모양을 적게 해 준다.
- ★★★ **판 — 4.0 이후 세 판이 갈린 칸 `2 / 15`.** `r06`(4.9.5 는 `as const` 값을 `unknown[]` 에 못 넘겨 `TS2345`)과 `r14`(유니온의 **표시 순서**만 다름)뿐이다.
- ★★★ **3.9.3 은 `10 / 15` 에서 다르다** — `[...T]` 를 못 읽어 `TS2574` · 가운데 나머지를 못 읽어 `TS1256` · 레이블을 못 읽어 `TS1005`. **4.0 전과 후가 이 격자에서 보인다.**

```text
  배열로 넓혀지는 자리 — 넓히는 것은 호출이 아니라 「값이 이미 가진 타입」이다

  const arr = [1, 2]          ─> number[]          (여기서 이미 칸 수가 사라졌다)
        f(...arr)             ─> number[]          r02
  const ro = [1, 2] as const  ─> readonly [1, 2]
        f(...ro)              ─> [1, 2]            r03
```

- ★ **`r14`·`r15`** — 함수 없이 배열 리터럴에 펼쳐도 같다. `[...ro, "x"]` 는 배열, `as const` 를 붙여야 `readonly [1, 2, "x"]`.

**자기검사** — 격자는 파일에 안 붙은 진단이 칸에 들면 멈춘다. 가짜 옵션을 끼운 판:

```text
===== EXTRA=--bogusOpt bash ts46b-infer46.sh -- 가짜 옵션을 끼운 판 (sh exit=4) =====
[r01] declare function f<T extends unknown[]>(...args: T): T;
      p = f(1, "a")
★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: TS5023 
```

- ★★ 이 검사가 막는 것 — 설정 진단(`TS5023`·`TS5112`)이 **모든 칸에 똑같이** 들면 칸마다 「탐침 진단 없음」이 찍히고 격자가 **조용히 거짓 결론**을 낸다.
- ★★★ **자기검사가 못 막은 사고가 하나 있었다** — 첫 판은 구분자를 **탭**으로 썼는데, 선언이 빈 `r14`·`r15` 에서 `read` 가 **연속 탭을 하나로 접어** 호출 식이 선언 칸으로 밀렸다. 칸 수 검사(`awk`)는 3을 세어 통과했고 두 칸이 「기타 · `TS1109`」로 찍혔다. **구분자를 US(`0x1f`)로 바꾸자** 둘 다 튜플/배열로 돌아왔다 — `IFS` 공백 문자는 빈 칸을 접는다(규칙 32 의 같은 집안).

### (2) ★★ 튜플 꼴의 금지 자리 — 그리고 레이블은 타입이 아니다

**언제 쓰나** — 튜플 타입을 손으로 적을 때 **선택·나머지·레이블의 자리**를 헷갈렸을 때.

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

- ★★ **선택 뒤 필수** `TS1257` · **나머지 뒤 나머지** `TS1265` · **나머지 뒤 선택** `TS1266` — 세 판이 같다.
- ★★★ **레이블 섞기(`T4`)는 판이 가른다** — 4.9.5 만 `TS5084`, 5.9.3·7.0.2 는 **받는다.** 「전부 달거나 전부 안 달거나」는 4.x 의 규칙이지 지금 규칙이 아니다(어느 판에서 풀렸는지는 이 머신의 판으로는 5.x 어딘가까지만 좁혀진다).
- ★ `TS5084` 는 **`TS5` 로 시작하지만 파일에 붙은 진단**이다(`vt46a.ts(5,23)`). 격자의 설정 진단 거름망을 「`error TS5` 가 있으면 멈춤」으로 짰다면 여기서 **거짓으로 멈췄다** — 그래서 거름망은 **파일 이름 없이 시작하는 줄**(`^error TS`)만 본다.

레이블만 다른 튜플끼리:

```ts
// vt46b.ts
// 레이블만 다른 튜플끼리 대입한다
const pt: [x: number, y: number] = [1, 2];
const size: [w: number, h: number] = pt;
const bare: [number, number] = size;
const back: [x: number, y: number] = bare;
declare function move(...args: [x: number, y: number]): void;
move(...size);
export {};
```

```text
===== tsc · "$TSC_OLD" · "$TSC_49" --pretty false --noEmit --strict -t es2022 vt46b.ts (sh exit=0) =====
---- 7.0.2
(exit 0)
---- 5.9.3
(exit 0)
---- 4.9.5
(exit 0)
```

- ★★★ **세 판 다 `exit 0` · 진단 0줄.** `[x, y]` ↔ `[w, h]` ↔ `[number, number]` 가 서로 대입된다. **레이블은 모양의 일부가 아니다** — 읽는 사람과 편집기 도움말(`Parameters<…>` 의 표시)을 위한 이름이다(1절 `r13` 이 레이블째 찍힌다).

고정 길이 나머지 매개변수 · 가운데 나머지에 넘기기:

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

- ★★★ **`two(...arr)` 가 `TS2556`** — `arr` 는 `number[]` 라 「두 개」인지 모른다. **`two(...ro)` 는 통과**한다. 1절 `r02`/`r03` 의 **진단 쪽 얼굴**이다.
- ★★ **가운데 나머지** `[string, ...number[], boolean]` — `m("a", true)`(가운데 0개) · `m("a", 1, 2, true)` 통과, `m("a", 1)` 은 끝 칸이 `boolean` 이 아니라 `TS2345`. 메시지가 「**0번 자리의 `number` 가 1번 자리의 `boolean` 에 안 맞는다**」 고 칸 번호로 말한다.
- ★ **`m("a", ...arr, true)` 는 통과** — 길이 모르는 배열도 **가운데 나머지 칸**에는 들어간다.

### (3) ★ 방출물에는 흔적이 없다

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

- ★★ 타입 매개변수 `<A, B>` · 반환 타입 `[...A, ...B]` · `type Pair` · 레이블이 **전부 사라졌다.** 남은 것은 JS 스프레드 `[...a, ...b]` 뿐이다 — [01번 주제](../01-what-ts-adds-and-erases/)의 「지우는 것」 그대로.
- ★ `node` 가 본 것은 `["k",1,true] 3` — **길이 3인 보통 배열**이다. 타입이 말한 `[string, number, boolean]` 을 런타임이 **확인하지 않는다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function f<T extends unknown[]>(...args: T): T             나머지 자리의 T — 인자 목록이 튜플로   (1절 r01)
  function h<T extends unknown[]>(arr: [...T]): T            [...T] — 배열 리터럴을 튜플로           (1절 r07)
  function c<A extends unknown[], B extends unknown[]>(a: [...A], b: [...B]): [...A, ...B]   튜플 잇기 (1절 r10)
  [string, ...number[], boolean]                             가운데 나머지 (4.2 이후)                (1절 r12 · 2절)
  [name: string, age?: number]                               레이블 튜플 (4.0 이후)                  (1절 r13 · 2절)
  Parameters<typeof fn>                                      나머지 매개변수의 튜플을 꺼낸다         (1절 r12·r13)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 판 |
|---|---|---|
| `[a?: string, b: number]` | `TS1257` | 세 판 |
| `[...string[], ...number[]]` | `TS1265` | 세 판 |
| `[...number[], string?]` | `TS1266` | 세 판 |
| `[a: string, number]` | `TS5084` | **4.9.5 만** — 5.9.3·7.0.2 는 통과 |
| `two(...arr)` (`arr: number[]`, 매개변수 `[number, number]`) | `TS2556` | 세 판 |
| `arr: [...T]` 를 3.9.3 에 | `TS2574` | 3.9.3 |

**규칙 불릿**

- ★★★ **`T extends unknown[]` 은 나머지 매개변수 자리이거나 `[...T]` 로 적혀야 튜플로 잡힌다** — 보통 매개변수 `T` 에 배열 리터럴을 주면 배열이다(1절).
- ★★★ **`as const` 없는 배열을 펼치면 `number[]`** — 칸 수는 값을 선언할 때 이미 사라졌다(1절 `r02` · 2절 `TS2556`).
- ★★ **레이블은 대입 가능성에 영향이 없다** — 이름이 달라도, 없어도 대입된다(2절).
- ★★ **나머지는 하나만, 선택은 나머지 앞에, 필수는 선택 앞에** — `TS1265`·`TS1266`·`TS1257`(2절).
- ★ **방출물에는 아무것도 없다** — 타입이 약속한 길이를 런타임이 지키게 하지 않는다(3절).

## 어디서 틀리나

- ★★★ 「**가변 튜플이면 스프레드 결과도 튜플이다**」 — 펼치는 값이 `number[]` 면 결과는 `number[]` 다(1절 `r02`). 튜플을 원하면 값을 `as const` 로 선언하거나 튜플 타입으로 적는다.
- ★★★ 「**`T extends unknown[]` 을 달았으니 튜플로 잡힌다**」 — 제약은 **상한**일 뿐이다. 보통 매개변수 `T` 에 배열 리터럴은 `(string | number)[]`(1절 `r05`). `[...T]` 가 튜플로 잡게 한다.
- ★★ 「**`concat(a, b): [...A, ...B]` 면 결과가 튜플이다**」 — 매개변수를 `A`·`B` 로 적으면 `(string | number)[]`(1절 `r09`). 반환 타입이 아니라 **매개변수 쪽**이 튜플 추론을 켠다.
- ★★ 「**레이블이 다르면 다른 타입이다**」 — 세 판 모두 대입된다(2절).
- ★★ 「**레이블은 전부 달거나 전부 빼야 한다**」 — 4.9.5 까지의 규칙이다. 5.9.3·7.0.2 는 섞어도 받는다(2절).
- ★ 「**`readonly` 튜플은 `T extends unknown[]` 에 못 넘긴다**」 — 4.9.5 에서는 `TS2345` 였고 5.9.3·7.0.2 는 받아 `[1, "a"]` 로 잡는다(1절 `r06`).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **JS(런타임)** | 나머지 매개변수는 배열 · 스프레드는 펼친다 · 길이 검사 없음 | 3절 · JS 11편 |
| **★★★ TS 타입 시스템(4.0 이후 판 공통)** | 나머지 자리·`[...T]`·`as const` 에서 튜플 추론 · 금지 자리 셋 | 1절 `2 / 15` · 2절 |
| **★★ 판에 매인 규칙** | 레이블 섞기(4.9.5 `TS5084`) · `readonly` 튜플을 `unknown[]` 제약에(4.9.5 `TS2345`) | 1·2절 |
| **★ 판에 매인 표시** | 유니온 원소의 표시 순서 | 1절 `r14` — 뜻은 같다 |
| **4.0 · 4.2 경계** | 3.9.3 이 `[...T]`·가운데 나머지·레이블을 못 읽는다 | 1절 — **경계 판 자체는 못 잼** |
| **출처 확인 못 함** | 「4.0 에서」「4.2 에서」 들어왔다는 릴리스 노트 문장 | 외부 문서를 열지 않았다 |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **인자 목록 전체를 타입으로 받을 때** `(...args: T)` — 래퍼·`bind`·이벤트 방출기 | 인자 개수가 정해진 함수에 굳이 `T extends unknown[]` |
| ★★★ **배열 리터럴을 튜플로 받고 싶으면 `[...T]`** | `T` 로 적고 호출하는 쪽에 `as const` 를 강요하기 |
| ★★ **튜플 잇기 `[...A, ...B]`** — `concat`·`prepend` 의 반환 타입 | 매개변수를 `A`·`B` 로 적은 채 반환만 `[...A, ...B]`(1절 `r09`) |
| ★★ **레이블** — 매개변수 이름이 편집기 도움말에 나오게 | 레이블로 두 튜플을 **구별**하려 하기 — 구별이 안 된다(2절) |
| ★ 가운데 나머지 `[string, ...number[], boolean]` — 「끝이 콜백」 꼴 | 나머지 둘 · 나머지 뒤 선택 — 막힌다 |

## 핵심 문장

1. **`T` 가 튜플로 잡히는 문은 셋이다 — 나머지 매개변수 자리 · `[...T]` 로 적은 매개변수 · `as const` 값.** 셋 다 아니면 배열로 넓혀진다(7.0.2 튜플 `11 / 15`).
2. **`as const` 없는 배열을 펼치면 `number[]` 다** — 칸 수는 그 배열을 선언할 때 이미 사라졌고, 고정 길이 매개변수에 넘기면 `TS2556` 이다.
3. **레이블은 타입이 아니다** — 이름만 다른 튜플끼리 세 판 모두 대입된다. 레이블 섞기는 4.9.5 만 막았다.
4. **4.0 이후 세 판은 이 격자에서 거의 같다(`2 / 15`)** — 갈린 두 칸은 4.9.5 의 `readonly` 규칙과 유니온 표시 순서다. 3.9.3 은 `10 / 15` 에서 다르다.
5. **튜플 타입은 방출물에 흔적이 없다** — 약속한 길이를 런타임은 확인하지 않는다.

## 관련 자료

- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) 4절 — ★★★ **튜플 네 꼴의 정본.** 그쪽은 **모양**까지, 여기는 **제네릭 추론**부터.
- [**19번 주제** — 제네릭 기본](../19-generics-basics/) 2절 — README 의 선행. 「추론은 리터럴로 좁혀지지 않는다」가 1절 `r05` 의 넓힘이다.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) · [**21번 주제** — `const` 타입 매개변수](../21-inference-control-const-and-noinfer/) — `as const` 를 **부르는 쪽**이 적느냐 **받는 쪽**이 적느냐. 여기서는 받는 쪽의 `[...T]` 만 쟀다.
- [**28번 주제** — 유틸리티 타입](../28-utility-types/) — `Parameters<…>` 의 정본.
- JS 갈래 [**11번** — 스프레드와 나머지](../../../js/syntax/11-spread-and-rest/) — 런타임 의미의 정본. 그쪽은 **값**, 여기는 **길이를 타입이 아나.**
- [**01번 주제**](../01-what-ts-adds-and-erases/) — 3절의 「지운다」.

## 용어 풀이

> **가변 튜플 타입(variadic tuple type)** — 튜플 안에 제네릭 스프레드 `...T` 가 들어간 타입. `[...A, ...B]` 처럼 **길이를 모르는 튜플을 이어 붙일 수 있다.**\
> 예: 1절 `r10` 의 `[number, string]`.

> **나머지 요소(rest element)** — 튜플 안의 `...X[]`. 그 자리에 0개 이상이 온다. 한 튜플에 **하나만.**\
> 예: 2절 `[string, ...number[], boolean]`.

> **레이블 튜플(labeled tuple)** — 칸마다 이름을 단 튜플 `[name: string, age?: number]`. 이름은 **표시용**이다.\
> 예: 1절 `r13`.

> **`[...T]` 표기** — 매개변수 타입을 `T` 대신 `[...T]` 로 적어 「**튜플로 추론해 달라**」 는 신호를 주는 것.\
> 예: 1절 `r07`.

> **`TS2556`** — 「A spread argument must either have a tuple type or be passed to a rest parameter.」 — 길이 모르는 배열을 고정 길이 자리에 펼쳤다.\
> 예: 2절 `two(...arr)`.

> **`TS5084`** — 4.9.5 의 「Tuple members must all have names or all not have names.」 — `TS5` 로 시작하지만 **파일에 붙은** 진단이다.\
> 예: 2절 `T4`.

## 더 들어가면

- **`pipe`·`compose` 의 타입** — 가변 튜플을 재귀 조건부 타입과 엮는 길([25번 주제](../25-infer-and-recursive-conditional-types/)). 깊어지면 45편의 `TS2589` 벽에 닿는다 — **여기서는 재지 않았다.**
- **4.0 · 4.2 바로 그 판** — 이 머신에 없어 경계 양쪽(3.9.3 · 4.9.5)만 쟀다.
