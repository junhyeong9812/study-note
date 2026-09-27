# ts/syntax/36 — 타입 전용 import·export — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **36 은 35 에서 온다** — [**35번 주제**](../35-module-resolution/)는 import 가 **풀리나**를 물었다. 여기는 풀린 import 가 **방출물에 남나**다.
> [**02번 주제**](../02-type-checking-vs-emit/) 5·6절이 `TS1205`·`TS1484` 와 node 의 `SyntaxError` 를, [**31번 주제**](../31-enum-pitfalls/)가 두 플래그의 `const enum` 쪽을 이미 쟀다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. import/export 꼴들을 플래그마다 방출하면 (예측)

```ts
// lib36.mts
console.log("lib36 evaluated");
export interface Shape {
    area: number;
}
export const version = 1;
```

```ts
// i36a.mts
import { Shape } from "./lib36.mjs";
const s: Shape = { area: 1 };
```

```ts
// i36b.mts
import type { Shape } from "./lib36.mjs";
const s: Shape = { area: 1 };
```

```ts
// i36c.mts
import { type Shape } from "./lib36.mjs";
const s: Shape = { area: 1 };
```

```ts
// i36d.mts
import "./lib36.mjs";
```

```ts
// i36e.mts
export type { Shape } from "./lib36.mjs";
```

```ts
// i36f.mts
export { Shape } from "./lib36.mjs";
```

```ts
// i36g.mts
import { version } from "./lib36.mjs";
```

```ts
// i36h.mts
import { type Shape, version } from "./lib36.mjs";
const s: Shape = { area: version };
```

```bash
# ts34b-emit36.sh
#!/usr/bin/env bash
# i36a~h 여덟 파일 × 플래그 넷 -- 방출물에 남은 import/export 줄 · 진단 · 그 방출물을 node 로 돌린 출력
# 방출물은 파일마다 node 프로세스를 따로 띄운다(ESM 은 한 프로세스에서 lib36 을 한 번만 평가한다)
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
modes=("" "--isolatedModules" "--verbatimModuleSyntax" "--erasableSyntaxOnly")
files=(i36a i36b i36c i36d i36e i36f i36g i36h)
for i in "${!modes[@]}"; do
  o="$D/o$i"
  # shellcheck disable=SC2086
  tsc --pretty false -t es2022 --strict --module nodenext ${modes[$i]} --outDir "$o" lib36.mts "${files[@]/%/.mts}" > "$D/diag$i" 2>&1
done
cell() {                       # cell <모드번호> <파일>
  local o="$D/o$1" f=$2 kept diag run
  kept=$(grep -E '^(import|export)' "$o/$f.mjs" | tr '\n' ' ' | sed 's/ $//')
  diag=$(grep -o "^$f.mts([0-9,]*): error TS[0-9]*" "$D/diag$1" | sed "s/^$f.mts//; s/: error / /" | tr '\n' ' ' | sed 's/ $//')
  run=$(cd "$o" && node "$f.mjs" 2>&1 | grep -E '^(lib36 evaluated|[A-Za-z]*Error)' | tr '\n' ' ' | sed 's/ $//')
  printf '줄 %s · 진단 %s · node %s' "${kept:-(없음)}" "${diag:-OK}" "${run:-(출력 없음)}"
}
names=("끔" "isolatedModules" "verbatimModuleSyntax" "erasableSyntaxOnly")
declare -a diff_count=(0 0 0 0)
total=0
for f in "${files[@]}"; do
  echo "[$f] $(head -1 "$f.mts")"
  base=$(cell 0 "$f")
  for i in "${!modes[@]}"; do
    c=$(cell "$i" "$f")
    printf '    %-22s %s\n' "${names[$i]}" "$c"
    [ "$c" != "$base" ] && diff_count[$i]=$((diff_count[$i]+1))
  done
  total=$((total+1))
done
echo
echo "끔과 갈린 칸 -- isolatedModules ${diff_count[1]} / $total · verbatimModuleSyntax ${diff_count[2]} / $total · erasableSyntaxOnly ${diff_count[3]} / $total"
```

- 서른두 칸 각각의 「남은 줄 · 진단 · node」는? 마지막 줄의 세 수는?

### 2. 이름 안쪽의 `type` 하나 (예측)

- 1번의 `i36c` 를 `--verbatimModuleSyntax` 로 방출하면 방출물의 첫 줄은 무엇이고, node 로 돌리면 무엇이 찍히는가? 기본 설정에서는?

### 3. 안 쓰는 값 import (예측)

- 1번의 `i36g` 를 기본 설정과 `--verbatimModuleSyntax` 로 각각 방출해 node 로 돌리면, `lib36` 의 첫 줄은 각각 실행되는가?

### 4. `erasableSyntaxOnly` 와 import/export 꼴 (예측)

```ts
// kit36.d.mts
export declare class Box {
    v: number;
}
```

```ts
// box36.d.cts
declare class Box {
    v: number;
}
export = Box;
```

```bash
# ts34b-erase36.sh
#!/usr/bin/env bash
# import/export 꼴 여섯 × 세 판 -- --erasableSyntaxOnly --module nodenext 에서의 진단
# 가져올 곳은 선언 파일 둘(kit36.d.mts 는 ESM, box36.d.cts 는 export = 을 쓰는 CJS)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
cp kit36.d.mts box36.d.cts "$D/"
T=$'\t'
probes=(
  "import-type-named${T}mts${T}import type { Box } from \"./kit36.mjs\"; let b: Box | undefined; export {};"
  "import-inline-type${T}mts${T}import { type Box } from \"./kit36.mjs\"; let b: Box | undefined; export {};"
  "export-type${T}mts${T}export type { Box } from \"./kit36.mjs\";"
  "import-equals-require${T}cts${T}import Box = require(\"./box36.cjs\"); console.log(new Box().v);"
  "import-type-equals-require${T}cts${T}import type Box = require(\"./box36.cjs\"); let b: Box | undefined; export {};"
  "export-equals${T}cts${T}const n = 1; export = n;"
)
codes() { grep -o '([0-9,]*): error TS[0-9]*' | sed 's/: error / /' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-28s %-16s %-16s %s\n' "탐침" "7.0.2" "5.9.3" "4.9.5"
hit=0; total=0
for p in "${probes[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$p")
  if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $p"; exit 3; fi
  IFS="$T" read -r name ext src <<< "$p"
  echo "$src" > "$D/c.$ext"
  fl=(--pretty false --noEmit -t es2022 --strict --module nodenext --erasableSyntaxOnly "c.$ext")
  a=$(cd "$D" && tsc "${fl[@]}" 2>&1 | codes)
  b=$(cd "$D" && node "$OLD" "${fl[@]}" 2>&1 | codes)
  c=$(cd "$D" && node "$V49" "${fl[@]}" 2>&1 | grep -o 'error TS[0-9]*' | sed 's/^error //')
  rm -f "$D/c.$ext"
  printf '%-28s %-16s %-16s %s\n' "$name" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1)); case $a in *TS1294*) hit=$((hit+1)) ;; esac
done
echo
echo "7.0.2 에서 TS1294 가 난 탐침 $hit / $total"
```

- 여섯 꼴 × 세 판은? 마지막 줄의 수는?

### 5. `type` 을 붙인 `require` import (예측)

```ts
// eqtype36.cts
import type Box = require("./box36.cjs");
let b: Box | undefined;
export {};
```

- 이 파일을 `--module nodenext` 로 방출하면 `.cjs` 에 import 의 흔적이 남는가? `--erasableSyntaxOnly` 를 주면?

### 6. 옛 import 플래그를 판마다 (예측)

```bash
# ts34b-flags36.sh
#!/usr/bin/env bash
# import 방출에 걸린 플래그 여섯 × 세 판 -- 받아들이나(OK) · 진단 코드
# 파일은 export 한 줄짜리 z36.mts -- 플래그의 존재만 묻는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
echo 'export const z = 1;' > "$D/z36.mts"
T=$'\t'
rows=(
  "isolatedModules${T}--isolatedModules"
  "importsNotUsedAsValues${T}--importsNotUsedAsValues preserve"
  "preserveValueImports${T}--preserveValueImports"
  "verbatimModuleSyntax${T}--verbatimModuleSyntax"
  "erasableSyntaxOnly${T}--erasableSyntaxOnly"
  "rewriteRelativeImportExtensions${T}--rewriteRelativeImportExtensions"
)
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-34s %-10s %-10s %s\n' "플래그" "7.0.2" "5.9.3" "4.9.5"
split=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r")
  if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r name flag <<< "$r"
  # shellcheck disable=SC2086
  a=$(cd "$D" && tsc --pretty false --noEmit --module nodenext $flag z36.mts 2>&1 | codes)
  b=$(cd "$D" && node "$OLD" --pretty false --noEmit --module nodenext $flag z36.mts 2>&1 | codes)
  c=$(cd "$D" && node "$V49" --pretty false --noEmit --module nodenext $flag z36.mts 2>&1 | codes)
  printf '%-34s %-10s %-10s %s\n' "$name" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1)); { [ "$a" != "$b" ] || [ "$b" != "$c" ]; } && split=$((split+1))
done
echo
echo "세 판이 한 답이 아닌 행 $split / $total"
```

- 여섯 행 × 세 판은? 마지막 줄의 수는?

### 7. 같은 진단, 다른 방출물 (왜)

- 1번의 `i36f` 에서 `isolatedModules` 와 `verbatimModuleSyntax` 는 같은 진단을 내는데 방출물이 다르다. 두 플래그가 각각 **무엇을 약속**하는 플래그이기에 그런가?

### 8. `import type` 이 줄이는 것 (경계)

- 「`import type` 을 쓰면 방출물이 줄어든다」 — 1번 격자의 **어느 칸 둘**을 견주면 이 문장의 참·거짓이 갈리는가? 어느 설정에서 참이 되는가?

### 9. `erasableSyntaxOnly` 가 보는 것 (경계)

- 34편 3절은 「방출 줄이 있다」와 「`TS1294`」가 6 / 6 같았다. 5번은 그 규칙의 **반례**인가? 그렇다면 이 플래그는 무엇을 보고 막는가?

### 10. 02·31·34 와 잇기 (연결)

- 1번의 `i36a` × `verbatimModuleSyntax` 칸은 02편 6절의 어느 블록과 같은 칸인가?
- 1번 마지막 줄의 `erasableSyntaxOnly` 수는 31편 4절의 어느 관찰과 같은 성질인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
