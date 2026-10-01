# distributed/08-cap-and-pacelc — CAP과 PACELC: 분할 시 C vs A, 평시 L vs C — 정리 (힌트)

## 해결하는 문제

복제된 데이터는 노드 사이 네트워크로 맞춘다(06번).\
그 네트워크가 끊기면, 요청을 받은 노드는 둘 중 하나를 해야 한다.
- 다른 쪽과 확인할 수 없으니 **거절하거나 기다린다** → 일관성은 지키고 응답은 못 한다.
- 자기가 가진 값으로 **답한다** → 응답은 하지만 옛 값이거나 다른 쪽과 갈라진다.

이 선택을 미리 정하지 않으면, 분할이 난 순간 시스템이 무엇을 할지 아무도 모른다.\
또 끊기지 않은 평소에도 비슷한 선택이 있다. 다른 복제본과 확인하고 답하면 느리고, 확인 없이 답하면 빠르지만 옛 값일 수 있다.

쉬운 예: 지점 두 곳인 은행, 지점 사이 전화가 끊겼다.
- 잔액을 본점과 맞출 수 없으니 출금을 막는다(일관성).
- 각 지점이 자기 장부로 출금해 준다(가용성). 나중에 맞춰 보면 잔액이 음수일 수 있다.
- 전화가 멀쩡해도, 출금마다 본점에 전화하면 손님이 기다린다(지연).

똑같은 구조다. 첫 둘이 CAP, 셋째까지가 PACELC다.

실무 예
- "우리 DB는 CA 시스템이라 분할 걱정이 없다"는 설계 문서.
- etcd·ZooKeeper 클러스터의 소수 쪽 노드가 쓰기를 거절한다.
- 다른 리전으로 페일오버했더니 DB 호출 대부분이 대륙 횡단 왕복을 하게 됐다(GitHub 2018).

## 동작·원리

### 1. CAP 정리 — 정확한 문장

```text
  분할: G1 | G2 사이 메시지가 모두 사라진다
  G1: [n1]  ──✘──  [n2] :G2
       ▲ write(x=1) OK          ▲ read(x) → ?
  A를 지키려면 n2는 답해야 한다 → n1의 쓰기를 모르므로 x=0(옛 값) → C 위반
  C를 지키려면 n2는 x=1을 알아야 한다 → 메시지가 안 오니 답할 수 없다 → A 위반
```

- Gilbert–Lynch 2002의 정의
  - *C(일관성)*: 원자적(atomic) 읽기/쓰기 객체. 원자적 = **선형화**다(07번).
  - *A(가용성)*: 고장 나지 않은 노드가 받은 **모든 요청**이 결국 응답을 받는다. 얼마나 걸려도 되지만 언젠가 답해야 한다.
  - *P(분할 허용)*: 네트워크가 한 노드에서 다른 노드로 가는 메시지를 임의로 많이 잃을 수 있다.
- 정리 1: 비동기 네트워크 모델에서, 메시지 유실이 있는 실행을 포함한 모든 공정 실행에서 가용성과 원자적 일관성을 함께 보장하는 읽기/쓰기 객체는 만들 수 없다(Gilbert–Lynch 2002 §3.1).
  - *비동기 네트워크 모델*: 시계가 없고, 메시지 지연에 상한이 없다. 노드는 받은 메시지와 자기 계산만으로 결정한다(02번).
- 부분 동기 모델(시계가 있고 지연 상한이 알려진 모델)에서도 메시지가 유실될 수 있으면 같은 불가능성이 성립한다(같은 논문 §4.2 정리 2).

### 2. "셋 중 둘"이 오해인 이유

- P는 고르는 것이 아니다. 인터넷과 데이터센터 네트워크는 메시지를 늦추고 잃는다. 분할은 **일어나는 사건**이다(Kleppmann 2015).
- 그래서 실제 질문은 "분할이 **나면** C와 A 중 무엇을 포기하나"다.
- "CA 시스템"은 "분할이 안 난다고 가정한 시스템"이라는 뜻밖에 안 된다. 분할이 나면 무슨 일이 생길지 정의되지 않았다.
- CAP의 범위는 좁다(Kleppmann 2015).
  - 대상은 **레지스터 하나**(키 하나의 읽기·쓰기)다. 여러 객체 트랜잭션은 범위 밖이다.
  - 다루는 장애는 네트워크 분할뿐이다. 노드 다운·디스크 가득 참은 다루지 않는다.
  - 지연을 다루지 않는다. CAP의 A는 "언젠가 답하면" 만족한다.
- 많은 시스템은 CP도 AP도 아니다. 예: 비동기 복제 단일 리더에서 팔로워 읽기를 허용하면, 분할 시 리더와 끊긴 쪽은 쓸 수 없고(A 아님) 팔로워 읽기는 옛 값일 수 있다(C 아님)(Kleppmann 2015).

### 3. 분할 중 두 가지 반응

```text
  과반 정족수 시스템 (etcd·ZooKeeper)          비동기 복제 + 복제본 읽기 (Redis 기본)
  [n1 n2] | [n3]                              [리더] | [복제본]
   다수 쪽: 읽기·쓰기 계속                       리더: 쓰기 계속 받음
   소수 쪽: 선형화 읽기·쓰기 거절(타임아웃)        복제본: 옛 값으로 계속 답함
   → 소수 쪽에서 C를 위해 A 포기                  → 응답은 하지만 C 아님
```

#### 실험: etcd 3.6.5 — 소수 쪽 노드는 답하지 않는다

- 환경: 일회용 etcd 3.6.5 3노드. 팔로워 etcd3을 Docker 네트워크에서 떼어 냈다(07번과 같은 실행).

(실험, etcd 3.6.5 3노드, 2026-10-01)

```text
--- etcd3 분리 ---
다수 쪽(etcd1) put v2 → 성공
다수 쪽(etcd1) 선형화 읽기: v2
소수 쪽(etcd3) 직렬화 읽기(--consistency=s): v1  [89ms]
소수 쪽(etcd3) 선형화 읽기(기본): Error: context deadline exceeded  [3097ms]
소수 쪽(etcd3) put v3: Error: context deadline exceeded  [3086ms]
--- 재연결 ---
재연결 5초 뒤 etcd3 선형화 읽기: v2
```

- 기본 읽기·쓰기에서 etcd3은 살아 있는데 답하지 않는다. CAP의 A가 요구하는 "살아 있는 노드는 답한다"를 포기했다.
- 같은 노드가 `--consistency=s` 읽기에는 바로 답했다. 대신 옛 값 v1이다. **같은 제품 안에서도 연산 옵션마다 선택이 다르다.**

#### 실험: Redis 7.4.9 — 설정 하나로 쓰기의 선택이 바뀐다

- 환경: 일회용 Redis 7.4.9 리더 1 + 복제본 1. 복제본을 리더와의 네트워크에서 떼고 3초마다 리더에 쓰고 복제본에서 읽었다. `min-replicas-to-write`만 0(기본)과 1로 바꿨다(`min-replicas-max-lag 10`).
  - *min-replicas-to-write N / min-replicas-max-lag M*: 지연이 M초 이하인 복제본이 N개 미만이면 리더가 쓰기를 거절한다(Redis replication 문서).

(실험, Redis 7.4.9, 2026-10-01)

```text
min-replicas-to-write=0, min-replicas-max-lag=10
t=+0s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+3s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+6s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+9s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+12s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+15s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
복구 4초 뒤 복제본 GET → before
min-replicas-to-write=1, min-replicas-max-lag=10
t=+0s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+3s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+6s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+9s 리더 SET → OK | 복제본 GET → before | 복제본 master_link_status:up
t=+12s 리더 SET → NOREPLICAS Not enough good replicas to write. | 복제본 GET → before | 복제본 master_link_status:up
t=+15s 리더 SET → NOREPLICAS Not enough good replicas to write. | 복제본 GET → before | 복제본 master_link_status:up
복구 4초 뒤 복제본 GET → after-9
```

- 기본(0)에서는 분할 내내 리더가 쓰기를 받았다. 복제본은 내내 `before`를 답했다. 둘 다 응답했지만 서로 다른 값이다.
- 1로 바꾸자 끊긴 지 약 10초 뒤부터 리더가 `NOREPLICAS`로 거절했다. 끊긴 직후 약 10초 동안 받은 쓰기(`after-0`·`after-3`·`after-6`·`after-9` 네 건)는 복제본에 없는 채로 OK였다. 문서 표현대로 "유실 창을 몇 초로 묶는" 최선 노력이지 일관성 보장이 아니다.
- 복제본은 15초 동안 `master_link_status:up`이라고 답했다. 이 컨테이너의 `repl-timeout`은 60(초)이었다. **끊긴 것을 아는 데도 시간이 걸린다.** 그동안 옛 값을 경고 없이 준다.
- 복구 4초 뒤 결과가 두 실행에서 달랐다(첫 실행은 아직 `before`, 둘째는 `after-9`). 첫 실행의 복제본도 나중에 오프셋이 리더와 같아진 것은 확인했다. 따라잡는 시간은 실행마다 다르다.

### 4. PACELC — 분할이 없어도 고른다

```text
  if  Partition:   A  vs  C          (CAP의 질문)
  else (평시):     L  vs  C          (지연 vs 일관성)
```

- Abadi 2012: 분할(P)이면 가용성(A)과 일관성(C)을, 그렇지 않으면(E) 지연(L)과 일관성(C)을 맞바꾼다.
- 평시 선택은 **데이터를 복제하는 시스템**에만 해당한다(Abadi 2012). 복제본과 맞추고 답하면 느리고, 하나만 보고 답하면 옛 값일 수 있다.
- 논문의 분류(2012년 당시 기본 설정 기준)
  - PA/EL: Dynamo, Cassandra, Riak 기본값. 분할 시 가용성, 평시 지연을 택한다. R+W를 키워 평시 일관성을 늘릴 수 있지만, R+W>N이어도 Gilbert–Lynch 의미의 완전한 일관성은 아니다.
  - PC/EC: VoltDB/H-Store, Megastore, BigTable/HBase.
  - PA/EC: MongoDB(당시 구조).
  - PC/EL: PNUTS. 평시엔 지연을 위해 일관성을 낮추고, 분할 시엔 소수 쪽 갱신을 막는다. "분할 때 더 일관해진다"는 뜻이 아니라 기본 수준 아래로 더 낮추지 않는다는 뜻이다.
- 지연의 하한: 서쪽에서 끝난 쓰기를 동쪽 읽기가 봐야 하면 둘 사이 통신이 필요하다. 읽는 쪽이든 쓰는 쪽이든 그 왕복을 기다린다. 대륙 횡단이면 수십 ms다(6.5840 L8).

#### 실험: etcd 3.6.5 평시 — 선형화 읽기 vs 직렬화 읽기 지연

- 환경: 일회용 etcd 3.6.5 3노드(리더 etcd2, term 2). 같은 Docker 네트워크의 Java 21 클라이언트가 v3 JSON 게이트웨이(`/v3/kv/range`)로 노드마다 1000번씩 번갈아 호출했다. 한 호스트 안이라 네트워크 왕복이 매우 짧다.

```java
// EtcdLat.java 핵심: 같은 키를 선형화·직렬화로 번갈아 읽고, put도 잰다
lin[i] = call(host, "/v3/kv/range", "{\"key\":\"" + key + "\"}");
ser[i] = call(host, "/v3/kv/range", "{\"key\":\"" + key + "\",\"serializable\":true}");
put[i] = call(host, "/v3/kv/put",   "{\"key\":\"" + key + "\",\"value\":\"" + b64("v" + i) + "\"}");
```

(실험, etcd 3.6.5 3노드, 한 호스트, 2026-10-01)

```text
sn-dw-w06-etcd1  선형화 읽기 p50 1.93ms  p99 9.53ms | 직렬화 읽기 p50 1.17ms  p99 7.22ms | put p50 7.07ms  p99 21.62ms
sn-dw-w06-etcd2  선형화 읽기 p50 1.49ms  p99 7.10ms | 직렬화 읽기 p50 1.00ms  p99 6.22ms | put p50 6.09ms  p99 19.37ms
sn-dw-w06-etcd3  선형화 읽기 p50 1.65ms  p99 9.68ms | 직렬화 읽기 p50 0.92ms  p99 6.18ms | put p50 6.67ms  p99 20.99ms
```

- p50 기준 직렬화 읽기가 선형화 읽기보다 0.5~0.8ms 빨랐다(사실 점검 재실행에서는 0.7~1.4ms, 재구성한 클라이언트라 절댓값은 더 컸다). 리더인 etcd2에서도 차이가 있었다. 선형화 읽기는 리더도 자기가 아직 리더인지 확인하는 단계를 거친다(ReadIndex, 11번).
- put은 과반의 디스크 기록(fsync)까지 기다려 p50 6~7ms였다(재실행 5~8ms).
- 해석: 한 호스트 안이라 차이가 1ms 안팎이다. 노드가 리전에 흩어지면 확인 왕복이 수십 ms가 되어 차이가 그만큼 커진다(위 6.5840 L8의 지연 하한). 수치는 실행마다 다르다.

### 5. 실사례 — GitHub 2018-10-21

- 2018-10-21 22:52 UTC, 미국 동부 허브와 동부 데이터센터 사이 연결이 43초 끊겼다.
- Raft 기반 Orchestrator의 서부·클라우드 노드가 정족수를 이뤄 MySQL 리더를 서부로 옮겼다. 연결이 돌아오자 앱이 서부 리더에 쓰기 시작했다.
- GitHub은 동부로 바로 되돌리지 않았다. 서부에 30분 넘게 쓰인 데이터 때문에 "사용자 데이터를 지키려면 forward로 갈 수밖에 없다"고 판단했다. 동부의 앱은 DB 호출 대부분이 대륙 횡단 왕복이 되는 것을 감당하지 못했다. 원문은 이 결정이 많은 사용자에게 서비스를 쓸 수 없게 만들 것이라고 적었다("unusable for many users"). 원문: "the extended degradation of service was worth ensuring the consistency of our users' data".
- 해석: 43초 분할 때 정족수를 이룬 것은 Orchestrator의 **리더 선출(제어)** 이다. MySQL 데이터가 C였던 것은 아니다. 동부에서 받았지만 서부로 복제되지 못한 쓰기가 남아 수동 조정이 필요했다(06번).
- 해석: 그 뒤 forward로 가서 서부 리더를 쓴 기간은 지연을 감수하고 데이터 정합을 택한 선택이었다. 이 원거리 지연은 10-22 11:12 UTC에 모든 리더가 동부로 돌아오며 끝났다. 그 뒤의 저하는 몇 시간 뒤처진 읽기 복제본이 옛 데이터를 보여 준 것이다. 24시간 11분은 이 둘을 합친 전체 저하 기간이다.
- 재발 방지책 하나가 "리전 경계를 넘는 리더 승격 금지"였다.

## 쓰이는 자료구조·알고리즘

- **과반 정족수의 교집합** — 노드 2f+1개에서 f+1개짜리 집합 둘을 고르면 합이 2f+2 > 2f+1이라 적어도 한 노드가 겹친다. 그래서 과반 쪽만 진행하면 분할 양쪽이 서로 다른 결정을 내릴 수 없다. 소수 쪽이 거절하는 이유다. [09-quorums](../09-quorums/2-summary.md)
- **장애 탐지기(타임아웃·하트비트)** — "분할인가 느린가"를 판단한다. 실험의 Redis 복제본은 `repl-timeout` 60초 동안 링크가 살아 있다고 봤다. [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md)(φ accrual)
- **버전 벡터·병합 규칙** — 가용성을 택해 갈라진 쪽들을 분할 뒤에 합친다. [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md)
- **리스(lease)** — 리더가 일정 시간 동안 자기만 리더임을 믿고 로컬 읽기로 답한다. 평시 지연(L)을 줄이되 시계 가정을 더한다(10·12번).

## 적용 — 풀어나가는 법

### 1. "CP냐 AP냐" 대신 연산마다 적는다

| 연산 | 분할 중(P) | 평시(E) | 설정 예 |
|---|---|---|---|
| 결제·재고 차감 | 거절(C) | 확인 후 답(C) | etcd 기본 읽기·쓰기 + `Txn` 조건부 갱신(07번). 결제 이벤트를 Kafka에 남긴다면 `acks=all` + `min.insync.replicas=2`는 그 기록의 복제 내구성 조건이지 차감 연산의 선형화·원자성은 아니다 |
| 상품 상세 조회 | 옛 값이라도 답(A) | 가까운 복제본(L) | 캐시·복제본 읽기, etcd `--consistency=s` |
| 장바구니 추가 | 받고 나중에 합침(A) | 로컬 확인(L) | 리더리스 + 병합(24번) |

- 표의 칸을 채우지 못하면 그 연산의 분할 시 동작이 정의되지 않은 것이다.

### 2. 설정으로 선택을 드러낸다

```bash
# Redis 7.4: 복제본이 끊기면 쓰기를 거절 (유실 창을 10초로 묶음)
redis-cli CONFIG SET min-replicas-to-write 1
redis-cli CONFIG SET min-replicas-max-lag 10
# Kafka 4.1: ISR 밖 복제본의 리더 승격 금지(기본 false) + 쓰기 최소 ISR
kafka-configs.sh --bootstrap-server localhost:9092 --alter --entity-type topics \
  --entity-name orders --add-config min.insync.replicas=2,unclean.leader.election.enable=false
# etcd 3.6: 클러스터 상태(리더·term)
etcdctl endpoint status -w table
```

- Kafka 4.1 문서: `unclean.leader.election.enable` 기본 false, `min.insync.replicas` 기본 1. `acks=all`이고 ISR이 `min.insync.replicas`보다 적으면 프로듀서는 `NotEnoughReplicas`(또는 `NotEnoughReplicasAfterAppend`) 예외를 받는다. ISR 밖 복제본을 리더로 뽑지 않는 것은 가용성보다 일관성을 고르는 것이고, 켜면 그 반대다(Kafka 설계 문서 "Unclean leader election"). 단 4.1 새 클러스터는 ELR이 켜져 있어, ISR에서 빠졌어도 데이터 손실 없이 리더가 될 수 있다고 기록된 복제본(ELR)은 unclean 선출 없이 리더가 될 수 있다([21번](../21-kafka-internals/2-summary.md)).

### 3. 코드에서 두 길을 나눈다

```java
// 강한 연산: 실패를 그대로 올린다(재시도·사용자 안내)
public void withdraw(String acct, long amount) {
    try {
        strongStore.txn(acct, amount, Duration.ofSeconds(3));   // 선형화 경로, 타임아웃 명시
    } catch (TimeoutException e) {
        throw new ServiceUnavailable("잠시 후 다시 시도", e);    // 옛 값으로 진행하지 않는다
    }
}
// 약한 연산: 옛 값이라도 답하되, 옛 값임을 표시한다
public ProductView product(String id) {
    try {
        return strongStore.get(id, Duration.ofMillis(200));
    } catch (TimeoutException e) {
        return cache.get(id).markStale();                        // 화면에 "갱신 지연" 표시 등
    }
}
```

## 장애 시나리오와 대처

### 1. "CA 시스템" 주장 → 분할 시 동작 미정의

- **현상**: 노드 두 대짜리 "고가용성" 구성에서 둘 사이 링크가 끊기자 양쪽이 각자 리더가 됐다. 링크가 돌아오니 데이터가 갈라져 있다.
- **보이는 형태**: 두 노드 모두 쓰기를 받은 기록, 복구 후 복제 충돌·키 중복 에러. 또는 반대로 둘 다 상대를 기다리며 멈춤.
- **원인**: 설계가 분할을 "안 일어나는 일"로 두었다. 분할 때 누가 진행하고 누가 멈출지 규칙이 없다. 두 대의 과반은 2대라서, 둘 사이가 끊기면 어느 쪽도 과반을 만들 수 없다.
- **대처**: 분할 시 동작을 연산마다 명시한다. 진행 측을 정하는 정족수(홀수 노드·증인 노드)를 둔다. 옛 리더를 막는 펜싱을 둔다(12번).

### 2. 소수 쪽 노드가 살아 있는데 타임아웃

- **현상**: 특정 가용 영역의 앱만 etcd·ZooKeeper 호출이 몇 초씩 걸리다 실패한다. 그 영역의 etcd 노드 프로세스는 멀쩡하다.
- **보이는 형태**: `context deadline exceeded`(실험에서 3초 타임아웃에 3097ms). `etcdctl endpoint status`에서 그 노드만 다른 노드와 연결이 안 되거나 상태 조회가 실패한다.
- **원인**: 그 노드가 소수 쪽에 갇혔다. 선형화 읽기·쓰기는 리더·과반 없이 답하지 않는다. 설계대로의 C 선택이다.
- **대처**: 클라이언트에 엔드포인트를 여러 개 주어 다수 쪽 노드로 옮기게 한다. 옛 값이 괜찮은 읽기만 직렬화 읽기로 바꾼다. 타임아웃을 연산마다 명시한다.

### 3. 가용성을 택한 쪽이 조용히 갈라진다

- **현상**: 분할 동안 리더가 받은 쓰기가 복제본에는 없다. 그 사이 복제본을 승격했다면 그 쓰기는 사라진다(06번 실험).
- **보이는 형태**: 분할 중 에러가 없다. 복제본은 `master_link_status:up`을 보고했다(실험에서 15초 동안).
- **원인**: 기본 설정(`min-replicas-to-write 0`)은 분할 중에도 쓰기를 받는다. 끊김 감지는 `repl-timeout`(60초)만큼 늦을 수 있다.
- **대처**: 쓰기 확인 조건(`min-replicas-to-write`, Kafka `min.insync.replicas`)으로 유실 창을 묶는다. 분할 중 승격은 정족수 기반 관리자(Sentinel·Raft)에 맡기고 펜싱한다.

### 4. 페일오버 뒤 지연 폭증 (평시 L vs C)

- **현상**: 리전 장애로 다른 리전에 리더를 옮긴 뒤, 장애가 끝났는데도 서비스가 느리다.
- **보이는 형태**: DB 호출 지연이 리전 간 왕복만큼 늘어 타임아웃·느린 페이지가 생긴다(해석). GitHub 2018에서는 모든 리더가 동부로 돌아온 10-22 11:12 UTC까지 원거리 왕복이 이어졌다(전체 저하는 지연된 읽기 복제본까지 합쳐 24시간 11분).
- **원인**: 데이터 정합(C)을 지키려고 리더를 새 리전에 둔 채 운영하면 다른 리전 앱의 DB 호출 대부분이 원거리 왕복이 된다.
- **대처**: 리전 경계를 넘는 자동 승격을 막고(GitHub의 조치), 리전 간 지연을 견딜 수 없는 경로를 미리 찾아 둔다. 복구 절차(되돌리기 vs forward)를 미리 정해 둔다.

## 핵심 문장

- CAP의 C는 선형화, A는 "살아 있는 노드는 모든 요청에 결국 답한다"다. 네트워크가 메시지를 잃을 수 있으면 둘을 함께 보장할 수 없다.
- P는 고르는 것이 아니라 일어나는 일이다. "CA 시스템"은 분할 때의 동작을 정의하지 않았다는 말이다.
- 같은 제품 안에서도 연산·옵션마다 선택이 다르다. etcd 기본 읽기는 거절하고, 직렬화 읽기는 옛 값으로 답한다.
- PACELC: 분할이 없어도 복제 시스템은 지연과 일관성을 맞바꾼다. 확인 왕복이 곧 일관성의 값이다.
- 끊긴 것을 아는 데도 시간이 걸린다. 그동안 가용성 쪽은 옛 값을 경고 없이 준다.

## 관련 주제·근거

- 선행
  - [07-consistency-models](../07-consistency-models/2-summary.md) — CAP의 C = 선형화
  - [06-replication-strategies](../06-replication-strategies/2-summary.md) — 분할이 복제에 주는 영향
- 후속·연결
  - [09-quorums](../09-quorums/2-summary.md) — 정족수 교집합, sloppy quorum
  - [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md) §6 — 분산 DB에서의 CAP·PACELC
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 비동기 페일오버 유실
  - [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md) · [10-leader-election](../10-leader-election/2-summary.md) · [11-consensus-raft](../11-consensus-raft/2-summary.md) · [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) · [25-impossibility-results](../25-impossibility-results/2-summary.md)
  - [36-distributed-incidents](../36-distributed-incidents/2-summary.md)
- 논문·글
  - Gilbert, Lynch, "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services", ACM SIGACT News 2002 — §2 정의, §3.1 정리 1(비동기), §3.2 둘씩 고르기, §4.2 정리 2(부분 동기) <https://www.comp.nus.edu.sg/~gilbert/pubs/BrewersConjecture-SigAct.pdf>
  - Abadi, "Consistency Tradeoffs in Modern Distributed Database System Design", IEEE Computer 2012 — PACELC, 시스템 분류 <https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf>
  - Kleppmann, "Please stop calling databases CP or AP"(2015) — C·A·P의 정확한 뜻, CAP의 범위, CP도 AP도 아닌 시스템, ZooKeeper 사례 <https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html>
  - MIT 6.5840 Spring 2026 L8 노트 — 선형화의 지연 하한(서·동 해안), 강한 일관성 vs 최대 가용성 <https://pdos.csail.mit.edu/6.824/notes/l-linearizability.txt>
  - DDIA 1판 9장 "The Cost of Linearizability" — CAP, 선형화와 네트워크 지연
- 제품 문서
  - etcd v3.6 API guarantees — 기본 선형화, serializable 읽기 <https://etcd.io/docs/v3.6/learning/api_guarantees/>
  - Redis replication — `min-replicas-to-write`·`min-replicas-max-lag`, 비동기라 유실 창이 남음 <https://redis.io/docs/latest/operate/oss_and_stack/management/replication/>
  - Apache Kafka 4.1 — Broker configs(`unclean.leader.election.enable` 기본 false, `min.insync.replicas` 기본 1), Design "Unclean leader election", "Availability and Durability Guarantees" <https://kafka.apache.org/41/configuration/broker-configs/>
- 사고 보고서
  - GitHub, "October 21 post-incident analysis"(2018-10-30) — 43초 연결 끊김, 24시간 11분 저하, 데이터 정합 우선 결정, 리전 간 승격 금지 <https://github.blog/news-insights/company-news/oct21-post-incident-analysis/>
- 실험 목록
  - etcd 3.6.5 일회용 3노드: 팔로워 하나를 네트워크에서 분리 → 소수 쪽 기본 읽기·쓰기 3초 타임아웃, 직렬화 읽기는 옛 값(07번과 같은 실행)
  - Redis 7.4.9 리더 1 + 복제본 1: 복제 링크 분리 중 `min-replicas-to-write` 0 vs 1에서 3초 간격 쓰기·읽기 15초
  - etcd 3.6.5 일회용 3노드 평시: Java 21로 노드마다 선형화 읽기·직렬화 읽기·put 각 1000회 p50·p99
