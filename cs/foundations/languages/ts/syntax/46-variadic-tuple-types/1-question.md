# ts/syntax/46 — 가변 튜플 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **46 은 03 과 19 에서 온다** — 튜플 네 꼴은 [**03번 주제**](../03-basic-type-annotations/) 4절, 제네릭 추론의 넓힘은 [**19번 주제**](../19-generics-basics/) 2절이 쟀다.
> 추론된 타입은 `const p: null = <식>;` 의 `TS2322` 메시지에서 읽는다 — **그 메시지가 답**이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5 · 3.9.3** 을 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`·`TSC_39`).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 선언 × 호출 열다섯 칸 (예측)

- 아래 격자 스크립트의 칸마다 7.0.2 가 `p` 의 타입을 무엇으로 말하는가? 튜플 모양과 배열 모양은 각각 몇 칸인가?

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

### 2. 같은 격자를 판 넷에 (예측)

- 1번 격자를 5.9.3 · 4.9.5 · 3.9.3 에도 던지면 7.0.2 와 **글자까지** 다른 칸은 어느 것인가? 3.9.3 이 다른 칸은 어떤 진단을 함께 내는가?

### 3. 튜플 꼴 넷 (예측)

- 아래를 세 판(7.0.2 · 5.9.3 · 4.9.5)에 `--noEmit --strict` 로 던지면 줄마다 무엇이 나는가?

```ts
// vt46a.ts
// 튜플 꼴 넷 -- 선택 요소 · 나머지 요소 · 레이블의 자리
type T1 = [a?: string, b: number];
type T2 = [...string[], ...number[]];
type T3 = [...number[], string?];
type T4 = [a: string, number];
export {};
```

### 4. 레이블만 다른 대입 (예측)

- 아래를 세 판에 던지면 진단은 몇 줄이고 종료 코드는 무엇인가?

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

### 5. 고정 길이 자리와 가운데 나머지 (예측)

- 아래 여섯 호출 가운데 막히는 것은 어느 줄이고 코드는 무엇인가? 세 판의 출력은 같은가?

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

### 6. 방출물과 실행 (예측)

- 아래를 7.0.2 로 방출하면 `.js` 에 무엇이 남고 `node` 는 무엇을 찍는가?

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

### 7. `r02` 와 `r03` 을 가른 것 (왜)

- 1번의 `r02` 와 `r03` 은 같은 함수 `f` 를 부른다. 두 칸의 답을 가른 것은 **호출**인가 **펼친 값의 선언**인가?

### 8. `[...T]` 한 표기 (왜)

- 1번의 `r05` 와 `r07` 은 제약이 같다. 매개변수 타입을 `[...T]` 로 적는 것은 컴파일러에게 무엇을 말하는가?

### 9. `c1` 과 `c2` (경계)

- 1번의 `c1` 과 `c2` 는 반환 타입이 같다. 추론을 켜고 끄는 것은 선언의 어느 자리인가?

### 10. 설정 진단 거름망 (왜)

- 격자 스크립트는 왜 「`error TS5` 라는 글자」가 아니라 **파일 이름 없이 시작하는 `error TS` 줄**을 보고 멈추게 짰나?

### 11. 03편·JS 11편과 잇기 (연결)

- 03편 4절은 `sum(...xs: [string, ...number[]])` 를 적었고 JS 갈래 11편은 나머지 매개변수가 늘 진짜 배열임을 쟀다. 이 주제는 두 편 사이의 어느 빈칸을 채웠나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
