# network/42-large-file-upload-patterns — 대용량 업로드: multipart·청크·재개(tus)·멀티파트 업로드·presigned URL — 정리 (힌트)

## 해결하는 문제

사용자가 5GB 동영상을 올린다.\
"POST 한 번에 전부"로 보내면 여러 곳이 동시에 깨진다.

```text
  브라우저 --(5GB, 20분)--> LB --> nginx --> 앱 서버 --> 스토리지
             |                |       |          |
             |                |       |          +- 파일을 힙에 통째로 올리면 OOM
             |                |       +- client_max_body_size 초과 -> 413
             |                +- idle/요청 타임아웃에 끊김
             +- 와이파이가 19분에 끊기면 처음부터 다시
```

쉬운 예: 이삿짐 트럭 한 대에 집 전체를 싣는다.\
다리 하나(LB)의 무게 제한에 걸리고, 도중 사고가 나면 짐 전체를 다시 싸야 한다.\
상자로 나눠 여러 번 나르고, 상자마다 번호와 내용물 목록을 붙이면 된다.

똑같은 구조다.\
대용량 업로드는 **쪼개기(청크)**, **어디까지 받았는지 기억하기(오프셋·조각 목록)**, **조각이 온전한지 확인하기(체크섬)**, **앱 서버를 경로에서 빼기(presigned URL)**의 조합이다.

실무 예:
- 영상·백업 파일 업로드, 대용량 CSV 적재
- 모바일 앱의 사진 업로드(네트워크가 자주 끊김)
- 클라이언트가 S3 같은 오브젝트 스토리지에 직접 올리고 서버는 메타데이터만 받는 구조

## 동작·원리

### 1. 기본형 — multipart/form-data (RFC 7578)

HTML 폼 파일 업로드의 와이어 형식이다.

```text
  POST /upload HTTP/1.1
  Content-Type: multipart/form-data; boundary=----b7x9
  Content-Length: 1048932

  ------b7x9\r\n
  Content-Disposition: form-data; name="title"\r\n
  \r\n
  여름 휴가\r\n
  ------b7x9\r\n
  Content-Disposition: form-data; name="file"; filename="a.mp4"\r\n
  Content-Type: video/mp4\r\n
  \r\n
  (파일 바이트 ...)\r\n
  ------b7x9--\r\n                         <- 끝 경계 (뒤에 "--")
```

- 부분마다 `Content-Disposition: form-data; name="..."`가 반드시 있다(MUST, §4.2). 파일이면 `filename`을 주는 것이 권장이다(SHOULD).
- 부분은 **경계 문자열**로 나뉜다. 경계는 부분 내용 안에 나오면 안 된다(MUST NOT, §4.1).
- 부분의 `Content-Type` 기본값은 `text/plain`이다. 파일은 알맞은 타입이나 `application/octet-stream`을 붙인다(SHOULD, §4.4).
- 한 필드에 파일 여러 개는 같은 `name`의 부분을 여러 개 보낸다(MUST, §4.3).
- **`filename`을 그대로 쓰면 안 된다.** 경로 정보(`../../etc/passwd`)를 버리고 로컬 규칙에 맞게 바꿔야 한다(§4.2, §7).
- 이 형식 자체에는 무결성 검사 기능이 없다(§7).

한계: 요청 하나다.\
중간에 끊기면 처음부터 다시 보내야 한다.

### 2. 받는 쪽 — 힙에 올리지 말고 흘려 받는다

```text
  [나쁨]  소켓 -> 파서 -> byte[] 5GB (힙) -> 디스크/스토리지       -> OOM
  [좋음]  소켓 -> 파서 -> 64KB 버퍼 반복 -> 디스크/스토리지 스트림   -> 메모리 일정
```

- Spring Boot 기본값: `spring.servlet.multipart.max-file-size` 1MB, `max-request-size` 10MB, `file-size-threshold` 0B(0B면 파일 부분은 바로 디스크 임시 파일로 간다)(Spring Boot 공통 속성).
  - `MultipartFile.getBytes()`는 파일 전체를 `byte[]`로 만든다. `getInputStream()`이나 `transferTo(Path)`로 흘려 받는다.
- Node `multer`의 `memoryStorage`는 파일 전체를 `Buffer`로 들고 있다. README가 큰 파일이나 동시 다발 업로드에서 메모리가 바닥날 수 있다고 직접 경고한다. `diskStorage`나 스트림 파서(busboy)를 쓴다.

### 3. 경로 위의 크기·시간 한도

```text
  위치                  설정 (기본값)                                초과 시
  nginx                client_max_body_size (1m)                    413
  nginx                proxy_request_buffering (on)                 본문 전체를 받은 뒤 상류로 보냄
  nginx                client_body_timeout (60s, 두 번의 읽기 사이)  408
  AWS ALB              idle timeout (60s)                           연결 종료
  Spring Boot          max-file-size 1MB / max-request-size 10MB    MaxUploadSizeExceededException
```

- `413 Content Too Large`(RFC 9110 §15.5.14): 요청 본문이 서버가 처리할 수 있는 것보다 크다. 조건이 일시적이면 `Retry-After`를 붙인다(SHOULD).
- `Expect: 100-continue`(RFC 9110 §10.1.1): 클라이언트가 헤더만 먼저 보내고 `100 Continue`(또는 최종 응답)를 잠시 기다린 뒤 본문을 보낸다. 서버가 빨리 거절하면 5GB를 보내기 **전에** 거절을 받는다.
  - 보장은 아니다. 클라이언트는 응답을 못 받아도 본문을 보내기 시작해도 된다(MAY). 그래서 본문 일부가 나간 뒤 413이 올 수도 있다.
- ALB 문서는 파일 업로드처럼 긴 작업은 idle timeout 안에 최소 1바이트를 보내고, 필요하면 타임아웃을 늘리라고 권한다.

### 4. 청크 업로드 + 재개 — tus 1.0

tus는 "어디까지 받았나"를 서버가 기억하고 클라이언트가 물어보게 하는 공개 프로토콜이다.

```text
  (1) 생성 — creation 확장
  POST /files                                    -->
  Upload-Length: 100
  Tus-Resumable: 1.0.0
                                                 <--  201 Created
                                                      Location: /files/24e5...
  (2) 전송 — 코어
  PATCH /files/24e5...                           -->
  Content-Type: application/offset+octet-stream
  Upload-Offset: 0
  (바이트 0..69 보내다 끊김)

  (3) 어디까지? — 코어
  HEAD /files/24e5...                            -->
                                                 <--  200 OK
                                                      Upload-Offset: 70
                                                      Cache-Control: no-store
  (4) 이어서
  PATCH /files/24e5...                           -->
  Upload-Offset: 70
  (나머지 30바이트)
                                                 <--  204 No Content
                                                      Upload-Offset: 100   <- 완료
```

- 모든 요청·응답에 `Tus-Resumable` 헤더가 있다(OPTIONS 제외). 서버가 모르는 버전이면 `412`와 `Tus-Version`으로 답한다.
- `PATCH`의 `Upload-Offset`은 서버의 현재 오프셋과 **같아야** 한다. 다르면 서버는 업로드를 건드리지 않고 `409 Conflict`로 답한다(MUST).
- 서버는 받은 데이터를 가능한 한 많이 저장해야 한다(SHOULD). 그래서 끊긴 PATCH의 앞부분도 오프셋에 반영된다.
- `HEAD` 응답에는 `Cache-Control: no-store`를 붙인다(MUST). 오래된 오프셋이 캐시되면 안 되기 때문이다.

tus 확장:

```text
  checksum      PATCH마다 Upload-Checksum: sha1 <base64>
                불일치 -> 460 Checksum Mismatch, 그 조각 폐기, 오프셋 불변
                서버는 최소 sha1을 지원해야 함
  expiration    Upload-Expires: 완료 안 된 업로드를 서버가 지우는 시각
  termination   DELETE로 업로드 취소
  concatenation Upload-Concat: partial 로 조각들을 따로(병렬) 올리고
                Upload-Concat: final;<URL1> <URL2> ... 로 합침
```

- IETF에서 tus를 바탕으로 한 "Resumable Uploads for HTTP"를 표준화하고 있다. `Upload-Offset`·`Upload-Complete`·`Upload-Length`·`Upload-Limit` 헤더와 `104 (Upload Resumption Supported)` 상태 코드를 쓴다. 2026-07 기준 draft-12, 아직 RFC가 아니다(IETF datatracker).

### 5. 오브젝트 스토리지 멀티파트 업로드 — S3

```text
  CreateMultipartUpload          --> UploadId = "u-123"
  UploadPart(part 1, u-123)      --> ETag "e1"    \
  UploadPart(part 2, u-123)      --> ETag "e2"     }  순서 무관, 병렬 가능,
  UploadPart(part 3, u-123)      --> ETag "e3"    /   실패한 조각만 재전송
  CompleteMultipartUpload(u-123, [(1,"e1"),(2,"e2"),(3,"e3")])
                                 --> 파트 번호 오름차순으로 이어 붙여 객체 생성
  (또는) AbortMultipartUpload(u-123) --> 조각 삭제
```

S3 한도(S3 문서 "multipart upload limits"):

```text
  최대 객체 크기        48.8 TiB
  파트 수              최대 10,000 (번호 1~10,000)
  파트 크기            5 MiB ~ 5 GiB, 마지막 파트는 최소 크기 없음
  권장                 100 MB 이상이면 멀티파트 고려
```

- Complete 요청에는 UploadId와 **파트 번호·ETag 목록**이 들어간다. 이 목록은 클라이언트가 직접 기록해야 한다. 파트 목록 조회 결과를 Complete에 쓰지 말라고 문서가 경고한다.
- 같은 파트 번호로 다시 올리면 이전 조각을 덮어쓴다.
- **완료나 중단을 하기 전까지 조각은 저장돼 있고 요금이 나온다.** 과금을 멈추려면 완료하거나 중단해야 한다고 문서가 적는다. 기본으로 알아서 정리되지 않는다.
  - 문서는 수명 주기 규칙의 `AbortIncompleteMultipartUpload`로 일정 기간 뒤 미완료 업로드를 지우라고 권한다.

### 6. presigned URL — 앱 서버를 데이터 경로에서 뺀다

```text
  Browser                     App Server                    S3
    | "5GB 올릴게요" -------->   |
    |                           | 권한 확인, 키 결정
    |                           | presign(PUT key, 15분)
    | <-- 서명된 URL ----------  |
    | ------------------ PUT (서명된 URL, 5GB) --------------> |
    | <----------------- 200 ---------------------------------- |
    | "다 올렸어요(key)" ------>  | HEAD/체크섬으로 확인, DB 기록
```

- 앱 서버는 수 KB짜리 요청만 처리한다. 대역폭·타임아웃·메모리 문제가 스토리지 쪽으로 넘어간다.
- 서명 URL은 **가진 사람 누구나 쓸 수 있는 토큰(bearer token)**이다. 만료까지 여러 번 쓸 수 있다(S3 문서).
- 만료
  - SigV4 + IAM 사용자 자격 증명으로 최대 7일이다.
  - 임시 자격 증명(역할·STS)으로 만들면 그 자격 증명이 만료될 때 URL도 만료된다. 설정한 만료 시각이 더 뒤여도 마찬가지다.
  - S3는 만료를 **요청 시작 시점**에 검사한다. 시작한 전송은 도중에 만료돼도 계속되지만, 끊긴 뒤 만료 후 재시도는 실패한다.
- 멀티파트와 합치면: 서버가 UploadId를 만들고 **파트마다** presigned URL을 발급한다. 클라이언트가 파트를 병렬로 직접 올린다.

### 7. 체크섬 — 조립 전에 확인한다

```text
  조각 단위   : tus Upload-Checksum, S3 x-amz-checksum-crc32/sha256 ...  -> 조각을 받을 때 검사
  객체 전체   : 전체 해시 (예: SHA-256)                               -> 조립 후 검사
  조각의 해시의 해시 : S3 composite 체크섬 ("checksum of checksums")     -> 조각 해시만으로 전체 검증
```

- S3는 멀티파트 업로드에 전체 객체 체크섬을 주면 서버에서 비교하고, 다르면 `BadDigest`로 실패시킨다(S3 문서).
- S3 멀티파트의 최종 ETag는 객체 데이터의 MD5가 아닐 수 있다(S3 문서). ETag를 MD5로 믿고 비교하면 안 된다.

### 8. 전송 경로 — 커널에서 바로 보낸다 (다운로드 쪽)

올린 파일을 다시 내려줄 때는 복사 횟수가 비용이다.

```text
  read()+write():  디스크 -> 페이지 캐시 -> [사용자 버퍼] -> 소켓 버퍼 -> NIC
  sendfile():      디스크 -> 페이지 캐시 -----------------> 소켓 버퍼 -> NIC
                                      (사용자 공간을 거치지 않음)
```

- `sendfile(2)`는 커널 안에서 파일 디스크립터 사이로 복사한다. `read`+`write`보다 효율적이다(man 2 sendfile).
  - 한 번 호출로 최대 0x7ffff000(2,147,479,552)바이트까지 보낸다. 반환값을 보고 반복해야 한다.
  - 입력은 mmap 가능한 파일이어야 한다(소켓 불가). 예외: Linux 5.12+에서 출력이 파이프면 `splice(2)` 규칙을 따른다.
- nginx `sendfile` 지시어(기본 `off`), Java `FileChannel.transferTo`("많은 OS가 파일 시스템 캐시에서 대상 채널로 복사 없이 옮길 수 있다", JDK 문서)가 이 경로를 쓴다.
- TLS를 쓰면 암호화를 위해 사용자 공간을 거쳐야 하므로 이득이 줄어든다. 커널 TLS(kTLS)가 이를 보완한다. 커널이 TLS 레코드 암호화를 맡으면 `sendfile`로 보낸 파일 데이터도 TLS 레코드로 나간다(kernel docs `networking/tls`). nginx는 OpenSSL 3.0에서 `SSL_sendfile()`을 지원한다(nginx CHANGES 1.21.4). 자세한 것은 `os/34-zero-copy-and-io-uring`.

## 쓰이는 자료구조·알고리즘

- **청크 분할** — 파일을 고정 크기 조각으로 자른다. 조각 크기는 "재전송 비용(작을수록 적음)"과 "요청 수·조각 수 한도(클수록 적음)" 사이의 절충이다. S3는 파트 수 10,000 상한이 있으니 `파트 크기 ≥ 파일 크기 / 10,000`이어야 한다.
- **수신 청크 비트맵** — 조각 i를 받으면 비트 i를 켠다. 모든 비트가 켜지면 조립한다. 빠진 조각 찾기는 "0인 비트 찾기"다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
  - 순차 업로드(tus 코어)는 비트맵 대신 **오프셋 정수 하나**로 충분하다. 앞에서부터 빈틈없이 채우기 때문이다.
- **부분 해시·머클 트리** — 조각마다 해시를 내고, 해시들을 다시 해시해 루트 하나를 만든다. 어느 조각이 틀렸는지 찾을 수 있고, 전체를 다시 읽지 않고 검증할 수 있다. S3 composite 체크섬("checksum of checksums")이 한 단계짜리 예다. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
- **체크섬(CRC·SHA)** — CRC는 우연한 손상 검출용으로 빠르다. SHA-256은 같은 해시를 갖는 다른 데이터를 일부러 만들기 어렵다(충돌 저항). 단 변조 방지가 되려면 해시값이 신뢰 경로로 오거나 HMAC·서명을 써야 한다. 공격자는 데이터와 함께 해시도 바꿀 수 있다. `os/33-data-integrity-checksums` — 미작성([os 영역 표](../../os/README.md)).

## 적용 — 풀어나가는 법

### 1. 크기별로 방식을 고른다

```text
  크기(예시)         방식
  ~ 수 MB           multipart/form-data 한 번 (한도 설정만 정확히)
  ~ 수백 MB         스트리밍 수신 + 413 한도 + 100-continue
  수백 MB ~ GB+     재개 가능 업로드(tus) 또는 스토리지 멀티파트 + presigned URL
```

### 2. 업로드 흐름 (presigned 멀티파트)

1. 클라이언트가 파일 크기·이름·해시를 알리고 업로드 세션을 요청한다.
2. 서버가 권한·크기 한도를 확인한다. `CreateMultipartUpload`로 UploadId를 받는다. 파트마다 presigned URL을 만든다(짧은 만료).
3. 클라이언트가 `Blob.slice`로 조각을 만들어 병렬로 PUT한다. 응답 ETag를 기록한다. 실패한 파트만 재시도한다.
4. 클라이언트가 파트 목록(번호·ETag)을 서버에 보낸다. 서버가 `CompleteMultipartUpload`를 호출한다.
5. 서버가 객체의 크기·체크섬을 확인하고 DB에 "업로드 완료"를 기록한다.
6. 버킷에는 `AbortIncompleteMultipartUpload` 수명 주기 규칙을 둔다.

### 3. 코드

브라우저 — 조각별 체크섬과 병렬 업로드:

```js
const PART = 8 * 1024 * 1024;                       // 8 MiB (예시) — S3 최소 5 MiB 이상
async function uploadParts(file, urls) {            // urls[i] = 파트 i+1의 presigned URL
  const results = await Promise.all(urls.map(async (url, i) => {
    const blob = file.slice(i * PART, Math.min((i + 1) * PART, file.size));
    const res = await fetch(url, { method: 'PUT', body: blob });
    if (!res.ok) throw new Error(`part ${i + 1}: ${res.status}`);
    return { PartNumber: i + 1, ETag: res.headers.get('ETag') };   // Complete에 필요 (CORS Expose 필요)
  }));
  return results;
}

async function sha256Hex(blob) {                    // 전체 또는 조각 해시
  const buf = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
```

- 교차 출처에서 `ETag` 응답 헤더를 읽으려면 버킷 CORS 설정에서 노출해야 한다(`ETag`는 CORS 안전 목록 응답 헤더가 아니다, WHATWG Fetch).
- 위 `Promise.all`은 모든 파트를 한꺼번에 보낸다. 실무에서는 동시 실행 수를 제한한다(예: 4개 (예시)).
- 위 `sha256Hex`는 조각을 메모리에 올린다. 파일 전체 해시는 조각 단위로 누적하는 증분 해시 라이브러리를 쓴다.

Java — Spring MVC에서 힙에 올리지 않고 받기:

```java
@PostMapping(path = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity<Void> upload(@RequestPart("file") MultipartFile file) throws IOException {
    Path dst = storageDir.resolve(UUID.randomUUID().toString());   // filename을 경로로 쓰지 않음
    file.transferTo(dst);                                          // getBytes() 금지
    return ResponseEntity.status(HttpStatus.CREATED).build();
}
```

Java — 파일 내려주기에 `transferTo`(zero-copy 경로):

```java
try (FileChannel in = FileChannel.open(path, StandardOpenOption.READ)) {
    long pos = 0, size = in.size();
    while (pos < size) pos += in.transferTo(pos, size - pos, socketChannel);  // 한 번에 다 안 갈 수 있음
}
```

### 4. 설정과 진단

```nginx
location /upload {
    client_max_body_size 100m;          # 기본 1m (예시 값)
    proxy_request_buffering off;        # 기본 on: 전체를 받은 뒤 상류로 보냄
    proxy_pass http://app;
}
```

```bash
# 413 재현: 한도보다 큰 본문
head -c 2000000 /dev/urandom > /tmp/2m.bin
curl -s -o /dev/null -w '%{http_code}\n' -F file=@/tmp/2m.bin https://example.com/upload

# multipart 원형 보기 (경계·Content-Disposition)
curl -v -F title=휴가 -F file=@a.mp4 https://example.com/upload 2>&1 | head -30

# tus: 오프셋 확인
curl -sI -H 'Tus-Resumable: 1.0.0' https://tus.example.org/files/24e5... | grep -i upload-offset

# 미완료 멀티파트 업로드 목록 (조각이 쌓이고 있나)
aws s3api list-multipart-uploads --bucket my-bucket
```

## 장애 시나리오와 대처

### 1. 단일 요청 대용량 → LB 타임아웃·413

- **현상**: 작은 파일은 되는데 큰 파일은 "업로드 실패"다. 실패 크기가 일정하거나 실패 시간이 일정하다.
- **보이는 형태**
  - 크기가 원인: nginx `413 Request Entity Too Large`(nginx 문서 표기), 에러 로그 `client intended to send too large body: N bytes`(nginx 소스 `ngx_http_core_module.c`), Spring `MaxUploadSizeExceededException`
  - 시간이 원인: 일정 시간(예: 60초) 뒤 연결 끊김, 클라이언트는 `ECONNRESET`나 502·504
- **원인**: 경로 위 한도(nginx `client_max_body_size` 1m, Spring 1MB/10MB, LB idle timeout 60s) 중 하나에 걸렸다.
- **대처**
  - 경로 위 모든 한도를 표로 적고 같은 값으로 맞춘다.
  - 큰 파일은 청크·재개 업로드나 presigned URL로 옮겨 단일 요청의 크기·시간을 줄인다.
  - `Expect: 100-continue`로 거절될 요청을 본문 전송 전에 끝낼 수 있다(최선 노력 — 클라이언트가 기다리지 않을 수 있다).

### 2. 중단 후 처음부터 재전송

- **현상**: 모바일에서 큰 파일 업로드가 거의 끝나지 않는다. 트래픽 비용이 파일 크기의 몇 배다.
- **보이는 형태**: 같은 사용자·같은 파일의 업로드 시작 로그가 여러 번 있고, 매번 0바이트부터 시작한다.
- **원인**: 요청 하나로 보내서 끊기면 서버에 남는 상태가 없다.
- **대처**
  - tus 같은 재개 가능 프로토콜을 쓴다. 끊기면 `HEAD`로 오프셋을 묻고 이어 보낸다.
  - 또는 멀티파트 업로드로 파트 단위 재시도를 한다.
  - 클라이언트는 업로드 URL·UploadId를 로컬에 저장해 앱 재시작 후에도 이어 간다.

### 3. 완료되지 않은 멀티파트 조각 누적 → 스토리지 비용

- **현상**: 버킷의 객체 용량은 작은데 스토리지 청구액이 크다.
- **보이는 형태**: `list-multipart-uploads`에 오래된 업로드가 수천 건 있다. 객체 목록(`ls`)에는 보이지 않는다.
- **원인**
  - 클라이언트가 중간에 포기하거나 Complete를 호출하지 못했다.
  - 완료·중단 전까지 조각이 저장되고 과금된다(S3 문서). 수명 주기 규칙이 없으면 알아서 정리되지 않는다.
- **대처**
  - 버킷에 `AbortIncompleteMultipartUpload` 수명 주기 규칙을 둔다(예: 시작 후 7일 (예시)).
  - 앱은 업로드 세션 테이블에 UploadId를 기록하고, 만료된 세션을 `AbortMultipartUpload`로 정리한다.
  - tus 서버라면 expiration 확장(`Upload-Expires`)으로 미완료 업로드를 지운다.

### 4. 체크섬 없이 조립 → 조용한 손상

- **현상**: 업로드는 "성공"인데 가끔 동영상이 중간부터 깨진다. 재현이 안 된다.
- **보이는 형태**: 서버 저장본의 해시가 원본과 다르다. 크기는 같을 수도 있다.
- **원인**
  - 조각 하나가 전송 중 손상됐거나, 같은 번호의 조각이 두 번 올라가 덮어써졌거나, 조립 순서가 틀렸다.
  - TCP 체크섬은 16비트 1의 보수 합이라(RFC 9293 §3.1) 모든 손상을 잡을 수는 없다. 게다가 앱·디스크 단계의 손상은 전혀 못 본다.
  - multipart/form-data 형식 자체에는 무결성 검사가 없다(RFC 7578 §7).
- **대처**
  - 조각마다 체크섬을 보낸다(tus `Upload-Checksum` → 불일치 시 460, S3 `x-amz-checksum-*`).
  - 전체 객체 체크섬을 클라이언트가 계산해 함께 보내고, 서버가 조립 후 비교한다(S3는 불일치 시 `BadDigest`).
  - 완료 처리는 "체크섬 일치"를 확인한 뒤에만 한다.

### 5. 파일을 힙에 통째로 적재 → OOM

- **현상**: 동시 업로드가 몰리면 앱 서버가 `OutOfMemoryError`나 Node 힙 한도로 죽는다.
- **보이는 형태**: 힙 덤프에 `byte[]`·`Buffer`가 파일 크기만큼 있다. GC 시간이 먼저 치솟는다.
- **원인**: `MultipartFile.getBytes()`, `multer.memoryStorage()`, 요청 본문을 문자열·배열로 읽는 코드. 메모리 = 파일 크기 × 동시 업로드 수가 된다.
- **대처**
  - 스트림으로 받아 디스크나 스토리지로 바로 흘린다(`transferTo`, `getInputStream`, `diskStorage`, busboy).
  - 파일 크기·동시 업로드 수 상한을 둔다.
  - 가장 좋은 방법은 presigned URL로 앱 서버가 파일 바이트를 아예 받지 않게 하는 것이다.

## 핵심 문장

- 대용량 업로드의 문제는 크기 한도, 시간 한도, 재시작 비용, 메모리, 무결성 다섯 가지다. 해법은 쪼개기·오프셋 기억·체크섬·경로에서 앱 빼기다.
- multipart/form-data는 경계로 나눈 한 번의 요청이다. 재개도 무결성 검사도 없고, `filename`은 믿으면 안 된다.
- tus는 서버가 `Upload-Offset`을 기억하고 클라이언트가 `HEAD`로 물어 `PATCH`로 이어 보낸다. 오프셋이 다르면 409, 체크섬이 다르면 460이다.
- S3 멀티파트는 파트를 병렬·재시도하고 번호·ETag 목록으로 완료한다. 완료·중단 전 조각은 과금되므로 수명 주기 규칙이 필수다.
- presigned URL은 만료가 있는 bearer 토큰이다. 앱 서버를 데이터 경로에서 빼는 대신 발급 범위·만료를 좁게 잡는다.

## 관련 주제·근거

- 선행
  - [41-range-requests-and-resume](../41-range-requests-and-resume/2-summary.md) — 다운로드 방향의 이어받기
  - [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md) — 스트리밍·`proxy_request_buffering`
  - `os/33-data-integrity-checksums` · `os/34-zero-copy-and-io-uring` — 미작성([os 영역 표](../../os/README.md))
- 관련
  - [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md) · [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
  - [languages/web-api/30-request-body-and-content-type](../../../languages/web-api/30-request-body-and-content-type/2-summary.md) — 브라우저 `FormData`와 multipart 경계
  - [languages/web-api/31-blob-file-and-object-url](../../../languages/web-api/31-blob-file-and-object-url/2-summary.md) — `Blob`·`File`·`slice`
  - [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) — 완료 콜백 중복 처리
  - `46-load-balancers-and-proxies` — [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md)
- RFC 7578 multipart/form-data(§4.1 경계 · §4.2 Content-Disposition·filename · §4.3 다중 파일 · §4.4 부분 Content-Type · §7 보안) <https://www.rfc-editor.org/rfc/rfc7578>
- RFC 9110 §10.1.1 Expect/100-continue · §15.5.14 413 Content Too Large <https://www.rfc-editor.org/rfc/rfc9110>
- tus 재개 가능 업로드 프로토콜 1.0(코어·creation·expiration·checksum·termination·concatenation) <https://tus.io/protocols/resumable-upload>
- IETF draft-ietf-httpbis-resumable-upload(Resumable Uploads for HTTP, draft-12) <https://datatracker.ietf.org/doc/draft-ietf-httpbis-resumable-upload/>
- Amazon S3 문서
  - 멀티파트 업로드 개요·과금·체크섬 <https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html>
  - 멀티파트 한도 <https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html>
  - presigned URL(만료·bearer·요청 시점 검사) <https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html>
- nginx `ngx_http_core_module`(`client_max_body_size`·`client_body_timeout`·`sendfile`) <https://nginx.org/en/docs/http/ngx_http_core_module.html> · `proxy_request_buffering` <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
- AWS ALB idle timeout(파일 업로드 권고) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html>
- Spring Boot 공통 속성 `spring.servlet.multipart.*` <https://docs.spring.io/spring-boot/appendix/application-properties/index.html>
- multer README(`MemoryStorage` 경고) <https://github.com/expressjs/multer>
- Linux kernel docs Kernel TLS <https://docs.kernel.org/networking/tls.html> · nginx CHANGES 1.21.4(`SSL_sendfile()`) <https://nginx.org/en/CHANGES>
- Linux man-pages `sendfile(2)` <https://man7.org/linux/man-pages/man2/sendfile.2.html> · Java `FileChannel.transferTo` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileChannel.html>
- WHATWG Fetch(CORS-safelisted response-header 목록) <https://fetch.spec.whatwg.org/>
- RFC 9293 TCP §3.1 체크섬(16비트 1의 보수) <https://www.rfc-editor.org/rfc/rfc9293>
