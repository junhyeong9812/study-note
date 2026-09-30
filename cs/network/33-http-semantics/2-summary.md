# network/33-http-semantics — HTTP 의미론: 메서드·상태 코드·헤더·안전/멱등·쿠키 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

클라이언트와 서버 사이에는 프록시·로드밸런서·캐시가 여럿 끼어 있다.\
이 중간자들은 요청의 "내용"을 모른다.\
그런데도 "이 요청은 다시 보내도 되나", "이 응답은 저장해도 되나", "이 실패는 누구 탓인가"를 판단해야 한다.\
그 판단의 공통 언어가 HTTP 의미론이다.

  - *의미론(semantics)*: 메시지가 "무엇을 뜻하는지"의 약속이다. 바이트를 어떻게 늘어놓는지(문법·프레이밍)와 구분한다.

쉬운 예: 택배 송장이다.\
송장에는 "취급 주의", "착불", "반송 불가" 같은 표준 칸이 있다.\
택배 기사는 상자를 열지 않고도 송장만 보고 처리 방법을 정한다.

똑같은 구조다.\
메서드(GET/POST…)와 상태 코드(200/502…)와 헤더가 송장의 표준 칸이다.\
중간자는 본문을 열지 않고 이 칸만 보고 재시도·캐시·라우팅을 정한다.

실무 예:
- 재시도 라이브러리는 "GET이면 다시 보내고 POST면 안 보낸다"를 메서드로 정한다.
- 로드밸런서는 상류가 죽었을 때 502나 504를 만들어 돌려준다. 이 숫자를 잘못 읽으면 엉뚱한 서버를 뒤진다.
- 브라우저는 `Set-Cookie`의 속성을 보고 다른 사이트 요청에 쿠키를 붙일지 정한다.

## 동작·원리

### 1. 의미론은 하나, 전송 형식은 셋

```text
                  RFC 9110  HTTP Semantics
          (메서드 · 상태 코드 · 헤더 · 내용 · 캐시 규칙 연결)
                 |                |                 |
        +--------+-----+   +------+------+   +------+------+
        | HTTP/1.1     |   | HTTP/2      |   | HTTP/3      |
        | RFC 9112     |   | RFC 9113    |   | RFC 9114    |
        | 텍스트 줄     |   | 이진 프레임  |   | QUIC 스트림  |
        +--------------+   +-------------+   +-------------+
               TCP          TCP(+TLS)         UDP 위 QUIC
```

- RFC 9110은 버전과 무관한 "뜻"만 정한다.
- 1.1·2·3은 그 뜻을 선에 싣는 방법만 다르다.
- 그래서 `GET`이 안전하다는 사실, `503`의 의미는 버전이 바뀌어도 같다.

### 2. 메시지의 모양

```text
  요청                                   응답
  +-------------------------------+      +-------------------------------+
  | 제어 데이터                    |      | 제어 데이터                    |
  |   메서드  GET                  |      |   상태 코드  200               |
  |   대상    /orders/42           |      |                               |
  +-------------------------------+      +-------------------------------+
  | 헤더 필드                      |      | 헤더 필드                      |
  |   Host: api.example.com       |      |   Content-Type: application/json
  |   Accept: application/json    |      |   Cache-Control: no-store     |
  +-------------------------------+      +-------------------------------+
  | 내용(content, 선택)            |      | 내용                           |
  +-------------------------------+      +-------------------------------+
  | 트레일러(선택)                  |      | 트레일러(선택)                  |
  +-------------------------------+      +-------------------------------+
```

(RFC 9110 §6 "Message Abstraction")

- `Host`는 요청마다 필요하다. 한 IP에 여러 도메인을 올린 서버가 이 값으로 사이트를 고른다(§7.2).
  - HTTP/2·3에서는 `:authority` 가상 헤더가 그 역할을 대신할 수 있다.
  - *가상 헤더(pseudo-header)*: HTTP/2·3에서 메서드·경로·상태 같은 제어 데이터를 `:`로 시작하는 이름으로 싣는 필드다.

### 3. 메서드 — 안전·멱등·캐시 가능

```text
  메서드    안전   멱등   캐시 의미 정의   흔한 용도
  GET       O      O      O               조회
  HEAD      O      O      O               헤더만 조회
  OPTIONS   O      O      -               지원 기능 조회(CORS preflight)
  TRACE     O      O      -               경로 진단(보통 막아 둠)
  PUT       -      O      -               전체 교체
  DELETE    -      O      -               삭제
  POST      -      -      O(*)            생성·처리 요청
  PATCH     -      -      O(*)            부분 수정 (RFC 5789)
  CONNECT   -      -      -               터널

  (*) POST(RFC 9110)·PATCH(RFC 5789 §2) 응답은 명시적 신선도 + 요청 URI와 같은 Content-Location이 있을 때만
      캐시할 수 있다. 실제로 대부분의 캐시는 GET·HEAD만 저장한다(§9.2.3).
```

(RFC 9110 §9.2.1 안전, §9.2.2 멱등, §9.2.3 캐시 · RFC 5789 §2)

- **안전(safe)**: 클라이언트가 서버 상태 변경을 **요청하지 않는** 메서드다(§9.2.1).
  - 서버가 로그를 남기는 부작용은 괜찮다. 클라이언트가 요청한 것이 아니기 때문이다.
  - 그래서 크롤러·프리페치가 안전 메서드를 마음대로 호출해도 된다는 전제가 선다.
  - `GET /delete?id=3` 같은 설계는 이 전제를 깬다. RFC는 이런 동작을 안전 메서드로 호출하면 막아야 한다고 적는다(MUST, §9.2.1).
- **멱등(idempotent)**: 같은 요청을 여러 번 보냈을 때 **의도한 효과**가 한 번 보낸 것과 같은 메서드다(§9.2.2).
  - 응답까지 같다는 뜻은 아니다. 두 번째 `DELETE`는 404를 받을 수 있다.
  - 멱등이 중요한 이유는 **재시도**다. 응답을 받기 전에 연결이 끊기면, 멱등 요청은 새 연결로 다시 보내도 된다.
- 재시도 규칙(§9.2.2)
  - 클라이언트는 비멱등 요청을 자동 재시도하지 않아야 한다(SHOULD NOT). 예외는 요청이 실제로 멱등임을 알거나, 원래 요청이 적용되지 않았음을 알 수 있을 때다.
  - 프록시는 비멱등 요청을 자동 재시도하면 안 된다(MUST NOT).
  - 클라이언트는 실패한 자동 재시도를 다시 자동 재시도하지 않아야 한다(SHOULD NOT).

### 4. 상태 코드 — 첫 자리가 분류

```text
  1xx  정보      100 Continue, 101 Switching Protocols
  2xx  성공      200 OK, 201 Created, 204 No Content, 206 Partial Content
  3xx  리다이렉트 301, 302, 303, 304 Not Modified, 307, 308
  4xx  클라 오류  400, 401, 403, 404, 405, 409, 412, 429
  5xx  서버 오류  500, 502, 503, 504
```

- 모르는 코드를 받으면 클라이언트는 그 클래스의 `x00`처럼 다룬다. 첫 자리만 봐도 처리 방향이 정해진다(§15).
- 이유 문구("Not Found")는 권고일 뿐이다. 바꾸거나 빼도 프로토콜에 영향이 없다(§15.1).

자주 헷갈리는 쌍:

```text
  401 Unauthorized   인증 정보가 없거나 틀림. WWW-Authenticate 헤더를 반드시 보냄 (MUST, §15.5.2)
  403 Forbidden      누군지는 알지만 권한 없음. 같은 자격으로 자동 재시도하지 말 것 (SHOULD NOT, §15.5.4)

  405 Method Not Allowed   Allow 헤더에 지원 메서드 목록을 반드시 담음 (MUST, §15.5.6)
  429 Too Many Requests    속도 제한. Retry-After를 담을 수 있음 (MAY, RFC 6585 §4)

  301 / 302   리다이렉트 시 POST를 GET으로 바꿔도 됨 (MAY — 역사적 이유, §15.4.2·§15.4.3)
  307 / 308   메서드를 유지하는 리다이렉트 (307 MUST NOT change, §15.4.8 · 307·308 도입 배경은 §15.4 Note, RFC 7538)
  303 See Other   다른 자원을 GET으로 가져가라는 뜻 (POST 뒤 결과 페이지로 보낼 때)
```

### 5. 502 · 503 · 504 — 게이트웨이가 만든 숫자

```text
  Client ---> [ 게이트웨이 / 프록시 / LB ] ---> Upstream(원 서버)

  502 Bad Gateway      게이트웨이가 상류에서 "잘못된 응답"을 받음
                       (연결 거부, 응답 도중 끊김·RST, 헤더 깨짐)
  503 Service Unavail. 응답하는 서버가 지금 처리 불가 (과부하·점검)
                       -> 곧 풀릴 것으로 예상. Retry-After 가능
  504 Gateway Timeout  게이트웨이가 상류의 응답을 "제때" 못 받음
```

(RFC 9110 §15.6.3~§15.6.5)

- 502·504는 **게이트웨이나 프록시가** 상류 문제를 대신 알리는 코드다. 원인은 상류 쪽에 있다.
- 503은 응답하는 서버 자신의 상태다. 다만 LB가 "살아 있는 대상이 없다"를 503으로 표현하기도 한다(AWS ALB 문서).
- nginx 소스에서는 상류 타임아웃이 504, 연결 오류·잘못된 응답이 502가 된다(`ngx_http_upstream_next`).

### 6. 헤더 — 대소문자 무시, 여러 줄이면 쉼표로 합침

```text
  수신한 줄                         의미상 필드 값
  Accept-Encoding: gzip             Accept-Encoding = "gzip, br"
  accept-encoding: br        --->   (이름은 대소문자 무시, 순서대로 쉼표 결합)

  예외
  Set-Cookie: a=1; Path=/           합치면 안 된다 -> 줄마다 따로 보관
  Set-Cookie: b=2; HttpOnly
```

- 필드 이름은 대소문자를 구분하지 않는다(§5.1).
- 같은 이름이 여러 줄이면 순서대로 쉼표로 이은 목록이 된다(§5.2). 그래서 프록시는 같은 이름 줄의 순서를 바꾸면 안 된다(MUST NOT, §5.3).
- 목록 문법을 허용하지 않는 필드를 여러 줄로 보내면 안 된다(MUST NOT, §5.3).
- `Set-Cookie`는 실무상 여러 줄로 오고 목록 문법도 아니다. 그래서 받는 쪽이 특별 취급해야 한다(§5.3 Note).
- *hop-by-hop 헤더*: 한 구간(연결)에만 의미가 있는 헤더다. `Connection` 헤더에 이름이 나열된 필드는 프록시가 다음 구간으로 넘기지 않는다(§7.6.1).

### 7. 쿠키 — 상태 없는 HTTP에 붙인 기억

```text
  1) 로그인
  Browser ---- POST /login ------------------------------> Server
          <--- 200  Set-Cookie: sid=abc; Path=/; Secure;
                               HttpOnly; SameSite=Lax  ----

  2) 이후 요청 (브라우저가 조건을 따져 자동으로 붙임)
  Browser ---- GET /me   Cookie: sid=abc --------------> Server
```

- HTTP 자체는 요청끼리 기억이 없다. 쿠키가 "같은 사용자"를 잇는다.
- 주요 속성

```text
  속성          뜻                                               근거
  Expires       절대 만료 시각                                    RFC 6265 §4.1.2.1
  Max-Age       상대 만료(초). Expires와 함께 있으면 Max-Age 우선   §4.1.2.2
  Domain        생략하면 보낸 호스트에만(host-only). 넣으면 하위 도메인까지   §4.1.2.3, MDN
  Path          이 경로 아래 요청에만 보냄                          §4.1.2.4
  Secure        HTTPS 요청에만 보냄                                §4.1.2.5
  HttpOnly      JS(document.cookie)로 못 읽음                     §4.1.2.6
  SameSite      크로스 사이트 요청에 보낼지: Strict / Lax / None      RFC 6265bis 초안, MDN
```

- **SameSite**
  - `Strict`: 같은 사이트에서 시작한 요청에만 보낸다.
  - `Lax`: 추가로, 크로스 사이트라도 **최상위 탐색 + 안전 메서드**(예: 링크 클릭 GET)면 보낸다.
  - `None`: 크로스 사이트·같은 사이트 요청 모두에 보낸다. 이때 `Secure`가 필수다(MDN).
  - 생략하면 일부 브라우저는 `Lax`로 취급한다(MDN). 그래서 크로스 사이트 POST 콜백에서 쿠키가 빠지는 일이 생긴다.
    - 예외: 기본값으로 적용된 `Lax`는 더 느슨하다. 설정된 지 2분이 안 된 쿠키는 크로스 사이트 **최상위 탐색** POST(폼 제출 등)에도 붙는다(MDN, RFC 6265bis 초안 "Lax-allowing-unsafe" — 브라우저 선택 사항 MAY). `fetch`·iframe 같은 하위 요청에는 붙지 않는다. 그래서 "로그인 직후에는 되고 조금 지나면 안 되는" 현상이 나올 수 있다.
  - *크로스 사이트*: 요청을 시작한 페이지의 사이트(등록 도메인 기준)와 요청 대상 사이트가 다른 경우다.
- `__Host-` 접두 이름은 `Secure` 필수, `Domain` 금지, `Path=/` 필수다(MDN). 하위 도메인이 쿠키를 덮어쓰는 공격을 막는다.

## 쓰이는 자료구조·알고리즘

- **헤더 = 대소문자 무시 다중값 맵** — 키는 소문자로 정규화하고, 값은 순서 있는 리스트로 둔다.
  - 구현마다 합치는 방식이 다르다. Node.js는 이름을 소문자로 바꾸고, `set-cookie`는 항상 배열, `cookie`는 `; `로, 나머지 대부분은 `, `로 합친다. 일부 필드(`content-type`, `host` 등)는 중복을 버린다(Node `message.headers` 문서).
  - 해시 맵 기초는 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) 참고.
- **쿠키 저장소 = (이름, 도메인, 경로) 키 맵 + 만료 시각** — 요청마다 도메인 일치·경로 일치·만료·Secure·SameSite를 걸러 붙인다(RFC 6265 §5.3~§5.4).
- **상태 코드 분기 = 첫 자리로 분류하는 결정 표** — 2xx 성공, 3xx 이동, 4xx 대체로 수정 필요(단 408·429는 시간을 두고 재시도 가능), 5xx 재시도 후보.
- **리다이렉트 추적 = 횟수 상한** — 무한 루프를 막으려고 따라가는 횟수를 센다. WHATWG Fetch는 20회에서 네트워크 오류로 끝낸다.
- **재시도 판정 = 메서드 기반 규칙표** — 멱등이면 재시도 후보, 아니면 멱등 키 같은 별도 수단이 있을 때만([ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 요청·응답을 날것으로 본다

```bash
# 요청 줄·헤더(>)와 응답 줄·헤더(<)를 모두 출력
curl -v https://api.example.com/orders/42

# 헤더만 (HEAD 요청)
curl -I https://api.example.com/orders/42

# 상태 코드만 뽑기 — 스크립트용
curl -s -o /dev/null -w '%{http_code}\n' https://api.example.com/health

# 리다이렉트를 따라가며 매 단계 보기 (POST 유지 여부 확인)
curl -v -L -X POST -d 'a=1' https://example.com/old-path
```

### 2. 실패 응답을 "누가 만들었나"로 먼저 가른다

1. 응답 헤더의 `Server`, `Via`, LB 전용 헤더를 본다. 게이트웨이가 만든 응답인지, 앱이 만든 응답인지 구분한다.
2. 게이트웨이가 만든 502·504면 **게이트웨이 로그**를 본다.
   - nginx `error.log` 예:
     - `connect() failed (111: Connection refused) while connecting to upstream` → 502
     - `upstream prematurely closed connection while reading response header from upstream` → 502
     - `upstream timed out (110: Connection timed out) while reading response header from upstream` → 504
3. 앱이 만든 5xx면 앱 로그와 트레이스를 본다.

### 3. 코드에서 — 상태 코드와 메서드를 판단에 쓴다

JS — `fetch`는 4xx·5xx에서 reject하지 않는다. `res.ok`(200~299)를 직접 확인한다.

```ts
async function getOrder(id: string) {
  const res = await fetch(`/orders/${id}`);
  if (!res.ok) {
    // 4xx: 대체로 요청을 고쳐야 한다. 예외: 408·429는 시간을 두고 재시도(429는 Retry-After 존중)
    // 5xx: 재시도 후보. 단, 메서드가 멱등일 때만
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}
```

Java — 재시도 여부를 메서드와 상태로 정한다(개념 예시).

```java
static final Set<String> IDEMPOTENT = Set.of("GET", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE");

boolean retryable(String method, int status, boolean hasIdempotencyKey) {
    boolean safeToRepeat = IDEMPOTENT.contains(method) || hasIdempotencyKey;
    boolean transientFailure = status == 502 || status == 503 || status == 504 || status == 429;
    return safeToRepeat && transientFailure;
}
```

Node — `Set-Cookie`를 여러 개 보낼 때는 배열로 넘긴다. 한 줄로 합치면 브라우저가 잘못 해석한다.

```js
res.setHeader('Set-Cookie', [
  '__Host-sid=abc; Path=/; Secure; HttpOnly; SameSite=Lax',
  'theme=dark; Path=/; Max-Age=31536000',
]);
```

### 4. API 설계에서

- 조회는 GET, 생성은 POST, 전체 교체는 PUT, 부분 수정은 PATCH로 맞춘다. 메서드가 캐시·재시도 동작을 결정하기 때문이다.
- 폼 POST 뒤에는 303으로 결과 페이지를 준다. 새로 고침으로 POST가 다시 가지 않는다.
- 경로를 영구 이전할 때 POST가 걸린 경로라면 301 대신 308을 쓴다.

## 장애 시나리오와 대처

### 1. 502 · 503 · 504를 혼동해 엉뚱한 곳을 진단한다

- **현상**: 장애 알림이 "5xx 급증" 하나로 뜬다. 앱 팀이 앱 로그를 뒤지는데 에러가 없다.
- **보이는 형태**
  - LB 지표에서 LB가 만든 5xx(AWS ALB `HTTPCode_ELB_5XX_Count`)와 대상이 만든 5xx(`HTTPCode_Target_5XX_Count`)가 따로 잡힌다.
  - nginx `error.log`에 `upstream timed out` 또는 `connect() failed`가 찍힌다.
- **원인** — 숫자별로 보는 곳이 다르다.
  - 502: 상류가 연결을 거부했거나, 응답 도중 끊었거나, 응답이 깨졌다. AWS ALB 문서는 "대상의 keep-alive가 LB idle timeout보다 짧아 대상이 먼저 끊은 경우"도 502 원인으로 든다.
  - 503: 서버가 스스로 과부하·점검이라고 답했거나, LB에 건강한 대상이 없다.
  - 504: 상류가 연결은 됐지만 제때 답하지 않았다. 느린 쿼리·외부 호출 대기가 흔하다.
- **대처**
  - 대시보드를 "누가 만든 5xx인가"로 나눈다.
  - 502는 상류 프로세스 생존·연결 수명(35번)을, 503은 용량·헬스체크를, 504는 상류 처리 시간과 타임아웃 설정을 본다.

### 2. POST 자동 재시도로 주문이 두 번 생긴다

- **현상**: 네트워크가 흔들린 날 중복 주문이 생긴다.
- **보이는 형태**: 같은 사용자·같은 금액의 주문이 몇 초 차이로 두 건 있다. 클라이언트 로그에는 첫 시도가 `ECONNRESET`이나 타임아웃으로 남는다.
- **원인**
  - 첫 요청은 서버에서 처리됐다. 응답만 돌아오지 못했다.
  - 클라이언트 라이브러리나 게이트웨이가 POST를 재시도했다. RFC 9110 §9.2.2가 하지 말라는(SHOULD NOT) 동작이다.
- **대처**
  - 비멱등 요청에는 재시도를 끈다. nginx는 1.9.13부터 기본으로, 요청을 이미 상류에 보낸 뒤라면 비멱등 요청(POST·LOCK·PATCH)을 다음 상류로 넘기지 않는다(`proxy_next_upstream`의 `non_idempotent`를 켜지 않는 한, nginx 문서).
  - 재시도가 필요하면 `Idempotency-Key` 같은 멱등 키를 두고 서버가 중복을 걸러낸다([ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)).

### 3. 리다이렉트 뒤 요청 본문이 사라진다

- **현상**: 경로를 옮긴 뒤 폼 전송이 "빈 요청"으로 들어온다.
- **보이는 형태**: `curl -v -L -X POST`로 보면 두 번째 요청이 `GET`이거나 본문이 없다. 서버 로그에 옮긴 경로로 GET이 찍힌다.
- **원인**: 301·302를 받은 사용자 에이전트는 POST를 GET으로 바꿀 수 있다(MAY, §15.4.2·§15.4.3). RFC 9110 §15.4 Note는 실무 관행이 GET으로 바꾸는 쪽으로 굳었다고 적는다.
- **대처**: 메서드를 유지해야 하면 307(임시)·308(영구)을 쓴다.

### 4. 헤더 이름·중복을 잘못 다뤄 값이 사라진다

- **현상**: 로그인 뒤 쿠키 하나만 저장된다. 또는 헤더 값이 `undefined`로 나온다.
- **보이는 형태**
  - `Set-Cookie`가 `a=1, b=2`처럼 한 줄로 합쳐져 나간다. 브라우저는 이를 쿠키 하나로 해석한다.
  - Node에서 `req.headers['Content-Type']`이 `undefined`다. 키가 소문자로 바뀌어 있기 때문이다.
- **원인**: 헤더를 대소문자 구분 단일값 맵으로 다뤘다. `Set-Cookie`의 예외를 무시했다(RFC 9110 §5.3).
- **대처**
  - 헤더는 라이브러리의 대소문자 무시 API로 읽는다. Java `java.net.http.HttpHeaders`는 이름의 대소문자를 무시하고 값을 리스트로 보관한다(Javadoc). Node는 소문자 키로 읽는다.
  - `Set-Cookie`는 줄마다 따로 쓴다.

### 5. SameSite 기본값 때문에 크로스 사이트 로그인 콜백에서 세션이 빠진다

- **현상**: 외부 결제·SSO 페이지에서 우리 사이트로 POST로 돌아올 때만 "로그인 풀림"이 난다.
- **보이는 형태**: 콜백 요청에 `Cookie` 헤더가 없다. 브라우저 개발자 도구에 SameSite 때문에 쿠키가 차단됐다는 경고가 뜬다.
- **원인**: 세션 쿠키에 `SameSite`를 지정하지 않았다. 브라우저가 이를 `Lax`로 취급하면 크로스 사이트 POST에는 쿠키가 붙지 않는다(MDN). 단 기본값 `Lax`를 쓰는 브라우저 일부는 설정 후 2분 안의 쿠키를 최상위 탐색 POST에도 붙이므로, 쿠키가 막 발급된 경우에는 증상이 안 보일 수 있다(MDN).
- **대처**
  - 콜백을 GET 최상위 탐색으로 바꾸거나, 콜백 전용 쿠키를 `SameSite=None; Secure`로 둔다.
  - `None`은 CSRF 방어를 약하게 하므로 범위를 좁힌다. 세부는 security/11 세션·쿠키 보안에서 다룬다.

## 핵심 문장

- RFC 9110은 버전과 무관한 HTTP의 뜻을 정하고, 1.1·2·3은 그 뜻을 선에 싣는 방법만 다르다.
- 안전은 "상태 변경을 요청하지 않음", 멱등은 "여러 번 보내도 의도한 효과가 같음"이다. 재시도해도 되는지를 이 성질로 정한다.
- 502는 상류의 잘못된 응답, 504는 상류의 늦은 응답, 503은 응답하는 서버 자신의 일시적 불능이다. 502·504는 게이트웨이가 상류 문제를 대신 알리는 코드다.
- 헤더 이름은 대소문자를 무시하고 같은 이름은 쉼표로 합친다. `Set-Cookie`만 예외라 줄마다 따로 다룬다.
- 쿠키의 `SameSite`는 크로스 사이트 요청에 쿠키를 붙일지 정하고, 생략하면 일부 브라우저는 `Lax`로 취급한다.

## 관련 주제·근거

- 선행
  - [23-socket-api](../23-socket-api/2-summary.md)
- 후속
  - `34-http-caching` — [34-http-caching](../34-http-caching/2-summary.md)
  - `35-http-connection-management` — [35-http-connection-management](../35-http-connection-management/2-summary.md)
  - `36-http2-multiplexing` — [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md)
  - `security/11-sessions-and-cookie-security` — 미작성([security 영역 표](../../security/README.md))
  - `web-platform/05-fetch-from-browser` — 미작성([web-platform 영역 표](../../web-platform/README.md))
  - [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) — 비멱등 요청 재시도의 앱 쪽 방어
- RFC 9110 HTTP Semantics <https://www.rfc-editor.org/rfc/rfc9110>
  - §5.1 필드 이름(대소문자 무시) · §5.2 결합 값 · §5.3 필드 순서와 `Set-Cookie` 예외
  - §6 메시지 추상화 · §7.2 Host와 `:authority` · §7.6.1 Connection(hop-by-hop)
  - §9.2.1 안전 · §9.2.2 멱등과 재시도 · §9.2.3 메서드와 캐시
  - §15.1 상태 코드 개요 · §15.4.2~§15.4.9 리다이렉트 · §15.5.2 401 · §15.5.4 403 · §15.5.6 405 · §15.6.3~§15.6.5 502/503/504
- RFC 5789 PATCH §2 <https://www.rfc-editor.org/rfc/rfc5789>
- RFC 7538 308 Permanent Redirect <https://www.rfc-editor.org/rfc/rfc7538>
- RFC 6585 §4 429 Too Many Requests <https://www.rfc-editor.org/rfc/rfc6585> · RFC 9110 §15.5.9 408(클라이언트는 요청을 다시 보낼 수 있음, MAY)
- RFC 6265bis 초안 §5.6.7.2 "Lax-allowing-unsafe"(최상위 요청 한정, 2분 권장) <https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/>
- RFC 6265 HTTP State Management(쿠키) §4.1.2 속성 · §5.3 저장 모델 · §5.4 Cookie 헤더 <https://www.rfc-editor.org/rfc/rfc6265>
- MDN `Set-Cookie`(SameSite·`__Host-`·Domain 생략) <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie>
- WHATWG Fetch(리다이렉트 20회 상한) <https://fetch.spec.whatwg.org/>
- Node.js `http` 문서(`message.headers` 중복 처리) <https://nodejs.org/api/http.html>
- Java `java.net.http.HttpHeaders` Javadoc(이름 대소문자 무시, 값 리스트) <https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpHeaders.html>
- MDN `Response.ok`·`fetch()`(HTTP 오류 상태에서 reject하지 않음) <https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch>
- nginx `proxy_next_upstream`(`non_idempotent`) <https://nginx.org/en/docs/http/ngx_http_proxy_module.html> · 소스 `src/http/ngx_http_upstream.c`(`ngx_http_upstream_next`의 상태 코드 선택)
- AWS ALB 문제 해결(HTTP 502/503/504 원인) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html>
- Grigorik, 『High Performance Browser Networking』 "Brief History of HTTP" 장 <https://hpbn.co/brief-history-of-http/>
