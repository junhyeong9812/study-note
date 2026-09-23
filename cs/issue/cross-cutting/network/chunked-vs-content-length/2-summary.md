# cs/issue/network/chunked-vs-content-length — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[송신] Spring RestClient
   본문 = Map        → 길이를 미리 못 정함 → Transfer-Encoding: chunked (조각으로 흘림)
   본문 = byte[]     → 길이를 앎          → Content-Length: N 명시

[수신] 파이썬 http.server (BaseHTTPRequestHandler)
   본문을 읽을 때 Content-Length 헤더 값 N 만큼만 rfile.read(N)
   → chunked 요청엔 Content-Length가 없다 → N=0 → read(0) → 0바이트
   → json.loads("") → "Expecting value: line 1 column 1 (char 0)"

[진단] 같은 요청을 curl로 보내면 성공(curl은 Content-Length를 붙인다)
   → 서버 아님, 클라이언트 차이 → RestClient의 본문 프레이밍이 원인

[교정] 본문을 byte[]로 직렬화 → RestClient가 길이를 알아 Content-Length 명시 → chunked 안 감
[방어] 브리지가 Transfer-Encoding 있으면 411 거절 + Content-Length 범위 강제 (조용한 0바이트 대신 명시적 거절)
```

## 핵심 문장

- HTTP 본문 경계를 긋는 두 방식: **Content-Length**(총 바이트 수를 앞에 명시) vs **chunked transfer-encoding**(길이 없이 조각 단위로 흘리고 0-크기 조각으로 끝을 알림). 전자는 length-prefix, 후자는 delimiter framing.
- 송신측이 **송신 시점에 본문 길이를 아느냐**가 방식을 가른다. `Map`은 직렬화 결과 길이를 미리 모르니 chunked, `byte[]`는 이미 길이가 확정이라 Content-Length.
- 소박한 수신 서버(파이썬 `http.server`)는 **Content-Length만 읽는다** — chunked 본문을 dechunk(조각 재조립)하지 않는다. 그래서 chunked 요청은 "짧게"가 아니라 **0바이트**로 잡힌다(읽을 길이 근거가 없음).
- 표준상 책임은 chunked를 구현 안 한 수신측이지만, 실무 교정은 **제어 가능한 송신측을 Content-Length로 고정**하는 쪽 — 낡은 수신 서버를 못 바꿀 때의 현실적 선택.
- 수신측 방어: chunked를 조용히 0바이트로 삼키지 말고 **411로 명시 거절 + 길이 범위 강제**. 실패는 시끄러워야 한다.
