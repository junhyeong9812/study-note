# distributed/13-distributed-id-generation — Snowflake·UUIDv7·시퀀스 블록 — 정리 (힌트)

## 해결하는 문제

여러 서버가 각자 ID를 만들어야 한다. 겹치면 안 되고, 가능하면 시간 순으로 정렬되면 좋다.

```text
                         조율         정렬         크기      약점
  DB 시퀀스 1개           매번 DB 왕복  있음         64비트    한 곳이 병목·단일 장애점
  UUIDv4(무작위)          없음         없음         128비트   인덱스 아무 데나 꽂힘
  Snowflake              없음(ID 배정만) 대체로 시간순  64비트    시계·worker ID에 의존
  UUIDv7                 없음         대체로 시간순  128비트   시계에 의존, 노드 구분은 확률
  시퀀스 블록(구간 할당)    구간마다 한 번  구간 안에서만  64비트    재시작 시 남은 구간 공백
```

- 트위터가 Snowflake를 만든 이유(2010 README): MySQL에서 Cassandra로 옮기는데 Cassandra에는 순차 ID 기능이 없었다.
  - 요구: 프로세스당 초당 1만 개 이상, 서로 조율하지 않음, "(대략) 시간 순"(k-sorted, 목표 1초 이내), 객체를 읽지 않고 정렬 가능, 64비트 이하.
  - *k-sorted*: 완전히 정렬되지는 않았지만 각 원소가 제자리에서 일정 범위 안에 있다.

쉬운 예: 전국 지점의 영수증 번호를 "날짜-지점-순번"으로 만든다.
- 본사에 묻지 않아도 지점 번호가 다르니 안 겹친다.
- 앞자리가 날짜라 대체로 시간 순이다.

똑같은 구조다.\
대신 지점 번호를 두 지점에 잘못 주거나, 날짜를 거꾸로 돌리면 번호가 겹친다.

실무 예:
- 샤딩한 DB의 주문 ID, 채팅 메시지 ID, 이벤트 ID.
- PostgreSQL 18의 `uuidv7()`, JPA `@SequenceGenerator(allocationSize = 50)`.

## 동작·원리

### 1. Snowflake — 시각 | 노드 | 순번

```text
  비트  63   62 ─────────── 22  21 ── 17  16 ── 12  11 ────── 0
       [0] [ 시각(ms) 41비트  ][ DC 5  ][ 워커 5 ][ 순번 12비트 ]
            twepoch(1288834974657 = 2010-11-04 UTC)부터 경과 ms

  id = ((ts - twepoch) << 22) | (dc << 17) | (worker << 12) | seq
```

- 트위터 원본(`IdWorker.scala`, snowflake-2010 브랜치)의 배치다.
  - 노드 10비트는 데이터센터 5비트 + 워커 5비트로 나뉜다. README는 "machine id 10 bits, 1024대"로 적는다.
  - 41비트 ms ≈ 69년(README: "custom epoch gives us 69 years").
- 생성 규칙(원본 `nextId`)

```text
  now < lastTs          → 예외 InvalidSystemClock("Clock moved backwards...")
  now == lastTs         → seq = (seq + 1) & 4095,  seq가 0으로 돌면 다음 ms까지 바쁜 대기(tilNextMillis)
  now > lastTs          → seq = 0
  lastTs = now
```

- `lastTs`는 **메모리 변수**다. 프로세스가 재시작하면 -1로 돌아간다(실험 2).
- README의 시계 의존 설명: NTP로 시계를 맞추되, 시계가 뒤로 가면 마지막 시각이 지날 때까지 발급을 거부한다. 더 나은 방법은 NTP가 시계를 뒤로 옮기지 않는 모드로 돌리는 것이라고 적는다. 시계를 점프 대신 서서히 맞추는 slew 방식이 그런 모드다.
  - *slew*: 시계를 한 번에 점프시키지 않고 속도를 조금 바꿔 서서히 맞추는 방식.

### 2. UUIDv7 — 시각 | 무작위 (RFC 9562 §5.7)

```text
  비트  0 ─────────────── 47  48─51  52 ──── 63  64─65  66 ─────────────── 127
       [ unix_ts_ms 48비트 ][ver=7][ rand_a 12 ][var=10][ rand_b 62비트       ]
```

- 앞 48비트가 Unix ms다. 바이트 순 정렬이 곧 ms 순이다.
- 같은 ms 안의 순서는 선택 사항이다. RFC §6.2의 세 방법
  - Method 1: rand_a(앞쪽) 일부를 **고정 길이 카운터**로 쓴다.
  - Method 2: 무작위 값을 시작점으로 삼아 생성마다 **증가**시킨다.
  - Method 3: rand_a 12비트를 **ms 미만 시각**으로 채운다.
- 노드 구분 비트는 없다. 서로 다른 노드가 같은 ms에 만들어도 무작위 비트(rand_a·rand_b 합쳐 최대 74비트 — 위 Method로 카운터·ms 미만 시각에 쓰면 그만큼 준다)로 충돌 확률을 낮춘다(§6.4). 노드 id를 넣고 싶으면 UUIDv8을 쓰라고 한다.
- 시계가 뒤로 가는 경우: RFC는 "직전 UUID보다 큰지 검사하고, 아니면 직전 시각을 재사용해 카운터를 올리거나 최소한 에러를 보고하라"고 권한다(§6.2 Monotonic Error Checking).
- PostgreSQL 18의 `uuidv7()`(소스 `src/backend/utils/adt/uuid.c`)
  - Method 3을 쓴다. rand_a 12비트에 ms 미만 시각을 넣는다.
  - 같은 **백엔드(세션)** 안에서는 직전 값보다 최소 한 단계 큰 시각을 쓴다. 시계가 뒤로 가도 그 세션 안에서는 증가가 유지된다. 세션 사이 순서는 보장하지 않는다.

### 3. 시퀀스 블록 — 중앙 카운터에서 구간을 빌린다

```text
  중앙 카운터(DB 시퀀스·Redis INCRBY)
       │ INCRBY 100 → 100         │ INCRBY 100 → 200
       ▼                          ▼
  인스턴스 A: 1..100 로컬 발급    인스턴스 B: 101..200 로컬 발급
       │ 소진 → INCRBY 100 → 300 (A는 201..300)
       ▼
  A 재시작: 남은 번호는 버려진다(공백). 새 구간을 다시 빌린다.
```

- 조율은 **구간마다 한 번**이다. 나머지는 메모리에서 낸다.
- 같은 아이디어가 제품에 들어 있다.
  - PostgreSQL 18 `CREATE SEQUENCE ... CACHE n`: 세션마다 n개를 미리 받는다. 쓰지 못한 값은 세션이 끝나면 사라져 "구멍"이 생긴다. 여러 세션을 합쳐 보면 생성 순서와 값 순서가 다를 수 있다(문서 Notes).
  - Jakarta Persistence `@SequenceGenerator`의 `allocationSize` 기본값 50.
- 보장 범위: 유일성은 중앙 카운터의 원자성, 그리고 이미 빌려준 구간의 카운터 값이 장애 복구·복제 전환 뒤에도 되돌아가지 않는 내구성에서 나온다(예: Redis 비동기 복제·영속화 설정에 따라 확인된 `INCRBY`도 잃을 수 있다 — redis.io replication·persistence 문서). 시간 순은 구간 안에서만이다.

### 실험 1: Snowflake — 시계 역행, worker ID 중복, 노드 간 순서

- 코드: `Snow.java`. 원본과 같은 41|5|5|12 배치. 시계는 주입한 가짜 시계(`FakeClock`)로 되감는다 — OS 시계를 실제로 돌리지 않았다.

```java
long next() {
    long ts = clock.now;
    if (guard && ts < lastTs) throw new IllegalStateException("Clock moved backwards. Refusing for " + (lastTs - ts) + "ms");
    if (ts == lastTs) {
        seq = (seq + 1) & 4095;
        if (seq == 0) { while (clock.now <= lastTs) clock.now++; ts = clock.now; }
    } else seq = 0;
    lastTs = ts;
    return ((ts - EPOCH) << 22) | (dc << 17) | (worker << 12) | seq;
}
```

(실험, eclipse-temurin 21 JDK 컨테이너, 2026-10-01)

```text
== 2. 시계 역행 — 실행 중(lastTs가 메모리에 있음) vs 재시작 직후(lastTs 잃음) ==
실행 중 역행: 예외 — Clock moved backwards. Refusing for 499ms
재시작 후 되돌아간 500ms 구간에서 2500개 발급 → 중복 2500개 (보호 장치 guard=true여도)

== 3. 같은 worker ID를 두 인스턴스가 받으면 ==
1초 동안 각자 3000개(밀리초당 3개) → 전체 6000개 중 중복 3000개
worker ID가 다르면: id=2102038474650710016 ts=1790000001000 dc=1 worker=7 seq=0 / id=2102038474650714112 ts=1790000001000 dc=1 worker=8 seq=0

== 4. 노드 간 순서: B 시계가 3ms 느리면 나중에 만든 id가 더 작다 ==
먼저 만든 A: id=2102038470456504320 ts=1790000000000 dc=1 worker=31 seq=0
나중 만든 B: id=2102038470447992832 ts=1789999999998 dc=1 worker=1 seq=0
id 정렬상 B가 앞 (실제 순서와 반대)

== 5. 순번 고갈: 1ms에 5000개 요청 ==
첫 id 시각 1790000000000, 마지막 id 시각 1790000000001 → 4096개 뒤 다음 ms로 넘어감 (+1ms)
```

- 관찰
  - 실행 중 역행은 예외로 막혔다. 그러나 재시작한 프로세스는 `lastTs`를 잃어 되돌아간 구간의 ID를 **전부** 다시 냈다.
  - 같은 worker ID 두 개는 같은 ms·같은 순번에서 정확히 같은 ID를 낸다. 6000개 중 3000개가 중복이었다.
  - 시계가 3ms 어긋나면 나중에 만든 ID가 더 작다. Snowflake의 "시간 순"은 노드 사이에서는 시계 어긋남만큼 흐트러진다.
  - 출력 1번(비트 배치 확인)은 `41비트 시각 한계(년): 69.7, twepoch 기준 소진 시각: Wed Jul 10 17:30:30 UTC 2080`이었다.

### 실험 2: PostgreSQL 18 — bigint·UUIDv4·UUIDv7 기본 키 인덱스

- 코드: `pk.sql`. 세 테이블에 1000행씩 200번, 20만 행. `pgstattuple`의 `pgstatindex`로 B-tree 상태를 본다. 전용 일회용 컨테이너 `sn-dw-w05-pg`(postgres:18 이미지).

(실험, PostgreSQL 18.6 단일 노드, 2026-10-01)

```text
 pk  | idx_size | leaf_pages | avg_leaf_density | leaf_fragmentation 
-----+----------+------------+------------------+--------------------
 seq | 4408 kB  |        547 |            89.95 |                  0
 v4  | 8376 kB  |       1039 |            66.46 |              49.18
 v7  | 6184 kB  |        767 |            89.91 |                  0

 pk | smaller_than_prev |   n    
----+-------------------+--------
 v4 |            100054 | 200000
 v7 |                 0 | 200000

                  id                  | ver |             ts             
--------------------------------------+-----+----------------------------
 01a0f4fc-73a7-71e0-bc45-397e2195d42b |   7 | 2026-10-01 01:03:00.519+00
 01a0f4fc-73a7-7466-87b1-46ed1825351a |   7 | 2026-10-01 01:03:00.519+00
 01a0f4fc-73a7-7478-a737-3dd630ca35c1 |   7 | 2026-10-01 01:03:00.519+00
```

- 관찰
  - v4는 삽입 순서에서 앞 행보다 작은 키가 절반(100054/200000)이다. 리프가 약 2/3만 찼고 단편화가 49%다.
  - v4 수치는 무작위라 실행마다 조금 다르다. 같은 스크립트를 두 번 더 돌리면 8608 kB·리프 1068·밀도 64.66·단편화 49.81(작은 키 100081개), 8392 kB·리프 1041·밀도 66.33·단편화 49.47(작은 키 99927개)이었다. bigint·v7 행은 매번 같았다.
  - v7은 한 세션 안에서 한 번도 줄지 않았다(0). 같은 ms(.519) 안의 세 값도 rand_a 자리(`71e0` < `7466` < `7478`)가 커지며 정렬됐다.
  - v7의 크기 차이(6184 kB vs 4408 kB)는 순서가 아니라 키 길이(16바이트 vs 8바이트) 때문이다. 밀도는 둘 다 약 90%다. PostgreSQL B-tree 기본 fillfactor 90과 같은 값이다(database/28이 문서로 확인).
  - 같은 비교를 PostgreSQL 17에서 SQL 함수로 만든 v7로 한 결과는 [database/28](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)에 있다. 이 실험은 18의 내장 `uuidv7()`로 같은 경향을 확인했다.

### 실험 3: 시퀀스 블록(Redis 7.4.9 `INCRBY`)과 JavaScript 정밀도

- 코드: `block.js`. 공용 `sn-dw-redis`의 `w05:order_seq` 키만 쓰고 지웠다. 두 인스턴스 A·B가 100개씩 구간을 받아 번갈아 250개씩 발급한다.

(실험, Redis 7.4.9 · Node 18.19.1, 2026-10-01)

```text
A 첫 3개 1,2,3, B 첫 3개 101,102,103
500개 발급, 중앙 왕복 A 3회 + B 3회, 중복 0개
시간 순으로 나열했을 때 앞 id보다 작은 id: 247/499
A 재시작: 버려진 구간 451~500 (50개 번호 공백), 재시작 후 첫 id 601
Redis 현재 값 700
정리: EXISTS w05:order_seq = 0
JSON.parse({"id": 2102038470456406017}).id = 2102038470456406000  (Number.MAX_SAFE_INTEGER = 9007199254740991)
BigInt로 문자열에서: 2102038470456406017
```

- 관찰
  - 500개에 중앙 왕복 6번. 중복 0.
  - 발급 시간 순으로 보면 거의 절반(247/499)이 앞보다 작다. 블록 방식은 인스턴스 사이 순서를 주지 않는다.
  - 재시작하면 남은 구간(451~500)이 사라진다.
  - Snowflake ID를 JSON 숫자로 받으면 JavaScript `Number`에서 끝자리가 바뀐다(…017 → …000).

## 쓰이는 자료구조·알고리즘

- **비트 필드 패킹** — 시프트·OR로 붙이고 시프트·마스크로 꺼낸다. [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)
- **B+Tree 오른쪽 끝 삽입** — 증가하는 키는 가장 오른쪽 리프에만 들어가 페이지가 꽉 차고 분할이 끝쪽에서만 난다. 무작위 키는 중간 페이지를 반씩 쪼갠다. [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md) · [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **단조 검사(마지막 값 기억)** — `now < lastTs`면 거부, 또는 직전 값 + 1. 기억이 메모리에만 있으면 재시작에 무력하다.
- **원자적 증가(fetch-and-add)** — 블록 할당의 유일성 근거. Redis `INCRBY`, DB 시퀀스.
- **리스(lease)** — worker ID를 중앙에서 기한부로 빌린다(10·12번).
- **생일 문제 확률** — UUIDv7·v4의 충돌 가능성을 무작위 비트 수로 가늠한다(RFC 9562 §6.7·§6.9).

## 적용 — 풀어나가는 법

### 1. 고르는 순서

1. **누가 ID를 소비하나**: DB 키로만 쓰나, URL·외부 API에 나가나. 외부로 나가면 시각·발급량이 드러난다(장애 5).
2. **64비트가 필요하나**: 저장·인덱스 크기, 기존 `bigint` 스키마 → Snowflake 또는 블록. 128비트를 감당하면 UUIDv7이 worker ID 배정 문제를 없앤다.
3. **노드 간 순서가 의미 있나**: 어느 방식도 노드 사이 정확한 순서는 주지 않는다. 필요하면 단일 리더 순번이나 논리 시계(05번)다.
4. **시계 역행 정책**: 거부(Snowflake)·직전 시각 재사용(RFC 9562 권고)·마지막 발급 시각 영속화.

### 2. Java — UUIDv7 생성(Method 1: 12비트 카운터, 시계 역행 시 직전 시각 재사용)

```java
public final class UuidV7 {
    private final SecureRandom rnd = new SecureRandom();
    private long lastMs = -1; private int counter;

    public synchronized UUID next() {
        long now = System.currentTimeMillis();
        if (now > lastMs) { lastMs = now; counter = rnd.nextInt(1 << 11); }   // 카운터를 무작위 절반 아래에서 시작
        else if (++counter > 0xFFF) { lastMs++; counter = 0; }                // 같은 ms(또는 역행): 카운터 증가, 넘치면 시각을 한 칸 민다
        long msb = (lastMs << 16) | (0x7L << 12) | counter;                   // 48비트 시각 | ver 7 | rand_a 자리 = 카운터
        long lsb = (rnd.nextLong() & 0x3FFFFFFFFFFFFFFFL) | 0x8000000000000000L; // var 10 | rand_b 62비트
        return new UUID(msb, lsb);
    }
}
```

- 로컬 확인(eclipse-temurin 21 JDK): 10만 개를 연속 생성해 문자열 비교로 직전보다 작거나 같은 값 0개, `version=7 variant=2`.
- `lastMs`가 메모리에만 있으므로 재시작 후 역행은 막지 못한다. 다만 v7은 무작위 62비트가 남아 같은 값이 다시 나올 확률이 매우 작다. Snowflake와 다른 점이다.

### 3. worker ID 배정 — 중앙에서 리스로

```bash
# etcd 3.6.5: 30초 리스를 받고, 키가 아직 없을 때만(create revision = 0) worker 7 자리를 잡는다
E="docker exec -i sn-dw-etcd1 etcdctl --endpoints=http://sn-dw-etcd1:2379,http://sn-dw-etcd2:2379,http://sn-dw-etcd3:2379"
L=$($E lease grant 30 | awk '{print $2}')
for h in host-a host-b; do
  printf 'create("/w05/idgen/worker/7") = "0"\n\nput /w05/idgen/worker/7 %s --lease=%s\n\nget /w05/idgen/worker/7\n\n' $h $L | $E txn
done
```

(실험, 공용 etcd 3.6.5 3노드, 키 `/w05/` 접두사, 실행 뒤 키 삭제·리스 해제, 2026-10-01)

```text
SUCCESS

OK
FAILURE

/w05/idgen/worker/7
host-a
```

- host-a는 자리를 잡았고, host-b의 같은 요청은 비교(create revision = 0)가 실패해 이미 잡은 주인(host-a)만 확인했다. 같은 번호를 둘이 잡는 일은 이 트랜잭션이 막는다.
- 운영에서는 `etcdctl lease keep-alive <LEASE_ID>`(또는 클라이언트 라이브러리의 keep-alive)로 리스를 유지한다.
- 리스를 잃은 인스턴스는 **즉시 발급을 멈춰야** 한다. 멈췄다 깨어난(GC·VM 정지) 옛 인스턴스가 계속 발급하면 같은 번호를 쓰게 된다(12번 fencing과 같은 문제).

### 4. 진단

```sql
-- PostgreSQL: 기본 키 인덱스 상태
SELECT * FROM pgstatindex('orders_pkey');            -- avg_leaf_density, leaf_fragmentation
-- UUIDv7이면 시각·버전을 꺼내 본다 (PostgreSQL 18)
SELECT uuid_extract_version(id), uuid_extract_timestamp(id) FROM orders ORDER BY id DESC LIMIT 5;
```

```bash
docker exec sn-dw-redis redis-cli GET w05:order_seq   # 블록 카운터 현재 값 (예시 키)
```

- Snowflake ID는 시프트로 해독해 `ts`·`worker`를 로그에 함께 남긴다. 중복이 나면 두 행의 worker가 같은지, 시각이 역행 구간인지 바로 본다.

## 장애 시나리오와 대처

### 1. 시계 역행 → ID 중복·역순 (커리큘럼 ⚠)

- **현상**: 가끔 `duplicate key value violates unique constraint`가 난다. upsert라면 남의 행을 조용히 덮는다.
- **보이는 형태**: 중복된 두 ID를 해독하면 같은 worker, 같은 ms, 같은 순번. 발생 시각이 NTP 점프·VM 이동·재시작 직후다.
- **원인**: 시각이 뒤로 갔다. 실행 중이면 `lastTs` 검사가 막지만, 재시작으로 `lastTs`를 잃으면 이미 쓴 ms를 다시 쓴다(실험 1-2: 2500개 중 2500개 중복).
- **대처**
  - 마지막 발급 시각(또는 그보다 넉넉한 미래 값)을 주기적으로 영속화하고, 기동 시 그 시각이 지날 때까지 발급을 미룬다. RFC 9562 §6.3도 안정 저장소에 마지막 시각을 두는 방법을 적는다.
  - NTP를 slew 모드로 둬 시계가 뒤로 점프하지 않게 한다(Snowflake README).
  - 역행 감지 시 예외 수를 지표로 내보내 알람을 건다.

### 2. worker ID 중복 할당 (커리큘럼 ⚠)

- **현상**: 오토스케일로 뜬 인스턴스와 기존 인스턴스가 같은 ID를 만든다.
- **보이는 형태**: 중복 ID의 worker 필드가 같고, 발급 로그의 호스트가 다르다. 실험 1-3에서 절반이 중복이었다.
- **원인**: worker ID를 설정 파일·환경 변수·이미지에 고정했거나, 재시작 때 무작위로 골랐다.
- **대처**: 중앙(etcd·ZooKeeper·DB)에서 원자적으로 리스를 잡는다. 리스 갱신 실패 시 발급 중지. 회수한 번호는 옛 주인의 마지막 발급 시각이 지난 뒤 재사용한다. UUIDv7로 바꾸면 이 배정 문제 자체가 사라진다(대신 128비트).

### 3. 64비트 ID가 JavaScript에서 깨진다

- **현상**: 프런트에서 받은 ID로 조회하면 "없는 주문"이다.
- **보이는 형태**: 서버 로그의 ID와 브라우저 ID가 끝 몇 자리만 다르다(실험 3: …017 → …000).
- **원인**: JSON 숫자를 `Number`(IEEE 754 배정밀도)로 읽으면 2^53−1(9007199254740991)을 넘는 정수는 정확하지 않다. Snowflake ID는 시각이 22비트 위에 있어 epoch 뒤 2^31 ms(약 25일)만 지나도 이 값을 넘는다.
- **대처**: API에서는 ID를 **문자열**로 내보낸다(Jackson `@JsonFormat(shape = STRING)` 등). JS 안에서 연산이 필요하면 `BigInt`.

### 4. ms당 순번 고갈 → 발급 지연

- **현상**: 순간 부하에 ID 발급 p99가 튄다.
- **보이는 형태**: CPU가 바쁜 대기(`tilNextMillis`)에 쓰인다. 실험 1-5처럼 4096개 뒤 다음 ms로 넘어간다.
- **원인**: 한 worker가 1ms에 4096개를 넘게 요청받았다.
- **대처**: worker 수를 늘리거나(프로세스·스레드별 ID), 순번 비트를 늘린 변형을 쓴다. 대기 횟수를 지표로 낸다.

### 5. ID가 정보를 흘린다·블록 공백을 오해한다

- **현상**: 경쟁사가 ID로 가입 시점·발급 속도를 추정한다. 또는 "번호가 비었으니 주문이 삭제됐다"고 오해해 감사 이슈가 된다.
- **보이는 형태**: Snowflake·UUIDv7에서 생성 시각이 바로 나온다(`uuid_extract_timestamp`). 블록 방식은 재시작 때 남은 구간만큼 번호 공백(실험 3: 451~500).
- **원인**: 시각을 앞에 둔 설계의 부작용, 블록 할당의 구조적 공백.
- **대처**: 외부 노출 ID는 따로 둔다(database/28). 연속 번호가 법적·업무 요건이면 ID와 별도로 트랜잭션 안에서 매기는 번호를 둔다.

## 핵심 문장

- 분산 ID는 "조율 없이 유일"과 "대체로 시간 순"을 얻으려고 시각을 앞자리에 둔다. 그래서 시계에 의존한다.
- Snowflake는 시각 41 | DC 5 | 워커 5 | 순번 12다. 유일성의 근거는 "worker ID가 서로 다르다"와 "시계가 뒤로 가지 않는다(재시작 뒤 이미 쓴 ms를 다시 쓰지 않는 것 포함)" 두 가정이다.
- 실행 중 역행은 `lastTs` 검사로 막지만, 재시작 후 역행은 마지막 시각을 영속화해야 막는다.
- UUIDv7은 노드 비트 없이 무작위 비트(최대 74비트, 카운터·ms 미만 시각에 쓴 만큼 줄어든다)로 충돌을 피하고, 같은 ms 안 순서는 카운터나 ms 미만 시각으로 보탠다.
- 시퀀스 블록은 구간마다 한 번만 조율하는 대신 인스턴스 사이 순서가 없고, 재시작 때 쓰지 않은 구간이 남아 있으면 번호 공백이 생긴다.
- 어느 방식도 노드 사이의 정확한 발생 순서는 주지 않는다. 순서가 계약이면 단일 순번이나 논리 시계가 필요하다.

## 관련 주제·근거

- 기초: [ops-patterns/13-snowflake](../../ops-patterns/13-snowflake/2-summary.md) — 비트 패킹·순번·역행 예외 구현과 테스트. 이 노트는 UUIDv7·시퀀스 블록, 재시작 역행, 실제 DB 인덱스 측정을 보탠다.
  - 참고: 원본 「동작·원리」는 노드를 "10비트"로만 그린다. 트위터 원본 코드(`IdWorker.scala`)는 데이터센터 5비트 + 워커 5비트로 나눈다(README는 "machine id 10 bits"로 요약).
  - 참고: 원본은 "시계가 뒤로 가면 던지는 것이 유일하게 안전한 선택"이라고 쓴다. 던지기는 실행 중 역행만 막는다. 재시작 뒤 역행은 마지막 시각 영속화가 필요하다(실험 1-2). 또 RFC 9562 §6.2는 직전 시각을 재사용해 카운터를 올리는 방법도 권한다.
- 선행: [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md)
- 연결
  - [05-logical-clocks](../05-logical-clocks/2-summary.md) — 노드 사이 순서가 필요할 때
  - [10-leader-election](../10-leader-election/2-summary.md) · [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) — worker ID 리스와 펜싱
  - [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md) — 내부 PK vs 외부 ID, PostgreSQL 17에서의 v4/v7 인덱스 재현
  - [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md) · [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)
  - [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)
- 원본·표준
  - Twitter Snowflake README·`IdWorker.scala`(snowflake-2010 브랜치) — 요구사항, 41|5|5|12, twepoch 1288834974657, 역행 시 `InvalidSystemClock` <https://github.com/twitter-archive/snowflake/tree/snowflake-2010>
  - RFC 9562 (2024) — §5.7 UUIDv7 배치, §6.2 Method 1~3·Monotonic Error Checking, §6.3 생성기 상태, §6.4 분산 생성, §6.11 정렬 <https://www.rfc-editor.org/rfc/rfc9562>
- 제품 문서·소스
  - PostgreSQL 18 9.14 UUID Functions — `uuidv4()`·`uuidv7()`·`uuid_extract_timestamp()` <https://www.postgresql.org/docs/18/functions-uuid.html>, 소스 `src/backend/utils/adt/uuid.c`(REL_18_STABLE: Method 3, 백엔드별 단조 증가)
  - PostgreSQL 18 CREATE SEQUENCE — `CACHE`, 세션 종료 시 구멍, 세션 간 순서 비보장 <https://www.postgresql.org/docs/18/sql-createsequence.html>
  - Jakarta Persistence `SequenceGenerator.allocationSize` 기본 50 (jakartaee/persistence 소스)
- 교재: DDIA 1판 9장 "Sequence Number Ordering"(노드별 번호·블록 할당·물리 시각 타임스탬프가 인과와 맞지 않는 이유)
- 실험 목록
  - `Snow.java` — 41|5|5|12 Snowflake, 가짜 시계로 역행·재시작·worker 중복·시계 어긋남·순번 고갈. eclipse-temurin 21 JDK 컨테이너.
  - `pk.sql` — PostgreSQL 18.6 전용 일회용 컨테이너, bigint·`uuidv4()`·`uuidv7()` PK 20만 행, `pgstatindex`.
  - `block.js` — 공용 Redis 7.4.9 `INCRBY` 구간 할당(키 `w05:order_seq`, 실험 후 삭제), Node 18 `JSON.parse` 정밀도.
