# security/29-security-symptom-index — 증상 사전: 401 vs 403·CORS 에러·`invalid signature`·`kid not found`·CSRF 403·TLS alert·로그인 폭주·메타데이터 접근 로그 → 원인·확인·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **원리에서 증상으로** 간다.\
"검증자가 미지 `kid`를 다시 가져오지 않으면, 키 회전 직후 캐시 TTL 동안 401이 난다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 증상 한 줄이다. "배포도 안 했는데 401이 쏟아진다", "콘솔에 CORS 에러", "`invalid signature`", "POST만 403", "로그인 요청이 평소의 수십 배", "앱 로그에 `169.254.169.254`".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                  이 노트 (역방향)
  원리·설정 --> 깨지는 조건 --> 보이는 증상              증상 --> 보이는 형태 --> 원인 후보 --> 확인 방법 --> leaf
  "재페치 없는 kid 캐시 + 회전 = TTL 동안 401"          "401 + kid not found. 실패 토큰의 kid가 JWKS에 이미 있나? 회복 시각 = 마지막 페치 + TTL인가?"
```

쉬운 예: 건물 출입구에서 막혔다.\
출입증이 없어서(누구인지 모름), 출입증은 있는데 그 층 권한이 없어서(누구인지는 앎), 출입증이 위조라서, 출입증 발급기가 고장 나서 — 원인이 넷이다.\
경비원이 "안 됩니다"만 말하면 넷을 가를 수 없다. 어느 문에서, 어떤 말로 막혔는지가 단서다.

똑같은 구조다.\
"요청이 막혔다"는 같은 증상에 원인이 여럿이고, 원인마다 고칠 곳이 다르다.
- `401`이면 "누구인지"(인증)에서 막혔다. 토큰·서명·키·시계를 본다.
- `403`이면 "누구인지는 아는데 안 된다"(인가) 또는 CSRF 필터다. 권한·scope·CSRF 토큰을 본다.
- 콘솔에만 에러가 있고 서버 로그는 `200`이면 브라우저가 응답 읽기를 막았다(CORS).

보안 증상은 두 갈래다.

```text
  (가) 정상 요청이 막힌다 — 시끄럽다          (나) 막혀야 할 요청이 통과한다 — 조용하다
      401·403 폭증, CORS 에러, TLS alert           200인데 남의 데이터, 장애 중 200, 위조 토큰 200
      사용자가 바로 신고한다                       에러가 없다. 로그·감사·외부 제보로만 보인다
      1~8절                                       9절
```

- (가)는 가용성 문제로 보인다. 급하게 "보호를 끄는" 처방을 쓰면 (나)를 만든다(장애 시나리오 1~3).
- (나)는 증상이 없다는 것이 증상이다. 지표·로그에 "거부가 0건"인 구간을 찾는다.

  - *역색인*: "leaf → 증상" 목록을 "증상 → leaf" 목록으로 뒤집은 것([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
  - *leaf 표기 `NN 장애 k`*: 이 영역 `NN`번 노트의 「장애 시나리오와 대처」 k번째 시나리오다. 예: `13 장애 1` = [13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md)의 시나리오 1(키 회전 직후 `kid` 캐시 미스 → 401 폭증).
  - *확인 방법*: 고치기 전에 원인 후보를 가르는 가장 싼 확인 한 가지.

## 동작·원리

### 0. 증상은 어느 층이 만든 말인가

```text
  브라우저 ──▶ TLS ──▶ 게이트웨이·WAF ──▶ [CSRF 필터] ──▶ [인증 필터] ──▶ [인가] ──▶ 앱 ──▶ 아웃바운드 요청
     │          │            │                 │               │             │          │           │
  CORS 에러   TLS alert    429·403(WAF)       403             401           403/404    500·200     메타데이터·내부 주소
  (콘솔만)    (핸드셰이크)  (속도 제한·규칙)  (토큰 없음)    (누구인지 모름) (권한 없음)  (조용한 실패) (SSRF 흔적)
     4절        6절         7절               5절          1·2·3절        1절         9절          8절
```

- 같은 `403`이라도 만든 층이 다르다. WAF·CSRF 필터·인가가 모두 `403`을 낸다. 응답 본문·헤더·로그의 **어느 층 로그에 남았나**로 가른다.
- 필터 순서는 프레임워크마다 다르다. Spring Security에서는 `CsrfFilter`가 인가(`AuthorizationFilter`, 기본으로 마지막)보다 앞에서 돈다([20-csrf-and-samesite](../20-csrf-and-samesite/2-summary.md) 장애 2). 그래서 인증된 사용자도 CSRF 토큰이 없으면 `403`이다.
- CORS 에러는 서버가 만든 말이 아니다. 서버는 정상 응답을 보냈고, 브라우저가 스크립트에 응답을 넘기지 않았다([21-same-origin-and-cors](../21-same-origin-and-cors/2-summary.md) 장애 1).

### 0-1. 401·403·404 — 표준이 정한 뜻

| 코드 | 표준의 뜻 | 함께 오는 것 | 다시 시도하면 |
|---|---|---|---|
| `401 Unauthorized` | 유효한 인증 자격 증명이 없다(RFC 9110 §15.5.2) | `WWW-Authenticate` 헤더가 **MUST** | 새 자격 증명으로 다시 시도해도 된다(MAY) |
| `403 Forbidden` | 요청은 이해했지만 거부한다. 자격 증명이 있었다면 그것으로는 부족하다(§15.5.4) | 이유를 본문에 쓸 수 있다 | 같은 자격 증명으로 자동 재시도하지 않는다(SHOULD NOT) |
| `404 Not Found` | 표현을 못 찾았거나, **있는지 밝히고 싶지 않다**(§15.5.5) | — | — |

- RFC 9110 §15.5.4: 금지된 대상의 존재를 숨기려는 서버는 `403` 대신 `404`를 줄 수 있다(MAY). "남의 것 = 403, 없는 것 = 404"를 섞으면 존재가 새어 나간다([15-access-control-models](../15-access-control-models/2-summary.md) 적용 4).
- Bearer 토큰 API(RFC 6750 §3.1)의 `WWW-Authenticate` 오류 코드
  - 토큰이 만료·폐기·형식 오류·기타 무효 → `error="invalid_token"`, `401`(SHOULD).
  - 토큰 권한(scope)이 부족 → `error="insufficient_scope"`, `403`(SHOULD).
  - **인증 정보가 아예 없으면** 오류 코드를 넣지 않는다(SHOULD NOT). 예: `WWW-Authenticate: Bearer realm="example"`. 토큰 없음과 무효 토큰은 같은 `401`이지만 헤더가 다르다.
- `error_description`의 문구는 표준이 정하지 않는다. 라이브러리마다 다르다. 예: Nimbus JOSE+JWT 9.40 `DefaultJWTProcessor`(소스 확인)는 서명 불일치에 `Signed JWT rejected: Invalid signature`, 키를 못 고르면 `Signed JWT rejected: Another algorithm expected, or no matching key(s) found`를 던진다. Spring은 이를 `An error occurred while attempting to decode the Jwt: …` 틀에 담는다([13](../13-jwks-and-key-rotation/2-summary.md) 동작·원리).

#### 실험: 한 서버에서 거부 열 가지를 응답으로 가르기 (`Triage.java`)

JDK `HttpServer`로 작은 자원 서버를 만들었다. HS256 꼴 토큰을 JDK `Mac`(HmacSHA256)으로 직접 만들고 검증한다. 키는 교육용 가짜 값이다. 필터 순서는 CSRF → 인증 → 인가(scope·소유) → 앱이다. `/admin`은 인가 판정 서비스(PDP) 호출을 흉내 내고, 장애를 주입할 수 있다.

```java
// 인증 실패 → 401. 정보 없음과 무효 토큰을 구분한다(RFC 6750 §3.1)
if (r[0].equals("none")) { x.getResponseHeaders().add("WWW-Authenticate", "Bearer realm=\"api\""); send(x, 401, ""); return; }
if (r[0].equals("bad"))  { x.getResponseHeaders().add("WWW-Authenticate",
        "Bearer error=\"invalid_token\", error_description=\"" + r[1] + "\""); send(x, 401, ""); return; }
// 인가 실패 → 403(scope) 또는 404(남의 객체 — 존재를 숨김)
if (!scope.contains("orders.read")) { /* insufficient_scope */ send(x, 403, ""); return; }
if (!owner.equals(sub)) { send(x, 404, "not found"); return; }

// PDP 장애 처리 — 취약 판과 고친 판
try { allow = pdpAllows(sub); }
catch (Exception e) {
    if (FAIL_OPEN) allow = true;                                  // 취약: 판정 불가 = 허가
    else { send(x, 503, "authz unavailable"); return; }            // 고친 판: 판정 불가 = 거부
}
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-07 — 두 번 실행, 같은 출력)

```text
== 취약 판 (PDP 예외 = 허가)
(9) 일반 사용자 /admin                  403  WWW-Authenticate: (없음)  body: forbidden
(10) PDP 장애 중 일반 사용자 /admin        200  WWW-Authenticate: (없음)  body: admin page
== 고친 판 (PDP 예외 = 503)
(1) 토큰 없음                          401  WWW-Authenticate: Bearer realm="api"  body: (빈)
(2) 서명 키가 다름                       401  WWW-Authenticate: Bearer error="invalid_token", error_description="invalid signature"  body: (빈)
(3) 모르는 kid                        401  WWW-Authenticate: Bearer error="invalid_token", error_description="kid not found"  body: (빈)
(4) 만료                             401  WWW-Authenticate: Bearer error="invalid_token", error_description="token expired"  body: (빈)
(5) scope 부족                       403  WWW-Authenticate: Bearer error="insufficient_scope", scope="orders.read"  body: (빈)
(6) 정상·자기 주문                       200  WWW-Authenticate: (없음)  body: order of alice
(7) 정상·남의 주문                       404  WWW-Authenticate: (없음)  body: not found
(8) 쿠키 POST·CSRF 토큰 없음             403  WWW-Authenticate: (없음)  body: csrf token missing
(9) 일반 사용자 /admin                  403  WWW-Authenticate: (없음)  body: forbidden
(10) PDP 장애 중 일반 사용자 /admin        503  WWW-Authenticate: (없음)  body: authz unavailable
```

- 관찰: `401` 네 줄은 코드가 같다. 원인은 `WWW-Authenticate`의 `error`·`error_description`이 가른다. 토큰이 없을 때만 `error`가 없다.
- 관찰: `403` 세 줄((5)·(8)·(9))도 코드가 같다. `insufficient_scope`가 있으면 토큰 scope, 헤더 없이 CSRF 문구면 CSRF 필터, 그 밖이면 인가 규칙이다.
- 관찰: 취약 판은 PDP 장애 중 일반 사용자에게 `/admin`을 `200`으로 열었다. 에러 로그는 없다. 고친 판은 같은 상황에서 `503`이다.
- 해석: 응답 코드만 세는 대시보드는 (2)·(3)·(4)를 한 덩어리로 본다. `error_description`(또는 서버 쪽 사유 로그)을 사유별로 세어야 1~3절의 갈래를 가를 수 있다.
- 한계: 문구(`invalid signature`·`kid not found`·`csrf token missing`)는 이 예제가 고른 것이다. 실제 라이브러리 문구는 위 0-1절처럼 다르다. 외부 응답에 사유를 얼마나 자세히 쓸지는 정보 노출과 진단 편의의 맞바꿈이다(이 예제는 진단용으로 자세히 썼다).

### 1. 401 vs 403 — 어느 층에서 막혔나

```text
  요청이 막혔다
     │
     ├─ 401 + WWW-Authenticate: Bearer realm=…  (error 없음) ───▶ 보통 토큰이 안 실렸다: 클라이언트·프록시가 Authorization을 버림, 쿠키 미전송 (error는 SHOULD라 확정은 아님)
     ├─ 401 + invalid_token ───────────────────────────────────▶ 2절(서명) · 3절(kid) · 만료·시계 · 발급자·aud 불일치
     ├─ 401 폭증, 특정 시각부터 전원 ───────────────────────────▶ 키 회전·JWKS 장애·세션 저장소 장애·enforce 전환
     ├─ 403 + insufficient_scope ──────────────────────────────▶ 토큰 scope 부족 (토큰 발급 요청을 본다)
     ├─ 403, 헤더 없음, POST·PUT·DELETE만 ─────────────────────▶ 5절 CSRF
     ├─ 403, 특정 경로·역할만 ─────────────────────────────────▶ 인가 규칙 (정상 거부일 수 있다)
     └─ 403 대신 200이 와야 할 것이 200 ─────────────────────────▶ 9절 (fail-open·인가 누락)
```

| 보이는 것 (응답·로그) | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| `401`, `WWW-Authenticate`에 `error` 없음 | 보통 요청에 자격 증명이 없다(무효 토큰에 `error`를 넣는 것은 RFC 6750 §3의 SHOULD라 생략하는 서버도 있다 — 헤더로 확인). 프록시가 `Authorization`을 지움, 교차 출처 요청에 쿠키가 안 실림 | 서버에 도착한 요청 헤더를 찍는다. 브라우저면 Network 탭의 요청 헤더 | [21 장애 3](../21-same-origin-and-cors/2-summary.md) · [11 장애 1](../11-sessions-and-cookie-security/2-summary.md) |
| 특정 인스턴스만 `401`, `Jwt expired at …`·`Jwt used before …` | 그 인스턴스 시계가 밀렸다(Spring 기본 여유 60초 초과) | `chronyc tracking` 오프셋, 인스턴스별 401 비율 | [12 장애 3](../12-tokens-and-jwt/2-summary.md) |
| 설정 변경 뒤 모든 로그인이 콜백에서 실패 | `iss` 문자열 불일치(끝 슬래시 등) | discovery 문서의 `issuer`와 설정값을 글자 단위로 비교 | [14 장애 4](../14-oauth2-and-oidc/2-summary.md) |
| 배포 직후 전원 `401`, 세션 저장소 연결 오류 | 세션 저장소 장애·인스턴스 메모리 세션 | 저장소 연결 로그, 같은 세션 ID가 다른 인스턴스로 갔나 | [11 장애 5](../11-sessions-and-cookie-security/2-summary.md) |
| 보안 강제를 켠 직후 특정 호출자(cron·agent)만 `401` | 클라이언트가 서명을 붙이기 전에 서버를 enforce로 올림 | 호출자별 401 분포, audit 모드의 무서명 경고 수 | [26 장애 5](../26-security-logging-and-audit/2-summary.md) |
| 탭 여러 개 쓰는 사용자만 로그아웃, 토큰 엔드포인트 `400 invalid_grant` | refresh 회전 + 재사용 탐지 + 동시 갱신 | 같은 사용자의 `/refresh`가 수백 ms 간격으로 여러 개인가 | [17 장애 1](../17-refresh-token-rotation-and-revocation/2-summary.md) |
| `403` + `insufficient_scope` | 토큰 발급 때 scope를 덜 요청 | 디코드한 토큰의 `scope` | [14](../14-oauth2-and-oidc/2-summary.md) 적용 3 |
| 권한을 회수했는데 계속 `200`, 재시작 뒤 `403` | 판정 캐시·긴 수명 토큰에 든 역할 | 회수 시각과 캐시 TTL·토큰 `exp` | [01 장애 2](../01-security-principles/2-summary.md) · [15 장애 4](../15-access-control-models/2-summary.md) |

- 처방 방향: `401`은 "누구인지"를 증명하는 재료(토큰·키·시계·세션)를 고친다. `403`은 정책(scope·역할·소유·CSRF)을 고친다. `401`을 줄이려고 인증을 끄거나 `403`을 줄이려고 규칙을 넓히는 것은 처방이 아니다.

### 2. `invalid signature` — 무엇의 서명인가

같은 문구가 세 군데서 나온다. 먼저 **무엇을 검증하다 실패했나**를 가른다.

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 웹훅 수신이 일부 이벤트(비ASCII·소수점·특정 필드)만 `401`, 보내는 쪽 재시도 누적 | 원문 바이트가 아니라 파싱 후 재직렬화한 바이트로 HMAC 검증 | 받은 원문 바이트로 다시 계산해 보면 맞는가 | [05 장애 2](../05-mac-and-hmac/2-summary.md) |
| 특정 시각부터 웹훅 `401` 100% | 비밀 회전 시점 어긋남(보내는 쪽 옛 키, 받는 쪽 새 키) | 실패 시작 시각 = 키 교체 배포 시각인가 | [05 장애 3](../05-mac-and-hmac/2-summary.md) |
| JWT `401` + `Signed JWT rejected: Invalid signature`(Nimbus) | 다른 발급자·다른 환경(스테이징 키)의 토큰, 키 교체 후 옛 키로 서명된 토큰 | 토큰 헤더의 `kid`·`alg`, 페이로드 `iss`를 디코드(서명 검증 없이 읽기만) | [12](../12-tokens-and-jwt/2-summary.md) 적용 4 · [13 장애 4](../13-jwks-and-key-rotation/2-summary.md) |
| 키 교체 배포 직후 `AEADBadTagException`·서명 `401`·외부 API 인증 오류 폭증 | 키 버전 없이 회전 — "새 키로 쓰기 + 옛 키로 읽기"를 동시에 못 함 | 실패 데이터·토큰의 키 버전 필드가 있나 | [09 장애 2](../09-randomness-and-key-management/2-summary.md) · [03 장애 4](../03-symmetric-encryption-and-aead/2-summary.md) |
| `openssl dgst -verify` → `Verification failure`, 파일 배포 검증 실패 | 파일 변조, 다른 키의 서명, 전송 중 변환(줄 끝 변환 등) | 파일 digest를 다른 신뢰 경로의 값과 대조 | [06](../06-public-key-and-signatures/2-summary.md) 실험 · [04 장애 3](../04-hash-functions-and-digests/2-summary.md) |

- 반대 방향이 더 위험하다. **서명이 틀렸는데 통과**하는 것은 증상이 없다. 9절 표의 "`alg: none`·HS/RS 혼동 수락", "검증 생략"을 본다.
- 한 출처가 같은 메시지에 태그만 조금씩 바꾼 요청을 대량으로 보내는 `401` 묶음은 타이밍 공격 시도일 수 있다([05 장애 1](../05-mac-and-hmac/2-summary.md)).

### 3. `kid not found` — 키 맵에 그 키가 없다

```text
  401 + kid not found (또는 Nimbus: no matching key(s) found)
     │
     ├─ 실패 토큰의 kid가 발급자 JWKS에 지금 있다 ─────────▶ 검증자 캐시가 낡았다 (회전 직후. 그 JWK의 kty·alg·use가 토큰·검증자 설정과 맞는지도 본다)   13 장애 1
     ├─ 실패 토큰의 kid가 JWKS에 없고, 옛 키다 ─────────────▶ 옛 키를 너무 일찍 뺐다                     13 장애 4
     ├─ JWKS 페치가 타임아웃·503 ─────────────────────────▶ JWKS 엔드포인트 장애 + 캐시 만료             13 장애 2
     └─ 요청마다 다른 무작위 kid, JWKS 페치 수 ≈ 실패 수 ─────▶ 무작위 kid 폭격 (재페치 쿨다운 없음)        13 장애 3
```

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 회전 직후 일부 서비스만 `401`, 몇 분~몇십 분 뒤 저절로 회복 | 미지 `kid` 재페치 없음(시작 때 한 번 로드) | 회복 시각 = 회전 전 마지막 페치 시각 + 그 서비스의 캐시 TTL인가(늦어도 회전 시각 + TTL). 13의 실험 A: t=0 페치, t=100 회전, 재페치 없으면 첫 200이 t=600(= 0 + 600) | [13 장애 1](../13-jwks-and-key-rotation/2-summary.md) |
| 발급자 장애 몇 분 뒤 전 API `401` | JWKS를 못 가져와 캐시가 비었다(fail-closed — 의도된 동작) | 401 시작 시각 = 마지막 성공 페치 + TTL인가(13 실험 C) | [13 장애 2](../13-jwks-and-key-rotation/2-summary.md) |
| 매 요청 다른 `kid`, JWKS 호출 폭증, 발급자가 우리를 `429` | 재페치 쿨다운 없음 | JWKS 페치 수와 실패 수의 비(13 실험 B: 쿨다운 0초면 1,000건 → 1,000회) | [13 장애 3](../13-jwks-and-key-rotation/2-summary.md) |
| 오래 켜 둔 앱·배치만 `401`, 실패 토큰의 `iat`가 옛 키 제거 이전 | 은퇴 대기 < 토큰 최대 수명 + 시계 여유(13: 캐시 TTL을 더하면 보수적 여유) | 옛 `kid` 서명 토큰 검증 수 지표 | [13 장애 4](../13-jwks-and-key-rotation/2-summary.md) |

- 문구는 라이브러리마다 다르다(0-1절). 로그 검색은 `kid` 값과 "key"·"kid" 단어를 함께 쓴다.
- JWKS 장애가 꼭 `401`로 보이는 것은 아니다. Spring Security 6.5.5 소스 기준으로, JWKS를 가져오다 실패하면(`RemoteKeySourceException`) `NimbusJwtDecoder`가 `BadJwtException`이 아닌 `JwtException`을 던지고, `JwtAuthenticationProvider`가 이를 `AuthenticationServiceException`으로 바꾼다. `BearerTokenAuthenticationFilter`의 기본 실패 처리기(`AuthenticationEntryPointFailureHandler`, `rethrowAuthenticationServiceException` 기본 true)는 이 예외를 401 진입점으로 보내지 않고 다시 던진다. 필터 밖으로 나간 예외를 오류 페이지 장치가 처리하지 않으면 서블릿 컨테이너는 `500`을 보내야 한다(Jakarta Servlet 명세 "Error Pages" 절). 그래서 응답이 `500`으로 보일 수 있다. 앱이 오류 페이지·예외 처리를 따로 두면 다른 코드가 될 수 있다(소스·명세로 확인, 실행으로는 확인 안 함). "JWKS 장애인데 401이 아니라 500"이면 이 경로를 의심한다.

### 4. CORS 에러 — 서버는 무엇을 받았나

```text
  콘솔: "... has been blocked by CORS policy: ..."   (스크립트가 받는 것은 TypeError: Failed to fetch 한 줄)
     │
     ├─ "No 'Access-Control-Allow-Origin' header is present" + 서버 로그 200 ──▶ 응답에 ACAO 없음. 요청은 이미 처리됐다      21 장애 1
     ├─ "Response to preflight request doesn't pass ... HTTP ok status" ───────▶ OPTIONS가 405·404·401                    21 장애 2
     ├─ credentials 요청 + ACAO: * 거부, 또는 쿠키가 안 실림 ─────────────────▶ 정확한 출처 + ACAC (+ 교차 사이트면 SameSite=None; Secure)    21 장애 3
     └─ (에러가 없어서 문제) 쿠키가 실리는 출처는 어디든 인증된 응답을 읽는다 ─────────────────▶ Origin 반사 + ACAC: true                     21 장애 4
```

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 콘솔 `No 'Access-Control-Allow-Origin' header is present`, 서버 로그 `200` | 서버가 CORS 헤더를 안 붙임. 단순 요청이라 서버는 처리했다 | 같은 요청을 `curl -i -H 'Origin: …'`으로 보내 응답 헤더 확인. 상태 변경이었다면 중복 처리 확인 | [21 장애 1](../21-same-origin-and-cors/2-summary.md) · [web-platform/23](../../web-platform/23-web-symptom-index/2-summary.md) |
| Network 탭 `OPTIONS` `405`/`404`, 본 요청은 안 나감 | 프레임워크가 `OPTIONS`를 처리 못 함, 보안 필터가 preflight를 막음(인증 요구 → 401) | `curl -i -X OPTIONS -H 'Origin: …' -H 'Access-Control-Request-Method: PUT'` | [21 장애 2](../21-same-origin-and-cors/2-summary.md) |
| 로그인했는데 교차 출처 API가 비인증 처리 | `credentials: 'include'` 누락, 서버 `ACAO: *`, 쿠키 `SameSite` | 요청 헤더에 `Cookie`가 있나, 응답에 `Access-Control-Allow-Credentials: true`·정확한 출처가 있나 | [21 장애 3](../21-same-origin-and-cors/2-summary.md) · [11](../11-sessions-and-cookie-security/2-summary.md) |

- CORS 에러를 없애려고 "요청 `Origin`을 그대로 반사"하면 증상은 사라지고 [21 장애 4](../21-same-origin-and-cors/2-summary.md)가 생긴다(아래 장애 시나리오 2).
- 단순 요청에서 CORS는 응답 **읽기**만 막는다(preflight가 실패하면 본 요청을 아예 안 보낸다). CSRF를 막지 않는다([21 장애 5](../21-same-origin-and-cors/2-summary.md)).

### 5. CSRF 403 — 상태 변경 요청만 막힌다

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| GET은 되는데 POST·PUT·DELETE만 `403`, `WWW-Authenticate` 없음 | 요청에 CSRF 토큰(Spring 기본 헤더 `X-CSRF-TOKEN`, 파라미터 `_csrf`)이 없다 | 요청에 토큰이 실렸나. Spring이면 `AccessDeniedException`(CSRF 계열) 로그 | [20](../20-csrf-and-samesite/2-summary.md) 적용 1 |
| SPA에서만 `403`, 서버 렌더링 폼은 정상 | 토큰을 쿠키로 받아 헤더로 다시 보내는 구성이 빠짐 | 응답에 토큰 쿠키가 있나, JS가 그 값을 헤더로 보내나 | [20](../20-csrf-and-samesite/2-summary.md) 적용 1 |
| 외부 IdP에서 돌아오는 POST 콜백이 "세션 없음"·로그인 루프 | 세션 쿠키 `SameSite=Lax`/`Strict`라 교차 사이트 POST에 안 실림 | DevTools 쿠키 탭의 "SameSite 때문에 차단" 표시 | [20 장애 3](../20-csrf-and-samesite/2-summary.md) · [11 장애 1](../11-sessions-and-cookie-security/2-summary.md) |
| (반대) 토큰 없는 요청이 `200` | 그 경로가 CSRF 보호 밖(제외 매처, GET 상태 변경) | 상태 변경 경로를 전수 점검 | [20 장애 2](../20-csrf-and-samesite/2-summary.md) · [20 장애 1](../20-csrf-and-samesite/2-summary.md) |

- 위 실험 (8)처럼 CSRF `403`은 인증 전에 날 수 있다. "로그인했는데 왜 403?"의 첫 후보다.
- 처방이 "CSRF 끄기"가 되는 조건은 하나다. 세션 쿠키·HTTP Basic처럼 브라우저가 자동으로 싣는 자격 증명을 쓰지 않고, 스크립트가 붙이는 `Authorization: Bearer`로만 인증할 때다([20](../20-csrf-and-samesite/2-summary.md) 적용 2).

### 6. TLS alert — 정본은 network

TLS alert와 인증서 오류의 표는 [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md) 6절이 정본이다. 여기서는 보안 영역 leaf와 이어지는 것만 둔다.

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| `Received fatal alert: handshake_failure`·`protocol_version` | 공통 버전·암호군 없음 | `openssl s_client -tls1_2`/`-tls1_3` | [network/29](../../network/29-tls-handshake/2-summary.md) |
| `PKIX path building failed`·`unable to get local issuer certificate` | 중간 인증서 누락·사설 CA 미등록 | `openssl s_client -showcerts` | [network/30](../../network/30-x509-and-chain-validation/2-summary.md) |
| `certificate has expired`, 또는 탐지 장비만 조용히 멈춤 | 인증서 갱신 누락 | `openssl x509 -noout -dates` | [network/30](../../network/30-x509-and-chain-validation/2-summary.md) · [network/32](../../network/32-mtls-and-cert-operations/2-summary.md) · [30](../30-security-incidents/2-summary.md) 사건 2 |
| 최신 JDK·FIPS 모드 클라이언트만 실패, `Algorithm constraints check failed` | RSA-1024·SHA-1 서명 같은 낡은 조합을 런타임 정책이 거부 | 인증서 서명 알고리즘·키 크기, JDK `jdk.certpath.disabledAlgorithms` | [06 장애 4](../06-public-key-and-signatures/2-summary.md) |
| 협상 결과가 `TLS_RSA_WITH_…`, `s_client`에 `Server Temp Key` 줄 없음 | 정적 RSA 키 교환 — 개인키 유출 시 과거 트래픽 복호 | `openssl s_client`의 협상 결과 | [07 장애 1](../07-key-exchange-forward-secrecy/2-summary.md) |
| mTLS에서 `certificate_required`(116) | 클라이언트 인증서 미제시 | `openssl s_client -cert … -key …` | [network/32](../../network/32-mtls-and-cert-operations/2-summary.md) |

- alert는 **누가** 보냈는지부터 본다. 서버가 보냈으면 내 제안을 거절한 것이고, 클라이언트가 보냈으면 서버 응답(대개 인증서)을 거절한 것이다(network/52 6절).
- 인증서 검증 실패를 "전부 신뢰" `TrustManager`로 없애면 증상은 사라지고 중간자가 열린다([07 장애 4](../07-key-exchange-forward-secrecy/2-summary.md)).

### 7. 로그인 폭주 — 누가, 어떻게 흩어져 오나

```text
  로그인 요청이 평소의 수십 배
     │
     ├─ 실패(401) 비율 급등, 수천 IP에 흩어져 IP당 몇 건, 소수 성공 ───▶ 크리덴셜 스터핑                         10 장애 1
     ├─ 한 계정에 MFA 푸시 수십 건, 마지막 하나 승인 ─────────────────▶ MFA 푸시 피로                           10 장애 2
     ├─ 없는 계정 응답이 유난히 빠르거나 메시지가 다름 ─────────────────▶ 계정 열거                               10 장애 3
     ├─ 로그인 API만 느리고 CPU 포화, OOMKilled ──────────────────────▶ 비싼 KDF × 동시 요청 (공격이 아닐 수도)    08 장애 3 · 28 장애 3
     └─ 429 급증 직후 요청량이 더 늘어남 ─────────────────────────────▶ 백오프 없는 재시도 (방어의 역풍)            28 장애 5
```

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 로그인 `401` 비율 급등, 실패가 수천 IP에 분산 | 다른 사이트에서 유출된 비밀번호 재사용 | 실패 요청의 계정 분포(다양한 계정 × 적은 시도) vs 한 계정 집중(무차별 대입) | [10 장애 1](../10-authentication-basics/2-summary.md) |
| 없는 계정은 `404`·"존재하지 않는 계정", 있는 계정은 `401` — 또는 시간 차 | 조회 실패에서 일찍 반환, 해시 비교 생략 | 두 계정 유형의 응답 코드·문구·시간 비교(10의 실험: 취약 판 0.0 ms vs 약 90 ms) | [10 장애 3](../10-authentication-basics/2-summary.md) |
| 같은 계정의 푸시 승인 요청 급증 | 비밀번호는 이미 유출 | 인증 로그의 푸시 요청 수·승인 위치 vs 로그인 IP | [10 장애 2](../10-authentication-basics/2-summary.md) |
| 로그인 p99 수 초, CPU 포화, `OOMKilled` | KDF 비용 × 동시 로그인 수 | 동시 로그인 수 × 해시 메모리 계산 | [08 장애 3](../08-password-storage-and-kdf/2-summary.md) |
| 유출 사고 뒤 다른 서비스에서 같은 비밀번호로 로그인 시도 | 빠른 해시로 저장된 비밀번호가 복원됨 | `password` 컬럼이 64자 16진수 하나, 같은 값 반복 | [08 장애 1](../08-password-storage-and-kdf/2-summary.md) · [04 장애 4](../04-hash-functions-and-digests/2-summary.md) |

- IP당 한도만으로는 분산된 스터핑을 못 막는다. 계정 단위 + 전역 실패율을 함께 본다([10 장애 1](../10-authentication-basics/2-summary.md), 제한 알고리즘은 [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)).

### 8. 메타데이터 접근 로그 — 서버가 대신 요청했다

| 보이는 것 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 앱·프록시 로그의 아웃바운드 목적지에 `169.254.169.254`, CloudTrail에 그 역할의 평소와 다른 호출 | 사용자 URL을 가져오는 기능(SSRF) + 토큰 없는 메타데이터(IMDSv1) | 해당 요청의 입력 URL, 인스턴스의 IMDSv2 필수 여부, 역할 자격 증명이 쓰인 출처 IP | [22 장애 1](../22-ssrf/2-summary.md) · [02 장애 2](../02-threat-modeling/2-summary.md) |
| 허용 도메인 이름이 든 URL이 내부로 감 | 문자열 포함·접두 일치 검사 | URL을 파싱한 **호스트 전체**가 허용 집합에 있나 | [22 장애 2](../22-ssrf/2-summary.md) |
| 검사는 통과, 가끔 내부 주소로 연결 | DNS rebinding(검사 후 재해석) | 같은 이름의 해석 기록, 짧은 TTL | [22 장애 3](../22-ssrf/2-summary.md) |
| 허용 URL의 `302 Location`이 내부 주소 | 리다이렉트 자동 추적 | HTTP 클라이언트의 리다이렉트 기본값 | [22 장애 4](../22-ssrf/2-summary.md) |
| `0x7f.0.0.1`·`2130706433`·`[::1]` 같은 표기의 목적지 | deny 목록·정규식 검사 | 파싱 후 정규화한 주소로 대역 판정하나 | [22 장애 5](../22-ssrf/2-summary.md) |
| 서버발 내부망 요청 + 요청 본문에 `<!DOCTYPE … SYSTEM` | XXE | 해당 XML 진입점의 DTD 허용 여부 | [23 장애 3](../23-deserialization-and-parser-attacks/2-summary.md) |
| 외부 요청 직후 앱 서버발 LDAP(389)·DNS 연결 | 로그 문자열 lookup(Log4Shell) | 접근 로그 필드의 `${jndi:` 문자열, log4j-core 판 | [23 장애 1](../23-deserialization-and-parser-attacks/2-summary.md) |

- 메타데이터 접근은 **흔적이 남은 뒤가 시작**이다. 역할 자격 증명이 나갔다고 보고 회전부터 한다([09](../09-randomness-and-key-management/2-summary.md) 적용 4). 사건 하나는 [30](../30-security-incidents/2-summary.md) 사건 3(Capital One).

### 9. 에러가 없는 증상 — 막혀야 할 것이 통과한다

| 보이는 것 (대개 사후 조사·감사·제보로) | 원인 | 확인 방법 | leaf |
|---|---|---|---|
| 장애 시간대에 평소 `403`이던 요청이 `200`, 거부 로그 0건 | 판정 불가를 허가로 처리(fail-open) | 의존 서비스 오류 로그와 같은 시각의 거부 수(위 실험 (10): 취약 판 `200`) | [01 장애 1](../01-security-principles/2-summary.md) · [15 장애 3](../15-access-control-models/2-summary.md) · [10 장애 5](../10-authentication-basics/2-summary.md) |
| 한 세션이 `/orders/1001`, `/1002`, …를 연속 호출해 전부 `200` | 객체 수준 인가 누락(IDOR/BOLA) | 응답 객체의 소유자 ≠ 요청자 | [15 장애 1](../15-access-control-models/2-summary.md) · [16 장애 1](../16-identifiers-and-enumeration/2-summary.md) |
| `role=USER` 주체의 관리 API `200` | 기능 수준 인가 누락, 신원 헤더를 믿음 | 경로 규칙의 기본값, 게이트웨이가 클라이언트 신원 헤더를 지우나 | [15 장애 2](../15-access-control-models/2-summary.md) · [02 장애 1](../02-threat-modeling/2-summary.md) |
| 발급 기록 없는 `sub=admin` 요청, 헤더 `alg`가 평소와 다름 | `alg: none`·HS/RS 혼동 수락 | 거부 회귀 테스트(위조 토큰) | [12 장애 1](../12-tokens-and-jwt/2-summary.md) · [06 장애 2](../06-public-key-and-signatures/2-summary.md) |
| `exp`가 과거인 토큰, 다른 서비스용 `aud` 토큰이 `200` | 시각·`aud` 미검증 | 디코더에 claim 검증기가 설정됐나 | [12 장애 2·5](../12-tokens-and-jwt/2-summary.md) |
| 비밀번호 변경 뒤에도 같은 토큰 패밀리의 갱신 성공 | 폐기 경로 없음 | 변경 시각 이후의 갱신 로그 | [17 장애 2](../17-refresh-token-rotation-and-revocation/2-summary.md) · [12 장애 4](../12-tokens-and-jwt/2-summary.md) |
| 응답이 요청 payload보다 크고, 요청과 무관한 데이터가 섞임. 로그는 정상 | 길이 필드를 믿은 경계 밖 읽기(Heartbleed형) | ASan 빌드에서 `heap-buffer-overflow READ` | [24 장애 1](../24-memory-safety-exploits/2-summary.md) |
| 저장 데이터의 nonce 필드에 중복 | GCM nonce 재사용 | 키별 nonce 중복 검사 배치 | [03 장애 2](../03-symmetric-encryption-and-aead/2-summary.md) |
| 로그 저장소·에러 트래커에서 토큰·카드번호·이메일 발견 | 바디 통째 로깅, 예외 메시지에 PII | 로그에 토큰·카드 패턴 `grep` | [26 장애 2](../26-security-logging-and-audit/2-summary.md) · [27 장애 1·2](../27-pii-classification-masking-retention/2-summary.md) |
| 침해 조사에 필요한 기록이 없다 | 감사 사건을 앱 로그에만, 보존 기한 경과 | 감사 사건 목록과 보존 기한 | [26 장애 1·4](../26-security-logging-and-audit/2-summary.md) |
| 공식 버전·패치가 있었는데 그 경로로 침해 | 미패치 구성 요소·자산 목록 공백 | SBOM으로 그 구성 요소가 어디 있나 | [25 장애 1](../25-supply-chain-security/2-summary.md) |

- 이 표의 증상은 대시보드의 에러율에 나타나지 않는다. **거부 수가 0으로 떨어진 구간**, **검증 실패 수 지표가 아예 없는 경로**를 찾는 것이 탐지 방법이다([06 장애 1](../06-public-key-and-signatures/2-summary.md): 검증 실패 횟수를 지표로 남긴다).

## 쓰이는 자료구조·알고리즘

- **역색인** — 이 노트 자체. leaf의 「장애 시나리오」를 증상 문자열로 뒤집었다([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
- **결정 트리** — 1·3·4·7절의 그림. 가장 싼 관찰(응답 코드 → 헤더 → 로그 문구 → 시각)부터 물어 후보를 반씩 줄인다.
- **TTL 캐시(`kid` → 키 맵)** — `kid not found`의 회복 시각과 JWKS 장애 때 401 시작 시각이 둘 다 "마지막 페치 + TTL"인 이유([13](../13-jwks-and-key-rotation/2-summary.md)).
- **출처 튜플 비교** — CORS·CSRF Origin 검사는 (스킴, 호스트, 포트)의 완전 일치다. 접두 일치가 장애를 만든다([21](../21-same-origin-and-cors/2-summary.md) · [20 장애 5](../20-csrf-and-samesite/2-summary.md)).
- **CIDR 대역 판정** — 메타데이터·사설 주소를 파싱 후 정규화한 주소로 판정한다([22](../22-ssrf/2-summary.md) · [network/07-ip-addressing-cidr](../../network/07-ip-addressing-cidr/2-summary.md)).
- **토큰 버킷** — 로그인 폭주와 비싼 엔드포인트의 남용 제한([28](../28-dos-and-abuse/2-summary.md) · [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)).
- **해시 체인** — 감사 로그가 지워졌는지 확인할 수 있게 한다([26](../26-security-logging-and-audit/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 원문을 잃지 않게 기록한다

증상 사전은 원문이 있어야 쓸 수 있다. "401이 났다"가 아니라 아래 다섯 가지를 함께 남긴다.

```text
  ① 상태 코드 + WWW-Authenticate 헤더 원문 (401·403의 사유)
  ② 거부한 층의 로그 원문 (필터 이름·예외 클래스·error_description)
  ③ 브라우저면 콘솔 원문 (스크립트 예외에는 사유가 빠진다 — 4절)
  ④ 시각: 첫 실패, 회복, 그 사이의 배포·키 회전·인증서 갱신
  ⑤ 범위: 전원인가, 특정 인스턴스·클라이언트·경로·사용자 유형인가
```

진단 명령(로컬·자기 서비스에만).

```bash
# ① 응답 코드와 도전 헤더를 함께 본다
curl -s -o /dev/null -D - -H "Authorization: Bearer $TOKEN" https://api.example.test/orders/1001 | grep -iE '^(HTTP|www-authenticate)'

# 토큰 헤더의 kid·alg를 읽는다 (서명 검증 아님 — 읽기만. 실제 토큰을 공유 채널에 붙이지 않는다)
cut -d. -f1 <<<"$TOKEN" | tr '_-' '/+' | base64 -d 2>/dev/null; echo

# preflight를 손으로 보낸다
curl -s -o /dev/null -D - -X OPTIONS -H 'Origin: https://app.example.test' \
     -H 'Access-Control-Request-Method: PUT' https://api.example.test/orders/1001
```

- `base64 -d`는 패딩이 없으면 끝부분에서 오류를 낼 수 있다. 앞부분 JSON이 읽히면 충분하다.

### 2. 거부 사유를 숫자로 남긴다 — 취약 예 → 고친 예

응답 코드만 세면 1~3절의 갈래가 한 덩어리가 된다. 서버 쪽에서 사유별 카운터를 남긴다.

```java
// 취약: 모든 인증 실패를 한 줄로 삼키고, 판정 불가를 허가로
try {
    decoder.decode(token);
} catch (Exception e) {
    log.warn("auth failed");          // 사유 없음 → kid·서명·만료·시계를 구분 못 함
}
try { return pdp.allows(user, resource); } catch (Exception e) { return true; }   // fail-open (9절)
```

```java
// 고친 예: 사유를 분류해 세고, 판정 불가는 거부
try {
    decoder.decode(token);
} catch (JwtValidationException e) {          // 만료·nbf·iss·aud 등 claim 검증 실패 (Spring Security)
    meter.counter("auth.reject", "reason", "claims").increment();
    throw e;
} catch (BadJwtException e) {                 // 서명·키 선택·형식 실패
    String m = String.valueOf(e.getMessage());
    String reason = m.contains("no matching key") ? "kid" : m.contains("Invalid signature") ? "signature" : "malformed";
    meter.counter("auth.reject", "reason", reason).increment();
    throw e;
}
try { return pdp.allows(user, resource); }
catch (Exception e) {
    meter.counter("authz.unavailable").increment();
    throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "authz unavailable", e);   // fail-closed
}
```

- `JwtValidationException`은 `BadJwtException`의 하위 클래스다(Spring Security `org.springframework.security.oauth2.jwt`). 그래서 catch 순서를 하위 클래스부터 둔다.
- JWKS 페치 실패는 `BadJwtException`이 아닌 `JwtException`이라 위 두 catch에 걸리지 않는다(3절). 그 사유도 세려면 `JwtException` catch를 하나 더 둔다.
- 메시지 문자열로 분류하는 것은 라이브러리 판이 바뀌면 깨진다. 판을 올릴 때 이 분류 테스트를 같이 돌린다(문구 예는 0-1절의 Nimbus 9.40).
- `meter`는 Micrometer `MeterRegistry` 같은 지표 수집기다. 사유 태그는 고정된 몇 값으로만 둔다(토큰·사용자 ID를 태그로 넣지 않는다 — 카디널리티와 PII, [27](../27-pii-classification-masking-retention/2-summary.md)).

### 3. 시각을 겹쳐 본다

```text
  401 시작 ── 배포? 키 회전? 인증서 갱신? JWKS 장애? enforce 전환? 시계 동기화 중단?
  401 회복 ── 저절로 회복했다면 그 간격이 어떤 TTL과 같은가 (13 실험 A: 페치 t=0 + TTL 600초 = 회복 t=600. 회전은 t=100)
  거부 0건 ── 의존 서비스 오류 구간과 겹치나 (9절 fail-open)
```

- 같은 시각에 바뀐 것이 없으면 공격(스터핑·무작위 `kid` 폭격)을 의심한다. 바뀐 것이 있으면 그 변경부터 되돌려 본다.

### 4. leaf로 간다

- 표의 leaf 칸으로 가서 그 시나리오의 **대처**를 읽는다. 이 노트는 분류까지만 한다.
- 처방이 "검증 끄기·규칙 넓히기·전부 허용"이면 멈춘다. 9절의 조용한 증상을 새로 만드는 처방이다.

## 장애 시나리오와 대처

색인을 잘못 읽어 생기는 사고다.

### 1. 401 폭증을 "공격"으로 읽고 차단한다 — 실제는 키 회전

- **현상**: 401이 갑자기 늘어 보안팀이 상위 출처 IP를 차단했는데, 차단된 것은 정상 사용자였다.
- **보이는 형태**: 401 사유가 전부 `kid not found`(또는 `no matching key(s) found`). 실패 토큰의 `kid`가 발급자 JWKS에 이미 있다. 출처 IP는 평소 사용자 분포와 같다.
- **원인**: 응답 코드만 보고 사유를 보지 않았다. 401 폭증은 [13 장애 1](../13-jwks-and-key-rotation/2-summary.md)·[11 장애 5](../11-sessions-and-cookie-security/2-summary.md)·[26 장애 5](../26-security-logging-and-audit/2-summary.md)처럼 운영 변경에서 더 자주 나온다.
- **대처**: 사유별 카운터(적용 2)를 먼저 본다. 실패 계정·IP 분포가 평소와 같으면 운영 변경을 의심한다. 차단은 사유가 공격 모양(무작위 `kid`, 분산 IP × 다양한 계정)일 때 건다.

### 2. CORS 에러를 "Origin 반사"로 없앤다 ⚠

- **현상**: 프런트 팀의 CORS 에러가 하루 만에 "해결"됐다. 몇 달 뒤 침투 테스트에서 다른 사이트가 인증된 응답을 읽는다는 보고가 온다(쿠키가 실리는 출처라면 어디든 — `SameSite=None` 쿠키면 아무 사이트나).
- **보이는 형태**: 응답 `Access-Control-Allow-Origin`이 요청 `Origin`을 그대로 되돌리고 `Access-Control-Allow-Credentials: true`.
- **원인**: 증상(콘솔 에러)을 없애는 것을 목표로 삼았다. CORS 에러는 서버 설정을 **정확히** 하라는 신호였다.
- **대처**: 허용 출처 집합과 완전 일치로 비교한다. 공개(비인증) API만 `*`. 상세는 [21 장애 4](../21-same-origin-and-cors/2-summary.md).

### 3. CSRF 403을 "CSRF 끄기"로 없앤다 ⚠

- **현상**: SPA 전환 뒤 POST가 전부 `403`이라 `csrf.disable()`을 넣었다. 이후 교차 사이트 폼으로 상태 변경이 일어난다.
- **보이는 형태**: 세션 쿠키 인증을 그대로 쓰는데 CSRF 필터가 없다. 서버 로그에 외부 `Origin`의 상태 변경 `200`.
- **원인**: "REST API는 CSRF가 필요 없다"를 쿠키 세션에도 적용했다. 그 말은 스크립트가 붙이는 `Authorization: Bearer` 인증에만 맞다(HTTP Basic은 브라우저가 기억했다가 자동으로 붙인다).
- **대처**: 토큰을 쿠키로 내려 헤더로 다시 보내는 SPA 구성을 쓴다. 상세는 [20](../20-csrf-and-samesite/2-summary.md) 적용 1·2.

### 4. 로그인 폭주를 IP 차단으로만 막는다

- **현상**: IP당 한도를 낮췄는데 실패율은 그대로이고, 며칠 뒤 계정 탈취 문의가 온다.
- **보이는 형태**: 실패 요청이 수천 IP에 흩어져 IP당 몇 건뿐이다. 한도에 걸리는 IP가 거의 없다.
- **원인**: 크리덴셜 스터핑은 분산된다. 출처 하나 기준의 탐지·제한은 통하지 않는다([16 장애 1](../16-identifiers-and-enumeration/2-summary.md)도 같은 교훈).
- **대처**: 계정 단위 제한 + 전역 실패율 + 봇 탐지 과제 + MFA. 이미 성공한 낯선 세션을 끊는다([10 장애 1](../10-authentication-basics/2-summary.md)).

### 5. "에러가 없다"를 "안전하다"로 읽는다 ⚠

- **현상**: 인가 서비스 장애 회고에서 "사용자 영향 없음"으로 정리했다. 감사에서 그 시간대에 권한 없는 관리 기능 호출이 발견된다.
- **보이는 형태**: 장애 시간대 에러율은 평소와 같다. 거부(`403`) 수가 0으로 떨어졌다. 위 실험 (10)의 취약 판처럼 `200`.
- **원인**: 판정 불가를 허가로 처리했다. 에러율 대시보드는 이것을 "정상"으로 그린다.
- **대처**: 거부 수·검증 실패 수를 지표로 두고 "0으로 떨어짐"에 알람을 건다. 판정 불가는 거부(503)로([01 장애 1](../01-security-principles/2-summary.md), 적용 2).

## 핵심 문장

- `401`은 "누구인지 모른다", `403`은 "누구인지 알지만 안 된다"다. 원인은 코드가 아니라 `WWW-Authenticate`의 `error`·`error_description`과 거부한 층의 로그가 가른다(실험: `401` 네 줄, `403` 세 줄이 각각 코드가 같았다).
- `kid not found`는 시각으로 가른다. 회복(회전 직후 캐시 미스)이나 시작(JWKS 장애)이 "마지막 페치 + 캐시 TTL"에 맞으면 캐시 문제다.
- CORS 에러는 브라우저가 응답 읽기를 막은 것이다. 서버 로그가 `200`이면 요청은 이미 처리됐다.
- CSRF `403`은 인증 전에 날 수 있다. "로그인했는데 POST만 403"의 첫 후보다.
- 정상 요청이 막히는 증상은 시끄럽고, 막혀야 할 요청이 통과하는 증상은 조용하다. 시끄러운 증상을 "보호 끄기"로 없애면 조용한 증상이 생긴다.

## 관련 주제·근거

- 이 영역 leaf(색인 대상): [01](../01-security-principles/2-summary.md) · [02](../02-threat-modeling/2-summary.md) · [03](../03-symmetric-encryption-and-aead/2-summary.md) · [04](../04-hash-functions-and-digests/2-summary.md) · [05](../05-mac-and-hmac/2-summary.md) · [06](../06-public-key-and-signatures/2-summary.md) · [07](../07-key-exchange-forward-secrecy/2-summary.md) · [08](../08-password-storage-and-kdf/2-summary.md) · [09](../09-randomness-and-key-management/2-summary.md) · [10](../10-authentication-basics/2-summary.md) · [11](../11-sessions-and-cookie-security/2-summary.md) · [12](../12-tokens-and-jwt/2-summary.md) · [13](../13-jwks-and-key-rotation/2-summary.md) · [14](../14-oauth2-and-oidc/2-summary.md) · [15](../15-access-control-models/2-summary.md) · [16](../16-identifiers-and-enumeration/2-summary.md) · [17](../17-refresh-token-rotation-and-revocation/2-summary.md) · [18](../18-injection/2-summary.md) · [19](../19-xss-and-csp/2-summary.md) · [20](../20-csrf-and-samesite/2-summary.md) · [21](../21-same-origin-and-cors/2-summary.md) · [22](../22-ssrf/2-summary.md) · [23](../23-deserialization-and-parser-attacks/2-summary.md) · [24](../24-memory-safety-exploits/2-summary.md) · [25](../25-supply-chain-security/2-summary.md) · [26](../26-security-logging-and-audit/2-summary.md) · [27](../27-pii-classification-masking-retention/2-summary.md) · [28](../28-dos-and-abuse/2-summary.md)
- 후속: [30-security-incidents](../30-security-incidents/2-summary.md) — 이 색인의 증상이 실제 사고에서 어떻게 보였나
- 다른 영역 색인: [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md)(TLS alert 정본) · [web-platform/23-web-symptom-index](../../web-platform/23-web-symptom-index/2-summary.md)(CORS 콘솔) · [api-design/28-api-symptom-index](../../api-design/28-api-symptom-index/2-summary.md) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)
- 상태 코드 선택: [api-design/03-status-codes-for-apis](../../api-design/03-status-codes-for-apis/2-summary.md)
- 후속(AI 엔지니어링): [ai-engineering/25-ai-symptom-index](../../ai-engineering/25-ai-symptom-index/2-summary.md) — LLM 증상 색인(모델이 문서 속 지시를 따름 등)
- 1차 출처
  - RFC 9110 HTTP Semantics §15.5.2(401 — `WWW-Authenticate` MUST)·§15.5.4(403, 존재를 숨기려면 404 MAY)·§15.5.5(404) <https://www.rfc-editor.org/rfc/rfc9110>
  - RFC 6750 Bearer Token Usage §3.1 — `invalid_token`(401 SHOULD)·`insufficient_scope`(403 SHOULD)·인증 정보가 없으면 오류 코드 넣지 않음(SHOULD NOT) <https://www.rfc-editor.org/rfc/rfc6750>
  - Nimbus JOSE+JWT 9.40 소스 `com/nimbusds/jwt/proc/DefaultJWTProcessor.java`(Maven Central sources jar, 2026-10-07 확인) — `Signed JWT rejected: Invalid signature`, `Signed JWT rejected: Another algorithm expected, or no matching key(s) found`
  - Spring Security 6.5.5 소스(GitHub 태그 `6.5.5`) — `NimbusJwtDecoder`(`RemoteKeySourceException` → `JwtException`), `JwtAuthenticationProvider`(`JwtException` → `AuthenticationServiceException`), `AuthenticationEntryPointFailureHandler`(`rethrowAuthenticationServiceException` 기본 true), `BearerTokenAuthenticationFilter` <https://github.com/spring-projects/spring-security/tree/6.5.5>
  - Jakarta Servlet 명세 "Error Pages" — "If a servlet generates an error that is not handled by the error page mechanism …, the container must ensure to send a response with status 500." <https://github.com/jakartaee/servlet>
  - RFC 8446 §6(TLS alert) — 표는 network/52
- 실험
  - `Triage.java` — 토큰 없음·서명 불일치·모르는 `kid`·만료·scope 부족·남의 객체·CSRF 토큰 없음·인가 거부·PDP 장애(fail-open vs fail-closed) 열 가지를 응답 코드·`WWW-Authenticate`로 구분. 코드 `scratchpad/sec/syn/Triage.java`, 명령 `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <dir>:/w -w /w eclipse-temurin:21-jdk java Triage.java`(OpenJDK 21.0.12). 결정적 출력, 두 번 실행.
  - 표 안의 수치(13 실험 A·B·C, 10의 열거 시간, 21의 콘솔 문구, 22의 가드 판정)는 각 leaf의 실험에서 옮겼다(새로 돌리지 않음).
