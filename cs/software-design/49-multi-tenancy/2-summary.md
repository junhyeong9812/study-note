# software-design/49-multi-tenancy — 멀티테넌시: 사일로·풀·브리지와 시끄러운 이웃 — 정리 (힌트)

## 해결하는 문제

한 시스템이 여러 고객(테넌트)을 동시에 받는다.
고객마다 시스템을 따로 만들면 비싸고, 다 섞으면 두 가지가 샌다.

```text
 데이터가 샌다                               자원이 샌다
 ─────────────────────────                 ─────────────────────────
 tenant 조건 하나 빠진 조회 → 남의 청구서      큰 고객 배치 하나 → 공용 워커·커넥션 독점
 캐시 키에 tenant 빠짐 → 남의 결과 반환        → 작은 고객 요청이 1초씩 대기
```

- *멀티테넌시(multi-tenancy)*: 한 배포·한 코드로 여러 테넌트를 서비스하면서, 서로의 데이터·자원·조작이 섞이지 않게 하는 설계.
- *테넌트(tenant)*: 격리 단위가 되는 고객(회사·조직·계정).
- *시끄러운 이웃(noisy neighbor)*: 한 테넌트의 활동 때문에 다른 테넌트의 성능이 떨어지는 문제(Azure Architecture Center).

쉬운 예: 아파트 한 동. 세대마다 열쇠가 달라야 하고(데이터 격리), 한 세대가 엘리베이터를 독점하면 안 된다(자원 격리).\
똑같은 구조다.\
실무 예: B2B SaaS가 한 PostgreSQL 테이블에 모든 회사의 청구서를 `tenant_id`로 구분해 넣는다. 대형 고객의 월말 정산 배치가 같은 커넥션 풀을 쓴다.

기초는 원본 [systems/multi-tenancy](../../systems/multi-tenancy/2-summary.md)에 있다.
원본은 격리 4단계(행 → 스키마 → DB → 인스턴스), 권한 누수 경로 L1~L8, 막는 방법의 강도 순서, 리소스 편중과 대응, 스키마 마이그레이션 N회와 expand-contract를 다룬다.
이 노트는 그 위에 **업계 용어(사일로·풀·브리지)의 출처 확인**, **테넌트 키 파티셔닝**, 그리고 두 실패(캐시 키 누락 L6, 시끄러운 이웃)를 **실험으로 재현**한 것을 더한다.

## 동작·원리

### 1. 사일로·풀·브리지 — 자원을 테넌트 전용으로 둘지, 나눠 쓸지

```text
 사일로(silo)                    풀(pool)                        브리지(bridge)
 ┌──────┐ ┌──────┐            ┌────────────────────┐          주문 서비스: 풀
 │ A 앱  │ │ B 앱  │            │ 앱 (모든 테넌트)       │          결제 서비스: 사일로 (규제)
 │ A DB  │ │ B DB  │            │ DB: tenant_id 컬럼    │          검색 서비스: 풀
 └──────┘ └──────┘            └────────────────────┘
 전용 자원, 격리 강함            공유 자원, 규모의 경제            서비스마다 다르게
 비용·운영이 테넌트 수만큼        코드·DB가 격리를 지킨다            규제·시끄러운 이웃 특성으로 고른다
         └────────── 공통: 가입·인증·운영 도구는 하나로 공유 ──────────┘
```

- AWS Well-Architected SaaS Lens "Silo, Pool, and Bridge Models":
  - 사일로 = 테넌트에게 **전용 자원**(전용 스택 전체 또는 전용 DB만).
  - 풀 = 테넌트가 **자원을 공유**(컴퓨트·스토리지·메시징 일부 또는 전부).
  - 브리지 = 둘이 섞인 모드. 예) 어떤 마이크로서비스는 사일로, 다른 것은 풀. 데이터의 규제 성격과 시끄러운 이웃 특성이 사일로 쪽으로, 민첩성·접근 패턴·비용이 풀 쪽으로 기울게 한다고 적는다.
  - 사일로라도 신원·가입·운영은 공유 구조로 관리한다는 점이 "고객마다 따로 돌리는 관리형 서비스"와의 차이라고 적는다.
- Azure Architecture Center "Tenancy models"는 같은 스펙트럼을 자동화된 단일 테넌트 배포 ↔ 완전 멀티테넌트, 그 사이의 **수직 분할**(대부분은 공유, 높은 성능·격리가 필요한 고객만 전용)로 설명한다.
- 원본의 4단계(행·스키마·DB·인스턴스)는 이 스펙트럼을 **데이터 층에서** 더 잘게 나눈 것이다. 행 단위가 풀, DB·인스턴스 분리가 사일로 쪽이다.

### 2. 풀의 데이터 격리 — 조건이 빠지는 곳

```text
 요청 ─> [인증: tenant=acme] ─> 컨트롤러 ─> 서비스 ─> [캐시] ─> 리포지토리 ─> DB
                                                  ↑               ↑            ↑
                                       L6 캐시 키에 tenant?   L1 WHERE에 tenant?  RLS 정책?
```

- 원본의 누수 경로 L1~L8 중 저장소만 봐서는 안 보이는 것이 L6(캐시 키)과 L8(이벤트·로그)이다.
  - 참고: 원본 「새는 경로 여덟」의 "저장소만 보면 절반(L6·L8)은 안 보인다"는 여덟 중 둘을 가리키므로 "절반"이 아니라 "일부(둘)"다. 원본이 같은 절에서 나열한 L6·L8 두 경로가 근거다.
- 아래 실험은 **SQL에는 tenant 조건이 제대로 있는데도** 캐시 한 층에서 새는 경우다.

### 실험 A: 캐시 키에 tenant가 빠지면

```java
// "DB" 조회는 (tenant, id)로만 찾는다 — WHERE tenant_id = ? AND id = ?
static Optional<Invoice> dbFind(String tenant, String id) { ... }

// 잘못: 키 = id   (예: @Cacheable(cacheNames="invoice", key="#id"), 또는 인자가 id 하나뿐인 기본 키)
static Optional<Invoice> findBad(String id) {
    return cache.computeIfAbsent(id, k -> dbFind(currentTenant.get(), id));
}
// 바름: 키 = (tenant, id)
static Optional<Invoice> findGood(String id) {
    String t = currentTenant.get();
    return cache.computeIfAbsent(t + "|" + id, k -> dbFind(t, id));
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/45/e49/CacheKeyLeak.java`, 2026-10-02 — 결정적)

```text
== 캐시 키 = id
  요청 테넌트=acme → Invoice[tenant=acme, id=INV-1, amount=990000]
  요청 테넌트=globex → Invoice[tenant=acme, id=INV-1, amount=990000]
  DB 조회 수=1, 캐시 키=[INV-1]
== 캐시 키 = tenant|id
  요청 테넌트=acme → Invoice[tenant=acme, id=INV-1, amount=990000]
  요청 테넌트=globex → Invoice[tenant=globex, id=INV-1, amount=15000]
  DB 조회 수=2, 캐시 키=[acme|INV-1, globex|INV-1]
```

- 관찰 1 — globex의 요청이 acme의 청구서(99만 원)를 받았다. DB는 한 번만 조회됐다. **두 번째 요청은 tenant 조건이 있는 SQL에 닿지도 않았다.**
- 관찰 2 — 키에 tenant를 넣자 DB 조회가 2번으로 늘고 각자 자기 것을 받았다. 격리의 대가로 캐시 적중이 줄었다(테넌트 수만큼 키 공간이 커진다).
- 관찰 3 — Spring Framework 캐시 추상화의 기본 키 생성 규칙은 "인자가 하나면 그 인자 자체"다(Spring Framework 7.0.9 레퍼런스 "Default Key Generation"). tenant를 `ThreadLocal`·보안 컨텍스트로 넘기는 코드에 `@Cacheable`을 붙이면 기본 키에 tenant가 들어가지 않는다.
- 이 경로는 DB 행 수준 보안(RLS)으로도 막히지 않는다. 캐시가 DB 앞에 있기 때문이다. RLS 자체는 [database/43-row-level-security](../../database/43-row-level-security/2-summary.md).

### 3. 자원 격리 — 시끄러운 이웃

```text
 공용 FIFO 풀 (워커 4)                       테넌트 쿼터 (A는 동시에 최대 3개)
 큐: [A][A][A]...[A] × 200 [B][B]...         A ─> 문지기(세마포어 3) ─┐
      B는 A 200개 뒤에 줄 선다                  B ──────────────────────┴─> 워커 4
                                            워커 1개는 늘 A가 못 쓴다 → B가 바로 들어간다
```

- Azure "Noisy Neighbor antipattern": 한 테넌트가 자원을 과하게 쓰면 다른 테넌트가 실패하거나 느려진다. 각 테넌트가 작게 써도 **합이 겹치면** 생긴다. 의도하지 않은 경우가 대부분이고, 원인과 상관없이 **자원 거버넌스(쿼터·스로틀링)** 문제로 다루라고 적는다. 스로틀링·쿼터가 있으면 고객에게 투명하게 알리라고 한다.

### 실험 B: 큰 테넌트 배치 앞의 작은 테넌트

공용 워커 4개에 테넌트 A가 작업 200개(각 20ms)를 먼저 넣고, 테넌트 B가 5ms마다 작업(각 2ms) 20개를 보낸다. B의 "제출 → 완료" 시간을 쟀다.

```java
// 쿼터: A의 제출은 세마포어(3) 뒤 문지기 스레드를 거쳐 워커 풀에 들어간다
aGate.submit(() -> {
    aSlots.acquireUninterruptibly();
    pool.submit(() -> { try { work(20); } finally { aSlots.release(); } });
});
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/45/e49/NoisyNeighbor.java`, 2026-10-02 — 3회 실행, 아래는 1회차)

```text
공용 FIFO 풀(워커 4)              B 응답(ms) 최소  920  중앙  968  최대 1011   A 200개 끝난 시각  1026ms
테넌트 쿼터(A 동시 3개)              B 응답(ms) 최소    2  중앙    2  최대    2   A 200개 끝난 시각  1367ms
```

- 관찰 1 — 공용 풀에서 2ms짜리 B 작업이 약 1초씩 기다렸다(3회 중앙값 967~969ms, 같은 조건 재실행 3회 965~968ms). A의 200개 뒤에 줄을 섰기 때문이다.
- 관찰 2 — A를 동시 3개로 묶자 B는 2ms에 끝났다(3회 모두).
- 관찰 3 — 대가: A의 배치가 1026ms → 1367ms로 늦어졌다(3회 1366~1367ms, 재실행 3회 1367~1369ms). 워커 하나를 B 몫으로 남겨 둔 비용이다. **쿼터는 공정함을 사고 최대 처리량을 낸다.**
- 같은 원리가 커넥션 풀·DB CPU·메시지 큐 파티션에도 적용된다. 일반 원리는 [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md), 요청률 상한은 [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md).

### 4. 테넌트 키 파티셔닝

```text
 tenant_id ──hash──> 샤드 0 │ 샤드 1 │ 샤드 2 │ 샤드 3
                         └─ 작은 테넌트 여럿이 해시로 고르게 퍼진다
 대형 테넌트(acme) ─────> 전용 샤드 (사일로로 승격)   ← 매핑 테이블에서 예외로 지정
```

- 파티션 키 = tenant_id로 두면 한 테넌트의 데이터가 한 파티션에 모인다. 테넌트 안 조회는 한 곳에서 끝나고, 테넌트 단위 이동·삭제·백업이 쉽다.
- 대가: 큰 테넌트 하나가 한 파티션을 포화시킨다(핫 파티션). 그래서 **매핑 테이블**(tenant → 샤드)로 큰 테넌트를 전용 샤드로 옮길 수 있게 둔다. 해시만 쓰면 옮길 수 없다.
- 노드 증감 시 재배치를 줄이는 방법은 일관 해싱([data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)). 샤딩 일반은 [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **복합 키(tenant, id)** — 캐시·인덱스·파티션 키의 앞자리에 tenant를 둔다. 실험 A에서 키 하나의 차이가 누출을 갈랐다.
- **세마포어(카운팅)** — 테넌트별 동시 실행 상한. 실험 B의 쿼터.
- **테넌트별 큐 + 공정 스케줄링(라운드 로빈·가중 공정 큐)** — 테넌트마다 큐를 두고 돌아가며 꺼내면 한 테넌트의 긴 줄이 다른 테넌트를 막지 않는다. 실험 B의 세마포어 방식보다 정교한 대안이다.
- **토큰 버킷** — 테넌트별 요청률 상한([reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)).
- **해시 파티셔닝 + 매핑 테이블** — tenant → 샤드. 예외 테넌트를 매핑으로 옮긴다.
- **정책 술어(RLS)** — DB가 모든 쿼리에 `tenant_id = current_setting(...)`을 덧붙인다([database/43](../../database/43-row-level-security/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **격리 모델을 서비스마다 고른다(브리지가 기본).** 규제 데이터(결제·의료)와 시끄러운 이웃 위험이 큰 서비스는 사일로 쪽, 나머지는 풀 쪽.
2. **tenant를 요청 입구에서 한 번 정하고, 타입으로 끝까지 나른다.** 문자열 인자로 흘리지 않고 `TenantId` 값 객체로 둔다.
3. **모든 키에 tenant를 넣는다.** SQL 조건, 캐시 키, 메시지 키, 파일 경로, 로그 필드.
4. **DB에서 한 번 더 막는다.** 풀 모델이면 RLS를 켠다. 단 캐시·검색 엔진처럼 DB 앞·옆 저장소는 RLS가 못 막는다(실험 A).
5. **자원을 테넌트별로 상한한다.** 요청률(토큰 버킷), 동시 실행(세마포어·벌크헤드), 배치 우선순위.
6. **큰 테넌트를 옮길 길을 만든다.** tenant → 샤드·셀 매핑을 두고, 사일로로 승격하는 절차를 준비한다([reliability/51-cells-stamps-and-blast-radius](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md)).
7. **"옆집"으로 시험한다.** 모든 조회 경로에 다른 테넌트의 식별자로 호출해 거절되는지(원본 「검증은 옆집으로」).

### 2. 코드 — tenant를 키에서 빠질 수 없게 (Java, Spring)

```java
public record TenantId(String value) {
    public TenantId { if (value == null || value.isBlank()) throw new IllegalArgumentException("tenant 없음"); }
}

// 캐시 키에 tenant를 명시한다 — 인자가 id 하나면 기본 키는 id뿐이다
@Cacheable(cacheNames = "invoice", key = "#tenant.value() + '|' + #id")
public Optional<Invoice> find(TenantId tenant, String id) {
    return repo.findByTenantIdAndId(tenant.value(), id);
}

// 시끄러운 이웃: 테넌트별 동시 실행 상한
private final Map<TenantId, Semaphore> slots = new ConcurrentHashMap<>();
public <T> T withQuota(TenantId t, Supplier<T> job) {
    Semaphore s = slots.computeIfAbsent(t, k -> new Semaphore(quotaOf(k)));
    if (!s.tryAcquire()) throw new TooManyRequestsException(t);   // 직접 정의한 예외 — 경계에서 429 + Retry-After로 번역
    try { return job.get(); } finally { s.release(); }
}
```

- 메서드 인자에 `TenantId`를 두면 호출하는 쪽이 tenant를 빼먹을 수 없다(원본 「`findById(accountId, requesterScope)`」와 같은 원리).

### 3. 진단

```bash
# 캐시 키·메시지 키 정의에서 tenant가 안 보이는 곳 찾기 (Spring 예)
grep -rn --include='*.java' '@Cacheable' src | grep -v -i 'tenant'
# 테넌트별 자원 사용 편중: 접근 로그(tenant 필드)를 집계해 상위 테넌트 비중
jq -r '.tenant' access.log | sort | uniq -c | sort -rn | head
```

- 지표는 tenant 라벨을 붙여 본다. 단 라벨 카디널리티가 테넌트 수만큼 커지므로 상위 N개와 나머지로 묶는 것이 흔한 타협이다.

## 장애 시나리오와 대처

### 1. 테넌트 ID 필터 누락 → 교차 테넌트 노출 (⚠ 커리큘럼)

- 현상: 고객사 B가 "우리 것이 아닌 청구서가 보인다"고 신고한다.
- 보이는 형태: 접근 로그의 tenant와 응답 데이터의 tenant가 다르다. 재현이 간헐적이다(캐시가 비어 있을 때는 정상).
- 원인: SQL 조건 누락(원본 L1), 또는 SQL은 맞는데 캐시 키에 tenant가 빠졌다(L6, 실험 A — globex가 acme 청구서를 받았다).
- 대처: 캐시를 즉시 비우고 키에 tenant를 넣는다. 영향받은 테넌트·기간을 로그로 산정해 통지 의무를 검토한다. 재발 방지로 tenant를 타입 인자로 강제하고, DB에는 RLS, 시험에는 "옆집 식별자" 전수 시험을 둔다.

### 2. 대형 테넌트가 공유 자원 독점 (⚠ 커리큘럼)

- 현상: 큰 고객의 월말 정산 시각에 다른 고객들의 응답이 느려진다.
- 보이는 형태: 작은 테넌트의 지연이 그 시각에만 크게 뛴다(실험 B 공용 풀: 2ms 작업이 약 1초 대기). 커넥션 풀 대기·워커 큐 길이가 그 시각에 치솟는다.
- 원인: 공용 FIFO 자원에 테넌트별 상한이 없다.
- 대처: 테넌트별 동시 실행·요청률 상한, 배치용 풀 분리, 공정 큐. 그래도 크면 그 테넌트를 전용 샤드·셀(사일로)로 옮긴다. 대가로 큰 테넌트의 처리 시간이 늘 수 있다(실험 B: 1026 → 1367ms)는 점을 계약·안내에 반영한다.

### 3. tenant 컨텍스트가 스레드를 넘으며 사라진다

- 현상: 비동기 작업·배치에서 만든 데이터의 tenant가 비어 있거나, 직전 요청의 tenant가 남아 다른 테넌트로 저장된다.
- 보이는 형태: `tenant_id`가 NULL이거나 기본값인 행, 엉뚱한 tenant 행.
- 원인: tenant를 `ThreadLocal`에 두었는데 스레드 풀·`@Async`로 넘어가며 전파되지 않거나, 풀 스레드에 이전 값이 남았다.
- 대처: tenant를 메서드 인자·메시지 필드로 명시적으로 넘긴다. `ThreadLocal`을 쓰면 작업 시작에 설정하고 끝에 finally로 비우는 래퍼를 둔다. DB 세션 변수도 트랜잭션 범위로만 둔다(database/43 「풀 커넥션에 남은 세션 변수」).

### 4. 사일로 테넌트 수만큼 운영 작업이 늘어난다

- 현상: 테넌트 300개가 각자 DB를 갖고 있어 스키마 변경이 하루 종일 걸리고, 중간에 몇 개가 실패한다.
- 보이는 형태: 마이그레이션 도구 로그에 테넌트별 성공·실패가 섞인다. 앱은 구·신 스키마를 동시에 만난다.
- 원인: 사일로는 격리를 사고 운영 작업을 테넌트 수만큼 곱한다(원본 「스키마 마이그레이션」).
- 대처: expand-contract로 구·신 공존 단계를 두고, 테넌트별 적용 상태를 추적해 재시도한다. 작은 테넌트는 풀로 모으는 브리지를 검토한다.

### 5. 노이즈를 막으려던 쿼터가 정상 고객을 끊는다

- 현상: 대형 고객의 정상 피크가 429로 거절된다.
- 보이는 형태: 특정 테넌트의 429 비율 급증, 고객 문의.
- 원인: 쿼터를 테넌트 크기와 무관하게 한 값으로 줬다.
- 대처: 요금제·계약별 쿼터, 버스트 허용(토큰 버킷 용량), 거절 시 `Retry-After`와 사전 안내(Azure 권고: 스로틀링을 고객에게 투명하게).

## 핵심 문장

- 사일로는 전용 자원, 풀은 공유 자원, 브리지는 서비스마다 섞은 것이다(AWS SaaS Lens). 사일로라도 가입·인증·운영은 공유한다.
- 풀 모델에서는 tenant가 SQL만이 아니라 캐시·메시지·로그의 모든 키에 들어가야 한다. 실험에서 캐시 키에 tenant가 빠지자 SQL이 맞는데도 globex가 acme의 청구서를 받았다.
- Spring 캐시의 기본 키는 인자가 하나면 그 인자 자체다. tenant를 컨텍스트로 넘기면 키에 들어가지 않는다.
- 시끄러운 이웃은 자원 거버넌스 문제다. 실험에서 공용 풀의 2ms 작업이 약 1초를 기다렸고, 큰 테넌트를 동시 3개로 묶자 2ms가 됐다. 대신 큰 테넌트의 배치는 1026 → 1367ms로 늦어졌다.
- tenant → 샤드 매핑을 두면 큰 테넌트를 전용 자원으로 옮길 수 있다. 해시만 쓰면 옮길 수 없다.

## 관련 주제·근거

- 원본
  - [systems/multi-tenancy](../../systems/multi-tenancy/2-summary.md) — 격리 4단계, 누수 경로 L1~L8, 막는 방법의 강도, 리소스 편중, 스키마 마이그레이션 N회
- 선행
  - [45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md) — 서비스마다 다른 격리 모델(브리지)은 서비스 분해 위에 놓인다
- 후속·연결
  - [database/43-row-level-security](../../database/43-row-level-security/2-summary.md) — DB가 tenant 술어를 강제한다
  - [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md) · [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md) — 테넌트 키 파티셔닝
  - [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md) · [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) — 자원 격리 수단
  - [reliability/51-cells-stamps-and-blast-radius](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md) — 테넌트를 셀로 나눠 장애 반경을 제한
- 글·문서
  - AWS Well-Architected SaaS Lens, "Silo, Pool, and Bridge Models" <https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html>
  - Azure Architecture Center, "Tenancy models for a multitenant solution" <https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models> · "Noisy Neighbor antipattern" <https://learn.microsoft.com/en-us/azure/architecture/antipatterns/noisy-neighbor/noisy-neighbor>
  - Spring Framework 7.0.9 레퍼런스, Cache Abstraction "Default Key Generation" <https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html>
- 실험 목록
  - A 캐시 키에 tenant 누락 → 교차 테넌트 반환 — `scratchpad/sd/45/e49/CacheKeyLeak.java`, JDK 21.0.12 temurin `--cpus=2`
  - B 시끄러운 이웃: 공용 FIFO 풀 vs 테넌트 쿼터(세마포어) — `scratchpad/sd/45/e49/NoisyNeighbor.java`, 같은 환경, 3회 실행
