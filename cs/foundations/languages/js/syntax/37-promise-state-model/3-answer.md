# js/syntax/37 — Promise 상태 모델: 「처음 것만 · thenable 은 잡으로 · `.finally()` 는 통과 · 보고는 호스트」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical` · 5번의 `0 / 6`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js36b-37a-transitions.js`(1번 · 7번) · `js36b-37b-ticks.js`(2번 · 8번) · `js36b-37c-chain.js`(3번 · 4번 · 9번) ·
> `js36b-37-h-late-catch.js` + `js36b-37d-unhandled-node.sh` · `js36b-37e-unhandled-stderr.sh`(5번 · 10번) · `js36b-37f-unhandled.web.js`(6번 · 11번).

## 정답

### 1. 첫 호출이 전부 이긴다(`0 / 5`) — `resolve(p)` 직후는 **`pending`**, 나중에 **`fulfilled "c"`** ★★★

**출력**

```text
===== node20 js36b-37a-transitions.js (exit=0) =====
[before p settles]
  resolve(p pending) · reject('b')                pending
[after everything settled]
  resolve('a') · resolve('b')                     fulfilled "a"
  resolve('a') · reject('b')                      fulfilled "a"
  reject('a') · resolve('b')                      rejected  "a"
  throw Error('a')                                rejected  Error 「a」
  resolve('a') · throw Error('b')                 fulfilled "a"
  resolve(p pending) · reject('b')                fulfilled "c"
  resolve(Promise.reject('r'))                    rejected  "r"
  resolve(thenable: onF('t'))                     fulfilled "t"
  resolve(thenable: onF('t') · onR('u') · throw)  fulfilled "t"
  resolve(object whose then getter throws)        rejected  Error 「g」
  resolve(the promise itself)                     rejected  TypeError 「Chaining cycle detected for promise #<Promise>」
rows with a plain first call where a later call decided the state: 0 / 5
```

**왜 그런가**

- ★★★ **`resolve('a')` 로 시작한 세 행은 전부 `fulfilled "a"`**, `reject('a')` 는 `rejected "a"`, executor 의 `throw` 는 `rejected Error 「a」`. 뒤의 `resolve`·`reject`·`throw` 는 **에러 없이** 버려진다.
- ★★★ **`resolve(p pending)` 직후는 `pending`** 인데 `reject('b')` 는 이미 무시된다 — `p` 가 `"c"` 로 이행하자 `fulfilled "c"`.
- ★★ thenable 은 **처음 부른 `onF('t')`** 로 정해지고, `then` 게터가 던지면 **그 예외로 거부**, 자기 자신이면 **`TypeError`**.

### 2. `@0` · `@2` · `@1` — thenable 은 **`get then` 이 동기, `then()` 호출은 잡 안** ★★★

**출력**

```text
===== node20 js36b-37b-ticks.js (exit=0) =====
[1] new Promise((resolve) => resolve(X))
  X = 'v'                                     sync code done @0 > then callback @0
  X = Promise.resolve('v')                    sync code done @0 > then callback @2
  X = thenable (then calls onF at once)       get then > sync code done @0 > then() called > then callback @1
[2] Promise.resolve(X)
  Promise.resolve(q) === q        true
  Promise.resolve(Promise.resolve('v'))       sync code done @0 > then callback @0
  Promise.resolve(thenable)                   get then > sync code done @0 > then() called > then callback @1
[3] a then callback returns X -- ticks counted from the start
  then(() => 'v')                             sync code done @0 > then callback @1
  then(() => Promise.resolve('v'))            sync code done @0 > then callback @3
```

```text
===== ./js36b-browser.sh js36b-37b-ticks.js (exit=0) =====
[1] new Promise((resolve) => resolve(X))
  X = 'v'                                     sync code done @0 > then callback @0
  X = Promise.resolve('v')                    sync code done @0 > then callback @2
  X = thenable (then calls onF at once)       get then > sync code done @0 > then() called > then callback @1
[2] Promise.resolve(X)
  Promise.resolve(q) === q        true
  Promise.resolve(Promise.resolve('v'))       sync code done @0 > then callback @0
  Promise.resolve(thenable)                   get then > sync code done @0 > then() called > then callback @1
[3] a then callback returns X -- ticks counted from the start
  then(() => 'v')                             sync code done @0 > then callback @1
  then(() => Promise.resolve('v'))            sync code done @0 > then callback @3
```

**왜 그런가**

- ★★★ 값 → `@0`, **진짜 프라미스 → `@2`**, **곧바로 부르는 thenable → `@1`**.
- ★★★ `get then > sync code done @0 > then() called` — `then` 은 **resolve 안에서 읽히고**, 호출은 **잡 안에서** 일어난다.
- ★★ **`Promise.resolve(q) === q` 는 `true`** — 그래서 `@0`. `Promise.resolve(thenable)` 은 `@1`.
- ★★ **`then` 콜백이 프라미스를 돌려주면 `@3`**, 값이면 `@1`(+2).
- ★ **Chrome 151 도 한 글자도 같다** — 틱 수는 명세의 잡 개수가 정한다.

### 3. `h1 h2 h4 h5 h6 h7 h8` — **`h3` 은 안 찍힌다** · `h7` 은 **인자 0개** · `h8` 은 **`undefined`** ★★

**출력**

```text
===== node20 js36b-37c-chain.js (exit=0) =====
[1] a chain
  h1 got 1
  h2 got 2
  h4 (catch) got Error 「from h2」
  h5 got "from h4"
  h6 (second argument) got Error 「from h5」
  h7 (finally) got 0 arguments
  h8 got undefined
[2] Promise.prototype.finally grid
  fulfilled 'T'     returns nothing                  value "T"           upstream reached caller: true
  fulfilled 'T'     returns 'F'                      value "T"           upstream reached caller: true
  fulfilled 'T'     throws Error F                   threw Error 「F」     upstream reached caller: false
  fulfilled 'T'     returns Promise.reject(Error F)  threw Error 「F」     upstream reached caller: false
  rejected Error T  returns nothing                  threw Error 「T」     upstream reached caller: true
  rejected Error T  returns 'F'                      threw Error 「T」     upstream reached caller: true
  rejected Error T  throws Error F                   threw Error 「F」     upstream reached caller: false
  rejected Error T  returns Promise.reject(Error F)  threw Error 「F」     upstream reached caller: false
cells where the upstream outcome did not reach the caller: 4 / 8
```

**왜 그런가**

- ★★★ `h2` 가 던지자 사슬이 거부가 되고, **거부 쪽 처리기가 없는 `h3` 과 `then(undefined, undefined)` 는 그대로 넘긴다.** `h4`(`catch`)가 값을 돌려주자 **이행으로 돌아온다.**
- ★★ `h5` 가 **거부된 프라미스를 돌려주면** 새 프라미스도 거부 — `h6` 의 둘째 인자가 받는다. `h6` 은 아무것도 안 돌려주므로 `undefined`, `finally` 는 **통과**시켜 `h8` 도 `undefined`.

### 4. 닿지 못한 칸 **`4 / 8`** — `returns 'F'` 는 **상류의 것이 그대로** ★★★

**출력** — 3번과 같은 블록의 `[2]` 다.

**왜 그런가**

- ★★★ **콜백이 던지거나 거부된 프라미스를 돌려준 네 칸만** 그 예외(`Error 「F」`)가 나간다.
- ★★★ **`returns 'F'` 두 칸은 `value "T"` · `threw Error 「T」`** — `.finally()` 는 콜백의 값을 **기다리기만 하고 버린다.**

### 5. 마이크로태스크 안에 달면 **보고 없음 · `exit 0`**, 매크로태스크에 달면 **보고 · 훅 없으면 `exit 1`** — `0 / 6` ★★★

**출력**

```text
===== ./js36b-37d-unhandled-node.sh (exit=0) =====
--- node18
  catch attached   with hooks: stdout                                   exit      no hooks: exit · ERR_UNHANDLED_REJECTION on stderr
  same-tick        catch ran                                            0         0 · no
  next-microtask   catch ran                                            0         0 · no
  3rd-microtask    catch ran                                            0         0 · no
  setTimeout-0     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  setImmediate     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  never            unhandledRejection(R)                                0         1 · yes
--- node20
  catch attached   with hooks: stdout                                   exit      no hooks: exit · ERR_UNHANDLED_REJECTION on stderr
  same-tick        catch ran                                            0         0 · no
  next-microtask   catch ran                                            0         0 · no
  3rd-microtask    catch ran                                            0         0 · no
  setTimeout-0     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  setImmediate     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  never            unhandledRejection(R)                                0         1 · yes

rows where node18 and node20 differ: 0 / 6
```

**왜 그런가**

- ★★★ **same-tick · next-microtask · 3rd-microtask** — `catch ran` · `0` · `0 · no`. node 는 **마이크로태스크를 다 비운 뒤에** 처리기 없는 거부를 본다.
- ★★★ **setTimeout-0 · setImmediate** — 훅이 있으면 `unhandledRejection(R) catch ran rejectionHandled` · `0`, 없으면 `1 · yes`(그리고 `catch` 는 못 돈다). **never** — `unhandledRejection(R)` · `0` / `1 · yes`.
- ★★ **훅이 있으면 `exit 0`** — 기본 모드 `throw` 는 「훅이 없을 때만」 미처리 예외로 올린다. **두 판이 같다**(`0 / 6`).

### 6. `catch ran` 셋 → **`unhandledrejection(setTimeout-0-twice)`** · **`unhandledrejection(never)`** → `catch ran(setTimeout-0-twice)` → **`rejectionhandled(setTimeout-0-twice)`** — 플래그 없이는 **이벤트 줄이 전부 빠진다** ★★★

**출력**

```text
===== ./js36b-browser.sh js36b-37f-unhandled.web.js (exit=0) =====
catch ran(same-tick)
catch ran(next-microtask)
catch ran(setTimeout-0)
unhandledrejection(setTimeout-0-twice)
unhandledrejection(never)
catch ran(setTimeout-0-twice)
rejectionhandled(setTimeout-0-twice)
```

```text
===== ./js36b-browser.sh --muted js36b-37f-unhandled.web.js (exit=0) =====
catch ran(same-tick)
catch ran(next-microtask)
catch ran(setTimeout-0)
catch ran(setTimeout-0-twice)
```

**왜 그런가**

- ★★★ **`setTimeout-0` 은 보고되지 않았다** — HTML 은 알림을 **태스크 하나로** 미루는데, 이 판에서는 `setTimeout` 0 의 `catch` 가 그 태스크보다 먼저 돌았다(node 는 보고했다 — 5번).
- ★★ `setTimeout` 을 두 번 거친 것은 **보고된 뒤** 달려 `rejectionhandled` 가 따라왔다.
- ★★★ **플래그 없이**는 `file://` 스크립트가 **muted** 라서 HTML 의 훅이 첫 단계에서 돌아간다 — `catch ran` 네 줄만 남는다.

### 7. **한 칸**(프라미스를 가리키는 레코드)을 나눠 준다 — 첫 호출이 **그 칸을 비운다** ★★

- ★★★ resolve·reject 는 같은 `promiseOrEmpty` 칸을 본다. 칸이 비어 있으면 **바로 돌아가고**, 아니면 칸을 **비운 뒤** 일을 한다 — 그래서 **둘째 호출부터 무력**하다.
- ★★ executor 의 `throw` 는 **`reject(예외)` 를 부르는 것**과 같다 — `resolve('a')` 가 칸을 이미 비웠으므로 **삼켜진다**(1번 `fulfilled "a"`).

### 8. ① `NewPromiseResolveThenableJob`(`q.then` 을 부르는 잡) ② **`q` 의 반응 잡** ★★★

- ★★★ ①은 thenable 의 `then` 을 **잡 안에서** 부르는 잡이다. ②는 `q.then(res, rej)` 에 건 처리기 — `q` 가 이미 이행했어도 **처리기는 잡으로** 돈다. 그 뒤에야 `p` 의 `then` 콜백이 걸린다.
- ★★ 곧바로 `onF` 를 부르는 thenable 은 **②가 없다** — 잡 ① 안에서 `p` 가 바로 이행한다(`@1`).
- ★ `Promise.resolve(q)` 는 `q` 가 **같은 생성자의 프라미스면 그대로 돌려준다**(`=== q` 가 `true`) — 감쌀 새 프라미스가 없다.

### 9. **`finally` 가 값 `'F'` 를 돌려준 칸** — `try`/`finally` 는 `'F'` 가 나가고, `.finally()` 는 **상류의 것**이 나간다 ★★★

- ★★★ 32번 동작 (1)에서 `finally` 의 `return 'F'` 는 `try` 의 반환값도 예외도 **버렸다.** `.finally()` 에서 `'F'` 는 **버려지고 상류가 통과**한다. 던지는 칸은 둘 다 **덮는다.**
- ★★ `thenFinally` 는 콜백 결과를 `PromiseResolve` 로 감싸 **기다린다**(거부면 그것이 나간다). 그러나 그 **값을 결과로 쓰지 않는다** — 「원래 `value` 를 돌려주는 함수」를 `then` 에 건다.

### 10. 언어는 **훅을 부르는 것까지**(`"reject"` · `"handle"`) — 보고·종료는 **호스트** ★★★

- ★★★ `HostPromiseRejectionTracker(promise, "reject")` — 처리기 없이 거부될 때. `"handle"` — 거부된 프라미스에 처리기가 **처음** 달릴 때. **기본 구현은 아무것도 안 한다.**
- ★★ node 기본 모드 `throw` — 마이크로태스크를 다 비운 뒤에도 처리기가 없고 **`unhandledRejection` 훅이 없으면** 미처리 예외 → `exit 1`. 훅이 있으면 `exit 0`. `warn` 모드면 경고만 적고 **`exit 0`**(5번의 표준 오류 블록).

```text
===== ./js36b-37e-unhandled-stderr.sh (exit=0) =====
--- node20 js36b-37-h-late-catch.js never
node:internal/process/promises:389
      new UnhandledPromiseRejection(reason);
      ^

UnhandledPromiseRejection: This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). The promise rejected with the reason "R".
    at throwUnhandledRejectionsMode (node:internal/process/promises:389:7)
    at processPromiseRejections (node:internal/process/promises:470:17)
    at process.processTicksAndRejections (node:internal/process/task_queues:96:32) {
  code: 'ERR_UNHANDLED_REJECTION'
}

Node.js v20.19.6
(exit 1)
--- node20 --unhandled-rejections=warn js36b-37-h-late-catch.js never
(node:212044) UnhandledPromiseRejectionWarning: R
(Use `node --trace-warnings ...` to show where the warning was created)
(node:212044) UnhandledPromiseRejectionWarning: Unhandled promise rejection. This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). To terminate the node process on unhandled promise rejection, use the CLI flag `--unhandled-rejections=strict` (see https://nodejs.org/api/cli.html#cli_unhandled_rejections_mode). (rejection id: 1)
(exit 0)
```

- ★★ HTML — 마이크로태스크 체크포인트 끝에서 **태스크 하나를 큐에 넣고**, 그 태스크가 돌 때 **아직 처리기 없는 것**에만 쏜다. 그 태스크와 **타이머 태스크의 순서는 HTML 이 정하지 않는다** — Chrome 151 의 `setTimeout-0` 은 **관찰**이다.

### 11. 「**classic script 이고 muted errors 면 return**」 ★★

- ★★ 교차 출처로 불러온 classic script — `file://` 는 교차 출처로 취급된다 — 에서는 HTML 이 거부를 **추적조차 안 한다.**
- ★ **「안 보인다」는 「없다」가 아니다** — 6번의 muted 블록에도 `never` 와 `setTimeout-0-twice` 의 거부는 **그대로 있었다.** 보고만 꺼졌다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js36b-37a-transitions.js` | ★★★ 전이 11행 · 「`0 / 5`」 · 잠긴 pending | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-37b-ticks.js` | ★★★ 틱 `@0`·`@1`·`@2`·`@3` · `get then` 과 `then()` 의 때 | node20 1벌 + node18 대조 + Chrome 151 1벌 |
| `js36b-37c-chain.js` | ★★ 사슬 전파 · ★★★ `finally` 8칸 「`4 / 8`」 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-37-h-late-catch.js` + `js36b-37d-unhandled-node.sh` | ★★★ 미처리 거부 6행 × 2판 「`0 / 6`」 | node18·node20 각 행 2벌(훅 있음·없음) |
| `js36b-37e-unhandled-stderr.sh` | ★★ 기본 모드 표준 오류 · `warn` 모드 | node20 1벌씩 |
| `js36b-37f-unhandled.web.js` | ★★★ Chrome 의 보고 순서 · muted 면 0 줄 | Chrome 151 플래그 있음·없음 1벌씩 |

두 node 판 · Chrome 대조기(이 묶음 전체의 node 탐침). `DIFFERS` 가 한 줄도 없다.

```sh
# js36b-vdiff.sh
#!/usr/bin/env bash
# Every plain node probe of this batch (js36b-3NX-*.js, not *.web.js), run on node18, node20 and Chrome 151.
# A probe that uses a node-only API (process.*) is compared between the two node versions only.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
s18=0; d18=0; sw=0; dw=0; skip=0
for f in js36b-3[6789]?-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"; b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then r18=identical; s18=$((s18 + 1)); else r18=DIFFERS; d18=$((d18 + 1)); fi
  if grep -q 'process\.' "$f"; then rw="(node only)"; skip=$((skip + 1))
  else
    w="$(./js36b-browser.sh "$f")"
    if [ "$w" = "$b" ]; then rw=identical; sw=$((sw + 1)); else rw=DIFFERS; dw=$((dw + 1)); fi
  fi
  printf '%-36s node18/node20 %-10s node20/Chrome %s\n' "$f" "$r18" "$rw"
done
echo ""
echo "node18 vs node20: identical $s18 · differs $d18   ·   node20 vs Chrome 151: identical $sw · differs $dw · node only $skip"
```

```text
===== ./js36b-vdiff.sh (exit=0) =====
js36b-36c-starvation.js              node18/node20 identical  node20/Chrome identical
js36b-36d-nexttick-starvation.js     node18/node20 identical  node20/Chrome (node only)
js36b-37a-transitions.js             node18/node20 identical  node20/Chrome identical
js36b-37b-ticks.js                   node18/node20 identical  node20/Chrome identical
js36b-37c-chain.js                   node18/node20 identical  node20/Chrome identical
js36b-38a-combinator-grid.js         node18/node20 identical  node20/Chrome identical
js36b-38b-no-cancel.js               node18/node20 identical  node20/Chrome identical
js36b-38e-endless.js                 node18/node20 identical  node20/Chrome identical
js36b-39a-async-basics.js            node18/node20 identical  node20/Chrome identical
js36b-39b-seq-vs-par.js              node18/node20 identical  node20/Chrome identical
js36b-39d-foreach.js                 node18/node20 identical  node20/Chrome identical
js36b-39e-return-await.js            node18/node20 identical  node20/Chrome identical
js36b-39g-generator-runner.js        node18/node20 identical  node20/Chrome identical

node18 vs node20: identical 13 · differs 0   ·   node20 vs Chrome 151: identical 12 · differs 0 · node only 1
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **미처리 거부의 보고 시점과 종료 코드** — node 의 모드와 Chrome 의 태스크 순서. 판이 오르면 5번·6번을 다시 돌린다.
- ★★ `--unhandled-rejections=warn` 블록의 **`(node:PID)`** 는 실행마다 바뀐다 — 재대조에서 정규화한 유일한 칸이다.
- ★ 예외 문구(`Chaining cycle detected …`)와 node 의 경고 문구.
