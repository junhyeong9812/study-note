# ts/syntax/36 — 타입 전용 import·export — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `verbatimModuleSyntax`](https://www.typescriptlang.org/tsconfig/#verbatimModuleSyntax)(타입 전용 import 는 지우고 값 import 는 그대로 둔다 · `import { type A } from "a"` 는 **`import {} from "a"`** 로 다시 쓰인다 · `importsNotUsedAsValues`·`preserveValueImports` 를 대체) ·
> [TypeScript 5.8 릴리스 노트 — `--erasableSyntaxOnly`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 본판은 아래다. ★ 판 격자에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.
> **버전** — `import { type T }`(이름 앞 `type`)는 **4.5**, `verbatimModuleSyntax` 는 **5.0**, `erasableSyntaxOnly` 는 **5.8**(각 릴리스 노트). ★ 이 머신에서 판 경계를 던져 본 것은 **4.9.5 · 5.9.3 · 7.0.2 세 판뿐이다** — 4.5·5.0·5.8 그 자체는 없다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(방출된 `.js` + `node`)이다 — 방출 격자로 센다.**
> 파일 여덟 × 플래그 넷에서 **방출물에 남은 import/export 줄**과 **그 방출물을 node 로 돌린 출력**을 한 칸에 담았다(1절). 「타입 전용 import 가 무엇을 줄이나」는 **방출물의 줄로만** 말한다 — 번들 크기는 재지 않았다.
> ★★★ **36 은 35 에서 온다.** [**35번 주제**](../35-module-resolution/)는 「import 가 **풀리나**」를 물었다 — 여기는 「풀린 import 가 **방출물에 남나**」다.
> ★★★ **이미 잰 것은 다시 안 잰다** — [**02번 주제**](../02-type-checking-vs-emit/) 6절이 `verbatimModuleSyntax` 에서 타입을 값 import 하면 **`TS1484` + 방출물에 그대로 남아 node 가 `SyntaxError`** 인 것을 쟀고, 5절이 `isolatedModules` 의 **`TS1205`** 를 쟀다.
> [**31번 주제**](../31-enum-pitfalls/) 4절은 두 플래그가 **`const enum`** 을 인라인 대신 참조로 바꾸는 것을, 3절은 `erasableSyntaxOnly` 의 판 격자(7.0.2·5.9.3 `TS1294`, 4.9.5 `TS5023`)를 쟀다. **여기서는 import/export 쪽 칸만** 센다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 방출 격자의 칸(남은 줄 · 진단 · node)과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | node 출력 | 파일마다 **node 프로세스를 따로** 띄웠다 — ESM 은 한 프로세스에서 모듈을 **한 번만** 평가하므로 섞으면 칸끼리 샌다(규칙 22) |
| **안 흔들린다** | ★★ 판 격자 둘의 칸 | 세 판 대조 |
| **판에 매인다** | 종료 코드 | 격자는 **진단 코드로** 갈랐다 |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | 질문은 **`.js` 에 import 줄이 남나**다 |
| **안 잰 것** | ★★★ **번들 크기** — 「`import type` 이 번들을 줄인다」 | **재지 않았다** — 방출 **줄**만 셌다(1절: 기본 설정에서는 **줄 수도 안 줄었다**) |

## 한눈에 — 쉽게 말하면

**타입 전용 import 는 「이삿짐 상자에 붙인 『버릴 것』 딱지」다. 딱지를 안 붙여도 tsc 는 상자를 열어 보고 알아서 버려 왔다(기본 설정). `verbatimModuleSyntax` 는 「상자를 열어 보지 말고 딱지대로만 해라」는 규칙이다 — 딱지가 없으면 그대로 싣고, 딱지가 상자 안 물건에만 붙어 있으면 빈 상자를 싣는다.**

| 비유 | 실체 |
|---|---|
| **상자를 열어 보고** 타입만 든 것은 버린다 | 기본 설정 — 값으로 안 쓰인 import 를 **지운다**(elision) |
| ★★ 쓰지 않은 물건이 든 상자도 버린다 | 값을 import 했는데 **안 쓰면** 그 줄이 지워진다 — **그 모듈의 부작용도 사라진다**(1절 `i36g`) |
| 「**딱지대로만**」 | `verbatimModuleSyntax` — `type` 이 붙은 것만 지우고 나머지는 **적힌 그대로** |
| ★★★ 물건 하나에만 딱지 → **빈 상자가 실린다** | `import { type Shape }` → **`import {} from "./lib36.mjs";`** — 모듈이 평가된다 |
| 상자 전체에 딱지 | `import type { Shape }` → **줄째** 지워진다 |
| 「딱지 없이 버릴 물건」을 쓰면 반려 | `verbatimModuleSyntax` 에서 타입을 값 import → **`TS1484`** |
| 「상자 뜯는 도구를 못 쓰는 창고」 | `erasableSyntaxOnly` — `import x = require()` 류 **TS 전용 꼴**을 막는다 |

- ★★★ 한 줄로 — 「**기본 설정은 tsc 가 import 를 골라 지우고, `verbatimModuleSyntax` 는 `type` 이 붙은 것만 지운다. 그 차이가 방출물의 import 줄과 부작용 모듈의 평가를 바꾼다.**」

```text
  같은 한 줄, 두 설정

  import { type Shape } from "./lib36.mjs";

  기본               ─> (줄째 사라짐)                     node: lib36 평가 안 됨
  verbatim           ─> import {} from "./lib36.mjs";      node: lib36 evaluated   ★ 빈 import 가 부작용을 살린다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 어느 import/export 줄이 방출물에 남나** — 꼴 여덟 × 플래그 넷(1절). 그 차이가 **node 실행**에서 어떻게 드러나나.
2. **★★ `erasableSyntaxOnly` 는 import/export 의 어느 꼴을 막나** — 꼴 여섯 × 세 판(2절). 34편의 「방출 줄 ⇔ `TS1294`」가 여기서도 맞나(3절).
3. **★★ 이 판들에서 import 방출 플래그는 무엇이 남고 무엇이 사라졌나** — 플래그 여섯 × 세 판(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — 방출된 `.js` + `node`(방출 격자)** | 파일 여덟 × 플래그 넷 — 남은 줄 · 진단 · node 출력 | 실행 결과 | **본체**(1절) |
| ★★ **판 격자** | import/export 꼴 여섯 × 세 판(`--erasableSyntaxOnly`) · 플래그 여섯 × 세 판 | 세 판 대조 | 2·4절 |
| ★★ **3창 단독** | `import type X = require()` 의 방출물 | 방출물 | 3절 |
| ★ **부적용 — 5창(`.d.ts` 방출)** · **2창(`null` 탐침)** | 이 주제는 타입의 모양이 아니라 **줄이 남나**를 묻는다 | — | — |

비용 — 방출 격자(방출 넷 · `node` 32) + 판 격자 둘(꼴 여섯 × 세 판 · 플래그 여섯 × 세 판) + 방출 한 번.

```text
  이 주제의 축 — 「누가 지울지 정하나」

  import { Shape } from "…"          기본: tsc 가 쓰임새를 보고 지운다    verbatim: TS1484 (값 import 인데 타입)
  import type { Shape } from "…"     기본·verbatim 모두 지운다
  import { type Shape } from "…"     기본: 줄째 지운다                    verbatim: import {} from "…"  ★
  import { version } from "…" (안 씀) 기본: 지운다(부작용도)             verbatim: 남긴다
  import "…"                         늘 남는다
```

### (1) ★★★ 방출 격자 — 꼴 여덟 × 플래그 넷

**언제 쓰나** — 「이 import 가 실행 때 그 모듈을 **부르나**」를 판단할 때. 특히 **부작용이 있는 모듈**(폴리필·등록 코드)을 가져올 때.

가져올 곳 — 평가되면 한 줄을 찍는 모듈이다.

```ts
// lib36.mts
console.log("lib36 evaluated");
export interface Shape {
    area: number;
}
export const version = 1;
```

가져오는 쪽 여덟 — 파일 하나에 꼴 하나.

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

```text
===== bash ts34b-emit36.sh (sh exit=0) =====
[i36a] import { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 import { Shape } from "./lib36.mjs"; · 진단 (1,10) TS1484 · node SyntaxError: The requested module './lib36.mjs' does not provide an export named 'Shape'
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36b] import type { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 export {}; · 진단 OK · node (출력 없음)
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36c] import { type Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 import {} from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36d] import "./lib36.mjs";
    끔                    줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    isolatedModules        줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    verbatimModuleSyntax   줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
[i36e] export type { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 export {}; · 진단 OK · node (출력 없음)
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36f] export { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 (1,10) TS1205 · node (출력 없음)
    verbatimModuleSyntax   줄 export { Shape } from "./lib36.mjs"; · 진단 (1,10) TS1205 · node SyntaxError: The requested module './lib36.mjs' does not provide an export named 'Shape'
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36g] import { version } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36h] import { type Shape, version } from "./lib36.mjs";
    끔                    줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    isolatedModules        줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    verbatimModuleSyntax   줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated

끔과 갈린 칸 -- isolatedModules 1 / 8 · verbatimModuleSyntax 4 / 8 · erasableSyntaxOnly 0 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`[i36c] import { type Shape }` × `verbatimModuleSyntax` → `import {} from "./lib36.mjs";` · node `lib36 evaluated`.** 기본·`isolatedModules`·`erasableSyntaxOnly` 에서는 **줄째 사라지고** node 는 **출력 없음**.
  TSConfig 문서의 문장(「`import {} from "a"` 로 다시 쓰인다」)이 **방출물과 실행으로** 확인됐다 — **빈 import 는 빈 줄이 아니다.** 모듈을 **평가**한다.
- ★★★ **`[i36g] import { version }`(값인데 안 씀) × 끔 → `export {};` · node 출력 없음.** 기본 설정은 **안 쓰인 값 import 도 지운다** — `lib36` 의 부작용(`console.log`)이 **사라졌다.** `verbatimModuleSyntax` 는 **남기고** 평가한다.
- ★★★ **`[i36a] import { Shape }`(타입인데 일반 import) × `verbatimModuleSyntax` → `TS1484`** 이고 방출물에 **그대로 남아** node 가 **`SyntaxError: The requested module './lib36.mjs' does not provide an export named 'Shape'`**. 02편 6절과 **같은 칸**이다.
- ★★ **`[i36f] export { Shape }`(타입 재수출)** — `isolatedModules` 는 **`TS1205` 를 내고 방출은 지운다**(`export {};`), `verbatimModuleSyntax` 는 **`TS1205` 를 내고 방출은 남긴다** → node `SyntaxError`. 같은 진단, **다른 방출물**.
- ★★ **`[i36b] import type`·`[i36e] export type`** — 네 설정 다 **`export {};`**, node 출력 없음. 딱지가 **줄 전체**에 붙어 있으면 모든 설정이 지운다.
- ★★ **`[i36d] import "./lib36.mjs"`**(부작용 import)·**`[i36h] { type Shape, version }`**(섞음) — 네 설정 다 **같다.** 섞은 쪽은 `type` 붙은 것만 빠진 **`import { version }`** 이 남는다.
- ★★ **`export {};`** — 지워서 import 가 하나도 안 남아도 tsc 는 **파일이 모듈로 남도록** 이 한 줄을 넣었다(`i36h`·`i36d` 처럼 import 가 남으면 안 넣는다).
- ★★★ 마지막 줄 — **끔과 갈린 칸 isolatedModules 1 / 8 · verbatimModuleSyntax 4 / 8 · erasableSyntaxOnly 0 / 8**.
  `isolatedModules` 의 1칸은 **진단만**(`i36f` 의 `TS1205`) 다르다. **`erasableSyntaxOnly` 는 방출을 하나도 안 바꿨다** — 이 플래그는 **검사만** 한다(31편 4절과 같은 성질).
- ★★★ **「`import type` 이 방출을 줄인다」는 이 격자에서 참이 아니다** — 기본 설정에서 `i36a`(일반 import)와 `i36b`(`import type`)의 방출물이 **한 글자도 같다**(`export {};`). 기본 설정은 **이미** 지우고 있었다. `import type` 이 방출을 가르는 것은 **`verbatimModuleSyntax` 에서만**이다.

```text
  방출 격자 — 갈린 칸만 (끔 기준)

              끔                     verbatimModuleSyntax                          node
  i36a        export {};             import { Shape } …   + TS1484                  SyntaxError
  i36c        export {};             ★ import {} from "./lib36.mjs";                ★ lib36 evaluated
  i36f        export {};             export { Shape } …   + TS1205                  SyntaxError
  i36g        ★ export {};           import { version } …                           ★ lib36 evaluated
                                                                                    (끔에서는 평가 안 됨)
  isolatedModules : i36f 에 TS1205 — 방출은 끔과 같다         1 / 8
  erasableSyntaxOnly : 한 칸도 안 갈렸다                      0 / 8
```

비용 — **두 방향의 사고가 대칭이다.** 기본 설정은 **안 쓴 값 import 를 지워 부작용을 잃고**(`i36g`), `verbatimModuleSyntax` 는 **`type` 을 안쪽에 붙이면 빈 import 로 부작용을 되살린다**(`i36c`). 어느 쪽을 원하든 **방출물을 봐야** 안다.

### (2) ★★ `erasableSyntaxOnly` — import/export 꼴 여섯 × 세 판

**언제 쓰나** — 타입만 지우고 실행하는 도구와 같이 쓸 코드에서, **CJS 식 import/export**(`import x = require()`·`export =`)가 남아 있을 때.

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

```text
===== bash ts34b-erase36.sh (sh exit=0) =====
탐침                       7.0.2            5.9.3            4.9.5
import-type-named            OK               OK               TS5023
import-inline-type           OK               OK               TS5023
export-type                  OK               OK               TS5023
import-equals-require        (1,1) TS1294     (1,1) TS1294     TS5023
import-type-equals-require   (1,1) TS1294     (1,1) TS1294     TS5023
export-equals                (1,14) TS1294    (1,14) TS1294    TS5023

7.0.2 에서 TS1294 가 난 탐침 3 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★ **`import type { … }`·`import { type … }`·`export type { … }` 셋은 7.0.2·5.9.3 에서 `OK`** — ESM 의 타입 전용 꼴은 **지우면 끝**이다.
- ★★★ **`import Box = require(…)`·`export = n` 은 `TS1294`** — TS 전용 문법이라 지우기만 해서는 JS 가 안 된다(`require` 호출·`module.exports` 대입을 **만들어야** 한다).
- ★★★ **`import type Box = require(…)` 도 `TS1294`** — `type` 이 붙었는데도 막혔다. 3절이 그 방출물을 본다.
- ★★ 4.9.5 는 **전부 `TS5023`**(플래그가 5.8 부터). 7.0.2 와 5.9.3 이 **여섯 칸 다 같다.**
- ★ 34편 3절의 `import V = N.v`(namespace 별칭)도 같은 `import =` 꼴이라 `TS1294` 였다 — 거기서 쟀다.
- ★★ 마지막 줄 **7.0.2 에서 TS1294 가 난 탐침 3 / 6**.

비용 — `erasableSyntaxOnly` 를 켜면 **CJS 식 TS 문법은 `type` 을 붙여도** 못 쓴다. `.d.cts` 의 `export = Box` 는 **선언 파일이라** 안 걸렸다(이 격자의 가져올 곳이 그것이다).

### (3) ★★ `import type X = require()` — 방출 0줄인데 막힌다

**언제 쓰나** — 34편 3절의 「방출 줄이 있는 꼴 ⇔ `TS1294`」 **6 / 6** 을 일반화하기 전에.

```ts
// eqtype36.cts
import type Box = require("./box36.cjs");
let b: Box | undefined;
export {};
```

```text
===== tsc --pretty false -t es2022 --strict --module nodenext --outDir e36q eqtype36.cts (tsc exit=0) =====
===== 방출된 e36q/eqtype36.cjs =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
let b;
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext --erasableSyntaxOnly eqtype36.cts (tsc exit=1) =====
eqtype36.cts(1,1): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 방출물 — `"use strict";` · `Object.defineProperty(exports, "__esModule", …)` · `let b;` — **`import type Box = require(…)` 의 흔적은 없다.** 지울 것만 있는 꼴이다.
- ★★★ 그런데 `--erasableSyntaxOnly` 는 **`(1,1) TS1294`**. **방출물을 보고 판정하지 않는다** — **`import … = require(…)` 라는 꼴**을 보고 판정한다.
- ★★ 그래서 34편 3절의 6 / 6 은 **그 여섯 칸의 관찰**이었다 — 규칙은 「방출물이 생기나」가 아니라 「**이 꼴이 TS 전용 문법인가**」로 읽는다. 이 한 칸이 **반례**다.
- ★ 남은 두 줄(`"use strict";` · `__esModule`)은 **`export {}` 가 만든 CJS 모듈 머리**다 — import 와 무관하다.

```text
  같은 「지울 것만 있는 꼴」 — 판정이 갈린다

  import type { Box } from "./kit36.mjs";         방출 0줄   erasable: OK
  import type Box = require("./box36.cjs");       방출 0줄   erasable: ★ TS1294
                                                  ★ 판정은 방출물이 아니라 꼴(import = require)이다
```

비용 — 없다. 대신 **「지워지니까 괜찮다」는 추론이 이 플래그에서는 안 선다.**

### (4) ★★ 판 격자 — import 방출 플래그 여섯 × 세 판

**언제 쓰나** — 옛 `tsconfig.json` 의 `importsNotUsedAsValues`·`preserveValueImports` 를 7.0 으로 들고 갈 때.

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

```text
===== bash ts34b-flags36.sh (sh exit=0) =====
플래그                          7.0.2      5.9.3      4.9.5
isolatedModules                    OK         OK         OK
importsNotUsedAsValues             TS5023     TS5102     OK
preserveValueImports               TS5023     TS5102     OK
verbatimModuleSyntax               OK         OK         TS5023
erasableSyntaxOnly                 OK         OK         TS5023
rewriteRelativeImportExtensions    OK         OK         TS5023

세 판이 한 답이 아닌 행 5 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`importsNotUsedAsValues`·`preserveValueImports` — 4.9.5 `OK` · 5.9.3 `TS5102` · 7.0.2 `TS5023`.** 세 판이 **세 답**이다.
  5.9.3 은 「**제거된 옵션**」(`TS5102` — 「Option … has been removed … Use 'verbatimModuleSyntax' instead.」), 7.0.2 는 「**모르는 옵션**」(`TS5023`) — **이름조차 모른다.** 제거 안내가 사라진 것이다.
- ★★ **`verbatimModuleSyntax`·`erasableSyntaxOnly`·`rewriteRelativeImportExtensions` — 4.9.5 `TS5023`** · 5.9.3·7.0.2 `OK`.
- ★ `isolatedModules` 만 **세 판 다 `OK`**(1.5 부터 — 02편).
- ★★ 마지막 줄 **세 판이 한 답이 아닌 행 5 / 6**.
- ★ 격자는 **기본값이 아닌 값**(`preserve`)으로 던졌다 — 5.9.3 은 기본값을 주면 **조용히 받는다**:

```ts
// lib36.mts
console.log("lib36 evaluated");
export interface Shape {
    area: number;
}
export const version = 1;
```

```text
===== node "$TSC_OLD" --pretty false --noEmit --module nodenext --importsNotUsedAsValues <remove · preserve> lib36.mts (sh exit=0) =====
---- remove
(exit 0)
---- preserve
error TS5102: Option 'importsNotUsedAsValues' has been removed. Please remove it from your configuration.
  Use 'verbatimModuleSyntax' instead.
(exit 2)
```

- ★★ `remove`(기본값)는 **`(exit 0)`**, `preserve` 는 **`TS5102`**. 5.9.3 의 「제거」는 **기본값과 다른 값을 줄 때만** 드러난다.

```text
  import 방출 플래그의 판 경계 (이 머신의 세 판)

                                 4.9.5     5.9.3      7.0.2
  importsNotUsedAsValues         OK        TS5102     TS5023   ← 제거 안내 → 이름째 모름
  preserveValueImports           OK        TS5102     TS5023
  verbatimModuleSyntax           TS5023    OK         OK       ← 5.0 (릴리스 노트)
  erasableSyntaxOnly             TS5023    OK         OK       ← 5.8
  rewriteRelativeImportExtensions TS5023   OK         OK       ← 5.7
  isolatedModules                OK        OK         OK
```

비용 — 7.0.2 의 `TS5023` 은 **대체 옵션을 알려 주지 않는다.** 5.9.3 을 거쳐 올리면 `TS5102` 가 **`verbatimModuleSyntax` 를 가리켜** 준다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  import type { T } from "m";            줄째 지워진다 — 모든 설정                     (1절 i36b)
  import { type T } from "m";            기본: 줄째 지움 · verbatim: import {} from "m"  (1절 i36c)
  import { type T, v } from "m";         type 붙은 것만 빠진다                          (1절 i36h)
  export type { T } from "m";            줄째 지워진다                                  (1절 i36e)
  import "m";                            늘 남는다 — 부작용 import                      (1절 i36d)
  import type X = require("m");          방출 0줄 — 그래도 erasable 에서 TS1294         (3절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `verbatimModuleSyntax` 에서 타입을 일반 import | `TS1484` | 1절 · 02편 6절 |
| `isolatedModules`·`verbatimModuleSyntax` 에서 타입을 `export { T }` 로 재수출 | `TS1205` | 1절 · 02편 5절 |
| `erasableSyntaxOnly` 에서 `import x = require()` · `import type x = require()` · `export =` | `TS1294` | 2·3절 |
| 7.0.2 에서 `importsNotUsedAsValues`·`preserveValueImports` | `TS5023` | 4절 |
| 5.9.3 에서 같은 둘(기본값 아닌 값) | `TS5102` | 4절 |
| 4.9.5 에서 `verbatimModuleSyntax`·`erasableSyntaxOnly` | `TS5023` | 2·4절 |

**규칙 불릿**

- ★★★ **기본 설정은 쓰임새를 보고 import 를 지운다** — 타입만 쓰인 것도, **안 쓰인 값**도(1절 `i36a`·`i36g`).
- ★★★ **`verbatimModuleSyntax` 는 `type` 이 붙은 것만 지운다** — 이름 안쪽의 `type` 은 **빈 import** 를 남긴다(1절 `i36c`).
- ★★ **`erasableSyntaxOnly` 는 방출을 안 바꾼다** — 검사만 하고(0 / 8), `import =`·`export =` 꼴을 막는다(2·3절).
- ★★ **`import type` 이 방출을 가르는 것은 `verbatimModuleSyntax` 에서다** — 기본 설정에서는 일반 import 와 방출물이 같다(1절).

## 어디서 틀리나

- ★★★ 「**`import { type T }` 와 `import type { T }` 는 같다**」 — `verbatimModuleSyntax` 에서 앞쪽은 **`import {} from`** 을 남겨 모듈을 평가한다(1절). 뒤쪽은 줄째 지운다.
- ★★★ 「**부작용 모듈에서 값 하나를 import 해 두면 부작용이 돈다**」 — 기본 설정은 **안 쓰인 값 import 를 지운다**(1절 `i36g`). 부작용이 필요하면 **`import "m";`** 로 적는다(`i36d` 는 모든 설정에서 남았다).
- ★★★ 「**`import type` 을 쓰면 방출이 줄어든다**」 — 기본 설정에서는 **이미 같았다**(1절 `i36a` = `i36b`). 번들 크기는 **재지 않았다.**
- ★★ 「**`isolatedModules` 와 `verbatimModuleSyntax` 는 같은 진단이니 같은 방출이다**」 — `i36f` 에서 **같은 `TS1205`, 다른 방출물**(지움 대 남김 → `SyntaxError`)(1절).
- ★★ 「**`erasableSyntaxOnly` 를 켜면 방출이 바뀐다**」 — **0 / 8**. 검사만 한다(1절).
- ★★ 「**`type` 을 붙이면 `erasableSyntaxOnly` 를 통과한다**」 — `import type X = require()` 는 **`TS1294`**(3절).
- ★ 「**옛 옵션은 7.0 이 제거 안내를 해 준다**」 — 5.9.3 은 `TS5102` 로 안내했지만 7.0.2 는 **`TS5023`**(모르는 옵션)이다(4절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **컴파일러 보장(TSConfig 문서)** | `verbatimModuleSyntax` — 타입 전용 import 는 지우고 값 import 는 그대로 · `import { type A }` → `import {} from "a"` | TSConfig · 1절 `i36c` |
| **컴파일러 보장(5.8 릴리스 노트)** | `erasableSyntaxOnly` 는 지우기만 해서 JS 가 안 되는 문법(`import =`·`export =` 포함)을 막는다 | 릴리스 노트 · 2절 |
| **★ 이 판(7.0.2)의 관찰** | 기본 설정이 **안 쓰인 값 import** 를 지운다 | 1절 `i36g` |
| **★ 이 판의 관찰** | `import type X = require()` 가 **방출 0줄인데 `TS1294`** | 3절 |
| **★ 이 판의 관찰** | `isolatedModules` 가 `i36f` 에 `TS1205` 를 내며 **방출은 지운다** | 1절 |
| **호스트(node v18)** | 빈 `import {} from "m"` 도 **모듈을 평가한다** · 없는 이름 import 는 링크 단계 `SyntaxError` | 1절 node 칸 |
| **★ 판 격자** | 옛 두 옵션 — 4.9.5 `OK` · 5.9.3 `TS5102` · 7.0.2 `TS5023` | 4절 — **세 번의 관찰** |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | 번들 크기 · 번들러의 트리 셰이킹 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **`verbatimModuleSyntax`** — 파일 하나만 보는 변환기(esbuild·SWC·타입 제거 실행)와 **방출을 맞출** 때. **무엇이 남을지 소스만 보고** 안다 | 기본 설정의 「알아서 지움」에 **부작용을 맡길** 때 — `i36g` 에서 사라졌다 |
| ★★ **`import type { … }`**(줄 전체) — 타입만 가져올 때. **모든 설정에서** 줄째 지워진다 | ★★ **`import { type … }` 만으로 된 줄** + `verbatimModuleSyntax` — 빈 import 가 남는다(부작용이 **싫다면**) |
| ★★ **`import "m";`** — 부작용이 **필요할** 때. 모든 설정에서 남는다 | 값 하나를 import 해 두고 부작용을 기대하기 |
| ★ **`erasableSyntaxOnly`** — 타입만 지우고 실행할 코드 · ESM 꼴만 쓸 때 | `import x = require()`·`export =` 이 남은 CJS 식 TS 코드 |
| — | 7.0 에서 `importsNotUsedAsValues`·`preserveValueImports` — `TS5023` |

## 핵심 문장

1. **기본 설정은 import 를 쓰임새로 지우고, `verbatimModuleSyntax` 는 `type` 딱지로만 지운다** — 방출 격자에서 끔과 갈린 칸 **4 / 8**(`isolatedModules` 1 / 8 · `erasableSyntaxOnly` 0 / 8).
2. **`import { type T }` 는 `verbatimModuleSyntax` 에서 `import {} from` 을 남겨 모듈을 평가한다** — 빈 import 는 부작용을 살린다. 반대로 기본 설정은 **안 쓰인 값 import 를 지워 부작용을 잃는다.**
3. **`import type` 이 방출을 가르는 것은 `verbatimModuleSyntax` 에서다** — 기본 설정에서는 일반 import 와 방출물이 같았다. 번들 크기는 재지 않았다.
4. **`erasableSyntaxOnly` 는 방출이 아니라 꼴을 본다** — `import type X = require()` 는 방출 0줄인데 `TS1294` 다.

## 관련 자료

- [**35번 주제** — 모듈 해석](../35-module-resolution/) — ★★★ **README 의 선행.** import 가 **풀리나**는 그쪽. 여기는 풀린 import 가 **남나**.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — `TS1484` + node `SyntaxError`(6절) · `TS1205`(5절)의 정본. 1절 `i36a`·`i36f` 가 그 칸을 격자 안에 다시 만났다.
- [**31번 주제** — 열거형의 함정](../31-enum-pitfalls/) — 두 플래그가 **`const enum`** 방출을 바꾸는 쪽(4절)과 `erasableSyntaxOnly` 의 enum 판 격자(3절).
- [**34번 주제** — `namespace` 의 자리](../34-namespace-place/) — `import V = N.v` 의 `TS1294` 와 「방출 줄 ⇔ `TS1294`」 **6 / 6**. 3절이 그 반례다.
- [JS 갈래 **42번**(ESM — 정적 구조·평가 순서)](../../../js/syntax/42-esm-modules/) — 「빈 import 도 모듈을 평가한다」는 ESM 쪽 규칙이다.
- [목록의 **48번 주제**](../48-js-file-type-checking/)(JS 파일 타입 검사) — README 가 이 주제를 선행으로 둔다(JSDoc 의 `@import` 등).

## 용어 풀이

> **import 지우기(elision)** — tsc 가 **값으로 안 쓰인** import 를 방출물에서 빼는 것. 기본 설정의 동작이다.\
> 예: 1절 `i36g` — 값 `version` 을 안 써서 줄이 사라졌다.

> **타입 전용 import** — `import type { T }`(줄 전체) 또는 `import { type T }`(이름 하나). 타입으로만 쓰겠다는 표시.\
> 예: 1절 `i36b`·`i36c`.

> **`verbatimModuleSyntax`** — 「적힌 그대로 방출」. `type` 이 붙은 것만 지우고, 나머지 import/export 는 **쓰임새와 무관하게** 남긴다(5.0).\
> 예: 1절 `i36c` → `import {} from "./lib36.mjs";`.

> **부작용 import** — `import "m";` 처럼 이름 없이 **모듈을 평가만** 하는 import.\
> 예: 1절 `i36d` — 모든 설정에서 남았다.

> **`TS1484`** — 「'X' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.」\
> 예: 1절 `i36a`.

> **`TS1205`** — 「Re-exporting a type when '…' is enabled requires using 'export type'.」\
> 예: 1절 `i36f`.

> **`TS5023` / `TS5102`** — 「모르는 옵션」 / 「제거된 옵션(대체 안내 포함)」.\
> 예: 4절 `importsNotUsedAsValues`.

## 더 들어가면

- **`import { type T }` 의 빈 import 를 막고 싶을 때** — `import type { T }` 로 줄 전체에 딱지를 붙이면 된다(1절 `i36b`). 린터 규칙으로 강제하는 방법은 **던지지 않았다.**
- **CJS 출력에서의 `verbatimModuleSyntax`** — 이 문서는 `.mts`(ESM) 로만 격자를 돌렸다. CJS 파일에서 이 플래그가 `import … from` 을 어떻게 다루는지는 **던지지 않았다.**
- **번들러가 빈 import 를 어떻게 다루나** — 번들러마다 부작용 판정(`sideEffects` 필드 등)이 따로 있다. **재지 않았다.**
