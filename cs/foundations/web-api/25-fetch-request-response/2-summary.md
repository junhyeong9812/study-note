# web-api/25 — `fetch` 와 `Request`/`Response`: 옵션·헤더·상태 코드가 예외가 아니라는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」 — 페이지가 본 것과 서버가 한 일을 나란히 놓는 「`catch` 로 간 칸」 격자다.** 200 · 404 · 500 · 아무도 안 듣는 포트 · 다른 출처의 허용 없는 POST · 허용 있는 POST 여섯 요청을 던지고, 칸마다 **`then`/`catch` · `res.ok` · `res.status` · 오류 이름**을 적은 뒤 **서버 두 대의 로그와 콘솔**을 같이 싣는다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 「ok status」(**200\~299** 범위의 상태) · fetch() 메서드 단계(「**If response is a network error, then reject p with a TypeError**」) · HTTP fetch 의 「response tainting 이 cors 이고 **CORS check 가 실패하면 network error 를 돌려준다**」 · 「forbidden request-header」(`Host` · `Cookie` · `Origin` · `Referer` · `Content-Length` · `Connection` 등, 그리고 `proxy-`·`sec-` 로 시작하는 이름) · 「forbidden response-header name」(`Set-Cookie`·`Set-Cookie2`) · `Response`/`Request` 의 `clone()`(「unusable 이면 TypeError」). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 페이지는 **서버 A**(`http://127.0.0.1`)에서 열었고, 다른 출처는 **같은 기계의 다른 포트인 서버 B** 다. **바깥 인터넷으로는 한 번도 요청하지 않았다.** 하네스는 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [JS 39번 주제](../../languages/js/syntax/39-async-await/2-summary.md)(`await`·`try`/`catch` 가 거부를 받는 자리) · [JS 37번 주제](../../languages/js/syntax/37-promise-state-model/2-summary.md)의 (5)(**미처리 거부가 언제 `unhandledrejection` 으로 보고되나** — Chrome 에서도 쟀다) · [JS 32번 주제](../../languages/js/syntax/32-error-handling-and-error/2-summary.md)의 (3)(`TypeError` 가 어느 가족인가). ★ CORS 자체(단순 요청·프리플라이트)는 [목록의 **28번 주제**](../28-cors-simple-and-preflight/)의 몫이다 — 여기서는 **「거부돼도 요청은 갔다」** 한 가지만 본다.\
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
| **안 흔들린다** | 격자 여섯 줄 · 콘솔 다섯 줄 · 서버 로그 · 값 다루기 · 헤더 · `urllib` 대비 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들렸다가 고쳤다** | **서버 로그의 마지막 줄이 빠지는 것** — `urllib` 블록에서 한 판 | 클라이언트는 **헤더만 받고도** 돌아온다. 서버가 로그를 남기기 전에 찍었다. **처리 중인 요청이 0 이 될 때까지** 기다린 뒤 찍게 고쳤다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다(이름 A·B 로 바꿔 적는다) |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `res.ok` · `res.status` · `res.headers.get()` · `document.cookie` |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 같은 `Request` 를 두 번 `fetch` ((4)) |
| **창 ④ 서버 요청 로그 — 페이지 대 서버** | ★★★ **본체** | 요청이 **도착했나** · 서버가 **처리했나** · 어떤 헤더가 **실제로 실렸나** |
| **콘솔(CDP Log 도메인)** | ★★ **쓴다** | `catch` 가 **말해 주지 않는** 이유(CORS 문구) |
| 파이썬 `urllib` | ★ **대비** | 같은 404 에 **다른 언어는 예외를 던진다** |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★ **실제 네트워크 끊김**(와이파이·DNS 실패·중간 장비) | 로컬 루프백만 썼다. 「네트워크 실패」는 **아무도 안 듣는 포트**(`ERR_CONNECTION_REFUSED`) 한 가지로만 흉내 냈다 |
| **HTTP/2 · HTTP/3 에서의 헤더 이름 글자꼴** | 이 판은 HTTP/1.1 이다 — 헤더 이름이 **보낸 글자꼴 그대로** 서버에 닿았다((5)). HTTP/2 에서 어떻게 되는지는 이 판으로 못 본다 |
| **리다이렉트 · 캐시 · 서비스 워커** | 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ `fetch` 는 「편지가 돌아왔나」만 약속한다. 답장에 「없는 주소입니다(404)」라고 적혀 있어도 편지는 돌아왔으니 `then` 이다. `catch` 는 편지 자체가 안 돌아왔을 때(가는 길이 끊김 · 문지기가 답장을 못 읽게 막음)만 돈다 — 그리고 그때 문지기가 막는 것은 보내기가 아니라 읽기다.**

| 비유 | 실체 |
|---|---|
| 답장이 돌아왔다 | 프라미스 이행(`then`) — 상태 코드가 무엇이든 |
| 답장의 내용 | `res.status` · `res.ok`(200\~299 면 참) |
| 편지가 안 돌아왔다 | 거부(`catch`) — `TypeError 「Failed to fetch」` |
| 문지기가 답장을 못 읽게 막음 | CORS 거부 — **서버는 이미 받고 처리했다** |
| 편지 봉투에 못 쓰는 칸 | 금지 헤더(`Host` · `Cookie` · `Origin` …) — 써도 **예외 없이 지워진다** |

```text
   ★ 여섯 요청 — then 과 catch 로 갈린다 (이 판)

   A 200           ─▶ then   ok=true   status=200
   A 404           ─▶ then   ok=false  status=404      ← 예외가 아니다
   A 500           ─▶ then   ok=false  status=500      ← 예외가 아니다
   없는 포트       ─▶ catch  TypeError 「Failed to fetch」
   B POST(허용 ✕)  ─▶ catch  TypeError 「Failed to fetch」 ← ★ 그런데 서버 B 는 주문을 처리했다
   B POST(허용 ○)  ─▶ then   ok=true   status=200
```

## 이 주제가 답하려는 질문

1. **404 에서 왜 `catch` 가 안 도나** — `fetch` 가 거부하는 것은 무엇이고, 이행하는 것은 무엇인가.
2. **CORS 로 거부될 때 서버에서는 무슨 일이 있었나** — 요청이 갔나, 처리됐나.
3. **`Request`/`Response` 를 값처럼 다룰 때의 규칙** — 만들기 · `clone()` · 한 번 쓴 요청 · 금지 헤더.

## 동작 방식

### (1) ★★★ 본체 — 「`catch` 로 간 칸」 격자

**언제 쓰나** — 「에러 처리를 했는데 404 가 화면에 안 뜬다」·「CORS 에러가 났으니 주문은 안 들어갔겠지」일 때.

**던진 것** — 여섯 요청을 차례로. 서버 A 의 `/status?code=N` 은 그 상태로 JSON 을 돌려주고, 서버 B 의 `/order` 는 본문을 받아 **「주문을 처리했다」** 고 로그를 남긴 뒤 200 을 준다 — `acao=1` 일 때만 `Access-Control-Allow-Origin: *` 를 붙인다.

```html
<!-- wa24b-25-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>25 grid</title>
<script>
// 다섯(+하나) 요청 — 각각 then 이 불렸나 · catch 가 불렸나 · res.ok · res.status · catch 의 오류
const 칸 = [
  ["A 200",            () => fetch("/status?code=200")],
  ["A 404",            () => fetch("/status?code=404")],
  ["A 500",            () => fetch("/status?code=500")],
  ["없는 포트",        () => fetch(window.__없는곳 + "/status?code=200")],
  ["B POST 허용 없음", () => fetch(window.__B + "/order", { method: "POST", body: "주문 1건" })],
  ["B POST 허용 있음", () => fetch(window.__B + "/order?acao=1", { method: "POST", body: "주문 2건" })],
];
const 너비 = t => [...t].reduce((n, ch) => n + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 한줄 = (칸들, 폭) => {                             // 칸 수가 머리와 다르면 멈춘다
  if (칸들.length !== 폭.length) throw new Error("칸 수가 어긋났다");
  return 칸들.map((c, k) => k === 칸들.length - 1 ? c : c + " ".repeat(Math.max(폭[k] - 너비(c), 1))).join("");
};
window.__끝 = async () => {
  const 폭 = [18, 6, 7, 8, 12, 0];
  const O = [한줄(["요청", "then", "catch", "res.ok", "res.status", "catch 의 오류"], 폭)];
  let 잡힘 = 0;
  for (const [이름, 부름] of 칸) {
    let row;
    await 부름().then(
      res => { row = [이름, "불림", "—", String(res.ok), String(res.status), "—"]; },
      err => { 잡힘++; row = [이름, "—", "불림", "—", "—", err.name + " 「" + err.message + "」"]; });
    O.push(한줄(row, 폭));
  }
  O.push("catch 로 간 칸 = " + 잡힘 + " / " + 칸.length);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py console wa24b-25-grid.html | sed -n '1,8p'
요청              then  catch  res.ok  res.status  catch 의 오류
A 200             불림  —     true    200         —
A 404             불림  —     false   404         —
A 500             불림  —     false   500         —
없는 포트         —    불림   —      —          TypeError 「Failed to fetch」
B POST 허용 없음  —    불림   —      —          TypeError 「Failed to fetch」
B POST 허용 있음  불림  —     true    200         —
catch 로 간 칸 = 2 / 6
(exit 0)
```

- ★★★ **`catch` 로 간 칸 2 / 6** — 없는 포트와 허용 없는 다른 출처 POST 뿐이다. **404·500 은 `then`** 이고 `res.ok` 만 `false` 다.
- ★★ **두 `catch` 의 오류가 한 글자도 같다** — `TypeError 「Failed to fetch」`. 페이지는 **「연결이 안 됐다」와 「CORS 로 막혔다」를 가를 수 없다.**
- ★ Fetch 명세 그대로 — **「ok status 는 200\~299」** 이고, 거부는 **「response 가 network error 일 때 `TypeError`」** 뿐이다. 404 응답은 network error 가 아니다.

### (2) ★★★ 서버는 처리했는데 페이지만 못 읽는다 — 콘솔과 서버 로그

```text
$ python3 wa24b-net.py console wa24b-25-grid.html | sed -n '/^--- 콘솔/,$p'
--- 콘솔 ---
network · error · Failed to load resource: the server responded with a status of 404 (Not Found)
network · error · Failed to load resource: the server responded with a status of 500 (Internal Server Error)
network · error · Failed to load resource: net::ERR_CONNECTION_REFUSED
javascript · error · Access to fetch at 'http://<B>/order' from origin 'http://<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=404  → 404 응답을 끝까지 보냈다
A GET /status?code=500  → 500 응답을 끝까지 보냈다
B POST /order  Origin=http://127.0.0.1:<A> · 본문 「주문 1건」 → 주문을 처리했다 · 200 을 보냈다 · 허용 헤더 없음
B POST /order?acao=1  Origin=http://127.0.0.1:<A> · 본문 「주문 2건」 → 주문을 처리했다 · 200 을 보냈다 · 허용 헤더 있음
(exit 0)
```

- ★★★ **서버 B 의 로그에 「허용 헤더 없음」 POST 가 있다** — **도착했고 · 본문 「주문 1건」을 받았고 · 주문을 처리했고 · 200 을 보냈다.** 페이지는 `TypeError` 를 받았다. **CORS 가 막은 것은 전송이 아니라 응답 읽기다.** Fetch 명세도 CORS 검사를 **응답을 받은 뒤**(「a CORS check for request **and response** returns failure」) 한다.
- ★★ **이유는 `catch` 가 아니라 콘솔에만 있다** — `Access to fetch at 'http://<B>/order' from origin 'http://<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header …`. 스크립트는 이 문구를 **읽을 수 없다.**
- ★ **콘솔은 404·500 을 `error` 수준으로 적는다**(`Failed to load resource: the server responded with a status of 404`) — **그런데 스크립트에서는 예외가 아니다.** 콘솔의 빨간 줄과 `catch` 는 서로 다른 창이다.
- **없는 포트는 `net::ERR_CONNECTION_REFUSED`**, CORS 는 `net::ERR_FAILED` 로 콘솔에 따로 남았다.

```text
   ★ 페이지와 서버 B — 허용 헤더 없는 POST 한 번 (시간은 아래로)

   페이지(A 출처)                               서버 B
   fetch(B/order, POST 「주문 1건」) ────────▶ 도착 · Origin=<A>
                                                주문을 처리했다   ★ 이미 일어났다
                                   ◀──────── 200 (Access-Control-Allow-Origin 없음)
   브라우저: CORS 검사 실패 → network error
   catch  TypeError 「Failed to fetch」          (서버는 모른다)
   콘솔   「… blocked by CORS policy …」          (스크립트는 못 읽는다)
```

### (3) ★★ 아무도 안 받은 거부 — `unhandledrejection`

**[JS 37번 주제](../../languages/js/syntax/37-promise-state-model/2-summary.md)의 (5)가 「거부를 아무도 안 받으면 체크포인트 뒤 태스크 하나로 `unhandledrejection`」을 Chrome 에서 쟀다.** 여기서는 **`fetch` 둘에 `catch` 를 안 달면** 누가 보고되나만 본다.

```html
<!-- wa24b-25-unhandled.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>25 unhandled</title>
<script>
// fetch 둘을 걸고 catch 를 안 단다 — 404 인 것과 아무도 안 듣는 포트인 것. 누가 unhandledrejection 이 되나
window.__끝 = () => new Promise(끝 => {
  const 칸 = { 걸기: "", 사백사: "(안 불림)", 없는포트: "(안 불림)", 미처리: [] };
  const 다됐나 = () => { if (칸.사백사 !== "(안 불림)" && 칸.미처리.length === 1)
    끝(["가. " + 칸.걸기, "나. 404 쪽 then → " + 칸.사백사, "다. 없는 포트 쪽 then → " + 칸.없는포트,
        "라. unhandledrejection → " + 칸.미처리.join(" · ")].join("\n")); };
  addEventListener("unhandledrejection", e => {
    칸.미처리.push("reason = " + e.reason.name + " 「" + e.reason.message + "」");
    다됐나();
  });
  fetch("/status?code=404").then(res => { 칸.사백사 = "불림 · res.ok=" + res.ok; 다됐나(); });
  fetch(window.__없는곳 + "/status?code=200").then(() => { 칸.없는포트 = "불림"; });
  칸.걸기 = "fetch 둘을 걸었다 — catch 는 안 달았다";
});
</script>
```

```text
$ python3 wa24b-net.py page wa24b-25-unhandled.html
가. fetch 둘을 걸었다 — catch 는 안 달았다
나. 404 쪽 then → 불림 · res.ok=false
다. 없는 포트 쪽 then → (안 불림)
라. unhandledrejection → reason = TypeError 「Failed to fetch」
--- 서버 로그 ---
A GET /status?code=404  → 404 응답을 끝까지 보냈다
(exit 0)
```

- ★★ **404 쪽은 `then` 이 불렸고(`ok=false`) 보고되지 않았다** — 거부가 아니다.
- ★★ **없는 포트 쪽만 `unhandledrejection`**(reason `TypeError 「Failed to fetch」`). 「`then` 만 달고 `catch` 를 잊은 코드」에서 **404 는 조용히 지나가고** 연결 실패만 보고된다.
- ★ 이 페이지는 **http 로 열었다** — `file://` 로 열면 오류가 muted 되어 이 이벤트가 아예 안 온다(가이드 규칙 34).

```text
   catch 없는 fetch 둘 — 무엇이 보고되나

   fetch(404)        ─▶ 이행 ─▶ then(ok=false)            보고할 것 없음   ★ 조용히 지나간다
   fetch(없는 포트)  ─▶ 거부 ─▶ 받는 쪽 없음 ─▶ unhandledrejection(TypeError)
```

### (4) `Request`/`Response` 를 값으로 — 네트워크 없이 만들고, 한 번 쓴 요청

```html
<!-- wa24b-25-value.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>25 value</title>
<script>
// Request·Response 를 네트워크 없이 값으로 — 만들고, 읽고, clone 하고, 다시 쓴다
const 이름 = e => e.name + " 「" + e.message + "」";
window.__끝 = async () => {
  const O = [];
  const r1 = new Response('{"n":1}', { status: 404, headers: { "Content-Type": "application/json" } });
  O.push("가. new Response(…, {status:404}) → ok=" + r1.ok + " · status=" + r1.status +
         " · statusText=" + JSON.stringify(r1.statusText) + " · type=" + r1.type + " · url=" + JSON.stringify(r1.url));
  O.push("   json() → " + JSON.stringify(await r1.json()));
  const r2 = Response.json({ n: 2 });
  O.push("나. Response.json({n:2}) → status=" + r2.status + " · Content-Type=" + r2.headers.get("content-type"));
  try { new Response("x", { status: 99 }); } catch (e) { O.push("다. status 99 → " + 이름(e)); }
  try { new Response("x", { status: 204 }); } catch (e) { O.push("   status 204 에 본문 → " + 이름(e)); }
  const 요청 = new Request("/status?code=201", { method: "POST", body: "하나" });
  O.push("라. new Request(…) → method=" + 요청.method + " · bodyUsed=" + 요청.bodyUsed);
  const 복사 = 요청.clone();
  const a = await fetch(요청);
  O.push("   fetch(요청) → status=" + a.status + " · 그 뒤 요청.bodyUsed=" + 요청.bodyUsed);
  try { await fetch(요청); } catch (e) { O.push("   fetch(요청) 한 번 더 → " + 이름(e)); }
  const b = await fetch(복사);
  O.push("   fetch(복사) — 미리 clone 한 것 → status=" + b.status);
  const 바꿈 = new Request(복사.url, { method: "PUT" });
  O.push("마. new Request(url, {method:'PUT'}) → method=" + 바꿈.method);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-25-value.html
가. new Response(…, {status:404}) → ok=false · status=404 · statusText="" · type=default · url=""
   json() → {"n":1}
나. Response.json({n:2}) → status=200 · Content-Type=application/json
다. status 99 → RangeError 「Failed to construct 'Response': The status provided (99) is outside the range [200, 599].」
   status 204 에 본문 → TypeError 「Failed to construct 'Response': Response with null body status cannot have body」
라. new Request(…) → method=POST · bodyUsed=false
   fetch(요청) → status=201 · 그 뒤 요청.bodyUsed=true
   fetch(요청) 한 번 더 → TypeError 「Failed to execute 'fetch' on 'Window': Cannot construct a Request with a Request object that has already been used.」
   fetch(복사) — 미리 clone 한 것 → status=201
마. new Request(url, {method:'PUT'}) → method=PUT
--- 서버 로그 ---
A POST /status?code=201  → 201 응답을 끝까지 보냈다
A POST /status?code=201  → 201 응답을 끝까지 보냈다
(exit 0)
```

- **`new Response(…, { status: 404 })` 도 `ok=false`** — 네트워크를 안 거친 응답이라 `type=default` · `url=""` 이다. **테스트에서 가짜 응답을 만들 때 쓴다.**
- **`Response.json()` 은 `Content-Type: application/json` 과 200** 을 채운다.
- ★ **상태 99 는 `RangeError`**(범위 `[200, 599]` — 문구가 범위를 말한다), **204 에 본문을 주면 `TypeError`**(「null body status」).
- ★★ **본문 있는 `Request` 는 한 번 쓰면 끝이다** — 첫 `fetch(요청)` 뒤 `bodyUsed=true`, 둘째는 `TypeError 「… Cannot construct a Request with a Request object that has already been used.」`. **미리 `clone()` 한 쪽은 멀쩡히** 나갔다(서버 로그에 POST 둘).
- **`new Request(url, { method: "PUT" })`** — 값을 바꾼 새 요청은 이렇게 만든다.

```text
   본문 있는 Request 의 한살이 (이 판)

   new Request(…, { body })   bodyUsed=false
        │ clone() ─────────────▶ 복사(본문 따로)   ← 보내기 「전에」
        ▼
   fetch(요청)                  bodyUsed=true   ─▶ 서버 POST
   fetch(요청) 다시             ✕ TypeError 「… already been used.」
   fetch(복사)                  ─▶ 서버 POST
```

### (5) ★★ 헤더 — 이름의 글자꼴 · 붙일 수 없는 헤더 · 읽을 수 없는 헤더

```html
<!-- wa24b-25-headers.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>25 headers</title>
<script>
// 헤더 — 이름의 대소문자 · 페이지가 못 붙이는 헤더 · 페이지가 못 읽는 응답 헤더
window.__끝 = async () => {
  const O = [];
  document.cookie = "jar=1; path=/";                 // 브라우저 쿠키 통에 하나 넣어 둔다
  const h = new Headers({ "X-Probe": "a" });
  h.append("x-PROBE", "b");
  O.push("가. Headers — get('x-probe') = " + JSON.stringify(h.get("x-probe")) + " · 이름 목록 = " + JSON.stringify([...h.keys()]));
  const 붙임 = { "x-PrObE": "1", "Host": "evil.example", "Cookie": "evil=1", "Origin": "http://evil.example",
                 "Referer": "http://evil.example/", "Content-Length": "999", "Connection": "close", "Sec-Probe": "1" };
  const 담김 = new Headers();
  for (const [k, v] of Object.entries(붙임)) 담김.set(k, v);
  O.push("나. new Headers 에 담긴 이름 = " + JSON.stringify([...담김.keys()]));
  const 요청 = new Request("/headers", { headers: 붙임 });
  O.push("다. new Request(…, {headers}) 의 headers 에 남은 이름 = " + JSON.stringify([...요청.headers.keys()]));
  const res = await fetch("/headers?show=X-Probe,Host,Cookie,Origin,Referer,Content-Length,Connection,Sec-Probe",
                          { headers: 붙임 });
  O.push("라. fetch(…, {headers}) — 예외 없이 status=" + res.status);
  O.push("마. 응답 — get('x-visible') = " + JSON.stringify(res.headers.get("x-visible")) +
         " · get('set-cookie') = " + JSON.stringify(res.headers.get("set-cookie")) +
         " · 쿠키 통 = " + JSON.stringify(document.cookie.split("; ").sort()));
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-25-headers.html
가. Headers — get('x-probe') = "a, b" · 이름 목록 = ["x-probe"]
나. new Headers 에 담긴 이름 = ["connection","content-length","cookie","host","origin","referer","sec-probe","x-probe"]
다. new Request(…, {headers}) 의 headers 에 남은 이름 = ["x-probe"]
라. fetch(…, {headers}) — 예외 없이 status=200
마. 응답 — get('x-visible') = "v1" · get('set-cookie') = null · 쿠키 통 = ["jar=1","srv=1"]
--- 서버 로그 ---
A GET /headers?show=X-Probe,Host,Cookie,Origin,Referer,Content-Length,Connection,Sec-Probe  받은 헤더 이름(보낸 그대로) = Host · Connection · sec-ch-ua-platform · User-Agent · x-PrObE · sec-ch-ua · sec-ch-ua-mobile · Accept · Sec-Fetch-Site · Sec-Fetch-Mode · Sec-Fetch-Dest · Referer · Accept-Encoding · Accept-Language · Cookie
    X-Probe = 1
    Host = 127.0.0.1:<A>
    Cookie = jar=1
    Origin = (안 왔다)
    Referer = http://127.0.0.1:<A>/wa24b-25-headers.html
    Content-Length = (안 왔다)
    Connection = keep-alive
    Sec-Probe = (안 왔다)
(exit 0)
```

- **`Headers` 는 이름을 소문자로 다룬다** — `get('x-probe')` 가 `"a, b"`(같은 이름 두 값은 쉼표로), 이름 목록은 `["x-probe"]`.
- ★★ **빈 `new Headers()` 에는 금지 헤더도 담긴다**(여덟 이름 전부) — **`new Request(…, { headers })` 로 만드는 순간 `x-probe` 하나만 남는다.** 지우는 자리는 `fetch` 가 아니라 **`Request` 를 만들 때**다.
- ★★★ **`fetch` 는 예외 없이 200** — 그런데 **서버 로그를 보면 페이지가 준 값은 `x-PrObE` 하나만 닿았다.** `Host` 는 진짜 주소, **`Cookie` 는 브라우저 쿠키 통의 `jar=1`**(페이지가 준 `evil=1` 이 아니다), `Referer` 는 진짜 페이지 주소, `Sec-Probe` 는 안 왔다. **조용히 지워졌다.**
- ★ **HTTP/1.1 에서는 헤더 이름이 보낸 글자꼴 그대로(`x-PrObE`) 서버에 닿았다.** 서버의 조회는 대소문자를 안 가리므로(`X-Probe = 1`) 값은 받았다.
- ★★ **응답의 `Set-Cookie` 는 `get()` 으로 `null`** — 금지 응답 헤더다. 그런데 **쿠키 통에는 `srv=1` 이 들어갔다** — 브라우저는 처리했고 스크립트만 못 본다. `X-Visible` 은 읽힌다.

```text
   페이지가 준 헤더 → 서버가 받은 값 (이 판)

   x-PrObE: 1                 ─▶  x-PrObE = 1         ○ 그대로 (이름 글자꼴도)
   Host: evil.example         ─▶  127.0.0.1:<A>       ✕ 브라우저 것
   Cookie: evil=1             ─▶  jar=1               ✕ 쿠키 통의 것
   Referer: evil.example      ─▶  진짜 페이지 주소     ✕
   Origin · Content-Length · Sec-Probe  ─▶  안 왔다    ✕
   ★ 예외는 0 — 「보냈다」고 믿으면 서버 로그에서만 들통난다
```

### (6) 대비 — 파이썬 `urllib` 는 404 에 예외를 던진다

```text
$ python3 wa24b-net.py urllib
urlopen /status?code=200 → 돌아옴 · status 200
urlopen /status?code=404 → 예외 HTTPError 「404 Not Found」
urlopen /status?code=500 → 예외 HTTPError 「500 Internal Server Error」
--- 서버 로그 ---
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=404  → 404 응답을 끝까지 보냈다
A GET /status?code=500  → 500 응답을 끝까지 보냈다
(exit 0)
```

- ★ **같은 서버 A, 같은 404 에 `urllib.request.urlopen` 은 `HTTPError 「404 Not Found」` 를 던진다.** JS 의 `fetch` 는 `then` 이다. **「HTTP 오류 = 예외」인지는 라이브러리의 설계**이지 HTTP 의 성질이 아니다.
- 서버 로그는 세 번 다 같다 — **서버가 한 일은 같고 클라이언트가 읽는 법만 다르다.**

```text
   같은 404 — 클라이언트 둘

   서버 A           404 응답을 끝까지 보냈다        (둘 다 같다)
   JS fetch         then · ok=false · status=404    ← 예외 아님
   파이썬 urlopen   HTTPError 「404 Not Found」      ← 예외
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   fetch(input, { method, headers, body, signal, mode, credentials, cache, redirect, … })  → Promise<Response>
   Response   .ok(200~299) · .status · .statusText · .headers · .type · .url · .body · .bodyUsed · .clone()
              new Response(body, { status, statusText, headers }) · Response.json(값) · Response.error()
   Request    new Request(url 또는 Request, init) · .method · .headers · .clone()
   Headers    new Headers(객체) · .get(이름) · .set · .append · .has · 순회하면 이름은 소문자

   관용구 — 상태 코드를 예외로 올리기
     const res = await fetch(url);
     if (!res.ok) throw new Error(`HTTP ${res.status}`);     ← 이 줄이 없으면 404 는 조용히 지나간다
     const data = await res.json();
```

### 어디서 헷갈리나

- **`catch` 는 「응답이 없을 때」다** — 404·500 은 응답이다((1)).
- **CORS `TypeError` 와 연결 실패 `TypeError` 는 스크립트에서 같다**((1)) — 이유는 콘솔에만((2)).
- **금지 헤더는 예외 없이 사라진다**((5)).

## 어디서 틀리나

### 1. `try { await fetch() } catch` 만으로 오류 처리가 끝났다고 믿는다

**404·500 은 `then`** 이다((1)). `res.ok` 를 보지 않으면 **오류 페이지 본문을 JSON 으로 읽다가** 엉뚱한 자리에서 터진다.

### 2. CORS 오류가 났으니 서버에서는 아무 일도 없었다고 믿는다

**서버 B 는 주문을 처리했다**((2)). 단순 요청(여기서는 본문이 글자인 `POST`)은 **보내지고 처리된다** — 막히는 것은 응답 읽기다. 되돌릴 수 없는 일을 하는 엔드포인트라면 서버 쪽에서 막아야 한다([목록의 **28번 주제**](../28-cors-simple-and-preflight/)).

### 3. `catch` 의 메시지로 CORS 와 연결 실패를 가른다

**둘 다 `Failed to fetch`** 다((1)). 스크립트는 못 가른다.

### 4. `fetch(…, { headers: { Cookie: … } })` 로 쿠키를 보낸다

**조용히 지워지고 쿠키 통의 값이 간다**((5)). 쿠키는 `credentials` 와 브라우저 쿠키 통의 몫이다([목록의 **29번 주제**](../29-credentials-and-cookies/)).

### 5. 한 `Request` 객체로 재시도한다

**본문이 있으면 두 번째가 `TypeError`**((4)). 재시도할 요청은 **보내기 전에 `clone()`** 해 둔다.

### 6. `then` 만 달고 `catch` 를 잊는다

**404 는 조용히 지나가고 연결 실패만 `unhandledrejection`** 이 된다((3)).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `ok` 는 200\~299 · 404·500 에서 이행 | **명세**(Fetch — ok status · fetch() 는 network error 일 때만 `TypeError` 로 거부) · 이 판도 그랬다((1)) |
| CORS 검사 실패 → network error → `TypeError` | **명세**(Fetch — CORS check 실패면 network error) · 이 판도 그랬다((1)) |
| ★ CORS 로 거부돼도 **요청은 서버에 닿고 처리된다** | **명세의 순서**(검사는 **응답**에 대해 한다) · ★ **서버 로그가 증명**((2)) |
| 금지 요청 헤더가 지워지는 것 · `Set-Cookie` 를 못 읽는 것 | **명세**(Fetch — forbidden request-header · forbidden response-header name) · 이 판도 그랬다((5)) |
| 한 번 쓴 본문 있는 `Request` 는 다시 못 쓴다 · `clone()` | **명세**(Fetch — unusable · clone) · 이 판도 그랬다((4)) |
| 오류 **문구**(`Failed to fetch` 등) | ★ **Chrome 의 글자** — 명세는 `TypeError` 만 정한다 |
| 콘솔의 CORS 설명 · 404 를 `error` 로 적는 것 | ★ **Chrome 개발자 도구의 성질** |
| 헤더 이름이 **보낸 글자꼴 그대로** 닿은 것 | ★ **이 판의 관찰**(HTTP/1.1) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 상태 코드로 오류 처리 | `if (!res.ok) throw …` | `catch` 만 |
| 테스트용 가짜 응답 | `new Response(…)` · `Response.json(…)` | 진짜 서버 |
| 같은 요청 재시도 | 보내기 전 `req.clone()` | 쓴 `Request` 재사용 |
| 쿠키·출처 헤더 | 브라우저에 맡김(`credentials`) | `headers` 에 직접 |
| 되돌릴 수 없는 다른 출처 요청 | 서버가 `Origin`·토큰으로 막음 | 「CORS 가 막아 주겠지」 |

## 핵심 문장

1. **`fetch` 는 응답이 오면 이행한다** — 404·500 도 `then` 이고 `res.ok` 만 거짓이다(`catch` 로 간 칸 2 / 6).
2. **거부는 network error 일 때 `TypeError` 하나** — 연결 실패와 CORS 거부가 스크립트에서 **같은 글자**다.
3. **CORS 가 막는 것은 응답 읽기다** — 서버 B 는 허용 헤더 없는 POST 를 **받고 처리했다.**
4. **금지 헤더는 `Request` 를 만들 때 예외 없이 지워진다** — 서버 로그로만 보인다.
5. **본문 있는 `Request` 는 한 번 쓰면 끝이다** — 재사용하려면 먼저 `clone()`.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 25번)
- [JS 37번 주제](../../languages/js/syntax/37-promise-state-model/2-summary.md) — **미처리 거부 보고의 정본.** 그쪽은 언어·호스트의 틀, 여기는 **`fetch` 의 거부가 보고되는 자리**
- [JS 39번 주제](../../languages/js/syntax/39-async-await/2-summary.md) — `await`·`try` 로 거부를 받는 문법
- [JS 32번 주제](../../languages/js/syntax/32-error-handling-and-error/2-summary.md) — `TypeError`·`RangeError` 의 가족
- [HTML 21번 주제](../../languages/html/syntax/21-form-submission-model/2-summary.md) — 폼 제출이 서버에 싣는 것과 **`curl` 우회**(「서버는 창구를 거쳤는지 모른다」). 여기는 **스크립트의 `fetch`** 가 무엇을 싣고 무엇이 지워지나
- [목록의 **28번 주제**](../28-cors-simple-and-preflight/) — **CORS 의 정본**(단순 요청·프리플라이트). 여기는 「요청은 갔다」 한 가지만
- [목록의 **29번 주제**](../29-credentials-and-cookies/) — 자격 증명과 쿠키
- [26번 주제](../26-response-body-streaming/2-summary.md) — 응답 **본문**을 읽는 쪽
- [`../../../../history/web/02-HTTP-진화.md`](../../../../history/web/02-HTTP-진화.md) — HTTP 가 어떻게 바뀌어 왔나(역사는 그쪽)

## 용어 풀이

- **`fetch`** — 요청을 보내고 **응답(헤더까지)이 오면 이행**하는 프라미스를 돌려주는 함수.
- **ok status** — 200\~299. `res.ok` 가 참인 범위.
- **network error** — Fetch 명세의 「응답이 없음」. `fetch` 가 `TypeError` 로 거부하는 유일한 경우.
- **CORS 거부** — 다른 출처의 응답에 허용 헤더가 없어 브라우저가 **읽기를 막은 것.** 요청은 이미 갔다.
- **금지 헤더** — 스크립트가 설정할 수 없는 요청 헤더(`Host` · `Cookie` · `Origin` …). 예외 없이 지워진다.
- **`clone()`** — 본문까지 둘로 가르는 복사. 한 번 쓴 것은 복사할 수 없다.
- **「`catch` 로 간 칸」 격자** — 요청 여섯 × (`then`/`catch`·`ok`·`status`·오류). 이 편의 본체.

## 더 들어가면

- **`mode: "no-cors"`** 는 불투명 응답(`status 0`)을 준다 — 던지지 않았다(28번 주제).
- **리다이렉트(`redirect: "manual"`)** 와 **`Response.error()`** 는 던지지 않았다.
- **HTTP/2 에서의 헤더 이름 글자꼴**은 이 판의 서버(HTTP/1.1)로는 못 본다.
