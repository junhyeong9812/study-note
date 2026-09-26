# js/syntax/38 — Promise 조합기: 「`all` 전부·첫 거부 · `allSettled` 전부 · `race` 첫 확정 · `any` 첫 이행 — 취소는 없다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Chrome 151**(헤드리스) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js36b-38a-combinator-grid.js`(1번 · 5번) · `js36b-38b-no-cancel.js`(2번 · 6번) · `js36b-38-h-race-ready.js` + `js36b-38d-race-ready.sh`(3번 · 8번) · `js36b-38c-resolvers-try.web.js`(4번) · `js36b-38e-endless.js`(7번).

## 정답

### 1. 일찍 끝난 칸 **`7 / 16`**, 끝내 안 끝난 칸 **`1 / 16`**(`race([])`) ★★★

**출력**

```text
===== node20 js36b-38a-combinator-grid.js (exit=0) =====
--- all fulfil
  all        at step 3      fulfilled ["v0","v1","v2"]
  allSettled at step 3      fulfilled [fulfilled,fulfilled,fulfilled]
  race       at step 1      fulfilled "v0"
  any        at step 1      fulfilled "v0"
--- one rejects
  all        at step 2      rejected  Error 「e1」
  allSettled at step 3      fulfilled [fulfilled,rejected,fulfilled]
  race       at step 1      fulfilled "v0"
  any        at step 1      fulfilled "v0"
--- all reject
  all        at step 1      rejected  Error 「e0」
  allSettled at step 3      fulfilled [rejected,rejected,rejected]
  race       at step 1      rejected  Error 「e0」
  any        at step 3      rejected  AggregateError 「All promises were rejected」 errors 3
--- empty
  all        at step 0      fulfilled []
  allSettled at step 0      fulfilled []
  race       never settled  pending
  any        at step 0      rejected  AggregateError 「All promises were rejected」 errors 0
cells settled before their last input settled: 7 / 16 · cells never settled: 1 / 16
```

**왜 그런가**

- ★★★ **전부 이행** — `all`·`allSettled` 는 3단계, `race`·`any` 는 1단계(`"v0"`).
- ★★★ **하나 거부(2단계)** — `all` 은 **2단계에 `Error 「e1」`**, `allSettled` 는 3단계에 목록, `race`·`any` 는 1단계에 `"v0"`.
- ★★★ **전부 거부** — `all`·`race` 는 **1단계에 `Error 「e0」`**, `allSettled` 는 3단계에 목록(**거부하지 않는다**), `any` 는 **3단계에 `AggregateError … errors 3`**.
- ★★★ **빈 입력** — `all`·`allSettled` 는 **0단계에 `[]`**, **`race` 는 `never settled`**, `any` 는 **0단계에 `AggregateError … errors 0`**.

### 2. `>> all rejected` 는 **`A step 3` 뒤**에 찍히고, 그 뒤로 **8 줄** — `race` 도 **8** ★★★

**출력**

```text
===== node20 js36b-38b-no-cancel.js (exit=0) =====
--- Promise.all
  A start
  B start
  C start
  A step 1
  B step 1
  C step 1
  A step 2
  C step 2
  A step 3
  >> all rejected Error 「B failed」
  C step 3
  A step 4
  C step 4
  A step 5
  C step 5
  C finished
  A step 6
  A finished
  lines printed by the jobs after the combinator settled: 8
--- Promise.race
  A start
  B start
  C start
  A step 1
  B step 1
  C step 1
  A step 2
  C step 2
  A step 3
  >> race rejected Error 「B failed」
  C step 3
  A step 4
  C step 4
  A step 5
  C step 5
  C finished
  A step 6
  A finished
  lines printed by the jobs after the combinator settled: 8
```

**왜 그런가**

- ★★★ 조합기는 결과 프라미스를 **확정할 뿐** 입력에게 아무 말도 안 한다 — `A` 와 `C` 는 `finished` 까지 간다.
- ★★ `B step 1` 과 `>>` 사이에 **네 줄**이 끼었다 — `B` 의 거부가 결과 프라미스를 지나 처리기에 닿기까지 틱을 먹는다(37번의 흡수 규칙).

### 3. 두 순서 모두 **가짓수 `1`** — `[a, b]` 는 **`a`**, `[b, a]` 는 **`b`** ★★

**출력**

```text
===== ./js36b-38d-race-ready.sh (exit=0) =====
[ab] 200 runs · distinct results 1 : a
[ba] 200 runs · distinct results 1 : b
```

**왜 그런가**

- ★★ `race` 는 넘긴 순서대로 `then` 을 걸고, 이미 이행한 입력의 반응 잡은 **건 순서대로** 돈다. 먼저 돈 쪽이 결과를 확정하고, 뒤의 것은 무시된다.

### 4. `withResolvers` 는 **세 키** · `try` 와 executor 는 **콜백이 먼저**, `then(f)` 은 **`call returned` 가 먼저** — 셋 다 거부로 받는다 · `Promise.resolve(f())` 는 **호출한 자리로 던진다** ★★

**출력**

```text
===== ./js36b-browser.sh js36b-38c-resolvers-try.web.js (exit=0) =====
[1] Promise.withResolvers()
  own keys ["promise","resolve","reject"] · promise instanceof Promise true
  awaited "from a timer"
  after resolve and reject once more "from a timer"
[2] when does the callback run, and where does its throw go?
 Promise.try(f)
  callback runs (t)
  call returned
  awaited promise rejected with Error 「t」
 Promise.resolve().then(f)
  call returned
  callback runs (r)
  awaited promise rejected with Error 「r」
 new Promise((res) => res(f()))
  callback runs (n)
  call returned
  awaited promise rejected with Error 「n」
[3] Promise.try passes the extra arguments
  5
[4] Promise.resolve(f()) with the same kind of f
  callback runs (p)
  thrown at the call site: Error 「p」
```

**왜 그런가**

- ★★ `[1]` — own 키 `["promise","resolve","reject"]` · `instanceof Promise true` · 타이머가 준 `"from a timer"` · 두 번째 `resolve`·`reject` 는 **무시**(37번의 「처음 것만」).
- ★★★ `[2]` — `Promise.try(f)` 는 `f` 를 **호출 안에서** 부른다(`callback runs (t)` → `call returned`). `then(f)` 은 **다음 틱**이다. 셋 다 `f` 의 `throw` 를 **거부**로 바꾼다.
- ★★ `[3]` — **`5`**(인자를 넘긴다). `[4]` — `f()` 가 **프라미스보다 먼저** 돌아 `thrown at the call site: Error 「p」`.

### 5. 남은 수는 **1 에서 시작해 입력마다 +1, 다 읽은 뒤 −1** — 빈 입력이면 **읽자마자 0** · `race` 에는 **그 수가 없다** ★★★

- ★★★ 0 이 되는 순간 `all`·`allSettled` 는 결과 배열로 이행하고 `any` 는 `AggregateError` 로 거부한다 — 빈 입력이면 **곧바로**(0단계).
- ★★ `race` 는 입력마다 `then(resolve, reject)` 를 걸 뿐 **세지 않는다** — 입력이 없으면 확정할 계기가 없다. 노트: 「**iterable 이 값을 하나도 내지 않으면 … 돌려준 pending 프라미스는 영원히 확정되지 않는다.**」

### 6. 조합기는 **결과 프라미스를 확정할 뿐** — 입력을 시작시킨 것은 **배열을 만든 식** ★★★

- ★★★ 하는 일 — 입력마다 `then` 을 걸어 **결과**를 모은다. 하지 않는 일 — 입력에게 **멈추라고 알리는 것.** 명세의 네 알고리즘에 그런 단계가 없고, 프라미스에는 취소가 없다.
- ★★ `[job("A", 6), job("B", 1, 1), job("C", 5)]` 가 **평가될 때** 셋이 이미 시작했다(`start` 세 줄이 먼저). 조합기는 **돌고 있는 것을 받았다.**

### 7. **`100000`** 번 `next()` 를 부른 뒤에야 돌아왔고, **던지지 않고** 거부된 프라미스를 돌려줬다 ★★

**출력**

```text
===== node20 js36b-38e-endless.js (exit=0) =====
Promise.all returned after 100000 next() calls · a Promise
rejected with RangeError 「guard: stopped at next #100000」
```

**왜 그런가**

- ★★★ `Promise.all` 은 이터러블을 **호출 안에서 동기로** 끝까지 읽는다 — 가드가 10만 번째에서 던질 때까지 **호출이 돌아오지 않았다.** 가드가 없으면 **영영** 안 돌아온다.
- ★★ 읽다가 난 예외는 **던지지 않고 거부**로 바꾼다(명세의 `IfAbruptRejectPromise`) — `rejected with RangeError 「guard: …」`.
- ★★ [19번](../19-iterable-protocol-and-for-of/2-summary.md) 동작 (1)의 `[4]` — 호출 직후 로그가 이미 **`next#4 done`** 까지 차 있었다. 19번이 「돌려 보지 않았다」로 남긴 끝없는 경우를 이 탐침이 **가드 안에서** 돌렸다.
- ★ [26번](../26-array-search-flatten-and-create/2-summary.md) 동작 (7)의 `[2]` — `Array.fromAsync` 는 **`next 0 | settle 0 | next 1 | …`**(하나씩), `Promise.all([...gen()])` 은 **`next 0 | next 1 | next 2 | settle …`**(다 꺼낸 뒤).

### 8. JS `race` 는 **먼저 넘긴 것**(가짓수 1), Go `select` 는 **무작위**(가짓수 2) — 둘 다 **명세**가 정한다 ★★

- ★★ JS 는 잡이 **등록 순서대로** 돈다는 ECMA-262 의 규칙에서, Go 는 「준비된 가지 중 **균등 무작위**」라는 Go 명세의 규칙에서 나온다([Go 30](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) 동작 (1)).

### 9. `allSettled` **ES2020** · `any` **ES2021** · `withResolvers` **ES2024** · `try` **ES2025** — 두 node 판에는 **뒤의 둘이 없다** ★★

- ★★ finished proposals 표와 README 가 같다. 판별 블록에서 두 node 판이 `ES2024`·`ES2025` 줄에 `no`.
- ★ **`AggregateError`** — `errors` 는 **입력 순서대로** 이유를 든다. 정본은 [32번](../32-error-handling-and-error/2-summary.md) 동작 (5).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js36b-38a-combinator-grid.js` | ★★★ 16칸 · 「`7 / 16` · `1 / 16`」 · 빈 입력 행 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-38b-no-cancel.js` | ★★★ 조합기 뒤 `8` 줄 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-38-h-race-ready.js` + `js36b-38d-race-ready.sh` | ★★ 가짓수 `1`·`1` | node20 순서마다 200판 |
| `js36b-38c-resolvers-try.web.js` | ★★ `withResolvers` · `try` | Chrome 151 1벌 |
| `js36b-38e-endless.js` | ★★ 끝없는 이터러블 — `100000` 번 뒤에 거부로 돌아온다 | node20 1벌 + node18 대조 + Chrome(대조기) |
| `js36b-versions.sh` · `js36b-vdiff.sh` | 판별 기능 표 · 갈린 탐침 수 | 1벌씩 |

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

- ★★ **node 22 이상** — `withResolvers`·`try` 가 들어오면 4번을 node 로도 돌린다(이 머신에 없다).
- ★ `AggregateError` 의 문구 `All promises were rejected` — V8 의 글자다.
