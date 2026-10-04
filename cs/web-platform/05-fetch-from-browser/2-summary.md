# web-platform/05-fetch-from-browser — 브라우저의 fetch: 수명·스트리밍·중단·자격 증명 — 정리 (힌트)

## 해결하는 문제

페이지는 화면을 다시 그리지 않고 서버와 데이터를 주고받아야 한다. 그런데 브라우저 안의 요청은 서버 코드의 HTTP 클라이언트와 다르다.

```text
  서버의 HTTP 클라이언트                 브라우저의 fetch
  ───────────────────────              ─────────────────────────────────────
  내가 보낸 헤더가 그대로 간다           금지 헤더(Cookie·Host·Origin 등)는 브라우저가 정한다
  응답은 내 코드가 다 읽는다             다른 출처 응답은 CORS 검사를 통과해야 읽는다
  쿠키는 내가 넣을 때만                  쿠키는 credentials 모드가 정한다
  타임아웃은 라이브러리 기본값이 있다     Fetch 표준에는 시간 제한이 없다
```

- 브라우저는 페이지 코드를 믿지 않는다. 사용자 쿠키를 들고 남의 서버에 요청을 보낼 수 있기 때문이다.
  - *출처(origin)*: 스킴·호스트·포트 세 값의 묶음. `http://127.0.0.1:3000`과 `http://127.0.0.1:3001`은 다른 출처다.
- 그래서 fetch는 "요청을 보낸다"보다 "브라우저가 정한 규칙 안에서 요청을 보내고, 읽어도 되는 응답만 넘겨준다"에 가깝다.

쉬운 예: 우체국 창구다.
- 편지를 맡기면 창구 직원이 봉투의 일부 칸(보내는 사람 주소 등)을 직접 채운다.
- 답장이 와도, 받는 쪽이 "이 사람에게 보여줘도 된다"고 적지 않았으면 창구가 내용을 보여주지 않는다. 그래도 편지는 이미 상대에게 배달됐다.

똑같은 구조다.\
단순 요청(프리플라이트가 없는 요청)에서 CORS가 막는 것은 **보내기가 아니라 읽기**다. 이 점을 놓치면 "CORS 에러가 났으니 주문은 안 들어갔다"는 오판이 생긴다.

실무 예:
- 결제 API가 500을 돌려줬는데 `fetch(...).then(...)`이 성공 경로를 탔다. 화면에 "결제 완료"가 떴다.
- 검색창 자동완성에서 늦게 온 이전 응답이 최신 결과를 덮었다. 이전 요청을 중단하지 않았다.
- 서버가 멈춘 채 응답을 안 줘서 로딩 스피너가 몇 분째 돈다.

## 동작·원리

### 1. fetch 한 번의 수명

```text
  fetch(url, init) 호출
     │
     ▼
  ① Request 생성 ── 금지 헤더 제거, mode·credentials·redirect 확정
     │
     ▼
  ② (교차 출처 + 단순하지 않은 요청이면) CORS 프리플라이트 OPTIONS
     │
     ▼
  ③ 네트워크 요청 ── 연결·TLS·HTTP (서비스 워커가 있으면 먼저 그쪽으로, 07번)
     │
     ▼
  ④ 응답 헤더 도착 ── CORS 검사 ── 실패: Promise reject(TypeError)
     │                              성공: Promise resolve(Response)   ← 여기서 then이 돈다
     ▼
  ⑤ 본문 스트림 ── res.body(ReadableStream)로 조금씩, 또는 res.text()/json()으로 끝까지
```

- **프라미스는 보통 헤더가 오면 이행된다.** 본문은 그 뒤에 따로 흐른다(아래 실험 5). 예외로 `integrity` 옵션을 주면 본문을 끝까지 받아 해시를 검사한 뒤에 넘긴다(Fetch 표준 §4.1 Main fetch).
- **상태 코드는 거부 사유가 아니다.** Fetch 표준 §5.6 fetch 메서드는 "response가 *네트워크 오류*이면 TypeError로 reject"한다. 404·500은 네트워크 오류가 아니라 정상 응답이다.
  - *네트워크 오류(network error)*: Fetch 표준의 특별한 응답(타입 `error`, 상태 0). 연결 실패, CORS 실패, 프리플라이트 실패 등이 여기로 모인다.
  - *ok*: 상태가 200~299 범위면 참(표준 §2.2.3 "ok status").

### 2. 단순 요청과 프리플라이트

```text
  단순 요청(프리플라이트 없음)                 프리플라이트가 붙는 요청
  ─────────────────────────                 ───────────────────────────────────
  페이지 ── GET/POST ──▶ 서버(처리함)          페이지 ── OPTIONS ──▶ 서버
  페이지 ◀── 응답 ─────── 서버                 페이지 ◀── 허용 헤더 ── 서버
          └ CORS 헤더 없으면 읽기만 막힘               └ 허용이면 ──▶ 본 요청(PUT 등)
                                                       └ 거부면 본 요청을 아예 안 보냄
```

- *CORS-safelisted method*: `GET`·`HEAD`·`POST`(Fetch 표준 §2.2.1).
- *CORS-safelisted request-header*: `Content-Type`은 essence가 `application/x-www-form-urlencoded`·`multipart/form-data`·`text/plain`일 때만 해당한다. 값 128바이트 초과면 안전 헤더가 아니다(§2.2.2).
- 방법과 헤더가 모두 안전 목록에 들면 보통 프리플라이트 없이 바로 보낸다. 하나라도 벗어나면 `OPTIONS`로 먼저 묻는다.
  - 예외: 요청 본문에 `ReadableStream`을 쓰면 표준은 *use-CORS-preflight* 플래그를 세운다. 방법·헤더가 안전해도 프리플라이트가 붙는다(§2.2.5, §5.4).
  - *프리플라이트(preflight)*: 본 요청 전에 `Access-Control-Request-Method`·`Access-Control-Request-Headers`를 담아 보내는 `OPTIONS` 요청.
- 프리플라이트 결과는 브라우저가 캐시를 두면 캐시된다. 표준은 캐시를 두지 않는 구현도, 만료 전에 항목을 지우는 것도 허용한다(§4.8·§4.9). `Access-Control-Max-Age`가 없으면 표준 기본값은 5초다(§4.8 "If max-age is failure or null, then set max-age to 5"). 표준은 브라우저가 상한을 둘 수 있게 한다. MDN은 Chromium 76+ 상한 2시간, Firefox 24시간으로 적는다.

### 3. 자격 증명 — credentials 모드

```text
                         credentials: 'omit'   'same-origin'(기본)   'include'
  같은 출처 요청의 쿠키        안 보냄              보냄                 보냄
  다른 출처 요청의 쿠키        안 보냄              안 보냄              보냄
  다른 출처 응답 읽기 조건      ACAO = * 또는 출처    ACAO = * 또는 출처    ACAO = 정확한 출처
                                                                       + ACAC: true ('*' 불가)
```

- 요청의 credentials 모드 기본값은 `same-origin`이다(Fetch 표준 §2.2.5 "Unless stated otherwise, it is same-origin").
  - *ACAO*: `Access-Control-Allow-Origin` 응답 헤더. *ACAC*: `Access-Control-Allow-Credentials`.
- `include`일 때 `ACAO: *`는 거부된다(§3.3.5). 쿠키가 실린 응답을 아무 출처에나 보여주지 않으려는 규칙이다.
- 쿠키는 **포트로 나뉘지 않는다**(RFC 6265 §8.5). 출처는 포트까지 보지만 쿠키는 포트를 구분하지 않는다(쿠키 범위는 도메인·경로·`Secure` 등으로 정한다). 아래 실험에서 A(포트 a)가 받은 쿠키가 B(포트 b)로 갔다.
- 쿠키의 `SameSite`·서드 파티 쿠키 정책은 이와 별개의 계층이다. 세션 쿠키 설계는 [security](../../security/README.md)의 11번(미작성)에서 다룬다.

### 4. 중단과 시간 제한

```text
  시간 →
  fetch ───────[ 헤더 대기 ]────────────────[ 본문 수신 ]──────────▶
                    ▲                              ▲
       signal 발화: fetch Promise가 reject     signal 발화: reader.read()가 reject
       (TimeoutError 또는 AbortError)          (AbortError)
       서버는 이미 요청을 받았을 수 있다          서버는 이미 보내는 중
```

- Fetch 표준의 fetch 알고리즘에는 요청 전체에 거는 시간 제한 단계가 없다(연결을 얻는 단계에서 구현이 타임아웃 시 재시도할 수 있다는 정도만 적혀 있다). 얼마나 기다릴지는 호출자가 `signal`로 정한다.
  - *AbortController*: `abort()`로 연결된 `signal`을 발화시키는 객체.
  - *AbortSignal.timeout(ms)*: 정해진 시간 뒤 스스로 발화하는 신호. 이유는 `TimeoutError` DOMException이다(MDN). 그냥 `abort()`면 `AbortError`다.
  - MDN은 이 타이머가 경과 시간이 아니라 **활성 시간** 기준이라고 적는다. bfcache에 들어간 문서에서는 멈춘다.
- 중단은 **클라이언트가 결과를 버리는 것**이다. 서버 처리를 되돌리지 않는다. 그래서 중단 뒤 재전송은 멱등성 설계가 받쳐야 한다([reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)).
- 중단 시점별 상세 격자(보내자마자 `abort()` 해도 서버에 닿는 경우 등)는 [languages/web-api/27](../../../languages/web-api/27-abort-and-timeout/2-summary.md)에 있다.

### 5. 스트리밍

- `res.body`는 *ReadableStream*이다. `getReader().read()`를 반복하면 청크가 도착하는 대로 받는다.
  - *ReadableStream*: WHATWG Streams 표준의 읽기 스트림. 청크 단위로 `{done, value}`를 준다.
- `res.text()`·`res.json()`은 스트림을 끝까지 읽어 한 번에 준다. 본문은 한 번만 읽을 수 있다(두 번 읽으려면 `res.clone()`).
- 서버 쪽 청크 전송 원리는 [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md), 본문 스트림 API 세부는 [languages/web-api/26](../../../languages/web-api/26-response-body-streaming/2-summary.md).

### 실험: 상태 코드·CORS·credentials·중단·스트리밍을 서버 로그와 함께 본다

두 개의 Node `http` 서버를 127.0.0.1에 띄웠다. A는 페이지 출처, B는 다른 포트(= 다른 출처)다. 서버는 받은 요청을 메서드·Origin·Cookie·`Access-Control-Request-Headers`와 함께 기록한다. 페이지에서 `fetch`를 부르고 결과와 서버 로그를 나란히 찍었다.

```js
// exp05-fetch.js 핵심 (Playwright playwright-core 1.62.1, Node 20)
const tryFetch = async ({ b, arg }) => {
  const [path, init] = arg;
  try { const r = await fetch(`http://127.0.0.1:${b}/${path}`, init);
        return 'resolve status=' + r.status + ' body=' + await r.text(); }
  catch (e) { return 'reject ' + e.name + ': ' + e.message; }
};
// B 서버: /allow* 경로에만 ACAO·ACAH(x-trace, content-type)·ACAM(PUT) 헤더, OPTIONS는 204
// A 서버: / 에서 Set-Cookie: sid=abc, /slow 는 3초 뒤 응답, /stream 은 200ms 간격 5청크
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 로컬 루프백, 2026-10-04 — 포트 번호는 A·B로 바꿔 적음)

```text
--- 1. 상태 코드와 reject
[same-origin GET /status/200] resolve ok=true status=200
[same-origin GET /status/404] resolve ok=false status=404
[same-origin GET /status/500] resolve ok=false status=500
[없는 포트(127.0.0.1:1)] reject TypeError: Failed to fetch
--- 2. 교차 출처: 단순 요청 vs 프리플라이트
[GET, 서버 CORS 헤더 없음] reject TypeError: Failed to fetch
    server: B GET /noallow origin=http://127.0.0.1:A cookie=- acrh=-
[POST text/plain, CORS 헤더 없음] reject TypeError: Failed to fetch
    server: B POST /noallow origin=http://127.0.0.1:A cookie=- acrh=-
[POST application/json, CORS 헤더 없음] reject TypeError: Failed to fetch
    server: B OPTIONS /noallow origin=http://127.0.0.1:A cookie=- acrh=content-type
[GET + X-Trace, 허용] resolve status=200 body=B-body
    server: B OPTIONS /allow origin=http://127.0.0.1:A cookie=- acrh=x-trace
    server: B GET /allow origin=http://127.0.0.1:A cookie=- acrh=-
--- 2b. 프리플라이트 캐시 (Access-Control-Max-Age 없음 = 표준 기본 5초)
[PUT, 처음 보는 URL /allow-put] resolve status=200 body=B-body
    server: B OPTIONS /allow-put origin=http://127.0.0.1:A cookie=- acrh=-
    server: B PUT /allow-put origin=http://127.0.0.1:A cookie=- acrh=-
[PUT, 같은 URL 즉시 다시] resolve status=200 body=B-body
    server: B PUT /allow-put origin=http://127.0.0.1:A cookie=- acrh=-
[PUT, 같은 URL 6초 뒤] resolve status=200 body=B-body
    server: B OPTIONS /allow-put origin=http://127.0.0.1:A cookie=- acrh=-
    server: B PUT /allow-put origin=http://127.0.0.1:A cookie=- acrh=-
--- 3. credentials 모드 (쿠키 sid=abc 는 A 에서 받음)
[same-origin 기본(credentials 미지정)] done
    server: A GET /c origin=- cookie=sid=abc acrh=-
[same-origin omit] done
    server: A GET /c origin=- cookie=- acrh=-
[교차 출처 기본, 허용] resolve status=200 body=B-body
    server: B GET /allow origin=http://127.0.0.1:A cookie=- acrh=-
[교차 출처 include, ACAO=*] reject TypeError: Failed to fetch
    server: B GET /allow?cred=star origin=http://127.0.0.1:A cookie=sid=abc acrh=-
[교차 출처 include, ACAO=정확한 출처+ACAC] resolve status=200 body=B-body
    server: B GET /allow origin=http://127.0.0.1:A cookie=sid=abc acrh=-
--- 4. 타임아웃·중단
[/slow 3초, 신호 없음] resolve after 3009ms
[/slow, AbortSignal.timeout(500)] reject TimeoutError after 501ms
    server: A GET /slow origin=- cookie=sid=abc acrh=-
[/stream, 첫 청크 뒤 abort] headers status=200 | read1="chunk0\n" | read2 reject AbortError
--- 5. 스트리밍: 청크 도착 시각
[/stream 200ms 간격 5청크] headers@204ms 204ms:chunk0 404ms:chunk1 605ms:chunk2 805ms:chunk3 1005ms:chunk4
[/stream 를 r.text() 로] headers@207ms text()@1006ms
```

(일부 줄만 옮겼다. 시간 수치는 실행마다 몇 ms씩 달랐다 — 집필 3회와 사실 점검 재실행 2회를 합쳐 `/slow` 3008~3010ms, 스트림 헤더 204~208ms, 마지막 청크 1004~1007ms.)

관찰과 해석:
- 404·500은 resolve, 연결 거부는 reject. **상태 코드로는 Promise가 거부되지 않는다.**
- CORS 헤더가 없는 `GET`·`POST text/plain`도 **서버에는 도착했다**. 브라우저가 응답 읽기만 막았다. `POST application/json`은 프리플라이트(`OPTIONS`)에서 막혀 본 요청이 서버에 가지 않았다.
- `catch`가 받은 메시지는 셋 다 `Failed to fetch`로 같다. 원인(연결 실패인지 CORS인지)은 JS에서 구분되지 않는다. 콘솔·DevTools Network 탭에서 본다.
- 프리플라이트 캐시: 같은 URL의 PUT은 즉시 재요청 때 `OPTIONS`가 없었고, 6초 뒤에는 다시 나갔다. 표준 기본 5초와 맞는다.
- `include` + `ACAO: *`는 **쿠키를 실어 서버가 처리한 뒤** 읽기만 거부됐다. 쿠키가 다른 포트 B로 간 것은 쿠키가 포트를 구분하지 않기 때문이다.
- `AbortSignal.timeout(500)`은 501ms에 `TimeoutError`로 끝났다. 서버 로그에는 요청이 남았다.
- 스트림 리더는 서버가 보낸 200ms 간격 그대로 청크를 받았다. `text()`는 마지막 청크(약 1005ms)까지 기다렸다. 헤더가 200ms에 온 것은 Node가 첫 `write` 때 헤더를 함께 보냈기 때문이다(해석).

## 쓰이는 자료구조·알고리즘

- **상태 기계**: Request의 mode(`cors`·`no-cors`·`same-origin`·`navigate`)와 credentials, 응답 타입(`basic`·`cors`·`opaque`·`error`)이 다음 단계를 정한다.
- **프리플라이트 캐시** = 키-값 캐시 + TTL. 표준의 캐시 항목은 (네트워크 분할 키, 바이트 직렬화된 출처, URL, credentials, 메서드 또는 헤더 이름)으로 찾는다(§4.9). TTL = max-age. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **스트림** = 청크 큐 + 배압(backpressure). 리더가 안 읽으면 내부 큐가 차고 원천에 그만 보내라고 알린다. [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)
- **취소 전파** = 신호 트리. `AbortSignal.any([...])`로 여러 신호를 묶는다. [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md)
- **요청 순서 역전 막기** = 최신 요청 번호(단조 증가 카운터) 비교 또는 이전 요청 abort.

## 적용 — 풀어나가는 법

### 1. fetch를 감싸는 얇은 래퍼 하나를 둔다

```ts
// 앱 전역에서 이 함수만 쓴다
export class HttpError extends Error {
  constructor(public status: number, public body: string) { super(`HTTP ${status}`); }
}

export async function api<T>(path: string, init: RequestInit & { timeoutMs?: number } = {}): Promise<T> {
  const { timeoutMs = 10_000, signal, ...rest } = init;              // 기본 시간 제한을 앱이 정한다
  const timeout = AbortSignal.timeout(timeoutMs);
  const res = await fetch(path, {
    ...rest,
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,   // 호출자 취소 + 시간 제한
  });
  if (!res.ok) throw new HttpError(res.status, await res.text());    // 4xx/5xx를 예외로 바꾼다
  return res.status === 204 ? (undefined as T) : res.json();
}
```

- 할 일 세 가지: `res.ok` 검사, 기본 시간 제한, 오류 타입 분리(`HttpError`·`TimeoutError`·`AbortError`·`TypeError`).
- 요청이 나간 뒤의 `TypeError`는 "네트워크 또는 CORS"다(금지된 메서드처럼 `Request`를 만들 때 실패해도 `TypeError`다 — Fetch 표준 §5.4). 사용자에게는 같은 메시지를 보이고, 원인 분석은 DevTools로 한다.

### 2. 자동완성 — 이전 요청을 끊는다

```ts
let current: AbortController | null = null;
async function onInput(q: string) {
  current?.abort();                    // 이전 요청 결과는 버린다
  current = new AbortController();
  try {
    render(await api<string[]>(`/search?q=${encodeURIComponent(q)}`, { signal: current.signal }));
  } catch (e) {
    if ((e as Error).name !== 'AbortError') showError(e);   // 내가 끊은 것은 오류가 아니다
  }
}
```

### 3. 교차 출처 API를 설계할 때

- 브라우저에서 부를 API면 프리플라이트 비용을 계산한다. `Content-Type: application/json`이나 `Authorization` 헤더면 요청마다 프리플라이트 대상이다(프리플라이트 캐시 항목이 살아 있으면 그동안은 `OPTIONS`가 생략된다 — 실험 2b).
  - 대처: 같은 출처 BFF·리버스 프록시로 묶거나, `Access-Control-Max-Age`를 준다(Chromium 상한 2시간 — MDN).
- 쿠키 인증이 필요하면 `credentials: 'include'` + 서버 `ACAO: <정확한 출처>` + `ACAC: true` + `Vary: Origin`.
- 상태를 바꾸는 요청은 CORS를 방어선으로 쓰지 않는다. 단순 요청은 CORS 검사 전에 서버에 닿는다(실험 2). CSRF 방어(SameSite·토큰)가 따로 필요하다.

### 4. 진단 순서

1. DevTools Network 탭: 요청이 몇 개 나갔나(`OPTIONS`가 따로 보이나), 상태, `(failed)`·`CORS error` 표시.
2. Console: Chrome은 CORS 실패 이유를 콘솔에 적는다(`... has been blocked by CORS policy: ...`). JS의 `e.message`에는 안 나온다.
3. 서버 로그: 요청이 도착했나. 도착했으면 "보내기"는 된 것이고 "읽기"가 막혔다.
4. 시간 문제는 Network 탭의 Timing(Queueing·Stalled·Waiting for server response).

## 장애 시나리오와 대처

### 1. 500인데 "성공"으로 처리 (⚠ fetch는 4xx/5xx에 reject하지 않음)

- **현상**: 결제 실패인데 완료 화면. 에러 모니터링에 아무것도 안 잡힌다.
- **보이는 형태**: Network 탭엔 빨간 500, 앱 로그엔 성공. `res.json()`이 서버 에러 HTML을 파싱하다 `SyntaxError: Unexpected token '<'`를 내기도 한다.
- **원인**: `then` 안에서 `res.ok`를 안 봤다. 상태 코드는 거부 사유가 아니다(표준 §5.6, 실험 1).
- **대처**: 공통 래퍼에서 `!res.ok`면 throw. 린트 규칙이나 코드 리뷰 체크리스트에 넣는다.

### 2. 무한 로딩 (⚠ 타임아웃 기본값 없음)

- **현상**: 서버가 응답을 안 주면 스피너가 끝나지 않는다.
- **보이는 형태**: Network 탭에 `(pending)`이 계속 남는다. 사용자는 새로고침을 반복한다.
- **원인**: Fetch 표준에 시간 제한이 없다. 실험 4에서 신호 없는 요청은 서버가 줄 때(3009ms)까지 기다렸다. 서버가 영영 안 주면 그만큼 기다린다. OS·브라우저 네트워크 계층의 연결 타임아웃은 있으나 Chrome의 구체 값은 [?].
- **대처**: `AbortSignal.timeout`을 기본으로 건다. 재시도는 멱등한 요청에만, 지수 백오프로([reliability/06](../../reliability/06-retry-backoff-jitter/2-summary.md)).

### 3. "CORS 에러니까 안 들어갔겠지" → 중복 주문

- **현상**: 사용자가 "실패" 메시지를 보고 다시 눌렀다. 주문이 두 건 생겼다.
- **보이는 형태**: 콘솔 `blocked by CORS policy`, 서버 로그에는 POST가 두 번.
- **원인**: 단순 요청(POST `text/plain`·form)은 프리플라이트 없이 서버에 가서 처리된다. 막힌 것은 응답 읽기다(실험 2).
- **대처**: 서버 CORS 설정 수정. 그리고 주문 생성에 멱등 키를 둔다([reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)).

### 4. 로그인했는데 API가 401 — 쿠키가 안 실림

- **현상**: 같은 사이트의 `api.` 서브도메인 호출이 401.
- **보이는 형태**: 요청 헤더에 `Cookie` 없음. 또는 응답은 왔는데 `Failed to fetch`.
- **원인**: 교차 출처 기본 credentials는 `same-origin`이라 쿠키를 안 싣는다. `include`로 바꿨다면 서버가 `ACAO: *`를 줘서 거부됐다(실험 3).
- **대처**: `credentials: 'include'`, 서버는 정확한 출처 + `ACAC: true` + `Vary: Origin`. 쿠키 쪽은 `SameSite`·`Domain` 속성 확인.

### 5. 스트림 중단 처리 누락

- **현상**: 탭 전환·검색어 변경 뒤에도 이전 스트림을 계속 그린다. 또는 중단 시 처리되지 않은 Promise 거부가 쌓인다.
- **보이는 형태**: 콘솔 `Uncaught (in promise) AbortError`.
- **원인**: `fetch` 쪽만 try/catch하고, `reader.read()` 루프에서 나는 `AbortError`를 안 받았다(실험 4: 헤더 뒤 abort는 `read()`가 reject).
- **대처**: 읽기 루프 전체를 try/catch로 감싸고 `AbortError`는 조용히 끝낸다. `finally`에서 `reader.releaseLock()`.

## 핵심 문장

- fetch의 Promise는 보통 응답 헤더가 오면 이행되고(`integrity`를 주면 본문 검사 뒤), 요청이 나간 뒤에는 네트워크 오류(연결 실패·CORS 실패 포함)일 때 TypeError로 거부된다. 404·500은 `res.ok === false`인 정상 응답이다.
- 단순 요청에서 CORS는 보내기가 아니라 읽기를 막는다. 단순 요청은 서버에 도착해 처리된 뒤 응답만 숨겨진다. 단순하지 않은 요청은 프리플라이트에서 막혀 본 요청이 안 간다.
- credentials 기본값은 `same-origin`이다. 교차 출처에 쿠키를 보내려면 `include`와 서버의 정확한 ACAO + ACAC가 함께 필요하다.
- Fetch 표준에는 시간 제한이 없다. 앱이 `AbortSignal.timeout`으로 정하고, 중단은 서버 처리를 되돌리지 않는다.
- `res.body`는 스트림이라 청크가 오는 대로 읽을 수 있다. `text()`·`json()`은 끝까지 기다린다.

## 관련 주제·근거

- 선행
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md) — 이벤트 처리 흐름
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 메서드·상태 코드의 의미
- 후속·연결
  - [06-browser-storage](../06-browser-storage/2-summary.md) — 쿠키·토큰을 어디에 두나
  - [07-service-workers-and-offline](../07-service-workers-and-offline/2-summary.md) — fetch를 가로채는 프록시
  - security 11(세션·쿠키 보안)·21(SOP/CORS 본문) — 미작성, [security 영역 표](../../security/README.md)
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) · [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) · [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md)
  - [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md) · [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)
  - Web API 문법·재현: [web-api/25 fetch·Request·Response](../../../languages/web-api/25-fetch-request-response/2-summary.md) · [26 본문 스트리밍](../../../languages/web-api/26-response-body-streaming/2-summary.md) · [27 중단·타임아웃](../../../languages/web-api/27-abort-and-timeout/2-summary.md) · [28 CORS 단순·프리플라이트](../../../languages/web-api/28-cors-simple-and-preflight/2-summary.md) · [29 credentials·쿠키](../../../languages/web-api/29-credentials-and-cookies/2-summary.md) · [30 요청 본문·Content-Type](../../../languages/web-api/30-request-body-and-content-type/2-summary.md) · [34 sendBeacon·keepalive](../../../languages/web-api/34-send-beacon-and-keepalive/2-summary.md)
- 표준·문서
  - WHATWG Fetch Living Standard <https://fetch.spec.whatwg.org/> — §2.2.1 Methods(CORS-safelisted method), §2.2.2 Headers(CORS-safelisted request-header, 128바이트·1024바이트), §2.2.3 Statuses(ok status), §2.2.5 Requests(credentials 기본 `same-origin`), §3.3.5 CORS protocol and credentials, §4.8 CORS-preflight fetch(기본 max-age 5, 브라우저 상한 허용, 캐시 없는 구현 허용), §4.9 CORS-preflight cache(캐시 키, 만료 전 제거 허용), §4.10 CORS check(credentials가 include가 아니면 `*` 통과), §4.1 Main fetch(integrity 검사), §5.4 Request class(ReadableStream 본문 → use-CORS-preflight), keepalive 본문 합계 64KiB 제한, §5.6 Fetch methods(네트워크 오류면 TypeError로 reject)
  - WHATWG Streams <https://streams.spec.whatwg.org/>
  - MDN `Access-Control-Max-Age`(기본 5초, Chromium 76+ 2시간, Firefox 24시간) <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age>
  - MDN `AbortSignal.timeout()`(TimeoutError, 활성 시간 기준·bfcache에서 멈춤) <https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static>
  - RFC 6265 HTTP State Management Mechanism §8.5 Weak Confidentiality(쿠키는 포트로 격리되지 않음)
- 실험 목록
  - `exp05-fetch.js` — Node 20.19.6 + playwright-core 1.62.1, headless Chrome 151.0.7922.173(`/usr/bin/google-chrome`), 127.0.0.1의 Node `http` 서버 두 개(A=페이지 출처, B=다른 포트). 상태 코드 resolve/reject, 단순 요청 vs 프리플라이트와 서버 도착 여부, 프리플라이트 캐시 5초, credentials 모드별 쿠키 전송과 `ACAO: *` 거부, `AbortSignal.timeout`, 본문 읽기 중 abort, 스트림 청크 도착 시각. 3회 실행.
