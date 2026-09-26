# web-api/34 — `navigator.sendBeacon` 과 이탈 시점 전송: `fetch` 의 `keepalive` 와의 관계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 떠날 때 **어느 이벤트가 불리나**는 [24번 주제](../24-document-lifecycle-events/1-question.md), 취소해도 요청이 닿는 판은 [27번 주제](../27-abort-and-timeout/1-question.md), 프리플라이트 조건은 [28번 주제](../28-cors-simple-and-preflight/1-question.md)가 물었다. 여기는 **그 이벤트 안에서 보낸 요청이 닿았나, 무엇이 잘렸나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진 · localhost 서버**의 관찰과 Fetch 명세 문장이다. 이식성과 **먼 서버에서의 결과**는 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `pagehide` 에서 한 번 보낸 요청 (예측)

```js
// wa32b-34-q1.js
// 질문용 — 실행 대상 아님
// 서버는 요청을 받으면 응답을 붙잡는다 — 떠난 뒤 0.5초에 놓으면서 「그때 연결이 살아 있었나」를 적는다
addEventListener("pagehide", () => {
  fetch("/beacon?...", { method: "POST", body: "x" });                   // (가)
  // fetch("/beacon?...", { method: "POST", body: "x", keepalive: true }); // (나)
  // navigator.sendBeacon("/beacon?...", "x");                             // (다)
});
// 떠나는 방식 둘 — 링크를 눌러 다른 문서로 · 탭 닫기(CDP Page.close)
// (가)(나)(다) × 두 방식 — 서버에 닿나? 응답을 놓을 때 연결이 살아 있나?
// 같은 (가) 를 unload 리스너에서 부르면?
```

- 여섯 칸(과 `unload` 두 칸)의 「닿았나 · 연결이 살아 있었나」는?

### 2. 떠나는 중의 동기 XHR (예측)

```js
// wa32b-34-q2.js
// 질문용 — 실행 대상 아님
function 보내기() {
  const x = new XMLHttpRequest();
  x.open("POST", "/beacon?...", false);   // 동기
  x.send("x");
}
// 네 자리 — visibilitychange(hidden) · pagehide · beforeunload · unload
// × 두 방식 — 링크로 떠나기 · 탭 닫기
// 어느 칸에서 send 가 돌아오고, 어느 칸에서 무엇을 던지나? 서버에는 닿나?
```

- 여덟 칸 각각은?

### 3. 본문 크기와 결과 (예측)

```js
// wa32b-34-q3.js
// 질문용 — 실행 대상 아님
const 본 = n => new Uint8Array(n);
await fetch("/beacon", { method: "POST", body: 본(65536), keepalive: true });
await fetch("/beacon", { method: "POST", body: 본(65537), keepalive: true });
await fetch("/beacon", { method: "POST", body: 본(65537) });
navigator.sendBeacon("/beacon", 본(65536));
navigator.sendBeacon("/beacon", 본(65537));
// 서버가 keepalive 40000바이트 하나를 붙잡고 있는 동안(한 줄에 한 번씩)
await fetch("/beacon", { method: "POST", body: 본(25536), keepalive: true });
await fetch("/beacon", { method: "POST", body: 본(25537), keepalive: true });
navigator.sendBeacon("/beacon", 본(25536));
navigator.sendBeacon("/beacon", 본(25537));
// 각 줄의 결과는(then / catch 무엇 / true · false)? 서버에는 무엇이 닿나?
```

- 각 줄의 결과는?

### 4. `sendBeacon` 이 보낸 것 (예측)

```js
// wa32b-34-q4.js
// 질문용 — 실행 대상 아님 — 같은 출처 A 와 다른 출처 B 로 각각
navigator.sendBeacon(url, "a=1");
navigator.sendBeacon(url, new Blob(["a=1"]));
navigator.sendBeacon(url, new Blob(["a=1"], { type: "text/plain" }));
navigator.sendBeacon(url, new Blob(['{"a":1}'], { type: "application/json" }));
navigator.sendBeacon(url, new URLSearchParams({ a: "1" }));
navigator.sendBeacon(url, formData);
// B 는 OPTIONS 에 허용 헤더를 안 준다
// 돌아오는 값은? 서버가 받은 메서드 · Content-Type 은? B 에 OPTIONS 가 먼저 오는 줄은?
```

- 반환값 · 서버가 받은 것 · `OPTIONS` 가 먼저 온 줄은?

### 5. 큰 본문을 떠나며 (예측)

```js
// wa32b-34-q5.js
// 질문용 — 실행 대상 아님
// 서버는 헤더만 받고, 떠난 뒤 0.5초가 지나서야 본문을 읽기 시작한다
addEventListener("pagehide", () => {
  fetch("/big?...", { method: "POST", body: new Uint8Array(8 << 20) });   // 8 MiB
});
// ① 떠나지 않고 부른다  ② 링크로 떠난다  ③ 탭을 닫는다
// 각각 — 서버가 본문을 끝까지 받나?
```

- 세 경우 각각 — 서버가 본문을 끝까지 받나?

### 6. 보통 `fetch` 가 끊기는 이유 (왜)

- 문항 1에서 보통 `fetch` 가 탭 닫기에서 받은 결과를 Fetch 명세의 어느 단계로 설명하나? 같은 `fetch` 가 링크로 떠날 때 다르게 굴었다면 무엇이 갈랐나?

### 7. `sendBeacon` 의 `true` (경계)

- `true` 가 말하는 것과 말하지 않는 것은? 문항 4의 어느 줄이 그 경계를 보여 주나?

### 8. 64KiB 는 무엇의 한도인가 (경계)

- 한 요청의 한도인가, 무엇의 합인가? `keepalive` 와 `sendBeacon` 은 한도를 따로 쓰나?

### 9. 어느 자리에서 부르나 (연결)

- [24번 주제](../24-document-lifecycle-events/1-question.md)의 격자로 보면, 네 자리 중 **떠남과 가림에서 빠짐없이 불리는** 것은? `unload` 를 피해야 하는 이유 두 가지(24편 하나 · 이 편 하나)는?

### 10. 「5판 모두 닿았다」를 어디까지 믿나 (연결)

- [27번 주제](../27-abort-and-timeout/1-question.md)의 「같은 잡에서 `abort()` 해도 닿은 판」과 이 편의 결과는 어떤 성질이 같은가? 이 편이 **주장하지 않는 것**은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
