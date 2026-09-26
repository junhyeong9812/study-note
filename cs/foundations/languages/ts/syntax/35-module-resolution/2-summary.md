# ts/syntax/35 — 모듈 해석 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Modules Reference](https://www.typescriptlang.org/docs/handbook/modules/reference.html)(`node16`/`nodenext` 의 상대 ESM import 는 **확장자가 필요** · `bundler` 는 확장자 없는 경로와 디렉토리 모듈을 받는다 · **`paths` 는 방출물의 import 경로를 바꾸지 않는다** · `exports` 의 `types` 조건) ·
> [Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)(`--moduleResolution node`·`classic` 과 `baseUrl` 의 deprecation — 「`node` 를 쓰던 사용자는 대개 `nodenext` 로, 번들러는 `bundler` 로」 · 「`baseUrl` 은 더 이상 해석의 조회 루트가 아니다 — `paths` 항목에 접두를 직접 넣어라」).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·추적·실행 출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 본판은 아래다. ★ 판 격자에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**. **6.0 은 이 머신에 없다.**

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 세 판 해석 격자(옵션 × 판)와 해석 격자(import 경로 × 해석 방식)이고, 급소는 호스트 창(`node` 가 실제로 푸나)이다.**
> ★★★ **축이 세 층이다.** 「이 경로가 풀리나」를 **TS 명세**가 정하는 것이 아니다 — **tsc 는 호스트(node·번들러)의 해석을 흉내 낼 뿐**이고, 실제로 푸는 것은 **호스트**다. 그래서 tsc 판정과 node 판정을 **한 쌍으로** 싣는다(4절).
> ★★★ **35 는 02 와 JS 43 에서 온다.** [**02번 주제**](../02-type-checking-vs-emit/) 7절이 `tsconfig.json` 의 `moduleResolution: "node10"` 이 7.0.2 에서 **`TS5108`** 인 것을 **이미 쟀다** — 여기서는 그것을 **세 판 × 여덟 행**으로 넓힌다.
> JS 쪽의 짝 — [JS 갈래 **42번**(ESM 모듈)](../../../js/syntax/42-esm-modules/) · [JS 갈래 **43번**(CJS 와 ESM 상호운용 — `type` 필드·확장자 해석)](../../../js/syntax/43-cjs-and-esm-interop/)이다. 이 문서의 node 쪽 사실은 **직접 던진 `node` 출력**으로 적었고, node 규칙 자체의 정본은 그 두 편이다.
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ JSON(`package.json`·`tsconfig.json`)은 주석을 달 수 없어 **캡처가 `===== 소스: 경로 =====` 배너를 찍어** 싣는다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` · node 의 오류 **코드**(`ERR_…`) | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 격자 넷의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **판에 매인다** | ★★ **종료 코드** — 진단 있는 `--noEmit` 이 7.0.2 는 `1`, 5.9.3·4.9.5 는 `2`(6절 블록) | 격자는 **진단 코드로** 갈랐다 |
| **안 흔들린다** | `--traceResolution` 의 줄 | ★ **절대 경로가 박힌다** — 배너의 `sed` 가 `.`·`..` 로 바꿨다. 바꾼 것은 **경로 앞부분뿐**이다 |
| **호스트에 매인다** | `node` 의 판정 | **node v18.19.1** 의 것이다 — 5절은 **node 판이 오르면 답이 바뀌는 칸**이다 |
| **★ 부적용 — 5창(`.d.ts` 방출)** | 선언 방출은 안 물었다 | 질문은 「**풀리나**」다 |
| **안 잰 것** | 해석 방식이 검사 **시간**에 주는 영향 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**모듈 해석은 「주소를 보고 집을 찾는 것」이다. tsc 는 지도를 들고 「이 주소면 이 집이다」라고 미리 짚어 보는 안내원이고, 실제로 문을 두드리는 배달원은 node(또는 번들러)다. 안내원이 배달원과 다른 지도를 들면, 안내원이 「있다」고 한 집에 배달원이 못 간다.**

| 비유 | 실체 |
|---|---|
| **주소** | `import … from "./util35.js"` 의 따옴표 안(모듈 지정자) |
| **안내원이 드는 지도** | `--moduleResolution` — `nodenext`·`bundler`… |
| **배달원** | node(v18) · 번들러 — **실제로** 파일을 찾는다 |
| ★★★ 안내원이 **배달원의 지도를 그대로** 들었다 | `nodenext` — node 와 **6 / 6** 같은 판정(4절) |
| ★★ 안내원이 **다른 배달원의 지도**를 들었다 | `bundler` 로 검사하고 node 로 실행 — **4 / 6**(4절) |
| ★★★ **7.0 이 옛 지도 두 장을 회수했다** | `node10`(`node`)·`classic` → `TS5108`, `baseUrl` → `TS5102`(1절) |
| 「`@src/…` 라는 별칭 주소」 | `paths` — **안내원만 아는 별칭**. 배달원은 모른다(6절) |

- ★★★ 한 줄로 — 「**tsc 의 해석은 호스트의 해석을 흉내 낸 것이다. 흉내 낼 호스트를 고르는 것이 `moduleResolution` 이고, 7.0 은 어느 호스트도 흉내 내지 않던 두 값을 없앴다.**」

```text
  한 import 가 거치는 두 층

  import { util } from "./util35.js";
        │
        ├── tsc (검사 때)   --moduleResolution 이 정한 규칙으로 ./util35.ts 를 찾는다   → 타입
        │                   ★ 경로는 한 글자도 안 바꿔서 방출한다
        │
        └── node (실행 때)  node 의 ESM 규칙으로 ./util35.js 를 찾는다               → 값
                            ★ 둘이 다른 규칙이면: tsc 는 통과, node 는 ERR_MODULE_NOT_FOUND
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 7.0 에서 무엇이 사라졌나** — `moduleResolution` 값·`baseUrl` × 세 판(1절). 아무것도 안 주면 판마다 **무엇을 고르나**.
2. **★★★ 같은 import 문이 해석 방식마다 어떻게 풀리나** — 확장자 없음 · `.js` 로 `.ts` 가져오기 · `.ts` 확장자 · 디렉토리 · `exports`(2·3절).
3. **★★★ tsc 가 통과시킨 import 를 node 가 실제로 푸나** — 호스트와의 한 쌍(4절) · `nodenext` 가 **어느 node 를** 흉내 내나(5절) · `paths` 와 7.0 뒤의 설정(6절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **세 판 해석 격자** | 옵션 여덟 행 × (7.0.2 · 5.9.3 · 4.9.5) | 세 판 대조 | **본체**(1절) |
| ★★★ **해석 격자** | import 경로 여섯 × 해석 방식 다섯 | 칸마다 진단 코드 | **본체**(2절) |
| ★★ **`--traceResolution`** | tsc 가 **어느 파일을 어떤 순서로** 찾았나 | 추적 로그 | 3절 |
| ★★★ **호스트 창 — `node` 실행** | 방출물의 import 를 **node 가 푸나** | 실행 결과 · 오류 코드 | **급소**(4·5·6절) |
| ★★ **`--module` × 판 격자** | CJS 파일이 ESM 을 부를 때 | 세 판 대조 | 5절 |
| ★ **부적용 — 5창(`.d.ts` 방출)** · **2창(`null` 탐침)** | 이 주제의 질문은 「**풀리나**」다 — 타입의 모양을 묻지 않는다 | — | — |

비용 — 격자 넷(여덟 행 × 세 판 · 여섯 × 다섯 · 여섯 × (tsc 둘 + node) · 넷 × 세 판) + 추적 넷 · 방출 셋 · `node` 셋.

```text
  이 주제의 축 — 「누가 흉내 내나」

  moduleResolution    흉내 내는 호스트             7.0.2
  node10 (= node)     옛 node 의 require 해석       ★ TS5108 — 사라졌다
  classic             어느 호스트도 아니다(TS 초기)  ★ TS5108 — 사라졌다
  node16 · nodenext   node 의 ESM/CJS 해석          있다
  bundler             번들러(확장자 없어도 된다)    있다 — ★ 아무것도 안 주면 이것
  baseUrl             (해석 방식이 아니라 조회 루트)  ★ TS5102 — 옵션째 사라졌다
```

### (1) ★★★ 세 판 해석 격자 — 7.0 에서 사라진 것

**언제 쓰나** — 5.x 의 `tsconfig.json` 을 7.0 으로 올릴 때. 02편 7절이 `tsconfig.json` 으로 본 `TS5108` 을 **명령줄로 여덟 행**에 넓혔다.

```bash
# ts34b-resgrid.sh
#!/usr/bin/env bash
# moduleResolution 값(과 baseUrl) 을 세 판의 tsc 에 준다 -- 파일은 export 한 줄짜리 r35.ts
# 칸: 판마다 진단 코드(없으면 OK) · 끝 세 줄은 아무것도 안 줬을 때 판마다 고른 해석 방식
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
rows=(
  "node10${T}--module commonjs --moduleResolution node10"
  "node${T}--module commonjs --moduleResolution node"
  "classic${T}--module commonjs --moduleResolution classic"
  "node16${T}--module node16 --moduleResolution node16"
  "nodenext${T}--module nodenext --moduleResolution nodenext"
  "bundler${T}--module esnext --moduleResolution bundler"
  "bundler+commonjs${T}--module commonjs --moduleResolution bundler"
  "nodenext+baseUrl${T}--module nodenext --moduleResolution nodenext --baseUrl ."
)
echo 'export const x = 1;' > "$D/r35.ts"
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-18s %-14s %-14s %s\n' "행" "7.0.2" "5.9.3" "4.9.5"
ok7=0; ok5=0; ok4=0; split=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r")
  if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r name flags <<< "$r"
  # shellcheck disable=SC2086
  a=$(cd "$D" && tsc --pretty false --noEmit $flags r35.ts 2>&1 | codes)
  b=$(cd "$D" && node "$OLD" --pretty false --noEmit $flags r35.ts 2>&1 | codes)
  c=$(cd "$D" && node "$V49" --pretty false --noEmit $flags r35.ts 2>&1 | codes)
  printf '%-18s %-14s %-14s %s\n' "$name" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1))
  [ -z "$a" ] && ok7=$((ok7+1)); [ -z "$b" ] && ok5=$((ok5+1)); [ -z "$c" ] && ok4=$((ok4+1))
  [ "$a" != "$b" ] && split=$((split+1))
done
echo
echo 'import { x } from "./r35";' > "$D/i35.ts"
kind() { grep -m1 -o "using '[A-Za-z0-9]*'"; }
echo "아무것도 안 줬을 때 -- 7.0.2 $(cd "$D" && tsc --pretty false --noEmit --traceResolution i35.ts 2>&1 | kind)"
echo "아무것도 안 줬을 때 -- 5.9.3 $(cd "$D" && node "$OLD" --pretty false --noEmit --traceResolution i35.ts 2>&1 | kind)"
echo "아무것도 안 줬을 때 -- 4.9.5 $(cd "$D" && node "$V49" --pretty false --noEmit --traceResolution i35.ts 2>&1 | kind)"
echo
echo "받아들인 행 -- 7.0.2 $ok7 / $total · 5.9.3 $ok5 / $total · 4.9.5 $ok4 / $total · 7.0.2 와 5.9.3 이 갈린 행 $split / $total"
```

```text
===== bash ts34b-resgrid.sh (sh exit=0) =====
행                7.0.2          5.9.3          4.9.5
node10             TS5108         OK             TS6046
node               TS5108         OK             OK
classic            TS5108         OK             OK
node16             OK             OK             OK
nodenext           OK             OK             OK
bundler            OK             OK             TS6046
bundler+commonjs   OK             TS5095         TS6046
nodenext+baseUrl   TS5102         OK             OK

아무것도 안 줬을 때 -- 7.0.2 using 'Bundler'
아무것도 안 줬을 때 -- 5.9.3 using 'Node10'
아무것도 안 줬을 때 -- 4.9.5 using 'NodeJs'

받아들인 행 -- 7.0.2 4 / 8 · 5.9.3 7 / 8 · 4.9.5 5 / 8 · 7.0.2 와 5.9.3 이 갈린 행 5 / 8
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`node10`·`node`·`classic` 이 7.0.2 에서 `TS5108`** — 「Option 'moduleResolution=…' has been removed.」 5.9.3 은 **셋 다 `OK`**. **값이 제거됐다.**
- ★★★ **`nodenext+baseUrl` 이 7.0.2 에서 `TS5102`** — 「Option 'baseUrl' has been removed.」 5.9.3·4.9.5 는 `OK`. **옵션 이름째 제거됐다.**
  02편 7절의 구분 그대로다 — **`TS5108` 은 값**, **`TS5102` 는 옵션**.
- ★★ `node` 는 `node10` 의 **옛 이름**이다(6.0 릴리스 글이 `--moduleResolution node` 를 node10 으로 부른다). 격자는 **코드만** 찍었다 — 두 행의 코드가 같다.
- ★★★ **`bundler+commonjs` 는 7.0.2 에서 `OK`, 5.9.3 에서 `TS5095`** — 7.0 은 **없앤 것만 있는 게 아니라 푼 것도 있다.** `bundler` 를 `--module commonjs` 와 같이 쓰는 길이 새로 열렸다.
- ★★ **4.9.5 의 `TS6046`** — 「Argument for '--moduleResolution' option must be …」. **`node10` 이라는 이름과 `bundler` 가 둘 다 5.0 부터**라서다. 4.9.5 에서 `node` 는 되는데 `node10` 은 안 되는 까닭이다.
- ★★★ **아무것도 안 줬을 때 판마다 다른 것을 고른다** — 7.0.2 **`Bundler`** · 5.9.3 **`Node10`** · 4.9.5 **`NodeJs`**. 같은 명령이 **판마다 다른 해석 규칙으로** 돈다.
- ★★ 마지막 줄 — **받아들인 행 7.0.2 4 / 8 · 5.9.3 7 / 8 · 4.9.5 5 / 8 · 7.0.2 와 5.9.3 이 갈린 행 5 / 8**.

```text
  세 판 — 사라진 것, 생긴 것, 기본값

                     4.9.5      5.9.3      7.0.2
  node10             (이름 없음) OK         TS5108   ← 값 제거
  node               OK         OK         TS5108
  classic            OK         OK         TS5108
  bundler            (없음)     OK         OK
  bundler+commonjs   (없음)     TS5095     ★ OK     ← 7.0 에서 풀렸다
  baseUrl            OK         OK         TS5102   ← 옵션 제거
  기본 해석           NodeJs     Node10     ★ Bundler
```

비용 — 올리기 전에는 **안 보인다** — 5.9.3 은 넷 다 조용히 받았다. **기본값이 바뀐 것**은 진단조차 없다 — 아무것도 안 적은 프로젝트는 **조용히 다른 규칙으로** 검사된다.

### (2) ★★★ 해석 격자 — 같은 import 문 × 해석 방식

**언제 쓰나** — 「이 import 를 이 설정에서 써도 되나」를 판단할 때.

패키지 하나를 차렸다 — `package.json` 의 `type: "module"` 로 `.ts` 가 **ESM** 이 되고, `exports` 로 **자기 이름 참조**(self-reference — 자기 패키지를 이름으로 부르는 것)를 연다. `node_modules` 는 **안 쓴다.**

```text
===== 소스: p35/package.json =====
{
  "name": "pkg35",
  "type": "module",
  "exports": {
    "./feature": {
      "types": "./src/feature35.ts",
      "default": "./out/feature35.js"
    }
  }
}
```

```ts
// util35.ts
export const util = "util35";
```

```ts
// feature35.ts
export const feature = "feature35";
```

```ts
// index.ts
export const dir = "dir35/index";
```

- ★ 위 파일은 `p35/src/dir35/index.ts` 다 — 배너는 파일 이름만 적는다.

```ts
// imp35a.ts
export { util as v } from "./util35";
```

```ts
// imp35b.ts
export { util as v } from "./util35.js";
```

```ts
// imp35c.ts
export { util as v } from "./util35.ts";
```

```ts
// imp35d.ts
export { dir as v } from "./dir35";
```

```ts
// imp35e.ts
export { feature as v } from "pkg35/feature";
```

```ts
// imp35f.ts
export { feature as v } from "pkg35/src/feature35.js";
```

```bash
# ts34b-spec35.sh
#!/usr/bin/env bash
# p35/src 의 imp35a~f -- import 문 하나씩을 해석 방식 다섯으로 던진다(파일마다 따로)
# 7.0.2 는 node16 · nodenext · bundler, 7.0 에서 사라진 node10 · classic 은 5.9.3 으로
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
cd p35/src || exit 1
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-8s %-38s %-8s %-8s %-8s %-8s %s\n' "파일" "import 경로" "node16" "nodenext" "bundler" "node10" "classic"
ok=0; total=0
for f in imp35a imp35b imp35c imp35d imp35e imp35f; do
  spec=$(grep -o '"[^"]*"' "$f.ts")
  row=()
  for mr in node16 nodenext bundler; do
    m=$mr; [ "$mr" = bundler ] && m=esnext
    row+=("$(tsc --pretty false --noEmit --module "$m" --moduleResolution "$mr" "$f.ts" 2>&1 | codes)")
  done
  for mr in node10 classic; do
    row+=("$(node "$OLD" --pretty false --noEmit --module esnext --moduleResolution "$mr" "$f.ts" 2>&1 | codes)")
  done
  out=()
  for c in "${row[@]}"; do
    total=$((total+1))
    if [ -z "$c" ]; then ok=$((ok+1)); out+=("OK"); else out+=("$c"); fi
  done
  printf '%-8s %-38s %-8s %-8s %-8s %-8s %s\n' "$f" "$spec" "${out[@]}"
done
echo
echo "풀린 칸 $ok / $total"
```

```text
===== bash ts34b-spec35.sh (sh exit=0) =====
파일   import 경로                          node16   nodenext bundler  node10   classic
imp35a   "./util35"                             TS2835   TS2835   OK       OK       OK
imp35b   "./util35.js"                          OK       OK       OK       OK       OK
imp35c   "./util35.ts"                          TS5097   TS5097   TS5097   TS5097   TS5097
imp35d   "./dir35"                              TS2834   TS2834   OK       OK       TS2792
imp35e   "pkg35/feature"                        OK       OK       OK       TS2307   TS2792
imp35f   "pkg35/src/feature35.js"               TS2307   TS2307   TS2307   TS2307   TS2792

풀린 칸 13 / 30
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`imp35a "./util35"`(확장자 없음) — `node16`·`nodenext` 에서 `TS2835`**(「Relative import paths need explicit file extensions in ECMAScript imports … Did you mean './util35.js'?」), `bundler`·`node10`·`classic` 은 `OK`.
- ★★★ **`imp35b "./util35.js"` — 다섯 칸 전부 `OK`.** 파일은 `util35.ts` 인데 **`.js` 로 적었다.** 이것이 **`nodenext` 가 요구하는 모양**이다 — **방출된 뒤의 이름**을 적는다(3절 추적이 그 기제를 보인다).
- ★★ **`imp35c "./util35.ts"` — 다섯 칸 전부 `TS5097`**(「… only end with a '.ts' extension when 'allowImportingTsExtensions' is enabled.」). 해석 방식과 **무관하게** 막힌다.
- ★★ **`imp35d "./dir35"`(디렉토리) — `node16`·`nodenext` 는 `TS2834`**(확장자를 붙이라), `bundler`·`node10` 은 `OK`(→ `dir35/index.ts`), **`classic` 은 `TS2792`**(못 찾는다).
- ★★★ **`imp35e "pkg35/feature"`(`exports`) — `node16`·`nodenext`·`bundler` 는 `OK`, `node10` 은 `TS2307`.** `node10` 은 **`exports` 를 모르고** 자기 이름 참조도 모른다.
- ★★ **`imp35f "pkg35/src/feature35.js"`(`exports` 에 없는 깊은 경로) — 다섯 칸 전부 막힘.** `exports` 를 아는 셋은 「**열어 두지 않은 경로**」라서, `node10`·`classic` 은 **패키지 자체를 못 찾아서**다. **같은 `TS2307` 이지만 까닭이 다르다** — 이 칸은 두 까닭을 가르지 못한다.
- ★★ **`classic` 의 `TS2792`** — 「Did you mean to set the 'moduleResolution' option to 'nodenext' …」. 진단이 **다른 해석 방식을 권한다.**
- ★★ 마지막 줄 **풀린 칸 13 / 30**.

```text
  해석 격자 — 이 판의 칸을 그림으로  (✓ 풀림 · 코드 = 막힘)

  import 경로                 node16  nodenext  bundler │ node10  classic   (5.9.3)
  "./util35"                  2835    2835      ✓       │ ✓       ✓
  "./util35.js"   ★           ✓       ✓         ✓       │ ✓       ✓         ← 다섯 다 받는 유일한 모양
  "./util35.ts"               5097    5097      5097    │ 5097    5097
  "./dir35"                   2834    2834      ✓       │ ✓       2792
  "pkg35/feature" (exports)   ✓       ✓         ✓       │ 2307    2792      ← node10 은 exports 를 모른다
  "pkg35/src/…"  (안 연 경로)  2307    2307      2307    │ 2307    2792
```

비용 — **`bundler` 에서 통과한 import 둘이 `nodenext` 에서 막힌다**(`imp35a`·`imp35d`). 번들러 없이 node 로 돌릴 코드를 `bundler` 로 검사하면 **그 둘이 새어 나간다**(4절).

### (3) ★★ `--traceResolution` — tsc 가 무엇을 찾았나

**언제 쓰나** — 「왜 이 import 가 안 풀리나 / 어느 파일로 풀렸나」를 볼 때. ★ 출력에 **절대 경로**가 박혀서 배너의 `sed` 로 앞부분만 `.`(=`p35/src`) · `..`(=`p35`) 로 바꿨다.

```text
===== cd p35/src && tsc --pretty false --noEmit --module nodenext --traceResolution imp35a.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=1) =====
======== Resolving module './util35' from './imp35a.ts'. ========
Module resolution kind is not specified, using 'NodeNext'.
Resolving in ESM mode with conditions 'import', 'types', 'node'.
Loading module as file / folder, candidate module location './util35', target file types: TypeScript, JavaScript, Declaration, JSON.
Directory './util35' does not exist, skipping all lookups in it.
======== Module name './util35' was not resolved. ========
imp35a.ts(1,27): error TS2835: Relative import paths need explicit file extensions in ECMAScript imports when '--moduleResolution' is 'node16' or 'nodenext'. Did you mean './util35.js'?
```

```text
===== cd p35/src && tsc --pretty false --noEmit --module esnext --moduleResolution bundler --traceResolution imp35a.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=0) =====
======== Resolving module './util35' from './imp35a.ts'. ========
Explicitly specified module resolution kind: 'Bundler'.
Resolving in CJS mode with conditions 'import', 'types'.
Loading module as file / folder, candidate module location './util35', target file types: TypeScript, JavaScript, Declaration, JSON.
File './util35.ts' exists - use it as a name resolution result.
======== Module name './util35' was successfully resolved to './util35.ts'. ========
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **같은 `imp35a.ts` · 같은 import** 인데 — `nodenext` 는 `candidate module location './util35'` 에서 **`Directory './util35' does not exist, skipping all lookups in it.`** 로 끝나 **`was not resolved`**.
  **확장자를 붙여 보는 시도가 아예 없다.** 적힌 그대로의 파일(과 디렉토리)만 본다.
- ★★★ `bundler` 는 같은 후보에서 **`File './util35.ts' exists`** — **`.ts` 를 붙여 봤다.**
- ★★ 줄 2 — `nodenext` 는 **`Module resolution kind is not specified, using 'NodeNext'.`**(`--module nodenext` 가 해석 방식까지 정했다), `bundler` 는 **`Explicitly specified …`**.
- ★ 줄 3 — `nodenext` 는 **`Resolving in ESM mode`**(`type: "module"` 때문), `bundler` 는 **`Resolving in CJS mode with conditions 'import', 'types'`** — 이 판의 문구다. `bundler` 가 ESM 파일을 「CJS mode」라 적는 까닭은 **확인하지 못했다**(조건은 `import` 를 쓴다).

```text
===== cd p35/src && tsc --pretty false --noEmit --module nodenext --traceResolution imp35e.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=0) =====
======== Resolving module 'pkg35/feature' from './imp35e.ts'. ========
Module resolution kind is not specified, using 'NodeNext'.
Resolving in ESM mode with conditions 'import', 'types', 'node'.
File './package.json' does not exist according to earlier cached lookups.
File '../package.json' exists according to earlier cached lookups.
Entering conditional exports.
Matched 'exports' condition 'types'.
Using 'exports' subpath './feature' with target './src/feature35.ts'.
File './feature35.ts' exists - use it as a name resolution result.
Resolved under condition 'types'.
Exiting conditional exports.
======== Module name 'pkg35/feature' was successfully resolved to './feature35.ts'. ========
```

- ★★★ **`exports` 의 길** — `../package.json`(=`p35/package.json`)을 찾고 → **`Matched 'exports' condition 'types'`** → **`./src/feature35.ts`** 로 풀렸다.
  **node 가 쓸 `default`(`./out/feature35.js`)가 아니라 `types` 조건**을 골랐다 — 핸드북 「`types` 조건이 있으면 **항상** 맞춘다」.
- ★ 이 추적은 `imp35a` 와 **다른 명령**이라 `package.json` 조회가 「according to earlier cached lookups」로 나온다 — 같은 명령 안의 **앞선 조회**(tsc 가 lib 을 볼 때 등)를 재쓴 것으로 읽힌다. **어떤 앞선 조회인지는 추적하지 않았다.**

```text
===== cd p35/src && tsc --pretty false --noEmit --module nodenext --traceResolution imp35b.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=0) =====
======== Resolving module './util35.js' from './imp35b.ts'. ========
Module resolution kind is not specified, using 'NodeNext'.
Resolving in ESM mode with conditions 'import', 'types', 'node'.
Loading module as file / folder, candidate module location './util35.js', target file types: TypeScript, JavaScript, Declaration, JSON.
File name './util35.js' has a '.js' extension - stripping it.
File './util35.ts' exists - use it as a name resolution result.
======== Module name './util35.js' was successfully resolved to './util35.ts'. ========
```

- ★★★ **`"./util35.js"` 가 풀리는 까닭** — `File name './util35.js' has a '.js' extension - stripping it.` → `File './util35.ts' exists`. **`.js` 를 떼고 `.ts` 로 찾는다** — 「방출된 뒤의 이름」을 「방출 전의 파일」로 되돌린다. 확장자를 **붙여 보는** 것(`bundler`)과 **바꿔 보는** 것(`nodenext`)은 다른 일이다.

비용 — 없다. 대신 **경로가 박혀** 그대로 실으면 재현이 안 된다 — 앞부분을 바꾸는 필터를 **배너에 적어** 던졌다.

### (4) ★★★ 호스트와 한 쌍 — tsc 의 판정과 node 의 판정

**언제 쓰나** — 「tsc 가 통과시켰으니 실행된다」를 믿기 전에.

```js
// run35.mjs
// out/ 의 방출물을 하나씩 node 에게 부른다 -- 풀리면 값, 못 풀면 오류 코드
for (const f of ["imp35a", "imp35b", "imp35c", "imp35d", "imp35e", "imp35f"]) {
    try {
        const m = await import(`./out/${f}.js`);
        console.log(f, "value", m.v);
    } catch (e) {
        console.log(f, "error", e.code);
    }
}
```

```bash
# ts34b-pair35.sh
#!/usr/bin/env bash
# 같은 여섯 파일 -- tsc(nodenext) 판정 · tsc(bundler) 판정 · bundler 로 방출한 것을 node 가 푼 결과
# 방출은 진단이 있어도 된다(규칙: tsc 는 에러여도 방출한다) -- node 가 볼 파일을 만들려고 bundler 로 한 번 방출
set -u -o pipefail
cd p35 || exit 1
rm -rf out
tsc --pretty false -t es2022 --module esnext --moduleResolution bundler --rootDir src --outDir out src/*.ts src/dir35/index.ts > /dev/null 2>&1
node run35.mjs > .node35.txt 2>&1
verdict() { if [ -z "$1" ]; then echo OK; else echo "$1"; fi; }
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-8s %-10s %-10s %s\n' "파일" "nodenext" "bundler" "node(v18)"
same_nn=0; same_b=0; total=0
for f in imp35a imp35b imp35c imp35d imp35e imp35f; do
  nn=$(verdict "$(cd src && tsc --pretty false --noEmit --module nodenext "$f.ts" 2>&1 | codes)")
  bu=$(verdict "$(cd src && tsc --pretty false --noEmit --module esnext --moduleResolution bundler "$f.ts" 2>&1 | codes)")
  nd=$(grep "^$f " .node35.txt | cut -d' ' -f2-)
  printf '%-8s %-10s %-10s %s\n' "$f" "$nn" "$bu" "$nd"
  total=$((total+1))
  case $nd in value*) ndok=1 ;; *) ndok=0 ;; esac
  if { [ "$nn" = OK ] && [ $ndok = 1 ]; } || { [ "$nn" != OK ] && [ $ndok = 0 ]; }; then same_nn=$((same_nn+1)); fi
  if { [ "$bu" = OK ] && [ $ndok = 1 ]; } || { [ "$bu" != OK ] && [ $ndok = 0 ]; }; then same_b=$((same_b+1)); fi
done
rm -rf out .node35.txt
echo
echo "node 와 같은 판정 -- nodenext $same_nn / $total · bundler $same_b / $total"
```

```text
===== bash ts34b-pair35.sh (sh exit=0) =====
파일   nodenext   bundler    node(v18)
imp35a   TS2835     OK         error ERR_MODULE_NOT_FOUND
imp35b   OK         OK         value util35
imp35c   TS5097     TS5097     error ERR_MODULE_NOT_FOUND
imp35d   TS2834     OK         error ERR_UNSUPPORTED_DIR_IMPORT
imp35e   OK         OK         value feature35
imp35f   TS2307     TS2307     error ERR_PACKAGE_PATH_NOT_EXPORTED

node 와 같은 판정 -- nodenext 6 / 6 · bundler 4 / 6
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`nodenext` 판정과 node 판정이 여섯 칸 다 같다 — 6 / 6.** `nodenext` 는 node 의 해석을 **정확히** 흉내 냈다.
- ★★★ **`bundler` 는 4 / 6** — `imp35a`(확장자 없음) · `imp35d`(디렉토리) 둘을 **`OK` 로 통과시켰는데** node 는 각각 **`ERR_MODULE_NOT_FOUND`** · **`ERR_UNSUPPORTED_DIR_IMPORT`**.
  node 의 ESM 은 **확장자를 붙여 보지 않고 디렉토리의 `index` 를 찾지 않는다** — 3절 추적에서 `nodenext` 가 **시도조차 안 한** 것과 같은 규칙이다.
- ★★ `imp35e`(`pkg35/feature`) — node 가 **`feature35`** 를 찍었다. node 는 `exports` 의 **`default`**(`./out/feature35.js`)로 갔고 tsc 는 **`types`**(`./src/feature35.ts`)로 갔다 — **같은 지정자, 다른 파일, 같은 판정**.
- ★★ `imp35f` — tsc 의 `TS2307` 과 node 의 **`ERR_PACKAGE_PATH_NOT_EXPORTED`** 가 짝이다. **`exports` 에 없는 경로는 둘 다 막는다.**
- ★★ `imp35c`(`.ts` 확장자) — tsc 는 `TS5097` 로 막지만 **방출은 한다**(02편 — 에러여도 방출). 방출물의 `"./util35.ts"` 를 node 가 `out/` 에서 못 찾아 `ERR_MODULE_NOT_FOUND`.
- ★ 방출은 **`bundler` 로 한 번** 했다 — node 에게 줄 파일을 만들려고. **import 경로는 한 글자도 안 바뀌므로** 어느 설정으로 방출해도 node 의 판정은 같다(핸드북 — TS 는 지정자를 **다시 쓰지 않는다**).

```text
  세 판정의 한 쌍 — node(v18) 가 기준

                  nodenext   bundler    node
  "./util35"      TS2835     ✓          ERR_MODULE_NOT_FOUND        ← bundler 가 새어 보냈다
  "./util35.js"   ✓          ✓          value
  "./util35.ts"   TS5097     TS5097     ERR_MODULE_NOT_FOUND
  "./dir35"       TS2834     ✓          ERR_UNSUPPORTED_DIR_IMPORT  ← bundler 가 새어 보냈다
  "pkg35/feature" ✓          ✓          value
  "pkg35/src/…"   TS2307     TS2307     ERR_PACKAGE_PATH_NOT_EXPORTED
                  ★ 6 / 6     ★ 4 / 6
```

비용 — **`bundler` 는 「번들러가 실행 전에 한 번 더 푼다」는 가정 위에서만 참이다.** 번들러 없이 node 로 돌리면 그 가정이 깨진다.

### (5) ★★★ `nodenext` 는 움직이는 과녁이다 — CJS 파일이 ESM 을 부를 때

**언제 쓰나** — `.cts`(또는 `type` 없는 패키지의 `.ts`)에서 ESM 파일을 import 할 때. JS 쪽 규칙(CJS 의 `require` 가 ESM 을 부르면 막힌다)은 [JS 갈래 **43번**(CJS 와 ESM 상호운용)](../../../js/syntax/43-cjs-and-esm-interop/) 몫이다.

```ts
// c35.cts
import { util } from "./util35.js";
console.log("[1]", util);
```

```bash
# ts34b-cjs35.sh
#!/usr/bin/env bash
# p35/src/c35.cts(CJS) 가 같은 패키지의 ESM(util35.ts) 을 import -- --module 값 넷 × 세 판
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
cd p35/src || exit 1
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-12s %-10s %-10s %s\n' "--module" "7.0.2" "5.9.3" "4.9.5"
split=0; total=0
for m in node16 node18 node20 nodenext; do
  a=$(tsc --pretty false --noEmit --module "$m" c35.cts 2>&1 | codes)
  b=$(node "$OLD" --pretty false --noEmit --module "$m" c35.cts 2>&1 | codes)
  c=$(node "$V49" --pretty false --noEmit --module "$m" c35.cts 2>&1 | codes)
  printf '%-12s %-10s %-10s %s\n' "$m" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1)); [ "$a" != "$c" ] && split=$((split+1))
done
echo
echo "7.0.2 와 4.9.5 가 갈린 행 $split / $total"
```

```text
===== bash ts34b-cjs35.sh (sh exit=0) =====
--module     7.0.2      5.9.3      4.9.5
node16       TS1479     TS1479     TS1479
node18       TS1479     TS1479     TS6046
node20       OK         OK         TS6046
nodenext     OK         OK         TS1479

7.0.2 와 4.9.5 가 갈린 행 3 / 4
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`--module nodenext` 가 판마다 다른 답을 낸다** — 4.9.5 **`TS1479`**(「The current file is a CommonJS module whose imports will produce 'require' calls; however, the referenced file is an ECMAScript module and cannot be imported with 'require'.」), **5.9.3 · 7.0.2 는 `OK`**.
- ★★ **`node16`·`node18` 은 세 판 다(있는 판에서) `TS1479`**, **`node20` 은 `OK`**. `node18`·`node20` 은 4.9.5 에 **없는 값**(`TS6046`).
- ★★★ 읽는 법 — `nodenext` 는 「**그 판의 tsc 가 아는 가장 새 node**」를 흉내 낸다. 4.9.5 의 `nodenext` 는 `node16` 과 같았고, 5.9.3·7.0.2 의 `nodenext` 는 **`node20` 쪽**(ESM 을 `require` 할 수 있는 node)이다.
- ★★ 마지막 줄 **7.0.2 와 4.9.5 가 갈린 행 3 / 4**.

```js
// run35c.cjs
// 방출된 CJS 파일을 node 에게 부른다 -- 오류면 이름과 코드만
try {
    require("./oc35/c35.cjs");
} catch (e) {
    console.log(e.constructor.name, e.code);
}
```

```text
===== cd p35 && tsc --pretty false -t es2022 --module nodenext --rootDir src --outDir oc35 src/c35.cts src/util35.ts (tsc exit=0) =====
===== 방출된 oc35/c35.cjs =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const util35_js_1 = require("./util35.js");
console.log("[1]", util35_js_1.util);
```

```text
===== cd p35 && node run35c.cjs (node exit=0) =====
Error ERR_REQUIRE_ESM
```

- ★★★ **7.0.2 `nodenext` 가 통과시킨 `c35.cts` 를 node v18 이 `ERR_REQUIRE_ESM` 으로 막는다.** 방출물은 `require("./util35.js")` 이고, `util35.js` 는 `type: "module"` 패키지의 **ESM** 이다.
- ★★★ **tsc 는 「어느 node」인지 모른다** — 이 머신의 node 는 **v18** 인데 `nodenext` 는 **더 새 node** 를 가정했다. **`--module node18` 이었다면 `TS1479` 로 미리 막혔다**(격자의 `node18` 행).
- ★ 새 node 에서 이 `require` 가 **되는지는 던지지 못했다** — 이 머신에 v18 뿐이다.

```text
  같은 c35.cts — 흉내 낼 node 를 누가 정하나

  --module node18     tsc: TS1479   ─┐
                                     ├─ node v18: ERR_REQUIRE_ESM   ← node18 이 호스트와 맞다
  --module nodenext   tsc: OK (7.0.2)┘
                      ★ nodenext = 「이 tsc 가 아는 가장 새 node」 — 호스트 판과 무관하다
```

비용 — **`nodenext` 는 tsc 를 올릴 때마다 뜻이 움직인다.** 호스트 node 의 판을 **고정해야** 하는 곳(배포 환경이 v18 인 서버 등)에서는 **`node18` 처럼 판을 박은 값**이 호스트와 맞는다.

### (6) ★★ 7.0 뒤의 설정 — `paths` 는 tsc 만 아는 별칭이다

**언제 쓰나** — `baseUrl` 이 없어진 뒤 별칭 import(`@src/…`)를 쓰려 할 때.

```text
===== 소스: p35g/tsconfig.json =====
{
  "compilerOptions": {
    "module": "nodenext",
    "target": "es2022",
    "rootDir": "src",
    "outDir": "outg",
    "paths": {
      "@src/*": ["./src/*"]
    }
  },
  "files": ["src/imp35g.ts"]
}
===== 소스: p35g/package.json =====
{
  "type": "module"
}
```

```ts
// util35g.ts
export const util = "util35g";
```

```ts
// imp35g.ts
export { util as v } from "@src/util35g.js";
```

```text
===== cd p35g && tsc --pretty false -p tsconfig.json (tsc exit=0) =====
===== 방출된 outg/imp35g.js =====
export { util as v } from "@src/util35g.js";
```

```js
// run35g.mjs
// paths 로 쓴 import 를 node 에게 부른다 -- 오류면 이름과 코드만
try {
    const m = await import("./outg/imp35g.js");
    console.log("value", m.v);
} catch (e) {
    console.log(e.constructor.name, e.code);
}
```

```text
===== cd p35g && node run35g.mjs (node exit=0) =====
Error ERR_MODULE_NOT_FOUND
```

```text
===== cd p35g && node "$TSC_OLD" --pretty false --noEmit -p tsconfig.json ; 이어서 "$TSC_49" 로 같은 것 (sh exit=0) =====
(exit 0)
(exit 0)
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`baseUrl` 없이 `paths` 만** — 7.0.2 가 `exit 0`. 6.0 릴리스 글의 처방(「`paths` 항목에 접두를 직접 넣어라」)대로 `"./src/*"` 를 **설정 파일 기준 상대 경로**로 적었다.
- ★★★ **방출물의 import 는 `"@src/util35g.js"` 그대로** — tsc 는 별칭을 **풀어서 검사만** 하고, 경로는 **다시 쓰지 않는다.**
- ★★★ node → **`ERR_MODULE_NOT_FOUND`**. node 는 `@src` 가 무엇인지 **모른다.** 핸드북의 문장 그대로 — 「TypeScript 는 통과, Node.js 는 깨진다」.
- ★★ 같은 설정을 5.9.3 · 4.9.5 에 — 둘 다 `(exit 0)`. **`baseUrl` 없는 `paths` 는 옛 판에서도 됐다** — 7.0 은 **`baseUrl` 만** 뺐다.

```text
===== cd p35g/src && tsc --pretty false --noEmit imp35g.ts ; 이어서 "$TSC_OLD" · "$TSC_49" 로 같은 것 (sh exit=0) =====
error TS5112: tsconfig.json is present but will not be loaded if files are specified on commandline. Use '--ignoreConfig' to skip this error.
(exit 1)
imp35g.ts(1,27): error TS2307: Cannot find module '@src/util35g.js' or its corresponding type declarations.
(exit 2)
imp35g.ts(1,27): error TS2307: Cannot find module '@src/util35g.js' or its corresponding type declarations.
(exit 2)
```

- ★★★ **7.0.2 의 새 진단 `TS5112`** — 「tsconfig.json is present but will not be loaded if files are specified on commandline. Use '--ignoreConfig' to skip this error.」
  `p35g/src` 에서 **파일을 직접 줬는데**, 한 단계 **위** `p35g/` 에 `tsconfig.json` 이 있자 **검사를 거부했다.** 5.9.3 · 4.9.5 는 설정 파일을 **무시하고** 파일만 검사해 `TS2307`(`paths` 가 없으니 `@src` 를 못 푼다).
- ★★★ **02편 7절의 「파일을 직접 주면 `tsconfig.json` 을 무시한다」가 7.0.2 에서 바뀐 자리다** — 02편의 블록들은 설정 파일이 없는 디렉토리에서 던져 이 칸을 안 밟았다.
  ★ 이 배치도 처음에 한 번 밟았다 — `p35/` 에 `tsconfig.json` 을 두자 2·4·5절 격자의 7.0.2 칸이 **전부 `TS5112`** 로 바뀌었고, 설정 실험을 `p35g/` 로 옮겨 다시 찍었다. **격자가 「전부 같은 코드」를 찍으면 격자가 아니라 환경을 의심해라.**
- ★ 종료 코드 — 7.0.2 `1` · 5.9.3·4.9.5 `2`(`--noEmit` 인데). **판마다 다르다** — 그래서 격자를 진단 코드로 갈랐다.

```text
  7.0 뒤의 설정 — 이 문서가 던진 것에서

  node 로 바로 돌린다          "module": "nodenext" (또는 호스트 판을 박은 node18)   ← 4절 6 / 6 · 5절
                               import 는 "./util35.js" 처럼 확장자까지
  번들러가 푼다                "module": "esnext", "moduleResolution": "bundler"     ← 4절: node 로 돌리면 4 / 6
  별칭                         "paths": { "@src/*": ["./src/*"] }  (baseUrl 없이)     ← 런타임은 별도로 알려 줘야 한다
  사라진 것                    node10 · node · classic (TS5108) · baseUrl (TS5102)
```

비용 — `paths` 를 쓰면 **런타임에도 같은 별칭을 알려 줄 장치**(번들러 설정 · `package.json` 의 `imports` 등)가 따로 필요하다. 그 장치는 **던지지 않았다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  --moduleResolution nodenext   상대 ESM import 에 확장자 필요 · exports 를 따른다        (2·4절)
  --moduleResolution bundler    확장자·디렉토리 index 를 붙여 본다 · exports 를 따른다    (2·3절)
  import … from "./a.js"        a.ts 를 가리킨다 — 방출 뒤의 이름                           (2·3절)
  "exports": { "./x": { "types": …, "default": … } }   tsc 는 types, node 는 default     (3·4절)
  "paths": { "@src/*": ["./src/*"] }                   tsc 만 안다 — 경로는 안 바뀐다     (6절)
  --traceResolution             tsc 의 해석 과정을 찍는다 — 절대 경로가 박힌다            (3절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| 7.0.2 에서 `--moduleResolution node10`·`node`·`classic` | `TS5108` | 1절 · 02편 7절 |
| 7.0.2 에서 `--baseUrl` | `TS5102` | 1절 |
| 5.9.3 에서 `bundler` + `--module commonjs` | `TS5095` | 1절 |
| 4.9.5 에서 `node10`·`bundler`·`node18`·`node20` | `TS6046` | 1·5절 |
| `nodenext` 에서 확장자 없는 상대 경로 · 디렉토리 | `TS2835` · `TS2834` | 2절 |
| `.ts` 확장자 import(설정 없이) | `TS5097` | 2절 |
| `classic` 에서 디렉토리·패키지 | `TS2792` | 2절 |
| `exports` 에 없는 경로 · `node10` 에서 `exports` 경로 | `TS2307` | 2절 |
| CJS 파일이 ESM 을 import — `node16`·`node18`(·4.9.5 `nodenext`) | `TS1479` | 5절 |
| 7.0.2 에서 설정 파일 아래 디렉토리에 파일을 직접 줌 | `TS5112` | 6절 |

**규칙 불릿**

- ★★★ **7.0 은 `node10`(`node`)·`classic` 값과 `baseUrl` 옵션을 없앴고, 기본 해석을 `Bundler` 로 바꿨다**(1절).
- ★★★ **`nodenext` 의 판정은 node 와 같고, `bundler` 의 판정은 node 보다 넓다**(4절 — 6 / 6 대 4 / 6).
- ★★★ **tsc 는 import 경로를 다시 쓰지 않는다** — 확장자·별칭 전부 적힌 그대로 방출된다(4·6절).
- ★★ **`nodenext` 는 「이 tsc 가 아는 가장 새 node」다** — 호스트 판과 맞추려면 판을 박은 값을 쓴다(5절).

## 어디서 틀리나

- ★★★ 「**tsc 가 import 를 통과시켰으니 실행된다**」 — `bundler` 로 검사한 **확장자 없는 경로·디렉토리**가 node 에서 깨진다(4절).
- ★★★ 「**`.ts` 파일을 가져오니 `.ts` 로 적는다**」 — `TS5097`. `nodenext` 는 **`.js`** 로 적기를 요구한다(2절).
- ★★★ 「**5.x 설정을 그대로 7.0 에 올려도 된다**」 — `node10`·`classic`·`baseUrl` 은 **막히고**, 아무것도 안 적은 프로젝트는 **조용히 `Bundler`** 로 바뀐다(1절).
- ★★★ 「**`nodenext` 면 지금 쓰는 node 와 맞다**」 — **tsc 판이 정한 node** 다. node v18 에서 `ERR_REQUIRE_ESM`(5절).
- ★★★ 「**`paths` 를 설정했으니 별칭이 동작한다**」 — **tsc 에서만.** 방출물은 `@src/…` 그대로, node 는 `ERR_MODULE_NOT_FOUND`(6절).
- ★★ 「**`exports` 가 있어도 깊은 경로로 가져오면 된다**」 — tsc `TS2307`, node `ERR_PACKAGE_PATH_NOT_EXPORTED`(2·4절).
- ★★ 「**파일을 직접 주면 설정 파일은 무시된다**」 — 7.0.2 는 **위쪽에 설정 파일이 있으면 `TS5112`** 로 거부한다(6절). 옛 판의 성질이었다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **호스트(node) 규칙** | ESM 의 상대 import 는 **확장자를 붙여 보지 않고 디렉토리 `index` 를 찾지 않는다** · `exports` 밖 경로 차단 · CJS `require` 가 ESM 을 부르면(v18) 막힌다 | 4·5절의 `node` 출력 — **node v18.19.1 의 관찰** |
| **컴파일러(tsc) — 호스트 흉내** | `node16`·`nodenext` 는 위 규칙을 흉내 내고, `bundler` 는 번들러의 관대한 규칙을 흉내 낸다 | 2·3절 · 핸드북 Modules Reference |
| **컴파일러 보장(핸드북)** | TS 는 import 지정자를 **다시 쓰지 않는다** · `paths` 는 방출물을 안 바꾼다 · `exports` 의 `types` 조건을 먼저 맞춘다 | 핸드북 · 4·6절 |
| **판 경계(7.0.2)** | `node10`·`classic` 값 제거(`TS5108`) · `baseUrl` 옵션 제거(`TS5102`) · 기본 해석 `Bundler` · `bundler`+`commonjs` 허용 · `TS5112` | 1·6절 — **세 판을 던졌다** |
| **판 경계(5.0 · 4.9.5)** | `node10` 이름·`bundler` 는 5.0 부터(4.9.5 `TS6046`) | 1절 — ★ 5.0 그 자체는 **없다** |
| **★ 이 판의 관찰** | `nodenext` 가 5.9.3·7.0.2 에서 CJS→ESM import 를 받는다(4.9.5 는 `TS1479`) | 5절 |
| **★ 이 판의 관찰** | `bundler` 추적이 ESM 파일에 「CJS mode」라 적는다 | 3절 — 까닭은 **확인 못 했다** |
| **★ 부적용 — 5창(`.d.ts` 방출)** · **2창** | 이 주제의 질문은 「풀리나」 | — |
| **안 잰 것** | 해석 방식별 검사 시간 · 새 node(v20+)에서의 5절 | **재지 않았다** · 이 머신에 v18 뿐 |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **`nodenext`**(또는 호스트 판을 박은 `node18`·`node20`) — **번들러 없이 node 로** 돌리는 코드 · 라이브러리 | **`bundler`** 로 검사하고 **node 로 바로** 돌리기 — 4절의 두 칸이 샌다 |
| ★★ **`bundler`** — 번들러(와 그 개발 서버)가 **실행 전에 반드시** 푸는 앱 | ★★★ **`node10`·`node`·`classic`·`baseUrl`** — 7.0.2 가 막는다 |
| ★★ **`.js` 확장자로 적은 상대 import** — 다섯 해석 방식이 다 받는다(2절) | **`.ts` 확장자** — 설정 없이는 `TS5097` |
| ★ **`paths`**(baseUrl 없이) — **런타임에도 같은 별칭**을 알려 줄 장치가 있을 때 | 런타임 장치 없는 `paths` — 6절 `ERR_MODULE_NOT_FOUND` |
| **`--traceResolution`** — 「왜 안 풀리나」를 볼 때 | 그 출력을 문서·로그에 **경로째** 싣기 — 절대 경로가 박힌다 |

## 핵심 문장

1. **7.0.2 는 `node10`·`node`·`classic` 을 `TS5108`, `baseUrl` 을 `TS5102` 로 막고, 아무것도 안 주면 `Bundler` 를 고른다** — 받아들인 행 **4 / 8**(5.9.3 은 7 / 8), 7.0.2 와 5.9.3 이 갈린 행 **5 / 8**.
2. **같은 import 가 해석 방식마다 다르게 풀린다** — 해석 격자 **13 / 30**. 다섯 방식이 다 받는 모양은 **`.js` 로 적은 상대 경로** 하나다.
3. **tsc 의 해석은 호스트의 흉내다** — `nodenext` 는 node 와 **6 / 6**, `bundler` 는 **4 / 6**. tsc 는 경로를 **다시 쓰지 않으니** 판정이 어긋나면 node 에서 깨진다.
4. **`nodenext` 는 tsc 판이 정한 node 이고, `paths` 는 tsc 만 아는 별칭이다** — 둘 다 **호스트가 모르는 약속**을 tsc 가 통과시킨 자리다.

## 관련 자료

- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — ★★★ **README 의 선행.** `tsconfig.json` 의 `moduleResolution=node10` 이 `TS5108` 인 것 · `TS5102` 와 `TS5108` 의 구분 · 에러여도 방출한다는 것은 그쪽 1·7절이 정본이다. **여기는 세 판 × 여덟 행 · import 경로 격자 · node 와의 한 쌍부터.** ★ 그쪽의 「파일을 직접 주면 설정 파일을 무시한다」는 7.0.2 의 `TS5112` 로 **바뀐 자리**가 있다(6절).
- [JS 갈래 **42번**(ESM 모듈)](../../../js/syntax/42-esm-modules/) · [JS 갈래 **43번**(CJS 와 ESM 상호운용)](../../../js/syntax/43-cjs-and-esm-interop/) — ★★★ **README 의 선행(JS 43).** node 쪽 규칙(확장자·`type` 필드·`require` 와 ESM)의 정본이다 — 이 문서는 node 출력을 직접 던져 실었다.
- [Python 갈래 — 모듈·패키지와 import](../../../python/syntax/42-modules-packages-and-import/) — 대비. 파이썬은 import 해석을 **런타임 하나**가 하고(검사기와 실행기가 따로 없다), 상대 import 의 기준이 **`__package__`** 라 `python3 pkg/mod.py` 와 `-m` 이 갈린다(그쪽 5절). TS 는 **검사기와 실행기가 따로** 풀어서 **둘이 어긋날** 수 있다.
- [Go 갈래 — 패키지 공개 범위·이름·`internal`](../../../go/syntax/40-package-visibility-naming-and-internal/) — 대비. Go 는 import 경로가 **곧 모듈 경로**(`go.mod` 의 `module` + 디렉토리)이고, 빌드 도구 **하나**가 해석과 실행을 다 맡는다 — 해석 방식을 고를 일이 없다.
- 목록의 **36번 주제**(타입 전용 import·export) — 사슬의 다음. **풀린 import 가 방출물에 남나**를 묻는다.
- 목록의 **43번 주제**(`tsconfig` 의 나머지 선택) — `module` 값의 일반론.

## 용어 풀이

> **모듈 지정자(module specifier)** — `from` 뒤 따옴표 안의 문자열. `"./util35.js"` · `"pkg35/feature"`.\
> 예: 2절의 여섯 파일이 지정자만 다르다.

> **모듈 해석(module resolution)** — 지정자를 **실제 파일**로 바꾸는 규칙. tsc 는 `--moduleResolution` 으로 고르고, 실행 때는 호스트가 제 규칙으로 한다.\
> 예: 3절 추적.

> **`nodenext`** — tsc 가 **그 판이 아는 가장 새 node** 의 해석을 흉내 내는 값. tsc 판이 오르면 뜻이 움직인다.\
> 예: 5절 — 4.9.5 `TS1479`, 7.0.2 `OK`.

> **`bundler`** — 번들러의 해석을 흉내 낸다. 확장자·디렉토리 `index` 를 붙여 본다. 7.0.2 의 **기본값**.\
> 예: 4절 `imp35a` 를 통과시켰다.

> **`exports` 필드** — `package.json` 에서 **밖에 열어 줄 경로**와 조건(`types`·`import`·`default`)을 적는 곳. 적지 않은 경로는 막힌다.\
> 예: 3절 `Matched 'exports' condition 'types'`.

> **자기 이름 참조(self-reference)** — 패키지 안에서 **자기 패키지 이름**으로 import 하는 것. `exports` 가 있어야 된다. 이 문서는 이것으로 `node_modules` 없이 `exports` 를 시험했다.\
> 예: 2절 `imp35e "pkg35/feature"`.

> **`paths`** — tsc 에게만 주는 별칭 표. 방출물의 경로는 **안 바뀐다.**\
> 예: 6절.

> **`TS5108` / `TS5102`** — 「그 **값**이 제거됐다」 / 「그 **옵션**이 제거됐다」.\
> 예: 1절 `node10` / `baseUrl`.

> **`TS2835` · `TS2834`** — `node16`·`nodenext` 의 상대 ESM import 에 확장자가 없다(앞쪽은 고칠 이름까지 제안한다).\
> 예: 2절 `imp35a` · `imp35d`.

> **`TS1479`** — CJS 파일의 import 가 `require` 가 되는데, 대상이 ESM 이라 `require` 로 부를 수 없다.\
> 예: 5절 `node18`.

> **`TS5112`** — 7.0.2 — 설정 파일이 있는데 명령줄에 파일을 줘서 설정을 안 읽게 된다. `--ignoreConfig` 로 넘긴다.\
> 예: 6절.

## 더 들어가면

- **`--rewriteRelativeImportExtensions`**(5.7) — `.ts` 로 적은 상대 import 를 방출 때 `.js` 로 **바꿔 쓰는** 플래그. 「TS 는 경로를 다시 쓰지 않는다」의 **예외**다. 7.0.2 가 이 플래그를 **받는다**는 것까지만 36번 판 격자에서 봤고, **방출은 던지지 않았다.**
- **`package.json` 의 `imports`(`#` 별칭)** — node 도 아는 별칭이라 `paths` 의 런타임 문제가 없다. **던지지 않았다.**
- **`bundler` 의 「CJS mode」** — 3절의 문구. 해석 모드와 조건 이름의 관계는 **확인하지 못했다.**
- **새 node(v20+)에서 5절** — `require(esm)` 이 되는 node 라면 `nodenext` 의 판정이 맞는다. 이 머신에 없다.
