# web-api/37 — `MutationObserver`: 관측 옵션 · 레코드 묶음 · 마이크로태스크 타이밍 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「디스패치 계수기」를 두 방향으로 돌린 것이다** — ① **묶음 · 타이밍 로그**(한 동기 블록의 변경 다섯 번이 콜백 몇 번 · 레코드 몇 개로 오나, `then` · `setTimeout` 과 어느 순서인가 — `then` 을 거는 자리만 바꾼 세 판)와 ② **옵션 격자**(옵션 아홉 벌 × 변경 일곱 가지 = 63칸 — 칸마다 레코드가 왔나). 스크립트가 **「레코드가 온 칸 N / M」 · 「subtree 가 바꾼 칸 N / M」** 을 마지막 줄로 찍는다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/#mutation-observers) §4.3 — 「queue a mutation observer microtask」(**이미 걸려 있으면 그냥 돌아간다**) · 「notify mutation observers」(레코드가 **비어 있지 않을 때만** 콜백) · `observe(target, options)` 의 단계(`TypeError` 넷) · `disconnect()`(레코드 큐를 비운다) · 「queue a mutation record」(`subtree` · `attributeFilter` 판정) · §4.9 「change an attribute」(값을 비교하지 않는다). 받아서 읽은 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 하네스는 [36번 주제](../36-resize-observer/3-answer.md)의 `wa36b-net.py` 다(이 편은 부탁 창구를 안 쓴다 — 페이지가 돌려준 글만 찍는다).\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** 이 편의 관찰은 **명세 알고리즘과 전부 맞았다**(이탈 0).\
> **선행** — ★★ **[03번 주제](../03-node-creation-insertion-removal/2-summary.md)** — 노드를 넣는 법 다섯과 **「삽입이 곧 이동」**. 여기서는 그 삽입 · 이동이 **레코드 몇 개로 보이나**를 센다((5)). ★ [05번 주제](../05-documentfragment-and-template/2-summary.md)가 이미 이 관찰자로 **조각 한 번 = 레코드 1개 대 반복 세 번 = 레코드 3개**를 쟀다 — 다시 재지 않는다.\
> ★ **JS 쪽 선행** — [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md) (1)이 「**마이크로태스크는 등록한 순서대로**」(`P1 → Q1 → A2 → P2`)를 이미 쟀다. 이 편은 **MO 콜백이 그 줄의 어디에 서나**만 잰다.\
> **경계** — 「마이크로태스크 대 태스크 대 렌더」의 브라우저 전체 순서는 목록의 **40번 주제**(폴더는 아직 없다)의 몫이다. 옛 **Mutation events**(`DOMNodeInserted` 등)는 「MO 가 대체한 것」으로만 둔다 — 던지지 않았다. ★ 「남의 스크립트가 만든 노드에 반응하기」((6))는 **설계 권고층**이다.\
> 이 본문은 Claude 작성이다(원고 없음). 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 묶음 로그 세 판 · 옵션 격자 63칸 · 집계 두 줄 · 잘못된 옵션 다섯 줄(`TypeError` 넷 · 통과 하나) · 가장자리 일곱 줄 · 남의 노드 네 줄 | 캡처 세 판이 **한 글자도 같았다** — 시간을 하나도 안 찍는다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 **없다.**

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 트리의 최종 모양은 묻지 않는다 — 묻는 것은 **바뀐 사건**이다 |
| 창 ② 노드 프로브 | ★ **쓴다** | `MutationRecord` 의 `type` · `oldValue` · `addedNodes` · `removedNodes` · `target` |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 같은 변경 다섯을 **`then` 자리만 바꿔 세 판** · 같은 변경 일곱을 **옵션 아홉 벌로** |
| **창 ④ 디스패치 계수기 → 묶음 로그 · 옵션 격자** | ★★★ **본체** | 콜백 **몇 번** · 레코드 **몇 개** · **어느 순서** · 칸마다 **왔나** |
| ★ **`takeRecords()` 로 큐를 직접 읽기** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 옵션 격자는 콜백을 기다리지 않고 **변경 직후 `takeRecords()`** 로 레코드 큐를 읽었다 — 63칸을 **한 태스크 안에서** 결정적으로 채우려고. ★ 바꾼 창이 못 보는 것 — **콜백이 언제 · 몇 번 불리나**. 그것은 ① 묶음 로그가 따로 잰다 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **비용** — 관찰자가 붙은 트리에서 DOM 을 바꾸는 값 | **재지 않았다** |
| **렌더링과의 순서** | 목록의 **40번 주제**의 몫 |
| **그림자 트리 · `slotchange`** | 던지지 않았다 — 명세의 「notify mutation observers」는 `slotchange` 도 같은 자리에서 쏜다 |
| **옛 Mutation events** | 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ `MutationObserver` 는 「우편함에 쌓이는 변경 통지서」다. 집(DOM)이 바뀔 때마다 통지서(레코드)가 한 장씩 우편함(레코드 큐)에 들어가지만, 집배원(콜백)은 지금 하던 일(동기 코드)이 끝난 직후에 한 번 와서 쌓인 것을 한 묶음으로 건네준다. 집배원의 방문 예약은 첫 통지서가 들어간 순간 잡힌다 — 그 전에 잡아 둔 다른 약속(`then`)이 있으면 그쪽이 먼저다. 무엇을 받아 볼지는 신청서(옵션)에 적는다 — 「방 배치(`childList`)」 · 「문패(`attributes`)」 · 「벽에 쓴 글(`characterData`)」, 그리고 「뒷방까지(`subtree`)」.**

| 비유 | 실체 |
|---|---|
| 통지서 한 장 | `MutationRecord` — 변경 한 번(대입 하나가 여러 노드를 바꿔도 한 장일 수 있다) |
| 우편함 | 관찰자의 레코드 큐 |
| 집배원의 한 번 방문 | 콜백 한 번 — 쌓인 레코드 **배열**을 받는다 |
| 방문 예약 | 「queue a mutation observer microtask」 — **첫 변경 때 한 번만** 마이크로태스크를 건다 |
| 신청서 | `observe(target, { childList · attributes · characterData · subtree · …OldValue · attributeFilter })` |
| 우편함을 직접 열어 보기 | `takeRecords()` — 꺼내면 비고, 비면 집배원이 안 온다 |

```text
   한 동기 블록 — 변경 다섯 번 (이 판)

   동기 코드     setAttribute · append · setAttribute · append · setAttribute   → 「동기 끝」
                  │ 첫 변경에서 MO 마이크로태스크를 예약(한 번만)
   마이크로태스크 [ (앞서 건 then) · MO 알림 · (뒤에 건 then) ]      ← 줄 선 순서대로
                  MO 콜백 1번 · 레코드 5개
   태스크         setTimeout
```

## 이 주제가 답하려는 질문

1. **통지는 언제 · 몇 번 오나** — 변경 다섯 번에 콜백 몇 번 · 레코드 몇 개, `then` · `setTimeout` 과의 순서.
2. **옵션은 무엇을 가르나** — 아홉 벌 × 변경 일곱. 옵션을 잘못 주면 무엇이 나오나.
3. **레코드 큐의 가장자리** — 콜백 전에 비우기 · 끊기 · 같은 값 · 대입 한 번 · 이동. 그리고 남의 스크립트가 만든 노드에 반응하는 형태.

## 동작 방식

### (1) ★★★ 묶음 · 타이밍 로그

**같은 관찰자 · 같은 변경 다섯**(속성 셋 · 자식 붙이기 둘)을 세 판 돌린다. 판마다 **`Promise.resolve().then` 을 거는 자리만** 다르다. `setTimeout 0` 은 판 첫머리에 건다.

```html
<!-- wa36b-37-batch.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>37 batch</title>
<div id="host"></div>
<script>
// 한 동기 블록에서 DOM 을 다섯 번 바꾼다 — 콜백은 몇 번 · 레코드는 몇 개 · 그리고 동기 코드 · then · setTimeout 과의 순서
// 판 가: then 을 첫 변경 「전」에 건다 · 판 나: 첫 변경 「뒤」에 건다 · 판 다: 변경 사이에 건다
const host = document.getElementById("host");
const 한판 = (이름, 차례) => new Promise(끝 => {
  const 로그 = [];
  const mo = new MutationObserver(rs => 로그.push(`MO 콜백(레코드 ${rs.length}개: ${rs.map(r => r.type).join(",")})`));
  mo.observe(host, { childList: true, attributes: true });
  setTimeout(() => { 로그.push("setTimeout"); mo.disconnect(); host.replaceChildren(); 끝(이름 + "\t" + 로그.join(" → ")); }, 0);
  const 바꾸기 = k => { if (k % 2) host.setAttribute("data-k", String(k)); else host.append(document.createElement("i")); };
  for (const 할일 of 차례) {
    if (할일 === "then") Promise.resolve().then(() => 로그.push("then"));
    else 바꾸기(할일);
  }
  로그.push("동기 끝");
});
window.__끝 = async () => {
  const 줄 = [];
  줄.push(await 한판("가 then → 변경 5번", ["then", 1, 2, 3, 4, 5]));
  줄.push(await 한판("나 변경 5번 → then", [1, 2, 3, 4, 5, "then"]));
  줄.push(await 한판("다 변경 → then → 변경 4번", [1, "then", 2, 3, 4, 5]));
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-37-batch.html
가 then → 변경 5번	동기 끝 → then → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → setTimeout
나 변경 5번 → then	동기 끝 → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → then → setTimeout
다 변경 → then → 변경 4번	동기 끝 → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → then → setTimeout
(exit 0)
```

- ★★★ **세 판 다 콜백 1번 · 레코드 5개**(`attributes,childList,attributes,childList,attributes` — 바꾼 순서 그대로). 변경마다 즉시 오지 않고 **동기 코드가 끝난 뒤 한 묶음**으로 왔다.
- ★★★ **가 — `then` 을 첫 변경 전에 걸면 `then → MO`**, **나 — 다 바꾼 뒤에 걸면 `MO → then`**, **다 — 첫 변경과 둘째 변경 사이에 걸어도 `MO → then`** 이고 MO 는 **레코드 5개**를 받았다.
- ★★★ **다의 뜻** — MO 알림은 **첫 변경 때 마이크로태스크 줄에 한 번 섰고**, 뒤의 네 변경은 **자리를 새로 잡지 않고 레코드만 보탰다.** DOM 명세의 글자가 「**If the surrounding agent's mutation observer microtask queued is true, then return.**」 이다. `then` 과 MO 는 **같은 마이크로태스크 줄에 선 순서대로** 돈다 — JS 36편 (1)의 「등록한 순서대로」와 같은 줄이다.
- ★★ **`setTimeout` 은 세 판 다 맨 끝** — 태스크는 마이크로태스크가 다 빠진 뒤다.

### (2) ★★★ 옵션 격자

**칸마다 새 나무**(`host > [글 「처음」 , child > 글 「처음」]`)를 만들고 **host** 를 관찰한다. 변경 한 번 뒤 **`takeRecords()`** 로 큐를 읽는다(제5의 상태 — 머리말).

```html
<!-- wa36b-37-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>37 grid</title>
<script>
// 옵션 격자 — observe 옵션 아홉 벌 × 변경 일곱 가지. 칸마다 새 나무(host > 글 · child > 글)를 만들고 host 를 관찰한다
// 한 칸 = 그 변경 한 번 뒤 takeRecords() 로 꺼낸 레코드 — 없으면 — · 있으면 ○(oldValue 가 있으면 함께)
const 옵션들 = [
  ["{childList}", { childList: true }],
  ["{attributes}", { attributes: true }],
  ["{characterData}", { characterData: true }],
  ["{childList, subtree}", { childList: true, subtree: true }],
  ["{attributes, subtree}", { attributes: true, subtree: true }],
  ["{characterData, subtree}", { characterData: true, subtree: true }],
  ["{attributeOldValue}", { attributeOldValue: true }],
  ["{attributeFilter:[data-a]}", { attributeFilter: ["data-a"] }],
  ["{attributeFilter:[data-a], subtree}", { attributeFilter: ["data-a"], subtree: true }],
];
const 변경들 = [
  ["host 에 자식 붙임", n => n.host.append(document.createElement("i"))],
  ["child 에 자식 붙임", n => n.child.append(document.createElement("i"))],
  ["host data-a", n => n.host.setAttribute("data-a", "2")],
  ["host data-b", n => n.host.setAttribute("data-b", "2")],
  ["child data-a", n => n.child.setAttribute("data-a", "2")],
  ["host 의 글 바꿈", n => { n.host.firstChild.data = "나중"; }],
  ["child 의 글 바꿈", n => { n.child.firstChild.data = "나중"; }],
];
const 나무 = () => { const host = document.createElement("div"), child = document.createElement("div");
  host.setAttribute("data-a", "1"); host.setAttribute("data-b", "1"); child.setAttribute("data-a", "1");
  host.append("처음", child); child.append("처음"); document.body.append(host); return { host, child }; };
window.__끝 = () => {
  const 줄 = [["옵션", ...변경들.map(x => x[0])].join("\t")], 표 = {};
  let 온칸 = 0, 칸수 = 0;
  for (const [이름, 옵션] of 옵션들) {
    const 칸 = [];
    for (const [, 바꾸기] of 변경들) {
      const n = 나무(), mo = new MutationObserver(() => {});
      mo.observe(n.host, 옵션);
      바꾸기(n);
      const rs = mo.takeRecords(); mo.disconnect(); n.host.remove();
      칸수++; if (rs.length) 온칸++;
      칸.push(rs.length ? "○" + rs.map(r => r.oldValue !== null ? ` old=${r.oldValue}` : "").join("") : "—");
    }
    if (칸.length !== 변경들.length) throw new Error("칸 수");
    표[이름] = 칸; 줄.push([이름, ...칸].join("\t"));
  }
  const 다름 = (a, b) => 표[a].filter((v, k) => v !== 표[b][k]).length;
  const subtree쌍 = [["{childList}", "{childList, subtree}"], ["{attributes}", "{attributes, subtree}"],
                     ["{characterData}", "{characterData, subtree}"], ["{attributeFilter:[data-a]}", "{attributeFilter:[data-a], subtree}"]];
  줄.push(`레코드가 온 칸 = ${온칸} / ${칸수}`);
  줄.push(`subtree 가 바꾼 칸 = ${subtree쌍.reduce((s, [a, b]) => s + 다름(a, b), 0)} / ${subtree쌍.length * 변경들.length}`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-37-grid.html
옵션	host 에 자식 붙임	child 에 자식 붙임	host data-a	host data-b	child data-a	host 의 글 바꿈	child 의 글 바꿈
{childList}	○	—	—	—	—	—	—
{attributes}	—	—	○	○	—	—	—
{characterData}	—	—	—	—	—	—	—
{childList, subtree}	○	○	—	—	—	—	—
{attributes, subtree}	—	—	○	○	○	—	—
{characterData, subtree}	—	—	—	—	—	○	○
{attributeOldValue}	—	—	○ old=1	○ old=1	—	—	—
{attributeFilter:[data-a]}	—	—	○	—	—	—	—
{attributeFilter:[data-a], subtree}	—	—	○	—	○	—	—
레코드가 온 칸 = 15 / 63
subtree 가 바꾼 칸 = 5 / 28
(exit 0)
```

- ★★★ **레코드가 온 칸 15 / 63.** 나머지 48칸은 변경이 있었는데도 **신청서에 없어서** 레코드가 안 생겼다.
- ★★★ **`{characterData}` 줄은 일곱 칸 전부 `—`** — **`host 의 글 바꿈` 도 안 왔다.** 바뀐 것은 host 가 아니라 **host 의 자식인 텍스트 노드**다. `characterData` 는 **대상 노드 자신이 텍스트일 때**의 옵션이고, 요소를 관찰하면서 그 글을 보려면 **`subtree`** 가 있어야 한다(`{characterData, subtree}` 는 두 칸 다 `○`).
- ★★ **`subtree` 가 바꾼 칸 5 / 28** — `child 에 자식 붙임` · `child data-a` · 글 바꿈 둘 · 필터 걸린 `child data-a`. **자식 쪽 변경은 `subtree` 없이는 하나도 안 왔다.**
- ★★ **`{attributeOldValue}` 만 줘도 속성 레코드가 왔다**(`old=1`) — 명세가 `attributes` 를 **참으로 채워 준다**(「set options["attributes"] to true」). `{attributeFilter:[data-a]}` 도 같다 — 그리고 `data-b` 는 **걸러졌다.**

```text
   host 를 관찰할 때 — 무엇이 「host 의 변경」인가 (이 판)

   host ─┬─ #text 「처음」   ← 글을 바꾸면 이 노드의 characterData 변경 (host 가 아니다)
         └─ child ─ #text    ← child 의 속성 · 자식 · 글은 전부 subtree 가 있어야 보인다
   host 의 자식 목록(childList) · host 의 속성(attributes)만 subtree 없이 보인다
```

### (3) ★★ 옵션을 잘못 주면 — `TypeError`

```html
<!-- wa36b-37-bad.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>37 bad</title>
<div id="host"></div>
<script>
// observe 에 옵션을 어떻게 주면 던지나 — 던진 예외의 이름과 메시지 전문
const host = document.getElementById("host");
const 판들 = [
  ["observe(host)", () => new MutationObserver(() => {}).observe(host)],
  ["observe(host, {})", () => new MutationObserver(() => {}).observe(host, {})],
  ["observe(host, {subtree: true})", () => new MutationObserver(() => {}).observe(host, { subtree: true })],
  ["observe(host, {attributes: false, attributeOldValue: true})", () => new MutationObserver(() => {}).observe(host, { attributes: false, attributeOldValue: true })],
  ["observe(host, {attributeOldValue: true})", () => new MutationObserver(() => {}).observe(host, { attributeOldValue: true })],
];
window.__끝 = () => 판들.map(([이름, f]) => { try { f(); return `${이름}\t던지지 않음`; } catch (e) { return `${이름}\t${e.name}: ${e.message}`; } }).join("\n");
</script>
```

```text
$ python3 wa36b-net.py page wa36b-37-bad.html
observe(host)	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.
observe(host, {})	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.
observe(host, {subtree: true})	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.
observe(host, {attributes: false, attributeOldValue: true})	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object may only set 'attributeOldValue' to true when 'attributes' is true or not present.
observe(host, {attributeOldValue: true})	던지지 않음
(exit 0)
```

- ★★ **옵션 없이 · 빈 객체 · `subtree` 만 — 셋 다 같은 `TypeError`**: `The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.` **`subtree` 는 「무엇을」이 아니라 「어디까지」** 라서 혼자서는 뜻이 없다.
- ★★ **`attributes: false` + `attributeOldValue: true` 는 던지고, `attributeOldValue: true` 만은 안 던진다** — 뒤쪽은 명세가 `attributes` 를 채워 주기 때문이다((2)). 명세 단계의 순서 그대로다 — 「채우기」가 먼저, 「검사」가 나중.

### (4) ★★ 레코드 큐의 가장자리

```html
<!-- wa36b-37-edge.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>37 edge</title>
<div id="a"></div><div id="b"></div>
<script>
// 레코드 큐의 가장자리 — 콜백 전에 비우기 · 같은 값 다시 쓰기 · 대기 중에 끊기 · 한 번의 대입이 만드는 레코드 · 이동
const 쉼 = () => new Promise(r => setTimeout(r, 0));
const a = document.getElementById("a"), b = document.getElementById("b");
window.__끝 = async () => {
  const 줄 = [];
  { let 콜백 = 0; const mo = new MutationObserver(() => 콜백++);
    mo.observe(a, { attributes: true }); a.setAttribute("x", "1"); a.setAttribute("x", "2");
    const rs = mo.takeRecords(); await 쉼();
    줄.push(`[1] 변경 2번 → 콜백 전에 takeRecords()\t꺼낸 레코드 ${rs.length}개 · 그 뒤 콜백 ${콜백}번`); mo.disconnect(); }
  { let got = []; const mo = new MutationObserver(rs => got.push(...rs));
    a.setAttribute("y", "같음"); mo.observe(a, { attributes: true, attributeOldValue: true });
    a.setAttribute("y", "같음"); await 쉼();
    줄.push(`[2] 이미 "같음" 인 속성에 "같음" 을 다시 씀\t레코드 ${got.length}개 · oldValue=${got[0] && got[0].oldValue} · 지금 값=${a.getAttribute("y")}`); mo.disconnect(); }
  { let 콜백 = 0; const mo = new MutationObserver(() => 콜백++);
    mo.observe(a, { attributes: true }); a.setAttribute("z", "1"); mo.disconnect(); await 쉼();
    const 뒤 = mo.takeRecords();
    줄.push(`[3] 변경 1번 → 콜백 전에 disconnect()\t콜백 ${콜백}번 · 그 뒤 takeRecords() ${뒤.length}개`); }
  { const 판 = [["textContent 대입", () => { a.textContent = "하나"; }], ["innerHTML 대입(요소 셋)", () => { a.innerHTML = "<i></i><i></i><i></i>"; }],
               ["append 로 요소 셋", () => { a.append(document.createElement("i"), document.createElement("i"), document.createElement("i")); }]];
    for (const [이름, f] of 판) {
      a.replaceChildren(document.createElement("b"), document.createElement("b"));
      const mo = new MutationObserver(() => {}); mo.observe(a, { childList: true }); f();
      const rs = mo.takeRecords(); mo.disconnect();
      줄.push(`[4] 자식 둘 있는 요소에 ${이름}\t레코드 ${rs.length}개 · ` + rs.map(r => `(제거 ${r.removedNodes.length} · 추가 ${r.addedNodes.length})`).join(" ")); } }
  { a.replaceChildren(); const 옮길 = document.createElement("i"); a.append(옮길);
    const mo = new MutationObserver(() => {}); mo.observe(document.body, { childList: true, subtree: true });
    b.append(옮길);
    const rs = mo.takeRecords(); mo.disconnect();
    줄.push(`[5] a 의 자식을 b 에 append(이동)\t레코드 ${rs.length}개 · ` + rs.map(r => `(${r.target.id} 에서 제거 ${r.removedNodes.length} · 추가 ${r.addedNodes.length})`).join(" ")); }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-37-edge.html
[1] 변경 2번 → 콜백 전에 takeRecords()	꺼낸 레코드 2개 · 그 뒤 콜백 0번
[2] 이미 "같음" 인 속성에 "같음" 을 다시 씀	레코드 1개 · oldValue=같음 · 지금 값=같음
[3] 변경 1번 → 콜백 전에 disconnect()	콜백 0번 · 그 뒤 takeRecords() 0개
[4] 자식 둘 있는 요소에 textContent 대입	레코드 1개 · (제거 2 · 추가 1)
[4] 자식 둘 있는 요소에 innerHTML 대입(요소 셋)	레코드 1개 · (제거 2 · 추가 3)
[4] 자식 둘 있는 요소에 append 로 요소 셋	레코드 1개 · (제거 0 · 추가 3)
[5] a 의 자식을 b 에 append(이동)	레코드 2개 · (a 에서 제거 1 · 추가 0) (b 에서 제거 0 · 추가 1)
(exit 0)
```

- ★★ **[1] 콜백 전에 `takeRecords()` 로 둘을 꺼내면 그 뒤 콜백 0번** — 알림 마이크로태스크는 돌았지만 **큐가 비어 있으면 콜백을 안 부른다**(명세 「If records is not empty」).
- ★★ **[2] 이미 `같음` 인 속성에 `같음` 을 다시 써도 레코드 1개 · `oldValue=같음`** — 「change an attribute」는 **값을 비교하지 않는다.** 「값이 바뀌었을 때만」을 원하면 콜백에서 `oldValue` 와 지금 값을 견준다.
- ★★ **[3] 콜백 전에 `disconnect()` 하면 콜백 0번 · 그 뒤 `takeRecords()` 도 0개** — `disconnect` 가 **레코드 큐를 비운다.** 끊기 직전의 변경을 놓치기 싫으면 **`takeRecords()` 를 먼저** 부른다.

### (5) ★★ 대입 한 번 · 이동 한 번은 레코드 몇 개인가

- ★★ **[4] `textContent` 대입 — 레코드 1개(제거 2 · 추가 1)** · **`innerHTML` 대입 — 1개(제거 2 · 추가 3)** · **`append` 로 셋 — 1개(추가 3)**. 레코드는 「**노드 하나**」가 아니라 「**트리를 바꾼 한 번**」이다. 05편의 「조각 = 1 대 반복 = 3」도 같은 성질이다.
- ★★★ **[5] 다른 부모로 `append`(이동) — 레코드 2개**: `a 에서 제거 1` · `b 에서 추가 1`. [03번 주제](../03-node-creation-insertion-removal/2-summary.md) (2)의 「**삽입이 곧 이동**」은 MO 에게는 **제거와 추가 두 사건**으로 보인다.

### (6) 남의 스크립트가 만든 노드에 반응하기 — 설계 권고층

광고 · 위젯 스크립트가 **언제 무엇을 넣을지 모를 때**, 넣힐 자리를 `{ childList, subtree }` 로 관찰해 `.ad` 를 찾는다. 「남」은 한 태스크 안에서 `.ad` 를 **세 번** 넣는다 — ① `innerHTML` 로 감싸서 · ② 바로 · ③ 넣었다가 곧바로 뺀다.

```html
<!-- wa36b-37-watch.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>37 watch</title>
<div id="slot"></div>
<script>
// 남의 스크립트가 만든 노드에 반응하기 — 한 태스크 안에서 「남」이 .ad 를 세 번 넣는다
//   ① innerHTML 로 section 안에 감싸서 · ② 요소 하나를 바로 append · ③ append 한 뒤 같은 태스크에서 바로 remove
// 콜백 한 번에서 세 가지 방식으로 .ad 를 찾아 몇 개를 찾았나 센다
const slot = document.getElementById("slot");
const 남의스크립트 = () => {
  slot.innerHTML = '<section><div class="ad">①</div></section>';
  const 둘 = document.createElement("div"); 둘.className = "ad"; 둘.textContent = "②"; slot.append(둘);
  const 셋 = document.createElement("div"); 셋.className = "ad"; 셋.textContent = "③"; slot.append(셋); 셋.remove();
};
window.__끝 = () => new Promise(끝 => {
  new MutationObserver(rs => {
    const 추가 = rs.flatMap(r => [...r.addedNodes]).filter(n => n.nodeType === 1);
    const 가 = 추가.filter(n => n.matches(".ad"));
    const 나 = 추가.flatMap(n => [...(n.matches(".ad") ? [n] : []), ...n.querySelectorAll(".ad")]);
    const 다 = 나.filter(n => n.isConnected);
    끝([`레코드 ${rs.length}개 · 추가된 요소 ${추가.length}개`,
        `가 addedNodes 에서 matches(".ad")\t${가.length}개 (${가.map(n => n.textContent).join("")})`,
        `나 가 + 추가된 요소 안을 querySelectorAll(".ad")\t${나.length}개 (${나.map(n => n.textContent).join("")})`,
        `다 나 중 isConnected 인 것만\t${다.length}개 (${다.map(n => n.textContent).join("")})`].join("\n"));
  }).observe(slot, { childList: true, subtree: true });
  남의스크립트();
});
</script>
```

```text
$ python3 wa36b-net.py page wa36b-37-watch.html
레코드 4개 · 추가된 요소 3개
가 addedNodes 에서 matches(".ad")	2개 (②③)
나 가 + 추가된 요소 안을 querySelectorAll(".ad")	3개 (①②③)
다 나 중 isConnected 인 것만	2개 (①②)
(exit 0)
```

- ★★ **가 `addedNodes` 만 보면 2개(②③)** — **감싸서 넣은 ①을 놓쳤다.** `addedNodes` 에는 **맨 위 노드**(`section`)만 있다.
- ★★ **나 추가된 요소 안을 `querySelectorAll` 로 한 번 더 보면 3개(①②③)** — 그런데 **③은 이미 빠졌다.** 레코드는 사건의 기록이지 **지금 모양**이 아니다.
- ★★ **다 `isConnected` 로 걸러야 2개(①②)** — **지금 문서에 있는 것만.** 이 세 줄이 「남의 노드에 반응하기」의 기본 형태다 — **넣힌 노드의 안까지 · 지금 붙어 있는 것만.**

```text
   남의 노드에 반응하는 형태 (이 편의 권고)

   new MutationObserver(rs => {
     for (const 노드 of rs.flatMap(r => [...r.addedNodes]))   ← 맨 위 노드만 온다
       if (노드.nodeType === 1)
         for (const 찾음 of [노드, ...노드.querySelectorAll(선택자)])   ← 안까지
           if (찾음.matches(선택자) && 찾음.isConnected) 처리(찾음)     ← 지금 붙은 것만
   }).observe(자리, { childList: true, subtree: true })             ← 자리를 좁게
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const mo = new MutationObserver((records, observer) => { … });
   mo.observe(노드, { childList, attributes, characterData, subtree,
                      attributeOldValue, characterDataOldValue, attributeFilter: [이름…] });
   mo.takeRecords()   ← 큐를 꺼내고 비운다
   mo.disconnect()    ← 모든 대상에서 떼고 큐도 비운다
   record.type("childList" | "attributes" | "characterData") · target · addedNodes · removedNodes
         · previousSibling · nextSibling · attributeName · oldValue
```

### 어디서 헷갈리나

- **셋 중 하나는 참이어야 한다** — `subtree` 만으로는 `TypeError`((3)).
- **`…OldValue` · `attributeFilter` 는 짝 옵션을 채워 준다** — 명시적으로 `false` 를 주면 던진다((3)).
- **요소를 관찰하면서 `characterData` 만 주면 그 요소의 글이 안 보인다** — 글은 자식 노드다((2)).
- **같은 관찰자로 같은 대상을 다시 `observe` 하면 옵션을 바꿔 끼운다** — 명세 단계(「Set registered's options to options」). 이 편은 던지지 않았다.

## 어디서 틀리나

### 1. MO 콜백을 「변경 직후」라고 믿고 다음 줄에서 결과를 기대한다

**동기 코드가 다 끝난 뒤에 온다**((1)). 같은 태스크 안에서 레코드가 필요하면 `takeRecords()` 다.

### 2. 콜백 한 번 = 변경 한 번으로 센다

**다섯 번 바꿔도 콜백 1번 · 레코드 5개**((1)). 반대로 **대입 한 번이 레코드 1개에 노드 여럿**일 수도 있다((5)).

### 3. `then` 이 MO 보다 먼저라고(또는 나중이라고) 외운다

**거는 자리가 가른다** — 첫 변경보다 먼저 건 `then` 만 앞선다((1)).

### 4. `{ characterData: true }` 로 요소의 글 변경을 기다린다

**아무것도 안 온다**((2)). `subtree` 를 같이 주거나 텍스트 노드 자체를 관찰한다.

### 5. `disconnect()` 로 정리하면서 마지막 변경을 처리했다고 믿는다

**큐가 버려진다**((4) [3]). `takeRecords()` → 처리 → `disconnect()` 순서.

### 6. 같은 값 쓰기는 레코드가 안 생긴다고 믿는다

**생긴다**((4) [2]). 속성을 매 프레임 같은 값으로 쓰는 코드 옆에 MO 를 두면 **레코드가 매번 쌓인다.**

### 7. `addedNodes` 만 보고 남의 노드를 찾는다

**감싸서 넣은 것을 놓치고, 이미 빠진 것을 잡는다**((6)).

### 8. 이동을 「사건 하나」로 센다

**제거 + 추가 두 레코드**다((5)).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 첫 변경 때 알림을 한 번만 예약 · 그 뒤 변경은 레코드만 보탬 | ★ **명세**(DOM 「queue a mutation observer microtask」) — 세 판 로그가 그대로다 |
| MO 와 `then` 은 같은 마이크로태스크 줄에 선 순서 | ★ **명세**(DOM 의 queue a microtask + HTML 마이크로태스크 체크포인트) |
| 레코드가 비면 콜백 없음 · `disconnect` 는 큐를 비운다 | ★ **명세**(notify mutation observers · `disconnect()` 단계) |
| 옵션 채우기 · `TypeError` 넷 | ★ **명세**(`observe` 단계) — **문구는 Chrome 의 것**이다 |
| 같은 값 쓰기도 레코드 | ★ **명세**(change an attribute 에 비교가 없다) |
| `textContent` · `innerHTML` 대입 = 레코드 1개 | ★ **명세**(replace all 이 트리 변경 레코드를 한 번 건다) + 이 판의 관찰 |
| 남의 노드에 반응하는 형태 | **설계 권고층** |
| 비용 | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 남의 스크립트가 넣는 노드에 반응 | MO(`childList` + `subtree`, 자리를 좁게) + 안까지 찾기 + `isConnected` | `setInterval` 로 `querySelector` 폴링 |
| 내 컴포넌트의 속성 변화에 반응 | 커스텀 요소의 `attributeChangedCallback`([13번 주제](../13-custom-element-lifecycle/2-summary.md)) | 문서 전체에 MO |
| 속성 하나만 | `attributeFilter: ["이름"]` + `attributeOldValue` | `attributes: true` 전체 |
| 같은 태스크 안에서 지금까지의 변경이 필요 | `takeRecords()` | 콜백을 기다림 |
| 크기 변화 | [36번 주제](../36-resize-observer/2-summary.md)의 RO | MO 로 `style` 속성 감시(크기는 스타일 말고도 바뀐다) |

## 핵심 문장

1. **MO 는 변경을 묶어서 동기 코드 뒤에 한 번 알린다** — 다섯 번 바꾸면 콜백 1번 · 레코드 5개.
2. **알림 예약은 첫 변경 때 한 번** — 그래서 `then` 과의 순서는 **거는 자리**가 가른다.
3. **옵션은 「무엇을」(셋 중 하나 이상) + 「어디까지」(`subtree`)** — 요소의 글은 자식이라 `subtree` 없이는 안 보인다. 63칸 중 15칸.
4. **레코드는 「트리를 바꾼 한 번」의 기록이다** — 대입 한 번이 노드 여럿, 이동 한 번이 레코드 둘.
5. **큐가 비면 콜백이 없고, `disconnect` 는 큐를 버린다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 37번)
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — 삽입 · 이동 · 제거. 여기는 그것이 **레코드 몇 개로** 보이나
- [05번 주제](../05-documentfragment-and-template/2-summary.md) — 조각 한 번 = 레코드 1개(이 관찰자로 이미 잰 것)
- [13번 주제](../13-custom-element-lifecycle/2-summary.md) — 내 요소의 속성 · 연결 변화는 반응 콜백으로
- [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md) — 마이크로태스크 줄의 정본. 여기는 MO 가 그 줄 어디에 서나만
- 목록의 **40번 주제**(마이크로태스크 대 태스크 대 렌더 — 폴더는 아직 없다) — 렌더링까지 넣은 브라우저 전체 순서

## 용어 풀이

- **`MutationObserver`(MO)** — DOM 변경을 레코드로 모아 마이크로태스크에서 한 묶음으로 알려 주는 관찰자.
- **`MutationRecord`** — 변경 한 번의 기록. `type` 셋 중 하나.
- **레코드 큐** — 관찰자마다 있는 쌓아 두는 줄. `takeRecords()` 가 꺼내고 비운다.
- **알림 마이크로태스크** — 첫 변경 때 한 번만 거는 마이크로태스크. 돌면 관찰자마다 콜백을 부른다(큐가 비었으면 건너뛴다).
- **`subtree`** — 대상의 자손 변경까지 받는다는 「범위」 옵션.
- **`attributeFilter`** — 받을 속성 이름 목록. 주면 `attributes` 가 채워진다.
- **옵션 격자** — 옵션 아홉 벌 × 변경 일곱 = 63칸. 이 편의 본체 둘 중 하나.

## 더 들어가면

- **그림자 트리 안의 변경 · `slotchange`** — 같은 알림 마이크로태스크에서 쏜다(명세). 던지지 않았다.
- **옛 Mutation events** — 변경마다 **동기로** 쏘던 것이 MO 로 바뀐 이유(묶음 · 마이크로태스크). 던지지 않았다.
- **같은 대상 재관찰 · 일시 등록 관찰자(transient)** — 자손을 떼어 낸 뒤에도 그 안의 변경을 잠깐 따라가는 장치. 던지지 않았다.
