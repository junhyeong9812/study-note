# ts/syntax/35 — 모듈 해석 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **35 는 02 에서 온다** — [**02번 주제**](../02-type-checking-vs-emit/) 7절이 `tsconfig.json` 의 `moduleResolution: "node10"` 이 7.0.2 에서 `TS5108` 인 것을 이미 쟀다. 여기서는 그것을 **세 판**으로 넓히고, **같은 import 문**이 해석 방식마다 어떻게 풀리는지, 그리고 **node 가 실제로 푸는지**를 한 쌍으로 묻는다.
> JS 쪽 짝은 [JS 갈래 **42번**(ESM 모듈)](../../../js/syntax/42-esm-modules/) · [JS 갈래 **43번**(CJS 와 ESM 상호운용)](../../../js/syntax/43-cjs-and-esm-interop/) 이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ JSON 파일은 주석을 달 수 없어 `===== 소스: 경로 =====` 배너로 싣는다.
> ★★ 격자는 판마다 **진단 코드**만 뽑는다(종료 코드는 판마다 다르다).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 해석 옵션을 판마다 (예측)

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

- 각 행에 7.0.2 · 5.9.3 · 4.9.5 가 무엇을 내는가? 아무것도 안 줬을 때 판마다 어느 해석 방식을 고르는가? 마지막 줄의 수는?

### 2. 같은 import 문을 해석 방식마다 (예측)

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

- (`index.ts` 는 `p35/src/dir35/` 안에 있다.) 서른 칸 각각은 풀리는가, 무슨 코드로 막히는가? 마지막 줄의 수는?

### 3. tsc 가 찾아본 길 (예측)

- `imp35a.ts` 를 `--module nodenext` 와 `--moduleResolution bundler` 로 각각 `--traceResolution` 하면, 후보 `./util35` 다음 줄에 무엇이 오는가?
- `imp35b.ts`(`"./util35.js"`) 를 `nodenext` 로 추적하면 어느 파일로 풀리는가? 그 사이에 tsc 는 무엇을 하는가?
- `imp35e.ts`(`"pkg35/feature"`) 를 `nodenext` 로 추적하면 `exports` 의 **어느 조건**을 쓰는가?

### 4. tsc 의 판정과 node 의 판정 (예측)

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

- 여섯 줄의 세 칸(nodenext · bundler · node)은 각각 무엇인가? 마지막 줄의 두 수는?

### 5. CJS 파일이 같은 패키지의 ESM 을 (예측)

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

```js
// run35c.cjs
// 방출된 CJS 파일을 node 에게 부른다 -- 오류면 이름과 코드만
try {
    require("./oc35/c35.cjs");
} catch (e) {
    console.log(e.constructor.name, e.code);
}
```

- 격자의 네 행 × 세 판은? 마지막 줄의 수는?
- 7.0.2 `--module nodenext` 로 방출한 `oc35/c35.cjs` 를 `run35c.cjs` 로 부르면 node v18 이 무엇을 찍는가?

### 6. `paths` 별칭 (예측)

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

- `cd p35g && tsc -p tsconfig.json` 은 통과하는가? 방출된 `outg/imp35g.js` 의 import 경로는? `node run35g.mjs` 는?
- 같은 설정을 5.9.3 · 4.9.5 로 `--noEmit -p` 하면?
- `cd p35g/src` 에서 **`imp35g.ts` 를 직접** 주고 `--noEmit` 하면 세 판이 각각 무엇을 내는가?

### 7. 다섯 방식이 다 받는 모양 (왜)

- 2번에서 다섯 칸이 전부 풀린 import 는 하나뿐이다. 없는 파일 이름(`.js`)을 적었는데 왜 풀리는가? 3번의 추적 한 줄로 설명할 수 있는가?

### 8. 번들러의 판정이 새는 자리 (왜)

- 4번에서 `bundler` 는 통과시켰는데 node 가 막은 칸들에 공통인 것은 무엇인가? 3번의 두 추적 중 어느 쪽이 node 와 같은 일을 했는가?

### 9. `nodenext` 는 무엇을 흉내 내나 (경계)

- 5번에서 같은 `--module nodenext` 가 판마다 답이 갈렸다. `nodenext` 가 흉내 내는 node 를 정하는 것은 **이 머신의 node** 인가 **tsc 의 판** 인가? 호스트와 맞추려면 무엇을 고르는가?

### 10. 진단이 없는 판 변화 (경계)

- 1번에서 7.0 의 변화 중 **진단이 아예 안 나는** 것은 무엇인가? 그 변화를 프로젝트에서 확인하려면 무엇을 찍어 보는가?

### 11. 02·JS·파이썬과 잇기 (연결)

- 6번의 마지막 결과는 02편 7절의 어느 문장과 어긋나는가?
- 파이썬 42편 5절의 「스크립트 실행 대 `-m` 실행」과 이 주제의 「tsc 판정 대 node 판정」은 **어긋나는 까닭**이 어떻게 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
