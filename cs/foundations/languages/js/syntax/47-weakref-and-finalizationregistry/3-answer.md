# js/syntax/47 — `WeakRef`·`FinalizationRegistry`: 「약속된 것은 『그 턴 동안은 돌려준다』 뿐 — `await` 열 번도 같은 턴이었고, 비워진 것은 `gc()` 를 부른 다음 턴의 관찰이다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6 · v18.19.1 · Google Chrome 151 · Python 3.12.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **`gc()` 는 V8 플래그가 여는 함수다** — 이 파일의 「비워졌다」 「불렸다」 는 전부 **이 판에서 `gc()` 를 부른 뒤의 관찰**이고, 「비워지지 않았다」 중 **같은 턴 안의 것만** 명세 보장이다(5번).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js44b-47a-observe-grid.js` + `.sh`(1번 · 5번 · 6번) · `js44b-47c-kept-alive.js`(2번 · 5번) · `js44b-47d-registry-api.js`(3번) · `js44b-47e-python.py`(4번 · 9번) · `js44b-47b-pressure-grid.js` + `.sh`(7번).

## 정답

### 1. `gc()` 없음 — 네 칸 **`0/20 · 0/20`** · **`0 / 4`** · `gc()` 있음 — `no wait`·`await ×1`·`await ×10` **`0/20 · 0/20`**, **`setTimeout 0` 만 `20/20 · 20/20`** · **`1 / 8`** · 비교 두 줄 **`yes`** ★★★

**출력**

```text
===== ./js44b-47a-observe.sh (exit=0) =====
--- node20
typeof gc: undefined · 20 rounds per cell
  does      waits           deref() undefined   callback ran
  nothing   no wait         0/20                0/20
  nothing   await null x1   0/20                0/20
  nothing   await null x10  0/20                0/20
  nothing   setTimeout 0    0/20                0/20
  gc()      no wait         n/a
  gc()      await null x1   n/a
  gc()      await null x10  n/a
  gc()      setTimeout 0    n/a
cells where at least one round saw deref() undefined or the callback: 0 / 4
--- node20 --expose-gc
typeof gc: function · 20 rounds per cell
  does      waits           deref() undefined   callback ran
  nothing   no wait         0/20                0/20
  nothing   await null x1   0/20                0/20
  nothing   await null x10  0/20                0/20
  nothing   setTimeout 0    0/20                0/20
  gc()      no wait         0/20                0/20
  gc()      await null x1   0/20                0/20
  gc()      await null x10  0/20                0/20
  gc()      setTimeout 0    20/20               20/20
cells where at least one round saw deref() undefined or the callback: 1 / 8
--- Chrome 151 --js-flags=--expose-gc
typeof gc: function · 20 rounds per cell
  does      waits           deref() undefined   callback ran
  nothing   no wait         0/20                0/20
  nothing   await null x1   0/20                0/20
  nothing   await null x10  0/20                0/20
  nothing   setTimeout 0    0/20                0/20
  gc()      no wait         0/20                0/20
  gc()      await null x1   0/20                0/20
  gc()      await null x10  0/20                0/20
  gc()      setTimeout 0    20/20               20/20
cells where at least one round saw deref() undefined or the callback: 1 / 8

node18 --expose-gc prints the same as node20 --expose-gc: yes
Chrome 151 without the flag prints the same as node20 without it: yes
```

**왜 그런가**

- ★★★ `new WeakRef(t)` 가 `t` 를 `[[KeptAlive]]` 에 넣고, 그 목록은 **마이크로태스크 체크포인트가 끝날 때**에야 비워진다 — 그 전의 `gc()` 는 못 거둔다(6번). `setTimeout` 을 넘기면 목록이 비어 있고, **이 판의** `gc()` 는 한 번에 거뒀다.
- ★★ `gc()` 가 없으면 20판 동안 GC 가 한 번도 이 대상을 안 거뒀다 — **「안 거둔다」 가 아니라 「이 시간 안에는 안 했다」** 다.

### 2. **`20` · `20` · `20` · `20` · `0`** ★★★

**출력**

```text
===== node20 --expose-gc js44b-47c-kept-alive.js (exit=0) =====
typeof gc: function · 20 rounds
  [1] same job: gc(), then deref()                        object 20/20
  [2] after await null: gc(), then deref()                object 20/20
  [3] next setTimeout turn: deref() before any gc()       object 20/20
  [4]   same turn, after that deref(): gc(), then deref() object 20/20
  [5] one more setTimeout turn: gc(), then deref()        object 0/20
```

Chrome 151 — `--js-flags=--expose-gc` 로.

```text
===== ./js44b-browser.sh --gc js44b-47c-kept-alive.js (exit=0) =====
typeof gc: function · 20 rounds
  [1] same job: gc(), then deref()                        object 20/20
  [2] after await null: gc(), then deref()                object 20/20
  [3] next setTimeout turn: deref() before any gc()       object 20/20
  [4]   same turn, after that deref(): gc(), then deref() object 20/20
  [5] one more setTimeout turn: gc(), then deref()        object 0/20
```

**왜 그런가**

- ★★★ `[3]` 의 `deref()` 가 대상을 **다시 `[[KeptAlive]]` 에 넣어**(`AddToKeptObjects`) `[4]` 의 `gc()` 도 못 거둔다 — 명세 note 「첫 `deref` 가 `undefined` 가 아니었으면 둘째도 그럴 수 없다」. `[5]` 는 목록이 빈 턴에서 `gc()` 를 부른 것이라 이 판은 거뒀다.

### 3. `constructor deref` · `constructor register unregister` · `undefined` · `undefined` · **`true`** · **`false`** · **`false`** · **`TypeError 「Invalid unregisterToken ('1')」`** · `undefined` · **`true`** · `TypeError`(같은 문구) · `TypeError 「FinalizationRegistry: cleanup must be callable」` ★

**출력**

```text
===== node20 js44b-47d-registry-api.js (exit=0) =====
[1] own properties
  WeakRef.prototype                                   ok constructor deref
  FinalizationRegistry.prototype                      ok constructor register unregister
[2] register and unregister
  reg.register({}, 'h1', token)                       ok undefined
  reg.register({}, 'h2', token)                       ok undefined
  reg.unregister(token)   (first time)                ok true
  reg.unregister(token)   (second time)               ok false
  reg.unregister({})   (a token never used)           ok false
  reg.unregister(1)                                   TypeError 「Invalid unregisterToken ('1')」
  reg.register(t, 'h', t)   (token = target)          ok undefined
  reg.unregister(t)                                   ok true
  reg.register({}, 'h', 1)   (a number as token)      TypeError 「Invalid unregisterToken ('1')」
  new FinalizationRegistry()                          TypeError 「FinalizationRegistry: cleanup must be callable」
```

- ★ node 18 은 두 `TypeError` 의 문구만 `unregisterToken ('1') must be an object` 로 달랐다(2-summary 동작 (4)).

### 4. `[1]` → **`finalize callback for b ran`** → `[2] … None` → `[3] … False` → **`finalize callback for c ran`** → `[4] … 2 …` → `[5] … True` ★★

**출력**

```text
===== python3 js44b-47e-python.py (exit=0) =====
[1] before del b: r() is alive -> True
  finalize callback for b ran
[2] the line after del b: r() -> None
[3] the line after del c (c.me = c): r2() is None -> False
  finalize callback for c ran
[4] gc.collect() found 2 unreachable objects
[5] after gc.collect(): r2() is None -> True
```

- ★★ 첫 콜백은 **`del b` 의 줄에서** — 참조 계수가 0 이 되는 순간. 둘째는 **`gc.collect()` 안에서** — 순환(`c.me = c`)은 계수가 0 이 안 되어 수집기를 기다린다. 「`[4]` 줄보다 먼저」 인 것은 `print` 의 인자인 `gc.collect()` 가 **그 줄을 찍기 전에** 돌기 때문이다.

### 5. 달라지면 **명세 위반** — 같은 턴(`no wait`) 행의 `0/20` · 2번의 `[1]`·`[3]`·`[4]` 의 `20` · 3번의 반환값·`TypeError` 의 종류 · 달라져도 **되는** 것 — `setTimeout` 행의 `20/20 · 20/20` · 2번 `[5]` 의 `0` · `gc()` 없는 판의 `0/20` · `await` 행(호스트가 목록을 언제 비우나에 달렸다) · **`gc()` 자체는 V8 플래그** ★★★

- ★★★ 명세가 **「비우지 마라」** 는 쪽만 못 박고(목록에 있는 동안), **「비워라」** 는 한 번도 말하지 않는다 — "may". 그래서 「비워졌다」 가 적힌 칸은 **전부** 판의 관찰이다.
- ★★ `await` 행은 **호스트 층**이다 — 명세는 「동기 실행이 끝날 때」 만 적고, HTML 이 그 끝을 체크포인트의 끝으로 정했다(6번). 다른 호스트가 마이크로태스크마다 비워도 명세 위반은 아니다(이 문장은 명세 문장에서 끌어낸 해석이다).

### 6. 명세 — `ClearKeptObjects` 는 「**when a synchronous sequence of ECMAScript executions completes**」 · HTML — **마이크로태스크 체크포인트의 끝에서 「Perform ClearKeptObjects()」** · `await ×10` 은 **아직 같은 체크포인트**라 목록이 남아 있었고(`0/20`), `setTimeout` 은 **다음 매크로태스크**라 목록이 비어 있었다(`20/20`) ★★★

- ★★ node 는 HTML 이 아니지만 **같은 결과**였다 — 「node 도 체크포인트 끝에 비운다」 는 이 관찰에서 끌어낸 것이다(node 문서·소스는 확인하지 않았다).

### 7. **재실행마다 수가 바뀌었다** — node 20 은 콜백이 한 판이라도 온 벌이 다섯 중 `0\~1`, Chrome 은 칸마다 `3\~10 / 20` · 근거로 쓸 수 있는 것 — **`deref()` 가 `undefined` 인 판이 두 호스트 다섯 벌 모두 `0`** 이었다는 것과 **「콜백이 한 판이라도 온 벌이 있다」** 까지 ★★

**출력**

```text
===== ./js44b-47b-pressure.sh (exit=0) =====
--- node20
typeof gc: undefined · 20 rounds per cell · each cell is: deref() undefined / callback ran
       no wait          await null x1    await null x10   setTimeout 0
run 1  0 / 1            0 / 0            0 / 0            0 / 0
run 2  0 / 0            0 / 0            0 / 0            0 / 0
run 3  0 / 0            0 / 0            0 / 0            0 / 0
run 4  0 / 0            0 / 0            0 / 0            0 / 0
run 5  0 / 0            0 / 0            0 / 0            0 / 0
runs with deref() undefined in at least one round: 0 / 5 · runs with the callback in at least one round: 1 / 5
--- Chrome 151
typeof gc: undefined · 20 rounds per cell · each cell is: deref() undefined / callback ran
       no wait          await null x1    await null x10   setTimeout 0
run 1  0 / 4            0 / 10           0 / 10           0 / 10
run 2  0 / 10           0 / 10           0 / 10           0 / 10
run 3  0 / 10           0 / 10           0 / 10           0 / 10
run 4  0 / 10           0 / 10           0 / 10           0 / 10
run 5  0 / 10           0 / 10           0 / 10           0 / 10
runs with deref() undefined in at least one round: 0 / 5 · runs with the callback in at least one round: 5 / 5
```

- ★★ 「언제」 는 GC 가 **스스로** 정했다 — 이 탐침이 고정할 수 없는 칸이라 머리말 표에 흔들리는 칸으로 선언하고, 재대조는 이 줄들을 정규화한다(규칙 17 · 24).

### 8. **「비워졌다」 는 사실 자체** — `WeakMap` 은 키를 쥔 사람만 물을 수 있게 해서 **비워지는 순간이 프로그램에 안 새지만**(23번 — 들여다볼 창이 없다), `WeakRef.deref()` 는 **`undefined` 로 그 순간을 보인다** · 그래서 명세가 「언제」 를 묶지 않고 "may" 로 둔다 — GC 의 시점이 **관찰 가능해진** 대가다 ★★

- ★ 23번 머리말이 인용한 `WeakMap` 절의 이유 — 그 지연이 보이면 "a source of indeterminacy" 가 된다. `WeakRef` 는 그 비결정성을 **드러내 놓고** 준 API 다(이 연결은 이 문서의 해석이다).

### 9. CPython — **참조 계수가 0 이 되는 순간**(순환이 없으면 결정적) · JS — 기댈 순간이 **없다**(명세 may · `gc()` 없이는 0) · 대신 **명시적 해제** — `try`/`finally` · `close()` · 목록의 **51번 주제** `using` ★★

- ★ C++ 의 `weak_ptr` 도 결정적 쪽이다(C++ 28번). 「소멸 시점에 정리」 는 **결정적 수명**이 있는 언어의 관용구라 JS 로 그대로 옮기면 안 된다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js44b-47a-observe-grid.js` + `.sh` | ★★★ 8칸 × 20판 · 「`0 / 4`」 · 「`1 / 8`」 | node20 · node20 `--expose-gc` · node18 `--expose-gc` · Chrome 151 유무 — 다섯 판 |
| `js44b-47c-kept-alive.js` | ★★★ 다섯 지점 × 20판 | node20 `--expose-gc` · Chrome 151 `--js-flags` · node18(같음) |
| `js44b-47b-pressure-grid.js` + `.sh` | ★★ 흔들리는 칸 — 20판 × 다섯 벌 | node20 · Chrome 151 · ★ 재실행마다 수가 바뀐다 |
| `js44b-47d-registry-api.js` | ★ 등록·취소의 반환값 · 문구 | node20 · node18(문구 다름) · Chrome 151(같음) |
| `js44b-47e-python.py` | ★★ CPython 의 즉시 콜백 · 순환 | python3 3.12.3 · python3.11 3.11.15(같음) |

세 판 대조기(이 묶음의 plain 탐침). 이 주제는 **`47d` 한 줄만** 대조기에 넣었다(나머지는 플래그가 필요하거나 흔들린다 — `.sh` 가 직접 견준다). `47d` 는 **node 18 과 20 이 문구에서 갈렸다.**

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

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★★★ **「비워졌다」·「불렸다」 가 적힌 칸 전부**(1번의 `setTimeout` 행 · 2번 `[5]` · 7번)와 `await` 행(호스트가 목록을 비우는 자리). 명세 보장 칸(같은 턴의 `0/20` · `[3]`·`[4]`)은 판이 올라도 같아야 한다.
