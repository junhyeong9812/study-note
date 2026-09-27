# web-api/34 — `navigator.sendBeacon` 과 이탈 시점 전송: `fetch` 의 `keepalive` 와의 관계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」로 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 「떠날 때」 격자에 열을 더한 「떠날 때 전송 격자」다.** 24편은 **떠날 때 어느 이벤트가 불리나**를 쟀다. 여기서는 그 이벤트 안에서 **한 번 보낸 요청이 서버에 닿았나**, 그리고 서버가 응답을 붙잡았다가 놓는 순간 **그 연결이 아직 살아 있었나**를 잰다. 전송 수단 5(`fetch` · `fetch keepalive` · `sendBeacon` · `img.src` · 동기 XHR) × 부르는 자리 4(`visibilitychange → hidden` · `pagehide` · `beforeunload` · `unload`) × 떠나는 방식 2(링크 · 탭 닫기) = **40칸을 5판** 돌려 **칸마다 「5판 중 몇 판」** 으로 적는다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/)(앞 배치가 받아 둔 사본에서 열었다) — request 의 **keepalive**(「요청이 **environment settings object 보다 오래 살게** 하는 데 쓸 수 있다 — 예: **`navigator.sendBeacon()` 과 HTML `img` 요소가 이것을 쓴다**」) · **fetch group 이 terminated 될 때**(「fetch record 마다 — controller 가 있고 **done 이 아니고 keepalive 가 false 면 그 controller 를 terminate 한다**」) · HTTP-network-or-cache fetch 의 **한도**(「contentLength 와 **아직 안 끝난 keepalive 요청들의 본문 길이 합**이 **64 kibibytes 보다 크면 network error**」) · 본문 추출(「본문이 `ReadableStream` 이고 **keepalive 가 true 면 `TypeError` 를 던진다**」). ★ **[W3C Beacon](https://w3c.github.io/beacon/) 과 HTML 명세의 「page dismissal 중 동기 XHR」 문장은 이 판에서 열지 못했다**(외부 네트워크를 쓰지 않았고 사본이 없다) — 그쪽 서술은 **관찰**로만 적는다. 열어서 확인한 것만 명세로 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 링크는 **CDP 로 넣은 진짜 마우스**로 누르고, 탭 닫기는 **`Page.close`** 다(24편 (3) — `Target.closeTarget` 은 `beforeunload` 를 안 부른다). 서버는 [32번 주제](../32-server-sent-events/2-summary.md)의 (1) `/beacon`·`/big` 이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** ★★ **서버는 같은 기계(localhost)다** — 요청이 선에 오르는 데 걸리는 시간이 거의 0 이다. 먼 서버 · 느린 선에서의 「닿았나」는 이 판이 말하지 않는다.\
> **선행** — ★★★ **[24번 주제](../24-document-lifecycle-events/2-summary.md)** — (2)의 「떠날 때」 격자(**`visibilitychange → hidden` 은 7행 전부**) · (3) 탭 닫기 두 명령 · (4) **`unload` 리스너 하나가 문서를 bfcache 에서 뺀다.** 여기서는 **다시 재지 않고 인용**한다. ★★ **[25번 주제](../25-fetch-request-response/2-summary.md)** — 서버 요청 로그 창. ★ **[27번 주제](../27-abort-and-timeout/2-summary.md)의 (4)** — **같은 잡에서 `abort()` 해도 요청이 서버에 닿은 판이 있었다.** 여기의 「잘리나」도 같은 모양일 수 있어 **판 수로** 적는다. ★ [31번 주제](../31-blob-file-and-object-url/2-summary.md)의 (5) — **「떠났다」와 「파괴됐다」가 bfcache 에서 갈린다.**\
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
| **안 흔들린다** | 격자 40칸의 「닿은 판 / 5」와 「살아 있던 판」 · 동기 결과 · 64KiB 표 · `Content-Type` 표 · 콘솔 · 8 MiB 세 줄 | **판 안에서 5판**, 캡처 세 판이 **한 글자도 같았다** — 판마다 갈린 칸 `0 / 40` |
| ★ **흔들리게 만들지 않았다** | 8 MiB 가 **얼마나** 올라갔나 | 바이트 수를 찍지 않고 **「끝까지 받았나」·「받은 것이 있나」** 만 찍었다 |
| ★ **판에 매일 수 있는 칸** | 「닿았다」 전부 | **localhost** 라서 닿는 데 시간이 거의 안 든다(머리말). 27편에서 `abort()` 가 **따라잡지 못한 것**과 같은 성질일 수 있다 — 먼 서버라면 **안 닿는 판이 나올 수 있다** |
| **흔들린다** | Chrome 판 번호 · 포트 · multipart 경계 | 포트는 출력에 안 나온다 · 경계는 뒤 16자를 가린다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `sendBeacon` 의 반환값 · `fetch` 의 `then`/`catch` · 던진 예외 |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | — |
| **창 ④ 서버 요청 로그 → 떠날 때 전송 격자** | ★★★ **본체** | 닿았나(5판 중 몇 판) · 응답을 놓을 때 연결이 살아 있었나 · 메서드 · `Content-Type` · 본문 길이 · 프리플라이트 |
| ★ **「잘렸나」를 서버 쪽 소켓으로** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 떠난 페이지는 **`then` 도 `catch` 도 적지 못한다**(문서가 없다). 그래서 **서버가 응답을 놓는 순간 소켓이 닫혔나**로 물었다. ★ 바꾼 창이 못 보는 것 — **브라우저가 응답을 받아 어디에 버렸나** |
| ★ **동기 결과를 다른 탭에서** | ★ **같은 질문을 다른 창으로** | 떠나는 페이지가 **localStorage 에 적어 두고**, 하네스가 **같은 출처의 다른 탭에서** 읽는다(24편의 기록기와 같은 수) |
| 콘솔(Log 도메인) | ★ **쓴다** | 교차 출처 프리플라이트 거부 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **먼 서버 · 느린 선에서 닿나** | localhost 뿐이다(머리말) |
| **모바일의 백그라운드 전환 · 프로세스 강제 종료** | 24편과 같다 — 헤드리스 데스크톱이다 |
| **사용자가 창을 닫는 것** | `Page.close` 로 흉내 냈다(24편 (3)) |
| **브라우저가 보내기를 미루다 언제 보냈나** | 서버가 받은 것만 본다 — 떠난 뒤 2초 안에 닿았나까지 |
| **`fetchLater()`**(명세의 deferred fetching) | 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ 떠나는 중에 보내는 요청은 「이사 가는 날 부치는 편지」다. 보통 `fetch` 는 **직접 들고 우체국까지 걸어가는 편지**라, 집(문서)이 헐리면 들고 가던 사람도 사라진다 — 편지가 우체통에 이미 들어갔으면 가지만, 답장은 받을 사람이 없다. `keepalive` · `sendBeacon` 은 **우체국 수거함에 넣는 편지**다 — 집이 헐려도 우체국(브라우저)이 끝까지 배달한다. 대신 수거함에는 **한 번에 64KiB** 까지만 들어간다. 동기 XHR 은 **「답장 올 때까지 이사를 멈춰라」** 인데 — 브라우저가 이제 그 부탁을 안 들어준다.**

| 비유 | 실체 |
|---|---|
| 들고 가는 편지 | `fetch`(keepalive 없음) — **문서가 파괴되면 끊긴다**(Fetch: fetch group terminated → keepalive 가 false 인 것만 terminate) |
| 우체국 수거함 | `keepalive: true` · `sendBeacon` · `img.src` — 문서보다 오래 산다(Fetch 의 keepalive 설명) |
| 수거함 크기 | 아직 안 끝난 keepalive 요청 본문의 **합** ≤ 64KiB |
| 집이 헐림 | 탭 닫기 · bfcache 에 못 들어간 이동(24편 (4)) |
| 잠깐 집을 비움 | bfcache 에 들어간 이동 — 문서가 살아 있다(31편 (5)) |
| 「이사를 멈춰라」 | 떠나는 중의 동기 XHR — Chrome 이 `NetworkError` 로 거절 |

```text
   떠나는 중에 한 번 보낸 요청 — 이 판에서 무엇이 잘렸나

   페이지 ── 요청 ──▶ 서버(받자마자 응답을 붙잡는다)
      │ 떠남                       │ 0.5초 뒤 응답을 놓으며 「연결 살아 있나?」
      ▼
   탭 닫기 ─ 문서 파괴 ─ fetch(보통) 연결 끊김 ✕   ← 요청은 이미 닿았다 · 응답이 잘렸다
                        keepalive · beacon · img ○ 끝까지
   링크(bfcache) ─ 문서 살아 있음 ─ fetch(보통)도 ○
   링크(unload 리스너 — bfcache 밖) ─ 문서 파괴 ─ fetch(보통) ✕
```

## 이 주제가 답하려는 질문

1. **떠나는 중에 보낸 요청은 서버에 닿나 — 무엇이 잘리나** — 요청인가, 응답(연결)인가, 큰 본문인가.
2. **`keepalive` · `sendBeacon` 은 무엇을 다르게 하나** — 그리고 그 대가(64KiB · 반환값의 뜻 · `Content-Type`)는 무엇인가.
3. **어느 자리에서 부르나** — 24편의 격자 위에서, 네 자리 중 어디가 빠짐없이 불리고 무엇이 막히나.

## 동작 방식

### (1) ★★★ 본체 — 떠날 때 전송 격자

**한 칸** = 새 탭에서 `wa32b-34-leave.html?how=…&at=…` 을 열고 → 떠난다(링크를 진짜 마우스로 · 또는 `Page.close`) → 서버가 그 `id` 를 **2초 안에** 받았나 → **떠난 뒤 0.5초**에 서버가 붙잡았던 응답을 놓으며 **소켓이 아직 열려 있나**를 적는다. 동기 XHR 만은 응답을 붙잡지 않는다(붙잡으면 페이지가 멈춘다).

```html
<!-- wa32b-34-leave.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>34 leave</title>
<script>
// 떠나는 중에 한 번 보낸다 — 무엇으로(how) · 어느 리스너에서(at). 부른 자리의 동기 결과는 localStorage 에 적는다
const q = new URLSearchParams(location.search), how = q.get("how"), at = q.get("at"), id = q.get("id");
const url = `/beacon?id=${id}&quiet=1&hold=${how === "xhr" ? 0 : 1}`;
let 보냄 = false;
function 보내기() {
  if (보냄) return;
  보냄 = true;
  let 결과 = "(프라미스 — 결과를 못 적는다)";
  try {
    if (how === "fetch") fetch(url, { method: "POST", body: "x" });
    if (how === "keepalive") fetch(url, { method: "POST", body: "x", keepalive: true });
    if (how === "beacon") 결과 = "sendBeacon → " + navigator.sendBeacon(url, "x");
    if (how === "img") { new Image().src = url; 결과 = "(img — 결과를 못 적는다)"; }
    if (how === "xhr") { const x = new XMLHttpRequest(); x.open("POST", url, false); x.send("x"); 결과 = "동기 XHR status " + x.status; }
  } catch (e) { 결과 = "던짐 " + e.name + " 「" + e.message.replace(/'http[^']*'/, "'<URL>'") + "」"; }
  localStorage.setItem("결과-" + id, 결과);
}
if (at === "visibilitychange") document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") 보내기(); });
else addEventListener(at, 보내기);
</script>
<p><a id="go" href="wa32b-34-next.html">다음 쪽으로</a></p>
```

```html
<!-- wa32b-34-next.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>34 next</title>
<p>다음 쪽</p>
```

```html
<!-- wa32b-34-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>34 grid</title>
<script>
// 떠날 때 전송 격자 — 하네스가 칸마다 새 탭에서 wa32b-34-leave.html 을 열고 떠난다
window.__방법 = ["fetch", "keepalive", "beacon", "img", "xhr"];
window.__자리 = ["visibilitychange", "pagehide", "beforeunload", "unload"];
window.__떠남 = ["링크", "닫기"];       // 링크 = 진짜 마우스로 #go 를 누른다 · 닫기 = CDP Page.close
</script>
```

**하네스 쪽 — 32편 (1) `wa32b-net.py` 의 `leave_grid`** 가 칸마다 위 순서를 돌고, 판(5)마다 되풀이한 뒤 칸마다 「닿은 판 / 5」와 「닿은 판 중 살아 있던 판」을 센다.

```text
$ python3 wa32b-net.py leave wa32b-34-grid.html 5
떠날 때 한 번 보낸 요청 — 서버에 닿은 판 / 5판 · (닿은 판 중 응답 때 연결이 살아 있던 판)
방법	자리	링크로 떠나기	탭 닫기(Page.close)
fetch	visibilitychange	5/5 (살아 5/5)	5/5 (살아 0/5)
fetch	pagehide	5/5 (살아 5/5)	5/5 (살아 0/5)
fetch	beforeunload	5/5 (살아 5/5)	5/5 (살아 0/5)
fetch	unload	5/5 (살아 0/5)	5/5 (살아 0/5)
keepalive	visibilitychange	5/5 (살아 5/5)	5/5 (살아 5/5)
keepalive	pagehide	5/5 (살아 5/5)	5/5 (살아 5/5)
keepalive	beforeunload	5/5 (살아 5/5)	5/5 (살아 5/5)
keepalive	unload	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	visibilitychange	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	pagehide	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	beforeunload	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	unload	5/5 (살아 5/5)	5/5 (살아 5/5)
img	visibilitychange	5/5 (살아 5/5)	5/5 (살아 5/5)
img	pagehide	5/5 (살아 5/5)	5/5 (살아 5/5)
img	beforeunload	5/5 (살아 5/5)	5/5 (살아 5/5)
img	unload	5/5 (살아 5/5)	5/5 (살아 5/5)
xhr	visibilitychange	5/5	0/5
xhr	pagehide	5/5	0/5
xhr	beforeunload	0/5	0/5
xhr	unload	0/5	0/5
한 판이라도 서버에 안 닿은 칸 = 6 / 40
판마다 갈린 칸(0 < 닿은 판 < 5) = 0 / 40
--- 부른 자리에서 페이지가 적은 동기 결과(첫 판) ---
beacon	visibilitychange	sendBeacon → true	sendBeacon → true
beacon	pagehide	sendBeacon → true	sendBeacon → true
beacon	beforeunload	sendBeacon → true	sendBeacon → true
beacon	unload	sendBeacon → true	sendBeacon → true
xhr	visibilitychange	동기 XHR status 204	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	pagehide	동기 XHR status 204	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	beforeunload	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	unload	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
(exit 0)
```

- ★★★ **서버에 닿지 않은 칸 6 / 40 — 여섯 칸 전부 동기 XHR 이다.** `fetch` · `keepalive` · `sendBeacon` · `img.src` 는 **네 자리 × 두 방식 32칸 전부 5/5 닿았다.** 판마다 갈린 칸 **0 / 40**.
- ★★★ **잘린 것은 요청이 아니라 연결이었다** — 보통 `fetch` 는 **탭을 닫으면 네 자리 모두 「살아 0/5」**: 요청은 닿았는데 **응답을 놓을 때 소켓이 이미 닫혀 있었다.** Fetch 명세 그대로 읽힌다 — **fetch group 이 terminated 되면 keepalive 가 false 인 진행 중 fetch 를 끊는다.** 누가 언제 그 terminate 를 부르나(HTML 쪽 문장)는 이 판에서 열지 못했다.
- ★★★ **`keepalive` · `sendBeacon` · `img.src` 는 탭을 닫아도 「살아 5/5」** — 문서가 사라진 뒤에도 브라우저가 응답까지 받아 갔다. Fetch 의 keepalive 설명이 **`sendBeacon()` 과 `img` 가 이것을 쓴다**고 적는다 — `img.src` 가 같은 줄에 선 이유다.
- ★★ **링크로 떠나면 보통 `fetch` 도 「살아 5/5」 — `unload` 자리만 「살아 0/5」.** `unload` 리스너를 단 페이지는 **bfcache 에 못 들어가 떠나는 순간 파괴되고**(24편 (4)), 나머지 세 자리는 리스너가 `unload` 가 아니라서 **문서가 bfcache 에 살아 있었다**(31편 (5)의 「떠남 ≠ 파괴」). 이 판은 bfcache 에 들어갔는지를 **따로 묻지 않았다** — 24편의 결과로 읽는다.
- ★★ **동기 XHR** — 링크로 떠날 때 `visibilitychange` · `pagehide` 에서는 **`status 204` 로 돌아오고 닿았다.** 그 밖의 여섯 칸은 **던지고 안 닿았다**(아래 (2)).

```text
   떠날 때 전송 격자 — 5판 요약 (이 판)

                          링크로 떠나기                 탭 닫기(Page.close)
                          닿음   응답 때 연결            닿음   응답 때 연결
   fetch(보통) vis/ph/bu  5/5    살아 5/5 (bfcache)      5/5    ✕ 0/5 ★
   fetch(보통) unload     5/5    ✕ 0/5 (bfcache 밖)      5/5    ✕ 0/5
   keepalive · beacon     5/5    살아 5/5                5/5    살아 5/5
   img.src                5/5    살아 5/5                5/5    살아 5/5
   동기 XHR vis · ph      5/5    (붙잡지 않음)           ✕ 0/5
   동기 XHR bu · unload   ✕ 0/5                          ✕ 0/5
   ★ 안 닿은 칸 6/40 = 전부 동기 XHR · 판마다 갈린 칸 0/40 · localhost
```

### (2) ★★ 동기 XHR — 부른 자리에서 무엇을 던지나

떠나는 페이지가 localStorage 에 적어 두고, 하네스가 다른 탭에서 읽었다(첫 판).

```text
$ python3 wa32b-net.py leave wa32b-34-grid.html 5 | sed -n '/^--- 부른 자리/,$p'
--- 부른 자리에서 페이지가 적은 동기 결과(첫 판) ---
beacon	visibilitychange	sendBeacon → true	sendBeacon → true
beacon	pagehide	sendBeacon → true	sendBeacon → true
beacon	beforeunload	sendBeacon → true	sendBeacon → true
beacon	unload	sendBeacon → true	sendBeacon → true
xhr	visibilitychange	동기 XHR status 204	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	pagehide	동기 XHR status 204	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	beforeunload	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	unload	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
(exit 0)
```

- ★★ **`sendBeacon` 은 여덟 칸 모두 `true`** — 부른 자리에서 「큐에 넣었다」.
- ★★ **동기 XHR 은 탭 닫기의 네 자리 · 링크의 `beforeunload`·`unload` 에서 `NetworkError` — 문구가 이유를 말한다: `Synchronous XHR in page dismissal.`** 링크로 떠날 때의 `visibilitychange` · `pagehide` 에서는 **`status 204`** 로 돌아왔다 — 두 자리가 **「page dismissal」 로 다뤄지지 않은** 것으로 읽힌다(bfcache 로 가는 이동이다). 어느 자리를 dismissal 로 치는지의 명세 문장은 이 판에서 열지 못했다.
- ★ **「그래도 동기 XHR 로 보내면 확실하다」는 옛 처방은 이 판에서 여섯 칸이 안 닿았다.**

```text
   떠나는 중의 동기 XHR — 자리 × 방식 (이 판)

                        링크로 떠나기(bfcache 로)      탭 닫기
   visibilitychange     status 204 · 닿음              ✕ NetworkError · 안 닿음
   pagehide             status 204 · 닿음              ✕ NetworkError · 안 닿음
   beforeunload         ✕ NetworkError · 안 닿음       ✕ NetworkError · 안 닿음
   unload               ✕ NetworkError · 안 닿음       ✕ NetworkError · 안 닿음
   ★ 문구 = 「Synchronous XHR in page dismissal」 — 막힌 곳에서는 요청이 아예 안 나갔다
```

### (3) ★★ 64KiB — 혼자일 때와, 붙잡힌 keepalive 가 있을 때

```html
<!-- wa32b-34-limit.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>34 limit</title>
<script>
// keepalive · sendBeacon 의 본문 크기 한도 — 혼자일 때와, 서버가 붙잡은 keepalive 40000바이트가 하나 있을 때
const 쉬기 = ms => new Promise(r => setTimeout(r, ms));
async function 닿기(id) {                    // 서버가 받았다고 할 때까지 묻고, 한 번 더 왕복한다
  for (let k = 0; k < 200; k++) { if ((await (await fetch("/seen?id=" + id)).json()).length) break; await 쉬기(10); }
  await fetch("/seen?id=-");
}
const 결과 = async p => { try { const r = await p; return "then status " + r.status; } catch (e) { return `catch ${e.name} 「${e.message}」`; } };
const 부름 = f => { try { return f(); } catch (e) { return Promise.reject(e); } };
const 본 = n => new Uint8Array(n);
let 판 = 0;
async function 붙잡고(할일) {                 // keepalive 40000바이트를 서버가 붙잡게 해 두고 할일 → 놓고 → 가라앉힌다
  const id = "H" + 판++, 붙잡힘 = fetch(`/beacon?id=${id}&hold=1`, { method: "POST", body: 본(40000), keepalive: true });
  await 닿기(id);
  const 답 = await 할일();
  await fetch("/go?id=" + id); await 붙잡힘; await 쉬기(300);
  return 답;
}
window.__끝 = async () => {
  const 줄 = [];
  줄.push("keepalive 65536바이트            → " + await 결과(fetch("/beacon?id=L1", { method: "POST", body: 본(65536), keepalive: true })));
  줄.push("keepalive 65537바이트            → " + await 결과(fetch("/beacon?id=L2", { method: "POST", body: 본(65537), keepalive: true })));
  줄.push("keepalive 없이 65537바이트       → " + await 결과(fetch("/beacon?id=L3", { method: "POST", body: 본(65537) })));
  줄.push("sendBeacon 65536바이트           → " + navigator.sendBeacon("/beacon?id=L4", 본(65536))); await 닿기("L4"); await 쉬기(300);
  줄.push("sendBeacon 65537바이트           → " + navigator.sendBeacon("/beacon?id=L5", 본(65537)));
  줄.push("(서버가 keepalive 40000바이트를 붙잡고 있는 동안 — 한 줄에 한 번씩)");
  줄.push("  keepalive 25536바이트          → " + await 붙잡고(() => 결과(fetch("/beacon?id=L6", { method: "POST", body: 본(25536), keepalive: true }))));
  줄.push("  keepalive 25537바이트          → " + await 붙잡고(() => 결과(fetch("/beacon?id=L7", { method: "POST", body: 본(25537), keepalive: true }))));
  줄.push("  sendBeacon 25536바이트         → " + await 붙잡고(async () => { const b = navigator.sendBeacon("/beacon?id=L8", 본(25536)); await 닿기("L8"); return b; }));
  줄.push("  sendBeacon 25537바이트         → " + await 붙잡고(async () => navigator.sendBeacon("/beacon?id=L9", 본(25537))));
  const 흐름 = new ReadableStream({ start(c) { c.enqueue(new Uint8Array([1])); c.close(); } });
  줄.push("keepalive + ReadableStream 본문  → " + await 결과(부름(() => fetch("/beacon?id=L10", { method: "POST", body: 흐름, duplex: "half", keepalive: true }))));
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py page wa32b-34-limit.html
keepalive 65536바이트            → then status 204
keepalive 65537바이트            → catch TypeError 「Failed to fetch」
keepalive 없이 65537바이트       → then status 204
sendBeacon 65536바이트           → true
sendBeacon 65537바이트           → false
(서버가 keepalive 40000바이트를 붙잡고 있는 동안 — 한 줄에 한 번씩)
  keepalive 25536바이트          → then status 204
  keepalive 25537바이트          → catch TypeError 「Failed to fetch」
  sendBeacon 25536바이트         → true
  sendBeacon 25537바이트         → false
keepalive + ReadableStream 본문  → catch TypeError 「Failed to execute 'fetch' on 'Window': Keepalive request cannot have a ReadableStream body.」
--- 서버 로그 ---
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 65536바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 65537바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 65536바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 25536바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 25536바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
(exit 0)
```

- ★★ **`keepalive` 본문 65536바이트는 되고 65537바이트는 `TypeError 「Failed to fetch」`** — 서버 로그에 그 요청이 **없다**(안 보냈다). keepalive 없이 65537 은 된다. 명세 — **64 kibibytes 보다 크면 network error**(→ `fetch` 는 `TypeError` 로 거부).
- ★★ **`sendBeacon` 도 65536 은 `true`, 65537 은 `false`** — 던지지 않고 **`false` 를 돌려준다.**
- ★★★ **한도는 「합」이다** — 서버가 keepalive **40000바이트**를 붙잡고 있는 동안 keepalive 는 **25536(합 65536)까지 되고 25537 은 `TypeError`**, `sendBeacon` 도 **25536 `true` · 25537 `false`**. **`keepalive` 와 `sendBeacon` 이 같은 한도를 나눠 쓴다** — 명세의 「아직 안 끝난 keepalive 요청들의 본문 길이 합」 그대로다.
- ★ **`keepalive` + `ReadableStream` 본문 → `TypeError`** — `Keepalive request cannot have a ReadableStream body.` 명세의 본문 추출 단계 그대로다(길이를 미리 모르는 본문은 한도를 셀 수 없다).

```text
   keepalive 한도 — 하나의 통 64KiB (이 판)

   [ 붙잡힌 keepalive 40000 ][ 새 요청 ≤ 25536 ]   = 65536   ○  keepalive then · beacon true
   [ 붙잡힌 keepalive 40000 ][ 새 요청   25537  ]   = 65537   ✕  keepalive TypeError · beacon false
   ★ 통은 keepalive 와 sendBeacon 이 같이 쓴다 · 끝난 요청은 통에서 빠진다
```

### (4) ★★ 큰 본문 — 보통 `fetch` 로 8 MiB 를 떠나며 보내면

keepalive 로는 **못 보낸다**((3)). 보통 `fetch` 로 보내고, 서버는 **헤더만 받은 뒤 떠난 뒤 0.5초가 지나서야 본문을 읽기 시작한다** — 그동안 버퍼가 차서 올리기가 멈춘다.

```html
<!-- wa32b-34-big.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>34 big</title>
<script>
// 8 MiB 본문을 보통 fetch 로 — pagehide 에서(또는 하네스가 직접 부르면 떠나지 않고)
const id = new URLSearchParams(location.search).get("id");
let 보냄 = false;
window.__보내기 = () => {
  if (보냄) return;
  보냄 = true;
  fetch(`/big?id=${id}&case=${id.slice(4)}`, { method: "POST", body: new Uint8Array(8 << 20) }).catch(() => {});
};
addEventListener("pagehide", () => window.__보내기());
</script>
<p><a id="go" href="wa32b-34-next.html">다음 쪽으로</a></p>
```

```text
$ python3 wa32b-net.py big
떠나지 않음(하네스가 직접 부름) → 헤더가 서버에 닿았나 = True
pagehide 에서 부르고 링크로 떠남 → 헤더가 서버에 닿았나 = True
pagehide 에서 부르고 탭 닫기(Page.close) → 헤더가 서버에 닿았나 = True
--- 서버 로그 ---
A POST /big?case=머묾  Content-Length=8388608 · 본문을 끝까지 받았나 = True · 받은 것이 있나 = True
A POST /big?case=링크  Content-Length=8388608 · 본문을 끝까지 받았나 = True · 받은 것이 있나 = True
A POST /big?case=닫기  Content-Length=8388608 · 본문을 끝까지 받았나 = False · 받은 것이 있나 = True
(exit 0)
```

- ★★ **떠나지 않으면 · 링크로 떠나면(bfcache) 끝까지 받았다. 탭을 닫으면 `끝까지 받았나 = False` · `받은 것이 있나 = True`** — **헤더는 닿았고 본문이 가운데서 잘렸다.** 서버는 **잘린 본문**을 받는다 — `Content-Length` 와 견주지 않으면 **반쪽 데이터를 처리하게 된다.**
- ★ **(1)의 「요청은 닿았다」는 작은 본문 이야기다** — 요청이 선에 다 오르기 전에 문서가 파괴되면 **오르던 것까지 끊긴다.**

```text
   8 MiB 를 보통 fetch 로 — 서버는 떠난 뒤 0.5초부터 읽는다 (이 판)

   떠나지 않음      헤더 ───▶ 본문 ████████████████ 끝까지         True
   링크(bfcache)    헤더 ───▶ 본문 ████████████████ 끝까지         True   ← 문서가 살아 있다
   탭 닫기          헤더 ───▶ 본문 █████░░░░░░░░░░░ 가운데서 끊김   False  ← 문서 파괴 = fetch 끊김
   ★ 서버가 받은 것은 「잘린 본문」 — Content-Length 와 견주지 않으면 반쪽을 처리한다
```

### (5) ★ `sendBeacon` 의 메서드와 `Content-Type` — 교차 출처면

```html
<!-- wa32b-34-types.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>34 types</title>
<script>
// sendBeacon 에 본문 종류를 바꿔 넣는다 — 같은 출처(A)와 다른 출처(B). 서버가 받은 메서드 · Content-Type 은 서버 로그로
const 쉬기 = ms => new Promise(r => setTimeout(r, ms));
async function 가라앉기(base, id) {
  for (let k = 0; k < 100; k++) { if ((await (await fetch(`${base}/seen?id=${id}`)).json()).length) return; await 쉬기(10); }
}
const 본문들 = () => [
  ["글", "a=1"],
  ["Blob(type 없음)", new Blob(["a=1"])],
  ["Blob(text/plain)", new Blob(["a=1"], { type: "text/plain" })],
  ["Blob(application/json)", new Blob(['{"a":1}'], { type: "application/json" })],
  ["URLSearchParams", new URLSearchParams({ a: "1" })],
  ["FormData", (() => { const f = new FormData(); f.append("a", "1"); return f; })()],
];
window.__끝 = async () => {
  const 줄 = [];
  for (const [쪽, base] of [["같은 출처 A", window.__A], ["다른 출처 B", window.__B]]) {
    for (const [k, [말, 본]] of 본문들().entries()) {
      const id = 쪽[0] + k, 됨 = navigator.sendBeacon(`${base}/beacon?id=${id}&body=${encodeURIComponent(말)}`, 본);
      줄.push(`${쪽}\t${말}\tsendBeacon → ${됨}`);
      if (됨) await 가라앉기(base, id);
      await 쉬기(200);
    }
  }
  // 대조 — 다른 출처로 keepalive fetch, Content-Type: application/json
  try {
    const r = await fetch(`${window.__B}/beacon?id=kj&body=keepalive-json`, { method: "POST", keepalive: true, headers: { "Content-Type": "application/json" }, body: '{"a":1}' });
    줄.push("다른 출처 B\tkeepalive fetch(application/json)\tthen " + r.status);
  } catch (e) { 줄.push(`다른 출처 B\tkeepalive fetch(application/json)\tcatch ${e.name} 「${e.message}」`); }
  await 쉬기(300);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py console wa32b-34-types.html
같은 출처 A	글	sendBeacon → true
같은 출처 A	Blob(type 없음)	sendBeacon → true
같은 출처 A	Blob(text/plain)	sendBeacon → true
같은 출처 A	Blob(application/json)	sendBeacon → true
같은 출처 A	URLSearchParams	sendBeacon → true
같은 출처 A	FormData	sendBeacon → true
다른 출처 B	글	sendBeacon → true
다른 출처 B	Blob(type 없음)	sendBeacon → true
다른 출처 B	Blob(text/plain)	sendBeacon → true
다른 출처 B	Blob(application/json)	sendBeacon → true
다른 출처 B	URLSearchParams	sendBeacon → true
다른 출처 B	FormData	sendBeacon → true
다른 출처 B	keepalive fetch(application/json)	catch TypeError 「Failed to fetch」
--- 콘솔 ---
javascript · error · Access to resource at 'http://127.0.0.1:<B>/beacon?id=%EB%8B%A43&body=Blob(application%2Fjson)' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/beacon?id=kj&body=keepalive-json' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
A POST /beacon?body=글  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · 본문 3바이트
A POST /beacon?body=Blob(type 없음)  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 3바이트
A POST /beacon?body=Blob(text/plain)  Origin=http://127.0.0.1:<A> · Content-Type=text/plain · 본문 3바이트
A POST /beacon?body=Blob(application/json)  Origin=http://127.0.0.1:<A> · Content-Type=application/json · 본문 7바이트
A POST /beacon?body=URLSearchParams  Origin=http://127.0.0.1:<A> · Content-Type=application/x-www-form-urlencoded;charset=UTF-8 · 본문 3바이트
A POST /beacon?body=FormData  Origin=http://127.0.0.1:<A> · Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 133바이트
B POST /beacon?body=글  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · 본문 3바이트
B POST /beacon?body=Blob(type 없음)  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 3바이트
B POST /beacon?body=Blob(text/plain)  Origin=http://127.0.0.1:<A> · Content-Type=text/plain · 본문 3바이트
B OPTIONS /beacon?body=Blob(application/json)  Origin=http://127.0.0.1:<A> · Access-Control-Request-Headers=content-type → 허용 헤더 없이 204
B POST /beacon?body=URLSearchParams  Origin=http://127.0.0.1:<A> · Content-Type=application/x-www-form-urlencoded;charset=UTF-8 · 본문 3바이트
B POST /beacon?body=FormData  Origin=http://127.0.0.1:<A> · Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 133바이트
B OPTIONS /beacon?body=keepalive-json  Origin=http://127.0.0.1:<A> · Access-Control-Request-Headers=content-type → 허용 헤더 없이 204
(exit 0)
```

- ★★ **메서드는 전부 `POST`.** `Content-Type` 은 본문 종류가 정한다 — 글 → **`text/plain;charset=UTF-8`** · 타입 없는 `Blob` → **헤더 없음** · `Blob` 의 `type` 그대로 · `URLSearchParams` → **`application/x-www-form-urlencoded;charset=UTF-8`** · `FormData` → **multipart**. [30번 주제](../30-request-body-and-content-type/2-summary.md)의 `fetch` 규칙과 같은 칸이다.
- ★★★ **다른 출처 B 에 `Blob(application/json)` → `sendBeacon` 은 `true` 인데 서버에는 `OPTIONS` 만 왔다** — 프리플라이트가 붙었고(`Access-Control-Request-Headers=content-type`), B 가 허용을 안 주자 **`POST` 는 안 갔다.** 콘솔에만 `blocked by CORS policy: Response to preflight request doesn't pass access control check` 가 있다. **`true` 는 「보냈다」가 아니라 「큐에 넣었다」다.** 프리플라이트가 붙는 조건은 [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 격자 그대로다(CORS-safelisted 가 아닌 `Content-Type`).
- **`keepalive` fetch 에 `application/json` 을 다른 출처로 → 같은 `OPTIONS` 뒤 `TypeError`** — 페이지가 살아 있으면 `catch` 로 알 수 있다.

```text
   sendBeacon 의 본문 → 선로 (이 판 — 메서드는 늘 POST)

   "a=1"(글)                    text/plain;charset=UTF-8          ─┐
   new Blob([…])                (Content-Type 없음)                 │ 다른 출처여도
   Blob type:"text/plain"       text/plain                          │ 곧바로 POST
   URLSearchParams              application/x-www-form-urlencoded;… │
   FormData                     multipart/form-data; boundary=…    ─┘
   Blob type:"application/json" application/json   ── 다른 출처면 OPTIONS 먼저 ─▶ 거부 ─▶ POST 없음
                                                      그래도 sendBeacon 은 true
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   navigator.sendBeacon(url, 본문?)  → true(큐에 넣음) | false(한도 초과 등)     ← 늘 POST · 응답은 못 읽는다
   fetch(url, { method, body, keepalive: true })  → 프라미스 — 떠난 뒤에는 결과를 받을 문서가 없다
       본문 ≤ 64KiB (아직 안 끝난 keepalive·beacon 본문의 합) · ReadableStream 본문 ✕
   new Image().src = url                           ← GET · keepalive 로 산다(Fetch 의 설명)
   부르는 자리   document "visibilitychange" (visibilityState === "hidden")   ← 24편: 떠남·가림 7행 전부
                 window "pagehide"                                           ← 가림에서는 안 난다(24편)
                 window "beforeunload" · "unload"                             ← unload 는 bfcache 를 막는다(24편)
```

### 어디서 헷갈리나

- **`sendBeacon` 의 `true` 는 전송 성공이 아니다**((5)) — 프리플라이트가 막혀도 `true` 였다.
- **64KiB 는 한 요청이 아니라 합**((3)).
- **보통 `fetch` 가 링크 이동에서 살아남은 것은 bfcache 덕**((1)) — 탭 닫기 · `unload` 리스너에서는 끊겼다.

## 어디서 틀리나

### 1. 떠날 때 분석 데이터를 보통 `fetch` 로 보낸다

**작으면 요청은 닿았지만 응답 전에 연결이 끊겼다**((1) 탭 닫기) — 서버가 처리한 뒤 무엇을 돌려주든 **아무도 안 받는다.** 크면 **본문이 가운데서 잘렸다**((4)). `keepalive: true` 나 `sendBeacon` 을 쓴다.

### 2. `unload` 에서 보낸다

**이 판에서는 닿았다** — 그러나 `unload` 리스너는 **문서를 bfcache 에서 빼고**(24편 (4)), 보통 `fetch` 는 링크 이동에서도 끊겼다((1)). **`visibilitychange → hidden`** 이 떠남·가림 7행 전부에서 났다(24편 (2)).

### 3. 확실하게 보내려고 동기 XHR 을 쓴다

**여섯 칸에서 `NetworkError` 로 던지고 안 닿았다**((2)).

### 4. `sendBeacon(url, JSON 문자열)` 을 서버가 `application/json` 으로 받을 것이라 믿는다

**`text/plain;charset=UTF-8`** 로 왔다((5)). `Blob` 에 `type` 을 주면 그대로 가지만, **다른 출처면 프리플라이트가 붙어** 막힐 수 있다.

### 5. `sendBeacon` 이 `true` 니 서버가 받았다고 기록한다

**큐에 넣었다는 뜻**이다((5) — 프리플라이트 거부에도 `true`).

### 6. 떠날 때 큰 덩어리(로그 전체 · 화면 스냅숏)를 `keepalive` 로 보낸다

**64KiB 를 넘으면 `TypeError`** · `sendBeacon` 은 **`false`** ((3)). 그리고 **다른 keepalive 가 통을 쓰고 있으면 더 작아도 거절된다.** 큰 것은 **떠나기 전에** 나눠 보낸다.

### 7. 「5판 모두 닿았다」를 「언제나 닿는다」로 읽는다

**localhost 의 5판**이다(머리말). 27편은 `abort()` 가 요청을 **따라잡지 못한** 판을 봤다 — 선이 느리면 반대쪽 판이 나올 수 있다. **닿아야 하는 것은 서버 쪽 멱등성으로 지킨다.**

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 문서가 사라질 때 keepalive 가 false 인 fetch 를 끊는다 | **명세**(Fetch — fetch group terminated) · 이 판도 그랬다((1) 탭 닫기) |
| keepalive 요청은 문서보다 오래 산다 · `sendBeacon` 과 `img` 가 쓴다 | **명세**(Fetch 의 keepalive 설명) · 이 판도 그랬다((1)) |
| 아직 안 끝난 keepalive 본문의 합 > 64KiB → network error | **명세**(Fetch) · 이 판도 그랬다((3) — 경계 둘씩) |
| keepalive + `ReadableStream` → `TypeError` | **명세**(Fetch 본문 추출) · 이 판도 그랬다((3)) |
| `sendBeacon` 이 같은 한도를 나눠 쓰고 넘으면 `false` · 늘 `POST` · 본문별 `Content-Type` | ★ **이 판의 관찰** — Beacon 명세는 열지 못했다 |
| 떠나는 중 동기 XHR → `NetworkError`(`Synchronous XHR in page dismissal`) · 링크의 vis/ph 에서는 됨 | ★ **이 판의 관찰** — 문구는 Chrome 의 것. HTML 명세 문장은 열지 못했다 |
| 링크로 떠날 때 보통 `fetch` 가 산 것 | ★ **이 판의 관찰** — bfcache 에 들어가느냐는 구현(24편) |
| 32칸 전부 닿았다 | ★ **이 판의 관찰 — localhost 5판**. 먼 서버는 모른다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 떠날 때 작은 분석 · 세션 종료 알림 | `visibilitychange → hidden` 에서 `sendBeacon` 또는 `fetch(…, { keepalive: true })` | `unload` · 동기 XHR · 보통 `fetch` |
| 응답(상태 코드)을 받아야 | `keepalive` fetch(페이지가 살아 있으면 `then`/`catch`) | `sendBeacon`(응답을 못 읽는다) |
| 다른 출처 수집 서버 | `text/plain` · `URLSearchParams` · `FormData` 본문(프리플라이트 없음) | `Blob(application/json)`(프리플라이트 — 서버가 허용해야) |
| 64KiB 가 넘는 것 | 떠나기 **전**에 나눠 보내기 | 떠날 때 한 번에 |
| 닿았는지 알아야 | 서버 쪽 기록 · 다음 방문에 다시 보내기(멱등 키) | `sendBeacon` 의 `true` |

## 핵심 문장

1. **떠나는 중에 잘린 것은 대개 요청이 아니라 연결이었다** — 보통 `fetch` 는 탭을 닫으면 **닿고 나서 끊겼다**(응답 전), 큰 본문은 **가운데서 잘렸다.**
2. **`keepalive` · `sendBeacon` · `img.src` 는 문서가 사라져도 끝까지 갔다** — Fetch 의 keepalive 그대로다.
3. **한도는 합 64KiB** — keepalive 와 beacon 이 한 통을 나눠 쓰고, 넘으면 `TypeError` / `false` 다.
4. **`sendBeacon` 의 `true` 는 「큐에 넣었다」** — 프리플라이트가 막혀도 `true` 였다.
5. **동기 XHR 은 떠나는 중에 여섯 칸에서 던지고 안 닿았다.** 부르는 자리는 24편대로 `visibilitychange → hidden`.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 34번)
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — **「떠날 때」 격자의 정본**(어느 이벤트가 불리나 · bfcache · 탭 닫기 두 명령). 여기는 **그 이벤트 안에서 보낸 것이 닿았나**
- [25번 주제](../25-fetch-request-response/2-summary.md) — 서버 요청 로그 창
- [27번 주제](../27-abort-and-timeout/2-summary.md) — 취소해도 닿은 판. 「닿았나」를 판 수로 읽는 이유
- [28번 주제](../28-cors-simple-and-preflight/2-summary.md) · [30번 주제](../30-request-body-and-content-type/2-summary.md) — 프리플라이트가 붙는 조건 · 본문별 `Content-Type`
- [31번 주제](../31-blob-file-and-object-url/2-summary.md) — 「떠났다」와 「파괴됐다」가 갈리는 bfcache

## 용어 풀이

- **keepalive(요청의)** — 요청이 문서보다 오래 살게 하는 표시. `fetch` 의 `keepalive: true` · `sendBeacon` · `img` 가 쓴다. (HTTP 의 `Connection: keep-alive` 와는 다른 것이다.)
- **fetch group terminated** — 문서가 사라질 때 그 문서의 진행 중 fetch 를 정리하는 단계. keepalive 가 false 인 것을 끊는다.
- **`sendBeacon`** — 응답을 안 읽는 `POST`. 큐에 넣으면 `true`.
- **page dismissal** — 페이지가 떠나는 중. Chrome 이 그때의 동기 XHR 을 거절한다(문구에서 온 말).
- **떠날 때 전송 격자** — 수단 × 자리 × 떠남 40칸을 5판 돌려 「닿았나 · 연결이 살아 있었나」를 센 표. 이 편의 본체.

## 더 들어가면

- **`fetchLater()`** — Fetch 의 deferred fetching(문서가 사라지거나 비활성이 될 때 **나중에** 보낼 요청을 미리 맡긴다). 명세 사본에 절이 있다 — 이 판의 Chrome 에서 던지지 않았다.
- **Beacon 명세 · HTML 의 page dismissal 문장** — 열지 못했다.
- **먼 서버 · 느린 선** — 이 격자를 네트워크 지연을 넣은 판(CDP `Network.emulateNetworkConditions`)으로 다시 돌리는 일이 남았다.
