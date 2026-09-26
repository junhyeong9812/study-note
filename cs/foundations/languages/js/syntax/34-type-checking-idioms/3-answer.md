# js/syntax/34 — 타입 검사 관용구: 「족보는 realm 에서 끊기고, 출생 기록은 안 끊긴다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 새 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(4번의 `.web.js`) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다. ★★ **1번의 답은 앞 편의 블록**이 근거다 — 링크의 동작 번호를 연다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js32b-34-h-realm-core.js` + `js32b-34a-realm-grid.js`(2번 · 3번 · 6번 · 7번) · `js32b-34-h-realm-core.js` + `js32b-34b-realm-grid.web.js`(4번 · 9번) · `js32b-34c-array-edges.js`(5번).

## 정답

### 1. `instanceof` 는 **사슬**, `#x in` 은 **브랜드**, 브랜드 태그는 **`toStringTag` 로 `7 / 7` 바뀐다** ★★★

- ★★★ [15번](../15-prototype-chain/2-summary.md) 동작 (4) — `instanceof` 는 **사슬에 `C.prototype` 이 있나**만 본다. `Symbol.hasInstance` 가 `true` 를 돌려주면 **`'a string' instanceof K2` 도 `true`**.
- ★★★ [16번](../16-class-syntax/2-summary.md) 동작 (5) — **`instanceof Account` 는 `true`, `#balance in` 은 `false`**. 사슬은 누구나 꾸미지만 브랜드는 생성자가 돌아야 생긴다.
- ★★ [17번](../17-inheritance-and-super/2-summary.md) 동작 (5) — 브랜드 **`[object Object]`** · `Array.isArray` **`false`** · `instanceof Array` **`true`**.
- ★★ [22번](../22-symbol-and-well-known-symbols/2-summary.md) 동작 (4) — **`7 / 7`**(위조도 은폐도 된다).
- ★ [01번](../01-value-types-and-typeof/2-summary.md) — **`"object"`**(명세에 박힌 결과).

### 2. **`32 / 100`** — `instanceof` `15 / 25` · 덕 타이핑 `10 / 25` · `toString` `7 / 25` · 출생 기록 두 열 **`0`** ★★★

**출력**

```text
===== node20 js32b-34a-realm-grid.js (exit=0) =====
[1] y/n = the method's answer to 'is this a genuine <type>?'   * = differs from the truth   - = no such method
    isArray/isError column for Error uses: util.types.isNativeError (node host API)
  type     condition             truth  instanceof       isArray/isError  toString tag     duck typing      slot via method
  Array    same realm            y      y                y                y                y                -
  Array    other realm           y      n*               y                y                y                -
  Array    proto swapped         y      n*               y                y                n*               -
  Array    Object.create(proto)  n      y*               n                n                y*               -
  Array    toStringTag forged    n      n                n                y*               n                -
  Error    same realm            y      y                y                y                y                -
  Error    other realm           y      n*               y                y                y                -
  Error    proto swapped         y      n*               y                y                n*               -
  Error    Object.create(proto)  n      y*               n                n                y*               -
  Error    toStringTag forged    n      n                n                y*               n                -
  Date     same realm            y      y                -                y                y                y
  Date     other realm           y      n*               -                y                y                y
  Date     proto swapped         y      n*               -                y                n*               y
  Date     Object.create(proto)  n      y*               -                n                y*               n
  Date     toStringTag forged    n      n                -                y*               n                n
  RegExp   same realm            y      y                -                y                y                y
  RegExp   other realm           y      n*               -                y                y                y
  RegExp   proto swapped         y      n*               -                y                n*               y
  RegExp   Object.create(proto)  n      y*               -                n                y*               n
  RegExp   toStringTag forged    n      n                -                y*               n                n
  Promise  same realm            y      y                -                y                y                y
  Promise  other realm           y      n*               -                y                y                y
  Promise  proto swapped         y      n*               -                n*               n*               y
  Promise  Object.create(proto)  n      y*               -                y*               y*               n
  Promise  toStringTag forged    n      n                -                y*               n                n

  per method (cells that differ from the truth / cells asked):
    instanceof        15 / 25
    isArray/isError   0 / 10
    toString tag      7 / 25
    duck typing       10 / 25
    slot via method   0 / 15
  per condition:
    same realm            0 / 20
    other realm           5 / 20
    proto swapped         11 / 20
    Object.create(proto)  11 / 20
    toStringTag forged    5 / 20
cells that differ from the truth: 32 / 100

[2] not graded -- a Proxy with no traps around a genuine value (is a Proxy 'genuine'? the question has no single answer)
  Array    new Proxy(v, {})             y                y                y                y                -
  Error    new Proxy(v, {})             y                n                n                y                -
  Date     new Proxy(v, {})             y                -                n                y                n
  RegExp   new Proxy(v, {})             y                -                n                y                n
  Promise  new Proxy(v, {})             y                -                y                y                n
```

**왜 그런가**

- ★★★ **`other realm` 다섯 행은 `instanceof` 만 `n*`** 다 — 나머지 넷(출생 기록 · 태그 · 모양)은 다 맞았다.
- ★★★ **`proto swapped` 는 `instanceof`·덕 타이핑이 `n*`, `Object.create(proto)` 는 둘 다 `y*`** — 둘 다 **사슬**을 보기 때문이다. 출생 기록 두 열은 교체에서 `y`, `Object.create` 에서 `n` — **맞다.**
- ★★★ **`toString tag` 는 `toStringTag forged` 다섯 칸이 전부 `y*`**, 그리고 **`Promise` 만 두 칸 더**(`proto swapped` 의 `n*`, `Object.create(proto)` 의 `y*`) — 다른 타입과 다르다(7번).
- ★★ 방법별 `15 / 25` · `0 / 10` · `7 / 25` · `10 / 25` · `0 / 15`, 조건별 `0` · `5` · `11` · `11` · `5`(각 `/ 20`), 마지막 줄 **`32 / 100`**.

### 3. **`Array.isArray` 는 프록시를 뚫고(`y`), 오류 슬롯 검사는 못 뚫는다(`n`)** ★★

2번 블록의 `[2]` 가 이것이다.

- ★★★ `Array` 행 둘째 열 **`y`**(`IsArray` 가 대상으로 재귀), `Error` 행 둘째 열 **`n`**(`[[ErrorData]]` 는 대상에 있다).
- ★★ **`Array` 와 `Promise` 행** — 배열은 `IsArray` 가 뚫어서, `Promise` 는 자칭 명찰이 사슬에 있어서.
- ★ **셋 다 `n`** — `getTime`·`exec`·`then` 이 프록시에서 던진다.

### 4. **칸 글자까지 같다** — 다른 줄은 **둘째 줄(오류 슬롯 열에 쓴 함수 이름) 하나** · `32 / 100` ★★★

**출력**

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js32b-page.html?js32b-34-h-realm-core.js,js32b-34b-realm-grid.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] y/n = the method's answer to 'is this a genuine <type>?'   * = differs from the truth   - = no such method
    isArray/isError column for Error uses: Error.isError (ES2026)
  type     condition             truth  instanceof       isArray/isError  toString tag     duck typing      slot via method
  Array    same realm            y      y                y                y                y                -
  Array    other realm           y      n*               y                y                y                -
  Array    proto swapped         y      n*               y                y                n*               -
  Array    Object.create(proto)  n      y*               n                n                y*               -
  Array    toStringTag forged    n      n                n                y*               n                -
  Error    same realm            y      y                y                y                y                -
  Error    other realm           y      n*               y                y                y                -
  Error    proto swapped         y      n*               y                y                n*               -
  Error    Object.create(proto)  n      y*               n                n                y*               -
  Error    toStringTag forged    n      n                n                y*               n                -
  Date     same realm            y      y                -                y                y                y
  Date     other realm           y      n*               -                y                y                y
  Date     proto swapped         y      n*               -                y                n*               y
  Date     Object.create(proto)  n      y*               -                n                y*               n
  Date     toStringTag forged    n      n                -                y*               n                n
  RegExp   same realm            y      y                -                y                y                y
  RegExp   other realm           y      n*               -                y                y                y
  RegExp   proto swapped         y      n*               -                y                n*               y
  RegExp   Object.create(proto)  n      y*               -                n                y*               n
  RegExp   toStringTag forged    n      n                -                y*               n                n
  Promise  same realm            y      y                -                y                y                y
  Promise  other realm           y      n*               -                y                y                y
  Promise  proto swapped         y      n*               -                n*               n*               y
  Promise  Object.create(proto)  n      y*               -                y*               y*               n
  Promise  toStringTag forged    n      n                -                y*               n                n

  per method (cells that differ from the truth / cells asked):
    instanceof        15 / 25
    isArray/isError   0 / 10
    toString tag      7 / 25
    duck typing       10 / 25
    slot via method   0 / 15
  per condition:
    same realm            0 / 20
    other realm           5 / 20
    proto swapped         11 / 20
    Object.create(proto)  11 / 20
    toStringTag forged    5 / 20
cells that differ from the truth: 32 / 100

[2] not graded -- a Proxy with no traps around a genuine value (is a Proxy 'genuine'? the question has no single answer)
  Array    new Proxy(v, {})             y                y                y                y                -
  Error    new Proxy(v, {})             y                n                n                y                -
  Date     new Proxy(v, {})             y                -                n                y                n
  RegExp   new Proxy(v, {})             y                -                n                y                n
  Promise  new Proxy(v, {})             y                -                y                y                n
```

**왜 그런가**

- ★★★ node 는 `util.types.isNativeError (node host API)`, Chrome 은 `Error.isError (ES2026)` — **그 설명 줄만** 다르고 격자·집계·`[2]` 는 한 글자도 같다.
- ★★ **`32 / 100`**. `vm` 과 iframe 이 판정 다섯에 관해 **같은 realm 성질**을 보였다.

### 5. `Array.prototype` 은 **배열인데 `instanceof Array` 가 아니다** ★★

**출력**

```text
===== node20 js32b-34c-array-edges.js (exit=0) =====
                                typeof            Array.isArray     instanceof Array  tag
  [1, 2]                        object            true              true              [object Array]
  new List()                    object            true              true              [object Array]
  Array.prototype               object            true              false             [object Array]
  argsOf(1, 2)                  object            false             false             [object Arguments]
  new Uint8Array(2)             object            false             false             [object Uint8Array]
  { length: 0 }                 object            false             false             [object Object]
  'ab'                          string            false             false             [object String]
```

**왜 그런가**

- ★★★ **`object` · `true` · `false` · `[object Array]`** — 명세가 `Array.prototype` 을 배열 이국 객체로 만들고, 자기 자신은 자기 사슬에 없다.
- ★★ **`[object Arguments]`** · **`[object Uint8Array]`** — 둘 다 `Array.isArray` `false`.
- ★ **`'ab'` 하나**(`string`). 나머지 여섯은 전부 `"object"`.

### 6. `OrdinaryHasInstance` 는 사슬의 객체를 **이 realm 의 `C.prototype` 과 `SameValue`** 로 견준다 — 다른 realm 의 사슬에는 그쪽 것이 있다 ★★★

- ★★★ 사슬을 따라 올라가며 각 객체를 **`C.prototype`(= 이쪽 realm 의 객체)** 과 `SameValue` 로 견준다.
- ★★ **그쪽 realm 의 `Array.prototype`** 이 있다 — 이름은 같아도 **다른 객체**다.
- ★★ **「메서드가 있나」를 본다** — 객체의 정체가 아니다. 그쪽 `Array.prototype` 에도 `push` 가 있으므로 다른 realm 에서 안 틀렸다. 대신 사슬을 바꾸면 행동도 같이 바뀐다(`proto swapped` · `Object.create`).

### 7. `builtinTag` 목록에 **`Promise` 가 없어서** 명찰이 **사슬 위의 자칭**뿐이다 ★★

- ★★★ 목록 — **`Array`·`Arguments`·`Function`·`Error`·`Boolean`·`Number`·`String`·`Date`·`RegExp`**, 그 밖은 `Object`. **`Promise`·`Map`·`Set` 이 없다.**
- ★★ `Promise.prototype[Symbol.toStringTag]` 에서 온다. **프로토타입을 바꾸면 명찰이 사라지고**(`n*`), **`Object.create(Promise.prototype)` 은 명찰을 얻는다**(`y*`).
- ★ **그렇다** — 3번의 `Promise` 행 태그 칸이 `y` 인 것은, 프록시의 `Get(Symbol.toStringTag)` 가 대상의 사슬로 가서 `"Promise"` 를 읽기 때문이다.

### 8. 배열 **`Array.isArray`** · 오류 **`Error.isError`** · `Date` **메서드 `call`** · 내 클래스 **`#brand in`** — `instanceof` 는 **한 realm 의 계층** ★★★

- ★★★ 요약 2-summary 「문법 — 형태와 규칙」의 판정 선택표 그대로다.
- ★★ `instanceof` — 「**이 realm 에서 이 클래스 계층에 속하나**」(메서드 오버라이드로 분기할 때).
- ★★ 덕 타이핑 — 「**이 동작을 할 수 있나**」. 언어 자신은 **thenable**(`await`·`Promise.resolve`)과 **이터러블**(`for...of`)에서 쓴다.

### 9. realm 의 동일성은 **확인하지 않았다** — 관찰은 **판정 다섯에 대한 두 창의 결과가 같았다**는 것 · 오류 열은 **호스트 함수** ★★

- ★★ **확인하지 않았다.** 관찰한 것은 **사슬의 객체가 다르고(`instanceof` `n*`) 슬롯은 넘는다(`y`)** 는 것이 `vm` 과 iframe 에서 같았다는 것이다.
- ★★ **`util.types.isNativeError`** — node 의 호스트 API 다. `Error.isError`(ES2026)가 두 node 판에 없어 **창을 바꿔 물었다.**
- ★ `Proxy` — 목록의 **45번 주제**. 워커·`structuredClone` 으로 건너온 값 — 목록의 **48번 주제**(복제).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js32b-34-h-realm-core.js` + `js32b-34a-realm-grid.js` | ★★★ realm 격자 · 「`32 / 100`」 · 방법별 · 조건별 · 프록시 행 | node20 1벌 + node18 대조 1벌 |
| `js32b-34-h-realm-core.js` + `js32b-34b-realm-grid.web.js` | ★★★ 같은 격자를 iframe realm 과 `Error.isError` 로 | **Chrome 151 만** |
| `js32b-34c-array-edges.js` | ★★ `Array.prototype` · `arguments` · 형식화 배열 | node20 1벌 + node18 대조 1벌 |
| (인용) 01 · 15 · 16 · 17 · 22 편의 블록 | 1번의 조각들 | 그 편의 「실행 검증」 |
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

- ★★ **`Error.isError`** — node 가 ES2026 을 받으면 node 판의 오류 슬롯 열을 `Error.isError` 로 바꿔 다시 돌린다(지금은 호스트 함수).
- ★ **다른 realm 을 만드는 호스트 API** — `vm`·iframe 의 동작이 바뀌면 격자를 다시 돌린다.
