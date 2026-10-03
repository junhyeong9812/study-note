# api-design/14-rate-limit-and-quota-contracts — 속도 제한·쿼터의 계약: 제한 키, 429와 Retry-After, RateLimit 헤더, 클라이언트 동작 — 정리 (힌트)

## 해결하는 문제

리미터를 **어떻게 세는가**(토큰 버킷·슬라이딩 창·분산 카운터)는 [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)에서 다뤘다. 이 노트는 그 리미터를 **API 계약으로 어떻게 드러내는가**를 본다.

계약이 없으면 이렇게 된다.

```text
  서버: 초당 5건 넘으면 429      클라이언트: "429? 다시 보내 보자" (즉시)
     │                                │
     └─── 429 ─── 429 ─── 429 ─── 429 ┘  ← 거절도 요청이다. 서버는 거절하느라 바쁘다
  다른 문제
  - 누구 몫으로 세나? IP? 계정? 회사 NAT 뒤 300명이 IP 하나를 쓰면?
  - 언제 다시 보내면 되나? 1초? 1시간?
  - "월 10만 건 요금제 초과"와 "지금 서버가 바쁘다"는 같은 429인가?
```

- *속도 제한(rate limit)*: 시간 창 안의 요청 수를 제한하는 것. 짧은 창(초·분)이 많다.
- *쿼터(quota)*: 더 긴 기간(일·월)의 사용량 할당. 요금제·계약과 묶이는 경우가 많다.
- *스로틀(throttle)*: 보호 목적으로 속도를 떨어뜨리거나 거절하는 것.

쉬운 예: 놀이공원이다.
- 자유이용권(쿼터)은 "오늘 하루 탈 수 있는 횟수"다. 다 쓰면 내일까지 못 탄다.
- 놀이기구 줄 입구 직원(스로틀)은 "지금 한 번에 들어갈 수 있는 인원"을 막는다. 잠깐 기다리면 들어간다.
- 직원이 "10분 뒤 오세요"라고 말해 주면(Retry-After) 손님이 입구에서 계속 밀지 않는다.

똑같은 구조다.

실무 예: GitHub REST API는 인증 없는 요청에 시간당 60건, 인증한 사용자에 시간당 5,000건(GitHub 문서). Stripe는 라이브 모드 계정당 초당 100건(전역)과 엔드포인트별 초당 25건, 그리고 별도로 "거래 1건당 평균 읽기 500건, 30일 이동 창"이라는 읽기 할당을 둔다(Stripe 문서, 2026-10-04 열람).

## 동작·원리

### 1. 제한 키 — 누구 몫으로 세나

```text
  요청 ──> 키 추출 ──> 키별 버킷 ──> 통과 / 429

  키 후보               잘 맞는 곳                      약점
  ─────────────        ──────────────────────          ─────────────────────────────
  IP                   인증 전 엔드포인트, 봇 방어       NAT·프록시 뒤 여러 명이 한 IP
  사용자·계정           로그인한 사용자 API              계정을 여러 개 만들면 우회
  API 키·앱            서버 간 연동, 요금제              키 하나를 여러 서비스가 공유
  테넌트(회사)          B2B SaaS 공정성                  큰 테넌트 안에서 다시 나눠야 함
  (키, 엔드포인트)       비싼 엔드포인트만 따로            키 수가 곱해진다
```

- 보통 여러 층을 겹친다: "IP당 넉넉한 한도(미인증 보호) + 키당 요금제 한도 + 비싼 엔드포인트 별도 한도 + 전역 보호 한도".
- RFC 6585 §4는 429를 정의하면서 **서버가 사용자를 어떻게 식별하고 어떻게 세는지는 정하지 않는다**고 명시한다(인증 정보·쿠키·리소스 단위·서버 전체 등 예시만 든다). 키 선택은 API 설계자의 몫이다.
- 로그인처럼 공격 표적인 엔드포인트는 키를 다르게 잡는다. OWASP Authentication Cheat Sheet는 로그인 실패 카운터를 **IP가 아니라 계정에** 붙이라고 한다(여러 IP로 나눠 공격하는 것을 막기 위해). 동시에 잠금이 남의 계정을 잠그는 서비스 거부 수단이 되지 않게 주의하라고 적는다.

### 2. 429와 Retry-After — 표준이 정한 만큼

```text
  HTTP/1.1 429 Too Many Requests
  Retry-After: 30                      ← 30초 뒤에 다시 (또는 HTTP-date)
  Content-Type: application/problem+json

  {"type": "...#quota-exceeded", "title": "...", "violated-policies": ["default"]}
```

- RFC 6585 §4(2012, Standards Track)
  - 429 = "주어진 시간에 너무 많은 요청을 보냈다".
  - 응답 표현은 상황 설명을 담아야 한다(SHOULD). `Retry-After`는 담을 수 있다(MAY) — **필수가 아니다**.
  - 429 응답은 캐시에 저장하면 안 된다(MUST NOT).
- RFC 9110 §10.2.3 `Retry-After`: HTTP-date 또는 초. 503과 함께면 "얼마나 오래 쓸 수 없을지", 3xx와 함께면 "리다이렉트 전에 기다릴 최소 시간".
- 429 vs 503
  - 429: **이 클라이언트**가 너무 많이 보냈다. 다른 클라이언트는 괜찮을 수 있다.
  - 503: **서버**가 지금 처리할 수 없다(과부하·점검). RFC 9110 §15.6.4.
  - nginx `limit_req`는 기본으로 503을 돌려준다(`limit_req_status` 기본 503) → 의도가 클라이언트별 제한이면 429로 바꾼다(reliability/11 「4. nginx」).
- 회사마다 다르다
  - GitHub 문서: 1차·2차 한도를 넘으면 **403 또는 429**를 받는다. 1차 한도는 `x-ratelimit-remaining`이 0이고 `x-ratelimit-reset` 시각까지 기다리라고 한다. 2차 한도는 `retry-after`가 있으면 그만큼, 없고 `x-ratelimit-remaining`이 0이면 reset 시각까지, 둘 다 아니면 최소 1분 기다리고, 계속 실패하면 지수로 늘려 가다 횟수 상한에서 멈추라고 한다. 한도 중에 계속 요청하면 연동이 차단될 수 있다고 경고한다.
  - Stripe 문서: 속도 제한 429에는 `Stripe-Rate-Limited-Reason` 헤더(`global-rate`, `endpoint-rate`, `global-concurrency`, `endpoint-concurrency`, `resource-specific`)가 붙는다. 이 헤더 **없는** 429는 속도 제한이 아니다 — 객체 잠금 타임아웃(`lock_timeout`)일 수 있다.

### 3. RateLimit 헤더 — 초안 단계

```text
  RateLimit-Policy: "burst";q=100;w=60,"daily";q=1000;w=86400     ← 정책: 60초에 100, 하루 1000
  RateLimit: "burst";r=50;t=30                                     ← 지금: 50 남음, 30초 안에

  q  = quota(할당량)            w = window(창, 초)
  r  = remaining(남은 양)       t = 유효 창(초)       pk = partition key(어느 몫인가)
```

- IETF `draft-ietf-httpapi-ratelimit-headers-11`(2026-05-23 게시, 2026-11-24 만료, **초안**) 기준. RFC가 아니다. 판이 바뀌면 이름·문법이 바뀔 수 있다.
  - `RateLimit-Policy`: 서버의 쿼터 정책(여러 개 가능).
  - `RateLimit`: 지금 남은 양(`r`)과 그 양을 써야 하는 초(`t`).
  - 클라이언트 쪽 규칙(초안 7절): 양수 `r`이 다음 요청 성공을 보장하지 않는다. 다음 응답에도 이 헤더가 있다고 가정하면 안 된다(MUST NOT). 형식이 틀린 헤더는 무시해야 한다(MUST). `Retry-After`와 같이 오면 **`Retry-After`가 우선**이다(MUST).
  - 서버 쪽 규칙(6절): 상태 코드와 상관없이 보낼 수 있다. 과부하·DoS 때는 값을 임의로 낮출 수 있다.
  - 문제 유형(5절): `…#quota-exceeded`, `…#temporary-reduced-capacity`, `…#abnormal-usage-detected`. RFC 9457 problem details 본문에 `violated-policies`를 싣는다 → [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md).
  - 보안(8절): 남은 용량 정보가 공격자에게 서버 포화 시점을 알려 줄 수 있다. 401·403도 쿼터를 깎으면 남의 트래픽을 엿볼 수 있다.
- 지금 널리 쓰는 비표준 헤더(실측):

(실험, curl로 api.github.com 인증 없이 1회 조회, 2026-10-04 KST)

```text
HTTP/2 200 
date: Sat, 03 Oct 2026 19:26:44 GMT
x-ratelimit-limit: 60
x-ratelimit-remaining: 55
x-ratelimit-used: 5
x-ratelimit-resource: core
x-ratelimit-reset: 1791058648
```

- `x-ratelimit-reset`은 **시각**(유닉스 초)이고, 초안의 `t`는 **남은 초**다. 초안은 시계 동기화에 기대지 않고 많은 클라이언트가 같은 시각에 몰리는 것을 줄이려고 초를 택했다고 설명한다(4.1.2).

### 4. 요금제 쿼터 vs 보호용 스로틀

| | 요금제 쿼터 | 보호용 스로틀 |
|---|---|---|
| 목적 | 사업(얼마나 쓸 권리가 있나) | 시스템 보호(지금 버틸 수 있나) |
| 창 | 일·월 | 초·분, 동시 실행 수 |
| 값을 바꾸는 사람 | 영업·요금제 | 운영(부하에 따라 즉시) |
| 넘으면 | 429/402·업그레이드 안내, 다음 주기까지 | 429/503 + 짧은 Retry-After |
| 공개 | 문서에 고정 값 | "바뀔 수 있음"으로만 |
| 예 | Stripe 읽기 할당(거래당 500, 30일) | Stripe 초당 100건, 동시 실행 한도 |

- 둘을 한 카운터로 섞으면 "요금제는 남았는데 과부하라 거절"과 "요금제를 다 썼다"를 클라이언트가 구분하지 못한다. 응답에 어떤 정책을 넘었는지 적는다(초안의 `violated-policies`, Stripe의 `Stripe-Rate-Limited-Reason`).
- 쿼터는 과금과 묶이므로 정확해야 하고, 스로틀은 빨라야 한다. 저장소도 달라지는 경우가 많다(해석): 쿼터는 DB·정산 집계, 스로틀은 메모리·Redis.

### 5. 클라이언트 동작 계약

```text
  응답 받음
    ├─ 2xx: RateLimit의 r·t를 보고 속도를 미리 줄인다(선택)
    ├─ 429 + Retry-After: 그 시간까지 기다린다 (지터를 조금 더한다)
    ├─ 429, Retry-After 없음: 지수 백오프 + 지터, 재시도 상한
    └─ 503 + Retry-After: 같은 규칙. 재시도 예산 안에서만
```

- 문서에 적을 것: 재시도해도 되는 상태 코드, `Retry-After` 준수, 최소·최대 대기, 재시도 상한, 멱등하지 않은 요청의 재시도 조건(→ [05-idempotency-keys](../05-idempotency-keys/2-summary.md)).
- Stripe 문서는 429에 지수 백오프 + 무작위성을 권하고, 더 나아가 클라이언트 쪽 토큰 버킷으로 전체 송신량을 조절하라고 권한다.
- 공식 SDK에 이 규칙을 넣어 두면 대부분의 클라이언트가 따른다. 문서만 있으면 각자 다르게 구현한다(해석).

### 실험: Retry-After 무시 vs 준수, 제한 키, 테넌트 공정성

JDK 21 단일 파일. 서버는 `com.sun.net.httpserver`에 API 키별 토큰 버킷(용량 5, 초당 5개 충전)을 두고, 넘으면 `429` + `Retry-After` + 초안 형식 `RateLimit` 헤더 + problem 본문을 준다. 클라이언트는 JDK `HttpClient`로 같은 프로세스 안에서 부른다.

```java
synchronized long tryTake() {                       // 0 = 통과, 양수 = 다음 토큰까지 기다릴 초(올림)
    long now = System.nanoTime();
    tokens = Math.min(cap, tokens + (now - last) / 1e9 * rate); last = now;
    if (tokens >= 1) { tokens -= 1; return 0; }
    return (long) Math.ceil((1 - tokens) / rate);
}
// 핸들러
h.set("RateLimit-Policy", "\"default\";q=5;w=1");
h.set("RateLimit", "\"default\";r=" + b.remaining() + ";t=1");
if (wait > 0) { h.set("Retry-After", String.valueOf(wait)); /* 429 + problem+json */ }
// A. 성공 20건이 필요한 클라이언트
while (ok < 20) {
    var r = c.send(req(key), HttpResponse.BodyHandlers.discarding());
    if (r.statusCode() == 200) { ok++; continue; }
    if (mode.equals("준수")) Thread.sleep(Long.parseLong(r.headers().firstValue("Retry-After").orElse("1")) * 1000);
}
```

- B는 회사 NAT 뒤 300명(사용자당 3건)이 IP 하나를 쓸 때, 한도 "키당 100건"을 IP 키와 API 키로 각각 셌다.
- C는 창 하나 100건을 테넌트 A(1000건 몰아 보냄)와 B(10건)가 공유할 때와, 테넌트당 50건으로 나눴을 때를 셌다.

(실험, JDK 21.0.12 eclipse-temurin, `--network none`, `--cpus=2`, 3회 실행, 2026-10-04)

```text
7번째 응답: 429 Retry-After=1 RateLimit="default";r=0;t=1 body={"type":"https://iana.org/assignments/http-problem-types#quota-exceeded","title":"quota exceeded","violated-policies":["default"]}
A Retry-After 무시: 성공 20건까지 3.0s, 서버가 받은 요청 84, 그중 429 64
A Retry-After 준수: 성공 20건까지 3.2s, 서버가 받은 요청 23, 그중 429 3
B IP 키: 429를 한 번 이상 받은 사용자 267/300, API 키: 0/300
C 공유 한도 100: A 성공 99, B 성공 1/10
C 테넌트별 한도 50: A 성공 50, B 성공 10/10
```

- 실행마다 조금 다르다. 집필 3회 + 사실 점검 8회(같은 코드·이미지)에서 첫 429는 6번째(3회) 또는 7번째(나머지), A 무시 쪽은 3.0~3.1초·요청 84~85·429 64~65, 준수 쪽은 매번 3.2초·23·3, B·C는 매번 같았다. 위 블록은 그중 한 실행이다.
- 관찰
  - 6~7번째에서 첫 429: 용량 5 + 첫 호출들 사이에 충전된 0~1개(첫 호출이 느린 정도에 따라 다르다).
  - A: 즉시 재시도는 **빨라지지 않았다**(3.0초 vs 3.2초). 성공 속도는 충전 속도(초당 5)가 정한다. 대신 서버가 받은 요청은 84 대 23으로 약 3.7배, 그중 429가 64건이다(다른 실행에서 85·65). 이 환경에서 무시 쪽 루프는 요청 왕복 시간에 묶였다(3.0초/84건 ≈ 36ms, 계산값). 클라이언트가 많거나 왕복이 짧으면 거절 처리 부하가 더 커진다.
  - B: IP로 세면 앞의 33명 남짓만 통과하고 267명이 막혔다. 같은 사람들을 API 키로 세면 아무도 막히지 않는다(커리큘럼 ⚠ "회사 NAT 뒤 수백 명").
  - C: 공유 한도에서 A가 99건을 쓰고 B는 10건 중 1건만 성공했다. 테넌트별로 나누면 B는 10건 모두 성공한다(커리큘럼 ⚠ "테넌트 하나가 공유 한도를 독점").
- 한계: B·C는 HTTP 없이 카운터만 센 계산 실험이다. A의 수치는 이 컨테이너 환경(CPU 2개 제한, 루프백)의 값이다.

## 쓰이는 자료구조·알고리즘

- **토큰 버킷** — 용량(버스트)과 충전 속도(평균)를 따로 정한다. `Retry-After`는 "다음 토큰까지 남은 시간"을 올림한 값으로 계산할 수 있다(실험 코드의 `tryTake`) → [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md).
- **키별 카운터 해시** — 키 → 버킷/카운터. 키 수가 무한히 늘지 않게 만료(TTL)·LRU를 둔다(IP 키는 특히) → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **슬라이딩 창 카운터** — 쿼터(일·월)에 쓰는 경우가 많다. 경계 2배 버스트 문제는 reliability/11 실험 A·B.
- **계층 한도(여러 버킷을 모두 통과)** — 요청 하나가 "IP 버킷 AND 키 버킷 AND 엔드포인트 버킷"을 모두 통과해야 한다. 어느 하나라도 거절하면 거절하고, 거절한 정책 이름을 응답에 싣는다.
- **클라이언트 쪽 토큰 버킷** — 같은 알고리즘을 송신 측에 두어 서버 한도보다 조금 낮게 보낸다(Stripe 권고).

## 적용 — 풀어나가는 법

### 1. 순서

1. 보호할 자원과 사업 단위를 나눈다: 스로틀(초·동시성)과 쿼터(일·월)를 다른 정책으로 둔다.
2. 키를 정한다: 인증된 요청은 API 키·사용자·테넌트, 인증 전은 IP(넉넉하게), 로그인은 계정 + IP 조합.
3. 비싼 엔드포인트(검색·내보내기·리스트+확장)는 따로 한도를 둔다.
4. 429 응답 형식을 고정한다: `Retry-After`(넣는 것을 기본으로), 어떤 정책을 넘었는지, problem details 본문.
5. 남은 양 헤더를 줄지 정한다: 초안 `RateLimit`/`RateLimit-Policy` 또는 사실상 표준 `X-RateLimit-*`. 초안을 쓰면 판 번호를 문서에 적는다.
6. 클라이언트 계약과 SDK: `Retry-After` 준수, 백오프 + 지터, 재시도 상한.
7. 리미터 장애 시 동작(fail open/closed)을 정책별로 정한다(reliability/11 장애 5).

### 2. 서버 — 응답 헤더를 붙이는 필터 (Java)

```java
Decision d = limiter.check(keyOf(req), endpointOf(req));      // 여러 정책을 모두 검사
res.setHeader("RateLimit-Policy", d.policyHeader());          // 예: "per-key";q=100;w=60
res.setHeader("RateLimit", d.remainingHeader());              // 예: "per-key";r=37;t=21
if (!d.allowed()) {
    res.setStatus(429);
    res.setHeader("Retry-After", String.valueOf(Math.max(1, d.retryAfterSeconds())));
    res.setContentType("application/problem+json");
    res.getWriter().write("""
        {"type":"https://iana.org/assignments/http-problem-types#quota-exceeded",
         "title":"요청 한도를 넘었습니다","violated-policies":["%s"]}""".formatted(d.violatedPolicy()));
    return;
}
chain.doFilter(req, res);
```

- `keyOf`는 인증을 마친 뒤의 주체(API 키·테넌트)를 쓴다. 인증 전에 돌아야 하는 IP 한도는 앞단(게이트웨이·nginx)에 둔다.
- 프록시 뒤라면 실제 클라이언트 IP를 `X-Forwarded-For`에서 꺼내되, **믿을 수 있는 프록시가 붙인 마지막 값**만 쓴다. 클라이언트가 직접 넣은 값을 믿으면 키를 마음대로 바꿔 우회한다.

### 3. 클라이언트 — 429 처리 (JDK `HttpClient`)

```java
for (int attempt = 0; attempt < 5; attempt++) {
    HttpResponse<String> r = http.send(request, BodyHandlers.ofString());
    if (r.statusCode() != 429 && r.statusCode() != 503) return r;
    Duration wait = r.headers().firstValue("Retry-After")
        .map(RetryAfter::parse)                                         // 초 또는 HTTP-date
        .orElse(Duration.ofMillis((long) (500 * Math.pow(2, attempt))));
    Thread.sleep(wait.plusMillis(ThreadLocalRandom.current().nextLong(250)));   // 지터
}
throw new RateLimitedException("재시도 상한 초과");
```

- `POST`처럼 멱등하지 않은 요청은 429·503이라도 서버가 처리하지 않았다는 보장이 문서에 있을 때만, 또는 멱등 키를 실었을 때만 재시도한다. Stripe의 `lock_timeout` 429는 "처리하지 않았다"고 문서에 적혀 있다.

### 4. 진단

```bash
curl -s -o /dev/null -D - https://api.github.com/zen | grep -i '^x-ratelimit\|^retry-after'   # 남은 양 확인
```

- 지표: 정책·키별 429 수, 429 비율 상위 키(특정 고객이 계속 맞나), 429 직후 같은 키의 재요청 간격(Retry-After를 지키나), 리미터 지연·오류율.
- "IP 하나에 계정 수백 개" 패턴이 보이면 IP 키가 NAT를 때리는 중이다.

## 장애 시나리오와 대처

### 1. IP 기준 제한 → 회사 NAT 뒤 수백 명이 한꺼번에 차단 (⚠ 커리큘럼)

- 현상: 고객사 한 곳의 직원 전원이 오전 9시에 429를 받는다.
- 보이는 형태: 429가 한 IP에 몰리고, 그 IP 뒤 계정이 수백 개(실험 B: 300명 중 267명 차단).
- 원인: 인증된 API까지 IP를 제한 키로 썼다.
- 대처: 인증된 요청은 API 키·사용자·테넌트로 센다. IP 한도는 인증 전 경로에만, 넉넉하게. 대형 고객은 테넌트 한도를 계약으로 정한다 → reliability/11 장애 4.

### 2. `Retry-After` 없는 429 → 즉시 재시도 폭주 (⚠ 커리큘럼)

- 현상: 리미터를 켠 뒤 요청 수가 오히려 늘고 429 비율이 대부분을 차지한다.
- 보이는 형태: 같은 키가 429 직후 수십 ms 안에 다시 요청한다(실험 A 무시 쪽: 약 84건 중 64건이 429).
- 원인: 응답에 `Retry-After`가 없고(RFC 6585에서 MAY라 빠뜨리기 쉽다), 클라이언트에 백오프가 없다.
- 대처: 429에 `Retry-After`를 넣고 SDK가 따르게 한다(실험 A 준수 쪽: 23건). 계속 무시하는 키는 더 긴 차단으로 올린다(GitHub는 차단 가능성을 문서에 적는다).

### 3. 로그인 엔드포인트를 전역 한도에 묶음 → 공격 중 정상 사용자 로그인 불가 (⚠ 커리큘럼)

- 현상: 크리덴셜 스터핑 공격이 시작되자 일반 사용자도 로그인하지 못한다.
- 보이는 형태: `/login` 429가 일반 사용자에게 고르게 퍼진다. 공격 IP 수천 개.
- 원인: `/login` 전체에 한도 하나를 걸었다. 공격 트래픽이 그 한도를 다 먹었다.
- 대처: 실패 카운터를 계정에 붙이고(OWASP), IP별·계정별 한도를 따로 둔다. 잠금 기간은 고정값 대신 짧게 시작해 실패마다 두 배로 늘리는 지수 잠금도 있다(OWASP가 "일부 애플리케이션이 쓰는" 방식으로 소개). 잠금이 남의 계정을 잠그는 서비스 거부 수단이 되지 않게, OWASP는 잠긴 계정도 비밀번호 찾기 기능으로는 들어올 수 있게 하는 방법을 예로 든다. 봇 판별·CAPTCHA 같은 별도 방어를 앞에 둔다.

### 4. 테넌트 하나가 공유 한도를 독점 (⚠ 커리큘럼)

- 현상: 고객사 A의 대량 동기화가 시작되자 다른 고객들이 간헐적으로 429를 받는다.
- 보이는 형태: 전역 한도 429가 여러 테넌트에 나오는데, 사용량 상위 1개 테넌트가 대부분을 차지한다(실험 C: 공유 한도에서 B 성공 1/10).
- 원인: 한도가 서비스 전체에 하나뿐이다.
- 대처: 테넌트별 한도를 두고, 전역 한도는 그 합보다 큰 최후 보호선으로만 쓴다(실험 C: B 성공 10/10). 대량 작업은 별도 큐·낮은 우선순위로 보낸다 → [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md).

### 5. 429인데 속도 제한이 아니었다

- 현상: 재시도 간격을 늘려도 특정 객체에 대한 429가 계속된다.
- 보이는 형태: Stripe에서 `Stripe-Rate-Limited-Reason` 헤더 없는 429, 코드 `lock_timeout`.
- 원인: 같은 객체에 동시 변경을 보내 객체 잠금 경합이 났다.
- 대처: 같은 객체 변경을 직렬화한다(Stripe 문서). 응답 헤더로 원인을 나눠 처리한다. 우리 API도 "속도 제한 429"와 "다른 사유 429"를 헤더·problem type으로 구분해 준다.

### 6. 쿼터 소진을 과부하처럼 응답

- 현상: 월 쿼터를 다 쓴 고객의 SDK가 몇 초마다 계속 재시도한다.
- 보이는 형태: 같은 키의 429가 몇 주 동안 이어진다. `Retry-After: 1`.
- 원인: 쿼터 초과와 스로틀을 같은 응답으로 줬다. 클라이언트는 "곧 풀린다"로 읽었다.
- 대처: 쿼터 초과는 다음 주기 시작까지의 `Retry-After`(또는 HTTP-date)와 `quota-exceeded` 유형, 업그레이드 안내 링크를 준다. 정책 이름을 싣는다.

## 핵심 문장

- 리미터의 계산법과 별개로, 누구 몫으로 세는지(제한 키)·넘으면 무엇을 돌려주는지·클라이언트가 어떻게 해야 하는지가 API 계약이다.
- RFC 6585는 429에 `Retry-After`를 MAY로만 둔다. 계약에서는 넣는 쪽을 기본으로 하고, 클라이언트 SDK가 그것을 따르게 한다.
- 즉시 재시도는 성공을 앞당기지 못하고 거절 처리만 늘린다(실험: 같은 3초 남짓, 요청 약 84 대 23).
- 인증된 요청은 IP가 아니라 API 키·사용자·테넌트로 센다. 로그인은 계정에 실패 카운터를 붙인다.
- 요금제 쿼터와 보호용 스로틀은 다른 정책이다. 응답에 어떤 정책을 넘었는지 적는다.
- `RateLimit` 헤더는 2026-10 현재 IETF 초안(-11)이다. 쓰면 판 번호를 적고, 클라이언트는 남은 양을 보장으로 읽지 않는다.

## 관련 주제·근거

- 선행
  - [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) — 4xx/5xx 선택, 429·503
  - [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) — 토큰 버킷·슬라이딩 창·분산 카운터, nginx `limit_req`, fail open
- 연결
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 429를 받는 쪽의 백오프·재시도 예산
  - [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) — 서버 전체 과부하 셰딩(503)
  - [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md) — 테넌트·작업 종류별 자원 분리
  - [13-long-running-operations](../13-long-running-operations/2-summary.md) — 폴링 폭주를 Retry-After로 조절
  - [10-notification-delivery-pipeline](../10-notification-delivery-pipeline/2-summary.md) — 공급자(FCM 등)의 429를 받는 쪽
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) — 429 뒤 POST 재시도의 안전
- 표준·문서
  - RFC 6585 §4 429 Too Many Requests <https://www.rfc-editor.org/rfc/rfc6585>
  - RFC 9110 §10.2.3 Retry-After · §15.6.4 503 <https://www.rfc-editor.org/rfc/rfc9110>
  - IETF draft-ietf-httpapi-ratelimit-headers-11 (2026-05-23, 초안, 2026-11-24 만료) <https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/>
  - GitHub "Rate limits for the REST API" <https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api> — 60/5,000 per hour, `x-ratelimit-*`, 403 또는 429, 1차는 reset까지·2차는 retry-after→reset→1분 규칙, 차단 경고
  - Stripe "Rate limits" <https://docs.stripe.com/rate-limits> (2026-10-04 열람) — 초당 100(라이브)·25(샌드박스)·엔드포인트 25, 동시 실행 한도, `Stripe-Rate-Limited-Reason`, `lock_timeout`, 읽기 할당 거래당 500/30일, 클라이언트 토큰 버킷 권고
  - Paul Tarjan, "Scaling your API with rate limiters", Stripe 블로그 2017 <https://stripe.com/blog/rate-limiters> (reliability/11에서 정리)
  - OWASP Authentication Cheat Sheet 「Account Lockout」 <https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html>
- 실험 목록
  - Retry-After 무시 vs 준수(A), 제한 키 IP vs API 키(B), 공유 vs 테넌트별 한도(C) — `Rl.java`, eclipse-temurin:21-jdk(21.0.12), `--network none`, `--cpus=2`, 3회(사실 점검에서 8회 재실행)
  - GitHub 응답 헤더 관찰 — 호스트 curl, `https://api.github.com/zen` 인증 없이 1회
