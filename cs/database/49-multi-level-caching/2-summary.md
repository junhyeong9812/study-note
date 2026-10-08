# database/49-multi-level-caching — 다층 캐시: 로컬 L1 + Redis L2, 무효화 전파, 핫키 — 정리 (힌트)

## 해결하는 문제

Redis 캐시(L2)를 붙였더니 DB 부하는 줄었다. 그런데 트래픽이 더 늘자 새 병목이 생긴다.

```text
  앱 인스턴스 × 20 ──(요청마다 GET)──> Redis
                                         │  왕복 지연(예시: 0.2~1ms) × 초당 수만 번
                                         │  인기 키 하나는 한 샤드로만 간다
                                         ▼
                                  샤드 3번 CPU 100%
```

- 모든 조회가 네트워크를 한 번 건넌다.
- 같은 키를 20개 인스턴스가 초당 수천 번씩 물어본다.
- Redis Cluster는 키 하나를 해시 슬롯 하나(`CRC16(key) mod 16384`, 키에 해시 태그 `{…}`가 있으면 중괄호 안만 해시)에 둔다. 인기 키 하나의 부하는 샤드를 늘려도 나뉘지 않는다(Redis Cluster spec).

그래서 앱 프로세스 안에 캐시를 하나 더 둔다(L1). 그러면 새 문제가 생긴다. **L1은 인스턴스마다 따로다.**

쉬운 예: 본사 게시판(Redis)과 지점마다 붙인 복사본(L1)이다. 본사 공지를 고쳤는데 어떤 지점은 복사본을 안 바꿨다. 손님이 지점을 옮겨 다니면 공지 내용이 매번 다르다.

똑같은 구조다. 로드밸런서가 요청을 인스턴스마다 번갈아 보내면, 새로고침할 때마다 값이 바뀐다.

## 동작·원리

### 1. 두 계층의 읽기·쓰기 경로

```text
  읽기:  L1(프로세스 메모리, ~마이크로초) ─miss─> L2(Redis, 네트워크 왕복) ─miss─> DB
            ▲ 채움                                    ▲ 채움
  쓰기:  DB 커밋 → L2 삭제 → 모든 인스턴스의 L1 삭제  ← 이 마지막 단계가 "전파"
```

- L1: 인스턴스 안의 해시맵 + 교체 정책(Caffeine 등). 가장 빠르다. 인스턴스마다 다르다.
- L2: Redis. 인스턴스가 공유한다. 네트워크를 건넌다.
- 내 인스턴스의 L1은 내가 지울 수 있다. **다른 인스턴스의 L1은 알려 줘야** 지운다.

### 2. 무효화 전파 없음 → 값이 번갈아 보인다

```text
  t0  인스턴스 A·B 모두 L1에 price=100
  t1  관리자 요청 → A: DB 90 커밋, Redis 삭제, A의 L1 삭제
  t2  사용자 새로고침 → LB → A: L1 miss → Redis miss → DB 90   → 90
  t3  사용자 새로고침 → LB → B: L1 hit                          → 100
  t4  사용자 새로고침 → LB → A                                   → 90
      ... B의 L1 TTL이 끝날 때까지 90/100이 번갈아 보인다
```

### 3. 전파 방법 셋

**(a) Pub/Sub 방송 — 앱이 직접 알린다**

```text
  쓰는 인스턴스 ── PUBLISH cache-inv "product:1" ──> Redis ──> 구독 중인 모든 인스턴스 → L1에서 삭제
```

- Redis Pub/Sub은 **최대 한 번(at-most-once)** 전달이다. 구독자가 처리 못 하거나 연결이 끊겨 있으면 그 메시지는 영원히 사라진다(Redis Pub/Sub 문서).
- 그래서 L1에는 짧은 TTL을 함께 둔다. 전파가 빠지면 L1 TTL이 L1과 L2 사이 불일치 시간의 상한이 된다. L2 자체가 옛 값이면 이 상한은 통하지 않는다(적용 2절).
- 재연결했다면 그사이 놓친 메시지를 알 수 없다. **재연결 시 L1 전체를 비운다.**

**(b) 서버 지원 클라이언트 캐싱 — `CLIENT TRACKING` (Redis 6+)**

```text
  기본 모드(추적):
    클라이언트 C1: CLIENT TRACKING on  →  GET product:1
    Redis: 무효화 테이블 "product:1 → {C1}" 기록
    다른 클라이언트: SET product:1 ...
    Redis → C1: invalidate [product:1]      ← Redis가 누가 읽었는지 기억했다가 알린다

  방송 모드(BCAST):
    CLIENT TRACKING on BCAST PREFIX product:
    Redis: 기억하지 않는다. "product:" 로 시작하는 키가 바뀔 때마다 구독자 전원에게 알린다
```

- *무효화 테이블(invalidation table)*: 어느 키를 어느 클라이언트가 읽었는지 적은 서버 쪽 표다. 클라이언트 ID만 저장한다.
  - 크기 상한은 `tracking-table-max-keys`다. `redis.conf` 기본 1M 키다. 가득 차면 Redis는 바뀌지 않은 키도 "바뀐 척" 무효화를 보내고 항목을 지운다.
  - 서버 메모리는 추적 키 수 × 그 키를 읽은 클라이언트 수에 비례한다.
- BCAST: 서버 메모리를 쓰지 않는다. 대신 접두사에 맞는 모든 변경이 모든 구독자에게 간다(`PREFIX product: PREFIX user:`).
- `OPTIN`: `CLIENT CACHING yes`를 보낸 다음 명령의 키만 추적한다. `NOLOOP`: 내가 바꾼 키의 무효화는 나에게 보내지 않는다.
- RESP3는 데이터 연결 하나로 무효화 메시지도 받는다. RESP2는 별도 연결에서 `__redis__:invalidate` 채널을 구독하고 `REDIRECT <client-id>`로 받는다.

**(c) TTL만 — 전파 없이 짧게**

- L1 TTL을 몇 초로 두고 불일치를 그만큼 허용한다. 참조 데이터(카테고리, 설정)에는 이것으로 충분한 경우가 많다.

### 4. 두 연결 모델의 경쟁 상태 — 자리표시자

Redis 문서의 예다. 데이터 연결 D와 무효화 연결 I가 따로일 때다.

```text
  잘못된 순서:
    [D] 클라이언트 → 서버: GET foo
    [I] 서버 → 클라이언트: Invalidate foo      (다른 누가 바꿈)
    [D] 서버 → 클라이언트: "bar"               (GET 응답이 늦게 도착)
    → 무효화가 먼저 와서 지울 것이 없었고, 늦게 온 옛 값 "bar"를 L1에 넣는다 → 계속 옛 값

  자리표시자로 막기:
    L1["foo"] = "caching-in-progress" 를 먼저 넣고 GET foo
    [I] Invalidate foo → L1에서 "foo" 삭제
    [D] "bar" 도착 → L1에 "foo" 자리가 없으므로 넣지 않는다
```

- 연결 하나로 데이터와 무효화를 함께 받으면 순서가 정해져 이 경쟁이 없다(문서).
- 같은 경쟁이 (a) Pub/Sub 방식에서도 생긴다. "DB 읽기 시작 → 무효화 도착 → 옛 값으로 L1 채움" 순서다. 같은 자리표시자(또는 버전 비교)로 막는다.

### 5. L1의 크기 제한과 GC

```text
  JVM 힙
  ┌──────── Young ────────┬──────────────── Old ────────────────┐
  │ 요청마다 생기는 객체     │ 오래 사는 객체 = L1 캐시 항목            │
  └───────────────────────┴─────────────────────────────────────┘
  크기 제한 없는 L1 → 항목이 계속 Old로 쌓임 → Old가 차면 전체 GC(긴 멈춤) → 결국 OutOfMemoryError
```

- Caffeine javadoc: 기본값으로는 **어떤 축출도 하지 않는다**. `maximumSize`나 `maximumWeight`, 만료를 직접 걸어야 한다.
- `softValues()`에 기대지 않는다. javadoc 경고: "대부분의 경우 캐시별 최대 크기를 두는 편이 soft reference보다 낫다". soft reference는 메모리 압박 때 **전역** LRU처럼 한꺼번에 치워진다.
- 캐시 항목 수보다 **크기**가 문제일 때는 `maximumWeight` + `weigher`로 바이트 근사치를 센다.

### 6. W-TinyLFU — 무엇을 L1에 남기나

```text
      새 항목
        │
        ▼
  ┌ 입장 창(Window, LRU, 작음) ┐     창에서 밀려난 후보
  └──────────────┬────────────┘            │
                 │   빈도 스케치로 비교:    ▼
                 │   후보 빈도 > 희생자 빈도 ? ──예──> 본 공간 입장, 희생자 축출
                 │                          └아니오─> 후보 버림
  ┌ 본 공간(Main, Segmented LRU: probation → protected) ┐
  └──────────────────────────────────────────────────┘
  빈도 스케치 = 4비트 Count-Min Sketch (최대 15, 주기적으로 절반으로 줄여 옛 인기를 잊는다)
```

- Caffeine `BoundedLocalCache` 주석: 새 항목은 입장 창에서 시작한다. 창에서 밀려날 때 본 공간이 가득 차 있으면 "역사적 빈도 필터"가 새 항목과 희생자 중 누구를 버릴지 정한다. 창은 LRU, 본 공간은 Segmented LRU다.
- 창과 본 공간의 비율은 hill climbing으로 적중률을 보며 자동 조정한다.
- 해시 충돌 공격 대비: 후보 빈도가 희생자 이하라도 일정 이상 "따뜻한" 후보는 1/128 확률로 받아들인다(`admit`, 소스 주석).
- 효과: 한 번만 읽히는 스캔(전체 목록 내보내기 등)이 인기 항목을 밀어내지 못한다. LRU의 약점이다([data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)).
- Caffeine 효율 문서: W-TinyLFU는 ARC·LIRS와 경쟁할 만한 적중률을 내면서 축출된 키를 따로 기억하지 않는다. 빈도 스케치는 항목당 8바이트 정도다.

### 7. 핫키 로컬화

```text
  핫키 "event:today" 초당 5만 조회 (예시)
  L1 없이: 5만 req/s → 샤드 하나
  L1 TTL 1초 + 인스턴스 20개: 인스턴스마다 1초에 1번 채움 → Redis는 초당 약 20회
```

- 핫키 하나는 Redis 샤드를 늘려도 한 샤드에 남는다. L1이 부하를 인스턴스 수만큼으로 줄인다.
- 대가: 최대 TTL만큼 옛 값을 본다. 핫키는 대개 "모두가 보는 같은 값"이라 짧은 TTL을 받아들이기 쉽다.
- 찾기: `redis-cli --hotkeys`는 `maxmemory-policy`가 `*lfu`일 때만 동작한다(`redis-cli.c` 도움말). 클라이언트 쪽 키별 조회 수 통계가 더 직접적이다.
- L1 miss가 동시에 몰리면(TTL이 같은 순간 끝남) 인스턴스 안에서 같은 키를 여러 스레드가 동시에 채운다. 로더를 키당 하나로 묶는다. Caffeine `Cache.get(key, fn)` javadoc: 호출 전체가 원자적이라 `fn`은 키당 최대 한 번 적용된다.

## 쓰이는 자료구조·알고리즘

- **해시맵 + 교체 정책** — LRU(이중 연결 리스트), Segmented LRU. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **Count-Min Sketch(4비트 카운터)** — 키별 빈도를 적은 메모리로 근사한다. 과대 추정만 한다. [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)
- **W-TinyLFU 허용 정책** — 입장 창 + 빈도 비교로 본 공간 입장을 거른다. 창 크기는 hill climbing으로 조정한다.
- **서버 쪽 추적 테이블** — Redis 무효화 테이블(키 → 클라이언트 ID 집합, 상한 도달 시 가짜 무효화로 축출). BCAST는 접두사 → 클라이언트 목록.
- **무효화 방송** — Pub/Sub 팬아웃(최대 한 번). 유실은 TTL과 재연결 시 전체 비우기로 막는다.
- **해시 슬롯** — `CRC16(key) mod 16384`(해시 태그가 있으면 `CRC16(태그) mod 16384`. 태그는 첫 `{`와 그 뒤 첫 `}` 사이이고, 비어 있으면 키 전체를 해시한다). 키 하나는 슬롯 하나다. [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)과 비교.

## 적용 — 풀어나가는 법

### 1. 어떤 데이터를 L1에 두나

```text
  L1에 두기 좋음: 자주 읽고 드물게 바뀜, 모두가 같은 값, 잠깐 옛 값이어도 됨
                  (카테고리 트리, 기능 플래그, 환율, 이벤트 배너, 핫키)
  L1에 두면 안 됨: 사용자별·권한별로 다름(키 폭발), 자주 바뀜(재고 수량),
                  옛 값이면 안 됨(결제 상태, 잔액)
```

- Redis 문서의 권고와 같다: 계속 바뀌는 키(예: 계속 INCR되는 카운터)와 거의 안 읽히는 키는 캐시하지 않는다.

### 2. Spring + Caffeine + Redis 무효화 (예시)

```java
// L1: 크기 상한과 TTL을 둔다
Cache<String, Product> l1 = Caffeine.newBuilder()
    .maximumSize(10_000)                       // 예시 값
    .expireAfterWrite(Duration.ofSeconds(30))   // L1 항목 하나의 수명 (예시). DB와 어긋나는 시간의 상한은 아니다
    .recordStats()
    .build();

Product get(long id) {
    String key = "product:" + id;
    return l1.get(key, k -> {                  // L1 miss → L2 → DB
        Product p = redis.get(k);
        if (p == null) {
            p = repo.findById(id).orElse(null);
            if (p != null) redis.set(k, p, Duration.ofMinutes(10));
        }
        return p;                              // null이면 L1에 넣지 않는다 (Caffeine 규칙)
    });
}

@Transactional
public void updatePrice(long id, long price) {   // 프록시를 거친 외부 호출이어야 트랜잭션이 걸린다
    repo.updatePrice(id, price);
    // 커밋 뒤에 지운다 — 커밋 전에 지우면 다른 요청이 옛 값을 다시 채울 수 있다
    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
        @Override public void afterCommit() {
            redis.del("product:" + id);
            redis.publish("cache-inv", "product:" + id);   // 모든 인스턴스에 방송
        }
    });
}

// 모든 인스턴스: 구독
void onInvalidate(String key) { l1.invalidate(key); }
void onReconnect()            { l1.invalidateAll(); }   // 놓친 메시지를 모르므로 전부 비운다
```

- `afterCommit`이 실패하거나 앱이 그 순간 죽으면 무효화가 빠진다. TTL이 최후 방어선이다.
  - L1 TTL 30초는 L1 항목의 수명일 뿐이다. 동시 읽기가 DB에서 옛 값을 읽고, `redis.del`이 끝난 뒤에 그 값을 Redis에 `SET`할 수 있다. 그러면 L1이 만료돼도 Redis에서 옛 값을 다시 채운다. 이 경합에서 불일치는 L2 TTL(위 예 10분)까지 갈 수 있다. 막으려면 버전을 붙여 늦은 채움을 버린다(Redis client-side caching 문서도 채움과 무효화의 경합을 다룬다). 더 강하게 하려면 outbox·CDC로 무효화 이벤트를 만든다([48](../48-search-index-sync-and-reindexing/2-summary.md)와 같은 구조).
- `Cache.get(key, fn)`에서 `fn`이 `null`을 돌려주면 Caffeine은 항목을 저장하지 않는다(javadoc "enters it into this cache unless null"). 없는 값 캐싱(negative caching)이 필요하면 `Optional` 같은 표지 값을 넣는다.
- 같은 javadoc은 계산 중 다른 스레드의 일부 갱신이 막힐 수 있으니 계산을 짧게 하라고 경고한다. 위 예처럼 Redis·DB를 부르는 적재가 느리면 `AsyncCache`/`AsyncLoadingCache`를 검토한다.

### 3. 서버 지원 클라이언트 캐싱 쓰기

```text
  RESP3 클라이언트:   HELLO 3
                     CLIENT TRACKING on BCAST PREFIX product: NOLOOP
  RESP2 클라이언트:   (연결 I) CLIENT ID → 4 ; SUBSCRIBE __redis__:invalidate
                     (연결 D) CLIENT TRACKING on REDIRECT 4
```

- `NOLOOP`을 켜면 그 연결로 바꾼 키의 무효화는 그 연결에 오지 않는다. 그래서 쓰는 인스턴스는 자기 L1을 직접 지우거나 갱신한다. 그러지 않을 거면 `NOLOOP`을 뺀다(Redis client-side caching "The NOLOOP option").
- 클라이언트 라이브러리가 지원하는지 먼저 본다. 직접 구현한다면 문서 체크리스트를 따른다.
  - 연결이 끊기면 L1을 비운다. 무효화 채널에 주기적으로 PING을 보내고, 응답이 없으면 연결을 닫고 비운다.
  - 키에 TTL이 있으면 L1에도 TTL을 둔다. TTL이 없는 키에도 최대 TTL을 둔다.
  - 클라이언트 메모리 상한을 둔다.
- 서버 쪽: 기본 모드를 쓰면 `INFO stats`의 추적 키 수를 보고 `tracking-table-max-keys`를 정한다. 무효화 테이블이 가득 차면 가짜 무효화가 늘어 L1 적중률이 떨어진다.

### 4. 관측

- L1: 적중률·축출 수(`recordStats()`), 추정 크기. 인스턴스마다 본다.
- L2: 키별 조회 상위(클라이언트 통계), 샤드별 CPU·네트워크.
- JVM: GC 로그의 Old 영역 사용량 추세, 전체 GC 빈도·멈춤 시간(`-Xlog:gc*`, JDK 9+).
- 무효화: 발행 수 vs 수신 수, 구독 연결 재연결 횟수.

## 장애 시나리오와 대처

### 1. L1 무효화가 전파되지 않음 → 새로고침마다 값이 바뀐다

- **현상**: 가격을 바꿨는데 새로고침하면 새 값과 옛 값이 번갈아 보인다.
- **보이는 형태**: 응답 헤더·로그의 인스턴스 ID별로 값이 다르다. Redis와 DB는 새 값이다.
- **원인**: 쓰는 인스턴스만 자기 L1을 지웠다. 방송이 없거나, Pub/Sub 구독 연결이 끊겨 메시지를 놓쳤다(최대 한 번 전달).
- **대처**: 커밋 뒤 방송, 재연결 시 L1 전체 비우기, 짧은 L1 TTL. 옛 값을 조금도 허용할 수 없는 데이터는 L1에서 뺀다.

### 2. 크기 제한 없는 로컬 캐시 → Old 영역 증가, GC 멈춤

- **현상**: 배포 후 며칠이 지나면 p99가 튀고 결국 인스턴스가 재시작된다.
- **보이는 형태**: GC 로그에서 Old 사용량이 계단식으로 오른다. 전체 GC가 잦아지고 멈춤이 길어진다. 마지막에 `java.lang.OutOfMemoryError: Java heap space`. 컨테이너라면 OOM kill(exit code 137).
- **원인**: `new ConcurrentHashMap<>()`이나 제한 없는 `Caffeine.newBuilder().build()`를 캐시로 썼다. 키 공간(상품 ID × 옵션 등)이 끝없이 늘어난다.
- **대처**: `maximumSize`/`maximumWeight` + 만료. 키 공간이 사용자별로 늘어나는 데이터는 L1에 두지 않는다. 힙 덤프로 가장 큰 보유자를 확인한다.

### 3. Redis 핫키 → 단일 샤드 CPU 100%, 네트워크 포화

- **현상**: 이벤트 시작과 함께 캐시 조회 지연이 치솟는다. 클러스터 전체 CPU는 낮은데 샤드 하나만 100%다.
- **보이는 형태**: 그 샤드의 `INFO` 명령 통계·네트워크 출력만 튄다. 앱 로그에 Redis 타임아웃(클라이언트 라이브러리 예외)이 쌓인다.
- **원인**: 키 하나는 슬롯 하나, 슬롯 하나는 마스터 하나에 있다. 샤드를 늘려도 그 키의 부하는 나뉘지 않는다. 값이 크면 네트워크가 먼저 포화된다.
- **대처**: 핫키를 L1에 짧은 TTL로 둔다(인스턴스 수만큼으로 부하 감소). 키 복제(`key:1..N`에 같은 값, 랜덤 조회), 읽기 복제본. 큰 값은 쪼개거나 줄인다. 기본 대처표는 원본 04-caching §5.

### 4. 무효화가 옛 값에 역전당한다

- **현상**: 무효화를 분명히 받았는데 L1에 옛 값이 다시 들어 있다. 드물게만 난다.
- **보이는 형태**: 로그 순서가 "무효화 수신 → (그 전에 시작한) 읽기 응답 도착 → L1 저장"이다.
- **원인**: 읽기 응답과 무효화가 다른 연결·스레드로 와서 순서가 뒤집혔다(Redis 문서의 D/I 경쟁).
- **대처**: 읽기 전에 자리표시자를 넣고, 무효화가 자리표시자를 지우면 늦은 응답을 버린다. 또는 값에 버전을 담아 더 낮은 버전은 넣지 않는다. 가능하면 RESP3 단일 연결로 받는다.

### 5. 무효화 테이블 포화 → 이유 없는 L1 적중률 하락

- **현상**: 트래픽이 늘자 데이터 변경은 그대로인데 L1 적중률이 떨어진다. Redis 메모리도 늘었다.
- **원인**: 기본 추적 모드에서 추적 키 수가 `tracking-table-max-keys`(기본 1M)에 닿았다. Redis가 공간을 만들려고 바뀌지 않은 키도 무효화한다.
- **대처**: 상한을 조정하거나 BCAST 모드(서버 메모리 0, 대신 접두사 단위 방송)로 바꾼다. `OPTIN`으로 추적 대상을 좁힌다.

## 핵심 문장

- L1은 인스턴스마다 따로라, 쓰기는 내 L1만 지운다. 다른 인스턴스의 L1은 방송이나 서버 추적으로 알려야 한다.
- Redis Pub/Sub은 최대 한 번 전달이므로, L1에는 짧은 TTL을 함께 두고 재연결 때 전부 비운다.
- `CLIENT TRACKING` 기본 모드는 서버가 "누가 무엇을 읽었나"를 기억하고(상한 기본 1M 키), BCAST는 기억하지 않고 접두사로 방송한다.
- Caffeine은 기본값으로 아무것도 축출하지 않는다. L1에는 크기 상한이 필수이고, W-TinyLFU는 빈도 스케치로 한 번 읽힌 항목이 인기 항목을 밀어내지 못하게 한다.
- 핫키 하나는 슬롯 하나라 샤드를 늘려도 나뉘지 않는다. L1이 그 부하를 인스턴스 수 수준으로 줄인다.

## 관련 주제·근거

기초(캐시 계층, cache-aside, 삭제 무효화, 스탬피드, 핫키 해법 표)는 [systems/server-design/04-caching.md](../../systems/server-design/04-caching.md) §1·§3·§5에 있다. 이 노트는 **L1이 여러 인스턴스에 흩어질 때** 생기는 문제만 판다.

버전 기준: Redis 문서(Client-side caching reference, `CLIENT TRACKING`, Pub/Sub, Cluster spec — 2026-10 확인)와 `redis.conf`, Caffeine `master` 소스. 로컬에 Redis·JDK 컴파일러가 없어 Redis·Caffeine 동작은 문서와 소스로만 확인했다.

- 선행
  - [30-caching-with-databases](../30-caching-with-databases/2-summary.md) · 원본 [systems/server-design/04-caching.md](../../systems/server-design/04-caching.md) — 캐시 계층, cache-aside, 삭제 무효화, 스탬피드, 핫키
  - [distributed/32-distributed-cache-consistency](../../distributed/32-distributed-cache-consistency/2-summary.md)
  - data-structure `14-lru-cache` → [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- 연결
  - database [31-cache-key-versioning-and-serialization](../31-cache-key-versioning-and-serialization/2-summary.md)
  - [48-search-index-sync-and-reindexing](../48-search-index-sync-and-reindexing/2-summary.md) — 커밋 후 전달, outbox·CDC로 무효화 이벤트 만들기
  - [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md) — Count-Min Sketch
- 후속(AI 엔지니어링): [ai-engineering/12-prompt-and-semantic-caching](../../ai-engineering/12-prompt-and-semantic-caching/2-summary.md) — LLM 응답 의미 캐시
- Redis 문서
  - Spring Framework `@Transactional` 메서드 가시성(인터페이스 프록시는 public만, 6.0+ 클래스 프록시는 protected·package-visible도) <https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html>
  - Client-side caching reference — 추적·BCAST·OPTIN·NOLOOP, 무효화 테이블, RESP2 REDIRECT, 경쟁 상태와 자리표시자, 연결 끊김 시 비우기, 캐시할 키 고르기 <https://redis.io/docs/latest/develop/reference/client-side-caching/>
  - `CLIENT TRACKING`(Redis 6부터) <https://redis.io/docs/latest/commands/client-tracking/>
  - Pub/Sub — "at-most-once message delivery semantics" <https://redis.io/docs/latest/develop/pubsub/>
  - Redis Cluster specification — 16384 슬롯, `CRC16(key) mod 16384`, Hash tags <https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/>
  - `redis.conf` — `tracking-table-max-keys 1000000` 주석 · `src/redis-cli.c` — `--hotkeys`는 `maxmemory-policy`가 `*lfu`일 때만
- Caffeine (github.com/ben-manes/caffeine `master`)
  - `Caffeine.java` javadoc — 기본 무축출, `maximumSize`, `softValues()` 경고
  - `BoundedLocalCache.java` 주석 — W-TinyLFU(입장 창 LRU + 본 공간 SLRU, 빈도 필터, hill climbing), `admit`
  - Wiki "Efficiency" — W-TinyLFU vs ARC·LIRS, 4비트 CountMinSketch
- 논문: G. Einziger, R. Friedman, B. Manes, "TinyLFU: A Highly Efficient Cache Admission Policy", ACM Transactions on Storage, 2017 (Caffeine 소스가 인용, 원문 미열람) <https://dl.acm.org/citation.cfm?id=3149371>
- 로컬 재현: 없음(Redis·javac 없음). 커밋 시에만 전달되는 알림은 [48](../48-search-index-sync-and-reindexing/2-summary.md)의 PostgreSQL NOTIFY 재현을 참고
