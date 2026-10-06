# security/17-refresh-token-rotation-and-revocation — refresh 토큰 회전·재사용 탐지·폐기와 브라우저 저장 위치 — 정리 (힌트)

## 해결하는 문제

access 토큰은 짧게, 로그인은 길게 — 이 두 요구를 refresh 토큰이 잇는다. 대신 refresh 토큰이 **가장 비싼 비밀**이 된다.

```text
  수명       0 ─── 10분 ─────────────────────────────── 8시간
  access     [■■■]  → 만료 → [■■■] → [■■■] → ...          짧다: 탈취돼도 피해 창이 좁다
  refresh    [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■]   길다: 탈취되면 access를 계속 찍어 낸다

  질문 1  refresh가 탈취되면 어떻게 알아채나?            → 회전 + 재사용 탐지
  질문 2  탭 여러 개가 동시에 갱신하면?                  → 경합이 "탈취"로 오판될 수 있다
  질문 3  비밀번호를 바꾸면 이미 나간 토큰은?            → 폐기·강제 만료
  질문 4  브라우저 어디에 두나?                          → XSS 앞에서 저장소별 차이, BFF
```

- *access 토큰*: 리소스 서버(API)에 내미는 짧은 수명 자격 증명. 자기 포함형(JWT)이면 서버가 서명·`exp`만 보고 받는다(12번).
- *refresh 토큰*: 인가 서버의 토큰 엔드포인트에서 새 access 토큰을 받는 데만 쓰는 긴 수명 자격 증명. `grant_type=refresh_token`(RFC 6749 §6).
- RFC 9700(OAuth 2.0 보안 BCP, 2025-01) §4.14.1: refresh 토큰은 클라이언트에 허락된 전체 범위를 대표하므로 공격자에게 매력적인 표적이다.
- 쉬운 예: 놀이공원 손목밴드와 재입장 도장.
  - 손목밴드(access)는 오늘 하루만 쓴다. 잃어버려도 내일이면 무효다.
  - 재입장 교환권(refresh)은 새 손목밴드를 받는 권리다. 교환할 때마다 새 교환권을 주고 옛 것은 회수한다. 같은 번호의 옛 교환권이 또 들어오면 "누가 복사했다"는 신호다.
- 실무 예
  - 탭 세 개를 열어 둔 사용자가 아침에 노트북을 열자 세 탭이 동시에 갱신했고, 전원 로그아웃됐다.
  - 비밀번호를 바꿨는데 다른 기기의 앱이 며칠 계속 동작했다.

## 동작·원리

### 1. 회전과 재사용 탐지 — 토큰 패밀리

```text
  로그인 → RT1 ──사용──> RT2 ──사용──> RT3 (현재 유효)       같은 패밀리 F
           (used)        (used)

  공격자가 RT2를 훔쳐 나중에 사용:
           RT2(used) 재제출 ──> 서버: "이미 쓴 토큰" → 재사용 탐지 → 패밀리 F 전체 폐기
                                     → RT3도 무효. 정상 사용자도 재로그인
```

- *refresh 토큰 회전(rotation)*: 갱신할 때마다 새 refresh 토큰을 주고 이전 것을 무효로 한다. 서버는 둘의 관계를 기억한다.
- *토큰 패밀리*: 처음 발급된 refresh 토큰에서 회전으로 이어진 토큰 전체. 재사용이 보이면 패밀리 단위로 폐기한다.
- RFC 9700 §4.14.2(public client에 대해 MUST): 인가 서버는 다음 둘 중 하나로 refresh 재사용을 탐지해야 한다.
  - sender-constrained refresh 토큰: 토큰을 특정 클라이언트 인스턴스의 키에 묶는다(mTLS RFC 8705, DPoP RFC 9449).
  - 회전: 탈취된 토큰을 공격자와 정상 클라이언트가 둘 다 쓰면 한쪽은 무효 토큰을 낸다. 서버는 **누가 냈는지 모르므로** 활성 토큰을 폐기한다. 정상 클라이언트가 다시 인가를 받는 비용으로 공격을 멈춘다.
- 회전의 뿌리는 RFC 6749 §10.4의 예시다. §6은 "새 refresh 토큰을 주면 클라이언트는 옛 것을 버려야 한다(MUST)"고 적는다.
- *최종 만료(absolute lifetime)*: 회전과 상관없이 패밀리가 끝나는 시각. 로그인 때 한 번 정한다.
- 회전된 토큰의 수명: RFC 10017(OAuth 2.0 for Browser-Based Applications, BCP, 2026-08) §6.3.2.3은 브라우저 클라이언트에 대해, 처음 정한 만료가 있으면 회전 때 그 너머로 늘리지 말라(MUST NOT)고 적는다. 예: access 10분, refresh 8시간 → 10분 뒤 새 refresh는 7시간 50분.

### 2. 동시 갱신 경합 — 정상 사용자를 탈취범으로 오판

```text
  탭 A ──RT1──┐
              ├──> 토큰 엔드포인트
  탭 B ──RT1──┘
     A 먼저 도착: RT1 used, RT2 발급  ✔
     B 도착:      RT1 이미 used → 재사용 탐지 → 패밀리 폐기 → RT2도 무효
  결과: A의 이번 갱신은 성공, B는 invalid_grant, A의 다음 갱신도 RT2 폐기로 실패
        → 결국 로그아웃 (공격자는 없었다)
```

- 서버는 "같은 토큰이 두 번"만 보고, 그것이 탭 경합인지 탈취인지 구별하지 못한다.
- 대처는 두 쪽에서 한다.
  - 클라이언트 단일 비행(single-flight): 진행 중인 갱신 하나를 탭·요청들이 공유한다. 같은 출처의 탭·워커 사이에서는 Web Locks API(`navigator.locks.request`)로 잠금을 잡는다. 잠금은 차례만 정하므로, 잠금 안에서 "다른 탭이 이미 갱신했나"를 확인하고 건너뛰어야 한 번으로 합쳐진다. MDN 기준 2022-03부터 주요 브라우저에서 쓸 수 있고 보안 컨텍스트(HTTPS)가 필요하다.
  - 서버 유예 창: 직전 토큰을 짧은 시간 안에 다시 내면 탐지하지 않고 새 토큰을 준다. 예: Auth0의 rotation "leeway"(초 단위 설정, 기본 꺼짐). 그 창 안에서는 탐지가 적용되지 않고, 직전 토큰만 재사용할 수 있다. 그 이전 토큰은 탐지 대상이다.
  - 유예 창은 탐지를 그만큼 약하게 한다. 공격자가 창 안에 쓰면 통과한다. 그래서 짧게 둔다.

### 3. 폐기 — 무엇이 즉시 막히고 무엇이 남나

```text
  비밀번호 변경 / 전체 로그아웃 / 관리자 강제 만료
        │
        ├─ refresh 토큰: 서버에 상태가 있다 → 즉시 무효 가능 (패밀리 폐기, valid_after)
        │
        └─ access 토큰(자기 포함 JWT): 리소스 서버는 서명·exp만 본다 → exp까지 그대로 통과
              막으려면 ① 짧은 수명  ② 내부 조회(introspection)  ③ 폐기 목록(jti, TTL = 남은 수명)
                       ④ 사용자별 valid_after와 iat 비교
```

- RFC 9700 §4.14.2: 비밀번호 변경·인가 서버 로그아웃 같은 보안 사건 때 refresh 토큰을 자동 폐기할 수 있다(MAY). 오래 안 쓴 refresh 토큰은 만료돼야 한다(SHOULD).
- RFC 7009(토큰 폐기): refresh 토큰 폐기 지원은 MUST, access 토큰은 SHOULD. refresh를 폐기하면 같은 인가에서 나온 access 토큰도 무효로 해야 한다(SHOULD, 서버가 access 폐기를 지원할 때).
  - 같은 RFC 3절: 자기 포함 access 토큰은 리소스 서버가 인가 서버에 묻지 않으므로 즉시 폐기에 비표준 백엔드 연동이 필요하다. 대안이 짧은 수명이다.
- *introspection*: 리소스 서버가 인가 서버에 "이 토큰 지금 유효한가(`active`)"를 묻는 것(RFC 7662).
- *valid_after*: 사용자별 시각. 이보다 먼저 발급(`iat`)된 토큰을 거부한다. 폐기 목록을 토큰마다 두지 않고 사용자 한 줄로 끝낸다.

### 4. 브라우저 저장 위치와 BFF

```text
  (가) 브라우저가 OAuth 클라이언트                 (나) BFF
  ┌ 브라우저 ─────────────────────┐            ┌ 브라우저 ───────────┐
  │ JS: access·refresh 보관        │            │ 쿠키만 (HttpOnly,   │
  │   localStorage / 메모리         │            │  Secure, SameSite)  │
  └──────────┬─────────────────────┘            └─────────┬───────────┘
             │ Bearer                                      │ 쿠키
             ▼                                             ▼
          API                                 BFF(서버, confidential client) ── 토큰 보관
                                                         │ Bearer
                                                         ▼
                                                        API
```

- RFC 10017 §6: 세 가지 구조를 보안 순서로 제시한다. BFF → token-mediating backend → 브라우저 OAuth 클라이언트.
- (가)에서 XSS가 돌면
  - localStorage: 같은 출처 스크립트가 다 읽는다(§8.5). 한 번에 탈취([web-platform/06](../../web-platform/06-browser-storage/2-summary.md) 실험이 HttpOnly 쿠키는 안 보이고 localStorage는 보이는 것을 확인).
  - 메모리·클로저: 노출 창은 줄지만 프로토타입 오염으로 뚫릴 수 있다(§8.4).
  - 회전도 지속적 탈취(§5.1.2)에는 약하다. 공격자가 최신 토큰을 계속 가져가고, 정상 앱이 그 토큰을 다시 안 쓰게 만들면 재사용이 탐지되지 않는다.
  - 공격자가 숨은 iframe으로 **새** 인가 코드 흐름을 돌려 독립된 토큰을 받는 경우(§5.1.3, 인가 서버가 iframe 무음 흐름을 허용할 때)는 저장소 격리·짧은 수명·회전·DPoP 어느 것도 막지 못한다고 RFC가 적는다.
- (나) BFF(§6.1): 토큰이 브라우저 JavaScript에 없다. 서버 측 세션이면 토큰은 서버에만 있고, 클라이언트 측 세션이면 access 토큰이 HttpOnly 세션 쿠키 안에 들어갈 수 있다(그때 쿠키 내용 암호화 SHOULD, §6.1.2.3·§6.1.3.2). BFF는 confidential client라 브라우저에서 새 흐름을 돌려도 토큰을 못 받는다. 남는 위험은 사용자 브라우저를 통해 BFF에 요청을 대신 보내는 것(§5.1.4)이다.
  - 쿠키 요구(§6.1.3.2): `Secure`·`HttpOnly` MUST, `SameSite=Strict` SHOULD, `Path=/` SHOULD, `Domain` 없음 SHOULD, 이름에 "HTTP로 설정됨"을 나타내는 접두사 SHOULD(예: `__Host-Http-`).
  - BFF 세션 수명은 refresh 토큰 최대 수명과 맞추는 것이 합리적이라고 적는다(§6.1.2.2).

### 실험: 회전·재사용 탐지, 탭 경합과 두 가지 대처, 강제 만료, 최종 만료

`RefreshDemo.java` — 메모리 안의 작은 인가 서버. refresh 토큰은 `SecureRandom` 256비트, 서버는 SHA-256 해시의 앞 64비트(16진 16자)만 키로 저장(데모라 줄였다). 가짜 시계(초)로 수명을 흉내 냈다. 실패는 RFC 6749 §5.2의 `invalid_grant`로 표시.

```java
static synchronized Object refresh(String rt) {
    Rt s = store.get(h(rt));
    if (s == null) return "invalid_grant(unknown)";
    if (revokedFamilies.contains(s.family())) return "invalid_grant(family revoked)";
    if (now >= s.absExp()) return "invalid_grant(expired)";
    if (validAfter.getOrDefault(s.user(), -1L) > loginTimeOf(s)) return "invalid_grant(revoked: password changed)";
    if (s.used()[0]) {
        if (now - s.usedAt()[0] < leewaySec) return issue(s.user(), s.family(), s.absExp());  // 유예 창
        revokedFamilies.add(s.family());                                                      // 재사용 → 패밀리 폐기
        return "invalid_grant(reuse detected -> family " + s.family() + " revoked)";
    }
    s.used()[0] = true; s.usedAt()[0] = now;
    return issue(s.user(), s.family(), s.absExp());     // 최종 만료는 처음 값을 물려준다
}
```

(위는 요지, `now`·`loginTimeOf`는 실제 코드에서 `clock.get()`·`s.absExp() - RT_ABS`. 데모의 유예 창은 단순화라 "직전 토큰인가"를 보지 않고 시간만 본다. Auth0식 "직전 토큰만" 제한은 적용 §1의 `isLatestUsed()` 쪽이다.)

(실험, OpenJDK 21.0.12 eclipse-temurin:21-jdk 컨테이너 `--network none`, 2026-10-07, 3회 실행 — 토큰 해시·패밀리 ID와 3번 유예 0초에서 이긴 탭(A/B)만 달랐다)

```text
== 1. 정상 회전: 최종 만료 고정
  t=600 OK new rt#53c564db8c3b77e0 absExp=28800
  t=1200 OK new rt#f619571af380997e absExp=28800
  t=1800 OK new rt#248c200b196357a3 absExp=28800
== 2. 탈취: 공격자가 옛 토큰을 나중에 사용
  attacker uses stolen  : invalid_grant(reuse detected -> family fam-5fnyif revoked)
  legit uses its new rt : invalid_grant(family revoked)
== 3. 탭 두 개 동시 갱신 (같은 rt)
  leeway=0s tabA: OK new rt#e15d9f35cec3c65f absExp=30600
  leeway=0s tabB: invalid_grant(reuse detected -> family fam-XN-2B7 revoked)
  leeway=0s winner's next refresh: invalid_grant(family revoked)
  leeway=10s tabA: OK new rt#161293ea9b18cd6e absExp=30600
  leeway=10s tabB: OK new rt#025732bf2a26a668 absExp=30600
  leeway=10s winner's next refresh: OK new rt#aa7febb45d4ecc22 absExp=30600
  single-flight: requests sent=1 tabA=OK new rt#132aec9fc3546598 absExp=30600 tabB=OK new rt#132aec9fc3546598 absExp=30600 same=true
== 4. 비밀번호 변경 → 강제 만료
  refresh with old rt          : invalid_grant(revoked: password changed)
  old access, exp only         : 200  (exp까지 539s 남음)
  old access, + valid_after chk: 401 revoked (iat < valid_after)
== 5. 최종 만료 8h: 회전해도 연장 안 됨
  elapsed=8h -> invalid_grant(expired)
```

- 관찰
  - 1: 회전마다 새 토큰이 나왔고 `absExp`는 28800(로그인 + 8시간)에서 움직이지 않았다.
  - 2: 공격자의 옛 토큰 제출이 패밀리를 폐기했고, 정상 사용자의 최신 토큰도 함께 죽었다. RFC 9700이 말한 "정상 클라이언트가 다시 인가를 받는 비용"이 이것이다.
  - 3: 유예 0초에서는 경합만으로 패밀리가 폐기됐다(공격자 없음). 유예 10초에서는 두 탭 모두 새 토큰을 받았다(패밀리가 두 갈래로 갈라진다). 단일 비행은 요청 1번, 두 탭이 같은 결과를 공유했다. 어느 탭이 먼저 도착하는지는 실행마다 다를 수 있다.
  - 4: refresh는 즉시 막혔다. 자기 포함 access는 `exp`만 보면 539초 동안 200, `valid_after`를 보면 401.
  - 5: 한 시간마다 회전해도 8시간째에 `expired`. 회전이 수명을 늘리지 않았다.

## 쓰이는 자료구조·알고리즘

- **토큰 패밀리(체인·트리)**: 각 토큰이 부모를 가리키는 연결 구조. 유예 창이 있으면 한 부모에서 두 자식이 나와 트리가 된다. 폐기는 패밀리 ID 하나로 한다(RFC 9700 구현 노트: 토큰에 인가 식별자를 넣으면 폐기 대상을 빨리 찾는다. 그때는 서명으로 무결성을 지켜야 한다 MUST).
- **해시로 저장**: 서버는 토큰 원문 대신 SHA-256 해시를 키로 둔다. DB가 새도 원문 토큰이 바로 쓰이지 않는다(해시는 [04번](../04-hash-functions-and-digests/2-summary.md)).
- **폐기 목록(TTL 해시)**: `jti → 폐기` 항목을 토큰의 남은 수명만큼만 둔다. 만료되면 어차피 거부되므로 목록이 무한히 크지 않는다. Redis `SET key 1 EX <남은 초>`, 시간 기반 만료는 [data-structure/26-timer-structures](../../data-structure/26-timer-structures/2-summary.md).
- **단일 비행(single-flight)**: 같은 키의 진행 중 작업을 하나로 합쳐 결과를 공유. 캐시 스탬피드 대책과 같은 모양이다([reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md)).
- **원자적 상태 전이**: "아직 안 쓴 토큰이면 쓴 것으로 표시"를 한 번에. DB에서는 조건부 UPDATE(`WHERE used_at IS NULL`)의 영향 행 수로 판정한다([database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 인가 서버 — 회전·재사용 탐지 테이블

```sql
CREATE TABLE refresh_tokens (
  token_hash  char(64) PRIMARY KEY,         -- SHA-256(원문), 원문은 저장하지 않는다
  family_id   uuid        NOT NULL,
  user_id     bigint      NOT NULL,
  parent_hash char(64),
  used_at     timestamptz,
  abs_exp     timestamptz NOT NULL,         -- 패밀리 처음 값 그대로 물려준다
  revoked     boolean     NOT NULL DEFAULT false
);
CREATE INDEX ON refresh_tokens (family_id);
```

```java
// 취약: 읽고 → 판단하고 → 쓰는 사이에 다른 요청이 끼어든다 (두 요청 모두 "미사용"으로 읽음)
RefreshToken t = repo.findByHash(h);
if (t.usedAt() == null) { repo.markUsed(h); return issueNext(t); }

// 고친 판: 조건부 UPDATE 한 문장으로 "처음 쓴 사람"만 이긴다
int won = jdbc.update("""
    UPDATE refresh_tokens SET used_at = now()
     WHERE token_hash = ? AND used_at IS NULL AND NOT revoked AND abs_exp > now()""", h);
if (won == 1) return issueNext(h);                               // 새 토큰, abs_exp 그대로
var t = repo.findByHash(h);                                      // 졌다: 이유를 가린다
if (t == null || t.revoked() || t.absExp().isBefore(now())) throw invalidGrant();
if (Duration.between(t.usedAt(), now()).compareTo(LEEWAY) < 0 && t.isLatestUsed()) return issueNext(h);   // 유예 창
jdbc.update("UPDATE refresh_tokens SET revoked = true WHERE family_id = ?", t.familyId());              // 재사용 → 패밀리 폐기
securityLog.warn("refresh_reuse family={} user={}", t.familyId(), t.userId());
throw invalidGrant();                                            // HTTP 400 {"error":"invalid_grant"}
```

- 재사용 탐지는 보안 사건이다. 로그에 남기고 알림 대상으로 둔다(26번). Auth0도 재사용 이벤트를 로그 유형으로 남긴다고 문서에 적는다.

### 2. Spring Authorization Server를 쓴다면

```java
RegisteredClient.withId(id)
    .clientId("web-bff")
    .tokenSettings(TokenSettings.builder()
        .accessTokenTimeToLive(Duration.ofMinutes(5))
        .refreshTokenTimeToLive(Duration.ofHours(8))
        .reuseRefreshTokens(false)          // false = 갱신마다 새 refresh 토큰(회전)
        .build())
    ...
```

- 주의: 이 설정만으로는 8시간 **최종** 만료가 되지 않는다. 기본 생성기 `OAuth2RefreshTokenGenerator`는 회전 때마다 만료를 "발급 시각 + `refreshTokenTimeToLive`"로 새로 계산한다(Spring Security main 소스, 2026-10-07 열람). RFC 10017 §6.3.2.3처럼 처음 만료를 물려주려면 생성기를 직접 바꿔야 한다.
- 소스 기준 기본값(`TokenSettings.builder()`): access 5분, refresh 60분, `reuseRefreshTokens(true)` = **회전 안 함**. 확인한 소스는 spring-authorization-server 저장소 main과, 이 프로젝트가 옮겨 간 Spring Security main의 같은 클래스다(2026-10-07 열람).
- `OAuth2RefreshTokenAuthenticationProvider`(같은 저장소)는 토큰을 못 찾거나 비활성이면 `invalid_grant`를 던진다. 열람한 이 클래스에는 재사용 시 패밀리 전체를 폐기하는 분기가 없었다. 탐지가 필요하면 직접 붙여야 한다 `[?]`(다른 확장 지점은 확인하지 않았다).

### 3. 브라우저 — 갱신을 하나로 합친다 (TypeScript)

```ts
// 취약: 401을 받은 요청마다 각자 refresh를 쏜다 → 탭·요청 경합
async function apiCall(input: RequestInfo) {
  let r = await fetch(input, { credentials: "include" });
  if (r.status === 401) { await fetch("/bff/refresh", { method: "POST", credentials: "include" }); r = await fetch(input, { credentials: "include" }); }
  return r;
}

// 고친 판: 탭 안에서는 진행 중 Promise 공유, 탭 사이에서는 Web Locks로 차례대로(한 번으로 합치려면 아래 확인을 잠금 안에 추가)
let inflight: Promise<void> | null = null;
function refreshOnce(): Promise<void> {
  inflight ??= navigator.locks.request("token-refresh", async () => {
    const r = await fetch("/bff/refresh", { method: "POST", credentials: "include" });
    if (!r.ok) throw new Error("refresh failed: " + r.status);      // 실패를 숨기지 않는다 → 로그인 화면
  }).finally(() => { inflight = null; });
  return inflight;
}
```

- 잠금을 기다린 탭은 잠금 안에서 "이미 다른 탭이 갱신했는지"를 확인하고 건너뛰게 만든다(예: 쿠키·BroadcastChannel로 갱신 시각 공유).
- BFF를 쓰면 이 경합은 브라우저가 아니라 BFF 서버 안의 문제가 된다. BFF가 세션별로 갱신을 직렬화한다.

### 4. 리소스 서버 — 강제 만료 반영

```java
// 서명·exp 검증 뒤 한 줄 더: 사용자 valid_after보다 먼저 발급된 토큰 거부
Instant validAfter = validAfterCache.get(jwt.getSubject());      // 짧은 TTL 캐시
if (validAfter != null && jwt.getIssuedAt().isBefore(validAfter))
    throw new InvalidBearerTokenException("token issued before valid_after");   // 401
```

- 비밀번호 변경·"전체 기기 로그아웃" 처리: `valid_after = now()` 기록 + 해당 사용자 refresh 패밀리 전체 폐기 + BFF 세션 삭제.
- 캐시 TTL만큼은 늦게 반영된다. 토큰은 `exp`가 지나면 어차피 거부되므로, 최대 지연은 access 수명(5~10분 (예시))과 캐시 TTL 중 **작은** 쪽이다.

### 5. 진단 — 응답과 로그 읽기

```text
  POST /oauth2/token  grant_type=refresh_token
  HTTP/1.1 400   {"error":"invalid_grant"}       ← RFC 6749 §5.2: 무효·만료·폐기된 refresh
  → 서버 로그에서 이유를 가린다: unknown / expired / revoked / reuse_detected

  "reuse_detected"가 한 사용자에게 몇 초 간격으로 여러 번  → 탭 경합 의심(클라이언트 단일 비행 누락)
  "reuse_detected"가 다른 IP·UA에서, 몇 시간 뒤            → 탈취 의심(사고 대응)
```

## 장애 시나리오와 대처

### 1. 탭 여러 개 동시 갱신 → 정상 사용자 전원 로그아웃 (⚠)

- **현상**: 배포 직후부터 "자꾸 로그아웃된다" 문의가 몰린다. 탭을 여러 개 쓰는 사용자에게 집중된다.
- **보이는 형태**: 토큰 엔드포인트 400 `invalid_grant` 급증, 서버 로그 `refresh_reuse`가 같은 사용자·같은 IP에서 수백 ms 간격으로. 브라우저 네트워크 탭에 `/refresh` 요청이 동시에 여러 개.
- **원인**: 회전 + 재사용 탐지를 켰는데 클라이언트는 401마다 각자 갱신한다(실험 3, 유예 0초).
- **대처**: 클라이언트 단일 비행(Web Locks·진행 중 Promise 공유). 서버에 짧은 유예 창(직전 토큰만). BFF로 옮기면 서버에서 직렬화. 유예 창은 탐지를 약하게 하므로 몇 초 단위로 둔다.

### 2. 비밀번호 변경 후에도 기존 refresh 토큰이 유효 (⚠)

- **현상**: 계정 탈취 신고 → 사용자가 비밀번호를 바꿨는데 공격자 세션이 계속 API를 호출한다.
- **보이는 형태**: 비밀번호 변경 시각 이후에도 같은 패밀리의 갱신 성공 로그가 다른 IP에서 이어진다.
- **원인**: 비밀번호 변경이 자격 증명만 바꾸고, 이미 발급된 refresh 패밀리·세션을 건드리지 않았다.
- **대처**: 비밀번호 변경·MFA 재설정·"전체 로그아웃" 때 사용자 refresh 패밀리 전체 폐기(RFC 9700 §4.14.2 MAY), `valid_after` 갱신, BFF 세션 삭제. 남은 access 토큰 창(실험 4의 539초)을 `valid_after` 검사로 닫는다.

### 3. 긴 수명 access 토큰 탈취 → 만료까지 무방비 (⚠)

- **현상**: 유출된 토큰으로 며칠간 API 호출. 폐기했는데도 계속 된다.
- **보이는 형태**: 디코드한 JWT의 `exp - iat`이 수일, 리소스 서버는 인가 서버에 묻지 않는다.
- **원인**: 자기 포함 토큰은 리소스 서버가 서명·`exp`만 본다. 폐기가 전달되지 않는다(RFC 7009 3절).
- **대처**: access 수명을 분 단위로, 갱신은 refresh로. 즉시성이 필요한 API는 introspection(RFC 7662) 또는 `jti` 폐기 목록(TTL = 남은 수명)·`valid_after`.

### 4. localStorage 저장 → XSS 한 번에 탈취 (⚠)

- **현상**: 서드 파티 스크립트 변조 뒤 여러 계정이 다른 IP에서 쓰였다.
- **보이는 형태**: 같은 시각대 여러 사용자의 refresh 재사용 탐지, 또는 (회전이 없으면) 아무 신호 없음.
- **원인**: refresh 토큰을 localStorage에 뒀다. 같은 출처 스크립트는 다 읽는다(RFC 10017 §8.5).
- **대처**: BFF로 옮겨 브라우저에 토큰을 두지 않는다(§6.1). 당장은 refresh를 브라우저에 두지 않고 메모리 access만, CSP로 스크립트 출처 제한(19번). 퍼진 토큰은 패밀리 폐기.

### 5. 회전 응답 유실 → 다음 갱신이 재사용으로 판정

- **현상**: 모바일 앱이 터널·엘리베이터에서 나오면 로그아웃돼 있다.
- **보이는 형태**: 서버는 RT2를 발급했는데 클라이언트 로그에는 응답 타임아웃. 다음 요청은 RT1로 → `reuse_detected`.
- **원인**: 서버는 RT1을 used로 표시했지만 새 토큰이 클라이언트에 닿지 않았다.
- **대처**: 직전 토큰 재시도를 짧은 유예 창으로 허용(Auth0 leeway 문서가 드는 이유가 네트워크 재시도). 클라이언트는 새 토큰을 받으면 먼저 저장하고 나서 쓴다.

## 핵심 문장

- refresh 토큰은 오래 사는 전체 권한이라 가장 비싼 비밀이다. public client라면 회전(재사용 탐지) 또는 키 결박이 필요하다(RFC 9700 §4.14.2 MUST).
- 회전된 토큰이 다시 오면 서버는 누가 냈는지 모르므로 패밀리 전체를 폐기한다. 정상 사용자도 재로그인한다.
- 동시 갱신 경합은 탈취와 똑같이 보인다. 클라이언트 단일 비행과 짧은 유예 창으로 막는다.
- refresh는 서버 상태라 즉시 폐기되지만, 자기 포함 access는 `exp`까지 산다. 짧은 수명·`valid_after`·introspection으로 그 창을 닫는다.
- 회전은 수명을 늘리지 않아야 한다(RFC 10017 §6.3.2.3). 처음 정한 최종 만료를 물려주는지 라이브러리 동작을 확인한다.
- 브라우저에 토큰을 두면 XSS 앞에서 저장소 선택으로는 한계가 있다. BFF는 토큰을 브라우저 밖에 둔다.

## 관련 주제·근거

- 선행·후속
  - [security 11 sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md)(HttpOnly·Secure·SameSite)·[12 tokens-and-jwt](../12-tokens-and-jwt/2-summary.md)(서명·exp·폐기 불가)·[14 oauth2-and-oidc](../14-oauth2-and-oidc/2-summary.md)·[19 xss-and-csp](../19-xss-and-csp/2-summary.md)·[26 security-logging-and-audit](../26-security-logging-and-audit/2-summary.md)
  - [15-access-control-models](../15-access-control-models/2-summary.md) — 권한 회수가 늦게 반영되는 문제
  - [16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md) — 토큰 값도 추측 불가해야 한다(CSPRNG)
- 연결
  - [web-platform/06-browser-storage](../../web-platform/06-browser-storage/2-summary.md) — HttpOnly 쿠키 vs localStorage 가시성 실험
  - [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md) — BFF 패턴
  - [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md) — 조건부 UPDATE
  - [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md) — 단일 비행
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 400·401 의미
- 1차 출처
  - RFC 9700 Best Current Practice for OAuth 2.0 Security(BCP 240, 2025-01) — §4.14.1 refresh가 표적인 이유, §4.14.2 sender-constrained 또는 회전(public client MUST), 구현 노트, 보안 사건 시 폐기 MAY, 비활성 만료 SHOULD <https://www.rfc-editor.org/rfc/rfc9700>
  - RFC 6749 — §5.2 `invalid_grant`(HTTP 400), §6 refresh 요청과 "옛 토큰을 버려야 한다 MUST", §10.4 회전 예시 <https://www.rfc-editor.org/rfc/rfc6749>
  - RFC 10017 OAuth 2.0 for Browser-Based Applications(BCP 212, 2026-08 — 커리큘럼이 IETF 초안으로 적은 문서의 발행판) — §5.1.1~5.1.4 공격 시나리오, §6 세 구조, §6.1 BFF, §6.1.2.2 세션 수명, §6.1.3.2 쿠키 요구, §6.3.2.3 회전 시 수명 연장 금지와 8시간 예, §8.4·8.5 저장소 <https://www.rfc-editor.org/rfc/rfc10017>
  - RFC 7009 Token Revocation — §2 refresh 폐기 MUST·access SHOULD, §2.1 연관 토큰 폐기, §3 자기 포함 토큰의 한계 <https://www.rfc-editor.org/rfc/rfc7009>
  - RFC 7662 Token Introspection(`active`) <https://www.rfc-editor.org/rfc/rfc7662>
  - Auth0 Docs — Refresh Token Rotation(패밀리 폐기, 재사용 로그) <https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation> · Configure Refresh Token Rotation(leeway: 초 단위, 기본 꺼짐, 직전 토큰만) <https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-rotation>
  - MDN Web Locks API(같은 출처 탭·워커 간 잠금, 2022-03부터 널리 사용 가능, 보안 컨텍스트) <https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API>
  - spring-authorization-server 저장소(README: Spring Security 7.0으로 이관) `TokenSettings`·`OAuth2RefreshTokenAuthenticationProvider` 소스, Spring Security main `TokenSettings`(같은 기본값) <https://github.com/spring-projects/spring-authorization-server>
- 실험: `RefreshDemo.java`(OpenJDK 21.0.12, 컨테이너 `--network none`, 3회) — 회전·최종 만료 고정, 탈취 재사용 → 패밀리 폐기, 탭 경합(유예 0초/10초)과 단일 비행, 비밀번호 변경 후 refresh 거부와 access 잔존·`valid_after`, 8시간 최종 만료
