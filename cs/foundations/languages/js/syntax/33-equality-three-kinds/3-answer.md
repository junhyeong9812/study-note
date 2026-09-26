# js/syntax/33 — 동등성 세 종류: 「`NaN` 과 `-0` 두 행 — 쓰는 곳마다 어느 알고리즘인지」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 새 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(3번의 `.web.js`) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다. ★★ **1번의 답은 앞 편의 블록**이 근거다 — 링크의 동작 번호를 연다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js32b-33-h-equality-core.js` + `js32b-33a-new-places.js`(2번) · `js32b-33-h-equality-core.js` + `js32b-33b-new-places.web.js`(3번 · 7번) · `js32b-33c-typed-and-string.js`(4번 · 6번 · 7번).

## 정답

### 1. `NaN` 은 `===`·`==`·`indexOf` 만 「다르다」, `-0` 은 `Object.is` 만 「다르다」 — `Map` 키와 여덟 답이 같은 열은 **`Set` 과 `includes`** ★★★

- ★★★ **`NaN, NaN`** — `===` 다르다 · `==` 다르다 · `Object.is` 같다 · `Map` 키 같다 · `includes` 같다 · `indexOf` 다르다. **`0, -0`** — **`Object.is` 만 다르다**, 나머지 다섯은 같다.
  근거 — [23번](../23-map-set-and-weak-collections/2-summary.md) 동작 (1)의 격자(`NaN, NaN` 행 · `0, -0` 행).
- ★★★ **`Set` 과 `includes`**(각 `0 / 8`) — 셋이 SameValueZero 한 가족이다. 격자 전체의 집계는 `9 / 56`.
- ★★ [26번](../26-array-search-flatten-and-create/2-summary.md) 동작 (2) — `[0].indexOf(-0)` 은 **`0`**, `[-0].includes(0)` 은 **`true`**. 배열은 **`-0` 을 그대로** 담는다(`Object.is([-0].at(0), -0)` 이 `true`).
- ★★ [02번](../02-coercion-and-loose-equality/2-summary.md) 동작 (3) — **정확히 두 칸**, 대각선 위의 `0`/`-0` 과 `NaN`/`NaN` — 서로 **반대 방향**으로 갈린다.

### 2. `switch` 와 `findIndex(x => x === b)` 는 **`===`**, 재정의는 **`Object.is`** — node 20 에는 `groupBy` 가 없어 `3 / 3` ★★★

**출력**

```text
===== node20 js32b-33a-new-places.js (exit=0) =====
                                switch        findIndex===  redefine      groupBy
  NaN, NaN                      n             n             y             (absent)
  0, -0                         y             y             n             (absent)
  '1', 1                        n             n             n             (absent)
  1, 1.0                        y             y             y             (absent)
  true, 1                       n             n             n             (absent)
  null, undefined               n             n             n             (absent)
  {a:1}, {a:1}  (two objects)   n             n             n             (absent)
  o, o  (one object)            y             y             y             (absent)

  which reference comparison gives the same eight answers:
    switch                nynynnny   ===
    findIndex===          nynynnny   ===
    redefine              ynnynnny   Object.is
    groupBy               (absent in this runtime)
    reference ===         nynynnny
    reference Object.is   ynnynnny
    reference includes    yynynnny
    reference ==          nyyyyyny
new columns whose signature equals a reference column: 3 / 3
```

**왜 그런가**

- ★★★ **`switch`·`findIndex===` 는 `nynynnny`**(`===` 와 같다), **`redefine` 은 `ynnynnny`**(`Object.is` 와 같다). `groupBy` 는 **`(absent)`** — node 20 에 `Map.groupBy` 가 없다(판별 블록 `ES2024 … no`).
- ★★ 마지막 줄 **`3 / 3`** — 물을 수 있었던 세 열이 **전부** 기준 넷 중 하나와 글자까지 같았다.

### 3. `Map.groupBy` 는 **SameValueZero**(`includes` 와 같은 서명) — 그리고 **`-0` 을 `+0` 으로 저장**한다 · `4 / 4` ★★

**출력**

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js32b-page.html?js32b-33-h-equality-core.js,js32b-33b-new-places.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
                                switch        findIndex===  redefine      groupBy
  NaN, NaN                      n             n             y             y
  0, -0                         y             y             n             y
  '1', 1                        n             n             n             n
  1, 1.0                        y             y             y             y
  true, 1                       n             n             n             n
  null, undefined               n             n             n             n
  {a:1}, {a:1}  (two objects)   n             n             n             n
  o, o  (one object)            y             y             y             y

  which reference comparison gives the same eight answers:
    switch                nynynnny   ===
    findIndex===          nynynnny   ===
    redefine              ynnynnny   Object.is
    groupBy               yynynnny   includes
    reference ===         nynynnny
    reference Object.is   ynnynnny
    reference includes    yynynnny
    reference ==          nyyyyyny
new columns whose signature equals a reference column: 4 / 4

[2] the key Map.groupBy stores for -0
  Object.is(stored key, -0)   false
  Object.is(stored key, +0)   true
```

**왜 그런가**

- ★★★ **`groupBy` 의 서명은 `yynynnny`** — `reference includes` 와 같다. `NaN` 둘은 한 무리, `0` 과 `-0` 도 한 무리.
- ★★ **`[2]` `Object.is(stored key, -0)` 이 `false`, `+0` 이 `true`** — 23번 동작 (2)의 `Map` 과 같다. 명세의 `GroupBy` 가 키를 **`CanonicalizeKeyedCollectionKey`** 에 통과시킨다.
- ★ 마지막 줄이 **`4 / 4`** — node 에서 빠졌던 열이 채워졌을 뿐, 나머지 세 열의 서명은 node 와 한 글자도 같다.

### 4. TypedArray 는 **배열과 같은 짝**(`indexOf` 는 `===`, `includes` 는 SameValueZero) · 문자열 `includes` 는 **동등성이 아니다** · 재정의는 **SameValue** ★★★

**출력**

```text
===== node20 js32b-33c-typed-and-string.js (exit=0) =====
[1] TypedArray -- the same two methods as on arrays
  new Float64Array([NaN]).indexOf(NaN)            -1
  new Float64Array([NaN]).includes(NaN)           true
  new Float64Array([-0]).includes(0)              true
  Object.is(new Float64Array([-0])[0], -0)        true
  Object.is(new Int32Array([-0])[0], -0)          false
  new Float64Array([1]).includes('1')             false
  new Float64Array([1]).indexOf('1')              -1
[2] String.prototype.includes -- given a number
  'NaN'.includes(NaN)                             true
  '-0'.includes(-0)                               true
  '10'.includes(1)                                true
  String(-0)                                      "0"
[3] Object.defineProperty on a non-writable, non-configurable property
  value 0, redefine with -0                       TypeError 「Cannot redefine property: k」
  value NaN, redefine with 0/0                    ok
  value 0, redefine with 0                        ok
  frozen { k: 0 }, redefine with -0               TypeError 「Cannot redefine property: k」
```

**왜 그런가**

- ★★★ **`[1]`** — `indexOf(NaN)` `-1`, `includes(NaN)` `true`, `includes(0)` 은 `[-0]` 에서 `true` — 배열과 같다. **`Float64Array` 는 `-0` 을 그대로**(`true`), **`Int32Array` 는 `+0`**(`false` — 정수 저장). `'1'` 은 못 찾는다(`false`·`-1`).
- ★★★ **`[2]` 동등성이 아니다** — 넷 다 `true` 인 것은 인자를 **글자로 바꾼 뒤 부분 문자열**을 찾았기 때문이다(`String(-0)` 이 `"0"`).
- ★★★ **`[3]` 첫 줄과 넷째 줄이 `TypeError 「Cannot redefine property: k」`** — `0` 을 `-0` 으로 재정의하려 했다. `NaN` 을 `0/0` 으로, `0` 을 `0` 으로는 `ok`. **SameValue** 로 견준 결과다.

### 5. **`NaN` 칸과 `-0` 칸의 네 조합 중 세 개**를 각각 하나씩 차지한다 — 그리고 `==` 는 강제 변환이 더 붙는다 ★★★

- ★★★ **IsStrictlyEqual** — `NaN` 다르다 / `-0` 같다. **SameValue** — `NaN` 같다 / `-0` 다르다. **SameValueZero** — `NaN` 같다 / `-0` 같다.
- ★★ **IsLooselyEqual** — 두 칸은 `===` 와 같고, 타입이 다르면 **강제 변환 뒤 다시 견준다**(`'1' == 1` · `null == undefined` — 02번).
- ★★ **「찾기」와 「키」에는 `-0` 을 가르면 불편하다** — 계산 결과로 생긴 `-0` 이 `0` 키를 못 찾게 된다. 그래서 `NaN` 은 찾되 `±0` 은 합치는 자가 따로 있다. `Map`·`Set`·`groupBy` 는 한 걸음 더 나가 **저장할 때 `-0` 을 지운다**(7번).

### 6. `CaseClauseIsSelected` 는 **`IsStrictlyEqual`** 을, 재정의 판정은 **`SameValue`** 를 돌려준다 ★★

- ★★★ `CaseClauseIsSelected` 는 `case` 식을 평가해 **`IsStrictlyEqual(input, clauseSelector)`** 를 돌려준다 — 2번의 `switch` 서명이 그 실측이다.
- ★★★ `ValidateAndApplyPropertyDescriptor` 는 쓰기 불가·설정 불가 데이터 프로퍼티에서 **`SameValue(Desc.[[Value]], current.[[Value]])`** 를 돌려준다. NOTE — 「**SameValue returns true for NaN values which may be distinguishable by other means**」 — 비트가 다른 `NaN` 도 같다고 보고 **기존 프로퍼티를 그대로 둔다.** 4번 `[3]` 의 `0/0` 이 `ok` 인 이유다.
- ★ `OrdinaryHasInstance` 는 프로토타입 **객체**를 `SameValue` 로 견준다 — 객체끼리는 `===` 와 답이 같아서 **갈라 볼 방법이 없다.** 잴 것이 없어 행을 두지 않았다(부적용).

### 7. **`Map`·`Set`·`Map.groupBy` 는 `+0`**, 배열·`Float64Array` 는 **`-0`**, `Int32Array` 는 **`+0`**, 객체 키는 **`"0"`** ★★★

- ★★★ `Map`·`Set` — `+0`(23번 동작 (2)) · `Map.groupBy` — `+0`(3번 `[2]`) · 배열 — `-0`(26번 동작 (2)) · `Float64Array` — `-0`, `Int32Array` — `+0`(4번 `[1]`) · 평범한 객체 — 키 글자 `"0"`(23번 동작 (1)의 `object key` 열).
- ★★ **`CanonicalizeKeyedCollectionKey`** — 「key 가 `-0` 이면 `+0`」. `Map.prototype.set` · `Set.prototype.add` · `GroupBy`(컬렉션 판)가 부른다.
- ★ **`+0`** — 23번 동작 (8)의 `log ["+0"]`. 접기가 **콜백을 부르기 전에** 일어난다.

### 8. 문자열 `includes` 는 **부적용 행** · UI 라이브러리의 비교는 **언어 밖** · `switch` 는 **52번** · 파이썬 대비는 **23번 동작 (9)** ★★

- ★★ `String.prototype.includes` — 동등성이 아니라 부분 문자열 검색이라 정본 표에 **부적용**으로 올렸다(4번 `[2]`).
- ★★ **안 들어간다** — 이 표는 **ECMA-262 가 정한 자리**만 담는다. 라이브러리가 무엇을 쓰는지는 그 라이브러리의 문서가 정한다.
- ★ 목록의 **52번 주제**(`switch`·라벨·흐름 제어 세부).
- ★ [23번](../23-map-set-and-weak-collections/2-summary.md) 동작 (9) — 파이썬은 **정체(`is`) 먼저, 그다음 `==`** 라 `nan` 두 개가 두 칸이 된다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js32b-33-h-equality-core.js` + `js32b-33a-new-places.js` | ★★★ 새 자리 셋의 서명 · 「`3 / 3`」 | node20 1벌 + node18 대조 1벌 |
| `js32b-33-h-equality-core.js` + `js32b-33b-new-places.web.js` | ★★★ `Map.groupBy` 의 서명 · 저장 키 · 「`4 / 4`」 | **Chrome 151 만** |
| `js32b-33c-typed-and-string.js` | ★★ TypedArray · 문자열 `includes` · 재정의 `TypeError` | node20 1벌 + node18 대조 1벌 |
| (인용) 02 · 23 · 26 편의 블록 | 정본 표의 인용 10행 | 그 편의 「실행 검증」 |
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

- ★★ **`Map.groupBy`** — node 가 ES2024 를 받으면 2번의 `groupBy` 열이 채워질 것이다(`4 / 4` 가 기대값이지만 **돌려서 확인한다**).
- ★ 재정의 실패 **문구** — V8 의 것이다.
