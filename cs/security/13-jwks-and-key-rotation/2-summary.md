# security/13-jwks-and-key-rotation — 공개키 배포, `kid`, 캐시, 회전 — 정리 (힌트)

## 해결하는 문제

비대칭 서명 토큰(12번)을 검증하려면 발급자의 공개키가 필요하다. 공개키는 비밀이 아니다. 어려운 것은 **전달과 교체**다.

```text
  공개키를 설정 파일에 박아 둔다
  발급자가 키를 바꾼다(정기 교체, 유출 의심)
     → 새 키로 서명된 토큰을 검증자가 하나도 검증 못 한다 → 401 폭증
     → 막으려면 회전 때마다 모든 검증자를 다시 배포
```

- 해법: 발급자가 현재 공개키들을 정해진 URL에 JSON으로 게시하고(JWKS), 검증자는 거기서 가져와 캐시한다. 토큰 헤더의 `kid`가 어느 키인지 알려 준다.
  - *JWK*: 키 하나를 표현한 JSON(RFC 7517). *JWKS(JWK Set)*: `keys` 배열을 가진 JSON.
  - *kid*: 키 식별자. 토큰 헤더의 `kid`와 JWK의 `kid`를 맞춰 키를 고른다.
  - *키 회전(key rotation)*: 서명 키를 새 키로 교체하는 일.
- 기초(왜 하드코딩하면 깨지나, JWK 필드, discovery → `jwks_uri` → `kid` 선택 → 검증의 네 걸음)는 원본 [foundations/security/jwks.md](../../foundations/security/jwks.md) §1~§3에 있다. 이 노트는 그 위에서 **캐시와 회전의 시간 계산, 장애 모양**을 다룬다.

쉬운 예: 관공서 "현재 유효한 도장 목록" 게시판이다.
- 검증자는 게시판을 가끔 베껴 온다(캐시).
- 처음 보는 도장이 찍힌 서류가 오면 게시판을 다시 본다(미지 `kid` 재페치).
- 관공서가 새 도장을 **게시판에 먼저 올리고 한참 뒤에** 쓰기 시작하면, 아무도 놀라지 않는다(사전 게시).

## 동작·원리

### 1. 검증자 안의 `kid → 공개키` 캐시

```text
  토큰 헤더 {"alg":"RS256","kid":"k2"}
        │
        ▼
  캐시(kid → 공개키, 가져온 시각)  ── TTL 지남? ──예──> JWKS 다시 가져옴 ── 실패 → 401 (fail-closed)
        │ 아니오
        ▼
  kid 있음? ──예──> 서명 검증 → 200 / 401
        │ 아니오
        ▼
  최근 강제 재페치 후 쿨다운 지났나? ──예──> JWKS 다시 가져옴 → 그래도 없으면 401 "kid not found"
        │ 아니오
        ▼
  401 "kid not found" (재페치 없이)
```

- 두 축이 따로 돈다(원본 §5).
  - **TTL**: 폐기된 옛 키를 언제까지 믿나. 길수록 유출 키를 오래 믿는다.
  - **미지 `kid` 재페치**: 새 키를 얼마나 빨리 받아들이나. 이것이 없으면 새 키를 TTL만큼 늦게 알게 된다.
- OpenID Connect Core 1.0 §10.1.1이 이 계약을 적는다. 서명자는 새 키를 "재량껏" 쓰기 시작할 수 있고, 검증자는 낯선 `kid`를 보면 `jwks_uri`를 다시 가져온다. JWKS는 최근 은퇴한 키를 "합리적 기간" 남겨 둬야 한다(SHOULD).
- `kid` 규칙
  - RFC 7517 §4.5: 구조는 정해져 있지 않다. 한 JWKS 안의 키들은 서로 다른 `kid`를 써야 한다(SHOULD).
  - OIDC Core §10.1: JWKS에 키가 여럿이면 JOSE 헤더에 `kid`가 있어야 한다(MUST).
  - 참고: 원본 §3의 "`kid`가 없으면 집합의 키를 하나씩 다 시도해야 한다"는 일반 규칙이 아니다. OIDC 발급자는 키가 여럿이면 `kid`를 넣어야 하므로, `kid` 없는 토큰은 키가 하나일 때만 정상이다. 여러 키를 차례로 시도하는 것은 일부 라이브러리의 호환 동작이고, 시도 횟수만큼 검증 비용이 든다.

### 2. 회전의 시간표 — 무엇을 언제 하나

```text
  시간 →   t0               t1 = t0 + 캐시 TTL 이상        t2 = t1 + 토큰 최대 수명 + 시계 여유
  JWKS     [k1] → [k1, k2]   [k1, k2]                       [k1, k2] ──제거──> [k2]
           (t0에 k2 게시)
  서명     k1                k1 ──전환──> k2                  k2
  검증자   k1만 앎           재페치(TTL)로 k2도 앎            k1 서명 토큰이 모두 만료됨 → k1 제거해도 안전

  ① 사전 게시: 새 키를 서명에 쓰기 전에(t0) JWKS에 올린다
  ② 전환: 검증자 캐시가 모두 새 JWKS를 봤을 시점(t0 + 최대 캐시 TTL) 이후에 서명 키를 바꾼다
  ③ 은퇴: 옛 키로 마지막 서명한 토큰까지 만료(+ 허용한 시계 여유)된 뒤 옛 키를 뺀다. 캐시 TTL을 더 기다리는 것은 보수적인 운영 여유다
```

- 사전 게시를 하면 검증자가 미지 `kid` 재페치를 안 해도 401이 없다(실험 D).
- 사전 게시 없이 바로 전환하면, 미지 `kid` 재페치가 있는 검증자만 버틴다(실험 A).
- **긴급 회전**(키 유출)은 반대다. 옛 키를 즉시 빼야 한다. 그러면 JWKS를 새로 받은 검증자부터 옛 키로 서명된 정상 토큰도 무효가 되고(재로그인), 옛 키를 캐시에 가진 검증자는 TTL이 끝나거나 캐시를 비울 때까지 빼낸 옛 키를 여전히 믿는다. TTL이 긴 검증자가 많을수록 유출 키의 수명이 길다.

### 3. 실험 — 캐시 정책별 401과 페치 횟수

OpenJDK 21.0.12 temurin, `--network none`, 2026-10-07. 한 JVM 안에 로컬 JWKS 서버(`com.sun.net.httpserver`, 127.0.0.1)와 검증자를 두고, 시각은 가상 시계로 1초에 요청 1건씩 흘렸다. 키는 실행마다 새로 만든 일회용 RSA 2048이다.

```text
  [A] t=100 회전(k2 게시와 동시에 k2로 서명). 요청 1건/초로 t=100..899
    TTL 600s, 미지 kid 재페치 없음          {200=300, 401 kid not found=500}  첫 200 시각 t=600  JWKS 페치 1회
    TTL 600s, 미지 kid 재페치(쿨다운 30s)    {200=800}  첫 200 시각 t=100  JWKS 페치 2회
  [B] 무작위 kid 토큰 1000건(같은 초 t=1000) — 재페치 쿨다운 유무
    쿨다운  0s: {401 kid not found=1000}  JWKS 페치 1000회
    쿨다운 30s: {401 kid not found=1000}  JWKS 페치 1회
  [C] t=2000 JWKS 503 시작
    t=2000 → 200   t=2300 → 200   t=2589 → 200
    t=2590 → 401 JWKS 페치 실패(fail-closed)   t=2600 → 401 ...   t=3000 → 401 ...
    t=3010 복구 후 → 200
  [D] t=4000 k3 게시(서명은 k2 유지) → t=4700 k3로 서명 전환. 재페치 없는 검증기
    {200=1400}
```

- A: 재페치가 없으면 회전 직후부터 TTL이 끝날 때까지(500초) 정상 토큰이 전부 401이다. 재페치가 있으면 첫 요청에서 바로 따라간다.
- B: 무작위 `kid` 토큰이 오면 재페치 규칙이 그대로 발급자 호출로 바뀐다. 쿨다운 없이 1000건 → 발급자 페치 1000회. 원본 [Claude 추가]의 "재페치에도 한도가 필요하다"가 수치로 보인다.
- C: 발급자 JWKS가 죽어도 캐시가 살아 있는 동안(마지막 페치 t=1990 + 600초 = t=2590 직전)은 검증이 된다. TTL이 끝나는 순간 전면 401이다. TTL은 "발급자 장애를 버티는 시간"이기도 하다.
- D: 캐시 TTL(600초)보다 오래(700초) 사전 게시하면, 재페치가 없는 검증기도 401이 0건이다.

### 4. 라이브러리가 실제로 하는 일 (소스 기준)

- Nimbus JOSE+JWT `JWKSourceBuilder`(master 소스, 2026-10-07 조회)
  - 기본 캐시 TTL 5분(`DEFAULT_CACHE_TIME_TO_LIVE`), 캐시 갱신 대기 15초, 미리 갱신 30초, 재페치 최소 간격 30초(`DEFAULT_RATE_LIMIT_MIN_INTERVAL`).
  - 기본 켜짐: 캐시·미리 갱신·속도 제한. 기본 꺼짐: 재시도·장애 허용(outage tolerant).
  - `JWKSetBasedJWKSource.get`: 고른 키가 없으면 JWKS를 다시 가져와 한 번 더 고른다(미지 `kid` 재페치).
- Spring Security `NimbusJwtDecoder.withJwkSetUri(...)`(main 소스, 2026-10-07 조회)
  - 위 빌더를 `.refreshAheadCache(false).rateLimited(false)`로 만든다. Spring `Cache`를 따로 주지 않으면 Nimbus 캐시를 쓴다.
  - 해석: 재페치 속도 제한이 꺼져 있으므로, 무작위 `kid` 토큰 폭격이 발급자 페치로 이어질 수 있다(실험 B의 "쿨다운 0" 쪽). 이 동작을 Spring 앱에서 직접 측정하지는 않았다.
  - 키를 못 고르면 Nimbus 메시지 `Signed JWT rejected: Another algorithm expected, or no matching key(s) found`가 Spring의 `An error occurred while attempting to decode the Jwt: %s` 틀에 담겨 나온다.

### 5. 보안 경계 — 원본 §5 요약과 보탬

- `jwks_uri`는 `https`여야 한다(OIDC Discovery 1.0, MUST). 페치 채널이 모든 서명 검증의 신뢰 뿌리다.
- 알고리즘은 서버가 고정한다(12번).
- `kid`는 서명 검증 전의 값이라 공격자가 바꿀 수 있다. **가져온 JWKS 안에서** 고를 때만 쓴다. `kid`를 파일 경로·SQL·URL로 쓰면 경로 조작·인젝션 통로가 된다(RFC 8725 §2.9 "받은 claim으로 조회하는 간접 공격" 계열. §3.10은 `kid`로 하는 키 조회가 SQL·LDAP 인젝션이 되지 않게 검증·정제하라고 직접 적는다). 헤더의 `jku`·`x5u`(키 URL)를 맹목적으로 따라가는 것은 SSRF가 될 수 있다(§3.10, SHOULD 허용 목록). 허용한 발급자 URL만 쓴다.
- 서명 검증 키와 암호화 키가 한 JWKS에 같이 있으면 `use`로 구분해야 한다(Discovery, REQUIRED). 서명 검증에는 `use: "sig"`만 쓴다.

## 쓰이는 자료구조·알고리즘

- **`kid → 키` 해시 맵 + TTL** — 조회 O(1). 맵 전체를 한 번에 교체한다(페치 결과로 원자적 치환). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **캐시 무효화 정책** — TTL 만료와 "미스 시 갱신"을 함께 쓴다. 미스 갱신은 쿨다운(최소 간격)으로 묶는다. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **단일 비행(single flight)** — 같은 순간 여러 요청이 미스를 내도 페치는 하나만 보낸다. Nimbus는 "읽은 JWKS와 지금 캐시가 같은 객체인지"(`referenceComparison`) 비교해 다른 스레드가 이미 갱신했으면 다시 가져오지 않는다. 캐시 스탬피드와 같은 문제다. [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md)
- **RSA 공개키 복원** — JWK의 `n`·`e`(Base64urlUInt, RFC 7518 §6.3.1)를 부호 없는 큰 정수로 읽어 `RSAPublicKeySpec`을 만든다.

## 적용 — 풀어나가는 법

### 1. 검증자 — 캐시 TTL, 미지 `kid` 재페치, 쿨다운, fail-closed

취약 예:

```java
// 앱 시작 때 한 번만 가져오고 끝. 회전하면 재배포 전까지 전부 401
private final Map<String, PublicKey> keys = fetchJwksOnce(jwksUri);
PublicKey keyFor(String kid) { return keys.get(kid); }
```

또 다른 취약 예:

```java
// 매 요청 페치 — 발급자를 두드리고, 발급자 장애가 곧 우리 장애
PublicKey keyFor(String kid) { return fetchJwks(jwksUri).get(kid); }
```

고친 예:

```java
final class JwksCache {
    private static final Duration TTL = Duration.ofMinutes(10);        // 예시 값
    private static final Duration REFETCH_COOLDOWN = Duration.ofSeconds(30);
    private volatile Map<String, PublicKey> keys = Map.of();
    private volatile Instant fetchedAt = Instant.EPOCH, lastForced = Instant.EPOCH;
    private final ReentrantLock lock = new ReentrantLock();

    PublicKey keyFor(String kid) {
        Instant now = Instant.now();
        Instant seen = fetchedAt;
        if (now.isAfter(seen.plus(TTL))) refresh(now, seen);            // 실패하면 keys가 비어 → 401
        seen = fetchedAt;
        PublicKey k = keys.get(kid);
        if (k == null && now.isAfter(lastForced.plus(REFETCH_COOLDOWN))) {
            lastForced = now;                                             // 무작위 kid 폭격을 쿨다운으로 묶음
            refresh(now, seen);
            k = keys.get(kid);
        }
        return k;                                                         // null → 호출자가 401
    }
    private void refresh(Instant now, Instant seen) {
        lock.lock();                                                      // 동시 미스는 줄을 선다
        try {
            if (!fetchedAt.equals(seen)) return;                          // 기다리는 동안 다른 스레드가 갱신함 → 다시 페치 안 함
            Map<String, PublicKey> fresh = fetchJwks();                   // https만, 연결·읽기 타임아웃 설정
            keys = fresh; fetchedAt = now;
        } catch (IOException e) {
            if (now.isAfter(fetchedAt.plus(TTL))) keys = Map.of();       // TTL 넘은 키는 믿지 않는다(fail-closed)
        } finally { lock.unlock(); }
    }
}
```

- Spring Security를 쓰면 이 구조를 직접 만들 필요는 없다. 대신 기본값(속도 제한 꺼짐)을 알고, 필요하면 앞단에서 `kid` 형식 검사(허용 문자·길이)나 요청 제한을 둔다.

### 2. 발급자 — 회전 절차를 문서로 고정한다

```text
  정기 회전(예: 90일, 예시)
  1. 새 키 생성(KMS·HSM 안에서, 개인키는 밖으로 안 나옴)            ← 09번
  2. JWKS에 새 공개키 추가 (kid 새로)
  3. 대기 ≥ 모든 검증자 캐시 TTL의 최댓값 (모르면 넉넉히, 예: 24시간)
  4. 서명 키 전환
  5. 대기 ≥ 토큰 최대 수명 + 시계 여유 (검증자 캐시 TTL을 더하면 보수적 여유)
  6. 옛 공개키 제거
  긴급 회전(유출)
  1~2 같음 → 즉시 서명 전환 + 옛 키 즉시 제거 → 옛 키 서명 토큰 무효화(재로그인 공지, 캐시를 비운 검증자부터)
  → 검증자 운영자에게 캐시 즉시 비우기 요청(TTL 동안 유출 키를 믿으므로)
```

### 3. 진단 — 401 폭증이 회전 때문인지 본다

```bash
# 토큰의 kid
cut -d. -f1 <<< "$TOKEN" | tr '_-' '/+' | base64 -d 2>/dev/null; echo
# 발급자가 지금 게시한 kid 목록 (운영 발급자 URL은 설정값으로)
curl -s "$ISSUER/.well-known/openid-configuration" | jq -r .jwks_uri
curl -s "$JWKS_URI" | jq -r '.keys[] | "\(.kid) \(.use) \(.alg)"'
```

- 토큰의 `kid`가 JWKS에 **있는데** 401이고 검증자 로그의 거부 사유가 `kid not found`·`no matching key` → 검증자 캐시가 낡았다(재페치 없음·쿨다운 과대·로컬 캐시 고정). 거부 사유가 서명 불일치·만료·`aud` 불일치면 키 선택은 맞은 것이다. `kid` 일치는 단서일 뿐이니 실제 거부 사유를 먼저 본다.
- 토큰의 `kid`가 JWKS에 **없는데** 정상 발급 토큰이다 → 발급자가 게시 전에 서명을 시작했거나, 여러 발급 노드 중 일부만 새 키를 쓴다.
- 검증자 로그에 JWKS 페치 실패(타임아웃·5xx)가 보이면 장애 2.

## 장애 시나리오와 대처

### 1. 키 회전 직후 `kid` 캐시 미스 → 401 폭증

- **현상**: 발급자가 키를 바꾼 직후 일부 서비스에서 로그인된 사용자 요청이 전부 401. 몇 분~몇십 분 뒤 저절로 회복된다.
- **보이는 형태**: 검증자 로그 `no matching key(s) found`·`kid not found`. 실패 토큰의 `kid`는 발급자 JWKS에 이미 있다. 회복 시각 = 회전 전 마지막 페치 시각 + 그 서비스의 캐시 TTL(늦어도 회전 시각 + TTL. 실험 A: t=0 페치, t=100 회전, t=600 회복 = 0 + 600).
- **원인**: 발급자가 사전 게시 없이 새 키로 서명을 시작했고, 검증자는 미지 `kid` 재페치가 없거나(시작 때 한 번 로드) 쿨다운이 너무 길다.
- **대처**
  - 검증자: 미지 `kid` 재페치(쿨다운 수십 초)를 켠다. 직접 만든 정적 키 맵을 라이브러리 캐시로 바꾼다.
  - 발급자: 사전 게시 → 대기(≥ 최대 캐시 TTL) → 전환 순서를 지킨다(실험 D: 401 0건).

### 2. JWKS 엔드포인트 장애 → 전면 인증 실패

- **현상**: 발급자(IdP) 장애 몇 분 뒤 모든 API가 401을 낸다. 이미 로그인한 사용자도 막힌다. 단 Spring Security 기본 설정이면 JWKS 페치 실패가 401이 아니라 `500`류로 보일 수 있다(페치 실패 → `AuthenticationServiceException` 재던짐 경로, 6.5.5 소스 기준 — [29 3절](../29-security-symptom-index/2-summary.md)).
- **보이는 형태**: 검증자 로그에 JWKS 페치 타임아웃·`503`. 401 시작 시각이 "발급자 장애 시작"이 아니라 "마지막 성공 페치 + TTL"이다(실험 C: t=2000 장애, t=2590부터 401).
- **원인**: 캐시가 만료된 뒤 새로 가져오지 못해 키가 없다. fail-closed라 거부한다. 이것은 의도된 안전 동작이고, 문제는 TTL과 장애 시간의 비율이다.
- **대처**
  - 단기: 발급자 복구가 우선이다. 검증 생략(fail-open)으로 열지 않는다.
  - 설계: "갱신 실패 시 마지막으로 성공한 JWKS를 일정 시간 더 쓰는" 장애 허용 옵션(Nimbus `outageTolerant`, 기본 꺼짐)을 검토한다. 유출 키 폐기 지연과 맞바꾸는 결정이라 상한 시간을 정해 문서화한다. JWKS는 CDN·복제로 가용성을 높인다.

### 3. 무작위 `kid` 폭격 → 발급자 호출 폭증

- **현상**: 특정 시간에 발급자 JWKS 엔드포인트 호출이 평소의 수백 배로 오르고, 발급자가 우리 서비스를 차단(429)한다.
- **보이는 형태**: 검증자 로그에 매 요청 다른 `kid`의 `kid not found`. JWKS 페치 수 ≈ 실패 요청 수(실험 B: 1000건 → 1000회).
- **원인**: 미지 `kid` 재페치에 속도 제한이 없다. 공격자는 아무 `kid`나 단 토큰을 보내기만 하면 된다.
- **대처**: 재페치 쿨다운(Nimbus 기본 30초 — Spring 디코더는 이를 끈다는 점을 확인), `kid` 형식 검사, 같은 출처의 401 연속에 요청 제한. 재페치 뒤에도 없는 `kid`는 즉시 거부한다.

### 4. 키를 너무 일찍 뺐다 → 일부 사용자만 401

- **현상**: 회전 며칠 뒤 옛 키를 제거하자, 오래 켜 둔 앱·배치 작업만 401을 받는다.
- **보이는 형태**: 실패 토큰의 `kid`가 옛 키, `iat`가 제거 이전. 대부분 refresh 직전의 긴 수명 토큰.
- **원인**: 옛 키로 서명한 토큰이 "최대 수명 + 시계 여유" 동안 다 만료되기 전에 옛 키를 뺐다. 또는 장기 토큰(서비스 간 토큰)의 수명을 계산에 넣지 않았다.
- **대처**: 은퇴 대기 시간을 가장 긴 토큰 수명 기준으로 정한다. 제거 전 "옛 `kid` 서명 토큰 검증 수"가 0인지 지표로 확인한다.

## 핵심 문장

- JWKS는 공개키의 "전달과 교체"를 표준화한다. 검증자가 쥐는 것은 키가 아니라 키를 가져올 위치다.
- 검증자는 JWKS를 TTL로 캐시하고, 모르는 `kid`를 보면 재페치한다. 재페치에는 쿨다운을 둔다.
- 회전은 사전 게시 → (캐시 TTL 이상 대기) → 서명 전환 → (토큰 최대 수명 + 시계 여유 대기, TTL을 더하면 보수적 여유) → 옛 키 제거 순서다.
- 캐시 TTL은 세 가지를 동시에 정한다. 폐기 키를 믿는 기간, 새 키를 늦게 아는 기간(재페치 없을 때), 발급자 장애를 버티는 기간.
- JWKS를 못 가져오거나 `kid`가 없으면 거부한다(fail-closed). `kid`는 받은 JWKS 안에서 고를 때만 쓴다.

## 관련 주제·근거

- 선행
  - [12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md) — JWT 검증, 알고리즘 고정
  - 원본 [foundations/security/jwks.md](../../foundations/security/jwks.md) — §1 하드코딩의 문제, §2 JWK·JWKS 필드, §3 discovery와 `kid`, §5 보안 고려, §6 JOSE 표준 묶음
- 후속·연결
  - [14-oauth2-and-oidc](../14-oauth2-and-oidc/2-summary.md) — discovery 문서와 ID 토큰
  - [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — 키 수명·KMS
  - [network/30-x509-and-chain-validation](../../network/30-x509-and-chain-validation/2-summary.md), [network/31-revocation-ocsp-ct](../../network/31-revocation-ocsp-ct/2-summary.md) — 인증서 세계의 같은 문제(배포·폐기)
  - [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md), [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)
- 1차 출처
  - RFC 7517 JWK — §4.5 `kid`(구조 미정, 집합 안 고유 SHOULD), §5 JWK Set <https://www.rfc-editor.org/rfc/rfc7517>
  - RFC 7515 JWS — §4.1.4 `kid` 헤더 = 키 변경을 알리는 힌트 <https://www.rfc-editor.org/rfc/rfc7515>
  - RFC 7518 JWA — §6.3.1 RSA `n`·`e` <https://www.rfc-editor.org/rfc/rfc7518>
  - RFC 8725 — §2.9 받은 claim으로 하는 조회의 간접 공격, §3.10 `kid` 조회 인젝션·`jku`/`x5u` SSRF <https://www.rfc-editor.org/rfc/rfc8725>
  - OpenID Connect Core 1.0 — §10.1 키가 여럿이면 `kid` MUST, §10.1.1 서명 키 회전(낯선 `kid` → 재페치, 은퇴 키 유지 SHOULD) <https://openid.net/specs/openid-connect-core-1_0.html>
  - OpenID Connect Discovery 1.0 — `jwks_uri` REQUIRED·https MUST, 서명·암호화 키 공존 시 `use` REQUIRED <https://openid.net/specs/openid-connect-discovery-1_0.html>
  - Nimbus JOSE+JWT 소스(master, 2026-10-07 조회) — `JWKSourceBuilder` 기본값, `JWKSetBasedJWKSource.get`, `DefaultJWTProcessor` 오류 문구 <https://bitbucket.org/connect2id/nimbus-jose-jwt>
  - Spring Security 소스(main, 2026-10-07 조회) — `NimbusJwtDecoder.JwkSetUriJwtDecoderBuilder.jwkSource()`(`refreshAheadCache(false)`, `rateLimited(false)`)
- 실험(2026-10-07, eclipse-temurin:21-jdk = OpenJDK 21.0.12, `--network none`, 로컬 JWKS 서버 + 가상 시계)
  - A 사전 게시 없는 회전: 재페치 없음 401 500건 vs 재페치 0건
  - B 무작위 `kid` 1000건: 쿨다운 0초 페치 1000회 vs 30초 1회
  - C JWKS 503: 캐시 만료 전 200, 만료 후 401(fail-closed), 복구 후 200
  - D 사전 게시 700초(> TTL 600초): 재페치 없는 검증기도 401 0건
