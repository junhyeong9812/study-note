# ts/syntax/43 — `tsconfig` 의 나머지 선택 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TSConfig — `target`](https://www.typescriptlang.org/tsconfig/#target) · [`incremental`](https://www.typescriptlang.org/tsconfig/#incremental) · [`useDefineForClassFields`](https://www.typescriptlang.org/tsconfig/#useDefineForClassFields) · [`downlevelIteration`](https://www.typescriptlang.org/tsconfig/#downlevelIteration).
> ★ 위는 **자리 안내용 링크**다 — 이 배치는 외부 네트워크를 쓰지 않아 **열어서 문장을 대조하지 못했다.** README 의 「7.0 에서 `es5`·`downlevelIteration`·AMD/UMD 계열은 불가」도 **확인 대상**으로 받아 1절 격자로 던졌다.
> **실행 검증** — 본판은 아래다. 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.

```text
===== tsc --version · "$TSC_OLD" · "$TSC_49" --version · node · "$NODE20" --version · nproc · CPU · PATH 의 tsc 첫 두 줄 (sh exit=0) =====
Version 7.0.2
Version 5.9.3
Version 4.9.5
v18.19.1
v20.19.6
nproc 24
Model name: 13th Gen Intel(R) Core(TM) i7-13700HX
#!/usr/bin/env node
import "../lib/tsc.js";
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 4창(진단·종료 코드) 격자 「7.0 에서 막힌 값」(행 열 × 세 판)이고, 둘째 기둥은 3창(방출물) 격자 「`target` 이 무엇을 내리나」(문법 여섯 × `target` 넷 × 두 판)다.**
> ★★★ **제5의 상태 — 「`incremental` 이 두 번째 빌드에서 무엇을 건너뛰나」를 시간으로 묻지 않았다.** 시간은 흔들리는 칸이라 **`--listEmittedFiles` 가 찍는 「다시 방출한 파일」** 로 창을 바꿔 물었다(4절). 바꾼 창이 못 보는 것 — **다시 검사했지만 방출은 안 한 파일**은 이 창에 안 나온다.
> ★★★ **43 은 39 에서 오고, 여기 적힌 옵션 절반은 이미 형제가 쟀다.** `lib`(38편) · `module`/`moduleResolution`(35편) · `isolatedModules`(02·36편) · `skipLibCheck`(37편) · `useDefineForClassFields` 의 전체 격자(32편 5절)는 **다시 재지 않고 5절 인용표 한 장**으로 묶는다. 여기서 새로 재는 것은 **막힌 값 · `target` 의 방출 · `target` 을 안 적었을 때 · `incremental`** 넷이다.
> ★★ 명령줄 격자는 **`tsconfig.json` 이 없는 임시 디렉토리**에서 던졌다 — 7.0.2 는 위쪽에 설정이 있으면 파일을 직접 줘도 `TS5112` 로 거부한다(35편 6절). 스크립트는 **칸에 `TS5112` 가 들면 멈추고, 대조 행이 막히면 멈춘다.** ★ 제출 전에 **위쪽에 `tsconfig.json` 을 둔 판으로 실제로 멈추는지** 돌려 봤다(`exit 4`).
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·방출된 `.js` 의 글자 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 두 격자의 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | ★★ 4절의 「다시 방출한 `.js`」 목록 | 파일 이름만 찍었다 — 시간 줄은 **안 찍었다** |
| **판에 매인다** | ★★★ 막힌 값 · `target` 기본값 | 결론 자체다 |
| **★ 부적용 — 시간** | ★★★ **「`incremental` 이 빠르게」·「`skipLibCheck` 가 빠르게」** | **재지 않았다** — 이 문서는 그 말을 **한 줄도 하지 않는다.** 검사 시간을 잰 자리는 [**45번 주제**](../45-type-level-performance/) |
| **★ 부적용 — 5창(`.d.ts` 모양)** | 4절이 `declaration` 을 켜지만 **`.d.ts` 의 글자**는 묻지 않는다 | 37·44편 |

## 한눈에 — 쉽게 말하면

**`tsconfig` 의 나머지 선택은 「출력 기계의 다이얼」이다. `target` 은 **얼마나 옛 브라우저에 맞춰 풀어 쓸지** 정하는 다이얼이고, 7.0 은 다이얼의 **맨 아래 칸(`es5`)을 떼어 냈다.** `incremental` 은 「지난번 작업 일지」를 남겨 **바뀐 것과 그것에 기대는 것만** 다시 찍게 하는 장치다.**

| 비유 | 실체 |
|---|---|
| 다이얼 맨 아래 칸이 **떼어졌다** | `target: es5` → 7.0.2 **`TS5108`** · `es3` → **`TS6046`**(값 목록에도 없다)(1절) |
| ★★ 풀어 쓰기 부품이 **통째로 빠졌다** | `downlevelIteration`·`outFile` → **`TS5102`**(옵션째 제거)(1절) |
| ★★ 옛 포장 규격(AMD·UMD·System)을 **안 받는다** | `module amd` 등 → `TS5108` — 기본 해석이 `bundler` 라 **`TS5095` 도 같이**(1절) |
| 다이얼을 **올릴수록 덜 풀어 쓴다** | `?.`·`??`·클래스 필드·`async` 가 `target` 에 따라 **내려가거나 남는다**(2절 `10 / 48`) |
| ★★★ 다이얼을 **안 돌리면** 공장 기본값 | `target` 없이 — 7.0.2 는 **네이티브 필드** · 5.9.3 은 **`_this.x = 1`** → 부모 setter 가 불리나가 **갈린다**(3절) |
| **작업 일지**(`.tsbuildinfo`) | 두 번째 빌드는 **바뀐 파일과 그 의존자만** 다시 방출(4절) |
| ★★ 일지에 **「겉모습」까지 적어 두면** | `declaration: true` — 겉모습이 같으면 **의존자를 건너뛴다**(4절) |

- ★★★ 한 줄로 — 「**7.0 은 `target`·`module` 의 옛 값(`es5`·`es3`·AMD/UMD/System)과 옵션(`downlevelIteration`·`outFile`)을 받지 않는다. 남은 `target` 은 방출할 문법을 고르는 다이얼이고, 안 적으면 판마다 기본값이 달라 **런타임 동작**까지 갈린다. `incremental` 은 바뀐 파일의 의존자를 다시 방출하는데, `declaration` 이 켜져 있어야 겉모습이 같은 변경을 알아본다.**」

```text
  이 문서의 네 다이얼 — 무엇을 재고 무엇을 인용하나

  target · module 의 옛 값          1절에서 잰다      7.0.2 가 받나 (세 판)
  target 이 내리는 문법             2절에서 잰다      방출물 글자 (두 판)
  target 을 안 적었을 때            3절에서 잰다      node 가 부모 setter 를 부르나 (두 판)
  incremental                     4절에서 잰다      다시 방출한 파일 (두 판) — 시간은 안 잰다
  lib · module · isolatedModules · skipLibCheck · useDefineForClassFields    5절 — 형제가 쟀다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ 7.0 은 어떤 값·옵션을 막았나 — README 의 「`es5`·`downlevelIteration`·AMD/UMD 불가」는 맞나** — 행 열 × 세 판(1절).
2. **★★★ `target` 은 무엇을 바꾸나** — 방출물(2절) · 안 적었을 때의 런타임(3절).
3. **★★ `incremental` 은 두 번째 빌드에서 무엇을 건너뛰나 — 시간을 재지 않고 어떻게 아나** — 다시 방출한 파일(4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **4창 — 막힌 값 격자** | 행 열 × 4.9.5 · 5.9.3 · 7.0.2 | 칸마다 진단 코드 | **본체**(1절) |
| ★★★ **3창 — 방출 격자** | 문법 여섯 × `target` 넷 × 두 판 — 원래 문법의 글자가 남았나 | 방출물 | **둘째 기둥**(2절) |
| ★★ **3창 + `node`** | `target` 을 안 적은 한 쌍 — 부모 setter | 실행 결과 | 3절 |
| ★★★ **제5의 상태 — `--listEmittedFiles`** | 「무엇을 건너뛰나」를 **시간 대신 방출 목록**으로 | 파일 이름 | 4절 |
| ★ **인용 창** | `lib`·`module`·`isolatedModules`·`skipLibCheck`·`useDefineForClassFields` | 형제 편의 격자 | 5절 |
| ★ **부적용 — 시간** | 「빠르게」 류 주장 | — | 45편 |

비용 — 막힌 값 격자 30칸 + 진단 전문 다섯 · 방출 격자 48칸 + `es2015` 방출물 넷 · 5.9.3 `es5` 방출 둘 · `target` 없는 한 쌍 · `incremental` 20단계(설정 둘 × 두 판 × 다섯 단계).

```text
  이 주제의 축 — 「판이 무엇을 받나」와 「받은 값이 무엇을 만드나」

  받나          4.9.5 ─ 5.9.3 ─ 7.0.2     옛 값이 하나씩 사라진다 (1절)
  만드나        target 이 높을수록 방출물에 원래 문법이 남는다 (2절)
  안 적으면      판의 기본 target 이 만든다 — 판마다 다른 런타임 (3절)
  다시 만드나    .tsbuildinfo 가 「바뀐 것 + 기대는 것」만 고른다 (4절)
```

### (1) ★★★ 막힌 값 격자 — 행 열 × 세 판

**언제 쓰나** — 5.x 시절 `tsconfig.json` 을 7.0 으로 올리기 전, **무엇이 막히는지 미리** 볼 때.

```ts
// z43.ts
export const z = 1;
```

```bash
# ts42b-blocked43.sh
#!/usr/bin/env bash
# 7.0 에서 막혔다는 값들 × 판 셋 -- 파일은 export 한 줄짜리 z43.ts · 칸은 진단 코드(없으면 OK)
# 마지막 행은 대조 -- 세 판 모두 받아야 격자가 선다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
cp z43.ts "$D/" || exit 3
T=$'\t'
rows=(
  "target es5${T}--target es5"
  "target es3${T}--target es3"
  "downlevelIteration${T}--target es2015 --downlevelIteration"
  "module amd${T}--module amd"
  "module umd${T}--module umd"
  "module system${T}--module system"
  "module none${T}--module none"
  "moduleResolution node10${T}--module commonjs --moduleResolution node10"
  "outFile + system${T}--module system --outFile out.js"
  "(대조) target es2015${T}--target es2015"
)
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
printf '%-26s %-14s %-14s %s\n' "행" "4.9.5" "5.9.3" "7.0.2"
ok4=0; ok5=0; ok7=0; blocked7=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r name flags <<< "$r"
  # shellcheck disable=SC2086
  r4=$(cd "$D" && node "$V49" --pretty false --noEmit $flags z43.ts 2>&1)
  # shellcheck disable=SC2086
  r5=$(cd "$D" && node "$OLD" --pretty false --noEmit $flags z43.ts 2>&1)
  # shellcheck disable=SC2086
  r7=$(cd "$D" && tsc --pretty false --noEmit $flags z43.ts 2>&1)
  case "$r4$r5$r7" in *TS5112*) echo "★ TS5112 -- 위쪽 디렉토리의 tsconfig.json 이 끼었다, 격자를 믿지 마라"; exit 4 ;; esac
  a=$(codes <<< "$r4"); b=$(codes <<< "$r5"); c=$(codes <<< "$r7")
  printf '%-26s %-14s %-14s %s\n' "$name" "${a:-OK}" "${b:-OK}" "${c:-OK}"
  total=$((total+1))
  [ -z "$a" ] && ok4=$((ok4+1)); [ -z "$b" ] && ok5=$((ok5+1)); [ -z "$c" ] && ok7=$((ok7+1))
  [ -z "$b" ] && [ -n "$c" ] && blocked7=$((blocked7+1))
  last="$a$b$c"
done
if [ -n "$last" ]; then echo "★ 대조 행이 막혔다 -- 격자를 믿지 마라"; exit 5; fi
echo
echo "받아들인 행 -- 4.9.5 $ok4 / $total · 5.9.3 $ok5 / $total · 7.0.2 $ok7 / $total · 5.9.3 은 받는데 7.0.2 가 막은 행 $blocked7 / $total"
```

```text
===== bash ts42b-blocked43.sh (sh exit=0) =====
행                        4.9.5          5.9.3          7.0.2
target es5                 OK             OK             TS5108
target es3                 OK             TS5108         TS6046
downlevelIteration         OK             OK             TS5102
module amd                 OK             OK             TS5095 TS5108
module umd                 OK             OK             TS5095 TS5108
module system              OK             OK             TS5095 TS5108
module none                TS1148         TS1148         TS6046
moduleResolution node10    TS6046         OK             TS5108
outFile + system           OK             OK             TS5095 TS5102 TS5108
(대조) target es2015     OK             OK             OK

받아들인 행 -- 4.9.5 8 / 10 · 5.9.3 8 / 10 · 7.0.2 1 / 10 · 5.9.3 은 받는데 7.0.2 가 막은 행 7 / 10
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **README 의 세 주장이 전부 맞았다** — `target es5` **`TS5108`** · `downlevelIteration` **`TS5102`** · `module amd`/`umd` **`TS5108`**. `system` 도 같다.
- ★★★ **`target es3` 는 5.9.3 에서 이미 `TS5108`, 7.0.2 에서는 `TS6046`** — 「제거된 값」도 아니고 **값 목록에 아예 없다.** 두 판에 걸쳐 **두 단계로** 사라졌다.
- ★★★ **`module none` 도 7.0.2 에서 `TS6046`** — 4.9.5·5.9.3 은 받긴 받되 `export` 가 있는 파일에 `TS1148` 을 냈다. 7.0.2 는 **값째 모른다.**
- ★★ **`module amd`·`umd`·`system` 칸에 `TS5095` 가 같이** 났다 — 「Option 'bundler' can only be used when 'module' is set to …」. 7.0.2 의 기본 해석이 **`bundler`**(35편 1절)라, 옛 `module` 값과 **맞물린 진단**이 하나 더 붙었다.
- ★★ **`outFile + system` 은 세 코드** — `outFile` 은 **옵션째**(`TS5102`), `system` 은 **값**(`TS5108`).
- ★ `moduleResolution node10` 은 35편 1절이 이미 쟀다 — 한 행만 다시 실었고 **같은 답**(`TS5108` · 4.9.5 `TS6046`)이다.
- ★★ 마지막 줄 — **받아들인 행 4.9.5 `8 / 10` · 5.9.3 `8 / 10` · 7.0.2 `1 / 10`**(대조 행뿐) · **5.9.3 은 받는데 7.0.2 가 막은 행 `7 / 10`**.

진단 전문 — 7.0.2 가 무엇이라고 말하나.

```text
===== tsc --pretty false --noEmit <행 다섯의 플래그> z43.ts -- 7.0.2 의 진단 전문 (sh exit=0) =====
---- --target es5
error TS5108: Option 'target=ES5' has been removed. Please remove it from your configuration.
(exit 1)
---- --target es3
error TS6046: Argument for '--target' option must be: 'es6', 'es2015', 'es2016', 'es2017', 'es2018', 'es2019', 'es2020', 'es2021', 'es2022', 'es2023', 'es2024', 'es2025', 'esnext'.
(exit 1)
---- --target es2015 --downlevelIteration
error TS5102: Option 'downlevelIteration' has been removed. Please remove it from your configuration.
(exit 1)
---- --module amd
error TS5095: Option 'bundler' can only be used when 'module' is set to 'preserve', 'commonjs', or 'es2015' or later.
error TS5108: Option 'module=AMD' has been removed. Please remove it from your configuration.
(exit 1)
---- --module system --outFile out.js
error TS5095: Option 'bundler' can only be used when 'module' is set to 'preserve', 'commonjs', or 'es2015' or later.
error TS5102: Option 'outFile' has been removed. Please remove it from your configuration.
error TS5108: Option 'module=System' has been removed. Please remove it from your configuration.
(exit 1)
```

- ★★ `TS5108`·`TS5102` 는 둘 다 「Please remove it from your configuration.」 — **대체 값을 알려 주지 않는다.** `TS6046` 은 **받는 값 목록**을 준다(`es6` 부터 `esnext` 까지 — `es5` 가 없다).

```text
  옛 값이 사라진 모양 — 판 셋

                      4.9.5        5.9.3             7.0.2
  target es3          받음         TS5108 (값 제거)    TS6046 (값 목록에 없음)
  target es5          받음         받음              TS5108 (값 제거)
  downlevelIteration  받음         받음              TS5102 (옵션 제거)
  module amd·umd·system 받음        받음              TS5108 (값 제거) + TS5095
  module none         TS1148       TS1148            TS6046
  outFile             받음         받음              TS5102 (옵션 제거)
```

비용 — **5.9.3 은 넷을 조용히 받는다**(`es5`·`downlevelIteration`·AMD 계열·`outFile`). 올리기 전에는 진단이 없고, 올리는 순간 **한꺼번에** 막힌다.

### (2) ★★★ `target` 이 방출물을 바꾸는 격자 — 문법 여섯 × `target` 넷 × 두 판

**언제 쓰나** — 「`target` 을 `es2020` 에서 `es2022` 로 올리면 방출물에서 **무엇이 달라지나**」를 판단할 때.

```ts
// oc43.ts
export const f = (o?: { a: number }) => o?.a;
```

```ts
// nc43.ts
export const f = (x: number | null) => x ?? 0;
```

```ts
// cf43.ts
export class C {
    x = 1;
}
```

```ts
// as43.ts
export async function f() {
    await 1;
}
```

```ts
// gen43.ts
export function* g() {
    yield 1;
}
```

```ts
// fo43.ts
export function s(xs: number[]) {
    let t = 0;
    for (const x of xs) t += x;
    return t;
}
```

```bash
# ts42b-emit43.sh
#!/usr/bin/env bash
# 문법 여섯 × target 넷 × 판 둘 -- 방출물에 그 문법이 그대로 남았나(남음) 내려갔나(내림)
# 「남음」의 판정은 방출물에서 원래 문법의 글자를 grep -E 로 찾는 것이다(행의 셋째 칸)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
rows=(
  "oc43.ts${T}옵셔널 체이닝${T}o\?\.a"
  "nc43.ts${T}널 병합${T}x \?\? 0"
  "cf43.ts${T}클래스 필드${T}^    x = 1;"
  "as43.ts${T}async/await${T}async function f"
  "gen43.ts${T}제너레이터${T}function\* g"
  "fo43.ts${T}for…of${T}for \(const x of xs\)"
)
targets=(es2015 es2020 es2022 esnext)
printf '%-9s %-6s' "파일" "판"; for t in "${targets[@]}"; do printf ' %-9s' "$t"; done; printf ' %s\n' "문법"
down=0; total=0; split=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 3 ]; then echo "칸 수 $n ≠ 3: $r"; exit 3; fi
  IFS="$T" read -r f what pat <<< "$r"
  declare -A got=()
  for v in 7 5; do
    for t in "${targets[@]}"; do
      o="$D/$v-$t"; rm -rf "$o"
      if [ $v = 7 ]; then raw=$(tsc --pretty false -t "$t" --outDir "$o" "$f" 2>&1); else raw=$(node "$OLD" --pretty false -t "$t" --outDir "$o" "$f" 2>&1); fi
      if [ -n "$raw" ]; then echo "★ 진단이 나왔다 -- $v $t $f: $raw"; exit 4; fi
      if grep -Eq "$pat" "$o/${f%.ts}.js"; then got[$v,$t]="남음"; else got[$v,$t]="내림"; fi
      total=$((total+1)); [ "${got[$v,$t]}" = "내림" ] && down=$((down+1))
    done
  done
  for v in 7 5; do
    if [ $v = 7 ]; then printf '%-9s %-6s' "$f" "7.0.2"; else printf '%-9s %-6s' "" "5.9.3"; fi
    for t in "${targets[@]}"; do printf ' %-9s' "${got[$v,$t]}"; done
    if [ $v = 7 ]; then printf ' %s\n' "$what"; else echo; fi
  done
  for t in "${targets[@]}"; do [ "${got[7,$t]}" != "${got[5,$t]}" ] && split=$((split+1)); done
  unset got
done
if [ "$down" -eq 0 ] || [ "$down" -eq "$total" ]; then echo "★ 모든 칸이 같다 -- 판정 글자를 의심하라"; exit 5; fi
echo
echo "내려간 칸 $down / $total · 두 판이 다른 칸 $split / $((total / 2))"
```

```text
===== bash ts42b-emit43.sh (sh exit=0) =====
파일    판    es2015    es2020    es2022    esnext    문법
oc43.ts   7.0.2  내림    남음    남음    남음    옵셔널 체이닝
          5.9.3  내림    남음    남음    남음   
nc43.ts   7.0.2  내림    남음    남음    남음    널 병합
          5.9.3  내림    남음    남음    남음   
cf43.ts   7.0.2  내림    내림    남음    남음    클래스 필드
          5.9.3  내림    내림    남음    남음   
as43.ts   7.0.2  내림    남음    남음    남음    async/await
          5.9.3  내림    남음    남음    남음   
gen43.ts  7.0.2  남음    남음    남음    남음    제너레이터
          5.9.3  남음    남음    남음    남음   
fo43.ts   7.0.2  남음    남음    남음    남음    for…of
          5.9.3  남음    남음    남음    남음   

내려간 칸 10 / 48 · 두 판이 다른 칸 0 / 24
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`es2015` 에서 내려간 넷** — 옵셔널 체이닝 · 널 병합 · 클래스 필드 · `async/await`. 제너레이터와 `for…of` 는 **남았다**(둘 다 ES2015 문법이다).
- ★★★ **`es2020` 에서 내려간 것은 클래스 필드 하나** — `?.`·`??`(ES2020)와 `async`(ES2017)는 남았다.
- ★★ **`es2022`·`esnext` 는 여섯 다 남았다** — 이 여섯에 한해서는 **내릴 것이 없다.**
- ★★ 마지막 줄 — **내려간 칸 `10 / 48`**(두 판 합) · **두 판이 다른 칸 `0 / 24`** — 방출 규칙은 7.0.2 와 5.9.3 이 이 격자에서 같다.

내려간 모양 — `es2015` 의 방출물 넷.

```text
===== tsc --pretty false -t es2015 --outDir e43 oc43.ts nc43.ts cf43.ts as43.ts ; 방출물 넷 (sh exit=0) =====
(exit 0)
===== 방출된 e43/oc43.js =====
export const f = (o) => o === null || o === void 0 ? void 0 : o.a;
===== 방출된 e43/nc43.js =====
export const f = (x) => x !== null && x !== void 0 ? x : 0;
===== 방출된 e43/cf43.js =====
export class C {
    constructor() {
        this.x = 1;
    }
}
===== 방출된 e43/as43.js =====
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
export function f() {
    return __awaiter(this, void 0, void 0, function* () {
        yield 1;
    });
}
```

- ★★ `o?.a` → **`o === null || o === void 0 ? void 0 : o.a`** · `x ?? 0` → **`x !== null && x !== void 0 ? x : 0`** — 식 하나가 **비교 둘**로 풀렸다.
- ★★★ 클래스 필드 `x = 1` → **생성자 안의 `this.x = 1`** — **대입**으로 바뀌었다. 3절과 32편 5절이 이 차이가 **부모 setter** 에서 드러나는 것을 본다.
- ★★ `async function` → **`__awaiter` 도우미 + `function*`** — 제너레이터로 흉내 낸다.

```text
  target 넷 × 문법 여섯 — 이 판의 방출 (두 판 같음)

                es2015     es2020     es2022     esnext
  o?.a          내림       남음       남음       남음
  x ?? 0        내림       남음       남음       남음
  x = 1 (필드)   내림       ★ 내림     남음       남음      ← es2022 부터 네이티브 필드
  async/await   내림       남음       남음       남음
  function*     남음       남음       남음       남음
  for…of        남음       남음       남음       남음      ← 둘을 내리던 es5 는 7.0 에서 막혔다 (1절)
```

`es5` 에서만 내려가던 것 — 7.0 이 없앤 길을 **5.9.3 으로** 본다.

```text
===== node "$TSC_OLD" --pretty false -t es5 --outDir e43a fo43.ts ; 이어서 --downlevelIteration 을 붙여 e43b 로 (sh exit=0) =====
(exit 0)
===== 방출된 e43a/fo43.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.s = s;
function s(xs) {
    var t = 0;
    for (var _i = 0, xs_1 = xs; _i < xs_1.length; _i++) {
        var x = xs_1[_i];
        t += x;
    }
    return t;
}
(exit 0)
===== 방출된 e43b/fo43.js =====
"use strict";
var __values = (this && this.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.s = s;
function s(xs) {
    var e_1, _a;
    var t = 0;
    try {
        for (var xs_1 = __values(xs), xs_1_1 = xs_1.next(); !xs_1_1.done; xs_1_1 = xs_1.next()) {
            var x = xs_1_1.value;
            t += x;
        }
    }
    catch (e_1_1) { e_1 = { error: e_1_1 }; }
    finally {
        try {
            if (xs_1_1 && !xs_1_1.done && (_a = xs_1.return)) _a.call(xs_1);
        }
        finally { if (e_1) throw e_1.error; }
    }
    return t;
}
```

- ★★★ **`for…of` 가 `es5` 에서 두 가지로 내려간다** — `downlevelIteration` 없이는 **배열 인덱스 루프**(`xs_1.length` 로 센다), 있으면 **`__values` 도우미로 반복자 규약**을 흉내 낸다.
- ★★ 7.0 에서는 **이 두 방출이 둘 다 없다** — `es5` 가 `TS5108`, `downlevelIteration` 이 `TS5102`(1절). 반복을 내려 쓸 필요가 있으면 **tsc 밖의 도구**가 맡아야 한다 — 이 문서는 그런 도구를 던지지 않았다.

비용 — `target` 을 낮출수록 **도우미 코드**(`__awaiter`·`__values`)가 붙고 식이 길어진다. 크기·속도는 **재지 않았다.**

### (3) ★★★ `target` 을 안 적으면 — 판마다 부모 setter 가 불리나가 갈린다

**언제 쓰나** — `tsconfig.json` 에 `target` 을 **안 적은** 프로젝트를 7.0 으로 올릴 때.

```ts
// ud43.ts
// target 을 적지 않은 채 방출한다 -- 필드 한 줄이 부모 setter 를 부르나
class Parent {
    set x(v: number) {
        console.log("  Parent setter got", v);
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    x = 1;
}
const c = new Child();
console.log("  own keys", JSON.stringify(Object.keys(c)), "x", c.x);
```

```bash
# ts42b-ud43.sh
#!/usr/bin/env bash
# ud43.ts 를 target 없이 판 둘로 방출하고 node 로 돌린다 -- 진단이 있어도 방출은 된다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
for v in 7.0.2 5.9.3; do
  if [ $v = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  echo "---- $v (target 안 줌)"
  "${c[@]}" --pretty false --outDir "$D/$v" ud43.ts; echo "tsc exit $?"
  echo "방출물에서 x = 1 이 든 첫 줄: $(grep -m1 'x = 1' "$D/$v/ud43.js" | sed 's/^ *//')"
  node "$D/$v/ud43.js"; echo "node exit $?"
done
```

```text
===== bash ts42b-ud43.sh (sh exit=0) =====
---- 7.0.2 (target 안 줌)
ud43.ts(11,5): error TS2610: 'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.
tsc exit 2
방출물에서 x = 1 이 든 첫 줄: x = 1;
  own keys ["x"] x 1
node exit 0
---- 5.9.3 (target 안 줌)
ud43.ts(11,5): error TS2610: 'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.
tsc exit 2
방출물에서 x = 1 이 든 첫 줄: _this.x = 1;
  Parent setter got 1
  own keys [] x -1
node exit 0
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **7.0.2** — 방출물에 **`x = 1;`**(네이티브 필드)이 남았고 `node` 는 **`own keys ["x"] x 1`** — 부모 setter 가 **안 불렸다.**
- ★★★ **5.9.3** — 방출물에 **`_this.x = 1;`**(대입)이고 `node` 는 **`Parent setter got 1`** 다음 **`own keys [] x -1`** — setter 가 **가져갔다.**
- ★★ 두 판 모두 **`TS2610`**(「'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.」)을 냈고 **그래도 방출했다** — 경고는 같고 **런타임이 다르다.**
- ★★ 소스도 명령도 같다 — 다른 것은 **판의 기본 `target`** 뿐이다(38편 3절 — 7.0.2 `es2025` · 5.9.3 은 `es5`). 그 기본값이 `useDefineForClassFields` 의 기본값을 끌고 간다.

```text
  같은 소스 · 같은 명령 · 다른 판 — target 을 안 적었을 때

  7.0.2   기본 target 이 높다   ─> x = 1;  (네이티브 필드 = 정의)   ─> setter 0번 · own ["x"]
  5.9.3   기본 target 이 es5   ─> _this.x = 1;  (대입)            ─> setter 1번 · own []
          ★ 32편 5절이 target · useDefineForClassFields 를 명시한 다섯 판을 이미 쟀다 — 여기는 「안 적은 칸」 하나
```

비용 — **`target` 을 적지 않은 설정은 판을 올리는 것만으로 런타임이 바뀐다.** 진단(`TS2610`)은 두 판이 같아서 **경고만 봐서는 모른다.**

### (4) ★★ `incremental` — 두 번째 빌드는 무엇을 다시 방출하나

**언제 쓰나** — `.tsbuildinfo` 가 무엇을 하는지, **`declaration` 을 켜면 왜 덜 다시 짓는지** 판단할 때. ★ **시간은 재지 않는다** — 「다시 방출한 파일」로 판별한다.

```bash
# ts42b-inc43.sh
#!/usr/bin/env bash
# incremental 두 설정(declaration 끔/켬) × 판 둘 -- 단계마다 다시 방출한 .js 를 --listEmittedFiles 로 센다
# 파일 셋: a.ts(값 하나) · b.ts(a 를 import) · c.ts(아무도 안 본다) -- 시간은 찍지 않는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
steps=("1 처음" "2 안 바꿈" "3 c.ts 값만" "4 a.ts 값만(타입 같음)" "5 a.ts 타입까지")
build() {   # build <판> <declaration>
  local c; if [ "$1" = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  (cd "$D/w" && "${c[@]}" --pretty false -p tsconfig.json --declaration "$2" --listEmittedFiles) > "$D/out" 2>&1
  local rc=$?
  emitted=$(grep -o 'dist/[a-z]*\.js$' "$D/out" | sed 's|^dist/||' | tr '\n' ' ' | sed 's/ $//')
  info=$(grep -c '\.tsbuildinfo$' "$D/out")
  if grep -q 'error' "$D/out"; then echo "★ 진단이 나왔다: $(cat "$D/out")"; exit 4; fi
  echo "exit $rc · 다시 방출한 .js [${emitted:-없음}] · .tsbuildinfo 를 썼나 $info"
}
for decl in false true; do
  for v in 7.0.2 5.9.3; do
    rm -rf "$D/w"; mkdir -p "$D/w/src"
    echo '{ "compilerOptions": { "incremental": true, "target": "es2022", "outDir": "dist", "rootDir": "src", "tsBuildInfoFile": "dist/.tsbuildinfo" }, "include": ["src"] }' > "$D/w/tsconfig.json"
    echo 'export const a: number = 1;' > "$D/w/src/a.ts"
    echo 'import { a } from "./a"; export const b = a + 1;' > "$D/w/src/b.ts"
    echo 'export const c = 3;' > "$D/w/src/c.ts"
    echo "---- $v · declaration $decl"
    for s in "${steps[@]}"; do
      case ${s%% *} in
        3) echo 'export const c = 4;' > "$D/w/src/c.ts" ;;
        4) echo 'export const a: number = 2;' > "$D/w/src/a.ts" ;;
        5) echo 'export const a = 2;' > "$D/w/src/a.ts" ;;
      esac
      printf '  %-22s ' "${s#* }"; build "$v" "$decl"
    done
  done
done
```

```text
===== bash ts42b-inc43.sh (sh exit=0) =====
---- 7.0.2 · declaration false
  처음                 exit 0 · 다시 방출한 .js [a.js b.js c.js] · .tsbuildinfo 를 썼나 1
  안 바꿈             exit 0 · 다시 방출한 .js [없음] · .tsbuildinfo 를 썼나 0
  c.ts 값만            exit 0 · 다시 방출한 .js [c.js] · .tsbuildinfo 를 썼나 1
  a.ts 값만(타입 같음) exit 0 · 다시 방출한 .js [a.js b.js] · .tsbuildinfo 를 썼나 1
  a.ts 타입까지      exit 0 · 다시 방출한 .js [a.js b.js] · .tsbuildinfo 를 썼나 1
---- 5.9.3 · declaration false
  처음                 exit 0 · 다시 방출한 .js [a.js b.js c.js] · .tsbuildinfo 를 썼나 1
  안 바꿈             exit 0 · 다시 방출한 .js [없음] · .tsbuildinfo 를 썼나 0
  c.ts 값만            exit 0 · 다시 방출한 .js [c.js] · .tsbuildinfo 를 썼나 1
  a.ts 값만(타입 같음) exit 0 · 다시 방출한 .js [a.js b.js] · .tsbuildinfo 를 썼나 1
  a.ts 타입까지      exit 0 · 다시 방출한 .js [a.js b.js] · .tsbuildinfo 를 썼나 1
---- 7.0.2 · declaration true
  처음                 exit 0 · 다시 방출한 .js [a.js b.js c.js] · .tsbuildinfo 를 썼나 1
  안 바꿈             exit 0 · 다시 방출한 .js [없음] · .tsbuildinfo 를 썼나 0
  c.ts 값만            exit 0 · 다시 방출한 .js [c.js] · .tsbuildinfo 를 썼나 1
  a.ts 값만(타입 같음) exit 0 · 다시 방출한 .js [a.js] · .tsbuildinfo 를 썼나 1
  a.ts 타입까지      exit 0 · 다시 방출한 .js [a.js b.js] · .tsbuildinfo 를 썼나 1
---- 5.9.3 · declaration true
  처음                 exit 0 · 다시 방출한 .js [a.js b.js c.js] · .tsbuildinfo 를 썼나 1
  안 바꿈             exit 0 · 다시 방출한 .js [없음] · .tsbuildinfo 를 썼나 0
  c.ts 값만            exit 0 · 다시 방출한 .js [c.js] · .tsbuildinfo 를 썼나 1
  a.ts 값만(타입 같음) exit 0 · 다시 방출한 .js [a.js] · .tsbuildinfo 를 썼나 1
  a.ts 타입까지      exit 0 · 다시 방출한 .js [a.js b.js] · .tsbuildinfo 를 썼나 1
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **「안 바꿈」은 두 판 · 두 설정 모두 `[없음]`** — `.tsbuildinfo` 도 **다시 안 썼다**(`0`). 일지가 「바뀐 것 없음」을 알아봤다.
- ★★★ **「c.ts 값만」은 `[c.js]` 하나** — 아무도 `c` 를 import 하지 않으니 **그것만** 다시 방출한다.
- ★★★ **「a.ts 값만(타입 같음)」이 두 설정에서 갈렸다** — `declaration: false` 는 **`[a.js b.js]`**, `declaration: true` 는 **`[a.js]`**. 겉모습(`a: number`)이 그대로라는 것을 **선언을 뽑아 본 판만** 알아봤다.
- ★★ **「a.ts 타입까지」**(`a: number` → `a = 2` — 타입이 `2` 로 좁아짐)는 두 설정 모두 **`[a.js b.js]`** — 겉모습이 바뀌면 의존자 `b` 를 다시 짓는다.
- ★★ **두 판이 20단계에서 한 줄도 안 갈렸다.**

```text
  a.ts 의 값만 바꿨을 때 — b.ts 를 다시 방출하나

  declaration: false    a 의 겉모습을 모른다   ─> a 가 바뀌면 import 한 b 도   [a.js b.js]
  declaration: true     a 의 .d.ts 를 비교한다 ─> 겉모습이 같으면 b 는 건너뜀  [a.js]
                        ★ 겉모습이 바뀌면(a = 2) 둘 다  [a.js b.js]
```

비용 — **`.tsbuildinfo` 라는 파일이 하나 더 생긴다**(이 실험은 `dist/` 안에 두었다). 두 번째 빌드가 **얼마나 빠른지는 재지 않았다** — 이 절이 말하는 것은 「**무엇을 다시 방출하나**」뿐이다. 다시 **검사**한 파일 수는 이 창이 보여 주지 않는다(머리말의 제5의 상태).

### (5) ★ 인용표 — 형제가 이미 잰 네 옵션과 하나

**언제 쓰나** — 나머지 옵션의 판단 지점을 한 장으로 볼 때. **다시 재지 않았다** — 칸은 전부 형제 편의 블록이다.

| 옵션 | 판단이 갈리는 지점 | 형제가 잰 것 | 어디 |
|---|---|---|---|
| `lib` | **하나라도 적으면 기본 목록 전체를 대체**한다 · 안 적으면 `target` 기본값을 따라간다 | `--lib es2020` 에서 `document`·`console` 이 `TS2584` · 7.0.2 와 5.9.3 이 「안 줌」 행에서 갈렸다(`1 / 5`) | [38번](../38-ambient-global-types-configuration/) 3절 |
| `lib` | **`lib` 는 약속이다** — 런타임에 그 API 가 있는지는 대조하지 않는다 | 7.0.2 기본 `lib` 가 허락한 `toSorted` 가 node 18 에서 `TypeError` · node 20 은 통과 | [38번](../38-ambient-global-types-configuration/) 4절 |
| `module` · `moduleResolution` | 7.0.2 에서 `node10`·`node`·`classic` 이 `TS5108` · `baseUrl` 이 `TS5102` · 기본 해석이 판마다 다르다 | 받아들인 행 7.0.2 `4 / 8` · 기본 `Bundler`·`Node10`·`NodeJs` | [35번](../35-module-resolution/) 1절 |
| `isolatedModules` | 파일 하나만 보는 도구가 못 하는 일을 **미리 막는다** · 방출은 거의 안 바꾼다 | 끔과 갈린 칸 `1 / 8`(`verbatimModuleSyntax` 는 `4 / 8`) | [36번](../36-type-only-imports-and-exports/) 1절 · [02번](../02-type-checking-vs-emit/) 5절 |
| `skipLibCheck` | **`.d.ts` 의 진단 전부를 끈다** — 오타 `TS2304` · 중복 선언 `TS2403` 이 사라지고 **먼저 나온 선언이 조용히 이긴다** | 파일 순서만 바꾸자 탐침이 `string` → `number` — 알려 줄 진단은 꺼져 있었다 | [37번](../37-writing-declaration-files/) 6절 |
| `useDefineForClassFields` | 필드가 **정의**인가 **대입**인가 — 부모 setter · 재선언 필드 · 초기자 순서 | 다섯 판 격자(7.0.2 넷 · 4.9.5 하나) · `TS2610`·`TS2612`·`TS2729` | [32번](../32-class-type-aspects/) 5절 |

- ★★★ **`skipLibCheck` 를 「빠르게 하려고」 켠다는 말은 이 표에 없다** — 37편은 **무엇을 숨기나**만 쟀다. 시간은 **어느 편도 재지 않았다.**
- ★★ 3절은 이 표의 마지막 행에서 **「`target` 을 안 적은 칸」** 하나만 더한 것이다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  "target": "es2015" … "esnext"          방출할 문법의 상한 — 넘는 문법은 내려 쓴다        (2절)
  "target" 없음                          판의 기본값 — 7.0.2 는 높고 5.9.3 은 es5            (3절)
  "incremental": true                    .tsbuildinfo 를 쓰고 두 번째 빌드는 바뀐 것만        (4절)
  "incremental": true, "declaration": true   겉모습이 같은 변경은 의존자를 건너뛴다          (4절)
  tsc --listEmittedFiles                 다시 방출한 파일을 찍는다 — 4절의 판별 창
```

**금지 사례** — 이 주제에서 던져 받은 것이다(7.0.2).

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `--target es5` | `TS5108` | 1절 |
| `--target es3` | `TS6046` (5.9.3 은 `TS5108`) | 1절 |
| `--downlevelIteration` | `TS5102` | 1절 |
| `--module amd` · `umd` · `system` | `TS5108` + `TS5095` | 1절 |
| `--module none` | `TS6046` | 1절 |
| `--outFile out.js` | `TS5102` | 1절 |

**규칙 불릿**

- ★★★ **7.0.2 는 `target es5`·`downlevelIteration`·`module amd/umd/system`·`outFile` 을 막는다** — 5.9.3 은 넷 다 조용히 받는다(1절).
- ★★★ **`target` 은 방출할 문법을 고른다** — `es2015` 에서 넷, `es2020` 에서 클래스 필드 하나가 내려갔다(2절).
- ★★★ **`target` 을 안 적으면 판마다 런타임이 다를 수 있다** — 부모 setter 가 7.0.2 는 안 불리고 5.9.3 은 불렸다(3절).
- ★★ **`incremental` 은 바뀐 파일과 그 의존자를 다시 방출한다** — `declaration` 이 켜지면 겉모습이 같은 변경의 의존자를 건너뛴다(4절).

## 어디서 틀리나

- ★★★ 「**7.0 에서 `es5` 가 안 되면 `es3` 도 같은 진단이다**」 — `es3` 는 **`TS6046`**(목록에 없음)이고 5.9.3 에서 이미 `TS5108` 이었다(1절).
- ★★★ 「**`target` 을 안 적었으니 방출은 판과 무관하다**」 — 기본값이 판마다 달라 **필드가 정의냐 대입이냐**가 바뀐다(3절 — 같은 경고 `TS2610`, 다른 `node` 출력).
- ★★ 「**`module amd` 를 막는 진단은 하나다**」 — 7.0.2 는 기본 해석 `bundler` 와 맞물려 **`TS5095` 가 같이** 난다(1절).
- ★★ 「**`target es2020` 이면 클래스 필드는 그대로 나온다**」 — **`this.x = 1` 로 내려간다.** 네이티브 필드는 `es2022` 부터(2절).
- ★★ 「**`incremental` 은 안 바뀐 파일을 전부 건너뛴다**」 — 바뀐 파일을 **import 하는 파일**도 다시 방출한다. `declaration` 이 꺼져 있으면 **겉모습이 같아도** 그렇다(4절).
- ★★ 「**`incremental`·`skipLibCheck` 는 빌드를 빠르게 한다**」 — **이 문서는 재지 않았다.** 무엇을 건너뛰나(4절)와 무엇을 숨기나(37편)만 쟀다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **ECMAScript** | `?.`·`??`(ES2020) · 클래스 필드(ES2022) · `async`(ES2017) · 제너레이터·`for…of`(ES2015) | 2절 격자가 **그 판에 맞춰** 갈렸다 |
| **★★★ tsc 판의 선택** | 7.0.2 가 막은 값·옵션 | 1절 — 5.9.3 은 받는다 |
| **★★★ tsc 판의 기본값** | 기본 `target` — 3절의 런타임을 가른다 | 3절 · 38편 3절 |
| **★ tsc 동작 — 두 판 같음** | `target` 별 방출 규칙 · `incremental` 의 다시 방출 규칙 | 2절 `0 / 24` · 4절 20단계 |
| **★ 판에 매인 진단 문구** | `TS5095` 가 같이 나는 것 — 기본 해석 `bundler` 의 결과 | 1절 |
| **안 잰 것** | 빌드 시간 · 방출물 크기 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★★ **`target` 을 명시한다** — 판을 올려도 방출·런타임이 안 바뀐다 | `target` 을 비워 두기 — 3절처럼 판이 런타임을 바꾼다 |
| ★★★ **올리기 전 1절 격자처럼 5.9.3 → 7.0.2 두 판에 던져 본다** | 5.9.3 이 조용하니 괜찮겠지 — 넷을 조용히 받았다(1절) |
| ★★ 실행 환경이 받는 가장 높은 `target` | 필요 없이 낮은 `target` — 도우미 코드가 붙는다(2절) |
| ★★ `incremental` + `declaration` — 의존자 재방출을 줄이려면 | `incremental` 만 켜고 「겉모습이 같으니 건너뛰겠지」(4절) |
| ★ `.tsbuildinfo` 의 자리를 `tsBuildInfoFile` 로 정해 둔다 | 저장소에 흘리기 — 빌드 산출물이다 |

## 핵심 문장

1. **7.0.2 는 `target es5`·`es3`·`downlevelIteration`·`module amd/umd/system/none`·`outFile` 을 받지 않는다** — 5.9.3 이 받던 행 중 `7 / 10` 이 막혔고, README 의 세 주장이 전부 맞았다.
2. **`es3` 와 `es5` 는 사라진 모양이 다르다** — `es3` 는 값 목록에서 빠졌고(`TS6046`), `es5` 는 「제거된 값」(`TS5108`)이다.
3. **`target` 은 방출할 문법을 고른다** — `es2015` 에서 넷, `es2020` 에서 클래스 필드 하나가 내려갔고(`10 / 48`), 두 판의 규칙은 같았다.
4. **`target` 을 안 적으면 판의 기본값이 런타임을 가른다** — 같은 소스에서 부모 setter 가 7.0.2 는 안 불리고 5.9.3 은 불렸다.
5. **`incremental` 은 바뀐 파일과 그 의존자를 다시 방출하고, `declaration` 이 켜져야 겉모습이 같은 변경을 건너뛴다** — 시간이 아니라 방출 목록으로 가렸다.

## 관련 자료

- [**39번 주제** — `strict` 묶음](../39-strict-bundle/) — ★★★ **README 의 선행.** 7.0 기본값이 바뀐 **검사** 쪽. 여기는 **출력** 쪽 다이얼.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) 7절 — `TS5108` 대 `TS5102` 의 구분을 처음 세운 곳.
- [**35번 주제**](../35-module-resolution/) · [**36번 주제**](../36-type-only-imports-and-exports/) · [**37번 주제**](../37-writing-declaration-files/) · [**38번 주제**](../38-ambient-global-types-configuration/) · [**32번 주제**](../32-class-type-aspects/) — 5절 인용표의 출처. **그쪽이 정본이고 여기는 한 장으로 묶기만.**
- [**44번 주제**](../44-project-references-and-declaration-emit/)(프로젝트 참조와 선언 방출) — `incremental` 위에 선 `composite`·`tsc -b`. [**45번 주제**](../45-type-level-performance/)(타입 수준 성능) — 이 문서가 재지 않은 **시간**.

## 용어 풀이

> **`target`** — 방출물에 쓸 ECMAScript 문법의 상한. 그보다 새 문법은 내려 쓴다.\
> 예: 2절 — `es2020` 에서 `x = 1` 이 `this.x = 1` 로.

> **내려 쓰기(downleveling)** — 새 문법을 옛 문법으로 흉내 내 방출하는 것. 도우미 함수(`__awaiter`·`__values`)가 붙기도 한다.\
> 예: 2절 `es2015` 방출물 넷.

> **`downlevelIteration`** — `es5` 이하에서 `for…of`·스프레드를 반복자 규약대로 내려 쓰는 옵션. 7.0.2 에서 `TS5102`.\
> 예: 2절 5.9.3 `es5` 방출 둘.

> **`TS6046`** — 「Argument for '--…' option must be: …」 — 그 값이 받는 목록에 없다.\
> 예: 1절 `target es3` · `module none`.

> **`incremental` · `.tsbuildinfo`** — 지난 빌드의 파일 상태를 적어 두고 다음 빌드에서 바뀐 것만 다시 하는 옵션과 그 일지 파일.\
> 예: 4절 「안 바꿈」 `[없음]`.

> **`--listEmittedFiles`** — 이번 빌드가 쓴 파일을 `TSFILE:` 줄로 찍는다. 4절은 그중 `.js` 이름만 뽑았다.\
> 예: 4절.

## 더 들어가면

- **`noCheck`·`isolatedDeclarations` 로 방출만 빠르게** — 44편이 `isolatedDeclarations` 를 본다. `noCheck` 는 **던지지 않았다.**
- **7.0 에서 `es5` 가 필요할 때** — 방출을 tsc 밖의 변환기(Babel·SWC·esbuild)에 맡기는 길. **어느 것도 던지지 않았다.**
- **`tsBuildInfoFile` 의 기본 자리** — 이 실험은 `dist/.tsbuildinfo` 로 **명시**했다. 안 적었을 때의 자리는 44편 3절(`composite` 에서 `tsconfig.tsbuildinfo`)에 한 번 나온다.
