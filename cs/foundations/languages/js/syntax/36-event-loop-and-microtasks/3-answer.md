# js/syntax/36 — 이벤트 루프와 마이크로태스크: 「동기 → 마이크로태스크 전부 → 매크로태스크 하나 · 순서의 층이 둘」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스) · Python 3.12 · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js36b-36-h-order.js` + `js36b-36a-order-grid.sh`(1번 · 2번) · `js36b-36-h-main.js` · `js36b-36-h-io.js` + `js36b-36b-timeout-vs-immediate.sh`(3번) ·
> `js36b-36c-starvation.js`(4번) · `js36b-36d-nexttick-starvation.js`(5번) · `js36b-36-h-onequeue.py` · `js36b-36-h-twoqueues.js` + `js36b-36e-python-contrast.sh`(6번).

## 정답

### 1. `S1 A1 S2 N1 P1 Q1 A2 P2 P3 T1 T2` ★★★

**출력**

```text
===== ./js36b-36a-order-grid.sh (exit=0) =====
label   node CJS   node ESM   Chrome 151
S1      1          1          1         
A1      2          2          2         
S2      3          3          3         
N1      4          9          -         
P1      5          4          4         
Q1      6          5          5         
A2      7          6          6         
P2      8          7          7         
P3      9          8          8         
T1      10         10         9         
T2      11         11         10        

labels not at the same rank in all three hosts: 8 / 11
with N1 left out, the three orders are identical: yes
node18 against node20 -- CJS: same · ESM: same
```

**왜 그런가**

- ★★★ **`node CJS` 열이 1번의 답이다** — `S1`(1) `A1`(2) `S2`(3) `N1`(4) `P1`(5) `Q1`(6) `A2`(7) `P2`(8) `P3`(9) `T1`(10) `T2`(11).
- ★★★ **동기 코드가 끝까지**(`S1 A1 S2` — `async` 본문은 첫 `await` 까지 동기) → **`nextTick` 큐**(node CJS) → **마이크로태스크를 등록 순서대로, 빌 때까지**(`P1 Q1 A2 P2`, 그리고 `P1` 이 도는 중에 붙은 `P3`) → **타이머를 등록 순서대로**(`T1 T2`).
- ★★★ **`P3` 가 `T1` 보다 먼저**다 — 체크포인트는 「큐가 비어 있지 않은 동안」 꺼내므로 **도중에 붙은 마이크로태스크도 같은 비우기에서** 돈다.

### 2. ES 모듈은 **`N1` 만 9위로** 내려가고, Chrome 은 **`N1` 이 없을 뿐 나머지 순서가 같다** — `8 / 11` · `yes` · `same`/`same` ★★★

**출력** — 1번과 같은 블록이다(`node ESM` 열 · `Chrome 151` 열 · 마지막 세 줄).

**왜 그런가**

- ★★★ **ES 모듈** — `N1` 이 **4위에서 9위**로 간다(마이크로태스크 다섯 뒤, 타이머 앞). node 문서: 「**ESM 은 이미 마이크로태스크 큐의 일부로 처리되므로 `queueMicrotask()` 콜백이 먼저 돈다.**」
- ★★★ **Chrome 151** — `N1` 이 없다(`-`). 나머지 열 라벨은 **CJS·ESM 과 같은 상대 순서**다.
- ★★ **`labels not at the same rank in all three hosts: 8 / 11`** — 갈린 여덟 칸은 **전부 `N1` 이 끼어든 자리 때문**이다. `N1` 을 빼면 **세 순서가 같다**(`yes`). 두 node 판도 두 모드 모두 `same`.

### 3. 메인 모듈은 **두 가지**(`immediate timeout` · `timeout immediate`), I/O 콜백 안은 **한 가지**(`immediate timeout`) ★★

**출력**

```text
===== ./js36b-36b-timeout-vs-immediate.sh (exit=0) =====
--- js36b-36-h-main.js · 300 runs · distinct orders: 2
    immediate timeout
    timeout immediate
--- js36b-36-h-io.js · 300 runs · distinct orders: 1
    immediate timeout
```

**왜 그런가**

- ★★★ **메인 모듈** — libuv 가 첫 timers 단계에 닿았을 때 **1ms 가 이미 지났느냐**에 달려서 **판마다** 바뀐다(node 문서의 「non-deterministic」).
- ★★ **I/O 콜백 안** — 그 콜백은 poll 단계에서 돈다. **다음 단계가 check** 이므로 `setImmediate` 가 **늘 먼저**다.
- ★ **몇 번씩인지는 적을 수 없다** — 비율은 판마다 흔들린다. **가짓수만** 근거다(규칙 11).

### 4. `[1]`·`[2]` 는 **`0` · `100000`**, `[3]` 은 **`1` · `1`** — Chrome 도 **한 글자도 같다** ★★★

**출력**

```text
===== node20 js36b-36c-starvation.js (exit=0) =====
[1] requeue with queueMicrotask, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[2] requeue with Promise.resolve().then, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[3] requeue with setTimeout 0, n = 100
  turns 100 · timer runs while turning 1 · turns done when the timer ran 1
```

```text
===== ./js36b-browser.sh js36b-36c-starvation.js (exit=0) =====
[1] requeue with queueMicrotask, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[2] requeue with Promise.resolve().then, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[3] requeue with setTimeout 0, n = 100
  turns 100 · timer runs while turning 1 · turns done when the timer ran 1
```

**왜 그런가**

- ★★★ **마이크로태스크로 다시 걸면**(`queueMicrotask` · `then` 둘 다) 체크포인트가 **10만 바퀴 동안 안 끝난다** — 타이머는 **한 번도** 못 돌고, 가드가 멈춘 뒤에야 돈다.
- ★★★ **`setTimeout` 0 으로 다시 걸면** 바퀴마다 태스크가 바뀌므로 turn 1 이 건 타이머가 **turn 1 바로 다음**에 돈다.
- ★★ **Chrome 151 도 같다** — HTML 의 「빌 때까지」와 node 의 구현이 같은 답을 냈다.

### 5. `then runs while turning 0` · `turns done when the then callback ran 100000` ★★

**출력**

```text
===== node20 js36b-36d-nexttick-starvation.js (exit=0) =====
turns 100000 · then runs while turning 0
turns done when the then callback ran 100000
```

**왜 그런가**

- ★★ node 는 **`nextTick` 큐를 빌 때까지** 비운 뒤에 프라미스 큐로 간다(CommonJS 의 모양) — `nextTick` 이 자기 자신을 다시 걸면 **프라미스 콜백이 굶는다.** node 의 것이다.

### 6. 파이썬은 **`C1 → F1 → C2`**(등록 순서), JS 는 **`F1 → C1 → C2`**(마이크로태스크가 앞지른다) ★★

**출력**

```text
===== ./js36b-36e-python-contrast.sh (exit=0) =====
--- python3 3.12 js36b-36-h-onequeue.py
C1 call_soon, scheduled first
F1 done-callback of a future
C2 call_soon, scheduled second
--- node20 js36b-36-h-twoqueues.js
F1 then of a fulfilled promise
C1 setTimeout 0, scheduled first
C2 setTimeout 0, scheduled second
```

**왜 그런가**

- ★★★ `asyncio` 는 future 의 완료 콜백도 `call_soon` 과 **같은 ready 큐**에 넣는다 — 우선순위가 높은 둘째 줄이 없다.
- ★★ JS 의 `then` 콜백은 **마이크로태스크**라서 먼저 등록된 타이머(`C1`)를 **앞지른다.**

### 7. 「**While the event loop's microtask queue is not empty**」 — 빌 때까지 ★★★

- ★★★ 체크포인트는 큐가 **빌 때까지** 가장 오래된 것부터 꺼낸다. 도중에 붙은 것도 같은 루프가 꺼낸다.
- ★★ 그래서 1번에서 **`P1` 이 붙인 `P3`** 가 타이머보다 먼저 돌고, 4번에서 **스스로 다시 붙는 잡**이 루프를 끝내지 않아 타이머가 **0 번** 돈다.
- ★ 체크포인트 끝에서 HTML 은 **미처리 거부를 알린다**(`notify about rejected promises`) — [37번](../37-promise-state-model/2-summary.md) 동작 (5)가 정본이다.

### 8. 언어는 **「잡은 등록 순서대로」** 까지 — 한 바퀴의 모양은 **호스트** ★★★

- ★★★ 「**Jobs must run in the same order as the `HostEnqueuePromiseJob` invocations that scheduled them.**」
- ★★ **없다.** 「태스크 하나 → 마이크로태스크 전부」는 **HTML event loop** 의 모양이고, node 는 **libuv 위에서** 같은 모양을 따로 구현한다.
- ★★ **「적어도」**(after **at least** milliseconds). 정확한 시점은 호스트의 몫이다 — 이 문서는 ms 를 **재지 않았다.**
- ★ `queueMicrotask` · `setTimeout` → **HTML**(node 도 구현) · `setImmediate` · `process.nextTick` → **node**.

### 9. ES 모듈의 본문은 **이미 마이크로태스크를 비우는 중에** 돈다 ★★

- ★★ node 문서 — 「**CJS 에서는 `process.nextTick()` 콜백이 항상 `queueMicrotask()` 콜백보다 먼저. ESM 은 이미 마이크로태스크 큐의 일부로 처리되므로 거기서는 `queueMicrotask()` 콜백이 먼저.**」
- ★ **CommonJS 에서만** 참이다 — 2번의 `N1` 이 4위(CJS) 대 9위(ESM).

### 10. **매크로태스크**로 다시 건다 — 4번 `[3]` 의 `timer runs while turning 1` · 재지 않은 것은 **렌더링과 시간** ★

- ★★ `setTimeout(f, 0)`(브라우저라면 `MessageChannel` 도 알려져 있다 — 이 문서는 돌리지 않았다) · node 의 `setImmediate`. 마이크로태스크로 걸면 **양보가 아니다**(4번 `[1]`·`[2]`).
- ★ **화면** — `requestAnimationFrame`·렌더링 시점은 세지 않았다. **시간** — `setTimeout(f, 0)` 이 몇 ms 뒤에 도는지 재지 않았다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js36b-36-h-order.js` + `js36b-36a-order-grid.sh` | ★★★ 라벨 11 × 호스트 3 격자 · 「`8 / 11`」 · `N1` 을 빼면 같다 | node20 CJS·ESM · Chrome 151 각 1벌 + node18 CJS·ESM 대조 |
| `js36b-36-h-main.js` · `js36b-36-h-io.js` + `js36b-36b-timeout-vs-immediate.sh` | ★★ 가짓수 `2` · `1` | node20 각 300판 |
| `js36b-36c-starvation.js` | ★★★ 기아 — 타이머 0 회 · 매크로태스크면 1 회 | node20 1벌 + node18 대조 + Chrome 151 1벌 |
| `js36b-36d-nexttick-starvation.js` | ★★ `nextTick` 기아 | node20 1벌 + node18 대조 |
| `js36b-36-h-onequeue.py` · `js36b-36-h-twoqueues.js` + `js36b-36e-python-contrast.sh` | ★★ 줄 하나 대 둘 | Python 3.12 · node20 1벌씩 |
| `js36b-vdiff.sh` · `js36b-versions.sh` | 두 node 판 · Chrome 이 갈린 탐침 수 · 판별 기능 표 | 1벌씩 |

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

- ★★ **`nextTick` 의 자리**(CJS 4위 · ESM 9위) — node 의 것이다. node 가 모듈 적재 방식을 바꾸면 다시 돌린다.
- ★★ **가짓수 `2`·`1`** — libuv 의 단계 순서와 기계 사정에 매인다.
- ★ **Chrome 쪽 블록은 가상 시간 예산 아래에서** 떴다(`--virtual-time-budget=2000`) — 순서만 싣고 시간은 싣지 않은 이유다.
