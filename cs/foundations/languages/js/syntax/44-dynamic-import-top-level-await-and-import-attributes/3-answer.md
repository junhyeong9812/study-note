# js/syntax/44 — 동적 `import`·최상위 `await`·import attributes: 「`import()` 는 그 줄에서 · 최상위 `await` 는 가져오는 쪽만 세우고 · `with` 는 node 18 이, `assert` 는 Chrome 이 막는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151**(로컬 HTTP 서버) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **평가 순서(1\~3번)는 세 판이 한 글자도 같았고, import attributes(4번)는 세 판이 `8 / 12` 행에서 갈렸다.**
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(격자를 세 판에 돌리는 `.sh` 와 Chrome 쪽 스크립트는 [2-summary.md](2-summary.md) 동작 (4), 끝내 안 풀리는 `await` 를 돌리는 `.sh` 는 동작 (2)).
> `js44b-44a/`(1번 · 10번) · `js44b-44b/`(2번 · 5번 · 6번) · `js44b-44c/`(3번 · 9번) · `js44b-44d-attributes-grid.js` + `.web.js` + `.sh`(4번 · 7번 · 8번).

## 정답

### 1. `stat44a` 본문 → `first line` → `p1 === p2 false` → `dyn44a` 본문(**한 번**) → 두 이름공간 `true` → 정적 이름공간과도 `true` → `last line` ★★★

**출력**

```text
===== cd js44b-44a && node20 main44a.mjs (exit=0) =====
stat44a.mjs: body runs
main44a.mjs: first line
main44a.mjs: two import() calls made · p1 === p2 false
dyn44a.mjs: body runs
namespace from p1 === namespace from p2 true · v = dyn
import('./stat44a.mjs') === the static namespace true
main44a.mjs: last line
```

**왜 그런가**

- ★★★ 정적 `import` 는 **연결 정보**라 상대가 본문 **전에** 평가되고(42번 동작 (4)), `import()` 는 **식**이라 그 줄을 평가한 뒤 적재가 시작된다 — 첫 `await` 에서 쉬는 동안 `dyn44a` 가 돈다.
- ★★ `import()` 는 부를 때마다 **새 `Promise`** 를 만들지만 모듈 레코드는 지정자마다 **하나**다 — 본문 한 번, 이름공간 `===`. 정적으로 이미 가져온 모듈도 같은 레코드다.

### 2. `tla(before)` → **`plain`** → `tla(after)` → `dep` → `main` — `plain44b` 는 **안 기다리고**, `dep44b` 는 **기다린다** ★★★

**출력**

```text
===== cd js44b-44b && node20 main44b.mjs (exit=0) =====
tla44b.mjs: before await
plain44b.mjs: body
tla44b.mjs: after await
dep44b.mjs: body · s = tla
main44b.mjs: body
```

**왜 그런가**

- ★★★ 최상위 `await` 는 **그 모듈의 평가를 비동기로** 만든다. 그 모듈을 **가져오는** 모듈(`dep44b`·`main44b`)만 「아직 안 끝난 비동기 의존」을 세며 멈추고, 서로 가져오지 않는 형제(`plain44b`)는 평소처럼 **동기로** 돈다(6번).
- ★ Chrome 151 도 같았다(2-summary 동작 (2)).

### 3. `[1]` **`SyntaxError 「Unexpected token ';'」`**(본문 0 줄) · `throws44c.mjs: body runs` · `[2]` `RangeError` · `[3]` 같은 문구에 **`same error object true`** · `[4]` **`1 time(s)`** ★★

**출력**

```text
===== cd js44b-44c && node20 main44c.mjs (exit=0) =====
[1] import('./broken44c.mjs') rejected: SyntaxError 「Unexpected token ';'」
throws44c.mjs: body runs
[2] import('./throws44c.mjs') rejected: RangeError 「thrown while evaluating」
[3] again: RangeError 「thrown while evaluating」 · same error object true
[4] throws44c.mjs body ran 1 time(s)
```

**왜 그런가**

- ★★ 파싱은 본문보다 먼저라 `broken44c.mjs` 의 첫 줄도 안 돈다. 평가 중에 던진 모듈은 레코드에 **그 예외를 남기고**, 다음 요청에 **그것을 그대로** 돌려준다(9번).

### 4. node 20 **막힌 행 `7 / 12`** · node 18 **`10 / 12`** · Chrome **`9 / 12`** · 세 판이 다 같지는 않은 행 **`8 / 12`** — **세 판 다 통과한 행은 없다** ★★★

**출력**

```text
===== ./js44b-44d-attributes.sh (exit=0) =====
--- node20
  1  static  with { type: 'json' }                  ok {"k":1}
  2  static  assert { type: 'json' }                ok {"k":1} + warning
  3  static  no attributes                          blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
  4  static  with { type: 'css' }                   blocked TypeError ERR_IMPORT_ASSERTION_TYPE_UNSUPPORTED
  5  static  with { type: 'json', mode: 'x' }       blocked TypeError ERR_IMPORT_ATTRIBUTE_UNSUPPORTED
  6  static  import { k } ... with { type: 'json' } blocked SyntaxError 「The requested module './data.json' does not provide an export named 'k'」
  7  static  code.mjs with { type: 'json' }         blocked TypeError ERR_IMPORT_ASSERTION_TYPE_FAILED
  8  import(..., { with: { type: 'json' } })        ok {"k":1}
  9  import(..., { assert: { type: 'json' } })      ok {"k":1} + warning
 10  import(...) with no options                    blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
 11  static  with { type: 'json', type: 'json' }    blocked SyntaxError 「Import assertion has duplicate key 'type'」
 12  static and import() of the same JSON           ok same object true
  row 2: V8: <dir>/main.mjs:1 'assert' is deprecated in import statements and support will be removed in a future version; use 'with' instead
  row 9: V8: <dir>/main.mjs:1 'assert' is deprecated in import statements and support will be removed in a future version; use 'with' instead
--- node18
  1  static  with { type: 'json' }                  blocked SyntaxError 「Unexpected token 'with'」
  2  static  assert { type: 'json' }                ok {"k":1} + warning
  3  static  no attributes                          blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
  4  static  with { type: 'css' }                   blocked SyntaxError 「Unexpected token 'with'」
  5  static  with { type: 'json', mode: 'x' }       blocked SyntaxError 「Unexpected token 'with'」
  6  static  import { k } ... with { type: 'json' } blocked SyntaxError 「Unexpected token 'with'」
  7  static  code.mjs with { type: 'json' }         blocked SyntaxError 「Unexpected token 'with'」
  8  import(..., { with: { type: 'json' } })        blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
  9  import(..., { assert: { type: 'json' } })      ok {"k":1} + warning
 10  import(...) with no options                    blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
 11  static  with { type: 'json', type: 'json' }    blocked SyntaxError 「Unexpected token 'with'」
 12  static and import() of the same JSON           blocked SyntaxError 「Unexpected token 'with'」
  row 2: ExperimentalWarning: Importing JSON modules is an experimental feature and might change at any time
  row 9: ExperimentalWarning: Importing JSON modules is an experimental feature and might change at any time
--- Chrome 151
  1  static  with { type: 'json' }                  ok {"k":1}
  2  static  assert { type: 'json' }                blocked SyntaxError 「Unexpected identifier 'assert'」
  3  static  no attributes                          blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/3/main.mjs」
  4  static  with { type: 'css' }                   blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/4/main.mjs」
  5  static  with { type: 'json', mode: 'x' }       blocked SyntaxError 「Invalid attribute key "mode".」
  6  static  import { k } ... with { type: 'json' } blocked SyntaxError 「The requested module './data.json' does not provide an export named 'k'」
  7  static  code.mjs with { type: 'json' }         blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/7/main.mjs」
  8  import(..., { with: { type: 'json' } })        ok {"k":1}
  9  import(..., { assert: { type: 'json' } })      blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/9/data.json」
 10  import(...) with no options                    blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/10/data.json」
 11  static  with { type: 'json', type: 'json' }    blocked SyntaxError 「Import attribute has duplicate key 'type'」
 12  static and import() of the same JSON           ok same object true

blocked rows: node20 7 / 12 · node18 10 / 12 · Chrome 9 / 12
rows where node18 and node20 differ: 6 / 12
rows where node20 and Chrome differ: 3 / 12
rows where the three do not all agree: 8 / 12
```

**왜 그런가**

- ★★★ **`with` 는 ES2025 문법**이라 node 18.19.1(V8 10.2)의 파서가 모른다 — 그 파일의 모든 `with` 행이 `SyntaxError 「Unexpected token 'with'」`. node 문서 이력상 전환은 **v18.20.0** 이다.
- ★★★ **`assert` 는 표준이 아니다** — node 두 판은 옛 제안을 남겨 두어 받았고(경고), Chrome 151 은 `SyntaxError 「Unexpected identifier 'assert'」`. 동적 쪽도 **읽는 키가 판마다 달라** 같은 방향으로 갈렸다(node 18 은 `with` 를, Chrome 은 `assert` 를 못 읽는다).
- ★★ 속성 없음(행 3·10)은 세 판 다 막았다 — **호스트의 선택**(7번). 이름 있는 가져오기(행 6)는 JSON 모듈의 내보내기가 `default` 하나라 막힌다. 키 중복(행 11)은 명세의 조기 오류다.

### 5. `pending44b.mjs: before await` **한 줄**, **`exit 13`**, 표준 오류 **0 줄** — `importer44b.mjs: body` 는 안 찍힌다 ★★

```text
===== ./js44b-44b-pending.sh (exit=0) =====
--- node20 importer44b.mjs
pending44b.mjs: before await
(exit 13 · standard error: 0 lines)
--- node18 importer44b.mjs
pending44b.mjs: before await
(exit 13 · standard error: 0 lines)
```

Chrome 151 — 같은 파일을 로컬 서버로(페이지에는 종료 코드가 없다).

```text
===== ./js44b-browser.sh --http js44b-44b/importer44b.mjs (exit=0) =====
pending44b.mjs: before await
```

- ★★ 풀릴 수 없는 프라미스를 기다리는 동안 **할 일이 없어진** node 는 코드 13 으로 끝난다(node 문서). 경고가 없으니 **종료 코드가 유일한 신호**다.

### 6. **가져오는 화살표**가 갈랐다 — `dep44b` 는 `tla44b` 를 `import` 하고 `plain44b` 는 안 한다 · 명세는 모듈마다 **`[[PendingAsyncDependencies]]`**(아직 안 끝난 비동기 의존의 수)를 센다 ★★★

- ★★★ 그 수가 0 이 되어야 `ExecuteAsyncModule` 로 돈다. 비동기 모듈이 끝나면 `GatherAvailableAncestors` 가 **자기를 가져온 쪽**만 모아 차례로 풀어 준다 — 형제는 애초에 그 목록에 없다.
- ★ 그래서 「초기화가 끝난 뒤에 돌아야 하는 모듈」은 그 초기화 모듈을 **직접 가져와야** 한다.

### 7. **명세는 요구하지 않는다** — note 가 「`type: "json"` 없이 JSON 모듈을 지원하는 것을 금하지 않는다」고 적는다 · 막은 것은 **호스트** · 모르는 키는 명세상 **`SyntaxError`** — Chrome 이 그 모양이고 node 20 은 `TypeError ERR_IMPORT_ATTRIBUTE_UNSUPPORTED` ★★★

- ★★★ 명세가 **`type: "json"` 이면 JSON 으로 해석하라**는 것만 못 박고, 나머지(속성 없는 JSON · 어느 키를 받나)는 `HostLoadImportedModule`·`HostGetSupportedImportAttributes` 로 호스트에 맡겼다. 이 머신의 세 판은 **셋 다 명시를 요구하는 쪽**이었다(행 3·10). 왜 그쪽을 골랐는지는 이 문서가 확인하지 않았다.
- ★★ `AllImportAttributesSupported` 가 거짓이면 「a newly created **SyntaxError** object」 — node 20 은 다른 이름으로 막았다.

### 8. `with` 문법 · 형제를 안 기다리는 평가 순서 — **ECMA-262** · `type` 만 받는 것 · 속성 없는 JSON 거절 · 종료 코드 13 — **호스트** · `assert` — **어느 표준에도 없다**(엔진이 남겨 둔 옛 제안) ★★

- ★★ 평가 순서가 **세 판 한 글자도 같았던 것**(1\~3번)과 attributes 가 **8 / 12 행 갈린 것**(4번)이 그 층의 차이다.

### 9. **안 돈다** — 레코드가 **`evaluated` 상태 + `[[EvaluationError]]`** 를 들고 있어, 다음 평가 요청에 그 예외를 **그대로** 돌려준다(`same error object true` · `1 time(s)`) ★★

- ★ 다시 시도하려면 **다른 지정자**(쿼리 문자열을 붙인 URL 등)로 새 모듈 레코드를 만들어야 한다 — 이 문서는 그것을 **돌리지 않았다.**

### 10. 42번 — **`import()` 는 `Promise` 를 돌려주는 식** · **두 번 불러도 같은 이름공간**(그리고 없는 파일의 거부 모양이 호스트마다 다른 것) · 이 주제는 **부르는 순간 · 정적과 섞어도 같은 레코드 · 최상위 `await` 의 순서 · 실패 · 속성**으로 넓혔다 · 43번 — node 18 **`ERR_REQUIRE_ESM`**, node 20 **`ERR_REQUIRE_ASYNC_MODULE`** ★★

- ★ 43번의 두 번째 칸은 「막혔지만 **이유가 바뀐**」 행이었다 — 최상위 `await` 가 든 모듈은 동기로 끝낼 수 없어 node 20 의 `require(esm)` 로도 못 가져온다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js44b-44a/*` | ★★★ 정적 대 동적의 본문 순서 · 두 번의 `import()` · 정적과 같은 레코드 | node20 1벌 + node18 대조(같음) + Chrome 151 1벌(같음) |
| `js44b-44b/*` + `js44b-44b-pending.sh` | ★★★ 최상위 `await` 와 형제 · 끝내 안 풀리면 `exit 13` | node20 · node18 · Chrome 151 각 1벌 |
| `js44b-44c/*` | ★★ 파싱 실패 · 평가 실패 · 같은 에러 객체 | node20 1벌 + node18 대조(같음) + Chrome 151 1벌(같음) |
| `js44b-44d-attributes-grid.js` + `.web.js` + `.sh` | ★★★ 12행 × 세 판 · 「`7 / 12`·`10 / 12`·`9 / 12`」 · 「`8 / 12`」 | 행마다 새 디렉토리 · node 는 새 프로세스 |

세 판 대조기(이 묶음의 plain 탐침). 이 주제의 줄은 `44d` 하나이고 **`DIFFERS`**(node 판 차이 — 4번) · Chrome 은 `.web.js` 로 따로 돌렸다.

```sh
# js44b-vdiff.sh
#!/usr/bin/env bash
# Every plain probe of 44-46 and js44b-47d (js44b-4NX-*.js, not *.web.js), run on node18, node20 and Chrome 151.
# The other 47 probes need a gc() flag or print counts that move between runs -- js44b-47a-observe.sh compares those.
# A probe that uses a node-only API (process.* or require) is compared between the two node versions only.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
s18=0; d18=0; sw=0; dw=0; skip=0
for f in js44b-4[456]?-*.js js44b-47d-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"; b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then r18=identical; s18=$((s18 + 1)); else r18=DIFFERS; d18=$((d18 + 1)); fi
  if grep -q 'process\.\|require(' "$f"; then rw="(node only)"; skip=$((skip + 1))
  else
    w="$(./js44b-browser.sh "$f")"
    if [ "$w" = "$b" ]; then rw=identical; sw=$((sw + 1)); else rw=DIFFERS; dw=$((dw + 1)); fi
  fi
  printf '%-40s node18/node20 %-10s node20/Chrome %s\n' "$f" "$r18" "$rw"
done
echo ""
echo "node18 vs node20: identical $s18 · differs $d18   ·   node20 vs Chrome 151: identical $sw · differs $dw · node only $skip"
```

```text
===== ./js44b-vdiff.sh (exit=0) =====
js44b-44d-attributes-grid.js             node18/node20 DIFFERS    node20/Chrome (node only)
js44b-45a-invariant-grid.js              node18/node20 identical  node20/Chrome identical
js44b-45c-falsish.js                     node18/node20 identical  node20/Chrome identical
js44b-45d-internal-slots.js              node18/node20 identical  node20/Chrome identical
js44b-45e-what-a-proxy-looks-like.js     node18/node20 identical  node20/Chrome identical
js44b-46a-reflect-and-traps.js           node18/node20 identical  node20/Chrome identical
js44b-46b-object-vs-reflect.js           node18/node20 identical  node20/Chrome identical
js44b-46c-receiver.js                    node18/node20 identical  node20/Chrome identical
js44b-47d-registry-api.js                node18/node20 DIFFERS    node20/Chrome identical

node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 8 · differs 0 · node only 1
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **import attributes 격자 전부** — node 18.20+ · node 22 · Chrome 의 다음 판에서 `with`/`assert` 칸이 바뀐다(node 20 경고가 「future version」에서 `assert` 를 없앤다고 적는다).
- ★★ node 의 에러 **코드 이름**(`ERR_IMPORT_ASSERTION_…`) · 키 중복 문구의 `assertion`/`attribute`.
- ★ 끝내 안 풀린 최상위 `await` 의 **경고 유무**(이 두 판은 0 줄).
