# network/39-http-content-encoding — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. br 협상 그림

```text
  GET /api/orders
  Accept-Encoding: br, gzip;q=0.8        ------>
                                          <------  200 OK
                                                   Content-Type: application/json
                                                   Content-Encoding: br        (1)
                                                   Vary: Accept-Encoding       (2)
                                                   ETag: "v7-br"               (3)
                                                   Content-Length: <압축 후 바이트 수>
```

1. `Content-Encoding: br` — 코딩을 적용한 쪽은 반드시 붙인다(MUST, RFC 9110 §8.4). 없으면 받는 쪽이 바이트를 JSON으로 읽다 깨진다.
2. `Vary: Accept-Encoding` — 캐시할 수 있는 협상 응답이면 붙여야 한다(SHOULD, §12.5.5). 캐시 키에 요청의 Accept-Encoding을 넣게 한다.
3. 압축본 전용 ETag — 강한 ETag를 쓴다면 원본과 달라야 한다(§8.8.3.3).

- `Content-Length`는 압축된 바이트 수다. 압축 결과 길이를 미리 모르면 chunked로 흘린다.

### 2. q=0과 빈 값

- `gzip;q=0, *`: gzip은 명시적으로 금지(q=0)다. `*`는 "목록에 없는 나머지 코딩 전부"이므로 br은 허용된다. 서버는 br이나 무압축을 보낼 수 있고, gzip은 보내면 안 된다(§12.5.3, §12.4.2).
- `Accept-Encoding:`(빈 값): "코딩 없는 응답을 원한다"는 뜻이다(§12.5.3). 무압축으로 보낸다.
- 헤더가 **아예 없으면** 규칙상 어떤 코딩이든 허용이다. 빈 값과 헤더 없음은 뜻이 다르다.

### 3. Content-Type이 그대로인 이유와 TE와의 차이

- Content-Encoding은 "미디어 타입의 정체성을 잃지 않고 압축하기 위해" 있다(§8.4). 받는 쪽은 Content-Encoding대로 푼 다음 Content-Type으로 해석한다.
- 차이
  - Content-Encoding은 **표현의 성질**이다. 캐시는 압축본 그대로 저장하고, ETag·길이·Range가 압축된 바이트 기준이다.
  - Transfer-Encoding은 **이번 전송 한 홉의 성질**이다. 중간 수신자가 풀거나 다시 감쌀 수 있고, ETag가 달라지지 않는다(§8.8.3.3 Note).
  - Transfer-Encoding(chunked 포함)은 HTTP/1.1 전용이다. HTTP/2는 이 헤더를 금지한다(RFC 9113 §8.2.2).

### 4. `1f 8b`로 시작하는 본문

- `1f 8b`는 gzip 매직 바이트다(RFC 1952: ID1=31, ID2=139). 압축을 요청하지 않은 클라이언트가 gzip본을 받은 것이다.
- 빠진 것: 원 서버 응답의 `Vary: Accept-Encoding`. CDN이 URL만으로 캐시해 처음 저장된 gzip본을 같은 URL의 다른 요청에도 준다.
- 고치는 순서
  1. `curl -sI`로 원 서버와 CDN 응답의 `Vary`·`Content-Encoding`을 비교해 확인한다.
  2. 원 서버에 `Vary: Accept-Encoding`을 붙인다(nginx `gzip_vary on`). 또는 압축을 CDN 한 곳에서만 하도록 정리한다.
  3. CDN 캐시를 무효화한다. 이미 잘못 저장된 항목은 헤더를 고쳐도 남아 있다.
  4. `Accept-Encoding` 없는 요청과 gzip 요청의 응답 바이트를 다시 비교해 확인한다.

### 5. 압축본의 ETag가 달라야 하는 이유

- 강한 ETag는 "이 바이트열"을 가리킨다. 원본과 압축본은 바이트열이 다르다.
- 같은 태그를 쓰면 캐시 갱신과 Range 요청에서 두 바이트열이 섞인다(§8.8.3.3).
  - 예: 클라이언트가 압축본 앞 1000바이트를 받아 두고 `If-Range: "same"`, `Range: bytes=1000-`로 나머지를 요청한다. 서버가 이번엔 원본에서 1000바이트 이후를 주면, 태그는 일치하지만 이어 붙인 결과는 망가진다.
- 조건부 갱신(`If-Match`)에서도 어느 표현을 기준으로 한 태그인지 모호해진다.

### 6. 약한 ETag와 이어받기

- 프록시가 본문을 gzip으로 바꾸면서 강한 ETag를 약한 ETag로 낮췄다. nginx는 1.7.3부터 이렇게 동작한다(nginx CHANGES).
- 304 재검증(`If-None-Match`)은 **약한 비교**라 `W/"abc"`로도 일치한다(RFC 9110 §13.1.2, §8.8.3.2).
- 이어받기의 `If-Range`는 **강한 비교**다. 약한 태그는 절대 일치하지 않는다. 게다가 클라이언트는 약한 태그를 `If-Range`에 넣으면 안 된다(MUST NOT, §13.1.5).
- 결과: 조건이 거짓이 되어 서버가 Range를 무시하고 200 전체를 준다. 그래서 늘 처음부터다.
- 대처: 다운로드 경로를 프록시 압축에서 빼거나, 원 서버가 압축본마다 다른 강한 ETag를 준다.

### 7. 이미 압축된 파일·작은 응답

- 이미 압축된 형식은 반복 패턴이 거의 없어 더 줄지 않는다. CPU만 쓴다.
- gzip 형식은 헤더 최소 10바이트(ID1·ID2·CM·FLG·MTIME·XFL·OS)와 꼬리 8바이트(CRC-32 + 원래 길이)를 붙인다(RFC 1952 §2.3). 줄어드는 양이 이보다 작으면 **오히려 커진다**.
- 그래서 MIME 허용 목록으로 텍스트 계열만 압축하고, 최소 길이 미만은 건너뛴다(nginx `gzip_min_length`, Spring Boot `server.compression.min-response-size`).

### 8. 동적 vs 정적 압축 전략

- 동적 API 응답
  - 요청마다 압축하므로 CPU와 첫 바이트 지연이 비용이다. 낮은~중간 수준을 쓴다.
  - 압축 수준을 올리면 크기 이득은 작고 CPU 비용은 크게 는다.
- 정적 파일
  - 빌드 때 한 번만 압축하므로 가장 높은 수준의 br·gzip을 미리 만든다.
  - 서버는 요청 시 CPU 없이 미리 만든 파일을 준다(nginx `gzip_static`).
- 둘 다 `Vary: Accept-Encoding`과 압축본별 ETag를 챙긴다.

### 9. 공통 알고리즘과 zstd 제약

- 공통: **LZ 계열 역참조**(슬라이딩 창에서 앞에 나온 문자열을 거리·길이로 가리킴)와 **엔트로피 부호**(허프만 등, 자주 나오는 기호에 짧은 부호). gzip의 DEFLATE는 LZ77 + 허프만이고(RFC 9110 §8.4.1.2), zstd는 LZ 계열 + FSE/허프만이다(RFC 8878).
- zstd HTTP 제약: 디코더는 창 크기 8MB까지 지원해야 하고, 인코더는 8MB를 넘는 창을 요구하는 프레임을 만들면 안 된다(MUST, RFC 9659). 브라우저가 메모리 보호를 위해 창 크기를 제한해 생긴 상호운용 문제를 막으려는 규칙이다.

### 10. 압축이 SSE를 뭉치게 하는 이유

- 압축기는 효율을 위해 입력을 내부 버퍼에 모은다. flush하지 않으면 블록이 찰 때까지 출력하지 않는다(Node `zlib` 문서 Flushing 절).
- SSE 이벤트는 작고 드문드문 오므로 한참 모인 뒤 한꺼번에 나간다.
- 켠 채로 고치려면 이벤트를 쓸 때마다 압축 스트림을 flush한다. 대가로 압축률이 떨어진다.
- 보통은 `text/event-stream`을 압축 대상에서 빼는 편이 단순하다. 프록시 버퍼링(`proxy_buffering`)도 함께 확인한다(40번).
