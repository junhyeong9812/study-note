# web-platform/05-fetch-from-browser — 정답

## 정답

### 1. 브라우저가 fetch를 제한하는 이유

- 페이지의 스크립트는 사용자 브라우저의 쿠키·네트워크 위치를 빌려 쓴다. 아무 사이트의 스크립트가 사용자 쿠키를 실어 남의 서버를 부르고 응답을 읽으면, 로그인된 메일·은행 데이터를 훔칠 수 있다.
- 그래서 브라우저가 중간에서
  - 금지 헤더(`Cookie`·`Host`·`Origin` 등)는 직접 채우고,
  - 다른 출처 응답은 그 서버가 CORS 헤더로 허락한 경우에만 스크립트에 넘긴다.
- 출처는 스킴·호스트·포트 묶음이다. 포트만 달라도 다른 출처다.

### 2. 상태 코드와 reject

```text
(실험, headless Chrome 151)
[same-origin GET /status/404] resolve ok=false status=404
[same-origin GET /status/500] resolve ok=false status=500
[없는 포트(127.0.0.1:1)] reject TypeError: Failed to fetch
```

- 404·500은 resolve, `ok=false`. 연결 거부는 reject(`TypeError`).
- Fetch 표준 §5.6: response가 *네트워크 오류*이면 TypeError로 reject, 아니면 Response로 resolve. `ok`는 상태 200~299일 때 참(§2.2.3).

### 3. CORS 헤더 없는 서버에 세 가지 요청

```text
[GET, 서버 CORS 헤더 없음]            server: B GET /noallow ...
[POST text/plain, CORS 헤더 없음]      server: B POST /noallow ...
[POST application/json, CORS 헤더 없음] server: B OPTIONS /noallow ... acrh=content-type
```

- (a)(b)는 단순 요청이라 **본 요청이 서버에 도착해 처리됐다**. 브라우저는 응답 읽기만 막았다.
- (c)는 `application/json`이 안전 목록 밖이라 `OPTIONS` 프리플라이트가 먼저 갔고, 허용 헤더가 없어 본 요청은 안 갔다.
- 세 경우 모두 `catch`에는 `TypeError: Failed to fetch`. JS에서는 원인을 구분할 수 없고, 콘솔·Network 탭에서 본다.

### 4. 프리플라이트 조건과 캐시

- 메서드: `GET`·`HEAD`·`POST` 밖이면(§2.2.1).
- 헤더: CORS-safelisted request-header 밖의 헤더가 있으면. `Content-Type`은 `application/x-www-form-urlencoded`·`multipart/form-data`·`text/plain`만 안전, 값 128바이트 초과도 제외(§2.2.2). `X-Trace` 같은 커스텀 헤더는 프리플라이트 대상.
- `Access-Control-Max-Age`가 없으면 5초(§4.8). 캐시를 둘지·언제 지울지는 브라우저 재량이다(§4.8·§4.9).
- 예외: 본문에 `ReadableStream`을 쓰면 방법·헤더가 안전해도 프리플라이트가 붙는다(§5.4).
- 실험 2b: 처음 PUT은 `OPTIONS`+`PUT`, 즉시 재요청은 `PUT`만, 6초 뒤엔 다시 `OPTIONS`+`PUT`.

### 5. include + `ACAO: *`

```text
[교차 출처 include, ACAO=*] reject TypeError: Failed to fetch
    server: B GET /allow?cred=star origin=http://127.0.0.1:A cookie=sid=abc
```

- 서버 B는 쿠키 `sid=abc`를 받고 처리했다. 페이지는 reject.
- `include` 모드에서 `ACAO: *`는 허용되지 않는다(§3.3.5). 정확한 출처 + `Access-Control-Allow-Credentials: true`여야 한다.
- 쿠키는 포트로 나뉘지 않는다(RFC 6265 §8.5). 그래서 127.0.0.1의 다른 포트 B에도 실렸다.

### 6. 타임아웃 중단

- `TimeoutError`(DOMException). 실험에서 501ms에 끝났다. 수동 `abort()`면 `AbortError`.
- 서버 로그에는 `GET /slow`가 찍혔다. 요청은 이미 서버에 갔고, 서버는 계속 처리했다.
- 의미: "타임아웃 = 실패"가 아니라 "결과를 모른다"다. 상태를 바꾸는 요청을 재시도하려면 멱등 키 등으로 중복 처리를 막아야 한다.

### 7. 본문 중 abort와 스트리밍 타이밍

```text
[/stream, 첫 청크 뒤 abort] headers status=200 | read1="chunk0\n" | read2 reject AbortError
[/stream 200ms 간격 5청크] headers@204ms 204ms:chunk0 404ms:chunk1 605ms:chunk2 805ms:chunk3 1005ms:chunk4
[/stream 를 r.text() 로] headers@207ms text()@1006ms
```

- 헤더 뒤 abort는 fetch Promise가 아니라 `reader.read()`가 `AbortError`로 reject한다.
- 리더는 약 200ms 간격으로 청크마다 값을 준다. `text()`는 마지막 청크까지 기다려 약 1006ms에 한 번 준다.

### 8. 500인데 "결제 완료"

- Network 탭에서 500 응답을 확인하고, 코드에서 `then` 안에 `res.ok` 검사가 없는지 본다. `res.json()`이 HTML 에러 페이지를 만나 `SyntaxError`를 내는 경우도 있다.
- 재발 방지: 앱 전역에서 쓰는 `api()` 래퍼가 `!res.ok`이면 `HttpError(status, body)`를 던지게 한다. 직접 `fetch`를 부르는 코드를 린트·리뷰로 막는다.

### 9. CORS 에러인데 주문 두 건

- 주문 POST가 단순 요청(form 또는 `text/plain`)이었다. 서버는 받고 처리했다. 브라우저는 응답 읽기만 막아 페이지가 실패로 판단했다. 사용자가 다시 눌러 두 번째 주문이 생겼다.
- 고칠 것
  - 서버 CORS 설정(정확한 출처 허용)을 바로잡는다.
  - 주문 생성에 멱등 키를 둔다. 같은 키의 재요청은 첫 결과를 돌려준다.

### 10. 응답 순서 역전

- 새 입력마다 이전 요청의 `AbortController.abort()`를 부르고 새 컨트롤러로 요청한다. 또는 요청 번호를 붙여 최신 번호의 응답만 반영한다.
- `catch`에서 `e.name === 'AbortError'`는 내가 끊은 것이므로 오류 표시를 하지 않는다. 시간 제한을 함께 쓰면 `TimeoutError`는 따로 처리한다.
