# database/30-caching-with-databases — DB 앞의 캐시: 패턴, 무효화, 일관성 — 정리 (힌트)

## 해결하는 문제

같은 행을 초당 수만 번 읽으면 DB는 CPU·커넥션·I/O가 먼저 바닥난다.\
그래서 자주 읽는 결과를 DB 앞의 빠른 저장소(메모리 캐시)에 복사해 두고, 대부분의 읽기를 거기서 끝낸다.

```text
  요청 ──▶ 캐시 ──hit──▶ 응답                (마이크로초~밀리초)
             └─miss──▶ DB ──▶ 캐시에 채움 ──▶ 응답   (DB 부하는 miss만큼)
```

쉬운 예: 자주 묻는 질문을 칠판에 적어 둔 안내 데스크다.
- 대부분의 손님은 칠판을 보고 간다(hit).
- 규정이 바뀌면 칠판을 지워야 한다. 안 지우면 손님은 옛 규정을 듣는다(낡은 값).

똑같은 구조다.\
어려운 부분은 넣는 법이 아니라 **복사본(캐시)과 원본(DB)이 어긋나는 순간을 관리하는 것**이다.\
캐시는 DB 트랜잭션 밖에 있다. 그래서 커밋 순서, 복제 지연, 동시 요청의 순서가 모두 어긋남의 원인이 된다.

실무 예:
- 상품 가격을 바꿨는데 일부 사용자에게 한 시간째 옛 가격이 보인다. 캐시 삭제는 분명히 했다.
- 인기 상품 키가 만료되는 순간 DB CPU가 100%가 된다.
- 존재하지 않는 상품 ID로 초당 수천 번 조회가 들어와 캐시를 뚫고 DB를 친다.

기초(캐시 계층, 5가지 패턴 표, 무효화 전략 표, 3대 사고, 핫키, 쓰면 안 되는 경우, 지표)는 원고 [server-design/04-caching](../../systems/server-design/04-caching.md) §1~8에 있다.\
이 노트는 **DB 트랜잭션·복제와 캐시가 만나는 지점**에서 생기는 일관성 문제와, 그 해법의 원리를 채운다.

## 동작·원리

### 1. cache-aside의 두 경로 (원고 §2 요약)

```text
  읽기: get(k) ─miss─▶ SELECT ─▶ set(k, v, TTL) ─▶ 반환
  쓰기: UPDATE(DB) ─▶ delete(k)          ← 갱신(set)이 아니라 삭제
```

- 쓰기 때 캐시를 **갱신하지 않고 삭제**한다. Facebook memcache 논문(Nishtala 외, NSDI 2013 §2)도 같은 선택을 하고, 이유를 "deletes are idempotent"라고 적는다.
  - *멱등(idempotent)*: 여러 번 해도 결과가 같다. 삭제는 두 번 해도 "없음"이다. set은 순서가 뒤바뀌면 옛 값이 이긴다.
- 캐시는 원본이 아니므로 언제든 지워도(evict) 정확성은 깨지지 않는다. 부하만 는다(같은 논문 §2, §5 "deleting or evicting keys is always a safe action").

### 2. 함정 ① — 커밋 전에 지우면 옛 값이 다시 들어온다

```text
  시간 →
  쓰기 스레드 W: BEGIN; UPDATE price=2000; cache.delete(k) ─────────────── COMMIT
  읽기 스레드 R:                             get(k) miss → SELECT → 1000(커밋 전이라 옛 값)
                                                           → set(k, 1000, TTL)
  결과: DB는 2000, 캐시는 1000 — TTL이 끝날 때까지
```

- 로컬 재현(PostgreSQL 17.11, READ COMMITTED): W가 `UPDATE` 후 커밋 전 3초 동안, R의 `SELECT`는 `price=1000`을 읽었다. 커밋 뒤에야 2000이 보였다.
- 그래서 삭제는 **커밋 뒤**에 해야 한다. Spring이면 `@TransactionalEventListener`(기본 phase가 `AFTER_COMMIT`) 또는 트랜잭션 동기화의 `afterCommit`에서 지운다.
- Facebook 논문 §4.1 Regional Invalidations(mcsqueal)도 "트랜잭션이 커밋되면 무효화"한다. DB가 커밋한 SQL에서 삭제할 키를 뽑아 캐시에 방송하는 데몬을 DB마다 둔다.

> 참고: 원본 §3 "갱신 vs 삭제"의 예제는 `@Transactional` 메서드 **안에서** `cache.delete`를 호출한다. 이 위치는 커밋 전이라 위 경합이 그대로 생긴다. 삭제를 커밋 후 훅으로 옮겨야 한다(Spring 문서 "Transaction-bound Events", 위 로컬 재현).

### 3. 함정 ② — 커밋 뒤에 지워도 남는 경합 (stale set)

원고 §3 "그래도 남는 경쟁 상태"의 시간축이다.

```text
  R: get miss → SELECT → 1000 ─────(느림: GC·네트워크)─────────────▶ set(k, 1000)  ✘ 옛 값 고착
  W:                  UPDATE → 2000 → COMMIT → delete(k)
                                                  ▲ R의 set보다 먼저 일어났다
```

- 삭제를 커밋 뒤로 옮겨도, **읽은 시점이 쓰기보다 앞선 set**이 삭제보다 늦게 도착하면 옛 값이 남는다.
- Facebook의 해법은 **리스(lease)**다(§3.2 "Leases").
  - miss가 나면 캐시 서버가 그 키에 묶인 64비트 토큰을 준다.
  - set할 때 토큰을 같이 보낸다. 그 사이 delete가 왔으면 토큰이 무효가 되어 set이 거절된다.
  - 논문은 이를 load-link/store-conditional과 비슷한 방식이라고 설명한다.

```text
  R: get miss → lease=t7 받음 → SELECT(1000) ─────────────▶ set(k, 1000, t7) → 거절(t7 무효)
  W:                       UPDATE → COMMIT → delete(k) → t7 무효화
```

- 리스가 없는 캐시(일반적인 Redis 사용 등)에서는 완전히 막기 어렵다. 실무 대응은 원고 §3처럼 **짧은 TTL을 반드시 걸기**(낡은 항목이 머무는 시간에 상한), 지연 이중 삭제, 값에 버전을 넣어 "더 새 버전만 덮어쓰기" 등이다.

### 4. 함정 ③ — 복제본에서 읽어 채우면 옛 값이 들어온다

```text
  W: 원본에 UPDATE → COMMIT → delete(k)
  R: get miss → SELECT(복제본) → 복제가 아직 안 옴 → 옛 값 → set(k, 옛 값)   ✘
     └ 복제 지연(수 ms~수 초) 동안의 miss는 모두 옛 값으로 캐시를 채울 수 있다
```

- Facebook 논문 §5는 이 문제를 다룬다. 비-마스터 지역에서 쓰면 **원격 마커**를 먼저 세운다. 이후 miss 때 마커가 있으면 복제본 대신 마스터로 읽으러 간다. 지연을 더 내고 낡은 값을 읽을 확률을 줄이는 거래다.
- 작은 시스템의 대응: 방금 쓴 키의 캐시 채우기는 원본(프라이머리)에서 읽는다. 또는 쓰기 직후 일정 시간은 캐시를 채우지 않는다. 복제 지연 자체는 32번 노트.

### 5. write-through·write-behind는 "두 저장소에 쓰기"다

```text
  write-through:  DB 커밋 ✔ → 캐시 set ✘(네트워크 오류)   → 캐시에 옛 값 남음
                  캐시 set ✔ → DB 커밋 ✘(제약 위반·롤백)  → 캐시에만 있는 유령 값
  write-behind:   캐시에만 쓰고 나중에 DB로               → 캐시 노드가 죽으면 유실
```

- DB 트랜잭션과 캐시 쓰기를 하나로 묶는 원자적 방법은 일반적으로 없다(서로 다른 시스템).
- 그래서 "DB가 원본, 캐시는 파생"이라는 규칙을 지키고, 캐시 쪽 실패는 **삭제 + TTL**로 수렴시키는 것이 흔한 설계다. 변경 이벤트를 커밋 로그(CDC)나 아웃박스에서 읽어 무효화하면 "커밋된 것만 무효화"가 보장된다(Facebook mcsqueal과 같은 발상).

### 6. 스탬피드·관통·눈사태 — DB 쪽에서 본 모양 (원고 §4 요약)

```text
  스탬피드: 인기 키 1개 만료 → 같은 SELECT 수천 개 동시 → DB 커넥션 풀 고갈
  관통:    없는 키 반복 → 캐시가 "없음"을 기억 못 함 → 매번 SELECT (결과 0행)
  눈사태:  키 대량 동시 만료 / 캐시 클러스터 다운 → DB가 전체 읽기 부하를 직접 받음
```

- 히트율 h면 DB가 받는 읽기는 전체의 (1 − h)다. h = 0.9에서 캐시가 사라지면 DB 읽기는 10배가 된다(원고 §4).
- Facebook 리스의 두 번째 용도가 스탬피드 완화다(§3.2 "Leases"). 캐시 서버가 **키당 10초에 한 번만** 토큰을 준다(기본 설정). 그 사이 다른 요청은 "잠깐 기다렸다 다시 오라"는 응답을 받는다. 논문의 측정에서 스탬피드에 취약한 키 집합의 DB 최대 조회율이 17K/s에서 1.3K/s로 줄었다.
- 확률적 조기 갱신(XFetch)·싱글플라이트는 [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md), 관통의 블룸 필터는 [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md).

### 7. DB 자신의 캐시와의 관계

```text
  앱 캐시(Redis 등)  ← 결과·객체 단위, 앱이 무효화 책임
  DB 버퍼 풀         ← 페이지 단위, DB가 일관성 보장(07번 노트)
  (MySQL 쿼리 캐시)   ← 8.0에서 제거됨
```

- DB 버퍼 풀은 트랜잭션과 일관된다. 앱 캐시는 아니다. 그래서 앱 캐시는 "조금 낡아도 되는" 데이터에 둔다.
- MySQL 8.0 "What Is New": 쿼리 캐시가 제거됐다. 결과 캐시는 앱 쪽의 몫이다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블 + LRU(또는 근사 LRU)**: 캐시 서버의 기본 구조. 메모리가 차면 오래 안 쓴 항목을 내보낸다(eviction). [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **TTL 만료**: 항목마다 만료 시각. 만료 처리는 타이머 휠·힙 같은 구조나, 접근 시 검사 + 주기적 표본 검사로 한다(구현마다 다름). TTL은 **한 캐시 항목의 수명** 상한이다. 채울 때 읽은 값 자체가 낡았다면(복제 지연) DB 변경 시점부터 잰 낡음은 TTL을 넘을 수 있다.
- **블룸 필터**: "확실히 없음"을 빠르게 판정해 관통을 막는다. 거짓 양성은 있고 거짓 음성은 없다.
- **리스 토큰(조건부 쓰기)**: 읽기 시점에 받은 토큰이 여전히 유효할 때만 쓴다. load-link/store-conditional, 낙관적 동시성 제어의 버전 비교와 같은 발상이다(17번 노트).
- **버전(세대) 키**: `user:v3:123`처럼 키에 버전을 넣으면 버전을 올리는 것만으로 대량 무효화가 된다(원고 §3).

## 적용 — 풀어나가는 법

**1) 캐시하기 전에 DB에서 먼저 확인한다.** 원고 §6 "먼저 쿼리를 고치고, 그래도 안 되면 캐시".

```sql
-- PostgreSQL: 호출 수·총 시간 상위 쿼리 (pg_stat_statements 확장 필요)
SELECT calls, round(total_exec_time) AS total_ms, round(mean_exec_time::numeric, 2) AS mean_ms, left(query, 60)
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
-- 실행 계획부터 본다
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM product WHERE id = 42;
```

- 호출이 많고, 결과가 자주 안 바뀌고, 조금 낡아도 되는 것이 캐시 후보다.

**2) 무효화는 커밋 후에 (Java / Spring).**

```java
@Transactional
public void changePrice(long id, int price) {
    productRepository.updatePrice(id, price);
    events.publishEvent(new ProductChanged(id));    // 아직 커밋 전
}

@TransactionalEventListener                          // 기본 phase = AFTER_COMMIT
public void onChanged(ProductChanged e) {
    cache.delete("product:" + e.id());               // 커밋된 뒤에만 삭제
}
```

**3) 읽기 경로에 TTL·지터·널 캐싱을 기본으로.**

```java
public Product get(long id) {
    String key = "product:" + id;
    CacheEntry<Product> hit = cache.get(key);
    if (hit != null) return hit.valueOrNull();                     // 널 캐싱도 hit
    Product p = productRepository.findById(id).orElse(null);        // 방금 쓴 키면 프라이머리에서
    Duration ttl = p == null ? Duration.ofSeconds(30)
                             : Duration.ofMinutes(10).plusSeconds(ThreadLocalRandom.current().nextInt(60));
    cache.set(key, CacheEntry.of(p), ttl);                          // TTL + 지터
    return p;
}
```

**4) 캐시가 죽었을 때를 시험한다.**
- 캐시를 끈 상태에서 DB가 버티는 처리량을 잰다. 못 버티면 DB 앞에 레이트 리밋·서킷 브레이커를 둔다(원고 §4 눈사태).

**5) 지표를 DB 지표와 같이 본다.**

```text
  캐시: 히트율, eviction 수, 키 크기, 캐시 응답 지연
  DB:   초당 쿼리 수, 커넥션 사용률, 버퍼 풀 적중률, 복제 지연
  → 캐시 히트율이 떨어지는 순간 DB 쿼리 수가 같이 뛰는지
```

## 장애 시나리오와 대처

**① 무효화 경합 → 오래된 값 고착 (커리큘럼 ⚠)**
- 현상: 가격 변경 후 일부 사용자에게 옛 가격이 TTL 내내 보인다. 재현이 잘 안 된다.
- 보이는 형태: 에러 없음. DB 값과 캐시 값을 직접 비교하면 다르다. 변경이 몰리는 시간대에만 생긴다.
- 원인(셋 중 하나): (1) 삭제를 커밋 전에 했다(2절). (2) 커밋 후 삭제했지만 늦게 도착한 옛 set이 이겼다(3절). (3) 복제본에서 읽어 채웠다(4절).
- 대처: 삭제를 `AFTER_COMMIT`으로 옮긴다. 모든 키에 TTL을 건다(낡은 항목 수명의 상한). 방금 쓴 키의 채우기는 프라이머리에서 한다. 지원되면 리스·버전 비교 조건부 set을 쓴다. 정합성이 절대적인 값(잔액·확정 재고)은 캐시하지 않는다(원고 §6).

**② 캐시 스탬피드 (커리큘럼 ⚠)**
- 현상: 매시 정각 등 특정 순간 DB CPU·커넥션이 치솟고 API가 타임아웃 난다.
- 보이는 형태: 같은 쿼리가 `pg_stat_activity`·`SHOW PROCESSLIST`에 수백 개 동시에. 커넥션 풀 대기 타임아웃. 캐시 miss 급증과 시각이 겹친다.
- 원인: 인기 키의 만료 순간 동시 miss가 모두 DB로 갔다.
- 대처: 싱글플라이트(키당 한 요청만 DB로), 확률적 조기 갱신, 만료 후 옛 값 제공(stale-while-revalidate), TTL 지터. 원리와 구현은 [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md).

**③ 캐시 관통 (커리큘럼 ⚠)**
- 현상: 캐시 히트율은 높은데 DB 부하가 줄지 않는다. 결과 0행 쿼리가 많다.
- 보이는 형태: `pg_stat_statements`에서 `rows / calls`가 0에 가까운 쿼리가 호출 수 상위. 접근 로그에 존재하지 않는 ID가 반복.
- 원인: "없음"을 캐시하지 않아 없는 키 조회가 매번 DB까지 간다. 의도적 공격일 수 있다.
- 대처: 널 캐싱(짧은 TTL), 블룸 필터로 존재하지 않는 키를 앞에서 차단, 입력 형식 검증, 레이트 리밋.

**④ 캐시 눈사태 (커리큘럼 ⚠)**
- 현상: 캐시 클러스터 장애나 배포 후 전체 재시작 직후 DB가 연쇄로 느려지거나 죽는다.
- 보이는 형태: 캐시 히트율이 0 근처로 급락, 동시에 DB 초당 쿼리 수가 평소의 1/(1 − h)배. PG `too many clients already` 또는 MySQL `ERROR 1040 Too many connections`.
- 원인: 대량 키 동시 만료, 또는 캐시 계층 전체 소실로 모든 읽기가 DB로 갔다.
- 대처: TTL 지터, 캐시 이중화, 재기동 워밍업, 캐시 miss 경로에 레이트 리밋·서킷 브레이커로 DB 보호. "캐시가 전부 죽어도 DB가 버티는가"를 정기적으로 시험한다(원고 §4·§8).

**⑤ 배포 직후 캐시 값 역직렬화 실패**
- 현상: 신버전 인스턴스에서만 캐시 읽기 예외가 나고, 예외 처리로 DB에 몰린다.
- 보이는 형태: 역직렬화 예외 로그 급증, 신버전 인스턴스의 DB 쿼리 수 급증.
- 원인: 값의 직렬화 형식이 바뀌었는데 키는 그대로였다. 신·구 버전이 같은 키에 서로 다른 형식을 쓴다.
- 대처: 형식을 바꿀 때 키에 버전을 넣는다(원고 [08 §1](../../systems/server-design/08-deployment-ops.md) "포맷 바꿀 땐 키를 바꾼다"). 키·직렬화 설계는 31번 노트.

## 핵심 문장

- 캐시는 DB 트랜잭션 밖의 복사본이다. 어긋남은 커밋 순서, 늦게 도착한 set, 복제 지연에서 생긴다.
- 쓰기 때는 캐시를 갱신하지 말고 삭제한다. 삭제는 멱등이다.
- 삭제는 커밋 **후**에 한다. 커밋 전에 지우면 다른 요청이 옛 값을 읽어 다시 채운다.
- 커밋 후 삭제로도 늦게 도착한 옛 set은 못 막는다. 리스·버전 비교가 없다면 TTL이 낡은 항목의 수명을 제한하는 마지막 장치다(채움을 복제본에서 하면 그 지연만큼 더 낡을 수 있다).
- 히트율 h에 기대는 시스템은 캐시가 사라지면 DB 읽기가 1/(1 − h)배가 된다. 캐시 없이도 DB가 버티게 보호한다.

## 관련 주제·근거

- 선행
  - [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — 복제 지연. 원고 [server-design/03-data-layer](../../systems/server-design/03-data-layer.md)
  - [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) — LRU와 교체 정책
- 연결
  - [07-buffer-pool](../07-buffer-pool/2-summary.md) — DB 내부 페이지 캐시
  - [16-mvcc](../16-mvcc/2-summary.md) — 커밋 전 값이 다른 트랜잭션에 안 보이는 이유
  - [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md) — 버전 비교 조건부 쓰기
  - [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) — 커밋 후 훅
  - [31-cache-key-versioning-and-serialization](../31-cache-key-versioning-and-serialization/2-summary.md)
  - [49-multi-level-caching](../49-multi-level-caching/2-summary.md) — 로컬 L1 + 분산 L2
  - [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md) — reliability/29-cache-stampede의 노트
  - [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
  - 원고 [server-design/04-caching](../../systems/server-design/04-caching.md) — 계층·패턴·무효화·3대 사고·핫키·지표·체크리스트
- 논문·문서
  - R. Nishtala 외, "Scaling Memcache at Facebook", NSDI 2013 — §2 look-aside·삭제(멱등), §3.2 Reducing Load의 Leases(stale set·thundering herd, 64비트 토큰, 키당 10초, 17K/s → 1.3K/s), §4.1 Regional Invalidations — mcsqueal(커밋 후 무효화), §5 remote marker <https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala>
  - Spring Framework Reference — Data Access › Transaction Management › Transaction-bound Events(`@TransactionalEventListener`, 기본 `AFTER_COMMIT`) <https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html>
  - MySQL 8.0 Reference Manual 1.4 What Is New in MySQL 8.0("The query cache was removed") <https://dev.mysql.com/doc/refman/8.0/en/mysql-nutshell.html>
  - Vattani 외, "Optimal Probabilistic Cache Stampede Prevention", VLDB 2015 — ops-patterns/09 경유
- 로컬 재현(PostgreSQL 17.11): 커밋 전 삭제 경합 — 쓰기 트랜잭션이 커밋 전인 동안 다른 세션이 옛 값을 읽음(READ COMMITTED)
