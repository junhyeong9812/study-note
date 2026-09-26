# js/syntax/35 — 엄격 모드: 「조용한 실패를 예외로, 헷갈리는 문법을 거절로 — 모듈과 클래스는 늘 엄격」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 새 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다. ★★ **1번의 답은 앞 편의 블록**이 근거다 — 링크의 동작 번호를 연다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js32b-35a-new-cells.js`(2번 · 5번 · 6번) · `js32b-35b-directive.js`(3번 · 7번) · `js32b-35-h-mode.mjs` + `js32b-35c-module.sh`(4번 · 8번).

## 정답

### 1. `this` `9 / 14` · `arguments` `7 / 12` · `??=` 는 **두 모드 다 `ReferenceError`** · `9 / 13` · 동결 배열 메서드는 **비엄격도 던진다** · 누수 `1 / 2` ★★★

- ★★★ [07번](../07-this-binding-four-rules/2-summary.md) 동작 (2) — `probes 14 · same 5 · DIFFER 9`. [08번](../08-function-forms-and-parameters/2-summary.md) 동작 (4) — `settings-dependent cells 7 of 12`.
- ★★★ [12번](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) 동작 (4) — **둘 다 `ReferenceError`**. 논리 할당은 **먼저 읽기 때문**이다(암시적 전역은 평범한 `G = 1` 만 만든다).
- ★★ [14번](../14-property-descriptors-and-freezing/2-summary.md) 동작 (4) — `mode-dependent cells 9 / 13`. [24번](../24-array-mutating-methods/2-summary.md) 동작 (8) — **비엄격에서도 `TypeError`**(메서드는 `Set(…, true)` 로 쓴다).
- ★★ [16번](../16-class-syntax/2-summary.md) 동작 (2) — `["leakedFromFunction"]  (1 / 2)`. 새는 것은 비엄격 쪽뿐.
- ★ [13번](../13-object-literals-and-properties/2-summary.md) — **안 막힌다**(ES2015 부터). 뒤의 키가 이긴다.

### 2. 설정에 달린 칸 **`11 / 14`** — 남은 전역은 **간접 `eval` 탐침의 두 모드**(엄격 쪽도 샜다) ★★★

**출력**

```text
===== node20 js32b-35a-new-cells.js (exit=0) =====
eval('var G = 1'), then typeof G   <-- DIFFERENT
    strict  undefined
    sloppy  number
eval('function G() {}'), then typeof G   <-- DIFFERENT
    strict  undefined
    sloppy  function
eval('let G = 1'), then typeof G
    strict  undefined
    sloppy  undefined
(0, eval)('var G = 1'), then typeof G
    strict  number
    sloppy  number
with ({ v: 1 }) { return v; }   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Strict mode code may not include a with statement」
    sloppy  1
return 010;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Octal literals are not allowed in strict mode.」
    sloppy  8
return 08;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Decimals with leading zeros are not allowed in strict mode.」
    sloppy  8
return '\101';   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Octal escape sequences are not allowed in strict mode.」
    sloppy  A
return 0o10;
    strict  8
    sloppy  8
var v = 1; return delete v;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Delete of an unqualified identifier in strict mode.」
    sloppy  false
undefined = 1; return typeof undefined;   <-- DIFFERENT
    strict  TypeError 「Cannot assign to read only property 'undefined' of object '#<Object>'」
    sloppy  undefined
'ab'.len = 1; return 'ab'.len;   <-- DIFFERENT
    strict  TypeError 「Cannot create property 'len' on string 'ab'」
    sloppy  undefined
var implements = 1; return implements;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Unexpected strict mode reserved word」
    sloppy  1
var let = 1; return let;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Unexpected strict mode reserved word」
    sloppy  1

globals left behind: ["js35_3_sloppy","js35_3_strict"]
settings-dependent cells 11 / 14
```

**왜 그런가**

- ★★★ **`eval` 넷** — 직접 `var`·`function` 은 엄격 `undefined` / 비엄격 `number`·`function`(바깥 함수로 샜다) · 직접 `let` 은 **두 모드 다 `undefined`** · 간접 `var` 는 **두 모드 다 `number`**.
- ★★★ **일곱이 전부 `COMPILE SyntaxError`** — `with` · `010` · `08` · `'\101'` · `delete v` · `implements` · `let`. 본문이 한 줄도 안 돌았다.
- ★★ **엄격은 실행에서 `TypeError`**(`Cannot assign to read only property 'undefined' …` · `Cannot create property 'len' on string 'ab'`), **비엄격은 말없이** `undefined` · `undefined`.
- ★★★ **`["js35_3_sloppy","js35_3_strict"]`** — 간접 `eval` 은 호출자의 모드를 안 물려받고 전역 코드로 돈다. **`11 / 14`** — 안 갈린 셋은 `eval('let …')` · 간접 `eval` · `0o10`.

### 3. **앞의 다섯은 `strict`, 뒤의 넷은 `sloppy`** · 비단순 목록 네 형태는 **컴파일조차 안 된다** ★★★

**출력**

```text
===== node20 js32b-35b-directive.js (exit=0) =====
[1] where the directive sits
  "use strict"; ...                       strict
  'use strict'; ...                       strict
  "hello"; "use strict"; ...              strict
  // note  NEWLINE  "use strict"; ...     strict
  "use strict"  NEWLINE  return ...       strict
  var a; "use strict"; ...                sloppy
  ("use strict"); ...                     sloppy
  "use\x20strict"; ...                    sloppy
  "USE STRICT"; ...                       sloppy
[2] a directive inside a function whose parameter list is not simple
  function (a = 1) { 'use strict'; }      COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  (a = 1) => { 'use strict'; }            COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  ({ m(...r) { 'use strict'; } })         COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  class { m({ a }) { 'use strict'; } }    COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  class { m(a) { 'use strict'; } }        compiles
```

**왜 그런가**

- ★★★ **`strict`** — 큰따옴표 · 작은따옴표 · 앞선 `"hello"` · 앞선 주석 · 세미콜론 없는 줄바꿈. **`sloppy`** — `var a;` 뒤 · 괄호 · `\x20` 이스케이프 · 대문자. **에러도 경고도 없다.**
- ★★★ **컴파일되는 것은 `class { m(a) { 'use strict'; } }` 하나** — 나머지 넷(기본값 · 화살표 · 나머지 · 구조 분해)은 `Illegal 'use strict' directive in function with non-simple parameter list`. **클래스 메서드 안이어도** 막힌다.

### 4. 모듈 판은 **엄격 넷**, CommonJS 판은 **비엄격 넷** — 모듈 안의 **`new Function`·간접 `eval` 은 비엄격** ★★★

**출력**

```text
===== ./js32b-35c-module.sh (exit=0) =====
--- node20 js32b-35-h-mode.mjs
  top-level this === undefined                        true
  plain call: this === undefined                      true
  assign to an undeclared name                        ReferenceError 「js35_mod_leak is not defined」
  direct eval('010')                                  SyntaxError 「Octal literals are not allowed in strict mode.」
  indirect (0, eval)('010')                           8
  new Function(...): plain call this === undefined    false
  globals left behind                                 []
(exit 0)
--- node20 --input-type=commonjs < js32b-35-h-mode.mjs
  top-level this === undefined                        false
  plain call: this === undefined                      false
  assign to an undeclared name                        assigned
  direct eval('010')                                  8
  indirect (0, eval)('010')                           8
  new Function(...): plain call this === undefined    false
  globals left behind                                 ["js35_mod_leak"]
(exit 0)
```

**왜 그런가**

- ★★★ **모듈** — 최상위 `this === undefined` `true` · 그냥 부른 함수 `true` · 대입 `ReferenceError 「js35_mod_leak is not defined」` · 직접 `eval('010')` `SyntaxError` · 누수 `[]`.
  **CommonJS** — `false` · `false` · `assigned` · `8` · 누수 `["js35_mod_leak"]`. 파일에 `"use strict"` 가 **없는데도** 모듈 판은 엄격이다.
- ★★ **두 판 모두** `new Function(...)` 줄은 `false`(비엄격) · 간접 `eval('010')` 은 `8`. **모듈 안에서도 이 둘은 호출자의 엄격을 안 물려받는다.**

### 5. early error 는 **컴파일에서** 거절 — 그 코드는 **한 줄도 안 돈다** · 암시적 전역·동결 쓰기는 **실행에서** ★★★

- ★★★ **early error** — 코드를 평가하기 전에 명세가 Syntax Error 로 정한 것. `new Function` 이 **함수를 만들지도 못했다**(2번의 `COMPILE`).
- ★★ **컴파일** — `with` · 옛 8진수 · 8진 이스케이프 · `delete 식별자` · 예약어 · 중복 매개변수 · 비단순 목록 + 지시어. **실행** — 암시적 전역(`ReferenceError`) · 읽기 전용 전역 · 원시값 쓰기 · 동결 쓰기(`TypeError`).
- ★ 비엄격의 실패하는 쓰기는 **`false` 를 돌려주고 그 값을 버린다** — 엄격은 **같은 자리에서 `TypeError`** 를 던진다(14번 동작 (4) — 「쓴 뒤 다시 읽는」 창으로 비엄격의 실패를 봤다).

### 6. eval 코드는 **스스로 지시어를 갖거나 · 엄격 코드 안의 직접 eval** 일 때만 엄격 — 엄격이면 **`var` 가 eval 자기 환경에** 갇힌다 ★★★

- ★★★ 두 조건 — 「eval 코드가 Use Strict Directive 로 시작하거나, **엄격 모드 코드 안에 있는 직접 eval** 이거나」.
- ★★ **`varEnv` 를 `lexEnv`(eval 자기 환경)로** 바꾼다 — 그래서 `var` 가 바깥 함수로 안 샌다(2번 탐침 0·1).
- ★★ **전역** — 간접 `eval` 은 직접 eval 이 아니므로 둘째 조건에 안 걸리고, 소스에 지시어도 없어 **비엄격 전역 코드**로 돈다. `var` 는 전역 객체에 붙는다(`js35_3_strict`).

### 7. **지시어 머리말 안의 정확한 글자** · 금지 규칙은 **「지시어가 있나 × 목록이 단순한가」** ★★

- ★★★ 본문 **맨 앞에 연달아 오는 문자열 식 문장들(머리말) 안**, 글자가 **정확히** `"use strict"` 또는 `'use strict'` — **이스케이프·줄 이음이 없어야** 한다(3번 `[1]`).
- ★★ **「지시어가 있나」** 를 본다 — `FunctionBodyContainsUseStrict` 가 참이고 `IsSimpleParameterList` 가 거짓이면 Syntax Error. 그래서 **이미 엄격인 클래스 메서드**에서도 막혔다(3번 `[2]`).
- ★ **머리말이 이미 끝났으므로 효력이 없다** — 3번의 `var a; "use strict";` 와 같은 모양이다. 에러도 안 난다.

### 8. **모듈 코드 · 클래스의 모든 부분** — 그 안의 비엄격은 **`new Function` · 간접 `eval`** ★★

- ★★★ 「**Module code is always strict mode code.**」 · 「**All parts of a ClassDeclaration or a ClassExpression are strict mode code.**」
- ★★ **`new Function(body)`**(body 가 스스로 지시어를 가질 때만 엄격) · **간접 `eval(src)`**(src 가 스스로 가질 때만). 4번이 둘 다 비엄격을 보였다.
- ★ [05번](../05-var-let-const-and-tdz/2-summary.md)의 「안 돌려 본 것 — **ESM(`.mjs`) 최상위**」 — 최상위 `this` 가 `undefined` 이고 엄격이라는 것을 4번이 쟀다.

### 9. 모듈 여부는 **호스트**가 정한다 · 모듈 자체는 **42·43번** · Annex C 의 나머지는 **안 쟀다** ★★

- ★★ **호스트**(node — `.mjs` · `--input-type` · `package.json` 의 `"type"`). 명세는 「모듈 코드면 엄격」까지다.
- ★★ [목록의 **42번 주제**](../42-esm-modules/)(ESM 모듈) · [목록의 **43번 주제**](../43-cjs-and-esm-interop/)(CJS 와 ESM 상호운용).
- ★ **있다** — 정본 표에 없는 Annex C 항목(`caller` 접근 제한 등)은 이 문서가 재지 않았다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js32b-35a-new-cells.js` | ★★★ 새 탐침 14 의 두 번 컴파일 격자 · 「`11 / 14`」 · 누수 목록 | node20 1벌 + node18 대조 1벌 |
| `js32b-35b-directive.js` | ★★★ 지시어의 자리 아홉 · 비단순 목록 다섯 형태 | node20 1벌 + node18 대조 1벌 |
| `js32b-35-h-mode.mjs` + `js32b-35c-module.sh` | ★★★ 같은 파일의 모듈 판 · CommonJS 판 | node20 1벌 |
| (인용) 05 · 07 · 08 · 09 · 10 · 12 · 13 · 14 · 16 · 24 편의 블록 | 정본 표의 인용 17행 | 그 편의 「실행 검증」 |
| `js32b-vdiff.sh` · `js32b-versions.sh` | 두 판이 갈린 탐침 수 · 판별 기능 표 | 1벌씩 |

두 node 판 대조기(이 배치 전체의 node 탐침). `DIFFERS` 가 한 줄도 없다.

```sh
# js32b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 와 셸 탐침 *.sh 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js32b-3[2345]?-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"
  b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-40s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-40s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```

```text
===== ./js32b-vdiff.sh (exit=0) =====
js32b-32a-finally-grid.js                identical
js32b-32b-finally-details.js             identical
js32b-32c-cause-chain.js                 identical
js32b-32d-hierarchy.js                   identical
js32b-32e-thrown-values.js               identical
js32b-32g-iserror-node.js                identical
js32b-33a-new-places.js                  identical
js32b-33c-typed-and-string.js            identical
js32b-34a-realm-grid.js                  identical
js32b-34c-array-edges.js                 identical
js32b-35a-new-cells.js                   identical
js32b-35b-directive.js                   identical

identical 12  ·  differs 0  ·  total 12
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★ 예외 **문구** — V8 의 것이다(`Octal literals are not allowed in strict mode.` 등).
- ★ 모듈 판별 규칙(`.mjs`·`--input-type`)은 **node 의 것**이다 — 판이 오르면 4번을 다시 돌린다.
