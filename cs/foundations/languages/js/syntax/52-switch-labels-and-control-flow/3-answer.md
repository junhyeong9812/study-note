# js/syntax/52 — `switch`·라벨·흐름 제어 세부: 「`NaN` 은 어디에도, `-0` 은 먼저 나온 `0` 으로 — `default` 는 다 떨어진 뒤의 입구이고, 라벨은 함수 경계를 못 넘는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6** 에서 실제로 돌려 얻은 것이고, **node v18.19.1 · Google Chrome 151 도 한 글자도 같았다**(실행 검증의 대조기). 블록은 **전부 캡처 파일에서 조립**했다.
> ★★ 예외 **문구**는 판에 매이는 칸이다 — 근거는 **예외의 종류와 「compile / run」** 이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js48b-52a-case-grid.js`(1번 · 6번) · `js48b-52b-clause-order.js`(2번 · 7번 · 8번) · `js48b-52c-switch-scope.js`(3번 · 9번) · `js48b-52d-labels.js`(4번 · 5번 · 9번).

## 정답

### 1. `[1]` — **`NaN → default`** · **`-0 → 0`**(`Object.is` 는 `-0`, SameValueZero 는 `0`) · 나머지는 세 열이 같다(`objA → objA`) · `[2]` — 대각선 여섯 칸 + **`-0`/`0` 네 칸** 이 `y`, **`NaN` 행 · `objA` 행은 전부 `.`** · **`3 / 64` · `1 / 64`** ★★★

**출력**

```text
===== node20 js48b-52a-case-grid.js (exit=0) =====
[1] case list in source order: 1 | '1' | NaN | 0 | -0 | objB {a:1} | null | undefined | objA | default
  switch (x)    switch enters   Object.is picks   SameValueZero picks
  1             1               1                 1
  '1'           '1'             '1'               '1'
  NaN           default         NaN               NaN
  -0            0               -0                0
  0             0               0                 0
  objA {a:1}    objA            objA              objA
  null          null            null              null
  undefined     undefined       undefined         undefined

[2] one clause at a time: y = the clause is selected (rows: discriminant, columns: case value)
              1         '1'       NaN       -0        0         objB      null      undefined
  1           y         .         .         .         .         .         .         .
  '1'         .         y         .         .         .         .         .         .
  NaN         .         .         .         .         .         .         .         .
  -0          .         .         .         y         y         .         .         .
  0           .         .         .         y         y         .         .         .
  objA {a:1}  .         .         .         .         .         .         .         .
  null        .         .         .         .         .         .         y         .
  undefined   .         .         .         .         .         .         .         y
  cells that differ from Object.is: NaN / NaN · -0 / 0 · 0 / -0
cells where switch differs from Object.is: 3 / 64 · from SameValueZero: 1 / 64
```

**왜 그런가**

- ★★★ `CaseClauseIsSelected` 가 **`IsStrictlyEqual`** 을 돌려준다 — `NaN` 은 자기와도 다르고, `-0 === 0` 은 참이다. 그래서 `Object.is`(SameValue)와 갈린 칸이 **`NaN`/`NaN` · `-0`/`0` · `0`/`-0`** 셋, SameValueZero 와 갈린 칸이 **`NaN`/`NaN`** 하나다.
- ★★ `-0` 이 `0` 에 들어간 것은 **목록에서 `0` 이 먼저**이기 때문이다 — `case` 는 앞에서부터 시험해 첫 참에서 멈춘다(2번).
- ★★ 객체는 **정체성** — 모양이 같은 `objB` 를 지나 맨 뒤 `objA` 에 들어갔다. `'1'`/`1` · `null`/`undefined` 칸이 `.` 인 것은 **강제 변환이 없어서**다.

### 2. `[1]` — `x = 1` **`test A > body A > body default > body B > body C`** · `x = 2` `test A > test B > body B > body C` · `x = 3` `test A > test B > test C > body C` · `x = 9` **`test A > test B > test C > body default > body B > body C`** · `[2]` — 시험은 같고 몸통이 **하나씩** · `[3]` `test first 1 > body first` · `[4]` `test discriminant > test A > test B > test C > body C` ★★★

**출력**

```text
===== node20 js48b-52b-clause-order.js (exit=0) =====
[1] no break anywhere
  x = 1   test A > body A > body default > body B > body C
  x = 2   test A > test B > body B > body C
  x = 3   test A > test B > test C > body C
  x = 9   test A > test B > test C > body default > body B > body C
[2] break at the end of every clause
  x = 1   test A > body A
  x = 2   test A > test B > body B
  x = 3   test A > test B > test C > body C
  x = 9   test A > test B > test C > body default
[3] two clauses with the same value
  x = 1   test first 1 > body first
[4] where the discriminant is evaluated
  test discriminant > test A > test B > test C > body C
```

**왜 그런가**

- ★★★ **시험은 소스 순서로, 첫 참에서 멈춘다** — `x = 1` 에서 `test B`·`test C` 가 **없다.** 몸통은 골라진 자리부터 **소스 순서로 흘러내리고** `default` 몸통도 그 길 위에 있다.
- ★★★ **`x = 9`** — `default` 를 **건너뛰고 뒤쪽 `case` 까지 다 시험**한 뒤 `default` 몸통 → 뒤쪽 몸통을 **시험 없이**(7번).
- ★ 같은 값의 `case` 둘은 에러가 아니고 첫째만 골라진다 · 판별식은 맨 먼저 한 번.

### 3. `compile: SyntaxError` — **`let a` 둘** · **`let a`/`var a`** · **`const c` 둘** · **엄격 모드의 `function h` 둘** · `run:` 값 — 중괄호 `one` · `var` 둘 `one` · 흘러내림 `zero` · `var` 건너뜀 `undefined` · 함수 `g` 두 줄 `g` · 비엄격 `function h` 둘 **`1`** · `run: ReferenceError` — **건너뛴 `let a` 를 읽기·쓰기·`typeof` 세 줄** · **`class K`** ★★

**출력**

```text
===== node20 js48b-52c-switch-scope.js (exit=0) =====
[1] let with the same name in two clauses
  case 0: let a · case 1: let a               compile: SyntaxError 「Identifier 'a' has already been declared」
  the same, each clause in braces             run: one
  case 0: var a · case 1: var a               run: one
  case 0: let a · case 1: var a               compile: SyntaxError 「Identifier 'a' has already been declared」
[2] a let declared in one clause, used in another
  case 0: let a · case 1: return a            run: ReferenceError 「Cannot access 'a' before initialization」
  case 0: let a · case 1: a = 'one'           run: ReferenceError 「Cannot access 'a' before initialization」
  case 0: let a · case 1: typeof a            run: ReferenceError 「Cannot access 'a' before initialization」
  case 0: let a · x = 0 falls into case 1     run: zero
  case 0: var a · case 1: return a            run: undefined
[3] const and function declarations
  case 0: const c · case 1: const c           compile: SyntaxError 「Identifier 'c' has already been declared」
  case 0: function g · case 1: g()            run: g
  the same, 'use strict'                      run: g
  case 0: function h · case 1: function h     run: 1
  the same, 'use strict'                      compile: SyntaxError 「Identifier 'h' has already been declared」
  case 0: class K · case 1: new K             run: ReferenceError 「Cannot access 'K' before initialization」
```

**왜 그런가**

- ★★★ **`switch` 의 `{ }` 하나가 스코프 하나**라 `case` 마다 `let a` 를 쓰면 **한 스코프에 `a` 가 둘** — Early Error 라 **부르기 전에** 막힌다.
- ★★★ `x = 1` 이 `case 0` 을 **건너뛰어** `let a` 의 초기화가 한 번도 안 돌았다 → TDZ. **`x = 0` 으로 흘러내리면** 초기화를 지나가서 `zero`.
- ★★ 함수 선언은 블록 맨 앞에서 만들어져 건너뛰어도 부를 수 있고, `class` 는 `let` 처럼 TDZ 다. 같은 이름 함수 둘은 **비엄격에서만** 허용(9번).

### 4. `[1]` — **`00 10 20`** · **`00 01 02 10`** · **`00 01 02 10 20 21 22`** · `[2]` **`a > after`** · `[3]` **`default 0 > end of body 0 > case 1 break > end of body 1 > case 2 continue > default 3 > end of body 3`** ★★

**출력**

```text
===== node20 js48b-52d-labels.js (exit=0) =====
[1] nested loops, break and continue with and without the label
  continue outer at j === 1   00 10 20
  break outer2 at i,j === 1,1 00 01 02 10
  plain break at i,j === 1,1  00 01 02 10 20 21 22
[2] a label on a block that is not a loop
  a > after
[3] break and continue inside a switch that sits in a loop
  default 0 > end of body 0 > case 1 break > end of body 1 > case 2 continue > default 3 > end of body 3
[4] compiled with new Function
  break nope   (no such label)            SyntaxError 「Undefined label 'nope'」
  blk: { continue blk; }                  SyntaxError 「Illegal continue statement: 'blk' does not denote an iteration statement」
  blk: { break blk; }                     compiles, returns ok
  break outside any loop or switch        SyntaxError 「Illegal break statement」
  continue in a switch, no loop           SyntaxError 「Illegal continue statement: no surrounding iteration statement」
  a: a: ;   (the same label twice)        SyntaxError 「Label 'a' has already been declared」
  break outer inside a callback           SyntaxError 「Undefined label 'outer'」
  lbl: function f() {}                    compiles, returns function
  'use strict'; lbl: function f() {}      SyntaxError 「In strict mode code, functions can only be declared at top level or inside a block.」
```

**왜 그런가**

- ★★ `continue outer` 는 안쪽 루프의 나머지를 버리고 **바깥의 다음 `i`** · `break outer2` 는 **두 루프 다** 끝 · 라벨 없는 `break` 는 **안쪽 하나만**.
- ★★ 루프가 아닌 블록도 `break 라벨` 의 표적이 된다.
- ★★★ `switch` 안의 `break` 는 **`switch` 만** 끝내고, `continue` 는 **바깥 루프의 다음 바퀴** — `case 2 continue` 뒤에 `end of body 2` 가 없다.

### 5. 컴파일되는 것은 둘 — **`blk: { break blk; }`** · **비엄격의 `lbl: function f() {}`** · 나머지 일곱은 전부 **`SyntaxError`** — `Undefined label 'nope'` · `'blk' does not denote an iteration statement` · `Illegal break statement` · `no surrounding iteration statement` · `Label 'a' has already been declared` · **콜백 안의 `break outer` 도 `Undefined label 'outer'`** · 엄격 모드의 라벨 붙은 함수 ★★

- ★★ 출력은 4번 블록의 `[4]` 아홉 줄이다.
- ★★★ **콜백 안에서는 바깥 라벨이 「없는 이름」** 이다 — 명세가 라벨과 `continue` 의 범위를 **함수 경계에서 끊는다**(「not crossing function … boundaries」).
- ★★ **`continue` 는 루프 라벨만** — 루프가 아닌 블록·루프 없는 `switch` 에서는 컴파일 에러. `break` 는 라벨이 있으면 **아무 문**이 표적이 된다.

### 6. **`IsStrictlyEqual(NaN, NaN)` 이 거짓**이라 `CaseClauseIsSelected` 가 한 번도 참을 안 돌려준다 · `switch` 앞의 `if (Number.isNaN(x))` 나 **`switch (true) { case Number.isNaN(x): … }`** ★★★

- ★★★ 1번 `[2]` 의 `NaN` 행이 **자기 자신 칸까지 여덟 칸 전부 `.`** 다. 33번이 서명 `nynynnny` 의 첫 글자 `n` 으로 잰 것과 같다.

### 7. **앞쪽 `case`(A) → 뒤쪽 `case`(B·C)를 전부 평가**한 뒤 `default` · 그다음 **`default` 아래 몸통(B·C)을 시험 없이** · `CaseBlockEvaluation` 의 **9단계**(뒤쪽 `CaseClauses` 를 시험) → **11단계**(`DefaultClause` 평가) → **15단계**(「another complete iteration of the second CaseClauses」) ★★★

- ★★★ 2번 `x = 9` 의 `test A > test B > test C > body default > body B > body C` 가 그 순서 그대로다. `default` 는 **자리가 아니라 「다 떨어진 뒤」** 의 입구다.

### 8. `case` 식은 **소스 순서로, 첫 참에서 멈춰** 평가된다 — 들어온 값이 앞쪽 `case` 에 맞으면 뒤쪽 식은 **평가조차 안 된다**(2번 `x = 1` 은 `test A` 하나, `x = 9` 는 셋) · `switch (true)` 관용구는 **「순서대로 · 첫 참에서 멈춘다」** 쪽에 기댄다 — `if … else if` 사슬과 같은 평가 순서다 ★★

- ★ 단 비교가 `===` 라서 **조건이 정확히 `true`** 여야 한다(불리언이 아닌 값을 내는 조건은 안 걸린다 — 이 문장은 1번의 「강제 변환이 없다」 에서 끌어낸 것이다).

### 9. 3번의 **같은 이름 함수 `h` 둘**(비엄격 `run: 1` · 엄격 `SyntaxError`) · 5번의 **라벨 붙은 함수 선언**(비엄격 컴파일 · 엄격 `SyntaxError`) · 명세 본문은 둘 다 금지하고 **「non-strict code and the host is a web browser or otherwise supports …」** 조건으로 Annex B 가 푼다 · 문구 `functions can only be declared at top level or inside a block` 는 **원인(라벨)을 가리키지 않는다** ★★

- ★★ 3번의 함수 `g` 두 줄은 엄격·비엄격이 **같다**(`g`) — 블록 수준 함수 선언은 본문 규칙이라 층이 다르다.
- ★ 근거로는 **`SyntaxError` 라는 종류와 엄격/비엄격의 갈림**만 쓴다(규칙 27).

### 10. 기본값 — **JS·옛 Java `case:` 는 흘러내림이 기본**, **Go 와 Java 화살표 `case ->` 는 안 흘러내림이 기본** · 적어야 하나 — Go 는 **`fallthrough` 라고 적어야** 내려간다(JS 는 반대로 **`break` 를 적어야 멈춘다**) · 다음 조건 — **셋 다 흘러내릴 때 다음 `case` 의 조건을 안 본다**(JS `x = 1 → body B > body C` · Go `case 1:` 에서 `fallthrough` 하면 `case 99` 몸통이 돈다) ★★

- ★ Go 15번 동작 (1) · Java 21번. JS 에는 흘러내림 경고가 엔진에 없다(요약 「어디서 틀리나 (4)」).

### 11. **`"after block"`** — `finally` 의 `break out` 이 `return "T"` 를 **지우고** 라벨 블록 밖으로 나갔다 · 이 문서의 `block: { … break block; … }` 가 보인 「**`break 라벨` 은 루프가 아닌 블록에서도 그 블록 밖으로**」 가 32번에서는 **완료 기록을 덮어쓰는 도구**로 쓰였다 ★

- ★ 32번 동작 (2) · 이 문서 4번 `[2]`. 라벨 `break` 는 **완료 기록 `break`** 이고, `finally` 의 비정상 완료는 `try` 의 `return` 을 이긴다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js48b-52a-case-grid.js` | ★★★ 64칸 · 「`3 / 64`」 · 「`1 / 64`」 · 줄지은 `case` 에서 `-0 → 0` | node20 · node18 · Chrome 151(같음) |
| `js48b-52b-clause-order.js` | ★★★ `case` 식의 평가 순서 · 흘러내림 · `default` 의 자리 | 〃 |
| `js48b-52c-switch-scope.js` | ★★ 한 스코프 · TDZ · Annex B 함수 | 〃 |
| `js48b-52d-labels.js` | ★★ 라벨 · `switch` 안의 `continue` · Early Error 일곱 | 〃 |

세 판 대조기.

```sh
# js48b-52e-three-runtimes.sh
#!/usr/bin/env bash
# Every probe of this topic (js48b-52[a-d]-*.js) on node18, node20 and Chrome 151: is the output the same as node20's, byte for byte?
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
same=0; total=0
for f in js48b-52[a-d]-*.js; do
  b="$("$N20" "$f")" || exit 1
  a="$("$N18" "$f")" || exit 1
  w="$(./js48b-browser.sh "$f")" || exit 1
  [ "$a" = "$b" ] && r18=identical || r18=DIFFERS
  [ "$w" = "$b" ] && rw=identical || rw=DIFFERS
  for r in "$r18" "$rw"; do total=$((total + 1)); [ "$r" = identical ] && same=$((same + 1)); done
  printf '%-32s node18/node20 %-10s Chrome/node20 %s\n' "$f" "$r18" "$rw"
done
echo "comparisons identical to node20: $same / $total"
```

```text
===== ./js48b-52e-three-runtimes.sh (exit=0) =====
js48b-52a-case-grid.js           node18/node20 identical  Chrome/node20 identical
js48b-52b-clause-order.js        node18/node20 identical  Chrome/node20 identical
js48b-52c-switch-scope.js        node18/node20 identical  Chrome/node20 identical
js48b-52d-labels.js              node18/node20 identical  Chrome/node20 identical
comparisons identical to node20: 8 / 8
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★ **예외 문구**(3번 · 5번)뿐이다. 격자·로그·예외 **종류**는 명세 본문의 것이라 판이 올라도 같아야 하고, Annex B 두 칸은 **엄격 모드의 `SyntaxError`** 가 같아야 한다.
