# network/39-http-content-encoding — 본문 압축 협상: Accept-Encoding·Content-Encoding·Vary — 정리 (힌트)

## 해결하는 문제

JSON·HTML·JS·CSS 같은 텍스트는 같은 단어가 반복된다.\
반복을 줄이면 보낼 바이트가 크게 준다.\
nginx 문서는 gzip이 "전송량을 절반 이하로 줄이는 경우가 많다"고 적는다.

문제는 **받는 쪽이 풀 수 있어야 한다**는 것이다.\
서버가 zstd로 압축했는데 클라이언트가 zstd를 모르면 본문은 깨진 바이트다.\
그래서 "나는 이것들을 풀 수 있다"(요청) ↔ "이것으로 압축했다"(응답)의 **협상**이 필요하다.

쉬운 예: 택배를 진공 압축 팩에 넣어 보낸다.\
받는 사람에게 압축 해제기가 있는지 먼저 묻는다.\
있으면 압축해서 보내고, 상자에 "진공 압축됨"이라고 적는다.

똑같은 구조다.\
`Accept-Encoding`이 "해제기 목록"이고, `Content-Encoding`이 "상자 위 표시"다.

실무 예:
- API 응답 JSON에 gzip/br을 켜면 모바일 사용자의 대기 시간이 준다.
- CDN이 압축본과 비압축본을 **같은 캐시 키**로 저장하면, 압축을 못 푸는 클라이언트가 깨진 본문을 받는다.
- 이미 압축된 JPEG·ZIP을 다시 gzip하면 CPU만 쓰고 크기는 줄지 않거나 오히려 는다.

## 동작·원리

### 1. 협상 한 번

```text
  Client                                            Server
  GET /api/orders
  Accept-Encoding: br, gzip;q=0.8, zstd;q=0.9 --->
                                                    가진 것 중 받는 쪽이 허용하고
                                                    q가 가장 높은 코딩 선택 -> br
                                         <---       200 OK
                                                    Content-Type: application/json
                                                    Content-Encoding: br
                                                    Vary: Accept-Encoding
                                                    Content-Length: 1834   <- 압축된 바이트 수 (예시)
                                                    ETag: "v7-br"          <- 압축본 전용 태그
                                                    (br로 압축된 JSON 바이트)
  Content-Encoding대로 풀고 -> Content-Type(JSON)으로 해석
```

그림 해설:

- **`Accept-Encoding`**: 클라이언트가 풀 수 있는 코딩과 선호도(q값)다(RFC 9110 §12.5.3).
  - *q값(quality value)*: 0~1 사이 가중치다. 없으면 1이다. **0은 "받지 않음"**이다(§12.4.2).
  - `identity`는 "압축 안 함"의 이름이다. `*`는 목록에 없는 나머지 전부다.
- **`Content-Encoding`**: 이 표현(representation)에 적용한 코딩을 **적용한 순서대로** 적는다. 코딩을 적용한 쪽은 이 헤더를 반드시 붙인다(MUST, §8.4).
  - *표현(representation)*: 리소스의 한 형태다. 같은 `/api/orders`라도 br판·gzip판·원본판은 서로 다른 표현이다.
- **Content-Type은 그대로다.** 압축해도 "이것은 JSON"이라는 정체성은 유지된다. 이것이 Content-Encoding의 존재 이유다(§8.4).
- **길이·ETag·Range는 모두 압축된 바이트 기준이다**(§8.4, §14.1.2).

### 2. 서버의 선택 규칙 (RFC 9110 §12.5.3)

```text
  요청 헤더                                  서버가 할 수 있는 것
  (Accept-Encoding 없음)                     어떤 코딩이든 허용된 것으로 본다
  Accept-Encoding: (빈 값)                   코딩 없는 응답을 원함
  Accept-Encoding: gzip                      gzip 또는 identity
  Accept-Encoding: gzip;q=1, identity;q=0    gzip만 허용 (코딩 없는 응답도 금지)
  Accept-Encoding: br;q=0, *                 br만 빼고 무엇이든
```

- 같은 목적(압축)의 코딩이 여럿 허용되면 **0이 아닌 가장 높은 q값**이 선호된다(preferred — 강제 규칙은 아니다).
- 목록에 맞는 게 없으면, identity가 금지되지 않은 한 **압축 없이** 보낸다(SHOULD).
- 헤더가 아예 없을 때 규칙상으로는 "무엇이든 허용"이다. 하지만 흔한 서버 구현은 요청이 해당 코딩을 받는다고 밝힐 때만 압축한다 [?]. 헤더 없이 요청하는 오래된 클라이언트를 배려한 선택이다.

### 3. 코딩 종류

```text
  이름      정의                                   알고리즘
  gzip      RFC 9110 §8.4.1.3 + RFC 1952 파일 형식  LZ77 + 허프만(DEFLATE) + CRC-32
  deflate   RFC 9110 §8.4.1.2                      zlib(RFC 1950) 포장 안의 DEFLATE
  br        RFC 7932                               LZ77 변형 + 허프만 + 내장 사전
  zstd      RFC 8878 (+ RFC 9659 창 크기 규칙)      LZ 계열 + FSE/허프만
  compress  RFC 9110 §8.4.1.1                      LZW (사실상 안 씀)
  dcb, dcz  RFC 9842                               사전 기반 br/zstd (공유 사전)
```

- **deflate의 함정**: 표준은 "zlib 포장 + DEFLATE"다. 그런데 포장 없이 원시 DEFLATE를 보내는 비표준 구현이 있다고 RFC 9110이 직접 경고한다. 그래서 실무는 gzip을 선호한다.
- **zstd 창 크기**: HTTP에서 zstd를 쓸 때 디코더는 8MB 창까지 지원해야 하고, 인코더는 8MB를 넘는 창을 쓰면 안 된다(MUST, RFC 9659).
  - *창(window)*: 압축기가 "이전에 나온 같은 패턴"을 찾으러 뒤로 볼 수 있는 거리다. 클수록 잘 줄지만 푸는 쪽 메모리가 든다.
- gzip 형식은 헤더 최소 10바이트와 꼬리 8바이트(CRC-32 + 원래 길이)를 붙인다(RFC 1952 §2.3). 아주 작은 본문은 압축해도 오히려 커질 수 있다.

### 4. Content-Encoding vs Transfer-Encoding

```text
                       Content-Encoding              Transfer-Encoding
  무엇의 성질          표현(리소스 형태)               이번 전송(한 홉)
  ETag                 압축본은 다른 ETag             ETag 그대로
  중간 프록시           그대로 전달·캐시               풀고 다시 감쌀 수 있음
  대표                 gzip, br, zstd                chunked (HTTP/1.1 전용)
  HTTP/2               사용                          금지 (TE: trailers만)
```

- RFC 9110 §8.4: Content-Encoding의 코딩은 **표현의 특성**이다. 표현에 대한 다른 메타데이터도 모두 "압축된 형태"에 대한 것이다.
- Transfer-Encoding으로도 압축할 수 있지만(RFC 9112 §7.2) 실무에서는 거의 쓰지 않는다. HTTP/2는 `Transfer-Encoding` 헤더 자체를 금지한다(RFC 9113 §8.2.2).
- 압축과 chunked는 함께 갈 수 있다. 압축 결과 길이를 미리 모르면 서버는 `Content-Encoding: gzip` + `Transfer-Encoding: chunked`로 흘린다(40번).

### 5. Vary — 캐시에게 "무엇에 따라 달라지는지" 알린다

```text
  캐시 키 = 메서드 + URL                           <- Vary 없을 때
  캐시 키 = 메서드 + URL + 요청의 Accept-Encoding    <- Vary: Accept-Encoding

  [Vary 누락]
  A: Accept-Encoding: br    -> 원 서버 br 응답 -> CDN이 "/app.js" 키로 저장
  B: Accept-Encoding: (없음) -> CDN이 "/app.js" 키로 찾음 -> br 바이트를 그대로 줌
                               B는 br을 못 풀어 깨진 본문
```

- `Vary`는 "메서드와 URL 말고 이 요청 헤더들도 응답 선택에 영향을 줬다"는 선언이다(RFC 9110 §12.5.5).
- 캐시는 나중 요청의 해당 헤더 값이 같을 때만 저장된 응답을 재사용해야 한다(MUST — 원 서버에 재검증해 재사용을 확인받은 경우는 예외, RFC 9111 §4.1). 즉 캐시 키가 넓어진다.
- 응답을 캐시할 수 있고 협상으로 내용이 달라지면 origin은 `Vary`를 보내야 한다(SHOULD).
- nginx `gzip_vary`의 기본값은 `off`다(nginx gzip 모듈 문서). 켜 두지 않으면 이 누락이 기본 상태다.

### 6. ETag — 압축본은 다른 태그여야 한다

```text
  원본        ETag: "123-a"   Content-Length: 70
  gzip본      ETag: "123-b"   Content-Length: 43   Content-Encoding: gzip
```

(RFC 9110 §8.8.3.3 예시)

- RFC 9110 §8.8.3.3: 압축된 표현의 **강한 ETag**는 원본의 ETag와 달라야 한다. 캐시 갱신과 Range 요청에서 두 바이트열이 섞이지 않게 하려는 것이다.
  - *강한 검증자(strong validator)*: 200 응답 본문의 바이트가 바뀔 때마다 반드시 바뀌는 값이다(§8.8.1). `W/`가 붙은 것은 약한 검증자다.
- 비교 규칙이 두 가지다(§8.8.3.2).
  - `If-None-Match`(캐시 재검증, 304)는 **약한 비교**다. `W/"1"`과 `"1"`이 일치한다.
  - `If-Match`(갱신 충돌 방지)와 `If-Range`(이어받기)는 **강한 비교**다. `W/`가 붙은 쪽이 있으면 절대 일치하지 않는다.
- nginx는 1.7.3부터 응답을 변형(gzip 등)할 때 강한 ETag를 약한 ETag로 바꾼다(nginx CHANGES). 재검증은 계속 되지만, 강한 비교를 쓰는 조건부 요청은 더 이상 일치하지 않는다.

### 7. 요청 본문도 압축할 수 있다

- 클라이언트가 `Content-Encoding: gzip`으로 요청 본문을 보낼 수 있다.
- 서버가 그 코딩을 못 받으면 `415 Unsupported Media Type`으로 답하고, 응답에 `Accept-Encoding`을 넣어 받을 수 있는 코딩을 알려야 한다(ought to, §12.5.3).
- 요청 압축을 해제할 때는 **압축 해제 후 크기**에 상한을 둔다. 작은 요청이 풀리면서 수백 배로 커지는 "압축 폭탄"을 막기 위해서다.

## 쓰이는 자료구조·알고리즘

- **DEFLATE = LZ77 + 허프만 부호** — gzip과 zlib의 본체다(RFC 9110 §8.4.1.2·§8.4.1.3).
  - *LZ77*: 슬라이딩 창 안에서 앞에 나온 같은 문자열을 찾아 "(거리, 길이)" 역참조로 바꾼다.
  - *허프만 부호*: 자주 나오는 기호에 짧은 비트열을 준다.
  - 원리는 `algorithm/33-lossless-compression-lz77-huffman`, br·zstd의 절충은 `algorithm/34-modern-codecs-lz4-zstd-brotli` — 둘 다 미작성([algorithm 영역 표](../../algorithm/curriculum.md)). 슬라이딩 창 개념은 [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md)와 같다.
- **CRC-32** — gzip 꼬리의 무결성 검사값이다(RFC 1952). 푸는 쪽이 다시 계산해 손상을 잡는다.
- **q값 우선순위 협상** — 클라이언트 목록을 (q 내림차순)으로 정렬하고, 서버가 가진 코딩과 교집합의 첫 원소를 고르는 과정이다. 0은 제외 집합이다.
- **캐시 키 확장(Vary)** — 캐시 저장소는 `hash(메서드, URL, Vary로 지정된 요청 헤더 값들)`을 키로 쓰는 해시 맵이다. [해시맵](../../data-structure/05-hashmap/2-summary.md)
  - 실무 캐시는 `Accept-Encoding` 값을 몇 가지 버킷(br / gzip / 없음)으로 **정규화**해 키 종류가 폭증하지 않게 한다 [?].

## 적용 — 풀어나가는 법

### 1. 무엇을 압축할지 고른다

```text
  압축한다        text/html, text/css, text/javascript, application/json,
                  application/xml, image/svg+xml, text/plain
  압축하지 않는다  image/jpeg, image/png, image/webp, video/*, audio/*,
                  application/zip, application/gzip, 이미 br/gzip된 파일
  작은 본문        최소 길이 미만은 압축 생략 (nginx gzip_min_length 기본 20바이트,
                  Spring Boot server.compression.min-response-size 기본 2KB)
```

- 이미 압축된 형식은 내부에 압축이 들어 있다. RFC 9110 §8.4도 이런 "형식에 내재된 인코딩"은 Content-Encoding으로 다시 적지 않는다고 설명한다. 다시 압축하면 반복 패턴이 없어 줄지 않고, 헤더·꼬리만큼 커진다.
- `text/event-stream`처럼 **조금씩 흘려야 하는 응답**은 압축기가 모아 두는 동안 지연이 생긴다. 압축하려면 이벤트마다 flush해야 한다(Node `zlib` 문서의 Flushing 절).

### 2. 압축 수준을 고른다

```text
  동적 응답(요청마다 압축)   낮은 수준 (예: gzip 1~5 (예시))  -> CPU·지연 우선
  정적 파일(빌드 때 한 번)   최고 수준 br/gzip로 미리 압축     -> 크기 우선
```

- 압축 수준이 높을수록 더 긴 패턴을 더 오래 찾는다. 크기는 조금 줄고 CPU는 크게 는다.
- 정적 파일은 빌드 단계에서 `.br`·`.gz`를 만들어 두고 서버가 그대로 준다(nginx `gzip_static`).
- nginx `gzip_comp_level` 기본값은 1, 범위는 1~9다(nginx 문서). 공식 nginx 모듈 목록에는 gzip만 있고 brotli는 별도 모듈로 붙인다.

### 3. 설정 예

nginx:

```nginx
gzip            on;
gzip_vary       on;                 # Vary: Accept-Encoding (기본 off)
gzip_types      application/json text/css text/javascript image/svg+xml;
                                     # text/html은 항상 포함
gzip_min_length 1024;               # (예시)
gzip_comp_level 5;                  # (예시)
gzip_proxied    any;                # 기본 off: Via 헤더가 있는 요청(프록시 경유)은 압축 안 함
```

Spring Boot(내장 서버):

```properties
server.compression.enabled=true                # 기본 false
server.compression.mime-types=application/json,text/html,text/css,text/javascript
server.compression.min-response-size=2KB       # 기본값
```

Node.js — 협상과 스트림 압축:

```js
const zlib = require('node:zlib');
const { pipeline } = require('node:stream');

function send(req, res, readable) {
  const ae = req.headers['accept-encoding'] || '';
  res.setHeader('Vary', 'Accept-Encoding');            // 협상했으면 항상
  if (/\bbr\b/.test(ae)) {                             // 간단 판정 (q=0은 무시하지 않음 — 실무는 파서 사용)
    res.setHeader('Content-Encoding', 'br');
    pipeline(readable, zlib.createBrotliCompress(), res, () => {});
  } else if (/\bgzip\b/.test(ae)) {
    res.setHeader('Content-Encoding', 'gzip');
    pipeline(readable, zlib.createGzip(), res, () => {});
  } else {
    pipeline(readable, res, () => {});
  }
}
```

- 위 정규식 판정은 `gzip;q=0`("gzip 금지")도 허용으로 읽는 버그가 있다. q값을 파싱하는 라이브러리(예: Express의 `compression` 미들웨어, `negotiator`)를 쓴다.

### 4. 진단

```bash
# 서버가 무엇을 골랐나, Vary가 있나
curl -sI -H 'Accept-Encoding: br, gzip' https://example.com/app.js | grep -iE 'content-encoding|vary|etag|content-length'

# 압축 해제까지 해서 본문 확인 (curl이 풀 수 있는 코딩을 알아서 요청)
curl -s --compressed https://example.com/api/orders | head

# 압축 안 받는 클라이언트 흉내: 이때 Content-Encoding이 오면 안 된다
curl -sI -H 'Accept-Encoding: identity' https://example.com/app.js

# CDN 캐시 오염 확인: 두 요청의 응답 바이트가 다르면 캐시 키가 갈렸다는 뜻
curl -s -H 'Accept-Encoding: gzip' https://cdn.example.com/app.js | head -c 2 | xxd   # 1f8b = gzip 매직
curl -s https://cdn.example.com/app.js | head -c 2 | xxd
```

- gzip 데이터는 첫 두 바이트가 `1f 8b`다(RFC 1952 §2.3.1, ID1=31, ID2=139). 압축을 안 요청했는데 이 바이트가 오면 캐시가 압축본을 줬다는 증거다.

## 장애 시나리오와 대처

### 1. `Vary: Accept-Encoding` 누락 → CDN이 압축본을 미지원 클라이언트에 준다

- **현상**: 대부분은 멀쩡한데, 일부 클라이언트(오래된 HTTP 라이브러리, 헬스체커, 내부 스크립트)만 "JSON 파싱 실패"나 깨진 글자를 본다. 캐시를 비우면 잠시 괜찮다가 다시 생긴다.
- **보이는 형태**
  - 클라이언트 로그: `Unexpected token` 류 JSON 파싱 오류, 본문 첫 바이트가 `1f 8b`
  - 반대 방향(비압축본이 먼저 캐시됨)이면 증상 없이 **전송량만 커진다**.
  - 브라우저에서는 `Content-Encoding`이 붙은 채 잘못된 바이트가 오면 Chrome이 `net::ERR_CONTENT_DECODING_FAILED`를 낸다.
- **원인**: 캐시 키가 URL뿐이라, 처음 캐시된 표현(압축본)이 캐시가 살아 있는 동안 같은 URL의 요청에 계속 나간다.
- **대처**
  - 협상하는 모든 응답에 `Vary: Accept-Encoding`을 붙인다. nginx는 `gzip_vary on`.
  - CDN이 압축을 대신한다면 CDN 쪽 설정으로 원 서버 압축을 끄고 한 곳에서만 한다.
  - 수정 후 CDN 캐시를 무효화한다.

### 2. 이미 압축된 파일을 재압축 → CPU 낭비·오히려 커짐

- **현상**: 이미지·동영상·zip 다운로드가 많은 서버의 CPU가 높다. 전송량은 줄지 않는다.
- **보이는 형태**: nginx `$gzip_ratio`가 1 근처다. 응답 크기가 원본보다 수십 바이트 크다.
- **원인**: 압축 대상 MIME을 `*`로 잡았다. JPEG·PNG·ZIP은 내부가 이미 압축돼 반복 패턴이 없다. gzip은 헤더·꼬리를 더한다.
- **대처**
  - MIME 허용 목록 방식으로 텍스트 계열만 압축한다.
  - 정적 텍스트는 빌드 때 미리 압축하고(`gzip_static`), 동적 응답은 낮은 수준을 쓴다.

### 3. 프록시 재압축 → ETag가 약해져 조건부 요청이 실패

- **현상**: 파일 이어받기가 늘 처음부터 다시 받는다. 또는 `If-Match`로 낙관적 잠금을 거는 PUT이 매번 `412 Precondition Failed`다.
- **보이는 형태**
  - 원 서버 응답은 `ETag: "abc"`인데, 프록시를 거친 응답은 `ETag: W/"abc"`다.
  - `If-Range: W/"abc"`를 보낼 수 없고(클라이언트 MUST NOT), 보내도 불일치 → 206 대신 200 전체 응답.
- **원인**
  - 프록시(nginx 1.7.3 이상 등)가 gzip으로 본문을 바꾸면서 강한 ETag를 약한 ETag로 낮췄다.
  - `If-Match`·`If-Range`는 강한 비교라 약한 태그와 절대 일치하지 않는다(RFC 9110 §8.8.3.2, §13.1.1, §13.1.5).
- **대처**
  - 이어받기·조건부 갱신 대상(대용량 다운로드, 쓰기 API)은 프록시 압축에서 뺀다.
  - 압축은 원 서버에서 하고, 압축본마다 **서로 다른 강한 ETag**를 준다(§8.8.3.3 예처럼).

### 4. 스트리밍 응답이 압축 때문에 몰려서 온다

- **현상**: SSE·진행률 스트림이 압축을 켠 뒤로 실시간성이 사라졌다.
- **보이는 형태**: `curl -N --compressed`로 보면 몇 KB씩 뭉쳐 온다.
- **원인**: 압축기는 효율을 위해 입력을 모아 둔다. flush하지 않으면 블록이 찰 때까지 출력하지 않는다(Node `zlib` 문서).
- **대처**: 스트림 응답은 압축에서 빼거나, 이벤트 경계마다 flush한다. flush가 잦을수록 압축률은 떨어진다.

### 5. HTTPS + 압축 + 비밀 반영 → 길이로 비밀이 샌다

- **현상**: 보안 점검에서 BREACH 취약 판정을 받는다.
- **원인**: 응답에 비밀(CSRF 토큰)과 공격자가 넣은 문자열이 함께 들어가면, 압축 후 길이 차이로 비밀을 한 글자씩 추측할 수 있다. nginx 문서도 TLS에서 압축 응답이 BREACH 대상이 될 수 있다고 경고한다.
- **대처**: 비밀이 든 응답은 압축하지 않거나, 토큰을 요청마다 마스킹한다. 자세한 것은 [43-compression-side-channels](../43-compression-side-channels/2-summary.md)

## 핵심 문장

- `Accept-Encoding`은 "풀 수 있는 목록 + q값", `Content-Encoding`은 "적용한 코딩"이다. q=0은 금지다.
- Content-Encoding은 **표현의 성질**이다. 길이·ETag·Range 오프셋은 모두 압축된 바이트 기준이다.
- 협상한 응답에는 `Vary: Accept-Encoding`을 붙인다. 빠지면 캐시가 한 표현을 Accept-Encoding이 다른 클라이언트에게도 준다.
- 압축본의 강한 ETag는 원본과 달라야 한다. 프록시가 강한 태그를 약하게 바꾸면 `If-Match`·`If-Range`가 실패한다.
- 이미 압축된 형식과 아주 작은 본문은 압축하지 않는다. 동적 응답은 낮은 수준, 정적 파일은 미리 최고 수준으로 압축한다.

## 관련 주제·근거

- 선행
  - [33-http-semantics](../33-http-semantics/2-summary.md) · [34-http-caching](../34-http-caching/2-summary.md) — 표현·검증자·캐시 키.
  - `algorithm/33-lossless-compression-lz77-huffman` — 미작성([algorithm 영역 표](../../algorithm/curriculum.md))
- 후속·관련
  - [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md) — 길이 모르는 압축 결과를 흘리는 법
  - [41-range-requests-and-resume](../41-range-requests-and-resume/2-summary.md) — 압축 표현의 바이트 오프셋·`If-Range`
  - [43-compression-side-channels](../43-compression-side-channels/2-summary.md) · [44-websocket-compression](../44-websocket-compression/2-summary.md) · [47-cdn-and-edge](../47-cdn-and-edge/2-summary.md)
  - [languages/web-api/26-response-body-streaming](../../../languages/web-api/26-response-body-streaming/2-summary.md) — 브라우저가 풀린 본문을 스트림으로 읽는 쪽
  - [issue/cross-cutting/network/payload-transfer-cost](../../../issue/cross-cutting/network/payload-transfer-cost/2-summary.md) — 전송 비용을 줄이는 다른 축(보내지 않기)
- RFC 9110 HTTP Semantics <https://www.rfc-editor.org/rfc/rfc9110>
  - §8.4 Content-Encoding · §8.4.1 코딩(compress·deflate·gzip) · §8.8.1 강/약 검증자 · §8.8.3.2 비교 함수 · §8.8.3.3 협상 리소스의 ETag 예
  - §12.4.2 q값 · §12.5.3 Accept-Encoding · §12.5.5 Vary · §13.1.1 If-Match · §13.1.5 If-Range · §14.1.2 압축 표현의 바이트 범위
- RFC 9112 §7.2 압축 전송 코딩 <https://www.rfc-editor.org/rfc/rfc9112> · RFC 9113 §8.2.2 <https://www.rfc-editor.org/rfc/rfc9113>
- RFC 1952 GZIP file format <https://www.rfc-editor.org/rfc/rfc1952> · RFC 1950 zlib · RFC 1951 DEFLATE
- RFC 7932 Brotli <https://www.rfc-editor.org/rfc/rfc7932> · RFC 8878 Zstandard <https://www.rfc-editor.org/rfc/rfc8878> · RFC 9659 zstd 창 크기 <https://www.rfc-editor.org/rfc/rfc9659> · RFC 9842 Compression Dictionary Transport <https://www.rfc-editor.org/rfc/rfc9842>
- IANA HTTP Content Coding Registry <https://www.iana.org/assignments/http-parameters/http-parameters.xhtml>
- nginx `ngx_http_gzip_module`(`gzip_vary`·`gzip_comp_level`·`gzip_types`·`gzip_min_length`·`gzip_proxied`, BREACH 경고) <https://nginx.org/en/docs/http/ngx_http_gzip_module.html> · nginx CHANGES 1.7.3(강한 ETag → 약한 ETag) <https://nginx.org/en/CHANGES>
- Spring Boot 공통 속성 `server.compression.*` <https://docs.spring.io/spring-boot/appendix/application-properties/index.html>
- Node.js `zlib`(Flushing 절) <https://nodejs.org/api/zlib.html>
- Chromium `net_error_list.h`(`CONTENT_DECODING_FAILED`) <https://chromium.googlesource.com/chromium/src/+/main/net/base/net_error_list.h>
