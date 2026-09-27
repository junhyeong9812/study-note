# js/syntax/40 — 비동기 이터레이션: 「떠날 때는 `return()` 을 기다리고 · 값은 기다린 뒤 받고 · 동기 이터러블은 감싼다 — 거부된 값을 닫는지는 판이 정한다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **이 주제에서 판이 갈린 칸은 하나다** — 1번 격자 C 행 `rejects`(Chrome 151 만 닫았다). 두 node 판은 서로 한 글자도 같았다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js40b-40a-close-grid.js`(1번 · 2번 · 8번) · `js40b-40-h-premade.js` + `js40b-40b-premade.sh`(3번 · 9번) · `js40b-40c-which-protocol.js`(4번 · 6번) · `js40b-40d-yield-and-ticks.js`(5번 · 7번 · 10번).

## 정답

### 1. `break`·`return`·`throw` 는 세 행 모두 **`return() yes · finally yes`**, 끝까지는 **`no · yes`** — 갈린 칸 **`1 / 10`**(`rejects` 열의 C 행) ★★★

**출력**

```text
===== node20 js40b-40a-close-grid.js (exit=0) =====
A for...of + sync generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  completed               got 1 > got a Promise > got 3 > finally
B for await + async generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  caught rejected value   got 1 > finally
C for await + sync generator of promises
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally no   caught rejected value   got 1
cells where a for await row differs from row A in (return() called, finally ran): 1 / 10
```

**왜 그런가**

- ★★★ 일찍 떠나는 셋은 `for...of` 가 `IteratorClose`, `for await` 가 `AsyncIteratorClose` 를 부른다 — **둘 다 `return()` 을 부른다.** 끝까지 간 루프는 `done: true` 를 **직접 받았으니** 닫을 일이 없고, `finally` 는 제너레이터가 **끝나면서** 돈다.
- ★★ `rejects` 열에서 A·B 는 `return() no · finally yes` 로 **같은 칸**이지만 이유가 다르다 — A 는 **끝까지 가서**, B 는 **제너레이터 안에서 던져져서**(`caught rejected value`). C 는 `no · no` 로 **A 와 갈린다.**

### 2. A 는 **아무도 안 기다린다** · B 는 **제너레이터의 `yield`** · C 는 **감싸개** — C 칸은 **node 18·20 은 안 닫고, Chrome 151 은 닫았다** ★★★

**출력** — Chrome 151 에서 같은 소스(C 행 `rejects` 만 다르다).

```text
===== ./js40b-browser.sh js40b-40a-close-grid.js (exit=0) =====
A for...of + sync generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  completed               got 1 > got a Promise > got 3 > finally
B for await + async generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  caught rejected value   got 1 > finally
C for await + sync generator of promises
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() yes finally yes  caught rejected value   got 1 > return() > finally
cells where a for await row differs from row A in (return() called, finally ran): 1 / 10
```

**왜 그런가**

- ★★★ C 행에서 거부된 프라미스를 기다린 것은 **`CreateAsyncFromSyncIterator` 의 감싸개**다. 명세의 `AsyncFromSyncIteratorContinuation` 은 「**`closeOnRejection` 이면 값 프라미스가 거부될 때 동기 이터레이터를 닫는다**」고 적는다 — 그래서 Chrome 151 은 `return() > finally` 를 찍었다.
- ★★ 그 낱말은 **ES2025(16판) 본문에 4건, 15판·14판에 0건**이다. node 20 의 V8 11.3 은 그 판보다 앞선다 — **node 18·20 에서는 제너레이터가 열린 채 남는다**(`finally no`).
- ★ 대조기의 `js40b-40a-close-grid.js … node20/Chrome DIFFERS` 가 이 한 칸이다.

### 3. `array-a-b-c` · `array-b-d` 는 **`unhandledRejection` + 훅 없으면 `exit 1`**, `all-a-b-c` · `gen-a-b-c` 는 **`exit 0`** — `c` 는 **시작하지 않는다** ★★★

**출력**

```text
===== ./js40b-40b-premade.sh (exit=0) =====
--- array-a-b-c
  with hooks : b rejects unhandledRejection(b) c settles a settles got a caught Error 「b」 rejectionHandled
  no hooks   : exit 1
--- array-b-d
  with hooks : b rejects caught Error 「b」 d rejects unhandledRejection(d)
  no hooks   : exit 1
--- all-a-b-c
  with hooks : b rejects caught Error 「b」 c settles a settles
  no hooks   : exit 0
--- gen-a-b-c
  with hooks : a settles got a b rejects caught Error 「b」
  no hooks   : exit 0

rows where node18 gives the same two answers as node20: 4 / 4
```

**왜 그런가**

- ★★★ `for await` 는 배열을 **하나씩** 기다린다. `a` 를 기다리는 동안 먼저 깨진 `b` 에는 **처리기가 없다** — node 는 마이크로태스크를 비운 뒤 그것을 보고하고, 훅이 없으면 `exit 1` 이다. `catch` 가 코드에 있어도 소용없다.
- ★★★ `array-b-d` — 루프가 `b` 에서 던지고 떠나면 `d` 는 **영영 안 기다려진다.**
- ★★ `Promise.all` 은 **모두에 곧바로** 처리기를 건다. async generator 는 **당길 때 만든다** — `b` 에서 떠났으니 `c` 는 **불리지도 않았다**(`c settles` 가 없다).

### 4. `for await` 는 **`@@asyncIterator` 하나만**, 없으면 **`@@iterator` 로 내려가 감싼다** · `for...of` 는 **`@@iterator` 하나만** — async generator 는 **`for...of`·스프레드 둘 다 `TypeError`** · `[4]` 는 **`finally end` 뒤에 `line after the loop`** ★★

**출력**

```text
===== node20 js40b-40c-which-protocol.js (exit=0) =====
[1] for await ... of
  both                get asyncIterator > got from async
  asyncIterator only  get asyncIterator > got from async
  iterator only       get iterator > got from sync
  neither             TypeError 「make(...) is not a function or its return value is not async iterable」
[2] for ... of
  both                get iterator > got from sync
  asyncIterator only  TypeError 「make is not a function or its return value is not iterable」
  iterator only       get iterator > got from sync
  neither             TypeError 「make is not a function or its return value is not iterable」
[3] an async generator object
  typeof g[Symbol.asyncIterator] function · typeof g[Symbol.iterator] undefined · g[Symbol.asyncIterator]() === g true
  for...of over it: TypeError 「ag is not a function or its return value is not iterable」
  spread of it:     TypeError 「ag is not a function or its return value is not iterable」
[4] break out of for await -- the generator's finally contains an await
  got 1 > finally start > finally end > line after the loop
```

**왜 그런가**

- ★★★ `GetIterator(obj, async)` 는 `@@asyncIterator` → 없으면 `@@iterator` 를 `CreateAsyncFromSyncIterator` 로 감싼다. `GetIterator(obj, sync)` 는 **`@@iterator` 만** 본다 — 그래서 `asyncIterator only` 는 `for...of` 에서 `TypeError` 다.
- ★★ 문구 `make is not a function or its return value is not iterable` 의 앞 절반은 **원인이 아니다** — `make` 는 함수다. 근거는 **`TypeError` 라는 종류**와 **getter 가 무엇을 읽었나**다.

### 5. **몸통은 늘 확정된 값**(`for...of` + 동기 gen 만 **`a Promise @0`**) · `@2`·`@2`·**`@3`**·`@2`·`@2` · **`body: step 2 begins` 가 먼저** ★★

**출력**

```text
===== node20 js40b-40d-yield-and-ticks.js (exit=0) =====
[1] one value, one loop
  async gen: yield 1                          body got number 1 @2
  async gen: yield settledP                   body got string "v" @2
  async gen: yield await settledP             body got string "v" @3
  for await over [1]                          body got number 1 @2
  for await over [settledP]                   body got string "v" @2
  for...of over sync gen: yield settledP      body got a Promise @0
[2] three it.next() calls in a row
  body: step 1 begins
  caller: three next() calls returned Promise,Promise,Promise
  body: yield 1
  body: step 2 begins
  caller: next#1 -> {"value":1,"done":false}
  body: yield 2
  body: step 3 begins
  caller: next#2 -> {"value":2,"done":false}
  body: yield 3
  caller: next#3 -> {"value":3,"done":false}
```

**왜 그런가**

- ★★ async generator 의 `yield` 는 **값을 기다린 뒤** 내보내고, `for await` 는 그 `next()` 결과를 **또 기다린다** — 몸통에는 프라미스가 안 온다. `yield await` 는 `await` 가 하나 더라 **한 틱 더**(`@3`).
- ★★ `next()` 세 번은 **요청 큐**에 선다. 본문은 `yield 1` 을 하고도 큐에 요청이 남아 있으니 **멈추지 않고** `step 2` 로 간다 — 호출자의 `then` 보다 먼저 찍힌 이유다.

### 6. **`AsyncIteratorClose`** — `return()` 을 부르고 **그 결과를 `Await`** 한다 → `finally` 의 `await` 가 끝나야 루프 뒤로 간다 ★★★

- ★★★ 명세 문장 그대로 「`return` 을 부르고 … 그 결과를 **`Await`**」 한다. 4번 `[4]` 의 `got 1 > finally start > finally end > line after the loop` 가 그 증거다.
- ★★ 동기 `IteratorClose` 는 기다릴 것이 없다 — 이것이 동기판과의 **유일한 형식 차이**이고, 격자의 `yes`/`no` 는 같았다(1번).

### 7. **`AsyncGeneratorYield(? Await(arg))`** — 몸통이 받는 것은 **같고**(`string "v"`), 틱은 **다르다**(`@2` 대 `@3`) ★★

- ★★ 그래서 async generator 에서 `yield await p` 의 `await` 는 **값을 바꾸지 않는다** — 틱 하나를 더 쓸 뿐이다(5번).

### 8. 19번은 **17 중 8** — 이 문서의 A 행은 그 가운데 **`break`·`return`·몸통 `throw`** 셋을 다시 보였다 · 20번 규칙은 B 행 **`break`·`return`·`throw` 의 `finally yes`** 에 그대로 ★★

- ★★ 19번 요약 줄 `return() was called in 8 of 17 probes` — `break`·`return`·몸통의 `throw` 가 전부 `… | return()` 이었다. A 행의 `got 1 > got 2 > return() > finally` 가 같은 모양이다.
- ★★ 20번 동작 (3) — 「멈춘 `yield` 자리에서 `return` 이 일어난 것처럼」 → `finally` 가 돈다. B 행은 그것의 **비동기판**이다.

### 9. 39번 동작 (4)의 **「먼저 부르고 차례로 `await`」** 와 같다 — 피하는 법은 **`Promise.all`(모두 지금 시작 · 처리기 곧바로)** 과 **async generator(당길 때 시작)** ★★

- ★★ 39번의 `one-by-one` 이 `unhandledRejection(b)` · `exit 1` 이었다 — `for await` 로 배열을 돌면 **같은 줄을 문법으로 쓴 것**이다.
- ★ 두 해법은 **언제 시작하나**가 다르다 — `Promise.all` 은 이미 다 시작한 것을 기다리고, async generator 는 앞의 것이 끝나야 다음 것을 만든다(`gen-a-b-c` 에서 `c` 는 시작도 안 했다).

### 10. async generator 는 **줄을 서서 차례로 이행**, 동기 제너레이터의 재진입은 **`TypeError 「Generator is already running」`** ★

- ★ 비동기판에는 **요청 큐**가 있어서 겹친 호출이 에러가 아니다(5번 `[2]`). 동기판은 큐가 없어 실행 중 재진입을 `GeneratorValidate` 가 막는다(20번 동작 (7)).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js40b-40a-close-grid.js` | ★★★ 15칸 격자 · 「`1 / 10`」 · C 행 `rejects` 의 판 차이 | node20 1벌 + node18 대조 + Chrome 1벌(블록) |
| `js40b-40-h-premade.js` + `js40b-40b-premade.sh` | ★★★ 미리 만든 프라미스 — 보고 · `exit 1` · 「`4 / 4`」 | node20 · node18 각 행 2벌(훅 있음·없음) |
| `js40b-40c-which-protocol.js` | ★★ 찾는 메서드 · `TypeError` 문구 · 정리를 기다리는 것 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js40b-40d-yield-and-ticks.js` | ★★ 몸통이 받는 것 · `@k` · 요청 큐 | node20 1벌 + node18 대조 + Chrome(대조기) |

세 판 대조기(이 묶음 전체의 plain 탐침). 이 주제의 줄은 `40a`(Chrome `DIFFERS` — 2번) · `40c` · `40d` 셋이다.

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

- ★★★ **C 행 `rejects` 칸** — node 가 ES2025 의 `closeOnRejection` 을 따르는 V8 로 오르면 `return() yes · finally yes` 로 바뀔 자리다. 판이 오르면 1번을 다시 돌린다.
- ★★ **3번의 보고와 종료 코드** — node 의 모드(37번).
- ★ 예외 문구 — `… is not a function or its return value is not iterable` · `… not async iterable`.
