# network/41-range-requests-and-resume — 부분 요청과 이어받기: Range·206·If-Range — 정리 (힌트)

## 해결하는 문제

4GB 파일을 받다가 3.9GB에서 끊겼다.\
처음부터 다시 받으면 3.9GB를 또 보낸다.\
"3.9GB 이후만 주세요"라고 말할 방법이 필요하다.

쉬운 예: 두꺼운 책을 복사하다가 300쪽에서 복사기가 멈췄다.\
301쪽부터 복사하면 된다.\
단, 그사이 누가 책을 **개정판으로 바꿔 놓았다면**, 1~300쪽(초판)과 301쪽~(개정판)을 합친 이상한 책이 된다.

똑같은 구조다.\
`Range`는 "몇 쪽부터"이고, `If-Range`는 "같은 판일 때만"이다.

실무 예:
- 다운로드 이어받기(브라우저, `curl -C -`, `wget -c`)
- 동영상 탐색: 재생 위치를 옮기면 플레이어가 그 위치의 바이트만 요청한다.
- 병렬 분할 다운로드: 한 파일을 여러 구간으로 나눠 동시에 받는다.
- 큰 파일의 앞부분만 읽기: ZIP의 끝(중앙 디렉터리)이나 동영상 헤더만 먼저 가져온다.

## 동작·원리

### 1. 이어받기 한 번 — 정상 흐름

```text
  [첫 다운로드]
  GET /big.iso                          -->
                                        <--  200 OK
                                             Accept-Ranges: bytes
                                             ETag: "v1"
                                             Content-Length: 10000
                                             (0..5999 바이트 받고 연결 끊김)
  로컬: big.iso.part (6000바이트), 저장해 둔 ETag "v1"

  [이어받기]
  GET /big.iso
  Range: bytes=6000-                    -->
  If-Range: "v1"
                                        <--  206 Partial Content
                                             Content-Range: bytes 6000-9999/10000
                                             Content-Length: 4000
                                             ETag: "v1"
                                             (6000..9999 바이트)
  로컬: part(0..5999) + 받은 것(6000..9999) = 완성
```

그림 해설:

- **`Accept-Ranges: bytes`**: 이 리소스는 바이트 범위 요청을 지원한다는 **권고**다(RFC 9110 §14.3).
  - 클라이언트는 이 헤더가 없어도 Range를 보낼 수 있다(MAY).
  - 이 헤더를 받았다고 다음 Range 요청이 반드시 206이 된다고 가정하면 안 된다(MUST NOT).
- **`Range: bytes=6000-`**: 6000번 바이트부터 끝까지 달라는 뜻이다. 오프셋은 0부터 세고 양 끝을 포함한다(§14.1.2).
- **`206 Partial Content`**: 요청한 범위 일부를 보낸다는 응답이다(§15.3.7).
  - `Content-Range: bytes 6000-9999/10000` = "전체 10000바이트 중 6000~9999"다(§14.4).
  - `Content-Length`는 **이번 메시지 본문** 길이(4000)다. 전체 길이가 아니다.
- **`If-Range: "v1"`**: "표현이 아직 v1이면 범위만, 바뀌었으면 전체를 달라"는 조건이다(§13.1.5).

### 2. If-Range — 바뀌었으면 처음부터

```text
  (그사이 서버 파일이 v2로 바뀜)
  GET /big.iso
  Range: bytes=6000-
  If-Range: "v1"                        -->  현재 ETag "v2" != "v1"  -> 조건 거짓
                                        <--  200 OK                 -> Range 무시
                                             ETag: "v2"
                                             Content-Length: 12000  (전체)
  클라이언트: 206이 아니라 200이다 -> part 파일을 버리고 이 본문으로 새로 저장
```

- 조건이 거짓이면 수신자는 Range를 **무시해야 한다**(MUST). 결과적으로 새 표현 전체(200)가 온다.
- `If-Match`와 `Range`를 함께 쓸 수도 있다. 하지만 표현이 바뀌었을 때 `412`를 받고, 전체를 받으려면 요청을 한 번 더 해야 한다. `If-Range`는 이 두 번째 요청을 줄인다(§13.1.5).
- `If-Range`의 비교는 **강한 비교**다.
  - 클라이언트는 약한 ETag(`W/"..."`)를 `If-Range`에 넣으면 안 된다(MUST NOT).
  - 날짜(`Last-Modified`)는 ETag가 없고 그 날짜가 강한 검증자일 때만 쓴다. 날짜 비교는 "이전이거나 같음"이 아니라 **정확히 일치**다.

### 3. 범위 문법 (RFC 9110 §14.1.2)

```text
  전체 길이 10000 가정
  bytes=0-499            처음 500바이트
  bytes=500-999          두 번째 500바이트
  bytes=9500-            9500부터 끝까지
  bytes=-500             마지막 500바이트 (suffix-range) = 9500-9999
  bytes=0-0,-1           첫 바이트와 마지막 바이트 (다중 범위)
  bytes=20000-           시작이 길이 이상 -> 만족 불가 -> 416
```

- 끝 위치를 비우거나 길이보다 크게 주면 "끝까지"로 해석한다.
- 숫자에는 상한이 없다. 받는 쪽은 정수 넘침을 막아야 한다(MUST).
- **압축된 표현이면 오프셋은 압축된 바이트 기준이다**(§14.1.2). 원본 파일의 몇 번째 바이트가 아니다.

### 4. 서버가 답할 수 있는 네 가지

```text
  상황                                            응답
  Range를 지원하고 만족 가능                        206 + Content-Range (한 범위)
  여러 범위를 요청                                  206 + multipart/byteranges (범위마다 Content-Range)
  범위가 만족 불가 (시작 >= 길이)                   416 + Content-Range: bytes */10000
  Range를 무시 (지원 안 함, If-Range 거짓 등)        200 + 전체 본문
```

- **서버는 Range를 무시해도 된다**(MAY, §14.2). 그래서 클라이언트는 206인지 200인지 반드시 확인해야 한다.
  - 206을 받으면 `Content-Type`·`Content-Range`를 보고 무엇이 들어 있는지 판단해야 한다(MUST, §15.3.7).
- 다중 범위 206은 `Content-Type: multipart/byteranges; boundary=...`이고, 헤더 영역에는 `Content-Range`를 넣지 않는다(MUST NOT). 각 부분에 넣는다(§15.3.7.2).
- 416에는 현재 전체 길이를 담은 `Content-Range: bytes */길이`를 보낸다(SHOULD, §14.4).
  - 다만 서버는 Range를 무시하고 200 + 전체 본문으로 답할 수도 있다. 그래서 클라이언트는 416이 온다고 기대하면 안 된다(RFC 9110 §15.5.17 Note).
- Range 처리는 조건부 헤더 평가 **뒤에** 한다. 조건부 GET이 304라면 Range는 무시된다(§14.2).
- HTTP 명세가 Range 처리를 정의한 메서드는 **GET뿐**이다(§14.2).

### 5. 조각을 합쳐도 되는 조건 (§15.3.7.3)

```text
  조각 A: bytes 0-5999     ETag "v1"
  조각 B: bytes 6000-9999  ETag "v1"    -> 같은 강한 검증자 -> 합쳐도 된다
  조각 C: bytes 6000-9999  ETag "v2"    -> A와 합치면 안 된다
```

- 여러 부분 응답은 **모두 같은 강한 검증자**를 가질 때만 안전하게 합칠 수 있다.
- 합친 범위가 전체를 덮으면, 그 결과를 완전한 200 응답처럼 다룬다(MUST).

### 6. 공격 면 — 다중 범위 남용 (§17.15)

```text
  Range: bytes=0-,0-,0-,0-, ... (수백 개)   -> 작은 요청 하나로 파일을 수백 번 전송하게 만듦
```

- 서버는 겹치는 범위가 두 개 넘거나, 작은 범위가 많고 순서가 뒤섞인 요청을 무시하거나 거절할 수 있다(MAY, §14.2). 겹치거나 틈이 작은 범위는 하나로 합쳐 보낼 수도 있다(MAY, §15.3.7.2).
- nginx `max_ranges`로 허용 범위 수를 제한한다. 기본은 무제한이고, 한도를 넘으면 범위가 없는 요청처럼 처리한다. 0이면 범위 지원을 끈다(nginx core 문서).

## 쓰이는 자료구조·알고리즘

- **구간 연산** — 이 주제의 중심 계산이다.
  - 정규화: suffix-range(`-500`)를 `[max(0, L-500), L-1]`로(L이 500보다 짧으면 전체, §14.1.2), 열린 끝(`9500-`)을 `[9500, L-1]`로 바꾼다. 끝이 L 이상이면 `L-1`로 자른다.
  - 만족 가능성: `first < L`인가, 또는 suffix 길이가 0보다 큰가.
  - 병합: 시작점으로 정렬한 뒤 겹치거나 맞닿은 구간을 합친다. 겹침 수를 세어 남용 요청을 거른다.
  - 받은 구간 집합 관리: 병렬 다운로드는 "받은 구간 목록"과 "빈 구간(구멍)"을 유지한다. 정렬된 구간 리스트나 구간 트리를 쓴다. `data-structure` 구간 트리는 [30-interval-tree](../../data-structure/30-interval-tree/2-summary.md).
- **강한 검증자 비교** — 조각을 합치기 전에 ETag를 문자 단위로 비교한다(`W/`가 있으면 불일치).
- **오프셋 기반 파일 쓰기** — 받은 조각을 로컬 파일의 해당 오프셋에 쓴다(`RandomAccessFile.seek`, `pwrite`).

## 적용 — 풀어나가는 법

### 1. 이어받기 클라이언트의 순서

1. 첫 응답의 `ETag`(없으면 강한 `Last-Modified`)와 전체 길이를 저장한다.
2. 끊기면 로컬 부분 파일 크기 N을 잰다.
3. `Range: bytes=N-`와 `If-Range: <저장한 ETag>`로 요청한다.
4. 응답 코드로 분기한다.
   - **206**: `Content-Range`의 시작이 정확히 N인지 확인하고 이어 쓴다.
   - **200**: 서버가 Range를 무시했거나 파일이 바뀌었다. 부분 파일을 **버리고** 처음부터 쓴다.
   - **416**: 이미 다 받았거나 서버 파일이 더 작아졌다. `Content-Range: bytes */L`의 L과 로컬 크기를 비교한다.
5. 끝나면 전체 길이와 (가능하면) 체크섬으로 검증한다.

### 2. 코드

Java — `HttpClient`로 이어받기:

```java
long have = Files.exists(part) ? Files.size(part) : 0;
HttpRequest req = HttpRequest.newBuilder(uri)
    .header("Range", "bytes=" + have + "-")
    .header("If-Range", savedEtag)                    // 강한 ETag만
    .build();
HttpResponse<InputStream> res = client.send(req, BodyHandlers.ofInputStream());

try (InputStream in = res.body()) {
    if (res.statusCode() == 206) {
        String cr = res.headers().firstValue("Content-Range").orElseThrow();  // "bytes 6000-9999/10000"
        long start = Long.parseLong(cr.substring(6, cr.indexOf('-')));
        if (start != have) throw new IOException("unexpected range " + cr);
        try (OutputStream out = Files.newOutputStream(part, StandardOpenOption.CREATE, StandardOpenOption.APPEND)) { in.transferTo(out); }
    } else if (res.statusCode() == 200) {
        try (OutputStream out = Files.newOutputStream(part, StandardOpenOption.TRUNCATE_EXISTING,
                                                      StandardOpenOption.CREATE)) { in.transferTo(out); }
        savedEtag = res.headers().firstValue("ETag").orElse(null);   // 새 버전
    } else if (res.statusCode() == 416) {
        // Content-Range: bytes */L 과 have 비교
    }
}
```

JS — 동영상 앞부분만 가져오기:

```js
const res = await fetch('/video.mp4', { headers: { Range: 'bytes=0-65535' } });
if (res.status === 206) {
  console.log(res.headers.get('Content-Range'));   // "bytes 0-65535/734003200"
} else if (res.status === 200) {
  res.body.cancel();                                 // 서버가 Range 무시 -> 전체가 오기 전에 끊는다
}
```

- 교차 출처 요청일 때(WHATWG Fetch)
  - `Range`는 단일 범위(`bytes=0-65535`, `bytes=6000-`)일 때만 CORS 안전 목록 헤더다. suffix(`bytes=-500`)나 다중 범위는 프리플라이트를 부른다.
  - `Content-Range`는 안전 목록 응답 헤더가 아니다. 스크립트가 읽으려면 서버가 `Access-Control-Expose-Headers: Content-Range`를 보내야 한다.
  - CORS 규칙은 [languages/web-api/28-cors-simple-and-preflight](../../../languages/web-api/28-cors-simple-and-preflight/2-summary.md).

### 3. 진단 명령

```bash
# 서버가 범위를 지원하나, 검증자는 무엇인가
curl -sI https://example.com/big.iso | grep -iE 'accept-ranges|etag|last-modified|content-length'

# 범위 한 개 (206과 Content-Range 확인)
curl -s -o /dev/null -D - -r 0-499 https://example.com/big.iso

# If-Range가 거짓이면 200이 오는지
curl -s -o /dev/null -D - -r 6000- -H 'If-Range: "old-etag"' https://example.com/big.iso

# 만족 불가 범위 -> 416과 Content-Range: bytes */L
curl -s -o /dev/null -D - -H 'Range: bytes=999999999999-' https://example.com/big.iso

# 이어받기 (로컬 파일 크기로 오프셋 결정)
curl -C - -o big.iso https://example.com/big.iso
wget -c https://example.com/big.iso
```

- `curl -C -`는 출력 파일로부터 오프셋을 정한다(curl 문서). 파일이 바뀌었는지 확인하려면 `If-Range`를 직접 헤더로 넣는다.
- `wget -c`는 로컬 파일이 원격 파일의 올바른 앞부분인지 **검증할 방법이 없다**고 매뉴얼이 직접 경고한다.

## 장애 시나리오와 대처

### 1. 파일이 바뀐 뒤 `If-Range` 없이 이어받기 → 두 버전이 섞인 파일

- **현상**: 다운로드는 "성공"했는데 설치 파일이 손상됐다고 나온다. 압축 해제·서명 검증이 실패한다.
- **보이는 형태**
  - 받은 파일 크기는 새 버전 크기와 같지만 해시가 공식 해시와 다르다.
  - 서버 로그에 206 응답이 있고, 그 사이 배포로 파일이 교체됐다.
- **원인**
  - 클라이언트가 `Range: bytes=N-`만 보냈다. 서버는 **새 버전**의 N 이후를 206으로 준다.
  - 로컬의 앞부분(구 버전)과 합쳐진다. `wget -c` 매뉴얼이 경고하는 바로 그 "garbled file"이다.
- **대처**
  - 이어받기에는 항상 `If-Range: <강한 ETag>`를 붙인다. 바뀌었으면 200 전체가 온다.
  - 서버는 파일 내용이 바뀌면 반드시 바뀌는 강한 ETag를 준다. 가능하면 버전별로 URL을 달리한다(`/v2/big.iso`).
  - 완료 후 전체 해시(SHA-256 등)를 검증한다.

### 2. 압축 표현에 Range → 오프셋이 엉뚱하다

- **현상**: 로그 파일의 "10MB 지점부터"를 요청했는데 알아볼 수 없는 바이트가 온다. 또는 이어받은 파일이 풀리지 않는다.
- **보이는 형태**: 응답에 `Content-Encoding: gzip`과 206이 함께 있다. 받은 조각을 단독으로 풀 수 없다.
- **원인**
  - Range 오프셋은 **압축된 바이트열** 기준이다(RFC 9110 §14.1.2).
  - 클라이언트는 원본 오프셋을 생각했다. 압축 스트림 중간부터는 앞 문맥 없이 해독할 수 없다.
  - 요청마다 압축 결과가 달라지면(동적 압축) 같은 오프셋이 다른 바이트를 가리킨다.
- **대처**
  - 이어받기·탐색 대상 리소스는 `Accept-Encoding: identity`로 요청하거나 서버가 동적 압축을 끈다.
  - 압축본을 제공한다면 압축본을 **고정된 파일**로 만들고 압축본 전용 강한 ETag를 준다(39번).

### 3. 서버가 Range를 무시했는데 클라이언트가 이어 붙였다 → 앞부분 중복

- **현상**: 이어받은 파일이 원래보다 크고 앞부분이 두 번 들어 있다.
- **보이는 형태**: 두 번째 요청의 응답 코드가 206이 아니라 200이다. `Content-Range`가 없다.
- **원인**: 서버(또는 중간 프록시·CDN)는 Range를 무시해도 된다(MAY). 클라이언트가 응답 코드를 확인하지 않고 append했다.
- **대처**: 206일 때만 이어 쓰고 `Content-Range` 시작 오프셋을 검증한다. 200이면 덮어쓴다.

### 4. 이미 다 받은 파일을 이어받기 → 416

- **현상**: 재시도 스크립트가 "416 Range Not Satisfiable"로 실패를 보고한다.
- **보이는 형태**: 요청 `Range: bytes=10000-`, 응답 `416`, `Content-Range: bytes */10000`
- **원인**: 로컬 파일이 이미 완성(길이 10000)이라 시작 오프셋이 전체 길이와 같다. 만족 불가다.
- **대처**
  - 416이면 `Content-Range`의 전체 길이와 로컬 크기를 비교한다. 같으면 완료로 보고 해시 검증으로 넘어간다.
  - 서버 파일이 로컬보다 작아졌다면(교체됨) 처음부터 받는다.
  - 서버가 416 대신 200 + 전체 본문을 줄 수도 있다(§15.5.17 Note). 그래서 완료 여부는 저장해 둔 전체 길이·해시로 먼저 판단하고, 필요하면 HEAD로 길이를 확인한 뒤 Range를 보낸다.

### 5. 서명된 URL과 Range·If-Range

- **현상**: S3 presigned URL로 이어받기를 하면 `AccessDenied`가 난다.
- **보이는 형태**: 오류 메시지에 `HeadersNotSigned: if-range`
- **원인**: S3는 `Range`를 서명 헤더에 포함했다면 요청에 있는 `If-Range`도 서명돼 있어야 한다고 요구한다(S3 presigned URL 문서 FAQ).
- **대처**: URL을 만들 때 `If-Range`도 서명 대상 헤더에 넣는다. 또는 `Range`만 서명하는 방식을 쓰지 않는다.

## 핵심 문장

- `Range`는 표현의 바이트 구간을 요청하고, 서버는 206 + `Content-Range`로 답하거나 Range를 **무시하고 200**을 줄 수 있다. 클라이언트는 응답 코드부터 확인한다.
- 이어받기에는 `If-Range: <강한 ETag>`를 붙인다. 표현이 바뀌었으면 200 전체가 와서 두 버전이 섞이지 않는다.
- 부분 응답은 같은 강한 검증자를 가질 때만 합친다. 약한 ETag로는 If-Range도, 합치기도 안 된다.
- 바이트 오프셋은 **Content-Encoding이 적용된 바이트** 기준이다. 압축본에 Range를 쓰면 원본 오프셋과 다르다.
- 만족 불가 범위는 416 + `Content-Range: bytes */길이`다. 다중 범위는 multipart/byteranges이고, 남용을 막으려면 범위 수를 제한한다.

## 관련 주제·근거

- 선행
  - [34-http-caching](../34-http-caching/2-summary.md) — ETag·조건부 요청.
  - [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md) — 불완전 응답·본문 길이
  - [39-http-content-encoding](../39-http-content-encoding/2-summary.md) — 압축 표현과 강한 ETag
- 후속
  - [42-large-file-upload-patterns](../42-large-file-upload-patterns/2-summary.md) — 업로드 방향의 이어 보내기(tus `Upload-Offset`)
  - [45-adaptive-media-streaming](../45-adaptive-media-streaming/2-summary.md) — 세그먼트 단위 전송.
- RFC 9110 HTTP Semantics <https://www.rfc-editor.org/rfc/rfc9110>
  - §8.8.1 강한 검증자 · §8.8.3.2 비교 · §13.1.5 If-Range · §14.1.2 바이트 범위(압축 표현 기준) · §14.2 Range(MAY 무시, GET만, 조건부 뒤 평가)
  - §14.3 Accept-Ranges · §14.4 Content-Range · §14.5 Partial PUT · §14.6 multipart/byteranges
  - §15.3.7 206(§15.3.7.2 다중 부분 · §15.3.7.3 조각 합치기) · §15.5.17 416 · §17.15 Range를 이용한 서비스 거부
- nginx `ngx_http_core_module` `max_ranges` <https://nginx.org/en/docs/http/ngx_http_core_module.html>
- GNU Wget 매뉴얼 `-c/--continue`(로컬 파일이 원격의 앞부분인지 검증 불가 경고) <https://www.gnu.org/software/wget/manual/wget.html>
- curl 매뉴얼 `-C/--continue-at`, `-r/--range` <https://curl.se/docs/manpage.html>
- WHATWG Fetch(CORS-safelisted request-header `range`, safelisted response-header 목록) <https://fetch.spec.whatwg.org/>
- Amazon S3 presigned URL FAQ(`HeadersNotSigned: if-range`) <https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html>
