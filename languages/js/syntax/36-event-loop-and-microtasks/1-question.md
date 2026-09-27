# js/syntax/36 — 이벤트 루프와 마이크로태스크: 「무엇이 먼저 도나, 그리고 누가 그 순서를 정하나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스) · Python 3.12 · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 한 파일을 세 호스트에 던진 순서 퍼즐 격자다** — **1번과 2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **동기 · 마이크로태스크 · 매크로태스크가 섞이면 어떤 순서로 찍히나**
> ② ★★★ **그 순서의 어느 칸을 언어가 정하고, 어느 칸을 호스트(HTML · node)가 정하나**
> ③ **마이크로태스크가 자기 자신을 다시 걸면 무엇이 굶나.**
>
> **선행** — [32](../32-error-handling-and-error/2-summary.md) · [20](../20-generators/2-summary.md) · [26](../26-array-search-flatten-and-create/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다. 각 줄의 **앞 두 글자(라벨)만** 적어도 된다.
- ★★★ **1번은 라벨 열한 개의 순서를 한 줄로** 적어라. 2번은 **1번과 달라지는 라벨만** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 순서는 ECMA-262 가 정하나, HTML 이 정하나, node 가 정하나**」.
- ★★★ **시간에 관한 답은 하나도 없다.** 「몇 ms 뒤」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 라벨 열한 개 — node CommonJS 에서 (예측) ★★★ 이 주제의 축

```js
// js36b-36-h-order.js
// One script for three hosts: node (CommonJS), node (ES module), Chrome.
// Every callback prints its own label. The order of the printed lines is the whole answer.
const log = (s) => console.log(s);
const tick = typeof process === "object" ? process.nextTick : undefined;

log("S1 sync, first line");
setTimeout(() => log("T1 setTimeout 0, scheduled first"), 0);
Promise.resolve().then(() => {
  log("P1 then, scheduled first");
  Promise.resolve().then(() => log("P3 then, scheduled from inside P1"));
});
queueMicrotask(() => log("Q1 queueMicrotask"));
if (tick) tick(() => log("N1 process.nextTick"));
(async () => {
  log("A1 async function, before its await");
  await undefined;
  log("A2 async function, after its await");
})();
setTimeout(() => log("T2 setTimeout 0, scheduled second"), 0);
Promise.resolve().then(() => log("P2 then, scheduled second"));
log("S2 sync, last line");
```

- ★★★ `node20 js36b-36-h-order.js` 로 돌리면 라벨 열한 개는 어떤 순서로 찍히나?
- ★★★ `P3` 는 `T1` 보다 먼저인가 나중인가? 왜?
- ★★ `A1` 은 `S2` 보다 먼저인가 나중인가?

### 2. 같은 파일을 ES 모듈로, 그리고 Chrome 에서 (예측) ★★★

```sh
# js36b-36a-order-grid.sh
#!/usr/bin/env bash
# The same file (js36b-36-h-order.js) in three hosts. A cell is the rank at which that host printed the label.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cjs="$("$N20" js36b-36-h-order.js | cut -c1-2)"
esm="$("$N20" --input-type=module < js36b-36-h-order.js | cut -c1-2)"
web="$(./js36b-browser.sh js36b-36-h-order.js | cut -c1-2)"
rank() { printf '%s\n' "$2" | grep -n -x "$1" | cut -d: -f1; }
printf '%-7s %-10s %-10s %-10s\n' "label" "node CJS" "node ESM" "Chrome 151"
moved=0; n=0
for l in $cjs; do
  a="$(rank "$l" "$cjs")"; b="$(rank "$l" "$esm")"; c="$(rank "$l" "$web")"
  printf '%-7s %-10s %-10s %-10s\n' "$l" "$a" "$b" "${c:--}"
  n=$((n + 1))
  [ "$a" = "$b" ] && [ "$a" = "${c:-x}" ] || moved=$((moved + 1))
done
echo ""
echo "labels not at the same rank in all three hosts: $moved / $n"
f() { printf '%s\n' "$1" | grep -v -x N1 | tr '\n' ' '; }
[ "$(f "$cjs")" = "$(f "$esm")" ] && [ "$(f "$esm")" = "$(f "$web")" ] && same=yes || same=no
echo "with N1 left out, the three orders are identical: $same"
[ "$("$N18" js36b-36-h-order.js)" = "$("$N20" js36b-36-h-order.js)" ] && s18a=same || s18a=DIFFERENT
[ "$("$N18" --input-type=module < js36b-36-h-order.js)" = "$("$N20" --input-type=module < js36b-36-h-order.js)" ] && s18b=same || s18b=DIFFERENT
echo "node18 against node20 -- CJS: $s18a · ESM: $s18b"
```

- ★★★ `node --input-type=module` 로 돌리면 1번의 순서에서 무엇이 움직이나?
- ★★★ Chrome 151 에서는? (`process` 가 없다 — `N1` 은 등록되지 않는다)
- ★★ 마지막 세 줄의 `N / M` · `yes`/`no` · `same`/`DIFFERENT` 는?

### 3. `setTimeout` 0 과 `setImmediate` — 300판 (예측) ★★

```js
// js36b-36-h-main.js
// Scheduled straight from the main module.
setTimeout(() => console.log("timeout"), 0);
setImmediate(() => console.log("immediate"));
```

```js
// js36b-36-h-io.js
// Scheduled from inside an I/O callback (readFile has finished).
require("fs").readFile(__filename, () => {
  setTimeout(() => console.log("timeout"), 0);
  setImmediate(() => console.log("immediate"));
});
```

```sh
# js36b-36b-timeout-vs-immediate.sh
#!/usr/bin/env bash
# Run each file 300 times and keep only the distinct orders (sort -u). The number of distinct orders is the answer.
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for f in js36b-36-h-main.js js36b-36-h-io.js; do
  runs="$(for i in $(seq 300); do "$N20" "$f" | paste -sd' ' -; done)"
  kinds="$(printf '%s\n' "$runs" | sort -u)"
  echo "--- $f · 300 runs · distinct orders: $(printf '%s\n' "$kinds" | wc -l)"
  printf '%s\n' "$kinds" | sed 's/^/    /'
done
```

- ★★★ 두 파일 각각, 300판에서 서로 다른 순서는 몇 가지이고 무엇인가?
- ★ 어느 쪽이 몇 번 나왔는지를 답에 적을 수 있나?

### 4. 스스로 다시 큐에 넣는 잡과 타이머 하나 (예측) ★★★

```js
// js36b-36c-starvation.js
// A job that queues itself again, stopped by a guard after n turns.
// At turn 1 a timer (setTimeout 0) is set. Question: how many times does that timer run while the loop is turning?
function trial(label, n, requeue) {
  return new Promise((done) => {
    let timerRuns = 0, turns = 0, seenAt = "-";
    const turn = () => {
      turns++;
      if (turns === 1) setTimeout(() => { timerRuns++; seenAt = turns; }, 0);
      if (turns < n) { requeue(turn); return; }
      const during = timerRuns;
      setTimeout(() => {
        console.log(label);
        console.log("  turns " + turns + " · timer runs while turning " + during + " · turns done when the timer ran " + seenAt);
        done();
      }, 0);
    };
    requeue(turn);
  });
}
(async () => {
  await trial("[1] requeue with queueMicrotask, n = 100000", 100000, (f) => queueMicrotask(f));
  await trial("[2] requeue with Promise.resolve().then, n = 100000", 100000, (f) => Promise.resolve().then(f));
  await trial("[3] requeue with setTimeout 0, n = 100", 100, (f) => setTimeout(f, 0));
})();
```

- ★★★ `[1]`·`[2]`·`[3]` 각각의 `timer runs while turning` 과 `turns done when the timer ran` 은?
- ★★ Chrome 151 에서 돌리면 달라지는 줄이 있나?

### 5. `process.nextTick` 이 자기 자신을 다시 걸면 (예측) ★★

```js
// js36b-36d-nexttick-starvation.js
// node only. process.nextTick requeues itself, stopped by a guard after n turns.
// At turn 1 a promise reaction (then) is queued. Question: how many times does it run while the loop is turning?
const n = 100000;
let turns = 0, thenRuns = 0, seenAt = "-";
const turn = () => {
  turns++;
  if (turns === 1) Promise.resolve().then(() => { thenRuns++; seenAt = turns; });
  if (turns < n) { process.nextTick(turn); return; }
  console.log("turns " + turns + " · then runs while turning " + thenRuns);
  setTimeout(() => console.log("turns done when the then callback ran " + seenAt), 0);
};
process.nextTick(turn);
```

- ★★ 두 줄의 숫자는?

### 6. 파이썬 `asyncio` 와 JS — 같은 등록 순서 (예측) ★★

```python
# js36b-36-h-onequeue.py
# asyncio: a callback, then a finished future's done-callback, then another callback -- in that order of scheduling.
import asyncio

async def main():
    loop = asyncio.get_running_loop()
    log = []
    loop.call_soon(log.append, "C1 call_soon, scheduled first")
    fut = loop.create_future()
    fut.add_done_callback(lambda f: log.append("F1 done-callback of a future"))
    fut.set_result(None)
    loop.call_soon(log.append, "C2 call_soon, scheduled second")
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    print("\n".join(log))

asyncio.run(main())
```

```js
// js36b-36-h-twoqueues.js
// The same shape in JS: a macrotask, a promise reaction, another macrotask -- in that order of scheduling.
const log = [];
setTimeout(() => log.push("C1 setTimeout 0, scheduled first"), 0);
Promise.resolve().then(() => log.push("F1 then of a fulfilled promise"));
setTimeout(() => log.push("C2 setTimeout 0, scheduled second"), 0);
setTimeout(() => console.log(log.join("\n")), 0);
```

- ★★★ 두 프로그램은 각각 `C1` · `F1` · `C2` 를 어떤 순서로 찍나?

### 7. 마이크로태스크는 왜 「하나」가 아니라 「전부」 도나 (왜) ★★★

- ★★★ HTML 의 마이크로태스크 체크포인트는 큐를 언제까지 비우나? 그 글자는?
- ★★ 그 규칙에서 1번의 `P3` 와 4번의 `0` 이 어떻게 나오나?
- ★ 체크포인트가 끝난 뒤, 다음 태스크 전에 하는 일 하나는(37번과 이어지는 것)?

### 8. ECMA-262 가 보장하는 것은 어디까지인가 (경계) ★★★

- ★★★ 언어 명세가 프라미스 잡의 순서에 대해 적는 한 문장은?
- ★★ 「태스크 하나 → 마이크로태스크 전부」라는 모양은 언어 명세에 있나?
- ★★ `HostEnqueueTimeoutJob` 이 시간에 대해 말하는 것은 「정확히」인가 「적어도」인가?
- ★ `queueMicrotask` · `setTimeout` · `setImmediate` · `process.nextTick` 은 각각 누구의 것인가?

### 9. ES 모듈에서 `nextTick` 이 뒤로 가는 이유 (왜) ★★

- ★★ node 문서는 CommonJS 와 ES 모듈의 차이를 무엇으로 설명하나?
- ★ 그래서 「`nextTick` 은 마이크로태스크보다 먼저」는 언제 참인가?

### 10. 양보하려면 무엇으로 다시 거나 · 무엇을 재지 않았나 (경계) ★

- ★★ 긴 작업을 쪼개 다른 태스크에 차례를 넘기려면 무엇으로 다시 걸어야 하나? 4번의 어느 줄이 근거인가?
- ★ 이 문서가 **재지 않은** 것 둘은(화면 쪽 · 시간 쪽)?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
