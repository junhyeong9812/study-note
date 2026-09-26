# ts/syntax/31 — 열거형의 함정 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **31 은 「`.js` 방출물로 증명하는」 주제다** — enum 은 TS 에서 드물게 **값을 방출하는** 문법이다.
> [**11번 주제**](../11-literal-types-and-as-const/)의 유니온 리터럴·`as const` 와 [**23번 주제**](../23-typeof-type-operator/)의 「enum 은 값이자 타입이다」를 떠올리지 못하면 1·5번이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(경로는 환경변수 `TSC_OLD`·`TSC_49` 로 준다).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`)이다** — 1번 격자와 4번 플래그 격자가 그 자리다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 같은 두 값을 여섯 가지로 선언하면 (예측)

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

- `emit` 열 — 여섯 행의 `.js` 줄 수는 각각 몇인가? **0줄**인 행은 어느 것인가?
- `n99` 열과 `nvar` 열 — `[num]` 행은 각각 무엇인가? `[declare]` 행은?
- `keys` 열 — `[num]` 과 `[str]` 은 각각 무엇을 찍는가?
- 마지막 줄의 수는 몇 / 몇인가?

### 2. 숫자 enum 의 방출물 (예측)

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

- 진단은 몇 줄인가? 방출된 `.js` 에서 `enum Dir` 은 **몇 줄의 무엇**이 되는가?
- `[1]`\~`[5]` 는 각각 무엇을 찍는가? `[4]` 의 `label(7)` 은 `string` 을 돌려주는가?

### 3. 멤버가 아닌 숫자 리터럴을 넣으면 — 세 판 (예측)

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

- 15·16·17·18행 중 7.0.2 에서 막히는 줄은 어느 것인가? 4.9.5 에서는?
- `--erasableSyntaxOnly` 를 주면 세 판이 각각 어떻게 반응하는가?

### 4. `const enum` 을 플래그 다섯 판으로 (예측)

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

- 플래그 없이 방출하면 `lib31.mjs` 에 `Level` 객체가 있는가? 그때 `jsuser31.mjs`(평범한 JS 소비자)는 어떻게 되는가?
- `--isolatedModules` 판에서 `use31.mjs` 의 출력 줄은 어떻게 바뀌는가? 진단은 어디서 나는가?
- `--preserveConstEnums` 판과 `--isolatedModules` 판은 **어느 칸에서** 갈리는가?
- 마지막 줄의 수는 몇 / 몇인가?

### 5. 숫자 enum 의 `Object.keys` (왜)

- 1번 `keys` 열의 `[num]` 과 `[str]` 을 2번 방출물의 **한 줄**로 설명할 수 있는가?

### 6. 리터럴과 `number` 변수 (왜)

- 1번 `[num]` 행의 `n99` 칸과 `nvar` 칸을 견주고, 2번 `[4]` 와 이어서 **그 차이가 실행에서 무엇이 되는지** 말할 수 있는가?

### 7. `declare enum` 의 두 칸 (경계)

- 1번에서 `[declare]` 행의 `n99` 칸과 `keys` 칸을 각각 설명할 수 있는가?

### 8. `const enum` 과 트랜스파일러 (경계)

- 「파일 하나씩 따로 변환하는 도구」 앞에서 `const enum` 이 위험한 이유를 4번의 **어느 두 칸**으로 보일 수 있는가?

### 9. 무엇으로 바꾸나 (경계)

- 1번 격자에서 **유니온 리터럴**과 **`as const` 객체** 행을 근거로, 숫자 enum 을 대신할 때 **얻는 칸과 잃는 칸**을 하나씩 댈 수 있는가?

### 10. 23·11 과, 다른 언어의 enum (연결)

- `[asconst]` 행의 선언은 **같은 이름**을 값과 타입에 한 번씩 쓴다. 이것이 되는 이유는 어느 편의 결론인가?
- 파이썬 `Enum` 과 C# `enum` 중 TS 숫자 enum 과 **런타임 모양이 가까운 쪽**은 어느 것인가?

### 11. 판 경계 (연결)

- 「숫자 enum 에 아무 숫자나 넣을 수 있다」는 **언제까지** 맞는 말인가? 이 머신에서 **어디까지** 확인할 수 있었나?
- `--erasableSyntaxOnly` 는 이 판에 있는가? 없는 판은 무엇이라고 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
