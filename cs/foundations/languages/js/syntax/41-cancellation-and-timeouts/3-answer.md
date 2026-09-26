# js/syntax/41 — 취소와 타임아웃: 「신호를 안 보는 작업은 끝까지 돈다 · 이유는 `AbortError`/`TimeoutError`/준 값 · 나무는 아래로만 · 서버는 이미 받았다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **판이 갈린 자리** — `message` 문구(node 대 Chrome) · node 18 `fetch` 의 `abort("mine")`(4번). 그 밖의 줄 순서·종류·숫자는 세 판이 같았다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(Chrome 의 `fetch` 소스는 [2-summary.md](2-summary.md) 동작 (4)).
> `js40b-41a-abort-mid-job.js`(1번 · 5번) · `js40b-41b-reasons.js`(2번 · 6번 · 10번) · `js40b-41c-signal-tree.js`(3번 · 8번) · `js40b-41-h-fetch.js` + `js40b-41-h-timeout-alone.js` + `js40b-41d-node-fetch.sh`(4번 · 7번 · 9번) · `js40b-41e-fetch.web.js`(4번).

## 정답

### 1. `[1]` 은 **`job step 3 … job returns` 까지 가고 `fulfilled "job result"`** · `[2]` 는 **`step 3` 없이 `rejected AbortError`** · `[3]` 은 **호출자가 먼저 `rejected AbortError` 를 받고 그 뒤에 `job step 3 … job returns`** ★★★

**출력**

```text
===== node20 js40b-41a-abort-mid-job.js (exit=0) =====
[0] Promise.prototype: then, catch, finally · 'cancel' in it: false
[1] job ignores the signal
  job step 1 > job step 2 > -- abort() called > job step 3 > job step 4 > job step 5 > job returns > caller got fulfilled "job result"
[2] job checks signal.throwIfAborted()
  job step 1 > job step 2 > -- abort() called > caller got rejected DOMException AbortError 「This operation was aborted」
[3] caller's wrapper rejects on abort, job ignores the signal
  job step 1 > job step 2 > -- abort() called > caller got rejected DOMException AbortError 「This operation was aborted」 > job step 3 > job step 4 > job step 5 > job returns
```

**왜 그런가**

- ★★★ `abort()` 는 **신호의 상태(`aborted`·`reason`)를 바꾸고 리스너를 부를 뿐**이다. 작업이 그것을 **보지 않으면**(`[1]`) 아무 일도 없다.
- ★★★ `[3]` 의 감싸개는 `abort` 이벤트에서 **자기 프라미스를 거부**했다 — 호출자는 떠났지만, 안쪽 `job(...)` 의 프라미스와 그 작업은 **그대로 살아** 끝까지 갔다. 프라미스를 거부하는 것은 **작업을 멈추는 것이 아니다.**
- ★★ `[0]` — `then, catch, finally · 'cancel' in it: false`.
- ★ Chrome 151 은 문구만 `signal is aborted without reason` 로 달랐다.

### 2. 인자 없음·`undefined`·`AbortSignal.abort()` 는 **`DOMException · AbortError · 20`** · `timeout` 은 **`TimeoutError · 23`** · 값은 **그대로**(`Error` 는 같은 객체) · 두 번째 `abort` 는 **무시** · `any` 는 **같은 `reason`** · `throwIfAborted` 는 **`reason` 을 던진다** · `[4]` 는 **`1` · `0` · `0`** ★★★

**출력**

```text
===== node20 js40b-41b-reasons.js (exit=0) =====
[1] signal.reason
  controller.abort()                      DOMException · AbortError · 「This operation was aborted」 · 20 · true
  controller.abort(undefined)             DOMException · AbortError · 「This operation was aborted」 · 20 · true
  controller.abort("stop")                string · "stop"
  controller.abort(new Error("mine"))     Error · Error · 「mine」 · - · true
    same object as the Error passed in    true
  AbortSignal.abort()                     DOMException · AbortError · 「This operation was aborted」 · 20 · true
  AbortSignal.timeout(0), after abort     DOMException · TimeoutError · 「The operation was aborted due to timeout」 · 23 · true
[2] a second abort(), and AbortSignal.any
  abort("first") then abort("second")     string · "first"
  any([src, other]) after src.abort(e)    aborted true · reason === e true
[3] throwIfAborted()
  on an aborted signal, threw             "why" · same as reason true
  on a live signal, returned              undefined
[4] addEventListener with { signal } on a plain EventTarget -- calls after dispatching once
  live signal                             1
  after that signal's abort()             0
  registered with an aborted signal       0
```

**왜 그런가**

- ★★★ DOM 표준의 signal abort — 「**이미 abort 됐으면 돌아간다** · reason 이 주어지면 그것, **아니면 새 `AbortError` `DOMException`**」. `timeout` 은 **새 `TimeoutError`** 로 abort 한다.
- ★★ `any` 가 만든 의존 신호에는 **원본의 abort reason 을 그대로** 넣는다(`reason === e true`). `throwIfAborted` 는 「**이것의 abort reason 을 던진다**」 — 그래서 `"why"` 문자열이 그대로 던져졌다.
- ★ `message` 는 표준 밖이다 — node 는 `This operation was aborted`, Chrome 151 은 `signal is aborted without reason`(요약 동작 (2)).

### 3. `root` → **`aborted 7 / 7`** · `a` → **`2 / 7`** · `a1` → **`1 / 7`** — 셋 다 **`… same object true`** ★★

**출력**

```text
===== node20 js40b-41c-signal-tree.js (exit=0) =====
abort root root=true a=true a1=true b=true b1=true c=true c1=true   aborted 7 / 7 · every aborted reason is the same object true
abort a    root=false a=true a1=true b=false b1=false c=false c1=false   aborted 2 / 7 · every aborted reason is the same object true
abort a1   root=false a=false a1=true b=false b1=false c=false c1=false   aborted 1 / 7 · every aborted reason is the same object true
```

**왜 그런가**

- ★★ 노드의 신호는 `any([부모, 내 것])` 이라 **부모가 끊기면 따라 끊기고**, 내 것을 끊어도 **부모는 그대로**다(`root=false`). 번짐은 **아래로만**이다.
- ★ 모든 노드가 원본의 `reason` 을 **같은 객체**로 받았다.

### 4. node 20 — `AbortError`(서버 **받음 1** · 연결 끊김) · **`"mine"` 그대로** · `AbortError`(서버 **0**) · **`TimeoutError`** — node 18 은 **`abort-in-flight-reason` 에서 `TypeError 「invalid_argument」`**(`differ 1 / 4`) · `alone` **한 줄**, `keep` **두 줄** ★★★

**출력**

```text
===== ./js40b-41d-node-fetch.sh (exit=0) =====
--- abort-in-flight
  node20  fetch rejected DOMException AbortError 「This operation was aborted」 · === signal.reason true
  node20  server: requests received 1 · saw the connection close yes
  node20  (exit 0)
  node18  the same
--- abort-in-flight-reason
  node20  fetch rejected "mine" · === signal.reason true
  node20  server: requests received 1 · saw the connection close yes
  node20  (exit 0)
  node18  fetch rejected TypeError TypeError 「invalid_argument」 · === signal.reason false
  node18  server: requests received 1 · saw the connection close yes
  node18  (exit 0)
--- already-aborted
  node20  fetch rejected DOMException AbortError 「This operation was aborted」 · === signal.reason true
  node20  server: requests received 0 · saw the connection close -
  node20  (exit 0)
  node18  the same
--- timeout-50ms
  node20  fetch rejected DOMException TimeoutError 「The operation was aborted due to timeout」 · === signal.reason true
  node20  server: - (this row does not report the server side)
  node20  (exit 0)
  node18  the same

rows where node18 and node20 differ: 1 / 4

--- node20 js40b-41-h-timeout-alone.js alone
end of the script
(exit 0)
--- node20 js40b-41-h-timeout-alone.js keep
end of the script
abort event: TimeoutError
(exit 0)
--- node18 js40b-41-h-timeout-alone.js alone
end of the script
(exit 0)
--- node18 js40b-41-h-timeout-alone.js keep
end of the script
abort event: TimeoutError
(exit 0)
```

Chrome 151 — 같은 세 행(시간 초과 행은 이 하네스에서 근거가 못 되어 뺐다).

```text
===== ./js40b-browser.sh --http js40b-41e-fetch.web.js (exit=0) =====
abort-in-flight         fetch rejected DOMException AbortError 「signal is aborted without reason」 · === signal.reason true
abort-in-flight-reason  fetch rejected "mine" · === signal.reason true
already-aborted         fetch rejected DOMException AbortError 「signal is aborted without reason」 · === signal.reason true
```

**왜 그런가**

- ★★★ fetch 표준은 요청을 **신호의 abort reason 으로** 끝낸다 — node 20 과 Chrome 151 이 `=== signal.reason true` 로 그랬다. **node 18 은 문자열 이유를 자기 `TypeError` 로 바꿨다**(`=== signal.reason false`) — 판의 결함이다.
- ★★★ `abort-in-flight` 에서 서버는 **이미 요청을 받았고**(`1`), 본 것은 **연결이 닫힌 것**뿐이다. `already-aborted` 는 **보내지도 않았다**(`0`).
- ★★ `alone` 은 `end of the script` 한 줄 · `exit 0` — **`timeout` 의 타이머가 프로세스를 붙잡지 않았다.** `keep` 은 다른 타이머가 살아 있어 `abort event: TimeoutError` 까지 두 줄.

### 5. 프라미스는 **`then`·`catch`·`finally` 뿐** — 「결과를 기다리는 창구」라 **거꾸로 작업을 멈출 길이 없다** · 멈춘 것은 **작업 자신**(`throwIfAborted`) ★★★

- ★★★ 그래서 `abort()` 가 할 수 있는 일은 **신호를 바꾸는 것**까지이고, 멈출지는 신호를 받은 코드가 정한다(1번 `[1]` 대 `[2]`).
- ★★ DOM 표준은 `throwIfAborted` 를 「신호를 받는 함수가 **정해진 확인 지점에서** 던지고 싶을 때 — 실제 비동기 작업(`await func()`)이 신호를 받지 않더라도」 쓰라고 설명한다. 1번 `[2]` 가 그 모양이다.

### 6. **`e.name`**(`AbortError`/`TimeoutError`) 또는 **`e === signal.reason`** — `message` 는 **판마다 달라** 안 된다 · `abort("stop")` 이면 `e` 는 **문자열이라 `name` 이 `undefined`** ★★

- ★★ 2번 — `name` 과 `code` 는 세 판이 같았고 `message` 는 node 와 Chrome 이 달랐다. 준 이유는 **아무 값**이나 될 수 있으니 `e === signal.reason`(또는 `signal.aborted`)이 가장 넓다.
- ★ `"stop"` 은 `string · "stop"` 이었다 — 문자열에는 `name` 속성이 없다.

### 7. 프라미스의 취소 부재는 **ECMA-262**, `AbortController`·`DOMException` 은 **DOM 표준**, `fetch` 는 **fetch 표준**, 그리고 **node 가 그것들을 구현**한다 — `alone`/`keep` 의 차이는 **node 의 성질**이다 ★★

- ★★ ECMA-262 에는 `AbortController` 가 없다. node 는 같은 이름의 API 를 준다(v20 문서의 「Added in」).
- ★★ DOM 표준은 `timeout` 에 대해 「abort 리스너가 있는 동안 **전역이 신호를 강하게 참조해야 한다**」고만 적는다 — 프로세스를 살려 두라는 문장은 없다. 살려 두지 않는 것은 **node 가 고른 것**이다(두 판 관찰).

### 8. **같다** — `7 / 7` · `2 / 7` · 다른 자리는 **정리 호출**(Go 는 `cancel` 을 안 부르면 샌다 — `vet lostcancel`, JS 의 `any` 에는 정리 호출이 없다) · 같은 자리는 **협조적**이다 ★★

- ★★ Go 34번 (1)절이 `Done 을 받은 노드 7 / 7` · `2 / 7` 을 찍었고, 3번이 같은 나무에서 같은 수를 찍었다.
- ★ 둘 다 신호를 받는 쪽이 **스스로 확인해야** 멈춘다 — Go 31번 (3)절이 `ctx` 를 보게 고쳐 누수를 막았고, 1번 `[2]` 가 JS 의 같은 모양이다.

### 9. **「2. 고아 작업 — 클라이언트가 끊어도 서버는 모른다」** — 경계는 **설계(무엇을 어디까지 넘기나)는 그쪽, JS API 의 동작은 여기** ★★

- ★★ `requests received 1 · saw the connection close yes` — 서버는 요청을 받았고, 끊긴 뒤에도 **이미 한 일은 되돌려지지 않는다.** 그 문서의 「3-2. 작업 스레드」 절도 「**취소는 협조적이다**」라고 적는다.

### 10. **같다** — `1` · `0` · `0` · 재사용하면 **이미 abort 된 신호라 리스너가 조용히 안 붙는다** ★

- ★ web-api 20번이 Chrome 에서 「이미 abort 된 signal 로 등록하면 **예외도 반환값도 없고 던져도 0회**」를 쟀다. node 의 `EventTarget` 도 `registered with an aborted signal  0` 이었다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js40b-41a-abort-mid-job.js` | ★★★ `abort()` 뒤에도 도는 작업 · 확인하는 작업 · 감싸개 | node20 1벌 + node18 대조 + Chrome 1벌(블록) |
| `js40b-41b-reasons.js` | ★★★ `reason` 7행 · 두 번째 `abort` · `any` · `throwIfAborted` · 리스너 | node20 1벌 + node18 대조 + Chrome 1벌(블록) |
| `js40b-41c-signal-tree.js` | ★★ `7 / 7` · `2 / 7` · `1 / 7` | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js40b-41-h-fetch.js` + `js40b-41-h-timeout-alone.js` + `js40b-41d-node-fetch.sh` | ★★★ `fetch` 4행 · 「`differ 1 / 4`」 · 타이머가 프로세스를 붙잡나 | node20 · node18 각 행 1벌 |
| `js40b-41e-fetch.web.js` | ★★ Chrome 의 `fetch` 3행 | Chrome 151 1벌(로컬 서버) |

세 판 대조기(이 묶음 전체의 plain 탐침). 이 주제의 줄은 `41a`·`41b`(Chrome `DIFFERS` — 문구) · `41c` 셋이다.

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

- ★★★ **node 18 의 `abort("mine")` → `TypeError 「invalid_argument」`** — node 20 에서 사라졌다. 판이 오르면 4번을 다시 돌린다.
- ★★ **`timeout` 이 프로세스를 붙잡지 않는 것** — node 의 성질이다.
- ★ 문구 — `This operation was aborted` · `The operation was aborted due to timeout`(node) / `signal is aborted without reason` · `signal timed out`(Chrome 151).
