# distributed/12-coordination-and-fencing — 조정 서비스(ZooKeeper·etcd)·분산 락·fencing token — 정리 (힌트)

## 해결하는 문제

서버 여러 대가 "지금은 나만 이 자원을 쓴다", "지금 설정은 이것이다", "리더는 저 서버다"에 **같은 답**을 가져야 할 때가 있다.\
각자 DB 행 하나로 이것을 흉내 내면 그 DB가 단일 장애점이 되거나, 장애 때 답이 갈라진다.

```text
 조정 서비스가 없을 때                       조정 서비스(합의 저장소)가 있을 때
 앱1 ─┐                                     앱1 ─┐
 앱2 ─┼─> "락 표" 행 하나 (DB 한 대)          앱2 ─┼─> ZooKeeper / etcd (3~5대, 합의로 복제)
 앱3 ─┘    DB가 죽으면 아무도 못 잡음          앱3 ─┘    과반이 살아 있으면 답이 하나
```

- *조정 서비스(coordination service)*: 작은 데이터를 합의로 복제해 두고, 락·리더 선출·설정·멤버십 같은 조정 기능의 재료(세션·lease·watch·순번)를 주는 서비스. ZooKeeper, etcd가 대표다.
- 그런데 조정 서비스로 락을 잡아도 **락만으로는 막지 못하는 사고**가 하나 남는다.
  - 락을 쥔 프로세스가 멈췄다 깨어나면, 락은 이미 남에게 넘어갔는데 본인은 모른다.
  - 그 프로세스의 늦은 쓰기를 막는 것이 **fencing token**이다.

쉬운 예: 회의실 예약이다.
- 예약 시스템(조정 서비스)이 "14시 회의실은 A팀"이라고 정한다. 예약은 30분 뒤 자동 해제된다.
- A팀 발표자가 졸다가(멈춤) 15시에 들어와 화이트보드를 지운다. 그 사이 B팀이 예약해 쓰고 있었다.
- 막으려면 화이트보드(자원)가 "지금 예약 번호 42번만 쓸 수 있다"를 확인해야 한다. 41번은 거절한다.

똑같은 구조다.\
실무 예: 배치 잡 단일 실행, 파일·객체 저장소에 한 작성자만 쓰기, HBase가 겪은 GC 멈춤 사고(Kleppmann 2016이 인용), Kubernetes·Kafka(구 ZooKeeper 모드)의 조정.\
기초(락의 세 부품 만료·소유자·토큰, FencedStore 구현)는 원본 [ops-patterns/11-distributed-lock](../../ops-patterns/11-distributed-lock/2-summary.md) 「동작·원리」에 있다. 이 노트는 실제 조정 서비스 위에서 그것을 다시 보고 실험한다.

## 동작·원리

### 1. 조정 서비스가 주는 네 가지 재료

| 재료 | ZooKeeper (Hunt 외 2010) | etcd 3.6 | 쓰임 |
|---|---|---|---|
| 합의로 정렬된 쓰기 | 쓰기는 linearizable, Zab으로 순서화, 번호 zxid | Raft, 전역 revision | 모두가 같은 순서로 본다 |
| 클라이언트 생존 표시 | 세션 + `EPHEMERAL` znode(세션 끝나면 삭제) | lease + 키에 lease 부착(만료되면 삭제) | 죽은 소유자의 락 자동 해제 |
| 줄 세우기 | `SEQUENTIAL` 플래그(이름 뒤에 순번) | 키의 `create_revision` | 누가 먼저인가 |
| 변경 알림 | watch(한 번 울리는 알림) | watch(revision부터 이어 받기) | 폴링 없이 기다리기 |

- ZooKeeper 읽기는 기본적으로 클라이언트가 붙은 서버의 로컬 사본을 읽어 **최신이 아닐 수 있다**. 최신이 필요하면 `sync` 뒤에 읽는다(논문 2.2절 API·2.3절 보장, MIT 6.5840 L9 노트 "a ZK read may not see latest completed writes").
- etcd 읽기는 기본이 선형화이고, `--consistency=s`로 로컬 읽기를 고를 수 있다(11번 실험).

### 2. 락 레시피 — 줄 세우고 앞사람만 지켜본다

```text
 /locks/job/ 아래 (etcd라면 접두사, ZooKeeper라면 부모 znode)
   lock-0000000007   ← A (가장 작은 번호 = 소유자)
   lock-0000000008   ← B: 7번만 watch
   lock-0000000009   ← C: 8번만 watch
 A가 죽거나 해제 → 7번 삭제 → B만 깨어나 "내가 가장 작은가?" 다시 확인
```

- ZooKeeper 논문 2.4절 "Simple Locks without Herd Effect": `create(l + "/lock-", EPHEMERAL|SEQUENTIAL)` → 자식 목록에서 가장 작으면 소유 → 아니면 바로 앞 znode에만 `exists(p, true)`.
  - *herd effect(우르르 깨어남)*: 락 하나가 풀릴 때 기다리던 모두가 깨어나 경쟁하는 것. 앞사람만 지켜보면 한 명만 깨어난다.
- etcd 3.6.5 `client/v3/concurrency/mutex.go`도 같은 모양이다.
  - `tryAcquire`: lease를 붙여 `접두사/<leaseID>` 키를 만든다(키가 없을 때만 — txn).
  - `waitDeletes(접두사, 내 revision-1)`: 나보다 먼저 만든 키가 다 지워질 때까지 기다린다.
  - `IsOwner()`: `Compare(CreateRevision(myKey), "=", myRev)` — etcd 자신에게 쓰는 txn을 "아직 내가 소유자일 때만"으로 묶을 수 있다.

### 3. 락이 원리적으로 못 막는 것 — 멈췄다 깨어난 소유자

Kleppmann(2016)의 그림을 옮기면 이렇다.

```text
 클라이언트1  ─[락 획득, 토큰 33]─[████ GC 멈춤 ████]──────────── 쓰기(33) ──> 저장소: 거절 (이미 34를 봤다)
 락 서비스                      lease 만료 ↓
 클라이언트2                    ─[락 획득, 토큰 34]─ 쓰기(34) ──> 저장소: 반영, 최대 토큰 = 34
```

- 클라이언트1은 자기가 멈췄다는 것을 모른다. 쓰기 직전에 "아직 내 락인가"를 확인해도 **확인과 쓰기 사이에 또 멈출 수 있다.**
- 그래서 확인하는 쪽을 바꾼다. **받는 쪽(저장소)이** 토큰을 검사한다. 받는 쪽에서는 검사와 쓰기를 한 원자 연산으로 묶을 수 있다.
  - *fencing token*: 락을 잡을 때마다 커지는 번호. 쓰기에 실어 보내고, 저장소는 지금까지 본 가장 큰 번호보다 작은 쓰기를 거절한다.
- 조건 둘
  1. 토큰이 **단조 증가**해야 한다. Kleppmann은 ZooKeeper라면 zxid나 znode 버전을 쓸 수 있다고 적는다. etcd라면 락 키의 `create_revision`이다.
    - 단, 이 노트의 ZooKeeper 락 레시피는 획득마다 **새** znode를 만든다. znode 버전은 그 znode 데이터의 변경 횟수라 새 락 노드마다 0부터 다시 센다. 이 레시피에서는 락 znode의 생성 zxid(`czxid`)나 순번을 쓴다(ZooKeeper Programmer's Guide, Stat).
  2. 저장소가 **검사에 참여**해야 한다. 검사하지 않는 자원(외부 API·메일 발송)은 토큰으로 못 막는다.

참고: ZooKeeper 세션이 끝나면 ZooKeeper는 그 세션의 ephemeral 노드를 지우고, 그 세션의 이후 요청을 **거절**한다(6.5840 L9 노트). 즉 ZooKeeper 안의 데이터는 세션 종료로 펜싱된다. 하지만 ZooKeeper **밖**의 자원(DB·파일)에 대한 쓰기는 그렇지 않다. 그래서 토큰이 필요하다.

### 4. 실험: 멈춘 소유자의 늦은 쓰기 — 토큰 검사 없음 vs 있음

- 락: etcd lease(TTL 2초) + Mutex와 같은 규칙. 토큰 = 내 락 키의 `create_revision`.
- 멈춤: A가 3.5초 동안 keepalive를 보내지 않는다(GC 멈춤 흉내).
- 자원: etcd 키 `/w10/acct`로 흉내 냈다.
  - plain = 그냥 `put`.
  - fenced = txn `If(acct_token > 내 토큰) Then(거절) Else(acct 쓰기 + acct_token = 내 토큰)`. DB라면 `UPDATE ... WHERE last_token <= ?` 한 문장이 그 자리다.

(실험, etcd 3.6.5 3노드 공용 클러스터, Java 21 HttpClient → gRPC-gateway, 키 `/w10/`, 2026-10-01)

```text
== 모드: plain(토큰 검사 없음)
t=  142ms A 락 획득: 소유자=A, A 토큰=31
t=  151ms A가 GC로 멈춘다(3.5초, keepalive 없음)
t= 2672ms A의 lease 만료 → B 락 획득, B 토큰=32
t= 2684ms B 쓰기 'B-1' (토큰 검사 없음) → 반영
t= 3694ms A가 깨어남. 아직 자기가 락을 쥐었다고 믿는다
t= 3703ms A 쓰기 'A-stale' (토큰 검사 없음) → 반영
t= 3703ms 최종 acct = A-stale
== 모드: fenced(저장소가 토큰 검사)
t=  142ms A 락 획득: 소유자=A, A 토큰=41
t=  151ms A가 GC로 멈춘다(3.5초, keepalive 없음)
t= 2238ms A의 lease 만료 → B 락 획득, B 토큰=42
t= 2254ms B 쓰기 'B-1' 토큰=42 → 반영
t= 3664ms A가 깨어남. 아직 자기가 락을 쥐었다고 믿는다
t= 3673ms A 쓰기 'A-stale' 토큰=41 → 거절(저장소가 본 토큰 42 > 41)
t= 3680ms 최종 acct = B-1
```

- 관찰 1 — plain: 두 소유자의 쓰기가 다 들어갔고 **B의 쓰기가 조용히 사라졌다**(최종 `A-stale`). 예외도 로그도 없다.
- 관찰 2 — fenced: 같은 순서인데 A의 쓰기가 거절됐다(41 < 42). 최종 값은 B의 것이다.
- 관찰 3 — 토큰 값(31·32, 41·42)은 실행마다 다르다. 클러스터 전역 revision이라 다른 키 쓰기에도 커진다. **연속일 필요는 없고 커지기만 하면 된다.**
- 관찰 4 — 락 만료는 A의 마지막 갱신 약 2~2.5초 뒤였다. etcd 3.6.5 기본 설정의 lease 최소 TTL이 2초다(10번 실험: TTL 1 요청 → `granted with TTL(2s)`).

### 5. Redis 락과 Redlock — 무엇이 쟁점인가

Redis 단일 노드 락은 `SET key 고유값 NX PX ttl`로 잡고, "값이 내 것일 때만 지운다" Lua 스크립트로 푼다(redis.io Distributed Locks 문서).

(실험, Redis 7.4.9 단일 노드 `sn-dw-redis`, 키 `w10:lock`, TTL 1초, 2026-10-01 — 빈 줄은 nil 응답)

```text
A 획득: OK
B 획득 시도: 
B 획득 시도(만료 뒤): OK
A 해제 — 소유자 확인 Lua: 0 / 남은 값: B-uuid
A 해제 — 그냥 DEL: 1 / 남은 값: 
```

- 관찰: A가 멈춘 사이 TTL이 끝나 B가 잡았다. A가 그냥 `DEL`로 풀면 **B의 락을 지운다**(남은 값 없음). 소유자 확인 Lua는 0을 돌려주고 B의 락을 남겼다.
- 그래도 이 락은 고유값만 있고 **단조 증가 토큰이 없다.** 늦은 쓰기를 자원 쪽에서 막는 재료가 없다.

Redlock(여러 독립 Redis에 다수결로 잡기)을 두고 두 주장이 있다.

| | Kleppmann 2016 "How to do distributed locking" | antirez 2016 "Is Redlock safe?" |
|---|---|---|
| 토큰 | Redlock은 단조 증가 fencing token을 만들지 않는다 | 고유 랜덤 값으로 check-and-set을 하면 같은 목적을 이룬다. 토큰 순서가 작업 순서와 같다는 보장도 없다 |
| 시계 | 안전성이 시간 가정(키 만료 시간·네트워크 지연·프로세스 멈춤이 TTL보다 짧다)에 기댄다. 시계가 뛰면 깨진다 | 시계를 사람이 건드리지 않고 단조 시계를 쓰면 흐른 시간은 오차 범위 안에서 잴 수 있다. 단조 시계로 바꾸겠다 |
| 결론 | 정확성이 중요하면 합의 기반(ZooKeeper 등) + fencing | 획득 후 남은 시간을 다시 확인하면 실무에 충분하다 |

- 해석: 둘 다 "멈췄다 깨어난 소유자"는 락만으로 못 막는다는 데 동의한다. 갈리는 지점은 (1) 자원 쪽 검사를 무엇으로 하나(단조 토큰 vs 고유값 CAS) (2) 시간 가정을 안전성의 근거로 받아들이나다.
- redis.io의 Distributed Locks 문서 자체가 지금은 "You should implement fencing tokens"라고 적고, Redis의 TTL 만료가 단조 시계를 쓰지 않아 벽시계 이동으로 락이 둘에게 갈 수 있다고 적는다(2026-10-01 열람).

### 6. 효율용 락 vs 정확성용 락

Kleppmann(2016)의 구분이다.

```text
 효율용: 같은 일을 두 번 하면 비용만 든다(캐시 재계산, 중복 알림 한 번)
         → 단일 Redis 락으로 충분. 가끔 깨져도 된다
 정확성용: 두 번 하면 데이터가 틀어진다(잔액, 파일 덮어쓰기)
         → 합의 저장소 락 + fencing token + 자원 쪽 검사
```

## 쓰이는 자료구조·알고리즘

- **lease / 세션** — 기한이 있는 소유. 갱신이 끊기면 저장소가 지운다. 10번의 리스와 같다.
- **순번 대기열** — `SEQUENTIAL` znode 순번, etcd `create_revision`. 앞사람만 watch해 herd effect를 막는다.
- **watch(관찰자 패턴)** — 폴링 대신 변경 알림. ZooKeeper watch는 한 번 울리고 다시 걸어야 한다(논문 2.1절).
- **비교 후 교환(CAS)** — 저장소 쪽 토큰 검사는 CAS로 만든다. etcd txn의 `compare`, SQL 조건부 `UPDATE`는 토큰 비교를 조건에 바로 넣는다. ZooKeeper `setData(path, data, version)`는 버전 **일치**만 검사하므로, 저장된 토큰을 읽어 비교한 뒤 이 버전 CAS로 그 사이 경쟁을 막는다.
- **MVCC revision** — etcd는 모든 변경에 전역 revision을 붙인다. 이것이 토큰의 재료다. MVCC 일반은 [database/16-mvcc](../../database/16-mvcc/2-summary.md).
- **해시맵의 원자 갱신** — 원본 구현의 `compute`. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 먼저 묻는다: 이 락은 효율용인가 정확성용인가

- 효율용이면 단일 Redis `SET NX PX` + 소유자 확인 해제로 충분하다.
- 정확성용이면 아래 순서를 따른다.

### 2. 정확성용 락의 순서

1. 락 키 = 보호할 자원의 단위(계좌·테넌트·파일).
2. 합의 기반 저장소(etcd·ZooKeeper)에서 잡는다. 토큰 = 락 키의 create_revision(etcd) 또는 락 znode의 `czxid`(ZooKeeper — 획득마다 새 znode를 만드는 레시피라 znode 버전은 안 된다).
3. 토큰을 **모든 쓰기 경로에** 싣는다.
4. 자원이 토큰을 검사한다 — 검사·쓰기를 한 원자 연산으로.
5. 거절 횟수를 지표로 낸다. 0이 아니면 락을 잃은 옛 소유자가 아직 쓰려 했다는 뜻이다(락이 막아 주지 못한 틈이 실제로 생겼다).

### 3. 자원 쪽 검사 — DB 조건부 UPDATE (Java, JDBC)

```java
/** 토큰이 지금까지 본 것 이상일 때만 쓴다. 같은 토큰의 반복 쓰기는 통과(긴 작업의 여러 번 쓰기). */
boolean fencedWrite(Connection c, long accountId, long amount, long token) throws SQLException {
    String sql = """
        UPDATE account
           SET balance = ?, last_token = ?
         WHERE id = ? AND last_token <= ?
        """;
    try (PreparedStatement ps = c.prepareStatement(sql)) {
        ps.setLong(1, amount);
        ps.setLong(2, token);
        ps.setLong(3, accountId);
        ps.setLong(4, token);
        int n = ps.executeUpdate();          // 0이면 행이 없거나 더 큰 토큰이 이미 썼다 → (행이 있다면) 내 락은 끝났다
        if (n == 0) metrics.increment("fencing.rejected");
        return n == 1;
    }
}
```

- 한 문장이라 검사와 쓰기 사이에 틈이 없다. 행 락이 둘의 동시 실행을 직렬화한다.
- 거절되면 재시도하지 않는다. 락을 잃었다는 뜻이므로 작업을 멈춘다.

### 4. 토큰을 못 싣는 자원

- 외부 결제 API처럼 토큰 검사를 못 하게 하는 자원은 **멱등 키**(요청 ID)를 쓴다. 같은 키의 두 번째 요청을 상대가 무시하게 한다.
- 그것도 안 되면 "락을 잃으면 바로 멈춘다"(10번의 짧은 기한)로 겹침을 줄이는 것까지가 한계다.

### 5. 진단 명령

```bash
# 락 대기열: 접두사 아래 키와 create_revision (가장 작은 것이 소유자)
etcdctl get --prefix /locks/job/ -w json | jq '.kvs[] | {key: (.key|@base64d), create_revision, lease}'
# 그 키에 붙은 lease의 남은 시간
etcdctl lease timetolive <leaseID 16진>
# 명령 하나를 락 안에서 실행 — 명령에는 ETCD_LOCK_KEY, ETCD_LOCK_REV 환경 변수가 주어진다(etcdctl README)
etcdctl lock /locks/job ./run-batch.sh
# Redis 락의 남은 시간
redis-cli PTTL <락 키>
```

## 장애 시나리오와 대처

### 1. GC 멈춤 중 락 만료 → 두 소유자 동시 쓰기

- 현상: 정산 결과에 다른 서버가 쓴 값이 덮여 있다. 락 로그상으로는 두 서버 모두 정상 획득이다.
- 보이는 형태: 예외 없음. 한 서버의 GC 로그에 TTL보다 긴 멈춤이 같은 시각에 있다. 위 실험의 plain처럼 B의 쓰기가 조용히 사라진다.
- 원인: 락은 시간으로 끊기는데, 멈춘 프로세스는 시간이 흐른 것을 모른다. 확인과 쓰기 사이의 틈은 없앨 수 없다.
- 대처: fencing token을 쓰기에 싣고 자원이 검사한다(위 실험의 fenced). TTL을 작업 시간보다 넉넉히 잡고, 갱신은 별도 스레드가 하되 갱신 실패 시 작업을 중단한다.

### 2. Redlock·Redis 락의 시계 가정이 깨짐

- 현상: Redis 서버의 시각이 NTP 계단 조정이나 수동 변경으로 뛰자, 같은 락을 두 클라이언트가 잡았다.
- 보이는 형태: 같은 락 키에 대해 두 클라이언트의 `SET NX` 성공 로그. 서버 측 시각 변경 기록. 페일오버 직후에도 비슷하게 나온다(비동기 복제로 새 주 서버에 락 키가 없다).
- 원인: Redis 키 만료가 벽시계에 기댄다(redis.io 문서). Redlock 안전성은 "시계 속도 차이·지연·멈춤이 TTL보다 작다"는 가정 위에 있다(Kleppmann 2016).
- 대처: 정확성용이면 합의 저장소 + fencing으로 옮긴다. Redis를 계속 쓰면 NTP를 slew(서서히 조정)로 두고 수동 시각 변경을 막는다. 고유값 CAS(antirez의 제안)라도 자원 쪽 검사를 넣는다.

### 3. 옛 소유자의 해제가 새 소유자의 락을 지움

- 현상: 가끔 같은 배치가 세 번 돈다. 두 번째 소유자가 잡은 락이 엉뚱한 순간에 사라진다.
- 보이는 형태: 위 Redis 실험처럼, 만료 뒤 늦게 깨어난 A의 `DEL`이 B의 락을 지운다. C가 바로 잡는다.
- 원인: 해제가 소유자를 확인하지 않는다.
- 대처: "값이 내 고유값일 때만 DEL" Lua 스크립트로 푼다. etcd·ZooKeeper 레시피는 요청마다 고유한 키를 만들어 그 키만 지우므로 이 문제가 구조적으로 작다(etcd 3.6.5 `Mutex.Unlock`은 소유 비교 없이 내 키 `pfx+leaseID`를 `Delete`한다 — 서버 검사가 아니라 키 이름 덕이다).

### 4. 세션 만료로 소유권이 넘어갔는데 소유자는 계속 일한다

- 현상: 조정 서비스와의 연결이 잠깐 끊긴 뒤, 소유자가 작업을 이어 가는 동안 다른 서버도 같은 작업을 시작한다.
- 보이는 형태: ZooKeeper 클라이언트 로그에 세션 만료(`Expired`) 이벤트, 그 뒤에도 작업 로그가 이어진다. etcd라면 keepalive 실패 뒤 lease TTL -1.
- 원인: 세션·lease 종료는 서버가 정한다. 클라이언트는 다음 요청이나 이벤트에서 처음 안다.
- 대처: 세션 만료·연결 끊김(ZooKeeper `Disconnected`) 이벤트에서 작업을 멈추는 핸들러를 둔다. 끊김이 길어질 수 있으니 fencing을 함께 둔다.

### 5. 락 하나에 대기자가 수백이라 풀릴 때마다 조정 서비스가 출렁인다

- 현상: 락이 풀리는 순간 조정 서비스 요청이 치솟고 지연이 튄다.
- 보이는 형태: 모든 대기자가 같은 키(또는 부모 노드 전체)를 watch한다. 해제마다 watch 이벤트가 대기자 수만큼 나간다.
- 원인: herd effect.
- 대처: 바로 앞 순번만 watch한다(ZooKeeper 논문 레시피, etcd Mutex의 `waitDeletes`). 대기자가 많으면 락 단위를 쪼개거나 큐로 바꾼다.

## 핵심 문장

- 조정 서비스는 합의로 복제한 작은 저장소에 세션·lease, 순번, watch를 얹어 락·선출·설정의 재료를 준다.
- 락은 멈췄다 깨어난 소유자를 막지 못한다. 확인과 쓰기 사이의 틈은 없앨 수 없다.
- fencing token은 단조 증가 번호를 쓰기에 실어 **자원이** 검사하게 한다. etcd 실험에서 토큰 없이는 B의 쓰기가 조용히 사라졌고, 토큰 검사로는 A의 늦은 쓰기가 거절됐다.
- etcd라면 락 키의 create_revision, ZooKeeper 락 레시피라면 락 znode의 czxid가 토큰이 된다. 연속일 필요는 없고 커지기만 하면 된다.
- Redlock 논쟁의 쟁점은 시간 가정을 안전성 근거로 받아들이느냐와 자원 쪽 검사를 무엇으로 하느냐다. 정확성용 락이면 합의 저장소 + fencing이 안전한 쪽이다.

## 관련 주제·근거

- 선행
  - [11-consensus-raft](../11-consensus-raft/2-summary.md) — etcd가 기대는 합의
  - [10-leader-election](../10-leader-election/2-summary.md) — lease·임기, 리더 둘
  - 원본 [ops-patterns/11-distributed-lock](../../ops-patterns/11-distributed-lock/2-summary.md) — 만료·소유자·토큰, FencedStore. 참고: 원본은 etcd 펜싱 토큰을 "락 키의 `create_revision`(획득마다 커진다)"로 적는다. 새 락 키가 생길 때마다 커진다는 뜻으로 맞다(etcd 3.6.5 `Mutex.tryAcquire`는 같은 세션이 이미 키를 가졌으면 그 키를 재사용해 값이 그대로다). 다만 이 값은 클러스터 전역 revision이라 락과 무관한 쓰기로도 커진다 — 연속 번호가 아니다(위 실험: 31→32, 41→42는 그 사이 다른 쓰기가 없었을 뿐).
- 후속·연결
  - 13 [distributed-id-generation](../13-distributed-id-generation/2-summary.md) — 겹치지 않는 번호를 조율 없이 만들기
  - [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md)(벽시계 계단 조정)
  - [database/16-mvcc](../../database/16-mvcc/2-summary.md) — revision과 버전
  - [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) — 한 기계 안의 락과 비교
- 논문·글
  - Hunt, Konar, Junqueira, Reed, "ZooKeeper: Wait-free coordination for Internet-scale systems", USENIX ATC 2010 — 2.1 znode·ephemeral·sequential·watch(one-time trigger), 2.2 API(sync·version 인자), 2.3 linearizable writes·FIFO client order, 2.4 Simple Locks without Herd Effect <https://www.usenix.org/legacy/event/atc10/tech/full_papers/Hunt.pdf>
  - Kleppmann, "How to do distributed locking", 2016-02-08 — 효율 vs 정확성, GC 멈춤(HBase), fencing token 33/34, ZooKeeper zxid·znode 버전, Redlock 시간 가정 <https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html>
  - antirez, "Is Redlock safe?", 2016 <http://antirez.com/news/101>
  - Kleppmann 『DDIA』 1판 8장 "The leader and the lock"·"Fencing tokens", 9장 "Membership and Coordination Services"
  - MIT 6.5840 Spring 2026 L9 ZooKeeper 노트(세션 종료 = ZooKeeper 안의 fencing, 읽기가 최신이 아닐 수 있음) <https://pdos.csail.mit.edu/6.824/notes/l-zookeeper.txt>
- 문서·소스
  - etcd v3.6.5 `client/v3/concurrency/mutex.go`(tryAcquire·waitDeletes·IsOwner), `session.go`(기본 TTL 60초), `etcdctl/README.md`(LOCK — ETCD_LOCK_KEY·ETCD_LOCK_REV)
  - redis.io "Distributed Locks with Redis"(SET NX PX, 해제 스크립트, Redlock, fencing 권고, TTL 만료와 벽시계) <https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/>
- 실험 목록
  - C etcd lease 락 + 3.5초 멈춤 → plain(B 쓰기 유실) vs fenced(A 쓰기 거절) — Java 21, 공용 etcd 3.6.5 3노드, 키 `/w10/`
  - C2 Redis 7.4.9 `SET NX PX` 만료 뒤 옛 소유자의 `DEL` vs 소유자 확인 Lua — 공용 Redis, 키 `w10:lock`
