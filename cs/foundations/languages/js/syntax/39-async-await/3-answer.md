# js/syntax/39 — `async`/`await`: 「늘 프라미스 · 첫 `await` 까지 지금 · `await` 마다 틱 · 시작 순서가 병렬을 정한다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스) · Python 3.12 · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical` · 4번의 `2 / 2`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(7번 · 8번 · 9번은 [2-summary.md](2-summary.md) 동작 (7)·(8)·(9)).
> `js36b-39a-async-basics.js`(1번 · 2번 · 10번) · `js36b-39b-seq-vs-par.js`(3번 · 11번) · `js36b-39-h-early-reject.js` + `js36b-39c-early-reject.sh`(4번) ·
> `js36b-39d-foreach.js`(5번) · `js36b-39e-return-await.js`(6번) · `js36b-39-h-tla.mjs` + `js36b-39f-top-level-await.sh`(7번) · `js36b-39g-generator-runner.js`(8번) · `js36b-39h-python-contrast.sh`(9번).

## 정답

### 1. 넷 다 **`returned` · `a Promise` · `inner` 와 다른 객체** — `throw` 도 **거부된 프라미스** · `[2]` 는 **`f: line 1 > f: line 2` 가 `caller: after f()` 앞** ★★★

**출력**

```text
===== node20 js36b-39a-async-basics.js (exit=0) =====
[1] return values
  async () => 1                     returned a Promise · same object as inner false · fulfilled 1
  async () => { throw Error('x') }  returned a Promise · same object as inner false · rejected Error 「x」
  async () => inner (a promise)     returned a Promise · same object as inner false · fulfilled "v"
  async () => {} (nothing)          returned a Promise · same object as inner false · fulfilled undefined
[2] order of lines around a call
  caller: before f() > f: line 1 > f: line 2 > caller: after f() > f: after await
[3] microtask ticks until the step after X runs
  await 1                                 caller's next line @0 > after await @0 > caller's then @1
  await settledP                          caller's next line @0 > after await @0 > caller's then @1
  await thenable                          caller's next line @0 > after await @1 > caller's then @2
  no await, return 'v'                    caller's next line @0 > caller's then @0
  return settledP                         caller's next line @0 > caller's then @2
  return await settledP                   caller's next line @0 > caller's then @1
```

**왜 그런가**

- ★★★ 호출은 **새 프라미스**를 만들어 돌려주고 본문을 **곧바로** 돌린다. 본문이 던지면 그 프라미스를 **거부**한다 — 호출한 자리로는 안 나온다.
- ★★★ 안에서 돌려준 `inner` 와 **같은 객체가 아니다**(`false`) — 바깥 프라미스가 `inner` 를 **따라간다**(`fulfilled "v"`).
- ★★★ 본문은 **첫 `await` 까지 지금** 돌고, `await` 에서 호출자로 돌아간다 — `caller: after f()` 가 `f: after await` 보다 먼저.

### 2. `await 1` · `await settledP` 는 **`@0`/`@1`**, `await thenable` 은 **`@1`/`@2`** · `return 'v'` **`@0`** · `return settledP` **`@2`** · `return await settledP` **`@1`** ★★★

**출력** — 1번과 같은 블록의 `[3]` 이다.

**왜 그런가**

- ★★★ **`await 1` 도 쉰다** — `caller's next line @0` 이 `after await @0` 보다 **먼저** 찍혔다. `Await` 는 값을 감싸 `then` 을 걸고 **반응 잡**으로 돌아온다.
- ★★ thenable 은 `PromiseResolve` 가 **새 프라미스 + `NewPromiseResolveThenableJob`** 을 만들어 한 틱 더 든다(37번 동작 (2)).
- ★★ `return settledP` 는 결과 프라미스를 **프라미스로 resolve** 해서 +2(37번), `return await` 는 **값으로 resolve** 해서 +1 이었다.

### 3. `[1]`·`[4]` 는 **`false`**, `[2]`·`[3]` 은 **`true`** — 결과는 넷 다 **`["a","b"]`** ★★★

**출력**

```text
===== node20 js36b-39b-seq-vs-par.js (exit=0) =====
[1] await a(); await b();
  a start > a end > b start > b end   result ["a","b"]
  b started before a ended: false
[2] await Promise.all([a(), b()])
  a start > b start > a end > b end   result ["a","b"]
  b started before a ended: true
[3] const pa = a(), pb = b(); await pa; await pb;
  a start > b start > a end > b end   result ["a","b"]
  b started before a ended: true
[4] for (const n of ['a', 'b']) await job(n)
  a start > a end > b start > b end   result ["a","b"]
  b started before a ended: false
```

**왜 그런가**

- ★★★ **`b()` 를 부른 줄이 `a` 를 기다리는 줄보다 앞에 있으면** 겹친다. `[3]` 은 `Promise.all` 없이도 `true` 다.
- ★★ 결과가 같은 것은 **값이 같은 순서로 모였기 때문**이다 — 달라진 것은 **시작 순서뿐**이다. 시간은 재지 않았다.

### 4. `one-by-one` 은 **`unhandledRejection(b)` 가 끼고 훅 없으면 `exit 1`**, `all` 은 **보고 없이 `exit 0`** — `2 / 2` ★★★

**출력**

```text
===== ./js36b-39c-early-reject.sh (exit=0) =====
--- one-by-one
  with hooks : b rejects unhandledRejection(b) a end caught Error 「b」 rejectionHandled
  no hooks   : exit 1
--- all
  with hooks : b rejects caught Error 「b」 a end
  no hooks   : exit 0

rows where node18 gives the same two answers as node20: 2 / 2
```

**왜 그런가**

- ★★★ `await pa` 를 기다리는 동안 **`pb` 가 먼저 거부**된다 — 그 순간 `pb` 에는 **처리기가 없다**(`await pb` 는 아직 안 닿았다). node 는 마이크로태스크를 다 비운 뒤 이것을 보고하고, 훅이 없으면 **`exit 1`** 로 끝낸다. `catch` 블록이 코드에 있어도 소용없다.
- ★★ `Promise.all` 은 **두 입력에 곧바로 `then` 을 건다** — 거부가 처리된 채 도착한다. `caught Error 「b」` 뒤에도 `a end` 가 찍혔다(38번 — 취소는 없다).

### 5. `forEach` 는 **`-- line after forEach` 가 `x done` 앞** · `forEach returned undefined` — `for…of` 와 `Promise.all(map)` 은 **맨 끝** ★★★

**출력**

```text
===== node20 js36b-39d-foreach.js (exit=0) =====
[1] items.forEach(async (it) => { await step(); ... })
  x start > y start > z start > -- line after forEach · forEach returned undefined > x done > y done > z done
[2] for (const it of items) { await step(); ... }
  x start > x done > y start > y done > z start > z done > -- line after for...of
[3] await Promise.all(items.map(async (it) => { await step(); ... }))
  x start > y start > z start > x done > y done > z done > -- line after Promise.all
```

**왜 그런가**

- ★★★ `forEach` 는 콜백이 돌려준 프라미스를 **버린다** — 기다릴 것을 받지 못한다. 세 항목은 **겹쳐서** 돌았다.
- ★★ `for…of` + `await` 는 **차례로**, `Promise.all(map(…))` 은 **겹쳐서** 돌고 **둘 다 기다린다.**

### 6. `return p` — **`catch` 없음 · `finally` 가 먼저 · `rejected Error 「late」`** / `return await p` — **`catch ran > finally ran` · `fulfilled "from catch"`** ★★★

**출력**

```text
===== node20 js36b-39e-return-await.js (exit=0) =====
return failLater()
  finally ran > caller: call returned > caller got rejected Error 「late」
return await failLater()
  caller: call returned > catch ran > finally ran > caller got fulfilled "from catch"
```

**왜 그런가**

- ★★★ `return p` 는 `p` 를 완료 기록에 담고 **곧바로 `try` 를 떠난다** — `finally` 가 호출 안에서 돌고, `p` 의 나중 거부는 **`try` 밖**에서 일어난다.
- ★★★ `return await p` 는 `p` 가 확정될 때까지 **`try` 안에서 멈춘다** — 거부가 그 자리에서 던져져 `catch` 가 받는다.

### 7. `.mjs` · `--input-type=module` 은 **돌고**, `--input-type=commonjs` 는 **`SyntaxError` · `exit 1` · 표준 출력 0 줄** ★★

```js
// js36b-39-h-tla.mjs
// await at the top level of the file, outside any function.
console.log("before");
const v = await new Promise((r) => setTimeout(() => r("value"), 0));
console.log("after: " + v);
```

```text
===== ./js36b-39f-top-level-await.sh (exit=0) =====
--- node18 js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node18 --input-type=module < js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node18 --input-type=commonjs < js36b-39-h-tla.mjs   (standard error: the error line only)
SyntaxError: await is only valid in async functions and the top level bodies of modules
(exit 1 · standard output had 0 lines)
--- node20 js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node20 --input-type=module < js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node20 --input-type=commonjs < js36b-39-h-tla.mjs   (standard error: the error line only)
SyntaxError: await is only valid in async functions and the top level bodies of modules
(exit 1 · standard output had 0 lines)
```

- ★★ 기준은 **모듈 코드인가**다 — 표준 입력의 같은 글자도 모듈로 주면 돌았다. **어느 파일이 모듈인가는 node(호스트)가 정한다**(`.mjs` · `--input-type` · `package.json` 의 `type` — 목록의 **42번 주제**).
- ★ CommonJS 판은 **컴파일에서** 거절되어 `before` 조차 안 찍혔다 — 35번의 early error 와 같은 모양이다.

### 8. `yield x` ↔ `await x` · 거부 ↔ `it.throw(e)` — **줄 순서까지 같았다**(`identical: true`) ★★

```text
===== node20 js36b-39g-generator-runner.js (exit=0) =====
async function    body start > other 1 > got 1 > other 2 > got 2 > other 3 > caught r > other 4 > result done > other 5 > other 6
generator + run() body start > other 1 > got 1 > other 2 > got 2 > other 3 > caught r > other 4 > result done > other 5 > other 6
identical: true
```

- ★★ 러너는 `yield` 된 값을 `Promise.resolve(x).then(next, throw)` 로 기다린다 — 명세의 `Await` 가 하는 **`PromiseResolve` → `PerformPromiseThen`** 두 걸음과 같다. 그래서 옆 사슬(`other k`)과 **틱 단위로** 같은 순서가 나왔다.

### 9. 파이썬은 **부르기만 해서는 안 돈다**, JS 는 **첫 `await` 까지 지금 돈다** ★★

```text
===== ./js36b-39h-python-contrast.sh (exit=0) =====
--- python3 3.12 js36b-39-h-lazy.py
caller: before f() > caller: after f() -- got coroutine
main: before f() > main: after create_task > f: line 1 > f: after await > main: after await t
(exit 0)
--- node20 js36b-39-h-eager.js
caller: before f() > f: line 1 > caller: after f() -- got Promise
(exit 0)
```

- ★★ 그래서 JS 에서 부르고 안 기다린 `async` 함수는 **이미 일을 하고**, 그 거부는 **처리기 없이** 도착할 수 있다 — 4번의 함정이 거기서 나온다.
- ★ Rust `Future` 는 **파이썬 쪽**이다 — 러스트 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **54번**이 「`await` 하지 않은 future 가 왜 아무 일도 안 하는지」를 인출 목표로 적는다. **이 문서는 Rust 를 돌리지 않았다.**

### 10. `PromiseResolve` → `PerformPromiseThen` → **호출자로 돌아간다** ★★★

- ★★★ 세 걸음이다. 재개는 `then` 에 건 처리기 — **반응 잡** — 이 한다.
- ★★ 값이 이미 있어도 **`then` 을 걸었으므로** 반응 잡을 기다린다(2번의 `caller's next line` 이 먼저). thenable 은 `PromiseResolve` 가 **새 프라미스를 만들고 thenable 잡을 하나 더** 건다.
- ★★ 32번 동작 (2)의 **「`return 식` 은 식을 먼저 평가해 완료 기록에 담는다」** — 담긴 것이 **아직 pending 인 프라미스**면, 그것의 거부는 `try` 가 끝난 뒤에 온다.

### 11. **`b()` 를 부른 자리**가 만든다 · 시간은 **안 쟀다** ★★

- ★★ `[3]` 이 `Promise.all` 없이 `true` 였다 — `Promise.all` 은 **이미 시작한 것을 기다리는** 방법이다(38번 동작 (2)).
- ★ 이 문서의 근거는 **시작 로그의 순서**뿐이다. 연혁 문서의 순차/병렬 그림도 「**가로 길이는 그림을 위한 것이고, 원문에 있는 수치는 아니다**」라고 스스로 적는다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js36b-39a-async-basics.js` | ★★★ 반환 4행 · 첫 `await` 까지 동기 · 틱 6행 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-39b-seq-vs-par.js` | ★★★ 시작 순서 4행 · `false`/`true` | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-39-h-early-reject.js` + `js36b-39c-early-reject.sh` | ★★★ 먼저 부르고 차례로 — 보고 · `exit 1` · 「`2 / 2`」 | node20 · node18 각 행 2벌(훅 있음·없음) |
| `js36b-39d-foreach.js` | ★★★ `forEach` 는 안 기다린다 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-39e-return-await.js` | ★★★ `return` 대 `return await` | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-39-h-tla.mjs` + `js36b-39f-top-level-await.sh` | ★★ 최상위 `await` — 모듈 · CommonJS | node18 · node20 세 방식씩 |
| `js36b-39g-generator-runner.js` | ★★ `identical: true` | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-39-h-lazy.py` · `js36b-39-h-eager.js` + `js36b-39h-python-contrast.sh` | ★★ 코루틴은 부르기만 해서는 안 돈다 | Python 3.12 · node20 1벌씩 |

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

- ★★ **4번의 보고와 종료 코드** — node 의 모드(37번). 판이 오르면 다시 돌린다.
- ★★ **모듈 판정**(`--input-type` · `.mjs`) — node 의 것이다. node 판이 모듈 판정 규칙을 바꾸면 7번을 다시 돌린다.
- ★ 예외 문구 — `await is only valid in async functions and the top level bodies of modules`.
