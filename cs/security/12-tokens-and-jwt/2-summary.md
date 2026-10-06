# security/12-tokens-and-jwt — 자기 포함 토큰, 서명·만료·폐기 — 정리 (힌트)

## 해결하는 문제

세션(11번)은 서버 저장소를 본다. 서버가 여럿이고 서비스가 여럿이면 모두가 같은 저장소를 봐야 한다.

```text
  세션 방식                                       자기 포함 토큰 방식
  요청 ── sid ──> API 서버 ──조회──> 세션 저장소     요청 ── 토큰 ──> API 서버
                  (모든 서비스가 같은 저장소 필요)                    서명 검증(키만 있으면 됨)
                                                                    → 토큰 안의 sub·exp·scope를 그대로 사용
```

- *자기 포함 토큰(self-contained token)*: 검증에 필요한 정보(누구, 언제까지, 무슨 권한)를 토큰 자체에 담고, 발급자의 서명으로 위조를 막은 토큰.
- *JWT(JSON Web Token)*: 그 대표 형식(RFC 7519). 서명형(JWS Compact)은 점 두 개로 나뉜 `header.payload.signature`다. 암호화형(JWE Compact)은 다섯 부분이고 내용이 가려진다. 이 노트는 흔히 쓰는 서명형을 다룬다.
- 대가가 있다. 서버가 토큰을 기억하지 않으므로 **발급한 토큰을 중간에 무효화하기 어렵다**. 탈취된 토큰은 만료까지 유효하다.

쉬운 예: 공연 입장권이다.
- 세션 = 매표소 명단. 입구마다 명단을 조회한다. 명단에서 지우면 바로 못 들어간다.
- JWT = 위조 방지 홀로그램이 붙은 입장권. 입구는 홀로그램과 날짜만 본다. 명단이 필요 없지만, 잃어버린 표를 무효화하려면 입구마다 "분실 표 번호 목록"을 따로 돌려야 한다.

실무 예:
- 라이브러리가 `"alg":"none"` 토큰이나, RS256 대신 HS256으로 바꿔 서명한 토큰(CVE-2015-9235)을 받아들여 아무나 관리자가 됐다.
- 퇴사자 계정을 막았는데 그 사람이 받아 둔 access token으로 1시간 동안 API가 됐다.

## 동작·원리

### 1. JWT의 생김새 — 인코딩이지 암호화가 아니다

```text
  eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9 . eyJpc3MiOiJodHRwczovL2lzc3Vlci5leGFtcGxlIiwi... . kV3o...
  └──────── header (base64url) ───────┘   └──────────── payload (base64url) ────────────┘  └ signature ┘
  {"alg":"RS256","typ":"JWT"}             {"iss":"https://issuer.example","aud":"orders-api",
                                           "sub":"user-42","exp":1791319982}

  서명 입력 = ASCII( base64url(header) + "." + base64url(payload) )
  signature = 발급자의 키로 서명 입력에 서명한 값
```

- base64url은 누구나 되돌린다. payload는 **누구나 읽는다**. 비밀(비밀번호, 주민번호, 내부 정보)을 넣지 않는다.
  - 흔한 오해: "JWT는 암호화돼 있다" → 서명된 JWT(JWS)는 기밀성을 주지 않는다. 주는 것은 무결성과 (믿을 수 있는 키로 검증했을 때) 발급자 진위다. 공유 HMAC 키라면 키를 가진 쪽 중 누가 만들었는지는 구별되지 않는다(아래 "HS256 vs RS256/ES256"). 기밀성이 필요하면 JWE(RFC 7516)지만, 보통은 넣지 않는 것이 답이다.
- *등록 claim*(RFC 7519 §4.1): `iss`(발급자), `sub`(주체), `aud`(수신 대상), `exp`(만료), `nbf`(이전 사용 금지), `iat`(발급 시각), `jti`(토큰 ID).
  - `exp`: 그 시각 **부터는**(같은 시각 포함) 받으면 안 된다(MUST NOT). 시계 오차용 여유는 "보통 몇 분 이하"를 허용한다(MAY, §4.1.4).

### 2. HS256 vs RS256/ES256 — 누가 발급할 수 있나

```text
  HS256 (HMAC, 대칭)                         RS256 / ES256 / EdDSA (서명, 비대칭)
  발급자 ──비밀 K──> 서명                     발급자 ──개인키──> 서명
  검증자 ──같은 K──> 검증                     검증자 ──공개키──> 검증
  → 검증할 수 있는 쪽은 모두 발급도 할 수 있다    → 검증자는 발급할 수 없다
  → 한 서비스 안에서만                         → 여러 서비스·외부에 검증을 맡길 때
```

- HS256 키가 사람이 기억할 만한 문자열이면, 토큰 하나만 손에 넣어도 오프라인으로 키를 대입해 찾을 수 있다(RFC 8725 §2.2). 키는 CSPRNG로 충분히 길게 만든다(§3.5, 09번).
- 서명 알고리즘 자체는 [06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md), HMAC은 [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md).

### 3. 검증 순서 — 하나라도 실패하면 거부

```text
  ① 형식: 점 2개, header·payload가 올바른 UTF-8 JSON (RFC 7519 §7.2)
  ② alg ∈ 서버가 정한 허용 목록, 이 키에 정해진 알고리즘과 일치   ← 토큰이 고르게 두지 않는다 (RFC 8725 §3.1)
  ③ 서명 검증 (키는 서버가 가진 것 / 발급자가 게시한 것만)
  ④ exp > 지금 − 여유, nbf ≤ 지금 + 여유
  ⑤ iss = 기대한 발급자 (§3.8)
  ⑥ aud ∋ 나 (§3.9)   ← 다른 서비스용 토큰을 나에게 쓰는 대체 공격 차단 (§2.7)
  ⑦ typ 등으로 토큰 종류 구분 (§3.11) — ID 토큰을 access token으로 쓰는 혼동 차단
  ⑧ 그다음에야 sub·scope로 인가
```

- RFC 7519 §7.2: 형식·디코딩·서명 검증 단계 중 하나라도 실패하면 JWT를 **거부해야 한다**(MUST). 서명이 맞아도 그 알고리즘이 애플리케이션이 받아들이는 것이 아니면 거부해야 한다(SHOULD).
- ④~⑦의 claim 검사는 §7.2의 단계가 아니라 각 claim 규정(§4.1.3 `aud`가 있는데 내가 없으면 거부 MUST, §4.1.4 `exp`, §4.1.5 `nbf`)과 RFC 8725 §3.8~§3.11이 요구한다.
- RFC 8725 §3.1: 라이브러리는 호출자가 허용 알고리즘을 정하게 해야 하고, 그 밖의 알고리즘을 쓰면 안 된다(MUST). 한 키는 정확히 한 알고리즘에만 쓴다(MUST).

### 4. 알고리즘 혼동 — 토큰이 검증 방법을 고르게 두면

```text
  취약 검증기: alg = header.alg;  key = 설정된 키 하나
     "alg":"none"   → 서명 검사 생략 → 아무 payload나 통과
     "alg":"HS256"  → HMAC(key = RSA 공개키 바이트, 서명 입력) 로 검증
                       공개키는 공개돼 있다 → 공격자도 같은 HMAC을 계산 → 위조 통과
  고친 검증기: 허용 = {RS256}; header.alg ≠ RS256 → 거부; RSA 서명 검증
```

- RFC 8725 §2.1이 정리한 두 공격이다. `none`을 믿는 라이브러리, RS256 토큰을 HS256으로 바꾸면 RSA 공개키를 HMAC 비밀로 쓰는 라이브러리. 후자의 예가 CVE-2015-9235다. NVD 설명: node `jsonwebtoken` 4.2.2 미만에서 비대칭(RS/ES) 대신 대칭(HS) 알고리즘으로 서명한 토큰으로 검증을 우회할 수 있다(CVSS 3.0 9.8).

실험(OpenJDK 21.0.12 temurin, `--network none`, 2026-10-07) — JDK만으로 RS256 발급기와 두 검증기를 만들었다. 키는 실행마다 새로 만든 일회용 2048비트 RSA다:

```text
  payload는 누구나 읽는다: {"iss":"https://issuer.example","aud":"orders-api","sub":"user-42","exp":1791319982}
  토큰                        | 취약 검증기             | 고친 검증기
  정상 RS256                  | ACCEPT sub=user-42     | ACCEPT sub=user-42
  alg:none + sub=admin        | ACCEPT sub=admin       | REJECT alg=none (허용 목록 밖)
  HS256(공개키를 비밀로)       | ACCEPT sub=admin       | REJECT alg=HS256 (허용 목록 밖)
  payload 변조(서명 그대로)    | REJECT                 | REJECT 서명 불일치
  만료(exp 1시간 전)           | ACCEPT sub=user-42     | REJECT exp
  다른 aud                    | ACCEPT sub=user-42     | REJECT aud
  ES256 서명 r=s=0 → REJECT  [java 21.0.12]
```

- 취약 검증기도 RS256 경로에서는 변조를 잡았다. 구멍은 서명 알고리즘이 아니라 **검증 방법을 토큰이 고르게 둔 설계**와 **claim 검사 누락**이다.
- 마지막 줄은 라이브러리 자체 결함의 회귀 확인이다. CVE-2022-21449(ECDSA가 r=s=0 서명을 받아들임, NVD CVSS 3.1 7.5)는 JDK 21.0.12에서 거부됐다. NVD는 영향 판을 지원 판 기준 Oracle Java SE 17.0.2·18로 적고, 발견자 블로그는 Java 15~18(2022-04 CPU 이전)이 영향을 받는다고 적는다. 서명 검증 코드가 맞아도 런타임이 낡으면 뚫린다. 패치 관리는 25번.

### 5. 폐기 — 기억하지 않는 토큰을 어떻게 무르나

```text
  선택지                       폐기 즉시성      상태 저장         비용
  짧은 exp (예: 5~15분, 예시)    만료까지 지연     없음             재발급 잦음 → refresh 토큰(17번)
  jti 차단 목록(TTL = exp+여유)  즉시            폐기된 것만       매 요청 조회(캐시)
  사용자별 "이 시각 이전 발급 무효" 즉시(사용자 단위) 사용자당 시각 하나  매 요청 조회
  불투명 토큰 + 조회(RFC 7662)    즉시            전부             매 요청 인가 서버 호출
  세션으로 돌아가기              즉시            전부             저장소 조회
```

- 차단 목록은 폐기한 토큰만 담고, 그 토큰의 `exp`에 시계 여유(Spring 기본 60초)까지 지나면 지워도 된다(그 뒤로는 만료 검사에서 걸린다). `exp`에 바로 지우면 여유 구간 동안 폐기 토큰이 다시 통과한다. 그래서 크기가 "만료 전 폐기 토큰 수"로 제한된다.
- 비밀번호 변경·강제 로그아웃은 사용자 단위 컷오프가 편하다. `iat < user.tokensValidAfter`이면 거부.
- 자기 포함 토큰의 장점(조회 없음)을 일부 포기하는 것이 폐기의 값이다. 수명 설계와 refresh 회전은 [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md).

### 6. 세션 vs 토큰 — 고르는 기준

| | 서버 세션 + 쿠키 | 자기 포함 토큰(JWT) |
|---|---|---|
| 검증 | 저장소 조회 | 서명·claim 검사(키만 필요) |
| 즉시 폐기 | 쉬움 | 어려움(위 표) |
| 여러 서비스·외부 위임 | 저장소 공유 필요 | 쉬움(공개키 배포, 13번) |
| 크기 | 쿠키에 ID만 | claim이 늘면 헤더가 커짐 |
| 브라우저 탈취 면 | `HttpOnly` 쿠키 | JS 저장소에 두면 XSS로 탈취(17번·web-platform/06) |

- 단일 웹 앱이면 세션이 단순하다. 서비스 사이 호출, 외부 발급자(OAuth/OIDC, 14번)가 있으면 토큰이 맞다.

## 쓰이는 자료구조·알고리즘

- **base64url** — `+/` 대신 `-_`, 패딩 `=` 생략. URL·헤더에 그대로 실린다. 인코딩일 뿐 비밀을 지키지 않는다.
- **HMAC-SHA-256 / RSA-PKCS#1 v1.5·PSS / ECDSA·EdDSA** — 서명 입력(header.payload)에 대한 MAC·서명. [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md), [06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md).
- **허용 목록 조회** — `(kid, alg) → 키` 맵에서 꺼낸 키와 그 키의 알고리즘만 쓴다. 토큰 헤더의 값은 "어느 칸을 볼지" 힌트일 뿐이다.
- **TTL 해시 집합(차단 목록)** — `jti`를 키로, 남은 수명을 TTL로 저장한다(Redis `SET jti 1 EX <exp-now>`). 조회 O(1). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **시각 비교와 여유(leeway)** — `now < exp + skew`. 서버 시계가 틀리면 정상 토큰이 거부된다. [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 직접 파싱하지 말고, 쓰더라도 알고리즘을 고정한다

취약 예:

```java
// 헤더의 alg를 그대로 믿는 손수 만든 검증
String alg = header.get("alg");
if (alg.equals("none")) return claims;                    // 서명 없음 허용
Mac mac = Mac.getInstance("Hmac" + alg.substring(2));     // HS256 → HMAC
mac.init(new SecretKeySpec(publicKeyPem.getBytes(), "HmacSHA256"));   // 공개키를 HMAC 비밀로
```

고친 예 — Spring Security 리소스 서버:

```java
@Bean
JwtDecoder jwtDecoder() {
    NimbusJwtDecoder decoder = NimbusJwtDecoder
        .withIssuerLocation("https://issuer.example")     // discovery로 jwks_uri를 찾는다(13번)
        .jwsAlgorithm(SignatureAlgorithm.RS256)            // 허용 알고리즘을 서버가 고정
        .build();
    OAuth2TokenValidator<Jwt> audience = jwt ->
        jwt.getAudience().contains("orders-api")
            ? OAuth2TokenValidatorResult.success()
            : OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_token", "aud mismatch", null));
    decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
        JwtValidators.createDefaultWithIssuer("https://issuer.example"),   // typ·exp/nbf·iss
        audience));
    return decoder;
}
```

- Spring Security 소스(main, 2026-10-07 조회) 기준
  - JWK Set URI 디코더의 기본 허용 알고리즘은 `RS256` 하나다.
  - `JwtValidators.createDefault…`는 `typ`(JWT 또는 없음), 시각(`JwtTimestampValidator`, 기본 시계 여유 60초), X.509 지문 검사를 넣는다. `aud`는 기본에 없다. 직접 넣는다.
  - 이 기본 `typ` 검사는 ID 토큰과 access token을 구별하지 못한다(둘 다 `JWT`이거나 없으면 통과). 구별하려면 access token에 `typ: at+jwt`(RFC 9068)를 요구하는 등 종류별로 배타적인 규칙을 둔다. main 소스에는 이를 묶은 `JwtValidators.createAtJwtValidator()`가 있다.
  - `JwtTimestampValidator`는 `exp`·`nbf`가 **없으면** 기본으로 통과시킨다(`allowEmptyExpiryClaim = true`). `exp`가 필수라면 `setAllowEmptyExpiryClaim(false)`나 존재 검사를 따로 넣는다.
  - 만료 실패 메시지는 `Jwt expired at <시각>`, 이른 사용은 `Jwt used before <시각>`이다.
- 설정만으로 할 때(Spring Boot 공통 프로퍼티 문서, 2026-10-07 조회): `spring.security.oauth2.resourceserver.jwt.issuer-uri`, `...jwt.audiences`, `...jwt.jws-algorithms`(기본 `RS256`).

### 2. 폐기를 설계한다

```java
// 사용자 단위 컷오프 + jti 차단 목록
boolean revoked(Jwt jwt) {
    Instant cutoff = users.tokensValidAfter(jwt.getSubject());            // 비밀번호 변경·강제 로그아웃 때 now로 갱신
    if (cutoff != null && jwt.getIssuedAt().isBefore(cutoff)) return true;
    return redis.hasKey("revoked:" + jwt.getId());                        // 폐기 시 TTL = exp − now 로 저장
}
```

- 이 검사를 넣으면 매 요청 조회가 생긴다. 조회 대상이 작아(폐기된 것만) 캐시하기 쉽다.

### 3. 토큰에 무엇을 넣지 않을지

```text
  넣지 않는다: 비밀번호·개인정보·내부 시스템 경로·긴 권한 목록(헤더가 커져 431·프록시 제한)
  넣는다:      iss, sub(불투명 ID), aud, exp(짧게), iat, jti, 최소한의 scope
```

- 개인정보는 로그·브라우저 저장소·프록시 로그에 함께 복제된다(27번).

### 4. 진단 — 토큰을 읽어 본다

```bash
# payload만 확인(검증 아님). 운영 토큰을 외부 디코딩 사이트에 붙여 넣지 않는다.
cut -d. -f2 <<< "$TOKEN" | tr '_-' '/+' | base64 -d 2>/dev/null; echo
```

- `exp`·`nbf`·`iat`를 서버 시각(`date +%s`)과 비교한다. `iss`·`aud`가 설정값과 문자 단위로 같은지(끝의 `/` 하나도) 본다.

## 장애 시나리오와 대처

### 1. `alg: none`·HS/RS 혼동 수락 → 아무나 관리자

- **현상**: 보안 점검에서 서명을 지운 토큰(`"alg":"none"`, 서명 부분 빈 문자열)이나 HS256으로 바꾼 토큰이 `200`을 받는다.
- **보이는 형태**: 접근 로그에 정상 발급 기록이 없는 `sub=admin` 요청. 토큰 헤더 `alg`가 발급자가 쓰지 않는 값.
- **원인**: 검증기가 헤더의 `alg`로 검증 방법을 고른다. 허용 목록이 없거나, 키가 알고리즘에 묶여 있지 않다.
- **대처**: 허용 알고리즘을 서버에서 고정(RFC 8725 §3.1). 키마다 알고리즘 하나. 손수 만든 검증을 버리고 검증된 라이브러리를 쓴다. 회귀 테스트에 `none`·HS 위조 토큰을 넣어 거부를 고정한다(위 실험 표가 그 테스트다).

### 2. `exp`를 안 본다 → 만료 토큰이 영원히 유효

- **현상**: 몇 달 전 로그에서 주운 토큰으로 API가 된다.
- **보이는 형태**: `exp`가 과거인 토큰의 `200` 응답. 디코더가 서명만 확인하고 claim 검증기를 설정하지 않았다.
- **원인**: 서명 검증 = 검증 완료로 착각했다. 사용자 지정 `JwtDecoder`에서 `setJwtValidator`를 빠뜨리거나, 직접 파싱에서 시각 비교를 생략했다.
- **대처**: 시각·iss·aud 검증을 넣고, "만료 토큰은 `401` + `WWW-Authenticate: Bearer error="invalid_token"`"을 테스트로 고정한다(RFC 6750 §3.1).

### 3. 서버 시계가 밀려 정상 토큰이 전부 거부된다

- **현상**: 특정 인스턴스만 `401`을 낸다. 다른 인스턴스는 같은 토큰을 받아들인다.
- **보이는 형태**: 그 인스턴스 로그에 `Jwt used before ...`(토큰에 `nbf`가 있고 시계가 느림) 또는 `Jwt expired at ...`(시계가 빠름). `chronyc tracking`의 오프셋이 수십 초 이상.
- **원인**: NTP 동기화가 멈췄다. 발급자와 검증자의 시계 차이가 여유(Spring 기본 60초)를 넘었다.
- **대처**: 시계 동기화를 복구하고 오프셋에 알람을 건다. 여유를 크게 늘려 덮지 않는다(만료 토큰을 그만큼 더 받는다).

### 4. 탈취된 토큰을 막을 수 없다

- **현상**: 계정 탈취를 확인하고 비밀번호를 바꿨는데, 공격자가 1시간 동안 API를 계속 쓴다.
- **보이는 형태**: 비밀번호 변경 뒤에도 같은 `jti`·옛 `iat`를 가진 토큰의 `200` 요청.
- **원인**: 자기 포함 토큰은 서버가 기억하지 않는다. access token 수명이 길고 폐기 경로가 없다.
- **대처**: access token 수명을 짧게, 사용자 단위 컷오프(`iat < tokensValidAfter`)와 `jti` 차단 목록을 둔다. refresh 토큰 회전과 전체 로그아웃은 17번.

### 5. `aud`를 안 본다 → 다른 서비스용 토큰이 통한다

- **현상**: 결제 API가 같은 발급자가 "알림 서비스"용으로 발급한 토큰을 받아들인다.
- **보이는 형태**: 요청 토큰의 `aud`가 `notification-api`인데 결제 API가 `200`.
- **원인**: iss·서명만 확인했다. 같은 발급자가 모든 서비스의 토큰을 같은 키로 서명하므로 서명은 맞다(RFC 8725 §2.7 대체 공격).
- **대처**: 서비스마다 고유 `aud`를 요구하고 검증한다(§3.9). ID 토큰과 access token은 `typ`·검증 규칙으로 구분한다(§3.11·§3.12).

## 핵심 문장

- 서명된 JWT는 `header.payload.signature`이고, payload는 인코딩일 뿐 누구나 읽는다. 서명이 주는 것은 무결성과 발급자 진위다.
- 검증 방법은 서버가 정한다. 토큰 헤더의 `alg`가 검증 방법을 고르게 두면 `none`과 HS/RS 혼동으로 위조가 통과한다.
- 서명 검증 뒤에 exp·nbf·iss·aud·typ를 확인한다(필수 claim은 존재 여부까지). 하나라도 실패하면 거부한다.
- HS256은 검증할 수 있는 쪽이 모두 발급도 할 수 있다. 여러 서비스에 검증을 맡기면 비대칭 서명을 쓴다.
- 자기 포함 토큰은 서버가 기억하지 않으므로 폐기가 어렵다. 짧은 수명, 사용자 단위 컷오프, jti 차단 목록으로 보완한다.

## 관련 주제·근거

- 선행
  - [06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md) — RSA·ECDSA·Ed25519 서명
  - [11-sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md) — 서버 세션과의 비교
- 후속·연결
  - [13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md) — 검증 키를 어디서 얻고 어떻게 회전하나
  - [14-oauth2-and-oidc](../14-oauth2-and-oidc/2-summary.md) — access token과 ID 토큰
  - [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) — 수명 설계·폐기·저장 위치
  - 원본 [foundations/security/oidc.md](../../foundations/security/oidc.md) §3 — JWT·claim 기초, [foundations/security/hmac.md](../../foundations/security/hmac.md)
  - [web-platform/06-browser-storage](../../web-platform/06-browser-storage/2-summary.md) — 브라우저에 토큰을 둘 때
- 1차 출처
  - RFC 7519 JWT — §4.1 등록 claim(§4.1.3 `aud` 불일치 시 거부 MUST), §4.1.4 `exp` 여유 "보통 몇 분 이하", §7.2 형식·서명 검증 단계(하나라도 실패 시 거부) <https://www.rfc-editor.org/rfc/rfc7519>
  - RFC 8725 JWT Best Current Practices — §2.1 `none`·RS→HS 혼동, §2.2 약한 대칭 키, §2.7 대체 공격, §3.1 알고리즘 검증, §3.8 iss, §3.9 aud, §3.11 명시적 타입 <https://www.rfc-editor.org/rfc/rfc8725>
  - RFC 7515 JWS, RFC 7518 JWA <https://www.rfc-editor.org/rfc/rfc7515>
  - RFC 6750 Bearer Token Usage — §3.1 `invalid_token`(401)·`insufficient_scope`(403) <https://www.rfc-editor.org/rfc/rfc6750>
  - RFC 7662 Token Introspection <https://www.rfc-editor.org/rfc/rfc7662>
  - NVD CVE-2015-9235 (jsonwebtoken < 4.2.2, CVSS 3.0 9.8) <https://nvd.nist.gov/vuln/detail/CVE-2015-9235> · CVE-2022-21449 (Java SE 17.0.2·18 등, CVSS 3.1 7.5) <https://nvd.nist.gov/vuln/detail/CVE-2022-21449> · 발견자 Neil Madden "Psychic Signatures in Java"(2022-04-19, Java 15~18) <https://neilmadden.blog/2022/04/19/psychic-signatures-in-java/>
  - Spring Security 소스(main, 2026-10-07 조회) — `NimbusJwtDecoder`(기본 RS256), `JwtValidators`, `JwtTimestampValidator`(60초, 오류 문구), `JwtTypeValidator.jwt()`
- 실험(2026-10-07, eclipse-temurin:21-jdk = OpenJDK 21.0.12, `--network none`)
  - 취약/고친 검증기 비교: `none`·HS256(공개키 비밀)·변조·만료·다른 aud 6가지 토큰
  - JDK 21의 ECDSA r=s=0 서명 거부(CVE-2022-21449 회귀 확인)
