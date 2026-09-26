# ts/syntax/44 — 프로젝트 참조와 선언 방출 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·빌드 로그·생긴 파일은 `tsc` **7.0.2** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 「프로젝트 참조 격자」(16칸)이다.** 「`app` 이 무엇을 보나」는 해석 창이 `.ts` 라고 답해 **프로그램 창(`--explainFiles`)과 `.d.ts` 고쳐 보기로** 바꿔 물었다(제5의 상태).\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 빌드된 칸 **`2 / 16`**(있음 · 있음 · `tsc -b`) · 있음 · 있음 · `-p` **`TS6305`** · `composite` 없음 **`TS6306`** · `references` 없음 **`TS6059`** — 두 판은 `TS6059` 의 `-b` 칸에서 **종료 코드만** 다르다(7.0.2 `2` · 5.9.3 `1`)

**출력**

```ts
// index.ts
export function add(a: number, b: number): number {
    return a + b;
}
```

```ts
// main.ts
import { add } from "../../core/src/index";
console.log(add(1, 2));
```

```bash
# ts42b-refs44.sh
#!/usr/bin/env bash
# core·app 두 프로젝트 × core 의 composite 있음/없음 × app 의 references 있음/없음 × tsc -b app / tsc -p app × 판 둘
# 칸마다 p44 를 새 디렉토리에 복사하고 두 tsconfig.json 을 그 칸의 설정으로 다시 쓴다(p44 의 두 파일은 「있음 · 있음」 칸이다)
# 칸 = 진단 코드 · 종료 코드 · 생긴 .js/.d.ts
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
core_cfg() { printf '{ "compilerOptions": { %s"target": "es2022", "outDir": "dist", "rootDir": "src" }, "include": ["src"] }\n' "$([ "$1" = 있음 ] && echo '"composite": true, ')"; }
app_cfg()  { printf '{ "compilerOptions": { "target": "es2022", "outDir": "dist", "rootDir": "src" }, "include": ["src"]%s }\n' "$([ "$1" = 있음 ] && echo ', "references": [{ "path": "../core" }]')"; }
printf '%-10s %-12s %-6s %-6s %-14s %-5s %s\n' "composite" "references" "명령" "판" "진단" "exit" "생긴 파일"
i=0; ok=0; split=0; total=0; all=""
for comp in 있음 없음; do for refs in 있음 없음; do for cmd in -b -p; do
  declare -A got=()
  for v in 7.0.2 5.9.3; do
    i=$((i+1)); w="$D/c$i"; cp -r p44 "$w" || exit 3
    core_cfg "$comp" > "$w/core/tsconfig.json"; app_cfg "$refs" > "$w/app/tsconfig.json"
    if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
    raw=$(cd "$w" && "${c[@]}" "$cmd" app --pretty false 2>&1); rc=$?
    case "$raw" in *TS5112*|*TS5023*) echo "★ 설정·명령 진단이 칸에 들었다 -- 격자를 믿지 마라: $raw"; exit 4 ;; esac
    files=$(cd "$w" && find core app -path '*/dist/*' \( -name '*.js' -o -name '*.d.ts' \) | sort | tr '\n' ' ' | sed 's/ $//')
    got[$v]="$(codes <<< "$raw")|$rc|$files"
    IFS='|' read -r cd_ rc_ f_ <<< "${got[$v]}"
    printf '%-10s %-12s %-6s %-6s %-14s %-5s %s\n' "$comp" "$refs" "$cmd" "$v" "${cd_:-OK}" "$rc_" "${f_:-없음}"
    total=$((total+1)); [ -z "$cd_" ] && [ "$rc_" = 0 ] && ok=$((ok+1)); all="$all#${cd_:-OK}"
  done
  [ "${got[7.0.2]}" != "${got[5.9.3]}" ] && split=$((split+1))
  unset got
done; done; done
kinds_seen=$(tr '#' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같은 코드다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "진단 없이 빌드된 칸 $ok / $total · 두 판이 갈린 칸(진단·exit·파일 중 하나라도) $split / $((total / 2))"
```

```text
===== bash ts42b-refs44.sh (sh exit=0) =====
composite  references   명령 판    진단         exit  생긴 파일
있음     있음       -b     7.0.2  OK             0     app/dist/main.js core/dist/index.d.ts core/dist/index.js
있음     있음       -b     5.9.3  OK             0     app/dist/main.js core/dist/index.d.ts core/dist/index.js
있음     있음       -p     7.0.2  TS6305         2     app/dist/main.js
있음     있음       -p     5.9.3  TS6305         2     app/dist/main.js
있음     없음       -b     7.0.2  TS6059         2     app/dist/main.js
있음     없음       -b     5.9.3  TS6059         1     app/dist/main.js
있음     없음       -p     7.0.2  TS6059         2     app/dist/main.js
있음     없음       -p     5.9.3  TS6059         2     app/dist/main.js
없음     있음       -b     7.0.2  TS6306         2     app/dist/main.js core/dist/index.js
없음     있음       -b     5.9.3  TS6306         2     app/dist/main.js core/dist/index.js
없음     있음       -p     7.0.2  TS6306         2     app/dist/main.js
없음     있음       -p     5.9.3  TS6306         2     app/dist/main.js
없음     없음       -b     7.0.2  TS6059         2     app/dist/main.js
없음     없음       -b     5.9.3  TS6059         1     app/dist/main.js
없음     없음       -p     7.0.2  TS6059         2     app/dist/main.js
없음     없음       -p     5.9.3  TS6059         2     app/dist/main.js

진단 없이 빌드된 칸 2 / 16 · 두 판이 갈린 칸(진단·exit·파일 중 하나라도) 2 / 8
```

```text
===== bash ts42b-msgs44.sh (sh exit=0) =====
---- composite 있음 · references 있음 · core 를 안 짓고 tsc -p app
app/src/main.ts(1,21): error TS6305: Output file 'core/dist/index.d.ts' has not been built from source file 'core/src/index.ts'.
(exit 2)
---- composite 없음 · references 있음 · tsc -b app
app/tsconfig.json(4,20): error TS6306: Referenced project 'core' must have setting "composite": true.
(exit 2)
---- composite 있음 · references 없음 · tsc -p app
app/src/main.ts(1,21): error TS6059: File 'core/src/index.ts' is not under 'rootDir' 'app/src'. 'rootDir' is expected to contain all source files.
(exit 2)
```

**왜 그런가**

- ★★★ **셋이 다 있어야 한다** — 참조되는 쪽 `composite` · 참조하는 쪽 `references` · 짓는 명령 `tsc -b`. `-p` 는 `core` 를 **안 짓는다.**
- ★★ `composite` 없는 `-b` 칸에 **`core/dist/index.js` 가 생겼다** — `core` 는 짓되(`.d.ts` 없이) `app` 에서 `TS6306` 으로 멈췄다.
- ★★ `references` 가 없으면 `core` 를 **모른다** — `app` 이 `core/src/index.ts` 를 자기 프로그램에 끌어와 `rootDir: src` 밖이라고 막는다.
- ★ 마지막 줄 **두 판이 갈린 칸 `2 / 8`**.

### 2. ★★★ ① **`core/src/index.ts`** · ② **`core/dist/index.d.ts`**(「File is output of project reference source 'core/src/index.ts'」) · ③ **`TS2345`** — `app` 이 고친 `.d.ts` 에 속는다

**출력**

```bash
# ts42b-dts44.sh
#!/usr/bin/env bash
# tsc -b app 으로 지은 뒤 app 의 프로그램에 무엇이 들었나 -- 판 둘
#   ① --traceResolution : import 가 어느 파일로 풀렸나(마지막 한 줄)
#   ② --explainFiles    : 프로그램에 실제로 든 파일과 그 까닭(표준 라이브러리 줄은 뺀다)
#   ③ core/dist/index.d.ts 한 줄을 손으로 바꾸고 app 만 다시 검사한다(core/src 는 그대로)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  w="$D/$v"; cp -r p44 "$w" || exit 3
  (cd "$w" && "${c[@]}" -b app --pretty false) > "$D/b.out" 2>&1; rc=$?
  echo "---- $v : tsc -b app (exit $rc)"
  echo "① $( (cd "$w" && "${c[@]}" -p app --pretty false --noEmit --traceResolution) | grep 'was successfully resolved' | sed "s|$w/||g")"
  echo "②"
  (cd "$w" && "${c[@]}" -p app --pretty false --noEmit --explainFiles) | sed "s|$w/||g" \
    | awk '/^[^ ]/{keep = ($0 ~ /^(core|app)\//)} keep'
  echo 'export declare function add(a: string, b: string): string;' > "$w/core/dist/index.d.ts"
  echo "③ index.d.ts 를 (a: string, b: string) 로 바꾼 뒤 tsc -p app --noEmit"
  (cd "$w" && "${c[@]}" -p app --pretty false --noEmit) | sed "s|$w/||g"; echo "(exit $?)"
done
```

```text
===== bash ts42b-dts44.sh (sh exit=0) =====
---- 7.0.2 : tsc -b app (exit 0)
① ======== Module name '../../core/src/index' was successfully resolved to 'core/src/index.ts'. ========
②
core/dist/index.d.ts
   Imported via "../../core/src/index" from file 'app/src/main.ts'
   File is output of project reference source 'core/src/index.ts'
app/src/main.ts
   Matched by include pattern 'src' in 'app/tsconfig.json'
③ index.d.ts 를 (a: string, b: string) 로 바꾼 뒤 tsc -p app --noEmit
app/src/main.ts(2,17): error TS2345: Argument of type 'number' is not assignable to parameter of type 'string'.
(exit 1)
---- 5.9.3 : tsc -b app (exit 0)
① ======== Module name '../../core/src/index' was successfully resolved to 'core/src/index.ts'. ========
②
core/dist/index.d.ts
  Imported via "../../core/src/index" from file 'app/src/main.ts'
  File is output of project reference source 'core/src/index.ts'
app/src/main.ts
  Matched by include pattern 'src' in 'app/tsconfig.json'
③ index.d.ts 를 (a: string, b: string) 로 바꾼 뒤 tsc -p app --noEmit
app/src/main.ts(2,17): error TS2345: Argument of type 'number' is not assignable to parameter of type 'string'.
(exit 2)
```

**왜 그런가**

- ★★★ 해석은 적힌 경로대로 `.ts` 로 풀리고, 그 자리에 **참조된 프로젝트의 출력 `.d.ts` 를 끼운다** — ② 의 둘째 까닭 줄.
- ★★★ ③ 은 **행동 증거**다 — `core/src/index.ts` 는 여전히 `number` 인데 `app` 이 `string` 을 요구받았다. `app` 이 보는 것은 **`.d.ts` 뿐**이다.
- ★ 두 판이 들여쓰기만 다르다. 종료 코드는 7.0.2 `1` · 5.9.3 `2`.

### 3. ★★★ 처음 — `core` → `app` · 안 바꿈 — 둘 다 최신 · 몸통만 — `core` 만, **`app` 은 「up to date with .d.ts files」** · 서명까지 — 둘 다 · **`dist` 만 지움 — 둘 다 「최신」, `exit 0`, `.d.ts` 없음** · `--clean` 뒤 — 처음부터

**출력**

```bash
# ts42b-verbose44.sh
#!/usr/bin/env bash
# tsc -b app --verbose 의 판정 줄 -- 단계 다섯 × 판 둘 · 로그 첫머리의 시각은 지운다(판마다 형식도 다르다)
#   1 처음 · 2 안 바꿈 · 3 core 몸통만(선언 같음) · 4 core 서명까지 · 5 core/dist 만 지움(.tsbuildinfo 는 남김) · 6 tsc -b app --clean 뒤
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
settle() {   # 빌드마다 mtime 을 과거로 고정한다 -- core 는 2분 전 · app 은 1분 전(app 이 core 뒤에 지어진 순서 그대로)
  find "$1/core" -exec touch -d '120 seconds ago' {} +; find "$1/app" -exec touch -d '60 seconds ago' {} +; }
clean() { sed -E "s|$1/||g; s/^(오전|오후) [0-9:]+ - //; s/^[0-9:]+ [AP]M - //" | sed '/^$/d; /^Projects in this build/,/app\/tsconfig.json$/d'; }
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  w="$D/$v"; cp -r p44 "$w" || exit 3
  for step in 1 2 3 4 5 6; do
    case $step in
      1) label="처음" ;;
      2) label="안 바꿈" ;;
      3) label="core 몸통만"; printf 'export function add(a: number, b: number): number {\n    return b + a;\n}\n' > "$w/core/src/index.ts" ;;
      4) label="core 서명까지"; printf 'export function add(a: number, b: number, c = 0): number {\n    return a + b + c;\n}\n' > "$w/core/src/index.ts" ;;
      5) label="core/dist 만 지움"; rm -rf "$w/core/dist" ;;
      6) label="--clean 뒤"; (cd "$w" && "${c[@]}" -b app --clean) > /dev/null 2>&1 ;;
    esac
    (cd "$w" && "${c[@]}" -b app --verbose --pretty false) > "$D/log" 2>&1; rc=$?; settle "$w"
    echo "---- $v · $step $label (exit $rc)"
    clean "$w" < "$D/log" | sed 's/^/  /'
    echo "  core/dist/index.d.ts 가 있나 $([ -f "$w/core/dist/index.d.ts" ] && echo 있음 || echo 없음)"
    clean "$w" < "$D/log" > "$D/log.$v.$step"
  done
done
same=0; for s in 1 2 3 4 5 6; do cmp -s "$D/log.7.0.2.$s" "$D/log.5.9.3.$s" && same=$((same+1)); done
echo
echo "두 판의 판정 줄이 한 글자도 같은 단계 $same / 6"
```

```text
===== bash ts42b-verbose44.sh (sh exit=0) =====
---- 7.0.2 · 1 처음 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 2 안 바꿈 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 3 core 몸통만 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is up to date with .d.ts files from its dependencies
  Updating output timestamps of project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 4 core 서명까지 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output 'app/tsconfig.tsbuildinfo' is older than input 'core'
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 7.0.2 · 5 core/dist 만 지움 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 없음
---- 7.0.2 · 6 --clean 뒤 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 1 처음 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 2 안 바꿈 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 3 core 몸통만 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is up to date with .d.ts files from its dependencies
  Updating output timestamps of project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 4 core 서명까지 (exit 0)
  Project 'core/tsconfig.json' is out of date because output 'core/tsconfig.tsbuildinfo' is older than input 'core/src/index.ts'
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output 'app/tsconfig.tsbuildinfo' is older than input 'core'
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음
---- 5.9.3 · 5 core/dist 만 지움 (exit 0)
  Project 'core/tsconfig.json' is up to date because newest input 'core/src/index.ts' is older than output 'core/tsconfig.tsbuildinfo'
  Project 'app/tsconfig.json' is up to date because newest input 'app/src/main.ts' is older than output 'app/tsconfig.tsbuildinfo'
  core/dist/index.d.ts 가 있나 없음
---- 5.9.3 · 6 --clean 뒤 (exit 0)
  Project 'core/tsconfig.json' is out of date because output file 'core/tsconfig.tsbuildinfo' does not exist
  Building project 'core/tsconfig.json'...
  Project 'app/tsconfig.json' is out of date because output file 'app/tsconfig.tsbuildinfo' does not exist
  Building project 'app/tsconfig.json'...
  core/dist/index.d.ts 가 있나 있음

두 판의 판정 줄이 한 글자도 같은 단계 6 / 6
```

**왜 그런가**

- ★★★ `tsc -b` 는 **일지(`.tsbuildinfo`)와 mtime** 으로 판정한다 — 「is older than」 문구가 그것이다. 출력 폴더가 있는지는 안 본다(5단계).
- ★★★ 몸통만 바꾸면 `core` 의 `.d.ts` 가 **같다** → `app` 은 타임스탬프만 고친다. 서명이 바뀌면 `.d.ts` 가 달라져 `app` 도 짓는다.
- ★★ 마지막 줄 **두 판의 판정 줄이 한 글자도 같은 단계 `6 / 6`**.

### 4. ★★★ 막힘 — `iso44a`(7.0.2 **`TS9013`** · 5.9.3 **`TS9007`**) · `iso44d` **`TS9017`** · `iso44h`(7.0.2 **`TS9013`** · 5.9.3 **`TS9008`**) · 통과 — `iso44k`(`return 1`) · `iso44e`(`as const`) · `iso44j` · 4.9.5 는 **전부 `TS5023`** — 두 판이 다른 행은 **`iso44a`·`iso44h`**

**출력**

```bash
# ts42b-iso44.sh
#!/usr/bin/env bash
# isolatedDeclarations -- export 꼴 열하나 × 판 셋 · 칸은 진단(행:코드) · 늘 --declaration 을 같이 준다
# 끝 행은 --declaration 없이 준 것(설정 진단을 보려고) -- 파일은 iso44b.ts
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
T=$'\t'
rows=(
  "iso44a.ts${T}function f(n) { return n * 2 }${T}--declaration"
  "iso44b.ts${T}function f(n): number { … }${T}--declaration"
  "iso44k.ts${T}function one() { return 1 }${T}--declaration"
  "iso44c.ts${T}const c = 10${T}--declaration"
  "iso44d.ts${T}const c = [1, 2]${T}--declaration"
  "iso44e.ts${T}const c = [1, 2] as const${T}--declaration"
  "iso44f.ts${T}const c = two()${T}--declaration"
  "iso44g.ts${T}const f = (n) => n${T}--declaration"
  "iso44h.ts${T}class K { m(n) { … } }${T}--declaration"
  "iso44i.ts${T}export default make()${T}--declaration"
  "iso44j.ts${T}export 는 적고 안쪽은 안 적음${T}--declaration"
  "iso44b.ts${T}(--declaration 없이)${T}"
)
cells() { sed -n 's/^[^ ]*(\([0-9]*\),[0-9]*): error \(TS[0-9]*\).*/\1:\2/p; s/^error \(TS[0-9]*\).*/설정:\1/p' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-10s %-12s %-12s %-12s %s\n' "파일" "7.0.2" "5.9.3" "4.9.5" "꼴"
ok7=0; split=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $r"; exit 3; fi
  IFS="$T" read -r f what extra <<< "$r"
  # shellcheck disable=SC2086
  a=$(tsc --pretty false --noEmit --isolatedDeclarations $extra "$f" 2>&1)
  # shellcheck disable=SC2086
  b=$(node "$OLD" --pretty false --noEmit --isolatedDeclarations $extra "$f" 2>&1)
  # shellcheck disable=SC2086
  c=$(node "$V49" --pretty false --noEmit --isolatedDeclarations $extra "$f" 2>&1)
  case "$a$b$c" in *TS5112*) echo "★ TS5112 -- 위쪽 디렉토리의 tsconfig.json 이 끼었다, 격자를 믿지 마라"; exit 4 ;; esac
  a=$(cells <<< "$a"); b=$(cells <<< "$b"); c=$(cells <<< "$c")
  printf '%-10s %-12s %-12s %-12s %s\n' "$f" "${a:-OK}" "${b:-OK}" "${c:-OK}" "$what"
  total=$((total+1)); [ -z "$a" ] && ok7=$((ok7+1)); [ "$a" != "$b" ] && split=$((split+1))
done
echo
echo "7.0.2 가 받은 행 $ok7 / $total · 7.0.2 와 5.9.3 이 갈린 행 $split / $total"
```

```text
===== bash ts42b-iso44.sh (sh exit=0) =====
파일     7.0.2        5.9.3        4.9.5        꼴
iso44a.ts  2:TS9013     1:TS9007     설정:TS5023 function f(n) { return n * 2 }
iso44b.ts  OK           OK           설정:TS5023 function f(n): number { … }
iso44k.ts  OK           OK           설정:TS5023 function one() { return 1 }
iso44c.ts  OK           OK           설정:TS5023 const c = 10
iso44d.ts  1:TS9017     1:TS9017     설정:TS5023 const c = [1, 2]
iso44e.ts  OK           OK           설정:TS5023 const c = [1, 2] as const
iso44f.ts  4:TS9010     4:TS9010     설정:TS5023 const c = two()
iso44g.ts  1:TS9007     1:TS9007     설정:TS5023 const f = (n) => n
iso44h.ts  3:TS9013     2:TS9008     설정:TS5023 class K { m(n) { … } }
iso44i.ts  4:TS9037     4:TS9037     설정:TS5023 export default make()
iso44j.ts  OK           OK           설정:TS5023 export 는 적고 안쪽은 안 적음
iso44b.ts  설정:TS5069 설정:TS5069 설정:TS5023 (--declaration 없이)

7.0.2 가 받은 행 5 / 12 · 7.0.2 와 5.9.3 이 갈린 행 2 / 12
```

```ts
// iso44a.ts
export function f(n: number) {
    return n * 2;
}
```

```ts
// iso44h.ts
export class K {
    m(n: number) {
        return n * 2;
    }
}
```

```text
===== tsc --pretty false --noEmit --declaration --isolatedDeclarations iso44a.ts iso44h.ts ; 이어서 "$TSC_OLD" 로 같은 것 (sh exit=0) =====
---- 7.0.2
iso44a.ts(2,12): error TS9013: Expression type can't be inferred with --isolatedDeclarations.
iso44h.ts(3,16): error TS9013: Expression type can't be inferred with --isolatedDeclarations.
(exit 1)
---- 5.9.3
iso44a.ts(1,17): error TS9007: Function must have an explicit return type annotation with --isolatedDeclarations.
iso44h.ts(2,5): error TS9008: Method must have an explicit return type annotation with --isolatedDeclarations.
(exit 2)
```

**왜 그런가**

- ★★★ 막는 **꼴은 두 판이 같다** — 식의 타입을 **추론해야** `.d.ts` 를 쓸 수 있는 자리(`n * 2` · 호출 결과 · 가변 배열 · 기본 export 식).
- ★★ 갈린 것은 **진단의 코드와 자리** — 7.0.2 는 식(`(2,12)` `n * 2`), 5.9.3 은 함수·메서드 이름(`(1,17)` `f`).
- ★★ 리터럴 반환(`return 1`)과 `as const` 배열은 **보고 안다** — 통과.
- ★ 4.9.5 는 옵션을 모른다(`TS5023`) · `--declaration` 없이 주면 두 판 모두 `TS5069`(격자 끝 행).

### 5. ★★★ 7.0.2 — **`TS5011`**(`rootDir` 를 적으라) · `app/dist/src/main.js` 하나 · 5.9.3 — **`(exit 0)`** · `app/dist/app/src/main.js` **와 `app/dist/core/src/index.js`**

**출력**

```bash
# ts42b-norootdir44.sh
#!/usr/bin/env bash
# references 도 rootDir 도 없는 app -- tsc -p app 이 core 의 .ts 를 어떻게 다루나 · 판 둘
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  w="$D/$v"; cp -r p44 "$w" || exit 3
  echo '{ "compilerOptions": { "target": "es2022", "outDir": "dist" }, "include": ["src"] }' > "$w/app/tsconfig.json"
  (cd "$w" && "${c[@]}" -p app --pretty false) > "$D/out" 2>&1; rc=$?
  echo "---- $v : tsc -p app (exit $rc)"
  sed "s|$w/||g" "$D/out"
  echo "  생긴 파일: $(cd "$w" && find core app -path '*/dist/*' -type f | sort | tr '\n' ' ')"
done
```

```text
===== bash ts42b-norootdir44.sh (sh exit=0) =====
---- 7.0.2 : tsc -p app (exit 2)
app/tsconfig.json(1,44): error TS5011: The common source directory of 'tsconfig.json' is '..'. The 'rootDir' setting must be explicitly set to this or another path to adjust your output's file layout.
  Visit https://aka.ms/ts6 for migration information.
  생긴 파일: app/dist/src/main.js 
---- 5.9.3 : tsc -p app (exit 0)
  생긴 파일: app/dist/app/src/main.js app/dist/core/src/index.js 
```

- ★★ 5.9.3 은 공통 조상(`..`)을 출력 뿌리로 잡아 **`core` 의 소스를 `app` 의 출력에 한 벌 더** 지었다 — 진단 없이. 7.0.2 는 그 자리를 **설정 진단**으로 바꿨다.

### 6. ★★ **`core/dist/index.d.ts`** — 「Output file 'core/dist/index.d.ts' has not been built from source file 'core/src/index.ts'.」 · `app` 이 찾는 것이 **`.ts` 가 아니라 출력 `.d.ts`** 라고 진단이 먼저 말한다

- ★★ 2번 ② 의 「File is output of project reference source」와 **같은 파일**이다 — `core` 를 짓기 전에는 그 자리가 비어 `TS6305`, 지은 뒤에는 그 파일이 프로그램에 든다.

### 7. ★★★ 해석 창은 **「어느 경로로 풀었나」**(`core/src/index.ts`)까지 · **「그 자리를 무엇으로 바꿔 끼웠나」** 는 못 본다 — ③ 은 **② 를** 뒷받침한다

- ★★ `.d.ts` 를 고치자 `app` 이 속었으니, 검사에 쓰인 것은 **② 의 `.d.ts`** 다. ① 만 보고 「`app` 이 소스를 검사한다」로 읽으면 틀린다.

### 8. ★★ `inner` 는 **export 되지 않아** `.d.ts` 에 안 나온다 — `isolatedDeclarations` 는 **공개 표면**만 본다 · `.d.ts` 는 **달라지지 않는다**(적든 안 적든 `f(n: number): number`)

**출력**

```text
===== tsc --pretty false --declaration --emitDeclarationOnly --outDir e44 iso44a.ts iso44b.ts ; 방출된 .d.ts 둘 (sh exit=0) =====
(exit 0)
===== 방출된 e44/iso44a.d.ts =====
export declare function f(n: number): number;
===== 방출된 e44/iso44b.d.ts =====
export declare function f(n: number): number;
두 .d.ts 가 한 글자도 같다
```

- ★★ 37편 5절의 「`--declaration` 은 안 적힌 자리를 추론한다」 그대로 두 `.d.ts` 가 **한 글자도 같다.** `isolatedDeclarations` 는 **결과가 아니라 얻는 법**(추론 없이)을 바꾼다.

### 9. ★★ 43편 4절 **「a.ts 값만(타입 같음) · `declaration: true` → `[a.js]`」** — 겉모습(`.d.ts`)이 같으면 **의존자를 건너뛴다**

- ★★ [**43번 주제**](../43-remaining-tsconfig-choices/) 4절은 **파일** 사이에서, 3번은 **프로젝트** 사이에서 같은 규칙이 돌았다. `composite` 가 `declaration` 을 켜기 때문에 `tsc -b` 는 늘 이 비교를 할 수 있다.

### 10. ★★★ `rm -rf core/dist` 는 **일지를 남긴다** → `tsc -b` 가 「최신」이라며 **아무것도 안 짓는다**(`exit 0`) · `--clean` 은 **일지와 출력을 같이** 지워 다음 빌드가 처음부터 · 근거는 **`.tsbuildinfo` 와 mtime**

- ★★ 3번 5단계의 판정 문구 「is up to date because newest input … is older than output 'core/tsconfig.tsbuildinfo'」 — 비교 대상이 **일지 파일**이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `"$TSC_OLD"`·`"$TSC_49"` · `node` | `7.0.2` · `5.9.3` · `4.9.5` · `v18.19.1` |
| ★★★ 참조 격자 | `bash ts42b-refs44.sh` — 16칸, 칸마다 새 복사 | 빌드된 칸 **`2 / 16`** · 두 판 갈린 칸 **`2 / 8`** |
| ★★ `-b` 자리 · 순서 | `--pretty false -b` · `-b app --dry` | `TS5023` · `core` → `app` |
| ★★★ 무엇을 보나 | `bash ts42b-dts44.sh` — 두 판 × ①②③ | `.ts` 로 풀리고 `.d.ts` 가 든다 · `.d.ts` 에 속는다 |
| ★★ `rootDir` 없음 | `bash ts42b-norootdir44.sh` | 7.0.2 `TS5011` · 5.9.3 `exit 0` + 한 벌 더 |
| ★★★ 빌드 로그 | `bash ts42b-verbose44.sh` — 두 판 × 여섯 단계, mtime 고정 | 판정 줄 같은 단계 **`6 / 6`** · 5단계 `exit 0` + `.d.ts` 없음 |
| ★★ `isolatedDeclarations` | `bash ts42b-iso44.sh` — 열두 행 × 세 판 | 7.0.2 받은 행 **`5 / 12`** · 두 판 갈린 행 **`2 / 12`** |
| ★ 가짜 격자 자기검사 | 가짜 옵션 · `p44` 없는 판 | **`exit 4` · `exit 3`** 로 멈췄다(처음 판은 `cp` 실패를 못 잡아 고쳤다) |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **`isolatedDeclarations` 진단 코드**(4번) · **`rootDir` 없는 칸**(5번) · **`-b` 의 종료 코드**(1번) — 이미 판마다 달랐다.
- ★ **빌드 로그 문구**(3번) — 두 판이 같았다. 판정이 mtime 에 기대므로 **mtime 을 고정한 판**이다.

**안 돌려 본 것**

- ★★ **빌드 시간 · 병렬 빌드** — 재지 않았다.
- ★ **`app/dist/main.js` 의 `node` 실행** — 던지지 않았다.
