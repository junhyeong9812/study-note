# js/syntax/42 — ESM 모듈: 「이름을 빌려 오고(라이브·불변) · 연결이 평가보다 먼저 · 순환은 `6 / 32` — `var` 는 `undefined`, 함수 선언은 멀쩡」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스 · 로컬 HTTP 서버) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다.** Chrome 151 은 이름공간 쓰기 문구와 없는 파일의 거부 모양만 달랐다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(`dynamic42e.cjs` 와 Chrome 쪽 소스는 [2-summary.md](2-summary.md) 동작 (3)·(5)).
> `js40b-42a/`(1번) · `js40b-42b/`(2번 · 10번) · `js40b-42c-cycle-grid.js`(3번 · 6번 · 7번 · 8번) · `js40b-42d/`(4번) · `js40b-42e/` + `js40b-42e-static.sh`(5번 · 9번).

## 정답

### 1. ESM — **`0 · 0` → `1 · 1` → `2 · 2`** · CommonJS — **세 줄 다 `0 · 0`** ★★★

**출력**

```text
===== cd js40b-42a && node20 main42a.mjs (exit=0) =====
[1] before inc()  n = 0 · ns.n = 0
[2] after inc()   n = 1 · ns.n = 1
[3] after inc()   n = 2 · ns.n = 2
```

```text
===== cd js40b-42a && node20 main42a.cjs (exit=0) =====
[1] before inc()  n = 0 · m.n = 0
[2] after inc()   n = 0 · m.n = 0
[3] after inc()   n = 0 · m.n = 0
```

**왜 그런가**

- ★★★ `import { n }` 은 `CreateImportBinding` 이 만든 **간접 바인딩** — 읽을 때마다 `counter42a.mjs` 의 `n` 칸을 읽는다. `ns.n` 도 같은 칸이다.
- ★★★ `module.exports = { n, inc }` 는 **그 순간의 값 `0` 을 새 객체에 담았다.** 모듈 안의 `n++` 는 지역 변수만 바꾼다 — 구조 분해한 `n` 도, `m.n` 도 `0` 이다.

### 2. `[1]` — **`TypeError` 넷**(대입 · 이름공간 쓰기 · 새 속성 · 삭제)과 **`ok 3`** · `[2]` — **`[object Module]` · `"Module"` · `null` · `false` · `false` · `writable: true` 인 서술자 · `"undefined"`** ★★★

**출력**

```text
===== cd js40b-42b && node20 main42b.mjs (exit=0) =====
[1] writes
  v = 2                             TypeError 「Assignment to constant variable.」
  ns.v = 2                          TypeError 「Cannot assign to read only property 'v' of object '[object Module]'」
  ns.w = 2 (a new property)         TypeError 「Cannot add property w, object is not extensible」
  delete ns.v                       TypeError 「Cannot delete property 'v' of [object Module]」
  setV(3), then read v              ok 3
[2] the namespace object
  Object.prototype.toString.call(ns)ok "[object Module]"
  ns[Symbol.toStringTag]            ok "Module"
  Object.getPrototypeOf(ns)         ok null
  Object.isExtensible(ns)           ok false
  Object.isFrozen(ns)               ok false
  descriptor of v                   ok {"value":3,"writable":true,"enumerable":true,"configurable":false}
  this at the top level             ok "undefined"
```

**왜 그런가**

- ★★★ 가져온 바인딩은 **불변**이고 모듈 코드는 **늘 엄격**이라 `v = 2` 가 `TypeError 「Assignment to constant variable.」` 로 던진다 — 내보낸 쪽 선언이 `let` 이어도 그렇다.
- ★★ 이름공간 객체는 **확장 불가** · 쓰기와 삭제를 **늘 거절**한다. 값은 라이브라 **동결은 아니다**(`isFrozen false` · `writable: true`).
- ★★ 바꾸는 길은 **내보낸 모듈의 함수**(`setV(3)` → `ok 3`)뿐이다.

### 3. **`6 / 32`** — `a first` · 최상위 읽기에서 `let`·`const`·`class`·`default` 식·`default class` 는 **`ReferenceError`**, `var` 는 **`undefined`**, `function`·`default function` 은 **`A`** — 나머지 26칸은 전부 **`A`** ★★★

**출력**

```text
===== node20 js40b-42c-cycle-grid.js (exit=0) =====
form                        main imports  b reads at its top level                                    b reads later, inside a function
export let X                a first       ReferenceError 「Cannot access 'X' before initialization」    A
export let X                b first       A                                                           A
export const X              a first       ReferenceError 「Cannot access 'X' before initialization」    A
export const X              b first       A                                                           A
export var X                a first       undefined                                                   A
export var X                b first       A                                                           A
export function X           a first       A                                                           A
export function X           b first       A                                                           A
export class X              a first       ReferenceError 「Cannot access 'X' before initialization」    A
export class X              b first       A                                                           A
export default expression   a first       ReferenceError 「Cannot access 'X' before initialization」    A
export default expression   b first       A                                                           A
export default function     a first       A                                                           A
export default function     b first       A                                                           A
export default class        a first       ReferenceError 「Cannot access 'X' before initialization」    A
export default class        b first       A                                                           A

cells that did not read "A": 6 / 32
```

**왜 그런가**

- ★★★ `main` 이 `a` 를 먼저 가져오면 평가는 **깊이 우선**이라 `b` 의 본문이 **`a` 의 본문보다 먼저** 돈다. 그때 `a` 의 `X` 는 **준비만 된 상태**다 — 준비의 모양이 셋이다(6번).
- ★★ `b` 를 먼저 가져오면 `a` 가 **먼저 끝까지** 돌아, `b` 가 읽을 때는 모두 `A` 다. 「나중에 읽기」는 `main` 이 부를 때라 **늘** `A` 다.
- ★ 두 node 판과 Chrome 151 이 32칸을 같게 냈다(Chrome 도 `6 / 32` — 요약 동작 (3)).

### 4. ESM — **`dep42d.mjs: body runs` 가 맨 먼저** · CommonJS — **`first line` → `dep42d.cjs: body runs` → `line after the require`** · 평가 순서 **`right · left · top`**, `right` 는 **한 번** ★★★

**출력**

```text
===== cd js40b-42d && node20 main42d.mjs (exit=0) =====
dep42d.mjs: body runs
main42d.mjs: first line
main42d.mjs: line after the import · x = x
```

```text
===== cd js40b-42d && node20 main42d.cjs (exit=0) =====
main42d.cjs: first line
dep42d.cjs: body runs
main42d.cjs: line after the require · x = x
```

```text
===== cd js40b-42d && node20 top42d.mjs (exit=0) =====
right42d.mjs: body
left42d.mjs: body
top42d.mjs: body
```

**왜 그런가**

- ★★★ ESM 의 `import` 는 **실행되는 문장이 아니라 연결 정보**다. 모듈 그래프를 먼저 다 잇고(연결), **의존하는 모듈부터** 평가한다 — 그래서 파일 중간에 적어도 `dep42d` 가 먼저다.
- ★★ CommonJS 의 `require` 는 **그 줄에서 도는 함수 호출**이다.
- ★★ 각 모듈은 **한 번만** 평가된다 — `left` 가 이미 `right` 를 평가시켰으니 `top` 의 두 번째 가져오기는 다시 돌리지 않는다.

### 5. 블록 안 — **`SyntaxError 「Unexpected token '{'」` · 0 줄** · 없는 이름 — **`SyntaxError 「… does not provide an export named 'nope'」` · 0 줄 · `has42e` 도 안 돈다** · `import()` — **`Promise` · `yes = 1` · 같은 객체 `true`** · 없는 파일은 node **`Error · ERR_MODULE_NOT_FOUND`**, Chrome **`TypeError`** ★★

```js
// inblock42e.mjs
// An import statement inside a block.
console.log("inblock42e.mjs: first line");
if (true) {
  import { yes } from "./has42e.mjs";
}
```

**출력**

```text
===== ./js40b-42e-static.sh (exit=0) =====
--- node20 inblock42e.mjs
file://<dir>/inblock42e.mjs:4
  import { yes } from "./has42e.mjs";
         ^

SyntaxError: Unexpected token '{'
(exit 1 · standard output had 0 lines)
--- node18 inblock42e.mjs
file://<dir>/inblock42e.mjs:4
  import { yes } from "./has42e.mjs";
         ^

SyntaxError: Unexpected token '{'
(exit 1 · standard output had 0 lines)
--- node20 missing42e.mjs
file://<dir>/missing42e.mjs:3
import { nope } from "./has42e.mjs";
         ^^^^
SyntaxError: The requested module './has42e.mjs' does not provide an export named 'nope'
(exit 1 · standard output had 0 lines)
--- node18 missing42e.mjs
file://<dir>/missing42e.mjs:3
import { nope } from "./has42e.mjs";
         ^^^^
SyntaxError: The requested module './has42e.mjs' does not provide an export named 'nope'
(exit 1 · standard output had 0 lines)
```

```text
===== cd js40b-42e && node20 dynamic42e.mjs (exit=0) =====
dynamic42e.mjs: first line
import() returned Promise
has42e.mjs: body runs
yes = 1 · same namespace object the second time: true
missing file: rejected with Error · code ERR_MODULE_NOT_FOUND
```

Chrome 151 — 같은 세 파일.

```text
===== ./js40b-browser.sh --http js40b-42e/inblock42e.mjs (exit=0) =====
uncaught Uncaught SyntaxError: Unexpected token '{'
```

```text
===== ./js40b-browser.sh --http js40b-42e/missing42e.mjs (exit=0) =====
uncaught Uncaught SyntaxError: The requested module './has42e.mjs' does not provide an export named 'nope'
```

```text
===== ./js40b-browser.sh --http js40b-42e/dynamic42e.mjs (exit=0) =====
dynamic42e.mjs: first line
import() returned Promise
has42e.mjs: body runs
yes = 1 · same namespace object the second time: true
missing file: rejected with TypeError · code undefined
```

**왜 그런가**

- ★★★ `import` 선언은 **모듈 최상위의 문법**이다 — 블록 안이면 **파싱**에서 거절된다.
- ★★★ 없는 이름은 **연결**에서 거절된다 — `InitializeEnvironment` 가 `ResolveExport` 로 찾다가 **null 이면 `SyntaxError`**. 연결은 **모든 평가보다 먼저**라 `has42e.mjs` 의 첫 줄도 안 돌았다.
- ★★ `import()` 는 **평가 중에 부르는 식**이다. 없는 파일을 찾는 것은 **호스트**라 거부의 모양이 node 와 Chrome 에서 달랐다.

### 6. `var` 는 **`undefined` 로 초기화** · 렉시컬 선언(`let`·`const`·`class`)은 **바인딩만**(초기화 전) · **함수 선언은 곧바로 함수 객체로 초기화** — 3번의 `undefined` 한 칸 · TDZ 다섯 칸 · 함수 두 칸 ★★★

- ★★★ 명세 `InitializeEnvironment` 의 세 걸음 그대로다 — `CreateMutableBinding` + `InitializeBinding(name, undefined)`(var) · `CreateMutableBinding`/`CreateImmutableBinding` 만(렉시컬) · `InstantiateFunctionObject` + `InitializeBinding`(함수 선언).
- ★★ `export default 식` 과 `export default class` 는 렉시컬 쪽, `export default function` 은 **함수 선언** 쪽이다 — 격자에서 그렇게 갈렸다.

### 7. **16칸 전부 `A`** — TDZ 는 **「언제 읽나」** 의 문제다(05번) · `var` 로 바꾸면 **`ReferenceError` 대신 `undefined` 가 조용히 흐른다** ★★

- ★★ 같은 `export let X` 도 `b first` 나 「나중에」 읽으면 `A` 였다 — 막히는 것은 **`a` 의 본문이 `X = "A"` 에 닿기 전**이라는 **시간**이다.
- ★ `export var X` · `a first` · 최상위 = `undefined` — 에러가 사라지는 대신 **값이 틀린 채** 간다.

### 8. 파이썬은 **`7 / 24`**(`ImportError`/`AttributeError`) — 축이 **「어떻게 import 했나」 대 「어떻게 export 했나」** · 공통으로 **「함수 안에서(나중에) 읽는 열」이 전부 통과** · Go 는 **빌드에서** `import cycle not allowed` ★★

- ★★ 파이썬 42번의 `깨진 칸 7 / 24` 는 `from ca import TAG`(`ImportError`)와 맨 위의 `ca.TAG`(`AttributeError`)였고 **함수 안 import 열은 전부 통과**했다. 이 문서의 「나중에 읽기」 열도 전부 `A` 다.
- ★ Go 는 실행 전에 거부한다 — 파이썬 42번 7절의 `go build` 가 `import cycle not allowed` · `(exit 1)` 이었다.

### 9. 연혁 문서는 「**정적 구조라 빌드 도구가 트리 셰이킹을 할 수 있다**」 — 이 문서는 **재지 않았다** · 실행으로 보인 것은 **블록 안 `import` 의 파싱 오류**와 **없는 이름이 본문 전에 막힌 것** ★★

- ★★ 크기·속도는 이 문서의 근거 밖이다. 「정적」의 실행 쪽 증거는 5번의 두 블록(`standard output had 0 lines`)이다.

### 10. 파일 찾기·모듈 판정은 **호스트**, 없는 이름의 `SyntaxError`·불변 바인딩은 **언어** ★

- ★ 명세의 `HostLoadImportedModule` 이 호스트에게 「이 지정자의 모듈을 가져와라」를 맡긴다. 연결 규칙(`ResolveExport`·`CreateImportBinding`)은 ECMA-262 가 정한다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js40b-42a/*` | ★★★ 라이브 바인딩 `0 → 1 → 2` · CommonJS `0` | node20 1벌 + node18 대조 + Chrome 1벌 |
| `js40b-42b/*` | ★★★ 대입 `TypeError` · 이름공간 브랜드 | node20 1벌 + node18 대조 + Chrome 1벌 |
| `js40b-42c-cycle-grid.js` · `js40b-42c-cycle.web.js` | ★★★ 순환 32칸 · 「`6 / 32`」 | node20 32칸 + node18 대조 + Chrome 32칸 |
| `js40b-42d/*` | ★★★ `import` 가 먼저 · 평가 순서 | node20 1벌씩 + node18 대조 + Chrome 1벌 |
| `js40b-42e/*` + `js40b-42e-static.sh` | ★★ 파싱·연결 단계의 `SyntaxError` · `import()` | node20 · node18 각 1벌 + Chrome 1벌씩 |

세 판 대조기(이 묶음 전체의 plain 탐침). 이 주제의 줄은 `42c`(node 전용) 하나다 — 나머지 모듈 탐침은 `cd <디렉토리> && node20 …` 블록마다 **node 18 을 같은 명령으로 던져 비교했고**(다르면 `-node18` 블록이 생긴다) **이 주제에서는 하나도 생기지 않았다.**

```sh
# js40b-vdiff.sh
#!/usr/bin/env bash
# Every plain probe of this batch (js40b-4NX-*.js, not *.web.js), run on node18, node20 and Chrome 151.
# A probe that uses a node-only API (process.* or require) is compared between the two node versions only.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
s18=0; d18=0; sw=0; dw=0; skip=0
for f in js40b-4[0123]?-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"; b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then r18=identical; s18=$((s18 + 1)); else r18=DIFFERS; d18=$((d18 + 1)); fi
  if grep -q 'process\.\|require(' "$f"; then rw="(node only)"; skip=$((skip + 1))
  else
    w="$(./js40b-browser.sh "$f")"
    if [ "$w" = "$b" ]; then rw=identical; sw=$((sw + 1)); else rw=DIFFERS; dw=$((dw + 1)); fi
  fi
  printf '%-34s node18/node20 %-10s node20/Chrome %s\n' "$f" "$r18" "$rw"
done
echo ""
echo "node18 vs node20: identical $s18 · differs $d18   ·   node20 vs Chrome 151: identical $sw · differs $dw · node only $skip"
```

```text
===== ./js40b-vdiff.sh (exit=0) =====
js40b-40a-close-grid.js            node18/node20 identical  node20/Chrome DIFFERS
js40b-40c-which-protocol.js        node18/node20 identical  node20/Chrome identical
js40b-40d-yield-and-ticks.js       node18/node20 identical  node20/Chrome identical
js40b-41a-abort-mid-job.js         node18/node20 identical  node20/Chrome DIFFERS
js40b-41b-reasons.js               node18/node20 identical  node20/Chrome DIFFERS
js40b-41c-signal-tree.js           node18/node20 identical  node20/Chrome identical
js40b-42c-cycle-grid.js            node18/node20 identical  node20/Chrome (node only)
js40b-43a-interop-grid.js          node18/node20 DIFFERS    node20/Chrome (node only)
js40b-43b-type-grid.js             node18/node20 DIFFERS    node20/Chrome (node only)

node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 3 · differs 3 · node only 3
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **없는 파일의 `import()` 거부 모양**(node `ERR_MODULE_NOT_FOUND` · Chrome `TypeError`) — 호스트의 것이다.
- ★ 문구 — `Cannot access 'X' before initialization` · `Assignment to constant variable.` · 이름공간 쓰기 문구(Chrome 151 은 `Cannot assign to property …`).
