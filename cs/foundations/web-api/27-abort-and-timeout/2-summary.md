# web-api/27 — `AbortController` 로 취소와 타임아웃: `AbortSignal.timeout()`/`any()` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」 — 페이지가 받은 것과 서버가 한 일을 칸마다 나란히 놓는 「취소 격자」다.** 서버의 `/work` 는 도착하면 「처리 시작」, 페이지가 `/go` 를 줄 때 「처리 끝(주문을 기록했다)」, 그다음 응답을 쓴다. 페이지는 **취소를 받은 뒤 서버가 연결 닫힘을 알아챌 때까지 기다렸다가** `/go` 를 준다 — 그래서 「취소한 뒤에도 서버는 처리를 끝냈나」가 시간 없이 칸마다 갈린다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 fetch() 메서드 단계(「signal 이 이미 abort 됐으면 **abort the fetch() call** … signal 의 abort reason 으로」 · signal 에 다는 abort 단계 — 「**controller 를 abort** 하고 **abort the fetch() call**」) · 「To abort a fetch() call」(**① 프라미스를 error 로 거부** · 요청 본문이 읽히는 중이면 취소 · **응답 본문이 읽히는 중이면 error 로 error**) · [WHATWG DOM](https://dom.spec.whatwg.org/) 의 `abort(reason)`(「reason 이 없으면 **`AbortError` DOMException**」) · `AbortSignal.timeout()`(「타이머 태스크로 **`TimeoutError` DOMException**」) · `AbortSignal.any()`(「dependent abort signal — **원인이 된 신호의 reason**」). ★ **명세 어디에도 「서버에게 취소를 알린다」는 단계는 없다** — 페이지 쪽 프라미스와 스트림만 끝낸다. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 서버는 로컬 서버 A 다. 하네스는 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★★ **[20번 주제](../20-listener-lifetime/2-summary.md)의 (5)\~(7)이 이 편의 절반을 리스너 쪽에서 쟀다** — `signal` 하나로 리스너 다섯을 떼는 것 · **이미 abort 된 `signal` 로 등록하면 예외 없이 `undefined` · 호출 0회** · `abort()` 인자 없음의 reason 이 `AbortError 「signal is aborted without reason」` · **`AbortSignal.any` 의 reason 은 원본과 같은 객체** · **`timeout(0)` 도 같은 잡 안에서는 아직 `aborted=false`**. 여기서는 **다시 재지 않고 인용**하고 **`fetch` 쪽**으로 간다. [25번 주제](../25-fetch-request-response/2-summary.md)(거부는 `catch` 로) · [26번 주제](../26-response-body-streaming/2-summary.md)(본문 스트림). ★★★ **[JS 41번 주제](../../languages/js/syntax/41-cancellation-and-timeouts/2-summary.md)가 나머지 절반을 node 안의 서버로 쟀다** — (1) 「프라미스에는 취소가 없다」 · (2) `reason` 7행과 **`AbortError` 대 `TimeoutError`**(문구가 node 와 Chrome 에서 다르다) · (4) **이미 abort 된 신호는 요청 0 · 처리 중 abort 는 서버가 이미 받았고 연결만 끊긴다** · `abort("mine")` 이 **Chrome 151 에서 `"mine"` 그대로**. 여기서는 그것을 **인용**하고, **브라우저 페이지 대 서버**로 넓혀 **「서버는 처리를 끝냈나 · 응답 쓰기는 어떻게 됐나 · 본문을 읽는 중이면 · 같은 잡에서 끊으면」** 을 더한다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 취소 격자 7칸 · 서버 로그 · 본문 중 취소 넷 · 오류 이름과 문구 · `=== signal.reason` | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **흔들린다 — 그 사실이 결론이다** | **같은 잡에서 `fetch()` 직후 `abort()` 했을 때 서버에 도착한 판 수**와 그 번호 | 캡처 여섯 판이 **5 · 6 · 6 · 6 · 6 · 6 / 100**(번호는 전부 앞쪽 `0…5`), 시험판(20번씩)은 **0 · 1 · 1** 이었다. **「0 이 아니다」만 주장한다** — 재대조기가 이 두 줄을 정규화한다 |
| ★ **흔들렸다가 고쳤다** | 「응답 쓰기」 칸 | 서버가 **닫힌 연결에 쓴 첫 바이트는 커널이 받아 준다** — 한 번만 쓰면 「오류 없음」이 나올 수 있다. **상대의 RST 가 돌아와 오류가 날 때까지** 한 바이트씩 더 쓰게 고쳤다 |
| ★ **시간에 기댄 칸 둘** | `timeout(1000)` 두 칸 | 1초 안에 요청이 서버에 닿아야 「도착 예」가 된다. 루프백에서 넉넉하다 — 세 판 모두 같았다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조 정규화 규칙은 **두 줄** — `서버에 도착한 판 = N / 100` 과 `도착한 번호 = […]`. **그 밖의 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | 거부의 `name`·`message` · `bodyUsed` |
| 창 ③ 같은 것을 두 번 읽기 | ★★ **쓴다** | 받은 오류 **`=== signal.reason`** — 같은 객체인가((3)) |
| **창 ④ 서버 요청 로그 — 페이지 대 서버** | ★★★ **본체** | 도착 · **처리 끝** · 연결 닫힘을 앎 · 응답 쓰기 |
| 리스너 쪽 `AbortSignal` | **부적용 — 20편이 쟀다** | 인용만 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **실제 네트워크에서 「요청이 가는 중에」 끊기는 것** | 루프백은 거의 즉시 닿는다. 「도착 전 취소」는 **이미 abort 된 signal** 로만 결정적으로 만들 수 있었다 |
| **HTTP/2 · HTTP/3 의 취소**(스트림 리셋) | 이 판은 HTTP/1.1 — 취소가 **연결을 닫는 것**으로 보였다. 다른 프로토콜에서 서버가 무엇을 보는지는 모른다 |
| **서버 프레임워크가 끊김을 처리에 알려 주는가** | 이 서버는 **알려 주지 않도록** 짰다(처리를 끝까지 한다). Go 의 `Request.Context()` 같은 장치는 대비로만 적는다 |
| **요청 본문 업로드 중 취소** | 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ `abort()` 는 「전화 끊기」다. 내 쪽 수화기는 내려놓았지만(프라미스 거부) 상대는 이미 주문서를 받아 처리하고 있다 — 끊긴 줄을 알아도 하던 일을 마치고, 답을 하려다 아무도 안 받는 것을 그제야 안다. 취소는 요청을 「없던 일」로 만들지 않는다.**

| 비유 | 실체 |
|---|---|
| 수화기를 내려놓는다 | `controller.abort()` — 페이지의 프라미스가 `AbortError` 로 거부 |
| 알람이 울리면 끊는다 | `AbortSignal.timeout(ms)` — 거부가 **`TimeoutError`** |
| 둘 중 먼저 오는 쪽 | `AbortSignal.any([사용자, 타임아웃])` — **원인이 된 쪽의** 이유 |
| 상대는 이미 받아 적었다 | 서버 로그의 「처리 끝(주문을 기록했다)」 |
| 답을 하려는데 신호가 없다 | 서버의 「응답 쓰기 실패(BrokenPipeError)」 |
| 전화를 걸기도 전에 포기 | 이미 abort 된 signal — **서버에 아무것도 안 간다** |

```text
   ★ 처리 중 abort() 한 번 — 페이지와 서버 (시간은 오른쪽으로)

   페이지  fetch ──────────┬── abort() ─ catch AbortError ─────────── (끝)
                           │                  ▲
   서버           도착 · 처리 시작 ──── 연결 닫힘을 앎 ── 처리 끝(주문 기록) ── 응답 쓰기 ✕ BrokenPipeError
                                                          ★ 취소 뒤에도 일어났다
```

## 이 주제가 답하려는 질문

1. **취소하면 서버에서는 무엇이 없던 일이 되나** — 도착 전 · 처리 중 · 응답 본문을 읽는 중.
2. **`TimeoutError` 와 `AbortError` 는 어디서 갈리나** — `timeout()` · 수동 `abort()` · `any()`.
3. **페이지가 받는 오류는 `signal.reason` 과 같은 것인가** — 프라미스 쪽과 본문 쪽.

## 동작 방식

### (1) ★★★ 본체 — 취소 격자: 서버에서 끝까지 처리된 칸

**언제 쓰나** — 「타임아웃이 나서 다시 보냈더니 주문이 두 번 들어갔다」일 때.

**던진 것** — 일곱 칸. 이미 abort 된 signal · 처리 중 `abort()` · 처리 중 `abort("그만")` · `timeout(1000)` · `any([사용자, timeout(60초)])` 에서 사용자가 누름 · `any([사용자, timeout(1000)])` 에서 아무도 안 누름 · abort 없음(대조). 「처리 중」은 **서버가 도착을 알린 뒤**(`/state?wait=arrived`)다.

```html
<!-- wa24b-27-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>27 grid</title>
<script>
// 취소 격자 — 칸마다 페이지가 받은 것과 서버가 한 일을 나란히 적는다
// 서버의 「처리」는 페이지가 /go 를 줄 때 끝난다. 페이지는 취소를 받은 뒤, 서버가 연결 닫힘을 알아챌 때까지 기다렸다가 /go 를 준다
const 서버 = async (id, 기다림 = "") => (await fetch(`/state?id=${id}&wait=${기다림}`)).json();
const 가 = id => fetch(`/go?id=${id}`);
const 받은것 = async p => { try { const r = await p; return "then · status=" + r.status; }
                           catch (e) { return "catch · " + (e?.name ?? typeof e) + " 「" + (e?.message ?? String(e)) + "」"; } };
const 칸 = [
  ["이미 abort 된 signal 로 fetch", async id => {
    const r = await 받은것(fetch(`/work?id=${id}`, { signal: AbortSignal.abort() }));
    return [r, null];
  }],
  ["서버 도착 뒤·처리 중 abort()", async id => {
    const c = new AbortController();
    const p = 받은것(fetch(`/work?id=${id}`, { signal: c.signal }));
    await 서버(id, "arrived"); c.abort();
    const r = await p; await 서버(id, "closed"); await 가(id); return [r, await 서버(id, "done")];
  }],
  ["처리 중 abort('그만') — 이유를 줌", async id => {
    const c = new AbortController();
    const p = 받은것(fetch(`/work?id=${id}`, { signal: c.signal }));
    await 서버(id, "arrived"); c.abort("그만");
    const r = await p; await 서버(id, "closed"); await 가(id); return [r, await 서버(id, "done")];
  }],
  ["처리 중 AbortSignal.timeout(1000)", async id => {
    const p = 받은것(fetch(`/work?id=${id}`, { signal: AbortSignal.timeout(1000) }));
    await 서버(id, "arrived");
    const r = await p; await 서버(id, "closed"); await 가(id); return [r, await 서버(id, "done")];
  }],
  ["any([사용자, timeout(60초)]) — 사용자가 abort", async id => {
    const c = new AbortController();
    const p = 받은것(fetch(`/work?id=${id}`, { signal: AbortSignal.any([c.signal, AbortSignal.timeout(60000)]) }));
    await 서버(id, "arrived"); c.abort();
    const r = await p; await 서버(id, "closed"); await 가(id); return [r, await 서버(id, "done")];
  }],
  ["any([사용자, timeout(1000)]) — 아무도 안 누름", async id => {
    const c = new AbortController();
    const p = 받은것(fetch(`/work?id=${id}`, { signal: AbortSignal.any([c.signal, AbortSignal.timeout(1000)]) }));
    await 서버(id, "arrived");
    const r = await p; await 서버(id, "closed"); await 가(id); return [r, await 서버(id, "done")];
  }],
  ["abort 없음(대조)", async id => {
    const c = new AbortController();
    const p = 받은것(fetch(`/work?id=${id}`, { signal: c.signal }));
    await 서버(id, "arrived"); await 가(id);
    const r = await p; return [r, await 서버(id, "done")];
  }],
];
const 너비 = t => [...t].reduce((n, ch) => n + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 한줄 = (칸들, 폭) => {                             // 칸 수가 머리와 다르면 멈춘다
  if (칸들.length !== 폭.length) throw new Error("칸 수가 어긋났다");
  return 칸들.map((c, k) => k === 칸들.length - 1 ? c : c + " ".repeat(Math.max(폭[k] - 너비(c), 1))).join("");
};
window.__끝 = async () => {
  const 폭 = [46, 56, 10, 8, 15, 0];
  const O = [한줄(["칸", "페이지가 받은 것", "서버 도착", "처리 끝", "연결 닫힘을 앎", "응답 쓰기"], 폭)];
  let 끝까지 = 0, k = 0;
  for (const [이름, 함] of 칸) {
    const id = "g" + (++k);
    const [받음, 뒤] = await 함(id);
    const 상태 = 뒤 ?? await 서버(id);
    if (상태.done) 끝까지++;
    O.push(한줄([이름, 받음, 상태.arrived ? "예" : "아니오", 상태.done ? "예" : "아니오", 상태.closed ? "예" : "아니오",
            상태.write ?? "—"], 폭));
  }
  O.push("서버에서 끝까지 처리된 칸 = " + 끝까지 + " / " + 칸.length);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-27-grid.html
칸                                            페이지가 받은 것                                        서버 도착 처리 끝 연결 닫힘을 앎 응답 쓰기
이미 abort 된 signal 로 fetch                 catch · AbortError 「signal is aborted without reason」 아니오    아니오  아니오         —
서버 도착 뒤·처리 중 abort()                  catch · AbortError 「signal is aborted without reason」 예        예      예             BrokenPipeError
처리 중 abort('그만') — 이유를 줌            catch · string 「그만」                                 예        예      예             BrokenPipeError
처리 중 AbortSignal.timeout(1000)             catch · TimeoutError 「signal timed out」               예        예      예             BrokenPipeError
any([사용자, timeout(60초)]) — 사용자가 abort catch · AbortError 「signal is aborted without reason」 예        예      예             BrokenPipeError
any([사용자, timeout(1000)]) — 아무도 안 누름 catch · TimeoutError 「signal timed out」               예        예      예             BrokenPipeError
abort 없음(대조)                              then · status=200                                       예        예      아니오         오류 없음
서버에서 끝까지 처리된 칸 = 6 / 7
--- 서버 로그 ---
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   처리 끝 (주문을 기록했다)
A   응답을 썼다 (오류 없음)
(exit 0)
```

- ★★★ **서버에서 끝까지 처리된 칸 6 / 7** — 취소한 다섯 칸이 전부 **「도착 예 · 처리 끝 예」** 다. 서버 로그가 칸마다 **「처리 끝 (주문을 기록했다)」** 을 적었다. **안 된 칸은 이미 abort 된 signal 하나뿐** — 요청이 아예 안 나갔다(서버 로그에 그 줄이 없다).
- ★★ **서버는 연결이 닫힌 것을 알았지만 처리를 멈추지 않았다** — 「연결 닫힘을 앎 예」인 다섯 칸 모두 그 뒤에 「처리 끝」이 왔다. **서버가 끊김을 처리에 전하지 않으면 취소는 서버에 아무것도 못 한다.**
- ★★ **응답 쓰기는 다섯 칸 전부 `BrokenPipeError`** — 서버는 **답을 하려다가** 페이지가 떠난 것을 확정했다. 대조 칸만 「오류 없음」.
- ★ Fetch 명세 그대로 — **abort the fetch() call 은 프라미스를 거부하고 스트림을 끝낼 뿐**, 서버에게 무언가를 되돌리라고 하는 단계가 없다.

```text
   ★ 취소 격자 — 페이지 대 서버 (이 판 7칸)

                                   페이지            서버 도착  처리 끝  응답 쓰기
   이미 abort 된 signal            AbortError        ✕          ✕        —
   처리 중 abort()                 AbortError        ○          ○ ★      BrokenPipe
   처리 중 abort("그만")           "그만"(문자열)    ○          ○ ★      BrokenPipe
   timeout(1000)                   TimeoutError      ○          ○ ★      BrokenPipe
   any([사용자, 60초]) 사용자      AbortError        ○          ○ ★      BrokenPipe
   any([사용자, 1000]) 아무도      TimeoutError      ○          ○ ★      BrokenPipe
   abort 없음                      then 200          ○          ○        오류 없음

   ★ 「없던 일」이 된 칸 = 요청이 아예 안 나간 한 칸
```

### (2) ★★ `TimeoutError` 대 `AbortError` — 이름이 원인을 말한다

같은 격자에서 **오류 이름**만 본다.

```text
$ python3 wa24b-net.py page wa24b-27-grid.html | sed -n '1,9p'
칸                                            페이지가 받은 것                                        서버 도착 처리 끝 연결 닫힘을 앎 응답 쓰기
이미 abort 된 signal 로 fetch                 catch · AbortError 「signal is aborted without reason」 아니오    아니오  아니오         —
서버 도착 뒤·처리 중 abort()                  catch · AbortError 「signal is aborted without reason」 예        예      예             BrokenPipeError
처리 중 abort('그만') — 이유를 줌            catch · string 「그만」                                 예        예      예             BrokenPipeError
처리 중 AbortSignal.timeout(1000)             catch · TimeoutError 「signal timed out」               예        예      예             BrokenPipeError
any([사용자, timeout(60초)]) — 사용자가 abort catch · AbortError 「signal is aborted without reason」 예        예      예             BrokenPipeError
any([사용자, timeout(1000)]) — 아무도 안 누름 catch · TimeoutError 「signal timed out」               예        예      예             BrokenPipeError
abort 없음(대조)                              then · status=200                                       예        예      아니오         오류 없음
서버에서 끝까지 처리된 칸 = 6 / 7
(exit 0)
```

- ★★ **`timeout()` 이 끊으면 `TimeoutError 「signal timed out」`, 사람이 `abort()` 하면 `AbortError 「signal is aborted without reason」`.** DOM 의 `timeout()` 이 **「`TimeoutError` DOMException 으로 signal abort」**, `abort()` 가 **「reason 이 없으면 `AbortError`」** 로 정한다.
- ★★ **`any([사용자, 타임아웃])` 은 먼저 끊은 쪽의 이름**을 받는다 — 사용자가 누르면 `AbortError`, 아무도 안 누르면 `TimeoutError`. [20번 주제](../20-listener-lifetime/2-summary.md)의 (7)이 **`any` 의 reason 이 원본과 같은 객체**임을 리스너 쪽에서 쟀고, [JS 41번 주제](../../languages/js/syntax/41-cancellation-and-timeouts/2-summary.md)의 (2)가 `reason` 일곱 가지와 `code`(20·23)를 쟀다.
- ★★ **`abort("그만")` 이면 `catch` 가 받는 것은 문자열 `"그만"` 그 자체**다 — `name` 이 없다(`typeof` 가 `string`). fetch() 의 abort 단계가 **signal 의 abort reason 으로** 거부하기 때문이다. `e.name === "AbortError"` 로만 거르는 코드는 이 칸을 **못 알아본다.**

```text
   catch 가 받는 것 — 누가 끊었나

   controller.abort()             AbortError     「signal is aborted without reason」
   controller.abort("그만")       "그만"          ← 이유를 주면 그 값 그대로(Error 가 아닐 수도)
   AbortSignal.timeout(ms)        TimeoutError   「signal timed out」
   AbortSignal.any([a, b])        먼저 끊은 쪽의 것
   ★ 「사용자가 취소함」과 「시간 초과」를 이름으로 가를 수 있다 — 재시도 판단은 뒤쪽에서만
```

### (3) ★★ 응답을 받은 뒤의 취소 — 본문 쪽

**던진 것** — 가. 청크 스트림에서 첫 `read()` 뒤 `abort()` · 나. 서버가 본문을 끝까지 쓴 뒤 **아직 안 읽은 채** `abort()` · 다. (대조) 처리 중 `abort()` 의 `fetch` 거부 · 라. `text()` 로 다 읽은 뒤 `abort()`. 오류마다 **`=== signal.reason`** 을 찍는다.

```html
<!-- wa24b-27-body.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>27 body</title>
<script>
// 응답(헤더)을 받은 뒤의 abort — 본문을 읽는 중 · 본문이 다 온 뒤 읽기 전 · (대조) fetch 자체의 거부 · 다 읽은 뒤
const 서버 = async (id, 기다림 = "") => (await fetch(`/state?id=${id}&wait=${기다림}`)).json();
const 가 = id => fetch(`/go?id=${id}`);
const 이름 = e => (e?.name ?? typeof e) + " 「" + (e?.message ?? String(e)) + "」";
window.__끝 = async () => {
  const O = [];
  // 가. 청크 스트림을 읽는 중에
  const c1 = new AbortController();
  const r1 = await fetch("/chunks?id=b1&n=5", { signal: c1.signal });
  const 읽개 = r1.body.getReader();
  await 가("b1");
  const 첫 = await 읽개.read();
  O.push("가. 첫 read() → " + JSON.stringify(new TextDecoder().decode(첫.value)) + " · 그다음 abort()");
  c1.abort();
  try { await 읽개.read(); O.push("   둘째 read() → 값"); }
  catch (e) { O.push("   둘째 read() → " + 이름(e) + " · === signal.reason → " + (e === c1.signal.reason)); }
  await 서버("b1", "closed");
  for (let k = 0; k < 5; k++) await 가("b1");            // 서버가 남은 청크를 쓰게 한다
  const s1 = await 서버("b1", "done");
  O.push("   서버 — 도착=" + s1.arrived + " · 보내려 한 청크=" + s1.sent + "/5 · 연결 닫힘을 앎=" + s1.closed + " · 쓰기=" + s1.write);
  // 나. 본문이 다 도착한 뒤, 읽기 전에
  const c2 = new AbortController();
  const r2 = await fetch("/chunks?id=b2&n=1", { signal: c2.signal });
  await 가("b2"); await 가("b2");                        // 청크 하나 + 끝 표시
  const s2 = await 서버("b2", "done");
  O.push("나. 서버가 끝까지 썼다(쓰기=" + s2.write + ") · 아직 안 읽었다 · 그다음 abort()");
  c2.abort();
  try { O.push("   text() → " + JSON.stringify(await r2.text())); }
  catch (e) { O.push("   text() → " + 이름(e) + " · === signal.reason → " + (e === c2.signal.reason)); }
  // 다. fetch 자체가 거부될 때(처리 중 abort) — 그 오류가 signal.reason 과 같은 객체인가
  const c4 = new AbortController();
  const p4 = fetch("/work?id=b4", { signal: c4.signal });
  await 서버("b4", "arrived"); c4.abort();
  try { await p4; } catch (e) { O.push("다. 처리 중 abort() → fetch 의 거부 = " + 이름(e) + " · === signal.reason → " + (e === c4.signal.reason)); }
  await 서버("b4", "closed"); await 가("b4"); await 서버("b4", "done");
  // 라. 다 읽은 뒤
  const c3 = new AbortController();
  const r3 = await fetch("/status?code=200", { signal: c3.signal });
  const t3 = await r3.text();
  c3.abort();
  O.push("라. text() 로 다 읽은 뒤 abort() → 이미 받은 글 = " + JSON.stringify(t3) + " · bodyUsed=" + r3.bodyUsed);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-27-body.html
가. 첫 read() → "줄1\n" · 그다음 abort()
   둘째 read() → AbortError 「BodyStreamBuffer was aborted」 · === signal.reason → false
   서버 — 도착=true · 보내려 한 청크=2/5 · 연결 닫힘을 앎=true · 쓰기=BrokenPipeError
나. 서버가 끝까지 썼다(쓰기=오류 없음) · 아직 안 읽었다 · 그다음 abort()
   text() → AbortError 「The user aborted a request.」 · === signal.reason → false
다. 처리 중 abort() → fetch 의 거부 = AbortError 「signal is aborted without reason」 · === signal.reason → true
라. text() 로 다 읽은 뒤 abort() → 이미 받은 글 = "{\"status\": 200}" · bodyUsed=true
--- 서버 로그 ---
A GET /chunks?n=5  도착
A   상대가 연결을 닫은 것을 알았다
A   쓰기 실패 (BrokenPipeError) — 청크 2/5 째에서
A GET /chunks?n=1  도착
A   청크 1개와 끝 표시까지 썼다
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /status?code=200  → 200 응답을 끝까지 보냈다
(exit 0)
```

- ★★ **읽는 중 취소 — 다음 `read()` 가 `AbortError 「BodyStreamBuffer was aborted」`.** 서버는 청크 2 를 쓰려다 `BrokenPipeError` — 「보내려 한 청크 2/5」에서 멈췄다.
- ★★★ **본문이 다 와 있어도 안 읽었으면 취소된다** — `text()` 가 `AbortError 「The user aborted a request.」`. 서버는 **끝까지 오류 없이 썼는데** 페이지는 그것을 못 읽는다. Fetch 명세의 「응답 본문이 **readable 이면** error 로 error」 — 다 도착했어도 아직 읽을 수 있는 상태였다.
- ★★ **다 읽은 뒤의 `abort()` 는 아무것도 안 한다** — 받은 글이 그대로 있다(`bodyUsed=true`).
- ★★★ **본문 쪽 오류는 `signal.reason` 과 다른 객체였다**(`=== signal.reason → false` 두 줄) — **`fetch` 의 거부는 같은 객체**(`true`)다. 명세의 「abort the fetch() call」은 **프라미스도 본문도 같은 error 로** 끝내라고 적는데, 이 판의 본문 쪽은 **새 `AbortError`** 를 만들었고 문구도 둘로 갈렸다. ★ **본문 쪽에서 `e === signal.reason` 으로 판정하지 마라.**

```text
   응답을 받은 뒤 abort() — 무엇이 끝나나 (이 판)

   헤더만 받음 · 읽는 중      다음 read()  ✕ AbortError 「BodyStreamBuffer was aborted」    ≠ signal.reason
   본문 다 옴 · 안 읽음       text()       ✕ AbortError 「The user aborted a request.」      ≠ signal.reason
   다 읽음                    (아무 일 없음) — 이미 받은 글은 그대로
   (대조) fetch 거부          ✕ AbortError 「signal is aborted without reason」              = signal.reason
```

### (4) ★★ 같은 잡에서 `abort()` 해도 요청이 닿을 때가 있다

**던진 것** — `fetch()` 를 부른 **바로 그 잡에서** `abort()` 를 100번. 끝난 뒤 서버에게 번호마다 「도착했나」를 묻는다.

```html
<!-- wa24b-27-race.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>27 race</title>
<script>
// fetch() 를 부른 바로 그 잡에서 abort() — 요청이 서버에 닿나? 100번 해 보고, 끝난 뒤 서버에게 번호마다 묻는다
window.__끝 = async () => {
  const N = 100;
  let 거부 = 0;
  for (let k = 0; k < N; k++) {
    const c = new AbortController();
    const p = fetch(`/work?id=r${k}`, { signal: c.signal });
    c.abort();
    try { await p; } catch (e) { if (e.name === "AbortError") 거부++; }
  }
  await fetch("/status?code=200");                       // 한 번 더 왕복해 늦게 온 요청을 받을 틈을 준다
  let 도착 = 0; const 번호 = [];
  for (let k = 0; k < N; k++) {
    const s = await (await fetch(`/state?id=r${k}`)).json();
    if (s.arrived) { 도착++; 번호.push(k); await fetch(`/go?id=r${k}`); }
  }
  return ["AbortError 로 거부된 판 = " + 거부 + " / " + N, "서버에 도착한 판 = " + 도착 + " / " + N, "도착한 번호 = " + JSON.stringify(번호)].join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py quiet wa24b-27-race.html
AbortError 로 거부된 판 = 100 / 100
서버에 도착한 판 = 6 / 100
도착한 번호 = [0,1,2,3,4,5]
(exit 0)
```

- ★★ **100번 전부 페이지는 `AbortError`** 를 받았다 — 그런데 **서버에 도착한 판이 0 이 아니다.** 캡처 여섯 판이 5 · 6 · 6 · 6 · 6 · 6, 도착한 번호는 전부 **앞쪽(0 부터)** 이었다. 시험판(20번씩)은 0 · 1 · 1 이었다.
- ★★★ **「보내자마자 취소했으니 안 갔겠지」는 보장이 아니다.** 페이지는 `fetch()` 가 돌려준 프라미스를 들고 있을 뿐, 요청을 실제로 내보내는 일과 `abort()` 가 그것을 따라잡는 일 중 **어느 쪽이 먼저 네트워크에 닿는지는 이 판에서 정해져 있지 않았다.** 결정적으로 「안 보냄」을 만든 것은 **이미 abort 된 signal**((1)의 첫 칸)뿐이었다.
- ★ 앞쪽 번호에 몰린 이유는 **재지 않았다.** 판 수는 흔들리므로 **「0 이 아니다」만** 주장한다.

```text
   보내지 않음을 확실히 만드는 것 — 이 판

   이미 abort 된 signal 로 fetch      요청을 만들기 전에 거부     서버 도착 ✕  (세 판 모두)
   fetch() 한 잡에서 abort()          거부는 늘 AbortError        서버 도착 ?  (0 이 아닌 판들)
   서버 도착 뒤 abort()               거부 AbortError             서버 도착 ○ · 처리 끝 ○
```

### (5) 그래서 — 취소는 서버 쪽 설계로 막는다

- **취소해도 서버는 처리했을 수 있다**((1)) → 재시도하면 **두 번** 처리된다. 되돌릴 수 없는 요청은 **멱등 키**로 서버가 중복을 거른다([`../../../ops-patterns/06-idempotency-store/`](../../../ops-patterns/06-idempotency-store/)).
- **서버가 끊김을 처리에 전하는 장치**가 있으면 일찍 멈출 수는 있다 — Go 의 `context` 가 그런 장치다([Go 34번 주제](../../languages/go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md) — 그 편은 `net/http` 쪽을 **안 던졌다**고 적는다). 이 편의 서버는 그런 장치가 없고, 그래서 **다섯 칸 모두 끝까지** 갔다.
- ★ 데드라인을 서비스 사이에 넘기는 일반론은 [`../../../ops-patterns/deadline-propagation/`](../../../ops-patterns/deadline-propagation/) 의 몫이다.

```text
   타임아웃 뒤 재시도 — 멱등 키가 없을 때와 있을 때

   없음   1차 요청 ─▶ 서버 처리 끝(주문 1) · 응답 ✕     페이지: TimeoutError
          2차 요청 ─▶ 서버 처리 끝(주문 2)             ★ 주문이 둘
   있음   1차 요청(키 K) ─▶ 서버: K 기록 · 주문 1
          2차 요청(키 K) ─▶ 서버: K 이미 있음 → 1차의 결과를 돌려줌   (이 편은 던지지 않았다 — 06 정본)
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const c = new AbortController();   c.signal   c.abort(reason?)
   AbortSignal.abort(reason?)         처음부터 abort 된 신호
   AbortSignal.timeout(ms)            ms 뒤 TimeoutError
   AbortSignal.any([s1, s2, …])       하나라도 abort 되면 — reason 은 원인이 된 것
   fetch(url, { signal })             거부 = signal.reason · 본문 읽기도 끝난다

   관용구 — 사용자 취소 + 시간 초과, 그리고 원인 가르기
     const 사용자 = new AbortController();
     try {
       const res = await fetch(url, { signal: AbortSignal.any([사용자.signal, AbortSignal.timeout(5000)]) });
     } catch (e) {
       if (e?.name === "TimeoutError") 다시_시도할까();       ← 서버는 처리했을 수 있다(멱등 키)
       else if (e?.name === "AbortError") 조용히_끝();
       else throw e;
     }
```

### 어디서 헷갈리나

```text
   catch 에서 가르는 법 — 받은 것으로

   e?.name === "TimeoutError"   시간 초과     재시도 후보 — 서버는 처리했을 수 있다
   e?.name === "AbortError"     사람이 취소   조용히 끝
   그 밖(문자열 등)             abort(이유)   signal.aborted 로 판정
```

- **`abort()` 한 뒤의 거부 이름은 reason 에 달렸다** — 이유를 주면 그 값 그대로((2)).
- **취소는 페이지 쪽 일이다** — 서버는 처리를 마쳤다((1)).
- **본문 쪽 오류는 `signal.reason` 과 다른 객체였다**((3)).

## 어디서 틀리나

### 1. 타임아웃이 났으니 서버는 처리 안 했다고 믿고 다시 보낸다

**`timeout(1000)` 칸에서도 서버는 「처리 끝」** 이었다((1)). 다시 보내면 **두 번** 처리된다. 멱등 키로 막는다.

### 2. 「보내자마자 `abort()`」면 안 간다고 믿는다

**100번 중 몇 번은 서버에 닿았다**((4)). 보내지 않으려면 **보내기 전에** 막는다(이미 abort 된 signal · `fetch` 를 안 부르기).

### 3. `catch` 에서 `e.name === "AbortError"` 로만 거른다

**`abort("그만")` 은 문자열**이 온다((2)). **`TimeoutError`** 도 따로 온다. reason 을 줄 때는 **`DOMException`·`Error` 로** 주거나 `signal.aborted` 로 판정한다.

### 4. 응답을 받았으니 `abort()` 해도 본문은 읽힌다고 믿는다

**다 도착했어도 안 읽었으면 `text()` 가 `AbortError`**((3)). 읽을 것은 **abort 전에** 다 읽는다.

### 5. 본문 쪽 오류를 `e === signal.reason` 으로 판정한다

**이 판에서는 `false`** 였다((3)). 이름(`AbortError`)이나 `signal.aborted` 를 본다.

### 6. 한 컨트롤러를 여러 요청에 돌려 쓴다

**한 번 abort 된 신호로는 다음 `fetch` 가 곧바로 거부된다**((1)의 첫 칸 — 서버에 안 간다). 요청마다 새 컨트롤러를 만든다([20번 주제](../20-listener-lifetime/2-summary.md)의 「abort 한 컨트롤러를 다음에도 쓴다」와 같은 사고).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 이미 abort 된 signal → 곧바로 거부 · 요청 안 나감 | **명세**(Fetch — signal is aborted 면 abort the fetch() call) · 이 판의 서버 로그도 그랬다((1)) |
| 거부 = **signal 의 abort reason**(문자열이면 문자열) | **명세**(Fetch — abort the fetch() call with … abort reason) · 이 판도 그랬다((2)·(3)의 「다」) |
| `timeout()` → `TimeoutError` · `abort()` → `AbortError` · `any()` → 원인의 것 | **명세**(DOM) · 이 판도 그랬다((2)) |
| ★ 취소해도 **서버는 처리를 마친다** | **명세에 서버 쪽 단계가 없다** — ★ **서버 로그가 증명**((1)). 서버가 멈추느냐는 서버 설계다 |
| ★ 같은 잡의 `abort()` 가 요청을 막느냐 | ★ **정해져 있지 않다** — 이 판은 100번 중 몇 번 닿았다((4)) |
| ★ 본문 쪽 오류가 `signal.reason` 과 **다른 객체** · 문구 둘 | ★ **이 판의 관찰** — 명세 문장(같은 error 로 본문을 error)과 다르다 |
| 취소가 **연결을 닫는 것**으로 보인 것 | ★ **이 판의 관찰**(HTTP/1.1) |
| 오류 문구 | ★ **Chrome 의 글자** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 사용자가 떠나거나 다른 검색어를 쳤다 | `controller.abort()` | 결과를 받고 버리기 |
| 시간 상한 | `AbortSignal.timeout(ms)` | `setTimeout` + `abort` 를 손으로 |
| 둘 다 | `AbortSignal.any([사용자, 타임아웃])` | 타이머와 컨트롤러를 따로 관리 |
| 되돌릴 수 없는 요청의 재시도 | 멱등 키 + 서버가 중복 거르기 | 「취소했으니 다시 보내도 된다」 |
| 시작도 하기 전에 포기 | `fetch` 를 안 부르기 · 이미 abort 된 signal | 부르자마자 `abort()` |

## 핵심 문장

1. **취소는 요청을 없던 일로 만들지 않는다** — 서버에서 끝까지 처리된 칸 6 / 7, 안 된 칸은 요청이 아예 안 나간 하나.
2. **서버는 연결 닫힘을 알고도 처리를 마쳤고, 답을 쓰다 `BrokenPipeError` 를 받았다.**
3. **`timeout()` 은 `TimeoutError`, `abort()` 는 `AbortError`, `any()` 는 먼저 끊은 쪽 것** — 이유를 주면 그 값 그대로.
4. **응답이 다 와 있어도 안 읽었으면 `abort()` 로 본문이 끝난다** — 그 오류는 이 판에서 `signal.reason` 과 다른 객체였다.
5. **「부르자마자 `abort()`」도 서버에 닿을 수 있다** — 결정적으로 막는 것은 보내기 전의 abort 뿐이다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 27번)
- [20번 주제](../20-listener-lifetime/2-summary.md) — **`AbortSignal` 의 리스너 쪽 정본**(떼기 · 이미 abort 된 신호 · `any`·`timeout` 판별). 여기는 **`fetch` 쪽**
- [JS 41번 주제](../../languages/js/syntax/41-cancellation-and-timeouts/2-summary.md) — **「프라미스에는 취소가 없다」와 `reason` 의 정본**(node 두 판 + Chrome). 그쪽은 `fetch` 를 **node 안의 서버**로 끊어 「서버는 이미 받았다」까지, 여기는 **처리 끝 · 응답 쓰기 · 본문 쪽 · 같은 잡**
- [26번 주제](../26-response-body-streaming/2-summary.md) — 본문 스트림(여기서 그것을 읽는 중에 끊었다)
- [Go 34번 주제](../../languages/go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md) — **서버 쪽이 취소를 받는 장치**의 대비(`context`)
- [`../../../ops-patterns/deadline-propagation/`](../../../ops-patterns/deadline-propagation/) — **데드라인 전파 일반론의 정본.** 여기는 브라우저의 `AbortSignal` 표면 하나
- [`../../../ops-patterns/06-idempotency-store/`](../../../ops-patterns/06-idempotency-store/) — 재시도가 두 번 처리되지 않게 하는 쪽

## 용어 풀이

- **`AbortController`/`AbortSignal`** — 취소를 거는 쪽과 받는 쪽. `fetch(…, { signal })` 에 넘긴다.
- **abort reason** — 신호에 실린 이유. 없으면 `AbortError`, `timeout` 이면 `TimeoutError`, 주면 그 값.
- **`AbortSignal.any()`** — 여러 신호 중 **하나라도** 끊기면 끊기는 신호. 이유는 원인이 된 것.
- **abort the fetch() call** — Fetch 명세의 단계. 프라미스를 거부하고 본문 스트림을 끝낸다 — **서버 쪽 단계는 없다.**
- **`BrokenPipeError`** — 상대가 닫은 연결에 쓰려다 난 오류(파이썬 서버 쪽).
- **멱등 키** — 같은 요청이 두 번 와도 한 번만 처리되게 서버가 쓰는 표.
- **취소 격자** — 취소 방식 × (페이지가 받은 것 · 서버 도착 · 처리 끝 · 응답 쓰기). 이 편의 본체.

## 더 들어가면

- **업로드 중 취소**(요청 본문 스트림)는 던지지 않았다 — 명세는 「요청 본문이 readable 이면 취소」라고 적는다.
- **`keepalive: true` 요청의 취소**는 던지지 않았다.
- **서비스 워커가 가로챈 요청의 취소**는 던지지 않았다.
