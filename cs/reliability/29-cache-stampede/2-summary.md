# reliability/29-cache-stampede — 스탬피드·관통·눈사태 방어 — 정리 (힌트)

## 해결하는 문제

캐시는 DB가 받을 부하를 대신 받는다.\
그래서 DB는 "캐시가 대부분을 막아 준다"는 가정으로 작게 잡힌다.\
캐시가 막아 주지 못하는 순간이 오면 그 가정이 한꺼번에 깨진다.

```text
 평소:   요청 1000/s ──▶ [캐시 hit 99.9%] ──▶ DB 1/s
 만료:   인기 키 하나가 만료되는 순간
         요청 수백 개가 동시에 miss ──▶ DB에 같은 SELECT 수백 개 ──▶ DB 느려짐
         느려진 동안 또 miss ──▶ 커넥션 풀 고갈 ──▶ DB 다운 (⚠)
```

쉬운 예: 마트 시식 코너다.
- 시식 접시(캐시)가 비는 순간 기다리던 사람들이 모두 주방(DB)으로 "더 주세요"를 외치러 간다.
- 주방은 한 번에 한 접시만 만든다. 대표 한 명만 주방에 가고 나머지는 접시를 기다리면 된다(싱글플라이트).
- 접시가 비기 **전에** 미리 채워 두면 아무도 기다리지 않는다(조기 갱신).

똑같은 구조다.\
실무 예: 메인 페이지 인기 상품, 환율표, 설정 값, 랭킹 — 모두가 같은 키를 읽는 캐시. 배포·재시작 직후 모든 키가 비어 있을 때.

세 가지 사고를 구분해야 대처가 갈린다.

| 사고 | 무엇이 | 막는 것 |
|---|---|---|
| 스탬피드(stampede, thundering herd) | **인기 키 하나**의 만료 순간 동시 miss | 싱글플라이트, 리스, 조기 갱신 |
| 눈사태(avalanche) | **많은 키**가 같은 시각에 만료 | TTL 지터, 워밍 |
| 관통(penetration) | **없는 키**를 계속 조회 — 캐시가 "없음"을 담지 않음 | 부정 캐시, 블룸 필터 |

- 기초(싱글플라이트·미리 갱신 구현, 실패를 캐시하는 사고, 측정 자 `peakConcurrentLoads`)는 원본 [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)에 있다.
- DB 쪽에서 본 모양(커넥션 풀 고갈, Facebook memcache 리스)은 [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md) §6, 분산 캐시 무효화와 thundering herd는 [distributed/32-distributed-cache-consistency](../../distributed/32-distributed-cache-consistency/2-summary.md) §3.
- 이 노트는 **확률적 조기 만료(XFetch)**와 **여러 인스턴스**, **눈사태·관통**을 실험으로 비교한다.

## 동작·원리

### 1. 스탬피드의 시간축

```text
 TTL 1000ms, 재계산(DB 조회) 100ms, 요청 1ms마다 1개
 t=1000 만료 ─┬─ 요청1 miss → DB ───────100ms──────▶ set
              ├─ 요청2 miss → DB ─────────────────▶ set
              ├─ ...       (재계산이 끝나기 전 100ms 동안 온 요청 전부)
              └─ 요청100 miss → DB
          DB 동시 조회 ≈ 도착률 × 재계산 시간 = 1/ms × 100ms = 100
```

- 스탬피드 크기는 **도착률 × 재계산 시간**이다(리틀의 법칙과 같은 꼴). 키가 인기 있을수록, DB가 느려질수록 커진다. DB가 느려지면 재계산 시간이 늘어 더 커진다 — 양의 되먹임이다.
- 아래 실험 B의 나이브: 3번의 만료에서 DB 호출 300~301번, 동시 최대 101(3회 실행).

### 2. 방어 1 — 싱글플라이트(요청 합치기)

```text
 만료 순간
 요청1 ─ inflight[k] 비어 있음 → 내가 조회 ─────▶ DB ──▶ set, future 완료
 요청2 ─ inflight[k] 있음 → future.join() ──기다림──┘
 요청3 ─ inflight[k] 있음 → future.join() ──기다림──┘
```

- 같은 키의 동시 miss를 하나의 조회로 합친다. Go `singleflight`, Guava·Caffeine의 로딩 캐시가 같은 모양이다.
- 남는 비용: 나머지 요청은 **기다린다**. 실험 B에서 싱글플라이트는 DB 호출 3번이었지만 3500요청 중 154~155개가 50ms 넘게 기다렸다(p99 89~90ms).
- 범위: 한 프로세스 안이다. 인스턴스가 N대면 같은 키에 DB 조회가 최대 N개 나간다(실험 A: 4대 → `DB 호출 4`).

### 3. 방어 2 — 확률적 조기 만료(XFetch)

```text
 시각 ──────────────────────────────────────────▶ expiry
 재계산 확률  ~0 ............... 점점 커짐 ...... ↑ 1
 요청마다 판정:  now − Δ·β·ln(rand()) ≥ expiry  이면 만료 전이라도 재계산
   Δ: 지난 재계산에 걸린 시간 · β: 조기 정도(기본 1) · ln(rand()) ≤ 0
```

- Vattani·Chierichetti·Lowenstein, "Optimal Probabilistic Cache Stampede Prevention"(VLDB 2015)의 알고리즘이다. 논문 Figure 3 의사코드 그대로다.
  - 조기 간격 `−Δ·β·ln(rand())`은 평균 Δ·β인 지수 분포에서 뽑은 값이다. 만료가 가까울수록, 재계산이 오래 걸릴수록 일찍 갱신할 확률이 커진다.
  - 각 요청이 혼자 판정한다. 조정(락·통신)이 필요 없다.
- 실험 B에서 드러난 한계: 요청이 많으면 재계산이 끝나기 전 다른 요청도 확률에 걸린다. XFetch만으로는 `DB 호출 9~20 · 동시 최대 2~9`(3회 실행 범위)였다. 나이브의 101보다 훨씬 작지만 1은 아니다.
  - 그래서 실무에서는 **XFetch + 키당 갱신 하나(싱글플라이트)**를 함께 쓴다. 조기 갱신은 뒤에서 하고 요청은 옛 값을 바로 받는다. 실험: `DB 호출 5 · 동시 최대 1 · 50ms 넘게 기다린 요청 0`(DB 호출은 실행마다 5~6).
- 같은 발상의 고정 임계판이 원본의 "수명 80%에서 미리 갱신", Caffeine `refreshAfterWrite`다.

### 4. 방어 3 — 리스(캐시 서버가 갱신자를 정함)

- Facebook memcache(Nishtala 외, NSDI 2013 §3.2.1): miss한 클라이언트에게 64비트 리스 토큰을 준다. 캐시 서버는 키당 **10초에 한 번만** 토큰을 준다(기본 설정). 그 사이 다른 클라이언트는 "잠깐 기다렸다 다시 오라"는 응답을 받는다.
- 논문 측정: 스탬피드에 취약한 키 집합에서 DB 최대 조회율이 17K/s에서 1.3K/s로 줄었다.
- 인스턴스 수와 무관하게 키당 토큰 발급을 10초에 한 번으로 묶는다. 보통은 리스를 받은 클라이언트가 수 ms 안에 값을 채우므로 사실상 갱신자 하나다. 다만 재계산이 10초를 넘으면 새 토큰이 나가 갱신이 겹칠 수 있다(같은 절). 캐시 서버가 그 기능을 가져야 한다는 것이 조건이다. Redis라면 `SET lock:k token NX PX 3000`으로 흉내 낸다(분산 락과 같은 모양 — 만료 시간과 옛 주인 문제도 같다).

### 5. 눈사태와 관통

```text
 눈사태: 재시작 직후 키 1000개를 같은 시각에 채움 → 같은 TTL → 같은 시각에 만료
         ████ ← 1초 뒤 한 구간에 몰림
 지터:   TTL = 1000ms × (1 ± 0.2·난수)  → 만료가 0.8~1.2초에 흩어짐
         ▂▄▆█▆▄▂

 관통:   없는 id 조회 → 캐시 miss → DB "없음" → 캐시에 안 담음 → 다음에도 miss
 부정 캐시: "없음"도 짧은 TTL로 담는다 · 블룸 필터: 확실히 없는 키를 DB 앞에서 거른다
```

- *TTL 지터*: TTL에 무작위를 섞어 같은 시각에 채운 키들의 만료를 흩뜨리는 것. 재시도 지터([06](../06-retry-backoff-jitter/2-summary.md))와 같은 발상이다.
- *부정 캐시(negative cache)*: "결과 없음"이라는 사실 자체를 잠시 기억하는 것. TTL은 짧게 둔다. 나중에 생긴 데이터가 오래 안 보이는 것을 막기 위해서다.
- *블룸 필터*: "확실히 없음 / 있을 수도 있음"을 답하는 비트 배열. 거짓 양성은 있지만 거짓 음성은 없다. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md).

### 실험: 스탬피드·XFetch·인스턴스 수·눈사태·관통

- A: 인기 키를 채운 뒤 만료시키고 가상 스레드 200개가 동시에 읽는다. DB 조회 50ms.
- B: 1ms마다 1요청(열린 부하) × 3.5초. TTL 1000ms, 재계산 100ms.
- C(모의 시간, 시드 고정): 키 1000개를 t=0에 채움. 1ms마다 무작위 키 5회 읽기, 4초. 100ms 구간별 DB 호출 수.
- D(모의): 없는 id 50개를 10000번 조회.

핵심 코드(전체: 실험 목록의 `Stampede.java`):

```java
// 싱글플라이트 — 같은 키의 미스는 진행 중인 하나의 Future를 공유
CompletableFuture<String> mine = new CompletableFuture<>();
CompletableFuture<String> f = inflight.putIfAbsent(k, mine);
if (f != null) return f.join();
try { String v = db(k, load); m.put(k, new Entry(v, System.nanoTime() + ttl, 0)); mine.complete(v); return v; }
catch (RuntimeException ex) { mine.completeExceptionally(ex); throw ex; }
finally { inflight.remove(k, mine); }

// XFetch — 논문 Figure 3
if (e == null || now - e.deltaNs() * beta * Math.log(ThreadLocalRandom.current().nextDouble()) >= e.expiry()) {
    long start = System.nanoTime(); String v = db(k, load);
    m.put(k, new Entry(v, System.nanoTime() + ttl, System.nanoTime() - start));
}

// XFetch + 싱글플라이트 — 조기 갱신은 키당 하나, 뒤에서. 요청은 옛 값을 바로 받는다
if (xfetchSaysRefresh && refreshing.add(k))
    Thread.ofVirtual().start(() -> { try { recompute(k); } finally { refreshing.remove(k); } });
return e.value();
```

(실험, JDK 21.0.12 eclipse-temurin, `--cpus=2`, 2026-10-01 — 집필 3회·점검 3회 실행. A·C·D는 매번 같았다. B의 나이브·싱글플라이트·XFetch+싱글플라이트 행은 ±1 안에서 흔들렸고, XFetch 행은 크게 다르다: DB 호출 9~20, 동시 최대 2~9)

```text
JDK 21.0.12+8-LTS, cores=2
A. 만료 직후 동시 200요청 (DB 조회 50ms)
  나이브                          DB 호출 200 · DB 동시 최대 200
  싱글플라이트(1대)                   DB 호출   1 · DB 동시 최대   1
  싱글플라이트(4대, 각자 로컬)            DB 호출   4 · DB 동시 최대   4
B. 1ms마다 1요청 x 3.5초, TTL 1000ms, 재계산 100ms
  나이브                          DB 호출 300 · DB 동시 최대 101 · 50ms 넘게 기다린 요청  300/3500 · p99 100ms · max 105ms
  싱글플라이트                       DB 호출   3 · DB 동시 최대   1 · 50ms 넘게 기다린 요청  154/3500 · p99  89ms · max 100ms
  XFetch β=1                   DB 호출   9 · DB 동시 최대   2 · 50ms 넘게 기다린 요청    9/3500 · p99   0ms · max 100ms
  XFetch β=1 + 싱글플라이트(뒤에서)     DB 호출   5 · DB 동시 최대   1 · 50ms 넘게 기다린 요청    0/3500 · p99   0ms · max   1ms
C. 눈사태 — 키 1000개 동시 적재 (모의 시간)
  지터 ± 0%: DB 호출 합 2871 · 100ms 구간 최대 398 · 0.8~2.4초 구간별:   0   0 398 233 138  84  60  38  18  11   6   5  96 179 172 158
  지터 ±20%: DB 호출 합 2867 · 100ms 구간 최대 214 · 0.8~2.4초 구간별:  57 123 169 214 180 102  59  40  21  22  26  55  75 129 144 126
D. 관통 (모의)
  부정 캐시 없음: 없는 id 조회 10000회 → DB 조회 10000회
  부정 캐시 있음: 없는 id 조회 10000회 → DB 조회 50회
```

- 관찰 1 — A: 나이브는 200요청이 200번 DB에 갔다(동시 200). 싱글플라이트는 1번. 인스턴스 4대가 각자 싱글플라이트를 가지면 4번이다. 프로세스 로컬 싱글플라이트의 상한은 "인스턴스 수"다.
- 관찰 2 — B: 나이브의 동시 최대 101은 "도착률 1/ms × 재계산 100ms"와 맞는다. 싱글플라이트는 DB를 지키지만 만료마다 50ms 넘게 기다린 요청이 약 50개다(154 ÷ 3).
- 관찰 3 — B: XFetch만 쓰면 기다린 요청이 재계산을 직접 한 요청 수와 같다(9). 재계산 중에도 다른 요청이 확률에 걸려 동시 재계산이 2~9개 생겼다. 갱신자를 하나로 묶고 뒤에서 돌리자 기다린 요청이 0이 됐다. 대신 DB 호출이 3 → 5~6으로 늘었다. 만료보다 일찍 갱신한 대가다.
- 관찰 4 — C: 지터 없이 같은 시각에 채운 키들은 1.0~1.1초 구간에 398회가 몰렸다. ±20% 지터는 최대 구간을 214로 낮췄다. DB 호출 **합**은 거의 같다(2871 vs 2867). 지터는 일을 줄이지 않고 몰림만 흩는다.
- 관찰 5 — D: 부정 캐시 없이 없는 id 50개를 반복 조회하면 10000번 모두 DB로 간다. "없음"을 담으면 id당 1번(50번)이다.

## 쓰이는 자료구조·알고리즘

- **해시맵 + Future(약속)** — 싱글플라이트의 `inflight` 맵. `putIfAbsent`가 "내가 첫 번째인가"를 원자로 판정한다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **TTL 캐시 / LRU** — 시간으로 버리는 캐시와 크기로 버리는 캐시. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **지수 분포 표본 추출(역변환)** — `−ln(U)`(U는 0~1 균등)는 평균 1인 지수 분포다. XFetch는 여기에 Δ·β를 곱해 조기 간격을 뽑는다.
- **블룸 필터** — 관통 방어. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md).
- **리스 토큰** — 캐시 서버가 키당 갱신 권한을 시간 한정으로 준다(memcache 리스). 분산 락과 같은 재료 — [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md).
- **난수 지터** — TTL에 균등 난수를 곱해 만료를 흩는다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **지표부터** — 적중률이 아니라 "키별 DB 재계산 수"와 "동시 재계산 수"를 잰다. 스탬피드 때 miss 수는 나이브와 싱글플라이트가 같다(원본의 측정).
2. **인기 키에 싱글플라이트** — 프로세스 안의 몰림을 1로.
3. **낡아도 되는 값이면 조기 갱신** — XFetch(또는 `refreshAfterWrite`) + 키당 갱신 하나. 줄 옛 값이 남아 있는 동안은 요청이 기다리지 않는다. 첫 조회나 이미 만료된(`expireAfterWrite`) 항목의 조회는 로드를 기다린다(Caffeine 위키 "Refresh").
4. **인스턴스가 많으면 갱신자 하나** — 캐시 서버 리스, 또는 Redis `SET NX PX` 짧은 락. 락을 못 잡은 쪽은 옛 값(stale)을 주거나 잠깐 기다렸다 다시 읽는다.
5. **TTL 지터** — 같은 시각에 채우는 키(재시작 직후, 배치 적재)에.
6. **관통 방어** — 부정 캐시(짧은 TTL), 키 공간이 정해져 있으면 블룸 필터, 입력 검증(존재할 수 없는 id 거절).
7. **재시작 워밍** — 인기 키를 미리 채우고 트래픽을 점진적으로 붙인다.

### 2. Caffeine으로 (Java)

```java
// Caffeine 위키 "Refresh": refreshAfterWrite가 지난 항목은 **조회될 때** 비동기로 다시 읽고, 그동안 옛 값을 준다.
// 갱신 중 예외가 나면 옛 값을 유지하고 예외는 로그로 남기고 삼킨다. 조회가 없으면 그냥 만료된다.
LoadingCache<String, Product> cache = Caffeine.newBuilder()
        .maximumSize(100_000)
        .expireAfterWrite(Duration.ofMinutes(10))      // 최대 수명
        .refreshAfterWrite(Duration.ofMinutes(8))      // 그 전에 뒤에서 갱신(고정 임계판 조기 갱신)
        .build(id -> repo.findById(id).orElse(null));  // null이면 담지 않는다 → 관통은 따로 막는다
```

- 부정 캐시가 필요하면 `Optional<Product>`를 값으로 담고 "없음"에 짧은 TTL을 주는 별도 캐시를 둔다.

### 3. 분산 갱신자 하나 (Redis, 개념 예)

```java
String v = redis.get(key);
if (v != null && !shouldRefreshEarly(key)) return v;              // XFetch 판정
String token = UUID.randomUUID().toString();
boolean leader = "OK".equals(redis.set("lock:" + key, token, SetParams.setParams().nx().px(3000)));
if (leader) {
    try { v = loadFromDb(key); redis.set(key, v, SetParams.setParams().px(ttlWithJitter())); }
    finally { releaseIfOwner("lock:" + key, token); }             // 소유자 확인 후 해제(Lua)
    return v;
}
return v != null ? v : waitAndReread(key);                       // 옛 값 주기 또는 잠깐 대기
```

- 이 예의 "갱신자 하나"는 락 유효 기간(3초) 안에서만 성립한다. DB 조회가 3초를 넘으면 락이 풀려 다른 인스턴스도 조회하고, 옛 주인의 `redis.set`이 더 새 값을 덮어쓸 수 있다. 해제 때의 소유자 확인으로는 이것을 막지 못한다. 넉넉한 TTL·락 연장, 또는 쓰기 직전 소유권 확인·펜싱 토큰이 필요하다(Redis 분산 락 문서, [distributed/12](../../distributed/12-coordination-and-fencing/2-summary.md)).

### 4. 진단

```bash
# Redis: 적중·미스 누계
redis-cli INFO stats | grep -E 'keyspace_hits|keyspace_misses'
# 같은 쿼리가 동시에 몇 개 도나(PostgreSQL)
psql -c "SELECT query, count(*) FROM pg_stat_activity WHERE state='active' GROUP BY query ORDER BY 2 DESC LIMIT 5;"
```

- PromQL 개념 예: `sum(rate(cache_load_total[1m])) by (cache)` 의 스파이크가 TTL 주기와 겹치면 눈사태, 특정 키에 몰리면 스탬피드다.

## 장애 시나리오와 대처

### 1. 인기 키 만료 순간 DB로 동시 수천 요청 → DB 다운 (⚠)

- 현상: 평소 한가한 DB가 정각·특정 주기마다 CPU 100%, 커넥션 풀 고갈. 그 뒤 애플리케이션 전체 지연.
- 보이는 형태: `pg_stat_activity`에 **같은 SELECT**가 수백 개 active. 애플리케이션 로그에 커넥션 풀 타임아웃. 적중률 그래프는 잠깐만 내려가 눈에 잘 안 띈다.
- 원인: 인기 키의 동시 miss가 전부 DB로 갔다. 동시 수 ≈ 도착률 × 재계산 시간(실험 B: 101).
- 대처: 싱글플라이트(1대 기준 1회), 조기 갱신 + 갱신자 하나(옛 값이 있는 동안 기다림 0), 인스턴스가 많으면 리스·분산 락.

### 2. 싱글플라이트를 넣었는데 인스턴스 수만큼 몰린다

- 현상: 서버를 50대로 늘리자 인기 키 만료 때 같은 쿼리가 50개 동시에 들어온다.
- 보이는 형태: 서버별 재계산은 1인데 DB 쪽 동시 실행은 인스턴스 수와 같다(실험 A: 4대 → 4).
- 원인: 싱글플라이트는 프로세스 로컬이다.
- 대처: 인스턴스 수만큼은 허용할 수 있는지 먼저 계산한다. 안 되면 캐시 서버 리스(memcache: 키당 10초에 한 번)나 분산 락으로 갱신자를 하나로 묶는다.

### 3. 재시작 직후 주기적 DB 스파이크 — 눈사태

- 현상: 배포 뒤 정확히 TTL마다 DB 부하가 튄다. 시간이 지나면 점점 잦아든다.
- 보이는 형태: DB 쿼리 수가 TTL 주기의 톱니 모양. 키 하나하나는 재계산 1회인데 키가 많다(실험 C: 한 구간 398).
- 원인: 재시작 때 같은 시각에 채운 키들이 같은 TTL로 같은 시각에 만료된다.
- 대처: TTL 지터(실험 C: ±20%로 최대 구간 214), 인기 키 워밍, 점진 트래픽 투입.

### 4. 없는 id로 DB 폭주 — 관통

- 현상: 적중률이 낮고 DB 조회가 많은데 결과는 대부분 0행이다.
- 보이는 형태: 존재하지 않는 id를 순서대로 훑는 요청(스캔·봇·버그). 로더가 `null`을 돌려주는 비율이 높다.
- 원인: 캐시가 "없음"을 담지 않는다(Caffeine 위키 "Population": 계산할 수 없는 항목이면 `get`이 null을 돌려준다 — 담기지 않는다). 싱글플라이트는 동시 요청만 합치고 순차 요청은 막지 못한다.
- 대처: 부정 캐시(실험 D: 10000 → 50), 블룸 필터, 입력 검증, 레이트 리미트([11](../11-rate-limiter/2-summary.md)).

### 5. 갱신 실패가 캐시된다

- 현상: DB 장애가 끝났는데도 특정 키 요청이 계속 실패한다.
- 보이는 형태: 같은 예외가 원인 해소 뒤에도 반복된다. 재시작하면 낫는다.
- 원인: 싱글플라이트가 실패한 Future를 맵에서 지우지 않았다. 이후 요청이 모두 그 실패를 받는다(원본 09의 "실패를 캐시하는 사고").
- 대처: 성공·실패 모두 `finally`에서 자리를 비운다(위 코드의 `inflight.remove(k, mine)`). 조기 갱신 실패는 옛 값이 유효한 동안 삼키고 지표로만 남긴다.

## 핵심 문장

- 스탬피드 크기는 도착률 × 재계산 시간이다. DB가 느려질수록 커지는 양의 되먹임이다.
- 싱글플라이트는 프로세스 안의 같은 키 재계산을 하나로 줄이지만, 나머지는 기다리고 인스턴스 수만큼은 남는다.
- XFetch는 만료가 가까울수록 확률적으로 일찍 갱신한다. 부하가 높으면 동시 재계산이 여럿 생기므로 키당 갱신 하나와 함께 쓴다(실험: 기다린 요청 0).
- 눈사태는 TTL 지터로 몰림을 흩고, 관통은 부정 캐시·블룸 필터로 막는다. 지터는 일의 총량을 줄이지 않는다.
- 측정의 자는 적중률이 아니라 재계산 수와 동시 재계산 수다.

## 관련 주제·근거

- 선행
  - [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md) — 캐시 패턴·무효화, DB 쪽에서 본 스탬피드(§6)
  - 원본 [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md) — 싱글플라이트·미리 갱신 구현, 실패 캐시, 측정 자
- 후속·연결
  - [distributed/32-distributed-cache-consistency](../../distributed/32-distributed-cache-consistency/2-summary.md) — 리스, 지역 간 무효화
  - [database/31-cache-key-versioning-and-serialization](../../database/31-cache-key-versioning-and-serialization/2-summary.md) — 배포 직후 역직렬화 실패로 전부 miss, TTL 지터
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 몰린 DB 부하를 셰딩으로 버티기
  - [30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md) — 읽기와 무관하게 중앙에서 미리 채우기
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 지터의 같은 발상
- 후속(AI 엔지니어링): [ai-engineering/12-prompt-and-semantic-caching](../../ai-engineering/12-prompt-and-semantic-caching/2-summary.md) — 의미 캐시 놓침이 몰릴 때 요청 합치기
- 근거
  - Vattani, Chierichetti, Lowenstein, "Optimal Probabilistic Cache Stampede Prevention", PVLDB 8(8), 2015 — Figure 3 XFetch 의사코드, §5 구현 노트(Δ 저장, `−Δβ log(rand())`) <https://www.vldb.org/pvldb/vol8/p886-vattani.pdf>
  - Nishtala 외, "Scaling Memcache at Facebook", NSDI 2013 §3.2.1 Leases(키당 10초에 토큰 하나 — 갱신자 수가 아니라 발급률 제한, 17K/s → 1.3K/s) <https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf>
  - Caffeine 위키 "Refresh"·"Population"(2026-10-01 열람) <https://github.com/ben-manes/caffeine/wiki/Refresh>
  - Redis 문서 "Distributed Locks with Redis" — 상호 배제는 락 유효 기간 안에 일을 끝낼 때만 보장 <https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/>
- 실험 목록
  - A~D 스탬피드·XFetch·인스턴스 수·눈사태·관통 — `Stampede.java`, JDK 21 temurin, 가상 스레드, `--cpus=2`, 집필 3회·점검 3회 실행(A·C·D 동일, B는 XFetch 행이 크게, 나머지 행은 ±1 변동)
