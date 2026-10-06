# network/43-compression-side-channels — 압축 + 암호화 + 비밀 반영 = 길이 사이드채널(CRIME·BREACH) — 정리 (힌트)

## 해결하는 문제

TLS는 내용을 숨긴다.\
하지만 **길이**는 거의 숨기지 못한다.\
압축은 내용에 따라 길이를 바꾼다.\
그래서 "압축한 뒤 암호화"하면 길이가 내용에 대한 힌트가 된다.

  - *사이드채널(side channel)*: 암호를 직접 깨지 않고, 부수적으로 새어 나오는 정보(길이·시간·전력)로 비밀을 알아내는 경로다.

쉬운 예: 봉투 속 편지를 못 읽는 우편 배달부가 있다.\
배달부는 내 편지에 문장을 하나 끼워 넣을 수 있다.\
편지는 부치기 전에 "같은 말이 반복되면 줄여 쓰는" 규칙으로 요약된다.\
배달부가 끼워 넣은 문장이 편지 속 비밀과 같으면, 요약본이 짧아지고 봉투가 얇아진다.\
배달부는 봉투 두께만 보고 추측이 맞았는지 안다.

똑같은 구조다.\
**공격자가 넣은 문자열 + 비밀이 같은 압축 사전으로 압축**되고, **암호문 길이를 공격자가 볼 수 있으면** 비밀이 한 글자씩 샌다.

실무 예:
- 검색 결과 페이지가 검색어를 그대로 보여 주고(반영), 같은 HTML에 CSRF 토큰이 있고, gzip으로 응답한다 → BREACH 조건이 갖춰진다.
- TLS 수준 압축을 켠 서버에서, 요청 헤더의 쿠키가 공격자가 고른 URL 경로와 함께 압축됐다 → CRIME(2012).

## 동작·원리

### 1. 압축이 길이를 바꾸는 방식 — LZ77 역참조

DEFLATE(gzip·zlib의 알고리즘)는 앞에서 나온 문자열이 다시 나오면 "(거리, 길이)" 참조로 바꾼다.

```text
  원문:   ...value="csrf_token=7f3a9c"...  검색어: csrf_token=7
                     ^^^^^^^^^^^^^                 ^^^^^^^^^^^^
                     앞에서 나온 문자열            여기서 다시 나옴
  압축:   ...value="csrf_token=7f3a9c"...  검색어: <거리 N, 길이 12>
```

- 추측이 비밀의 접두사와 **한 글자 더** 맞으면, 역참조가 한 글자 길어진다.
- 틀린 글자는 리터럴로 남는다. 그만큼 출력이 길어진다.
- 그래서 "길이가 가장 짧은 추측 = 맞는 글자"가 된다.

  - *LZ77*: 최근 입력을 담은 **슬라이딩 윈도**에서 가장 긴 일치를 찾아 역참조로 바꾸는 압축법이다. DEFLATE의 윈도는 최대 32KB다(RFC 1951).
  - *DEFLATE*: LZ77 뒤에 허프만 부호를 붙인 압축 형식이다. gzip(RFC 1952)과 zlib이 이것을 담는다.

실제로 돌려 본 결과다(예시 — Node.js `zlib.gzipSync`, 비밀 `csrf_token=7f3a9c`가 든 짧은 HTML에 검색어를 반영).

```text
  검색어(추측)       gzip 길이(바이트)
  csrf_token=0       121
  csrf_token=7       120    <- 한 글자 더 일치
  csrf_token=7e      121
  csrf_token=7f      120    <- 한 글자 더 일치
```

- 차이는 1바이트 안팎이다. 허프만 부호가 비트 단위로 길이를 흔들기 때문에 항상 깔끔하게 나오지는 않는다.
- 공격자는 요청을 여러 번 보내 이 잡음을 줄인다.

### 2. 공격 모델 — 세 조건이 동시에

```text
      [피해자 브라우저] ---- TLS ----> [서버]
         ^    |                          |
         |    +-- 쿠키 자동 첨부 --------+
  (1) 공격자 페이지의 JS가
      bank.com으로 요청을 계속 보내게 함
                                        (2) 응답/요청 안에
                                            비밀 + 공격자 문자열이
                                            같은 압축 문맥에 들어감
      [공격자: 같은 네트워크]
        (3) 암호문 길이만 관찰 -----> 가장 짧은 추측 선택 -> 다음 글자
```

1. **공격자가 평문 일부를 고를 수 있다.** 예: 공격자 사이트의 `<img src="https://bank.com/x?q=추측">`. 브라우저는 쿠키를 자동으로 붙여 보낸다. 단 `SameSite=Lax`·`Strict` 쿠키는 이런 교차 사이트 하위 요청에 붙지 않는다(MDN `Set-Cookie`). 그래서 이 조건은 쿠키 설정에 따라 달라진다.
2. **비밀과 공격자 입력이 같은 압축 사전을 쓴다.** 같은 요청 헤더 블록이나 같은 응답 본문 안에 있다.
3. **공격자가 암호문 길이를 본다.** 같은 Wi-Fi·중간 네트워크에 있으면 된다.

RFC 9110 §17.6은 이 공격군의 뿌리를 "공격자가 통제하는 내용과 기밀 정보 사이에 중복을 만들고, 같은 사전을 쓰는 동적 압축이 그 중복을 더 잘 압축하게 만드는 것"으로 설명한다.

### 3. CRIME (2012) — TLS 수준 압축을 노림

- Juliano Rizzo와 Thai Duong이 2012년 9월 Ekoparty에서 발표했다(CVE-2012-4929, RFC 7457 §2.6).
- 대상: **TLS 레코드 압축**을 켠 연결의 **요청 헤더 속 쿠키**.
- TLS 압축은 HTTP 요청 전체(경로 + 헤더 + 쿠키)를 한 덩어리로 압축했다. 공격자가 고른 경로와 비밀 쿠키가 한 사전에 들어간 셈이다.
- IETF 85 SAAG 발표 자료는 원인을 "공격자가 통제한 데이터와 비밀 데이터가 함께 압축된다"로 요약한다. 대처는 TLS 압축 끄기였다.

```text
  GET /x?sessid=5 HTTP/1.1          <- 공격자가 고른 추측
  Cookie: sessid=5ec20c5e...         <- 브라우저가 붙인 비밀
  --------------------------------
  "sessid=5" 가 두 번 나옴 -> 역참조 -> 더 짧은 레코드
```

- **TLS 1.3은 압축을 없앴다**(RFC 8446 §1.2).
  - ClientHello의 `legacy_compression_methods`는 1바이트 `0`(null)만 담아야 한다(MUST). 다른 값이면 서버가 `illegal_parameter`로 끊어야 한다(MUST, §4.1.2).
- HTTP/2의 헤더 압축 HPACK은 CRIME을 의식해 설계됐다.
  - 동적 테이블은 헤더 값 **전체**가 같을 때만 참조한다. 그래서 한 글자씩 맞히는 공격이 "값 전체를 맞히는" 무차별 대입으로 바뀐다(RFC 7541 §7.1.1).
  - 엔트로피가 낮은 값은 여전히 위험하다. 그래서 `Cookie`·`Authorization`처럼 민감한 헤더는 **never-indexed literal**로 보낼 수 있다(§7.1.3).

### 4. BREACH (2013) — HTTP 응답 본문 압축을 노림

- Yoel Gluck, Neal Harris, Angelo Prado가 Black Hat USA 2013에서 발표했다("BREACH: Reviving the CRIME Attack", RFC 9110 참고문헌).
- 대상: **gzip/deflate로 압축된 HTTP 응답 본문** 안의 비밀(CSRF 토큰·개인정보).
- TLS 압축을 끄는 것으로는 막히지 않는다. 압축이 TLS 위, HTTP 층에서 일어나기 때문이다.
- breachattack.com이 밝힌 취약 조건(세 가지 모두):

```text
  (1) 응답이 HTTP 압축(gzip/deflate)으로 나간다
  (2) 응답 본문이 사용자 입력(쿼리 문자열·POST 값)을 반영한다
  (3) 같은 응답 본문에 비밀(CSRF 토큰·PII 등)이 있다
```

- 같은 사이트는 이 공격이 TLS 버전과 암호군에 상관없다고 적는다. "몇 천 번의 요청, 1분 이내"에 가능하다고도 적는다(발표자 주장).
- RFC 7457 §2.6: TLS 층에서 BREACH를 막는 방법은 알려지지 않았고, 애플리케이션 수준 대처가 필요하다. 예로 CSRF 토큰 무작위화를 든다.

### 5. 계층별 정리

```text
  압축 위치              공격        비밀 위치         현재 상태
  TLS 레코드 압축         CRIME       요청 헤더(쿠키)   TLS 1.3에서 제거, 브라우저 비활성
  SPDY 헤더 압축          CRIME류     요청 헤더(쿠키)   HPACK(RFC 7541)로 대체
  HTTP 본문(gzip·br)     BREACH      응답 본문         지금도 유효 -> 앱이 막는다
  WebSocket 메시지 압축   같은 원리    메시지 본문       44번 노트
```

- SPDY 헤더 압축도 CRIME의 대상이었다. breachattack.com은 "CRIME was mitigated by disabling TLS/SPDY compression"이라고 적는다. 원 발표 자료는 직접 확인하지 못했다.
- Brotli·zstd도 사전 기반 압축이다. 같은 조건이면 같은 원리가 적용된다고 보는 것이 안전하다. 알고리즘별 실측 공격 난이도는 확인하지 못했다 [?].

## 쓰이는 자료구조·알고리즘

- **LZ77 슬라이딩 윈도 + 가장 긴 일치 탐색** — 비밀과 추측의 공통 접두사 길이가 출력 길이로 드러나는 핵심이다. [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md)의 "창 안에서만 본다" 구조와 같다. LZ77 자체는 [algorithm/33-lossless-compression-lz77-huffman](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md).
  - 구현은 보통 3바이트 해시 체인으로 후보 위치를 찾는다. 이 해시 테이블이 [05-hashmap](../../data-structure/05-hashmap/2-summary.md)과 같은 역할이다.
- **허프만 부호** — 자주 나오는 기호에 짧은 비트열을 준다. 길이 신호에 비트 단위 잡음을 섞는다. 공격자는 반복 측정으로 이를 걸러 낸다.
- **적응형 탐색(한 글자씩)** — 추측 공간이 "문자 집합 크기 × 비밀 길이"로 줄어든다. RFC 7541 §7.1은 이를 "지수 시간 공격을 선형 시간 공격으로 바꾼다"고 설명한다.
- **HPACK 동적 테이블** — 헤더 (이름, 값) 쌍을 담는 FIFO 테이블이다. 값 전체 일치만 참조해서 한 글자씩 탐색을 막는다.
- **XOR 마스킹** — CSRF 토큰을 요청마다 무작위 마스크와 XOR해서 내보낸다. 원래 비밀은 같아도 응답에 나가는 문자열이 매번 달라진다.

## 적용 — 풀어나가는 법

### 1. 내 응답이 BREACH 조건을 갖췄나 점검한다

세 질문을 차례로 던진다.

```text
  Q1. 이 응답은 압축되어 나가나?          (Content-Encoding: gzip | br | zstd)
  Q2. 사용자가 조절할 수 있는 값이 본문에 반영되나?  (검색어·에러 메시지·리다이렉트 URL)
  Q3. 같은 본문에 비밀이 있나?            (CSRF 토큰·API 키·개인정보)
        셋 다 "예" -> 위험. 하나라도 끊으면 이 경로는 막힌다.
```

```bash
# Q1: 압축 여부
curl -s -o /dev/null -D - -H 'Accept-Encoding: gzip, br' https://app.example.com/search?q=test \
  | grep -i '^content-encoding'

# 길이 신호 재현: 추측만 바꿔 압축 후 크기를 비교한다
for g in csrf_token=a csrf_token=b csrf_token=c; do
  printf '%s ' "$g"
  curl -s -o /dev/null -w '%{size_download}\n' -H 'Accept-Encoding: gzip' \
    "https://app.example.com/search?q=$g" -b 'session=...'
done
```

- 크기가 추측에 따라 흔들리면, 그 페이지는 비밀과 반영값을 같이 압축하고 있다.
- 이 점검은 **내 서비스**에서만 한다.

### 2. 대처를 효과 순서로 고른다

breachattack.com의 목록을 효과 순서대로 정리했다.

```text
  1. 해당 응답의 HTTP 압축 끄기                  가장 확실, 대신 대역폭 증가
  2. 비밀과 사용자 입력을 다른 응답으로 분리       예: CSRF 토큰은 별도 API/쿠키로
  3. 비밀을 요청마다 무작위화(재발급)
  4. 비밀을 무작위 값과 XOR해서 마스킹           프레임워크 기본값으로 흔함
  5. 민감 페이지에 CSRF 보호                    공격자가 요청을 못 보내게
  6. 길이 숨기기(무작위 패딩)                    잡음만 늘림, 효과 제한적
  7. 요청 속도 제한                             수천 번 요청을 어렵게
```

- 패딩은 약하다. RFC 9113 §10.7도 패딩은 기껏해야 관측 횟수만 늘리고, 압축을 끄거나 제한하는 편이 나을 수 있다(might be preferable)고 적는다.
- 참고로 breachattack.com은 이 목록과 별도로, gzip 라이브러리가 응답 크기에 무작위성을 더하는 HTB(Heal-the-BREACH)를 "매우 효과적"이라고 소개한다(발표자 주장).
- HTTP/2 구현은 보안 채널에서 기밀 데이터와 공격자 통제 데이터를 **같은 사전으로 압축하면 안 된다**(MUST NOT, RFC 9113 §10.6). 출처를 판단할 수 없으면 압축하지 않아야 한다(MUST NOT).

### 3. 프레임워크 기본값을 확인한다

Spring Security 6.0+는 기본 CSRF 핸들러(`XorCsrfTokenRequestAttributeHandler`)로 BREACH를 막는다. 5.x(5.8 포함)의 기본은 마스킹 없는 `CsrfTokenRequestAttributeHandler`다(`CsrfFilter` 소스 5.8.0·6.0.0 태그). 토큰에 무작위성을 섞어 요청마다 다른 값을 내보낸다(Spring Security 문서).

```java
// 6.0+에서는 기본값이 이미 BREACH 보호다. 5.8에서는 이렇게 명시해야 한다.
http.csrf(csrf -> csrf
    .csrfTokenRequestHandler(new XorCsrfTokenRequestAttributeHandler()));
```

- 기본 대신 `CsrfTokenRequestAttributeHandler`(마스킹 없음)로 바꾸면 이 보호가 빠진다.
- Django도 폼에 넣는 CSRF 값을 `get_token()` 호출마다 무작위 마스크로 섞는다(Django 문서).

마스킹의 원리를 TS로 쓰면 이렇다.

```ts
import { randomBytes } from 'node:crypto';

// 비밀(secret)은 세션에 그대로 두고, HTML에는 매번 다른 문자열을 내보낸다.
function maskToken(secret: Buffer): string {
  const mask = randomBytes(secret.length);
  const masked = Buffer.alloc(secret.length);
  for (let i = 0; i < secret.length; i++) masked[i] = secret[i] ^ mask[i];
  return Buffer.concat([mask, masked]).toString('base64url'); // mask || (secret XOR mask)
}

function unmaskToken(token: string): Buffer {
  const raw = Buffer.from(token, 'base64url');
  const n = raw.length / 2;
  const out = Buffer.alloc(n);
  for (let i = 0; i < n; i++) out[i] = raw[i] ^ raw[n + i];
  return out; // 세션의 secret과 상수 시간 비교(timingSafeEqual)
}
```

- 응답마다 문자열이 달라서, 공격자의 추측이 이전 응답의 토큰 문자열과 맞아도 다음 응답에서는 의미가 없다.

### 4. 압축을 선택적으로 끈다

nginx `gzip`은 기본값이 `off`다(nginx 문서). 켰다면 민감 경로만 제외할 수 있다.

```nginx
gzip on;
gzip_types text/css application/javascript;   # text/html은 이 설정과 무관하게 항상 압축된다
location /account/ {
    gzip off;                                  # 비밀 + 반영이 섞이는 페이지
}
```

- `gzip on`이면 `text/html` 응답은 `gzip_types`와 상관없이 항상 압축된다(nginx 문서). 그래서 민감한 HTML 경로는 `location`에서 따로 꺼야 한다.
- 정적 JS·CSS에는 비밀도 반영값도 없다. 압축해도 안전하다.
- 앞단 CDN·프록시가 다시 압축하지 않는지도 확인한다(39번 `http-content-encoding` 참고).

## 장애 시나리오와 대처

### 1. 응답 길이 차이로 CSRF 토큰이 추론된다 (BREACH)

- **현상**: 보안 점검에서 "검색 페이지의 CSRF 토큰이 압축 길이로 복원 가능"이라는 지적을 받는다.
- **보이는 형태**
  - `Content-Encoding: gzip` 응답.
  - `q` 파라미터만 바꿨는데 `size_download`가 1~2바이트씩 달라진다.
  - 운영 지표로는 같은 IP에서 같은 경로로 수천 건의 짧은 요청이 몰린다.
- **원인**: 반영값(검색어)과 비밀(CSRF 토큰)이 같은 gzip 스트림에 들어간다. 공격자는 암호문 길이만 봐도 된다.
- **대처**
  - 토큰을 요청마다 마스킹한다(프레임워크 기본값을 확인한다).
  - 또는 토큰을 본문에서 빼서 쿠키나 별도 요청으로 옮긴다.
  - 급하면 해당 경로의 압축을 끈다.

### 2. 쿠키가 요청 압축으로 새어 나간다 (CRIME)

- **현상**: 오래된 서버·임베디드 장비가 TLS 압축을 협상한다. 점검 도구가 "TLS compression enabled"로 표시한다.
- **보이는 형태**: TLS 1.2 이하 연결에서 `openssl s_client -comp` 출력의 `Compression:` 줄이 `NONE`이 아니다.
  - `-comp`가 필요하다. OpenSSL 1.1.0부터 클라이언트가 압축을 기본으로 끄므로, 옵션 없이는 서버가 압축을 지원해도 `NONE`이 나온다(openssl-s_client 문서).
- **원인**: TLS 레코드 압축은 공격자 경로와 쿠키를 한 사전에 넣는다.
- **대처**
  - TLS 압축을 끈다. TLS 1.3만 쓰면 압축 자체가 없다(RFC 8446).
  - 클라이언트·서버 TLS 라이브러리를 올린다.

```bash
openssl s_client -comp -connect legacy.example.com:443 -tls1_2 </dev/null 2>/dev/null \
  | grep -E '^(Compression|Expansion)'
```

### 3. 프록시가 여러 사용자의 요청을 한 HTTP/2 연결에 모아 헤더가 샌다

- **현상**: 공용 프록시(예: 사내 게이트웨이)가 여러 클라이언트의 요청을 한 HTTP/2 연결로 원 서버에 보낸다.
- **보이는 형태**: 증상이 조용하다. 설계 리뷰나 점검에서만 드러난다.
- **원인**
  - 서로 신뢰하지 않는 주체가 **같은 HPACK 동적 테이블**을 공유한다.
  - 한 주체가 넣은 헤더 값을 다른 주체가 추측으로 확인할 수 있다(RFC 7541 §7.1.1).
- **대처**
  - 민감 헤더(`Cookie`, `Authorization`)는 never-indexed literal로 보낸다.
  - 중간자는 그 표현을 인덱싱하는 표현으로 다시 인코딩하면 안 된다(MUST NOT, §7.1.3).
  - 가능하면 주체별로 연결을 분리한다.

### 4. "압축을 끄면 된다"로 대처했다가 대역폭·지연이 튄다

- **현상**: BREACH 지적 뒤 전역 `gzip off`를 했다. 다음 날 CDN 전송량과 페이지 로드 시간이 크게 늘었다.
- **보이는 형태**: 대역폭 그래프 상승, `Content-Encoding` 헤더 사라짐.
- **원인**: 위험한 것은 "비밀 + 반영"이 같이 있는 응답뿐이다. 정적 자원까지 압축을 끌 이유는 없다.
- **대처**
  - 압축은 경로·타입별로 끈다.
  - 근본 대처는 토큰 마스킹·분리다.

## 핵심 문장

- 암호화는 내용을 숨기지만 길이는 숨기지 않는다. 압축은 내용에 따라 길이를 바꾼다. 둘을 겹치면 길이가 내용에 대한 신호가 된다.
- 공격 조건은 셋이다. 공격자가 평문 일부를 고르고, 그것이 비밀과 같은 압축 사전에 들어가고, 공격자가 암호문 길이를 본다.
- CRIME은 TLS 수준 압축(요청 헤더의 쿠키)을 노렸고, TLS 1.3은 압축을 아예 없앴다. BREACH는 HTTP 본문 압축을 노리므로 TLS 설정으로는 막을 수 없다.
- BREACH 대처는 셋 중 하나를 끊는 것이다. 민감 응답의 압축 끄기, 비밀과 반영값 분리, 비밀의 요청별 무작위화·마스킹이다. 패딩은 약한 대처다.
- HPACK은 값 전체 일치만 참조해 한 글자씩 탐색을 막는다. 그래도 엔트로피가 낮은 값은 약하므로 민감 헤더는 인덱싱하지 않는다.

## 관련 주제·근거

- 선행
  - [39-http-content-encoding](../39-http-content-encoding/2-summary.md) — 압축 협상·`Vary`
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — TLS 1.3에서 사라진 것들
  - [algorithm/33-lossless-compression-lz77-huffman](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md)
- 후속·연결
  - [44-websocket-compression](../44-websocket-compression/2-summary.md) — 메시지 압축에서 같은 원리
  - [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md) — HPACK
  - [security/20-csrf-and-samesite](../../security/20-csrf-and-samesite/2-summary.md)
- RFC 7457 §2.6 Compression Attacks: CRIME, TIME, and BREACH <https://www.rfc-editor.org/rfc/rfc7457>
- RFC 8446 §1.2(압축 제거) · §4.1.2(`legacy_compression_methods`) <https://www.rfc-editor.org/rfc/rfc8446>
- RFC 9110 §17.6 Attacks Using Shared-Dictionary Compression <https://www.rfc-editor.org/rfc/rfc9110>
- RFC 9113 §10.6 Use of Compression · §10.7 Use of Padding <https://www.rfc-editor.org/rfc/rfc9113>
- RFC 7541 §7.1 Probing Dynamic Table State · §7.1.3 Never-Indexed Literals <https://www.rfc-editor.org/rfc/rfc7541>
- RFC 1951 DEFLATE · RFC 3749 TLS Compression Methods
- Rizzo, Duong, "The CRIME Attack", Ekoparty 2012 (CVE-2012-4929). 원 슬라이드는 직접 확인하지 못했고, IETF 85 SAAG 발표 "BEAST & CRIME" <https://www.ietf.org/proceedings/85/slides/slides-85-saag-1.pdf>로 공격 방식을 확인했다.
- Gluck, Harris, Prado, "BREACH: Reviving the CRIME Attack", Black Hat USA 2013 · <https://www.breachattack.com/>
- Spring Security "Cross Site Request Forgery (CSRF)" — `XorCsrfTokenRequestAttributeHandler` <https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html>
  - 기본 핸들러 버전 차이: `CsrfFilter.java` 5.8.0 태그(`CsrfTokenRequestAttributeHandler`) vs 6.0.0 태그(`XorCsrfTokenRequestAttributeHandler`) <https://github.com/spring-projects/spring-security/blob/6.0.0/web/src/main/java/org/springframework/security/web/csrf/CsrfFilter.java>
- OpenSSL `openssl-s_client` `-comp`(1.1.0부터 압축 기본 꺼짐) <https://docs.openssl.org/3.0/man1/openssl-s_client/>
- Django "Cross Site Request Forgery protection" <https://docs.djangoproject.com/en/stable/ref/csrf/>
- nginx `ngx_http_gzip_module` <https://nginx.org/en/docs/http/ngx_http_gzip_module.html>
- MDN `Set-Cookie` — `SameSite` 속성 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie>
