# security/01-security-principles — CIA, 최소 권한, 심층 방어, fail-safe 기본값, 완전한 중재 — 정리 (힌트)

## 해결하는 문제

보안 결함은 대부분 "몰랐던 공격 기법"이 아니라 **설계 규칙을 한 군데에서 어긴 것**이다.

```text
  흔한 사고 세 가지 — 셋 다 "새 공격"이 아니다
  ① 인가 서버가 타임아웃 → catch 블록이 "일단 통과" → 장애 동안 누구나 관리자 API 호출
  ② 권한을 회수했는데 → 앱이 첫 판정을 캐시해 둠 → 퇴사자가 계속 접근
  ③ 배치 계정 하나가 DB 전체 쓰기 권한 → 그 계정 키가 새자 전 테이블이 위험
```

- 1975년 Saltzer–Schroeder 논문이 이런 실수를 막는 설계 원칙 8개를 정리했다. 50년이 지난 지금도 위 세 사고는 각각 원칙 하나씩을 어긴 것이다.
  - ① = fail-safe 기본값 위반, ② = 완전한 중재 위반, ③ = 최소 권한 위반.
- 이 노트는 보안 영역 전체의 공통 어휘다. 뒤의 암호(03~09)·인증·인가(10~17)·웹 공격(18~24)은 모두 "어떤 성질(CIA)을, 어떤 원칙으로 지키나"로 읽힌다.

쉬운 예: 건물 출입 관리다.
- 출입증이 없으면 들어갈 수 없다(기본은 거부).
- 문마다 카드를 찍는다(매번 확인).
- 청소 직원 카드는 청소 구역만 연다(최소 권한).
- 정문 경비가 뚫려도 서버실 문이 따로 잠겨 있다(심층 방어).

똑같은 구조다.\
차이는 소프트웨어에서는 "문"이 수천 개이고, 장애·캐시·예외 경로처럼 **눈에 안 띄는 문**이 많다는 것이다.

## 동작·원리

### 1. 지킬 성질 — CIA

```text
               무엇을 잃나                  예                         관련 노트
  기밀성 C    허가 없는 공개               DB 덤프 유출, 로그에 토큰    03 암호화, 27 마스킹
  무결성 I    허가 없는 변경·파괴           금액 변조, 위조 웹훅         04 해시, 05 MAC, 06 서명
  가용성 A    정당한 사용의 방해            DoS, 인증 서버 장애 전파     28 남용 제한
```

- 정의(FIPS 199, 44 U.S.C. §3542 인용)
  - *기밀성(confidentiality)*: 정보 접근·공개에 대한 허가된 제한을 지키는 것.
  - *무결성(integrity)*: 부적절한 변경·파괴를 막는 것. 부인 방지와 진위(authenticity) 보장을 포함한다.
  - *가용성(availability)*: 정보에 제때 믿을 만하게 접근·사용할 수 있게 하는 것.
- Saltzer–Schroeder도 같은 세 범주로 위반을 나눈다: 허가 없는 정보 공개, 허가 없는 변경, 허가 없는 사용 거부.
- 세 성질은 서로 부딪친다.
  - 인가 서버가 죽었을 때 "통과"는 가용성을 지키고 기밀성·무결성을 버린다. "거부"는 반대다.
  - 어느 쪽을 고를지가 다음 절의 fail-safe 기본값 문제다.

### 2. Saltzer–Schroeder 설계 원칙 8개

| 원칙 | 논문 요지 | 오늘의 모양 |
|---|---|---|
| 메커니즘의 경제성(economy of mechanism) | 설계를 작고 단순하게 — 검사할 수 있게 | 인가 로직을 한 곳(필터·정책 엔진)에 |
| **fail-safe 기본값** | 접근 판단은 "배제"가 아니라 "허가"에 근거. 기본은 접근 없음 | 허용 목록, `anyRequest().denyAll()`, 예외 시 거부 |
| **완전한 중재(complete mediation)** | 모든 객체에 대한 모든 접근을 매번 권한 확인 | 객체 수준 인가(15번), 캐시된 판정의 무효화 |
| 공개 설계(open design) | 설계는 비밀이 아니어야 한다. 비밀은 키·비밀번호에만 | 검증된 공개 알고리즘(AES·HMAC), 자작 암호 금지 |
| 권한 분리(separation of privilege) | 두 조건(키 두 개)이 있어야 열리게 | MFA, 배포 2인 승인 |
| **최소 권한** | 모든 프로그램·사용자는 일에 필요한 최소 권한으로 | 역할별 DB 계정, 짧은 수명 토큰, 범위 제한 키 |
| 최소 공통 메커니즘 | 여러 사용자가 공유·의존하는 메커니즘을 줄인다 | 테넌트 격리, 공유 캐시 키에 사용자 구분 |
| 심리적 수용성 | 인터페이스가 사용자의 사고방식에 맞아 올바른 보호가 일상이 되게 | 안전한 기본값, 쉬운 MFA |

- 논문은 두 원칙을 더 든다. *작업 계수(work factor)*: 우회 비용을 공격자 자원과 비교한다. *침해 기록(compromise recording)*: 막지 못해도 침해 흔적을 남긴다(26번 감사 로그).
- *심층 방어(defense in depth)*: 8원칙 목록에는 없는 말이다. 한 층이 뚫려도 다음 층이 막도록 독립된 통제를 겹친다. 권한 분리·침해 기록과 같은 생각에서 나온다.
  - 흔한 오해: "층이 많을수록 안전하다." 층들이 같은 가정(예: "내부망은 안전")에 기대면 한 번에 같이 뚫린다. 층은 **서로 다른 실패 원인**을 가져야 한다.

### 3. fail-safe 기본값 — 예외 경로가 "허가"가 되면

```text
  요청 ──> [인가 확인] ──> 인가 서버
                │
       ┌────────┼──────────────────┐
     200 허가  403 거부    타임아웃·연결 거부·파싱 실패 (판정 불가)
       │        │                  │
     통과     403          fail-open : 통과  ← 장애 = 무방비
                           fail-closed: 503/403 ← 장애 = 서비스 중단(그러나 안전)
```

- 논문 문장: "기본 상황은 접근 없음이고, 보호 체계는 접근이 허가되는 조건을 식별한다."
  - 허가 조건을 빠뜨리면 정당한 사용자가 거부된다. 시끄럽고 금방 발견된다.
  - 거부 조건을 빠뜨리면(배제 방식) 공격자가 통과한다. 조용하다.
- 코드의 예외 경로가 가장 흔한 위반 자리다.
  - *fail-open*: 보호 장치가 판정을 못 하면 통과시키는 동작. CWE-636 "Not Failing Securely ('Failing Open')".
  - *fail-closed*: 판정을 못 하면 막는 동작.
- OWASP Top 10 2025는 이 문제를 새 범주 **A10:2025 Mishandling of Exceptional Conditions**로 넣었고(24개 CWE), CWE-636을 "주목할 CWE"(Notable CWEs) 다섯 개 중 하나로 든다. 2021판에는 없던 범주다.
- 예외: 보호 대상이 기밀성이 아니라 **가용성 보조 장치**면 fail-open이 맞을 수 있다.
  - 예: Stripe는 요청 속도 제한기가 고장 나면 통과시키도록 설계했다([reliability/11](../../reliability/11-rate-limiter/2-summary.md)). 같은 노트도 로그인 시도 제한처럼 보안 한도는 fail-closed가 맞을 수 있다고 적는다.
  - 판단 기준: "이 장치가 고장 났을 때 통과시키면 **누가 무엇을** 할 수 있게 되나?"

로컬 재현(실험 E1) — 127.0.0.1의 인가 서버를 끈 뒤 같은 요청:

```text
  (실험, OpenJDK 21.0.12 eclipse-temurin, --network none, 2026-10-07)
  [3] 인가 서버 중단(연결 거부)
      mallory: open=200 closed=503  (22 ms)
      예외 형태: java.net.ConnectException
```

- 괄호 안 시간은 실행마다 다르다(재실행 11 ms). 상태 코드(200/503)와 예외 이름은 재실행에서도 같았다.
- 평소에는 두 구현이 같은 답(alice 200, mallory 403)을 낸다. **차이는 장애 때만 보인다.** 그래서 정상 경로 테스트로는 안 잡힌다.

### 4. 완전한 중재 — "한 번 확인했으니 됐다"의 함정

```text
  t0  alice 요청 → 인가 서버 "허가" → 앱이 결과를 캐시(만료 없음)
  t1  관리자가 alice 권한 회수
  t2  alice 요청 → 캐시 적중 "허가"   ← 인가 서버는 묻지도 않음
```

- 논문 문장: "모든 객체에 대한 모든 접근은 권한을 확인해야 한다."
  - 정상 운영뿐 아니라 초기화·복구·종료·유지보수 경로도 포함한다.
  - 성능을 위해 권한 확인 결과를 기억해 두자는 제안은 회의적으로 검토하고, 권한이 바뀌면 기억된 결과를 체계적으로 갱신해야 한다고 적는다.
- 위반 모양 셋
  - 판정 캐시에 만료·무효화가 없다(위 그림).
  - 화면에서는 버튼을 숨겼지만 API는 검사하지 않는다.
  - 목록 조회는 검사하지만 단건 조회 `/orders/{id}`는 검사하지 않는다(IDOR — 15번).
- 로컬 재현(실험 E1): 권한 회수 후 만료 없는 캐시는 `200`, 매번 묻는 판은 `403`.

```text
  [2] 캐시된 허가: alice 허가 후 권한 회수
      회수 전 cached=200
      회수 후 cached=200  매번 확인=403
```

- 캐시 자체가 잘못은 아니다. 캐시 TTL이 곧 **"권한 회수가 반영되기까지 최대 지연"**이라는 것을 정하고 문서화하면 된다(12번 JWT의 `exp`와 같은 문제).

### 5. 최소 권한·심층 방어 — 피해 반경을 줄인다

```text
  최소 권한 없이                          최소 권한 + 심층 방어
  ┌──────────────┐                        ┌──────────────┐
  │ 웹 앱         │ DB 계정: superuser      │ 웹 앱         │ DB 계정: app_rw (자기 스키마 DML만)
  └──────┬───────┘                        └──────┬───────┘
         │ SQL 인젝션 1건                         │ SQL 인젝션 1건
         ▼                                       ▼
   전 DB 읽기·DROP·파일 읽기                   자기 테이블만. 감사 로그(26)에 흔적. WAF·바인딩(18)이 앞층
```

- 최소 권한은 공격을 막지 않는다. **뚫렸을 때의 피해 범위(blast radius)**를 줄인다. 논문도 "사고나 오류로 생기는 피해를 제한한다"고 적는다.
- 권한은 사람·서비스·토큰·키 모두에 적용된다: 범위(scope)가 좁은 OAuth 토큰(14번), 짧은 수명 자격 증명(09번), 컨테이너 비루트 실행([os/28](../../os/28-containers-namespaces-cgroups/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- 이 노트는 원리 노트라 커리큘럼 🔧 칸이 비어 있다. 원칙이 실제로 놓이는 구조만 짚는다.
- **허용 목록(allowlist) = 집합 소속 판정.** fail-safe 기본값은 "목록에 있으면 허가, 없으면 거부"다. 해시 집합으로 O(1) 판정([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)). 반대인 차단 목록은 "모르는 것 = 허가"라 기본값이 뒤집힌다.
- **규칙 매칭 순서 = 첫 일치 규칙.** Spring Security의 `requestMatchers`는 위에서부터 첫 일치 규칙을 쓴다. 마지막 줄 `anyRequest()`가 기본값이다.
- **판정 캐시 = TTL 해시 맵.** 완전한 중재를 지키면서 캐시하려면 키 = (주체, 자원, 행위), 값 = 판정, TTL = 허용 가능한 회수 지연. 판정이 시간·위치 같은 환경 조건에도 달린 정책이면 그 조건도 키에 넣거나 그 판정은 캐시하지 않는다(NIST SP 800-162 §2). 권한 변경 이벤트로 키를 지운다([data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 기본값을 거부로 — Spring Security

```java
// 취약: 명시한 경로만 막고 나머지는 통과 (배제 방식)
http.authorizeHttpRequests(a -> a
        .requestMatchers("/admin/**").hasRole("ADMIN")
        .anyRequest().permitAll());          // 새로 만든 /internal/debug 도 열림

// 고친 판: 명시한 것만 허가, 나머지 거부 (허가 방식)
http.authorizeHttpRequests(a -> a
        .requestMatchers("/admin/**").hasRole("ADMIN")
        .requestMatchers("/api/**").authenticated()
        .requestMatchers("/health").permitAll()
        .anyRequest().denyAll());
```

- Spring Security 레퍼런스(7.1판)는 `denyAll()`로 끝내는 이유를 "규칙 갱신을 잊는 사고를 막는다"고 적는다.
- 같은 문서: `AuthorizationFilter`는 요청마다가 아니라 **디스패치마다**(REQUEST·FORWARD·ERROR·INCLUDE) 돈다. 완전한 중재를 프레임워크 수준에서 지키는 설계다. 에러 페이지 포워드가 막혀 예상 밖 `AccessDeniedException`이 나면, 그 디스패치 유형만 명시적으로 허가한다.

### 2. 예외 경로를 fail-closed로

```java
// 취약: 판정 불가 = 통과
boolean allowed(String user) {
    try { return authClient.check(user); }
    catch (Exception e) { log.warn("authz down", e); return true; }
}

// 고친 판: 판정 불가 = 거부. 상태 코드로 "거부"와 "판정 불가"를 구분한다
Decision decide(String user) {
    try { return authClient.check(user) ? Decision.ALLOW : Decision.DENY; }     // 403
    catch (Exception e) { meter.counter("authz.unavailable").increment();
                          return Decision.UNAVAILABLE; }                         // 503
}
```

- 503과 403을 나누는 이유: 403은 "당신은 안 된다", 503은 "지금 판정할 수 없다". 클라이언트 재시도·경보가 달라진다.
- 장애 주입 테스트로 확인한다: 인가 서버를 끈 상태에서 보호 API가 2xx를 내면 실패.

### 3. 최소 권한 점검표

- DB: 앱 계정에 DDL·superuser 없음, 읽기 전용 리포트는 별도 계정([database 영역](../../database/README.md)).
- 클라우드: 역할 정책에 `*` 행위·`*` 자원이 없는지.
- 토큰: 범위(scope)·대상(aud)·수명 제한(12~14번).
- 프로세스: 컨테이너 `USER` 비루트, 쓸 필요 없는 파일시스템은 읽기 전용.

### 4. 진단 — 로그에서 fail-open 흔적 찾기

```text
  장애 구간 동안
    authz.denied   (분당)   평소 40  →  0      ← 거부가 0이 됐다 = 아무도 안 막혔다
    authz.error    (분당)   평소 0   →  1,200
    2xx on /admin/**        평소 3   →  250
```

- "거부 수가 0"은 좋은 신호가 아니다. 인가 서버 오류율과 함께 보면 fail-open을 찾는다(예시 수치).

## 장애 시나리오와 대처

### 1. 인가 서버 장애 때 모두 통과 (fail-open) ⚠

- **현상**: 인가 서버(또는 정책 엔진·세션 저장소) 장애 동안 권한 없는 사용자의 요청이 성공한다. 장애가 끝나야 드러나거나, 감사에서 뒤늦게 발견된다.
- **보이는 형태**
  - 응답: 보호 경로에 평소 403이 나와야 할 요청이 200.
  - 로그: `ConnectException`·`SocketTimeoutException` 경고와 같은 시각에 거부 로그가 0건.
  - 코드: `catch (Exception e) { return true; }`, 기본값이 `ALLOW`인 enum, `null` 정책 = 허가.
- **원인**: 예외 경로의 기본값이 허가다. "인증 서버 때문에 서비스 전체가 멈추면 안 된다"는 가용성 압력이 만든 경우가 많다.
- **대처**
  - 판정 불가는 503(또는 403)으로. 가용성 요구는 인가 서버의 이중화·판정 캐시(짧은 TTL)로 푼다. 보호를 끄는 것으로 풀지 않는다.
  - 장애 주입 테스트를 CI에 둔다([engineering-practice/15](../../engineering-practice/15-security-standards/2-summary.md) 장애 5와 같은 대처).
  - 가용성 장치(속도 제한기 등)를 fail-open으로 둘 때는 그것이 보안 통제가 아님을 문서화한다.

### 2. 권한을 회수했는데 계속 접근된다 (완전한 중재 위반)

- **현상**: 퇴사자·강등된 사용자가 몇 시간~며칠 더 접근한다.
- **보이는 형태**: 권한 DB에는 없는 사용자가 접근 로그에 계속 200. 앱 재시작 뒤에야 403.
- **원인**: 판정을 만료 없이 캐시했다. 또는 긴 수명 토큰(JWT)에 역할을 넣어 두고 매 요청 확인을 안 한다(12·17번).
- **대처**: 캐시 TTL = 허용 가능한 회수 지연으로 정하고 문서화. 권한 변경 이벤트로 캐시 키 삭제. 민감 작업(송금·권한 변경)은 캐시를 거치지 않는다.

### 3. 계정 하나가 뚫려 전부가 뚫림 (최소 권한·심층 방어 부재)

- **현상**: 작은 취약점(인젝션 1건, 유출된 CI 토큰 1개)이 전체 데이터 유출로 커진다.
- **보이는 형태**: 사후 조사에서 그 자격 증명 하나로 모든 테이블·버킷에 접근 가능했음이 드러난다.
- **원인**: 편의를 위한 넓은 권한. 내부망·내부 계정은 안전하다는 단일 가정(02번 신뢰 경계).
- **대처**: 역할 분리, 범위 제한 토큰, 자원별 정책. 층마다 다른 실패 원인(네트워크 정책 + 인가 + 감사 로그).

### 4. 숨긴 버튼 = 보안이라고 착각 (공개 설계·완전한 중재 위반)

- **현상**: 관리 기능 버튼을 화면에서 숨겼지만 API 직접 호출로 실행된다.
- **보이는 형태**: 브라우저 개발자 도구 네트워크 탭에서 보인 경로를 그대로 호출하면 200.
- **원인**: 클라이언트 측 통제만 있고 서버 측 확인이 없다. "경로를 모르면 못 부른다"는 비밀 설계 의존.
- **대처**: 서버에서 매 요청 인가. 경로·설계는 공개돼도 안전해야 한다.

## 핵심 문장

- 보안 목표는 기밀성·무결성·가용성(CIA)이고, 셋은 서로 부딪친다. 장애 때 무엇을 포기할지를 미리 정하는 것이 설계다.
- fail-safe 기본값: 접근은 "허가 조건"이 있을 때만. 예외·타임아웃·파싱 실패 같은 판정 불가 경로가 허가가 되면 장애가 곧 무방비가 된다.
- 완전한 중재: 모든 접근을 매번 확인한다. 판정 캐시의 TTL은 곧 권한 회수의 최대 지연이다.
- 최소 권한은 공격을 막는 것이 아니라 뚫렸을 때의 피해 반경을 줄인다.
- 심층 방어의 층은 서로 다른 실패 원인을 가져야 한다. 같은 가정에 기댄 층은 함께 무너진다.
- 설계는 공개돼도 안전해야 하고, 비밀은 키·비밀번호에만 둔다.

## 관련 주제·근거

- 후속(같은 영역 — [영역 표](../README.md))
  - [02-threat-modeling](../02-threat-modeling/2-summary.md) — 원칙을 어디에 적용할지 찾는 절차(자산·신뢰 경계·STRIDE)
  - [security/15-access-control-models](../15-access-control-models/2-summary.md) — 완전한 중재의 객체 수준 구현(IDOR)
  - [security/12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md), [security/17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) — 캐시된 판정으로서의 토큰, 회수 지연
  - [security/26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md) — 침해 기록(compromise recording)
- 연결
  - [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) — 가용성 장치의 fail-open 선택(Stripe)
  - [engineering-practice/15-security-standards](../../engineering-practice/15-security-standards/2-summary.md) — OWASP Top 10·ASVS·A10 예외 경로 리뷰
  - [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md) — 게이트웨이 = 중재 지점, 백엔드 직접 접근 차단
  - [software-design/15-error-handling-design](../../software-design/15-error-handling-design/2-summary.md) — 예외 경로 설계
- 1차 출처
  - J. H. Saltzer, M. D. Schroeder, "The Protection of Information in Computer Systems", Proceedings of the IEEE 63(9), 1975, pp. 1278–1308 — §I.A.3 설계 원칙 8개 + 작업 계수·침해 기록, 위반 3범주. 온라인 전재본 <https://www.cs.virginia.edu/~evans/cs551/saltzer/>
  - NIST FIPS 199 (2004) — 기밀성·무결성·가용성 정의(44 U.S.C. §3542) <https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.199.pdf>
  - OSTEP 53 "Introduction to Operating System Security"(Peter Reiher) <https://pages.cs.wisc.edu/~remzi/OSTEP/>
  - OWASP Top 10:2025 A10 Mishandling of Exceptional Conditions — 새 범주, CWE-636 포함, "failing closed" <https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions>
  - CWE-636 Not Failing Securely ('Failing Open') <https://cwe.mitre.org/data/definitions/636.html>
  - Spring Security Reference(7.1판) "Authorize HttpServletRequests" — `anyRequest().denyAll()`, 디스패치마다 인가 <https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html>
- 실험
  - E1 `FailSafe.java` — 127.0.0.1 인가 서버(JDK `HttpServer`)를 둔 fail-open/fail-closed 비교, 만료 없는 판정 캐시. OpenJDK 21.0.12(eclipse-temurin:21-jdk), `--network none`, 2026-10-07.
