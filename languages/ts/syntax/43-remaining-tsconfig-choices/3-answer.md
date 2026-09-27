# ts/syntax/43 — `tsconfig` 의 나머지 선택 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 4창 격자 「7.0 에서 막힌 값」이고, 둘째 기둥은 3창 격자 「`target` 이 무엇을 내리나」다.** `incremental` 은 시간 대신 **`--listEmittedFiles`** 로 물었다(제5의 상태).\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 7.0.2 는 대조 행만 받았다(`1 / 10`) — `es5` `TS5108` · `es3` `TS6046` · `downlevelIteration` `TS5102` · AMD/UMD/System `TS5108`+`TS5095` · `none` `TS6046` · `node10` `TS5108` · `outFile` `TS5102` — README 는 **맞다**

**출력**

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

**왜 그런가**

- ★★★ **5.9.3 은 받는데 7.0.2 가 막은 행 `7 / 10`** — 5.9.3 은 `es5`·`downlevelIteration`·AMD 계열·`outFile` 을 **진단 없이** 받는다. 올리기 전에는 신호가 없다.
- ★★ `TS5108` 은 **값**, `TS5102` 는 **옵션**, `TS6046` 은 **받는 값 목록에 없음**이다(02편 7절의 구분 + 5번).
- ★ 4.9.5 는 `node10` 이라는 **이름**을 모른다(`TS6046` — 35편 1절).

### 2. ★★★ `es2015` 에서 `?.`·`??`·클래스 필드·`async` 넷이 내려가고, `es2020` 에서는 **클래스 필드 하나** · `es2022`·`esnext` 는 전부 남음 · 제너레이터·`for…of` 는 넷 다 남음 — 두 판이 다른 칸 **`0 / 24`**

**출력**

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

**왜 그런가**

- ★★★ 각 문법은 **자기가 들어온 판**보다 낮은 `target` 에서만 내려간다 — `?.`·`??` 는 ES2020, 클래스 필드는 ES2022, `async` 는 ES2017, 제너레이터·`for…of` 는 ES2015.
- ★★ 클래스 필드가 `es2020` 에서 **`this.x = 1`** 로 내려가는 것이 3번·32편 5절의 「정의 대 대입」 갈림의 출발점이다.
- ★ 마지막 줄 **내려간 칸 `10 / 48`**(두 판 합).

### 3. ★★★ 7.0.2 — **`own keys ["x"] x 1`**(setter 안 불림) · 5.9.3 — **`Parent setter got 1`** → **`own keys [] x -1`** — 진단은 두 판 모두 **`TS2610`** 으로 같다

**출력**

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

**왜 그런가**

- ★★★ 방출물에서 `x = 1` 이 든 첫 줄이 **`x = 1;`**(7.0.2 — 네이티브 필드 = 정의) 대 **`_this.x = 1;`**(5.9.3 — 대입)이다. 정의는 부모 setter 를 **안 거치고**, 대입은 **거친다.**
- ★★ 갈린 것은 **판의 기본 `target`** 이다(38편 3절 — 7.0.2 `es2025` · 5.9.3 `es5`). 경고가 같아서 **진단만 봐서는 모른다.**

### 4. ★★★ 처음 `[a.js b.js c.js]` · 안 바꿈 `[없음]` · c 값만 `[c.js]` · **a 값만(타입 같음) — `declaration` 끔 `[a.js b.js]`, 켬 `[a.js]`** · a 타입까지 `[a.js b.js]` — 두 판이 같다

**출력**

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

**왜 그런가**

- ★★★ `.tsbuildinfo` 가 **바뀐 파일과 그것을 import 한 파일**을 고른다 — `c` 는 아무도 import 하지 않아 혼자, `a` 는 `b` 가 import 해서 둘.
- ★★★ `declaration` 이 켜지면 `a` 의 **`.d.ts` 를 뽑아 비교**할 수 있다 — `a: number` 가 그대로면 **`b` 를 건너뛴다.** 꺼져 있으면 겉모습을 모르니 `b` 도 다시 한다.
- ★ 「안 바꿈」 단계는 `.tsbuildinfo` 도 **다시 안 썼다**(`0`).

### 5. ★★ `es3` **`TS6046`**(받는 값 목록에 없음) · `es5` **`TS5108`**(제거된 값 — 안내 문구가 붙는다) · 5.9.3 의 `es3` 는 이미 **`TS5108`**

- ★★ `es3` 는 두 판에 걸쳐 **두 단계로** 사라졌다 — 5.9.3 에서 「제거된 값」, 7.0.2 에서 **목록에서도 빠짐.** `es5` 는 지금 7.0.2 에서 첫 단계에 있다. `TS6046` 의 목록이 `es6` 부터다(1번 진단 전문).

### 6. ★★ 7.0.2 의 **기본 해석이 `bundler`** 라서다 — `bundler` 는 `module` 이 `preserve`·`commonjs`·`es2015` 이상일 때만 받는다(「Option 'bundler' can only be used when …」)

- ★★ `--module amd` 는 그 자체로 `TS5108` 이고, 남은 기본 `moduleResolution: bundler` 와 **맞물려** `TS5095` 가 하나 더 붙는다. 기본 해석이 `Bundler` 인 것은 35편 1절이 쟀다.

### 7. ★★★ 없이 — **배열 인덱스 루프**(`xs_1.length` 로 센다) · `--downlevelIteration` — **`__values` 도우미로 반복자 규약** · 7.0.2 에서는 `es5` 가 `TS5108`, `downlevelIteration` 이 `TS5102` 라 **둘 다 없다**

**출력**

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

- ★★ 앞쪽은 **배열에만** 맞는 흉내이고 뒤쪽은 `Symbol.iterator` 를 찾는다. 7.0 에서 `es5` 방출이 필요하면 tsc 밖의 도구가 맡는다 — **던지지 않았다.**

### 8. ★★★ **`--listEmittedFiles` 가 찍는 「다시 방출한 `.js`」** 로 판별했다 · 못 보는 것 — **다시 검사했지만 방출은 안 한 파일**

- ★★ 시간은 흔들리는 칸이고 「빠르다」는 이 문서가 주장하지 않는다. 방출 목록은 **파일 이름**이라 안 흔들린다(머리말 표). 검사 비용 자체는 [**45번 주제**](../45-type-level-performance/)가 잰다.

### 9. ★★ `skipLibCheck` — **`.d.ts` 의 진단 전부**(오타 `TS2304` · 중복 선언 `TS2403`)를 숨겨 **먼저 나온 선언이 조용히 이긴다** · 「빠르게」는 **어디서도 재지 않았다** · `lib` 를 하나 적으면 **기본 목록 전체를 대체**한다

- ★★ [**37번 주제**](../37-writing-declaration-files/) 6절 — 파일 순서만 바꾸자 탐침이 `string` → `number` 가 됐고 그것을 알려 줄 진단은 꺼져 있었다.
- ★★ [**38번 주제**](../38-ambient-global-types-configuration/) 3절 — `--lib es2020` 만 적은 칸에서 `document`·`console` 이 `TS2584` — `dom` 이 빠졌다.

### 10. ★★ 32편 5절 — **다섯 판**(7.0.2 넷 — `es2022`·`es2021` × `useDefineForClassFields` 기본/반대로 명시 — 과 4.9.5 `es2022` 하나) · 3번이 더한 칸 — **`target` 을 안 적은 판 × 두 판**

- ★★ [**32번 주제**](../32-class-type-aspects/) 5절은 **`target` 을 적은** 칸들로 「정의 대 대입」을 갈랐다. 3번은 **적지 않은** 칸 하나 — 판의 기본값이 그 갈림을 대신 고른다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `"$TSC_OLD"`·`"$TSC_49"` · `node` | `7.0.2` · `5.9.3` · `4.9.5` · `v18.19.1` |
| ★★★ 막힌 값 | `bash ts42b-blocked43.sh` — 열 행 × 세 판 | 7.0.2 받은 행 **`1 / 10`** · 5.9.3 이 받는데 막힌 행 **`7 / 10`** |
| ★★★ 방출 격자 | `bash ts42b-emit43.sh` — 여섯 × 넷 × 두 판 | 내려간 칸 **`10 / 48`** · 두 판 다른 칸 **`0 / 24`** |
| ★★ `es5` 두 방출 | 5.9.3 · `fo43.ts` × `downlevelIteration` 끔/켬 | 인덱스 루프 · `__values` |
| ★★★ `target` 없이 | `bash ts42b-ud43.sh` — 두 판 | setter 7.0.2 0번 · 5.9.3 1번 |
| ★★ `incremental` | `bash ts42b-inc43.sh` — 두 설정 × 두 판 × 다섯 단계 | 20단계에서 두 판 같음 · 「a 값만」에서 설정이 갈림 |
| ★ 가짜 격자 자기검사 | 위쪽에 `tsconfig.json` 을 둔 판 | 1·2번 스크립트가 **`exit 4`** 로 멈췄다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **막힌 값**(1번) · **기본 `target`**(3번) — 이미 판마다 달랐다.
- ★★ **`TS5095` 가 같이 나는 것**(6번) — 기본 해석에 매였다.
- ★ **방출 규칙 · 재방출 규칙**(2·4번) — 두 판이 같았다.

**안 돌려 본 것**

- ★★★ **빌드 시간 · 방출물 크기** — 재지 않았다. 「`incremental`·`skipLibCheck` 가 빠르게」는 **이 문서의 주장이 아니다.**
- ★ tsc 밖의 변환기(`es5` 대체) — 던지지 않았다.
