# distributed/32-distributed-cache-consistency — 대규모 캐시 일관성: lease·무효화 파이프라인·장애 격리 — 정리 (힌트)

## 해결하는 문제

캐시 서버 한 대와 DB 하나라면 "커밋 뒤 삭제 + TTL"로 대부분 버틴다. 이 기초는 [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md)에 있다.\
규모가 커지면 캐시 복사본이 여러 곳에 생긴다. 무효화가 늦거나 빠지거나, 순서가 바뀌는 경로도 같이 늘어난다.

```text
  지역(region) A — DB 원본                         지역 B — DB 복제본(비동기)
  ┌ 프론트엔드 클러스터 1: 웹 서버들 + 캐시 서버들 ┐      ┌ 클러스터 3 ┐
  ├ 프론트엔드 클러스터 2: 웹 서버들 + 캐시 서버들 ┤      └ 클러스터 4 ┘
  └ 저장 클러스터: MySQL 샤드들 ─────── 복제 ───────────▶ MySQL 복제본
  같은 키 k의 복사본: 클러스터 1·2·3·4에 각각 하나씩 + DB 원본·복제본
```

쉬운 예: 체인점 네 곳의 안내 데스크 칠판이다.
- 본사 규정이 바뀌면 네 지점 칠판을 모두 지워야 한다. 한 곳이라도 놓치면 그 지점 손님은 옛 규정을 듣는다.
- 지점 직원이 "본사에 물어보고 적는" 사이에 규정이 또 바뀌면, 늦게 적은 옛 규정이 칠판에 남는다.
- 인기 질문의 답을 지우자마자 손님 수백 명이 한꺼번에 본사에 전화한다.

똑같은 구조다.\
Facebook memcache 논문(Nishtala 외, NSDI 2013)은 이 문제들을 실제 규모에서 다룬다. MIT 6.5840 Spring 2026 L16이 이 논문을 "성능 vs 일관성 vs 실용성"의 예로 읽는다.

- 여기서 "일관성"은 선형화 같은 보장이 아니다. L16 노트의 표현으로는 "읽기가 최근 쓰기보다 **얼마나 뒤처지나**"다.
  - 논문 §5: 최선 노력(best-effort) 최종 일관성을 제공하고, 성능·가용성을 우선한다.
  - L16: 최종 일관성 + "자기가 쓴 것은 읽기(read-your-own-writes)".
- 목표는 "한 번도 낡지 않음"이 아니다. **낡은 값이 영원히 고착되지 않게, 낡은 기간이 짧게**다.

실무 예:
- 가격을 바꿨는데 일부 사용자에게 TTL 내내 옛 가격이 보인다. 삭제 로그는 분명히 있다.
- 인기 게시물에 좋아요가 몰리자, 매번 캐시가 지워지고 DB 조회가 폭증한다.
- 캐시 서버 한 대가 죽자 그 몫의 키를 다른 서버로 재해시했고, 핫키를 받은 서버까지 연쇄로 넘어진다.
- Redis 클라이언트 측 캐싱을 켰더니, 아무도 쓰지 않았는데 무효화 메시지가 쏟아지고 로컬 적중률이 떨어진다.

## 동작·원리

### 1. 읽기·쓰기 경로 — 갱신하지 않고 지운다

```text
  read(k):  v = mc[hash(k) % n].get(k)
            if v == nil: v = DB에서 읽기; mc.set(k, v)
  write(k): DB에 쓰기(트랜잭션) → mc[hash(k) % n].delete(k)
```

- *look-aside 캐시*: 캐시는 DB를 모른다. 앱(웹 서버)이 캐시와 DB에 따로 말한다(L16, 논문 Figure 1).
- 쓰기 때 `set`이 아니라 `delete`를 쓴다. 논문 §2는 "삭제는 멱등"이라고 이유를 적는다.
  - 두 클라이언트가 같은 키에 쓰면, DB에 닿는 순서와 캐시에 닿는 순서가 다를 수 있다. `set`이면 늦게 도착한 옛 값이 남는다. `delete`는 어느 순서로 와도 결과가 "없음"이다(L16).
- 캐시는 원본이 아니다. 지우거나 내쫓는(evict) 것은 부하만 늘릴 뿐 정확성을 해치지 않는다(§5).

### 2. stale set — 늦은 set이 삭제를 덮어쓴다

```text
  시간 →
  C1:  get(k) miss ── DB 읽기 v1 ───────────(느림)───────────▶ set(k, v1)   ✘ v1 고착
  C2:                         DB에 v2 쓰기 → delete(k)
                                              ▲ C1의 set보다 먼저 일어났다
  결과: 캐시 v1, DB v2 — 다음 쓰기나 TTL 만료까지
```

- *stale set*: 웹 서버가 캐시에 넣은 값이 넣어야 할 최신 값이 아닌 경우. 동시 갱신이 캐시에 닿는 순서가 바뀌면 생긴다(§3.2.1).
- 커밋 뒤에 지워도 막지 못한다. **읽은 시점이 쓰기보다 앞선 set이 삭제보다 늦게 도착**하는 것이 원인이다.
- 해법은 *lease*다(§3.2.1 "Leases").
  - miss가 나면 캐시 서버가 그 키에 묶인 64비트 토큰을 준다.
  - set할 때 토큰을 함께 낸다. 그 사이 delete가 왔으면 캐시 서버가 토큰을 무효로 만들어 두었으므로 set이 거절된다.
  - 논문은 이를 load-link/store-conditional과 비슷하다고 설명한다.

```text
  C1:  get(k) miss → lease t7 ── DB 읽기 v1 ─────────────▶ set(k, v1, t7) → 거절
  C2:                     DB에 v2 쓰기 → delete(k) → t7 무효
  다음 읽기: miss → 새 lease → DB에서 v2 → 캐시 v2
```

#### 실험: lease 없이 vs lease로 — 같은 경합

Redis 7.4 위에 Lua 스크립트로 lease를 흉내 냈다. `LGET`은 값이 없으면 키당 하나의 토큰을 발급하고, `LSET`은 토큰이 그대로일 때만 저장하고, 쓰기 쪽 `DEL`은 값과 토큰을 함께 지운다. "DB"는 Java 프로세스 안의 맵이다(시뮬레이션).

```java
static final String LGET =
    "local v = redis.call('GET', KEYS[1]) if v then return {'HIT', v} end " +
    "if redis.call('EXISTS', KEYS[2]) == 1 then return {'WAIT', ''} end " +          // 다른 클라이언트가 채우는 중
    "local t = redis.call('INCR', 'w32:leaseseq') redis.call('SET', KEYS[2], t, 'PX', ARGV[1]) return {'LEASE', tostring(t)}";
static final String LSET =
    "if redis.call('GET', KEYS[2]) == ARGV[1] then redis.call('SET', KEYS[1], ARGV[2], 'EX', 600) " +
    "redis.call('DEL', KEYS[2]) return 1 end return 0";                               // 토큰이 살아 있을 때만 저장
static void write(Conn c, int k) throws IOException {
    db.merge(k, 1L, Long::sum);                 // DB 커밋
    c.cmd("DEL", vk(k), lk(k));                 // 커밋 뒤 무효화: 값과 lease를 함께 지운다
}
```

순서를 고정한 한 번의 경합(R 읽기 → W 쓰기·삭제 → R 늦은 set):

(실험, Redis 7.4.9 + Java 21, 2026-10-01)

```text
scripted race, no lease:
  R: GET -> null (miss)
  R: DB read v=1
  W: DB v=2 commit, DEL cache
  R: SET v=1 -> OK
  cache=1  db=2  (stale until TTL or next write)
scripted race, lease:
  R: miss, lease token=1
  R: DB read v=1
  W: DB v=2 commit, DEL cache
  R: LSET(token=1, v=1) -> 0
  cache=null  db=2  (next reader misses and refills 2)
```

키 200개에 읽기 스레드 6개(채우기 전 0~4ms 지연, DB 조회 3ms)와 쓰기 스레드 2개를 3초 돌린 뒤, 쓰기를 멈추고 캐시와 DB를 비교했다. 개수는 실행마다 다르다.

```text
stale-set  lease=false keys=200 cached=117  stale(cache!=db, no more writes)=3
stale-set  lease=true  keys=200 cached=126  stale(cache!=db, no more writes)=0
stale-set  lease=false keys=200 cached=134  stale(cache!=db, no more writes)=4
stale-set  lease=true  keys=200 cached=122  stale(cache!=db, no more writes)=0
```

- lease 없이 두 번 돌려 3개·4개 키가 "쓰기가 끝났는데도 DB와 다른 값"으로 남았다. 이 값은 다음 쓰기나 TTL(실험에서는 600초)까지 고착된다. 점검 재실행(5회 × 2)에서는 2~7개였다.
- lease로는 두 번 모두 0개였다(재실행 10번도 모두 0개).

### 3. thundering herd — 지우자마자 몰려드는 miss

```text
  핫키 k: 쓰기 → delete(k) → 동시에 수백 개 get miss → 모두 DB로
  lease 변형: 캐시 서버가 키당 토큰을 일정 간격에 하나만 준다
     첫 miss  → lease 받음 → DB → set
     나머지   → "잠깐 뒤 다시" → 재시도 때 대개 hit
```

- *thundering herd*: 읽기와 쓰기가 모두 잦은 키에서, 쓰기가 값을 계속 지우는 바람에 많은 읽기가 비싼 경로(DB)로 가는 현상(§3.2.1).
- 논문 설정: 캐시 서버가 **키당 10초에 한 번만** 토큰을 준다(기본). 그 사이 요청은 "잠깐 기다리라"는 응답을 받는다. 토큰을 받은 클라이언트는 보통 수 밀리초 안에 값을 채운다.
- 측정: 허드에 취약한 키 집합의 일주일치 miss에서, DB 최대 조회율이 lease 없이 17K/s, lease로 1.3K/s였다(§3.2.1). DB를 최대 부하 기준으로 준비하므로 큰 절약이다.
- *stale values* 옵션: 지운 값을 잠깐 따로 보관해, get이 "낡았다고 표시한 값"을 줄 수 있다. 조금 낡은 값으로 진행할 수 있는 앱은 기다리지 않는다(§3.2.1).

#### 실험: 핫키 하나에 동시 miss 50개

```java
for (int i = 0; i < 50; i++) fs.add(ex.submit(() -> { try (Conn c = new Conn()) { go.await(); return read(c, k, lease); } }));
go.countDown();   // 50개를 한꺼번에 출발시킨다
```

(실험, Redis 7.4.9 + Java 21, DB 조회 3ms 시뮬레이션, 2026-10-01) — 수치는 실행마다 다르다.

```text
herd       lease=false concurrent misses=50  db reads=26
herd       lease=true  concurrent misses=50  db reads=1
```

- lease 없이 50개 중 26개가 DB까지 갔다. 먼저 채운 값이 보이기 전에 출발한 요청들이다. 이 수는 실행마다 크게 다르다. 점검 재실행 5회에서는 4회가 50개 전부, 1회가 31개였다.
- lease로는 1개만 DB에 갔다. 나머지는 `WAIT`을 받고 2ms 뒤 재시도해 hit했다.

### 4. 무효화 파이프라인 — 누가, 언제, 어떻게 지우나

```text
  웹 서버 ── SQL(+ 지울 캐시 키) ──▶ MySQL ── 커밋 로그 ──▶ mcsqueal(DB마다)
     │                                                       │ 커밋된 SQL에서 delete 추출
     │ 자기 클러스터에 직접 delete (자기가 쓴 것 읽기용)         │ 묶어서(batch) 전송
     ▼                                                       ▼
  클러스터 1 캐시                              클러스터마다 mcrouter → 해당 캐시 서버로 분배
```

- 논문 §4.1 Regional Invalidations
  - SQL에 "커밋되면 무효화할 캐시 키"를 덧붙인다. DB마다 도는 데몬(mcsqueal)이 **커밋된** SQL에서 삭제를 뽑아 지역 안 모든 프론트엔드 클러스터에 보낸다.
  - 쓴 웹 서버는 자기 클러스터에도 직접 지운다. 한 사용자 요청 안에서 자기가 쓴 것을 읽게 하고, 자기 클러스터의 낡은 시간을 줄인다.
  - 묶음 전송: 데몬이 삭제를 패킷 몇 개로 묶어 클러스터의 mcrouter로 보내고, mcrouter가 풀어서 각 캐시 서버로 보낸다. 패킷당 삭제 수의 중앙값이 18배 늘었다.
  - 발행한 삭제 중 실제로 캐시된 데이터를 지운 것은 4%뿐이었다. 대부분의 무효화는 "없는 것을 지운다".
- 왜 웹 서버가 모든 클러스터에 직접 방송하지 않나(§4.1)
  - 웹 서버는 묶음 전송을 잘 못해 패킷 부담이 크다.
  - 설정 오류로 삭제가 잘못 라우팅되는 등 체계적 문제가 나면 되돌릴 방법이 거의 없다. 예전에는 캐시 전체를 순차 재시작해야 했다.
  - 커밋 로그에 무효화를 넣으면 데몬이 **로그를 다시 재생**해 잃거나 잘못 간 무효화를 복구할 수 있다.
- L16의 질문 "DB가 캐시에 값을 직접 넣으면 경합이 없지 않나?"의 답: 캐시 값은 DB 레코드 그대로가 아니라 앱이 계산한 결과가 많다. DB는 무엇이 캐시돼 있는지도 모른다.
- 지연 측정(§7.3): 삭제 100만 건 중 1건을 표본으로 뽑아 주기적으로 모든 클러스터를 조회하고, 지워졌어야 할 항목이 남아 있으면 오류로 기록한다.
  - 원본 지역 안 삭제: 1초 안에 99.99%, 1시간 뒤 99.999%.
  - 복제 지역 간 삭제: 1초 안에 99.9%, 10분 안에 99.99%.
  - 몇 초 뒤에도 빠진 무효화는 대개 첫 시도가 실패한 것이고 재시도로 해결됐다.

### 5. 지역 간 — 복제 지연과 무효화의 경주

```text
  원본 지역의 웹 서버가 복제 지역 캐시를 바로 지우면:
    delete(k) ──▶ 복제 지역 캐시       (빠름)
    DB 변경  ──▶ 복제 지역 DB          (복제 지연, 느림)
    그 사이 miss → 복제 DB에서 옛 값 → set → ✘ 옛 값 고착

  논문의 방식: 복제 지역의 무효화는 그 지역 DB의 mcsqueal이 낸다 = 복제가 도착한 뒤에 지운다
```

- 원본(master) 지역에서 쓰기: 데몬이 무효화하므로 "복제보다 먼저 도착한 무효화" 경합을 피한다(§5).
- 복제 지역에서 쓰기: *remote marker*를 쓴다(§5).
  1. 키 k에 영향을 주는 쓰기 전에 지역에 마커 `rk`를 세운다.
  2. 원본 DB에 쓰면서 `k`와 `rk`를 무효화 대상으로 SQL에 넣는다.
  3. 자기 클러스터에서 `k`를 지운다.
  - 이후 `k`가 miss이면 `rk`가 있는지 본다. 있으면 로컬 복제본 대신 원본 지역에서 읽는다. miss 때 지연을 더 내고 낡은 값을 읽을 확률을 줄이는 거래다.
  - 같은 키를 동시에 고치면 한 작업이 다른 작업의 마커를 지워 낡은 정보가 보일 수 있다고 논문이 적는다. 마커는 캐시와 달리 지워지면 정확성에 영향을 준다.
- 하위 구성 요소가 응답하지 않으면 DB·mcrouter가 삭제를 **버퍼에 쌓았다가** 복구 뒤 재생한다(§5 Operational considerations).

### 6. 장애 격리 — Gutter와 cold cluster warmup

```text
  캐시 서버 한 대 무응답
   ✘ 남은 서버로 재해시 → 핫키(한 서버 요청의 20%)를 받은 서버도 과부하 → 연쇄
   ✔ Gutter 풀(클러스터 서버의 약 1%)로 재요청 → miss면 DB 읽고 Gutter에 짧은 수명으로 넣기
```

- *Gutter*: 실패한 서버 몇 대의 일을 대신 맡는 작은 예비 캐시 풀(§3.3).
  - get에 응답이 없으면 클라이언트가 Gutter에 다시 묻는다. Gutter 항목은 빨리 만료되게 해서 Gutter에 무효화를 보내지 않아도 되게 한다. 대가는 "조금 낡은 데이터"다.
  - 클라이언트가 보는 실패를 99% 줄였고, 매일 실패의 10~25%를 hit로 바꿨다. 서버 한 대가 통째로 죽으면 Gutter 적중률이 대개 4분 안에 35%를 넘고, 50%에 가까워지는 경우가 많다(§3.3).
  - L16 노트의 추측: Gutter는 어떤 키든 가질 수 있어서 모든 무효화를 Gutter에도 보내야 하고, 그러면 삭제 트래픽이 최소 두 배가 된다.
- *Cold cluster warmup*: 빈 클러스터의 클라이언트가 DB 대신 "따뜻한" 클러스터에서 값을 가져와 채운다. 며칠 걸릴 회복이 몇 시간으로 줄었다(§4.3).
  - 위험: cold 클러스터에서 DB를 고친 직후, warm 클러스터에 무효화가 닿기 전에 다른 클라이언트가 warm의 옛 값을 가져오면, cold에 그 값이 무기한 남는다.
  - 대책: cold 클러스터의 삭제를 **2초 hold-off**로 낸다. hold-off 동안 같은 키의 `add`가 거절된다. `add`가 실패하면 "DB에 더 새 값이 있다"는 뜻이므로 DB에서 다시 읽는다. 2초보다 늦는 삭제가 이론상 가능하지만 드물다고 논문이 적는다.

#### 실험: hold-off 삭제를 Redis로 흉내 내기

삭제 대신 2초짜리 묘비(tombstone)를 쓰고, 채우기는 `SET NX`(memcached `add`와 같은 "없을 때만")로 한다. 클라이언트는 묘비를 miss로 취급한다.

(실험, Redis 7.4.9 `redis-cli`, 2026-10-01)

```text
# warm 클러스터에는 아직 무효화가 안 온 옛 값
OK
# DB v2 커밋 → cold 클러스터에 hold-off 2초짜리 삭제(묘비)
OK
# cold miss → warm에서 가져와 add(SET NX)

__holdoff__
# hold-off 이후

OK
v2
```

- hold-off 안의 `SET NX`는 nil(빈 줄)로 거절됐다. 묘비가 그대로 남아 옛 값 v1이 들어가지 못했다.
- 2.2초 뒤 묘비가 사라지자 DB에서 다시 읽은 v2를 넣을 수 있었다.

### 7. 클라이언트 측 캐싱의 무효화 — 추적 테이블이 넘칠 때

- Redis 6+ `CLIENT TRACKING`은 "어느 클라이언트가 어느 키를 읽었나"를 서버의 무효화 테이블에 적고, 키가 바뀌면 그 클라이언트에 무효화를 보낸다. 원리·경합·BCAST는 [database/49-multi-level-caching](../../database/49-multi-level-caching/2-summary.md)에 있다.
- 테이블에는 상한(`tracking-table-max-keys`)이 있다. 새 키가 들어오면 서버가 옛 항목을 "바뀐 척" 무효화하고 지운다(Redis 문서 "Client-side caching").
  - 아무도 쓰지 않았는데 무효화가 쏟아질 수 있다는 뜻이다.

#### 실험: 상한 100인 Redis에서 키 1,000개를 읽기만 하기

전용 일회용 컨테이너 `redis:7-alpine`(7.4.9)을 `--tracking-table-max-keys 100`으로 띄웠다. RESP2 두 연결 방식이다(무효화 연결은 `__redis__:invalidate` 구독, 데이터 연결은 `CLIENT TRACKING on REDIRECT <id>`). 키 1,000개를 먼저 쓰고, 추적 상태에서 읽기만 했다.

(실험, Redis 7.4.9 전용 컨테이너 + Java 21, 2026-10-01)

```text
tracking: OK
keys read=1000, writes after read=0, invalidation messages=900 (keys invalidated=900), tracking_total_keys:100
```

- 쓰기가 0인데 무효화가 900건 왔다. 테이블에 100개만 남기고 나머지는 "바뀐 척" 내보낸 것이다.
- 로컬 캐시는 그 900개를 지운다. 적중률이 떨어지고, 다시 읽으면 또 다른 항목이 밀려나 무효화가 이어진다.
- 로컬 확인: 공용 Redis 7.4.9의 `CONFIG GET tracking-table-max-keys`는 `1000000`이었다.

## 쓰이는 자료구조·알고리즘

- **lease 토큰 = 조건부 쓰기(load-link/store-conditional)** — 읽을 때 받은 토큰이 그대로일 때만 쓴다. 낙관적 동시성의 버전 비교와 같은 발상이다. [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md)
- **키당 발급 간격 제한** — 토큰을 키당 일정 간격에 하나만 주는 것은 키 단위 레이트 리밋이다. 단일 비행(single-flight)과 같은 효과. [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)
- **해시 샤딩 vs 복제** — `hash(k) % n`으로 키를 나누면 메모리 효율이 좋지만 핫키를 못 나눈다. 복제는 핫키 읽기를 나누지만 메모리를 더 쓰고 무효화를 모든 복제본에 보내야 한다(L16, §3.2.3). [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)
- **로그 기반 무효화** — 커밋 로그를 순서대로 읽어 삭제를 만든다. 로그가 남아 있으면 재생으로 복구한다. CDC·outbox와 같은 구조다(16번).
- **추적 테이블(키 → 클라이언트 ID 집합)** — 상한이 있는 맵. 넘치면 축출이 곧 무효화다.
- **묘비(tombstone) + 조건부 add** — hold-off 동안 "없을 때만 넣기"를 거절해 늦은 옛 값을 막는다.
- **LRU 교체** — memcached는 RAM이 제한돼 LRU로 내쫓는다(L16). [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)

## 적용 — 풀어나가는 법

**1) 무엇을 보장할지 먼저 적는다.** "최신 보장"이 필요한 값(잔액·확정 재고)은 캐시하지 않거나 원본에서 읽는다. 나머지는 "얼마나 낡아도 되나"(초 단위 목표)와 "자기가 쓴 것은 바로 보여야 하나"를 정한다.

**2) 채우기 경로에 lease(또는 버전 비교)를 둔다.** Redis라면 위 실험의 Lua 두 개로 시작할 수 있다. 읽기 쪽은 이렇게 쓴다(예시 — `redis.eval`은 클라이언트 라이브러리의 EVAL 호출을 단순화한 것).

```java
long read(int k) {
    while (true) {
        List<Object> r = redis.eval(LGET, List.of(vk(k), lk(k)), List.of("2000"));   // lease 2초
        switch ((String) r.get(0)) {
            case "HIT":   return Long.parseLong((String) r.get(1));
            case "WAIT":  sleepMillis(2); continue;                                 // 다른 클라이언트가 채우는 중
            default: {                                                             // "LEASE"
                long v = db.load(k);
                redis.eval(LSET, List.of(vk(k), lk(k)), List.of((String) r.get(1), Long.toString(v)));
                return v;                                                          // 거절돼도 이번 응답에는 DB 값을 쓴다
            }
        }
    }
}
```

- lease 만료(위 2초)는 "채우던 클라이언트가 죽으면 다음 클라이언트가 이어받는" 시간이다. DB 조회 시간보다 넉넉히 잡는다.
- `WAIT` 재시도에는 상한을 둔다. 상한을 넘으면 DB에서 직접 읽어 응답만 하고 set은 하지 않는다.

**3) 무효화는 커밋 로그에서 만든다.** 웹 서버의 `afterCommit` 삭제는 "자기가 쓴 것 읽기"용으로 두고, 다른 클러스터·지역의 무효화는 CDC(Debezium 등)나 outbox를 읽는 소비자가 낸다. 소비자가 밀리면 무효화도 밀리므로 LAG를 본다.

```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group cache-invalidator   # 무효화 소비자의 LAG
redis-cli INFO stats | grep -E 'keyspace_(hits|misses)|tracking_total_keys'                       # 적중률·추적 키 수
redis-cli INFO keyspace                                                                          # 키 수·만료 키 수
```

**4) 무효화가 실제로 닿는지 표본으로 잰다.** 논문 §7.3처럼 삭제 일부를 표본으로 기록하고, 몇 초·몇 분 뒤 모든 캐시 복사본에 그 키가 남았는지 조회한다. "삭제 후 N초 내 제거율"을 지표로 둔다.

**5) 캐시 서버 장애 대응을 미리 정한다.** 남은 서버로 재해시하지 말고, 작은 예비 풀(Gutter)이나 "짧은 TTL로만 채우는 예비 계층"을 둔다. 캐시가 비었을 때 DB가 버티는지 정기적으로 시험한다.

## 장애 시나리오와 대처

### 1. 늦은 set이 삭제를 덮어써 오래된 값 고착

- **현상**: 쓰기가 몰리는 시간대 뒤에 일부 키만 TTL 내내 옛 값이다. 다시 재현하기 어렵다.
- **보이는 형태**: 에러 없음. 해당 키의 캐시 값과 DB 값을 비교하면 다르다. 삭제 로그는 있고, 삭제 시각보다 뒤에 같은 키의 set 로그가 있다.
- **원인**: 쓰기보다 먼저 DB를 읽은 채우기 요청의 set이 삭제보다 늦게 도착했다. 커밋 뒤 삭제로는 막지 못한다. 위 실험에서 lease 없이 키 200개 중 2~7개가 고착됐다(재실행 포함).
- **대처**: lease(또는 버전 비교 set)로 "삭제 이후의 옛 set"을 거절한다. TTL은 고착 기간의 상한으로 남겨 둔다. 복제본에서 읽어 채운다면 그 지연만큼 더 낡을 수 있으므로, 방금 쓴 키는 원본에서 읽는다(remote marker의 작은 판).

### 2. 무효화 폭풍 — 지울 때마다 DB가 맞는다

- **현상**: 인기 키의 쓰기가 잦아지거나, 대량 무효화(키 버전 올리기·전체 비우기) 직후 DB CPU·커넥션이 치솟는다.
- **보이는 형태**: 캐시 miss율 급증과 같은 시각에 같은 SELECT가 수백 개 동시. DB 커넥션 풀 대기 타임아웃. 위 실험에서 동시 miss 50개 중 26~50개가 DB로 갔다(재실행 포함).
- **원인**: 삭제 직후 그 키를 찾은 읽기들이 값이 다시 채워질 때까지 DB로 갔다. 대량 무효화는 그것을 키 수만큼 곱한다.
- **대처**: lease의 "키당 토큰 하나 + 나머지는 대기"(실험: DB 1회). 조금 낡아도 되는 값은 지운 값을 잠깐 낡은 표시로 주는 stale 응답. 대량 무효화는 나눠서(키 범위·시간) 낸다. 무효화 전송은 묶어서 보낸다(mcsqueal 묶음).

### 3. 무효화 유실·잘못된 라우팅

- **현상**: 특정 클러스터·지역에서만 오래된 값이 사라지지 않는다. 배포·설정 변경 뒤부터다.
- **보이는 형태**: 무효화 표본 모니터링에서 "N초 뒤에도 남은 키" 비율이 오른다. 무효화 소비자의 LAG가 계속 증가하거나 오류 로그가 있다.
- **원인**: 웹 서버가 직접 방송하다 일부가 실패했거나, 라우팅 설정이 틀려 다른 서버로 갔다. 하위 구성 요소가 잠시 응답하지 않았다.
- **대처**: 무효화를 커밋 로그(CDC·outbox)에서 만들어 **재생 가능**하게 한다. 하위가 죽으면 버퍼에 쌓았다가 재생한다(§5). 표본 측정으로 무효화 지연을 지표로 본다.

### 4. 캐시 서버 장애 → 재해시 연쇄

- **현상**: 캐시 서버 한 대가 죽은 뒤 다른 캐시 서버들이 차례로 과부하에 빠지고, DB까지 느려진다.
- **보이는 형태**: 죽은 서버의 키가 몰린 서버의 CPU·네트워크 포화. 그 서버의 응답 지연 증가 → 클라이언트 타임아웃 → DB 직행 증가.
- **원인**: 남은 서버로 키를 재해시하면 핫키(논문 예: 한 서버 요청의 20%)를 받은 서버도 넘친다(§3.3).
- **대처**: 재해시 대신 놀고 있는 소규모 예비 풀(Gutter)로 보낸다. 예비 풀 항목은 짧게 만료시켜 무효화를 보내지 않아도 되게 한다. 핫키는 복제해 읽기를 나눈다.

### 5. 클라이언트 측 캐싱의 가짜 무효화

- **현상**: 로컬(L1) 캐시를 켰는데 적중률이 기대보다 낮고, Redis가 보내는 무효화 메시지 수가 쓰기 수보다 훨씬 많다.
- **보이는 형태**: 무효화 채널 메시지 급증, `INFO stats`의 `tracking_total_keys`가 `tracking-table-max-keys`에 붙어 있다. 위 실험에서 쓰기 0건에 무효화 900건.
- **원인**: 추적하는 키가 테이블 상한을 넘어 서버가 옛 항목을 "바뀐 척" 무효화했다.
- **대처**: 상한을 추적 키 수에 맞추거나, `OPTIN`으로 정말 로컬에 둘 키만 추적하거나, 서버 메모리를 쓰지 않는 BCAST(접두사 방송)로 바꾼다. 무효화 연결이 끊기면 로컬 캐시를 전부 비운다(Redis 문서).

## 핵심 문장

- 대규모 캐시의 일관성 목표는 "한 번도 낡지 않음"이 아니라 "낡은 값이 고착되지 않고, 낡은 기간이 짧음"이다(memcache 논문: 최선 노력 최종 일관성 + 자기가 쓴 것 읽기).
- 쓰기 때 갱신하지 않고 지운다. 삭제는 어떤 순서로 도착해도 결과가 같다.
- 커밋 뒤 삭제로도 "쓰기 전에 읽은 값의 늦은 set"은 못 막는다. lease 토큰이 그 set을 거절한다.
- lease를 키당 하나만 주면 지운 직후 몰리는 miss가 DB 한 번으로 줄어든다(논문: 최대 17K/s → 1.3K/s).
- 무효화는 커밋 로그에서 만들고 묶어서 보내야 재생할 수 있고 패킷 부담도 준다. 복제 지역은 그 지역 DB가 복제를 받은 뒤 지운다.
- 캐시 서버가 죽으면 재해시보다 예비 풀이 안전하고, 빈 클러스터를 데울 때는 hold-off 삭제로 늦은 옛 값을 막는다.

## 관련 주제·근거

- 선행
  - [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md) — cache-aside, 커밋 후 삭제, stale set의 기초, 스탬피드·관통·눈사태
- 연결
  - [database/49-multi-level-caching](../../database/49-multi-level-caching/2-summary.md) — 로컬 L1 + Redis L2, `CLIENT TRACKING`·BCAST·두 연결 경합
  - [database/31-cache-key-versioning-and-serialization](../../database/31-cache-key-versioning-and-serialization/2-summary.md) — 키 버전으로 대량 무효화
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 복제 지연
  - [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md) — 조건부 쓰기
  - [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md) — 싱글플라이트·확률적 조기 갱신
  - [06-replication-strategies](../06-replication-strategies/2-summary.md) — 단일 리더 복제와 복제 지연
  - [07-consistency-models](../07-consistency-models/2-summary.md)(최종 일관성·세션 보장), [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md)(커밋 로그 기반 무효화)
  - [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md) · [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- 논문·강의
  - R. Nishtala 외, "Scaling Memcache at Facebook", NSDI 2013 — §2 look-aside·삭제(멱등), §3.2.1 Leases(stale set·thundering herd, 64비트 토큰, LL/SC, 키당 10초, 17K/s → 1.3K/s, stale values), §3.2.3 풀 안 복제, §3.3 Gutter(약 1%, 실패 99% 감소, 10~25% hit, 4분 내 35%, 핫키 20%), §4.1 Regional Invalidations(mcsqueal, 4%, 18배, 웹 서버 방송의 문제, 로그 재생), §4.3 Cold Cluster Warmup(2초 hold-off), §5 Across Regions(원본 지역 데몬 무효화, remote marker, 버퍼·재생), §7.3 Invalidation Latency(100만 건 중 1건 표본, 99.99%/1초 등) <https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf>
  - MIT 6.5840 Spring 2026 Lecture 16 "Scaling Memcache at Facebook" 노트 — look-aside 의사코드, 99% 적중률·1% 하락 시 DB 부하 2배, 샤딩 vs 복제, 최종 일관성 + read-your-own-writes, stale set 경합과 lease, "DB가 직접 채우면?" 문답, Gutter 무효화 질문 <https://pdos.csail.mit.edu/6.824/notes/l-memcached.txt>
- 제품 문서
  - Redis "Client-side caching reference" — 무효화 테이블·상한 도달 시 가짜 무효화, 두 연결 경합, 연결 끊김 시 비우기, BCAST·OPTIN·NOLOOP <https://redis.io/docs/latest/develop/reference/client-side-caching/> (원문 markdown: redis/redis-doc `docs/manual/client-side-caching.md`)
- 실험(scratchpad, 2026-10-01)
  - `LeaseCache.java` — 공용 Redis 7.4.9(키 `w32:`) + Java 21: 순서 고정 경합(lease 유무), 키 200개·3초 경합 뒤 고착 키 수(lease 없이 3·4, lease 0·0 — 점검 재실행 2~7 vs 0), 핫키 동시 miss 50개의 DB 조회 수(26 vs 1 — 점검 재실행 31~50 vs 1). DB는 프로세스 안 맵(시뮬레이션)
  - `redis-cli` hold-off 흉내 — 2초 묘비 + `SET NX` 거절 → 만료 뒤 v2 채움(공용 Redis 7.4.9)
  - `TrackingEvict.java` — 전용 일회용 `redis:7-alpine`(7.4.9, `--tracking-table-max-keys 100`)에서 키 1,000개 읽기만 → 무효화 900건, `tracking_total_keys:100`
