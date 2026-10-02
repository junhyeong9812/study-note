# distributed/09-quorums — 정족수: R+W>N, sloppy quorum, hinted handoff, anti-entropy — 정리 (힌트)

## 해결하는 문제

리더리스 복제(06번)에는 "최신 값은 여기 있다"고 알려 주는 리더가 없다.\
그래서 쓰기는 여러 복제본에 보내고, 읽기도 여러 복제본에서 받아 가장 새 버전을 고른다.\
문제는 **몇 개에 쓰고 몇 개에서 읽어야 방금 쓴 값을 놓치지 않나**다. 또 복제본 몇이 죽었을 때 계속 쓸 수 있나, 놓친 쓰기는 누가 메우나.

쉬운 예: 출석부가 세 권이다.
- 출석을 부를 때 아무 두 권에 체크한다.
- 확인할 때도 아무 두 권을 펼친다.
- 2 + 2 > 3이라 펼친 두 권 중 적어도 한 권에는 체크가 있다.
- 한 권씩만 쓰고 한 권씩만 보면, 체크 안 된 권을 펼칠 수 있다.

똑같은 구조다. 쓴 집합과 읽은 집합이 겹치게 만드는 것이 정족수다.

실무 예
- Cassandra의 일관성 수준 `QUORUM`·`ONE`·`LOCAL_QUORUM`.
- Dynamo 논문의 (N, R, W) = (3, 2, 2).
- 노드 하나가 죽어도 쓰기를 받으려고 다른 노드가 대신 받아 두는 hinted handoff.
- etcd·ZooKeeper가 과반이 없으면 쓰기를 거절하는 것도 같은 정족수 원리다.

## 동작·원리

### 1. R + W > N — 겹치면 본다

```text
  N=3 복제본 [A][B][C]
  쓰기 W=2:  A ✔  B ✔  C ·      (A·B에 v2)
  읽기 R=2:  A ·  B ✔  C ✔      (B·C에서 읽음 → B가 v2를 갖고 있다)
             └── 2 + 2 > 3 → 쓴 집합과 읽은 집합이 적어도 한 곳(B)에서 겹친다

  R=1, W=1:  A ✔ (v2)            C에서 읽으면 v1 → 놓친다 (1 + 1 ≤ 3)
```

- *N*: 키 하나의 복제본 수. *W*: 쓰기 성공으로 치기 위한 확인 수. *R*: 읽기에 필요한 응답 수.
- Dynamo 논문 §4.5: R + W > N이면 정족수와 비슷한 시스템이 된다. get·put의 지연은 R개(W개) 중 **가장 느린 것**이 정한다. 그래서 R·W를 보통 N보다 작게 둔다. 흔한 설정은 (3, 2, 2)다(§6).
- 겹침이 주는 것: 읽은 R개 중 적어도 하나는 마지막으로 성공한 쓰기를 갖고 있다. 그래서 버전이 가장 큰 값을 고르면 된다.
  - 버전 비교가 전제다. 버전 없이 "먼저 온 응답"을 쓰면 겹쳐도 소용없다.

#### 실험(시뮬레이션): R·W 조합별 오래된 읽기 비율

- 환경: Java 21 단일 프로세스 시뮬레이션. N=3, 메시지 지연 = 1ms + 지수분포(평균 5ms, 예시). 쓰기는 W번째 확인이 온 순간 OK, 읽기는 그 순간 시작해 먼저 응답한 R개 중 최대 버전을 고른다. 2만 회, 시드 고정이라 실행마다 같다.

```java
// Quorum.java 핵심
long okAt = sorted[W - 1];                               // W번째 ack 시각 = 쓰기 OK
for (int i = 0; i < N; i++) {
    long reqArrive = okAt + delay();                     // 읽기 요청이 복제본 i에 닿는 시각
    seen[i] = arrive[i] <= reqArrive ? t : reps[i].ver;  // 그때 새 쓰기가 도착해 있었나
    respAt[i] = reqArrive + delay();
}
// 먼저 응답한 R개 중 최대 버전 → 방금 쓴 버전 t보다 작으면 "옛 값"
```

(실험, Java 21 시뮬레이션, 2026-10-01)

```text
[A] 엄격한 정족수, 메시지 유실 없음, 시행 20000회
  N=3 R=1 W=1  R+W<=N  옛 값 읽기 17.93%
  N=3 R=1 W=2  R+W<=N  옛 값 읽기 6.30%
  N=3 R=2 W=1  R+W<=N  옛 값 읽기 1.94%
  N=3 R=1 W=3  R+W>N  옛 값 읽기 0.00%
  N=3 R=3 W=1  R+W>N  옛 값 읽기 0.00%
  N=3 R=2 W=2  R+W>N  옛 값 읽기 0.00%
```

- R+W>N인 세 조합은 0%였다. 이 모델(엄격한 정족수, 버전 비교, 동시 쓰기 없음)에서는 겹침 때문에 옛 값이 나올 수 없다. 현실에서 이 전제가 깨지는 경우가 §2다.
- R+W≤N이면 비율이 지연 분포에 달렸다. 이 분포에서 R=1·W=1은 18%였다. 수치는 가정한 지연 분포가 정한 것이라 실제 시스템의 값은 아니다.

### 2. R + W > N이어도 옛 값이 나오는 경우

- R+W>N과 버전 비교가 있어도 다음은 막지 못한다(DDIA 5장 "Limitations of Quorum Consistency"). 첫 항목(sloppy quorum)은 정족수를 엄격하게 세지 않는 경우이고, 나머지는 엄격한 정족수에서도 생긴다.
  - **sloppy quorum**: 쓴 W개가 원래 N개 밖의 노드일 수 있다(아래 §3).
  - **동시 쓰기**: 두 쓰기가 동시에 오면 어느 쪽이 이길지 정해야 한다. LWW면 하나가 조용히 사라진다(06·24번).
  - **읽기와 쓰기가 동시**: 쓰기가 일부 복제본에만 도착한 순간의 읽기는 옛 값일 수도, 새 값일 수도 있다.
  - **쓰기가 W 미만에서 실패**: 성공한 복제본의 값은 되돌려지지 않는다. 다음 읽기에 보일 수도 안 보일 수도 있다.
  - **새 값을 가진 노드의 데이터 손실**: 그 노드를 옛 값을 가진 복제본에서 복구하면 새 값을 가진 노드 수가 W보다 줄어든다.
- 그래서 R+W>N은 "대개 최신 값을 읽는다"이지 선형화가 아니다. Abadi 2012도 R+W>N이어도 Gilbert–Lynch 의미의 일관성은 아니라고 적는다. Kleppmann 2015는 sloppy quorum과 읽기 복구가 섞이면 지운 데이터가 되살아나는 등의 경우를 든다.
- Cassandra 5.0은 이 가운데 하나를 막는 장치로 **blocking 읽기 복구**를 쓴다. 정족수 읽기에서 복제본이 다르면 응답 전에 고쳐 쓴다. 그래서 정족수 읽기 두 번이 연속이면 두 번째가 첫 번째보다 옛 값을 주지 않는다("monotonic quorum reads"). 테이블 옵션 `read_repair`를 `NONE`으로 바꾸면 이 보장이 없어진다(Cassandra 5.0 "Read repair").

### 3. sloppy quorum과 hinted handoff

```text
  키 K의 홈 복제본(preference list 앞 3개): A B C        대체 후보: D
  분할: 클라이언트 쪽 [A, D]  |  [B, C] 반대편

  쓰기 v2 (W=2):  A ✔  D ✔(힌트: "원래 B 몫")   → W=2 충족, OK
  반대편 읽기 R=2: B(v1) C(v1)  → v1           ← R+W=4 > N=3인데 옛 값!

  분할 해소 →  D가 B에 v2 전달(hinted handoff) → D는 사본 삭제
  B=v2, C=v1  → C는 읽기 복구·anti-entropy가 맞춘다
```

- Dynamo 논문 §4.6: 엄격한 정족수는 서버 장애·분할 때 쓰기를 못 받는다. 그래서 Dynamo는 "선호 목록(preference list)의 **처음 N개 건강한 노드**"에 읽고 쓴다. 이것이 *sloppy quorum*이다.
  - *preference list*: 일관 해싱 링에서 키를 담당하는 노드 목록. 장애에 대비해 N개보다 많이 둔다(§4.3).
- 원래 노드 대신 받은 노드는 메타데이터에 "원래 주인"을 *힌트*로 적어 따로 보관한다. 주인이 돌아오면 넘겨주고 지운다(*hinted handoff*).
- 대가: 쓴 W개와 읽는 R개가 **다른 노드 집합**에서 고를 수 있다. 겹침 보장이 사라진다.

#### 실험(시뮬레이션): sloppy quorum에서의 옛 값

(실험, Java 21 시뮬레이션, 2026-10-01)

```text
[C] sloppy quorum: 분할 중 쓰기 v2 → ack 2개(W=2 충족, D는 B 몫 힌트 보관)
  반대편 클라이언트 R=2 읽기(B,C) → v1   (R+W=4>N=3인데 옛 값)
  분할 해소 후 hinted handoff(D→B) → 상태 {A=2, B=2, C=1, D=0}, R=2(B,C) 읽기 → v2
  C는 아직 v1 — 읽기 복구나 anti-entropy가 맞춰야 한다
```

- 이 [C]는 위 그림의 경우를 정해 놓고 따라간 것이다(확률 실험이 아님). 핵심은 숫자 조건(R+W>N)이 맞아도 **노드 집합**이 안 겹치면 소용없다는 점이다.

#### 제품은 다르다 — Cassandra 5.0

- Cassandra 5.0도 hinted handoff를 쓴다. 복제본이 응답하지 않으면 코디네이터가 힌트를 로컬 디스크에 저장했다가 그 노드가 돌아오면 다시 보낸다. 힌트는 `max_hint_window`(기본 3시간) 동안의 다운타임까지만 쌓는다(Cassandra 5.0 "Hints").
- 그러나 일관성 수준을 세는 것은 진짜 복제본의 응답이다. 힌트만으로 쓰기를 성공시키는 수준은 `ANY`뿐이다. `ANY`는 쓰기에만 쓸 수 있다(Cassandra 5.0 "Dynamo" 절 Tunable Consistency).
- 즉 Dynamo 논문의 sloppy quorum(대체 노드가 W에 포함)과 Cassandra의 기본 동작(대체 노드는 힌트 보관만)은 다르다. "Dynamo 계열"이라도 제품마다 확인해야 한다.

### 4. 놓친 쓰기 메우기 — 읽기 복구와 anti-entropy

```text
  읽기 복구                               anti-entropy (Merkle 트리)
  R=2로 A(v2), C(v1)를 읽음                 A와 C가 루트 해시를 교환 → 다르면 자식 비교 → … → 다른 잎(키)만 전송
  → v2를 돌려주고 C에 v2를 써 준다             root
  읽힌 키, 읽힌 복제본만 고쳐진다              ├─ h(0..511)  같음 → 건너뜀
                                           └─ h(512..1023) 다름 → 내려감
```

- *읽기 복구*: 읽다가 옛 버전을 준 복제본에 최신 버전을 써 준다. 기회가 왔을 때 고치므로 anti-entropy의 일을 덜어 준다(Dynamo §5).
- *anti-entropy*: 복제본끼리 데이터를 비교해 다른 부분을 맞춘다. 키 범위마다 Merkle 트리를 두고 루트부터 내려가며 다른 가지만 따라간다. 전체를 보내지 않고 다른 키만 찾는다(Dynamo §4.7).
  - *Merkle 트리*: 잎은 키(값)의 해시, 부모는 자식 해시들의 해시. 루트가 같으면 아래가 다 같다고 본다. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
- Cassandra 5.0에서 hinted handoff·읽기 복구는 최선 노력이고, 최종 일관성을 **보장**하는 것은 Merkle 트리를 비교하는 repair(`nodetool repair`)다. repair는 기본적으로 자동으로 돌지 않는다. 운영자가 돌리거나 스케줄을 건다(Cassandra 5.0 "Repair"). 5.0.8부터는 Auto Repair 스케줄러가 백포트됐지만, JVM 속성 `-Dcassandra.autorepair.enable=true`와 스케줄 설정을 켜야 동작한다(Cassandra "Auto Repair" 문서).

#### 실험(시뮬레이션): 복구 장치별 남는 옛 값, Merkle 비교량

- [B] 키 3000개를 W=1로 한 번씩 쓰고, 쓰기 메시지가 복제본마다 10% 확률로 유실되게 했다(힌트 없음). 그 뒤 R=1 읽기를 두 바퀴 돈다. 시드 고정.
- [D] 키 1024개 중 3개만 다른 두 복제본을 Merkle 트리(이진, 높이 10)로 비교했다.

(실험, Java 21 시뮬레이션, 2026-10-01)

```text
[B] 복구 없음          1바퀴 옛 값  274/3000  2바퀴(R=1) 옛 값  283/3000
[B] 읽기 복구(R=2)     1바퀴 옛 값   34/3000  2바퀴(R=1) 옛 값  108/3000
[B] anti-entropy   1바퀴 옛 값  274/3000  2바퀴(R=1) 옛 값    0/3000
[D] Merkle anti-entropy: 키 1024개 중 다른 키 [17, 500, 1000], 비교한 해시 55개 (전수 비교면 1024개)
```

- 복구가 없으면 옛 값이 그대로 남는다(274 → 283, 차이는 무작위 복제본 선택 때문).
- 읽기 복구(첫 바퀴를 R=2로 읽으며 고침)는 첫 바퀴의 옛 값을 34로 줄였다. 하지만 읽은 두 복제본만 고쳐서 세 번째 복제본이 남는다. 둘째 바퀴 R=1에서 108.
- anti-entropy 한 번 뒤에는 0.
- Merkle 비교는 해시 55개로 다른 키 3개를 정확히 찾았다. 다른 키가 적을수록 이득이 크다. 다른 키가 많으면 내려가야 할 가지가 늘어난다.

### 5. 정족수 미달 → 쓰기 거부

- W개(엄격한 정족수) 또는 과반(합의 시스템)에 닿지 못하면 쓰기는 실패한다. 이것이 정족수가 분할 때 가용성을 잃는 지점이다(08번).

#### 실험: etcd 3.6.5 — 과반을 잃으면 쓰기 거부

(실험, etcd 3.6.5 일회용 3노드, 과반 정족수 2, 2026-10-01)

```text
3/3 살아 있음: put → OK
2/3 살아 있음(etcd3 정지): put → OK
1/3 살아 있음(etcd2·3 정지): put → Error: context deadline exceeded [3091ms]
1/3: 직렬화 읽기 → b
복구 뒤 선형화 읽기 → b
```

- 3노드 과반은 2다. 하나가 죽어도 쓰기가 됐고, 둘이 죽자 3초 타임아웃으로 실패했다.
- etcd는 Dynamo식 R/W 정족수가 아니라 Raft 과반이다(11번). "겹치는 집합에서만 진행"이라는 원리는 같다.

## 쓰이는 자료구조·알고리즘

- **Merkle 트리 anti-entropy** — 키 범위마다 해시 트리를 두고 루트부터 비교해 다른 잎만 찾는다(Dynamo §4.7, Cassandra repair). 실험에서 1024키 중 3개 차이를 해시 55개로 찾았다. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
- **일관 해싱 + 가상 노드** — 키를 링에 올려 담당 노드 N개(preference list)를 정한다. 노드가 들고 나도 옮기는 키가 일부다(Dynamo §4.2, Cassandra 5.0 "Dynamo" 절). [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)
- **버전 벡터** — 읽은 R개 중 "최신"과 "동시"를 가린다(Dynamo §4.4). [05-logical-clocks](../05-logical-clocks/2-summary.md), [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md)
- **집합의 교집합(비둘기집 원리)** — |W| + |R| > N이면 두 부분집합은 겹친다. 과반 정족수는 R = W = ⌊N/2⌋ + 1인 특수한 경우다.

## 적용 — 풀어나가는 법

### 1. N·R·W를 연산 목적에 맞춘다

| 목표 | 예 (N=3) | 얻는 것 | 잃는 것 |
|---|---|---|---|
| 읽은 값이 대개 최신 | R=2, W=2 | 겹침 | 복제본 2개가 죽으면 읽기·쓰기 실패 |
| 빠른 읽기 | R=1, W=3 | 겹침 + 읽기 1개 | 복제본 하나만 죽어도 쓰기 실패 |
| 쓰기 가용성 최대 | W=1 (또는 Cassandra `ANY`) | 복제본 하나만 살아 있어도 쓰기 성공(`ANY`는 힌트만으로도) | 옛 값 읽기, 노드 하나 잃으면 유실 가능 |

- 다중 데이터센터면 Cassandra `LOCAL_QUORUM`(로컬 DC 과반)으로 원거리 왕복을 피한다. 다른 DC의 읽기는 그 쓰기를 늦게 볼 수 있다.

### 2. 일관성 수준을 코드에 드러낸다

```java
// DataStax Java Driver 4.x: 연산마다 일관성 수준을 명시
SimpleStatement write = SimpleStatement.builder("UPDATE account SET email = ? WHERE id = ?")
        .addPositionalValues(email, id)
        .setConsistencyLevel(DefaultConsistencyLevel.QUORUM)    // W = 과반
        .build();
SimpleStatement read = SimpleStatement.builder("SELECT email FROM account WHERE id = ?")
        .addPositionalValues(id)
        .setConsistencyLevel(DefaultConsistencyLevel.QUORUM)    // R = 과반 → R+W>RF
        .build();
session.execute(write);
Row row = session.execute(read).one();
```

- 정족수 미달이면 드라이버 4.x가 `com.datastax.oss.driver.api.core.servererrors.UnavailableException`을 올린다(코디네이터가 살아 있는 복제본이 모자란다고 미리 아는 경우). 재시도 규칙은 오류 종류마다 다르다(DataStax Java Driver 4.17 "Retries").
  - `UnavailableException`: 기본 정책이 다음 노드로 최대 한 번 재시도한다. 코디네이터가 시작 전에 거절한 것이라 멱등 여부를 따지지 않는다.
  - 쓰기 타임아웃(`WriteTimeoutException`): 멱등인 문장만 재시도 정책에 넘기고, 아니면 바로 올린다. 일부 복제본에 쓰기가 남아 있을 수 있기 때문이다(§2).

### 3. 복구를 운영한다

```bash
# Cassandra 5.0: 증분 repair(기본), 전체 repair, 노드별 주 범위만
nodetool repair
nodetool repair --full
nodetool repair -pr <keyspace>
# 힌트 창 확인
nodetool getmaxhintwindow
```

- 문서의 출발점 권고: 증분 repair 1~3일, 전체 repair 1~3주마다. 기본 gc grace 10일이면 모든 노드를 적어도 7일마다 repair해야 지운 데이터가 되살아나지 않는다(Cassandra 5.0 "Repair").
- 노드가 `max_hint_window`(3시간)보다 오래 내려가 있었다면 돌아온 뒤 repair를 돌린다. 힌트는 장애 뒤 처음 3시간 동안의 쓰기에만 만들어지므로, 그 이후의 쓰기는 힌트로 메워지지 않는다(Cassandra 5.0 "Hints").

## 장애 시나리오와 대처

### 1. sloppy quorum에서 R+W>N이어도 오래된 읽기

- **현상**: R=W=2(N=3)로 설정했는데 분할 중·직후 방금 쓴 값이 안 보인다.
- **보이는 형태**: 쓰기는 성공 응답, 반대편 클라이언트 읽기는 옛 값. 분할이 풀리고 hinted handoff가 끝나면 보인다.
- **원인**: 쓰기가 원래 복제본이 아닌 대체 노드에 W를 채웠다. 읽기는 원래 복제본에서 R을 채웠다. 숫자는 맞지만 집합이 안 겹친다(시뮬레이션 [C]).
- **대처**: 최신 값이 꼭 필요한 연산은 대체 노드를 정족수에 세지 않는 설정·제품을 쓴다(Cassandra는 `ANY` 외 일관성 수준이 진짜 복제본만 센다). 분할 뒤 hinted handoff·repair가 끝났는지 확인한다.

### 2. 정족수 미달 → 쓰기 거부

- **현상**: 노드 둘이 동시에 내려가자 해당 키 범위의 쓰기가 모두 실패한다.
- **보이는 형태**: Cassandra Java 드라이버 4.x의 `UnavailableException`, 메시지 형식 `Not enough replicas available for query at consistency QUORUM (2 required but only 1 alive)`(드라이버 소스의 형식 문자열), etcd의 `context deadline exceeded`(실험에서 3초 타임아웃 3091ms).
- **원인**: 살아 있는 복제본이 W(또는 과반)보다 적다. 일관성을 위해 쓰기를 받지 않는다.
- **대처**: 복제본을 장애 도메인(랙·영역)에 나눠 동시 장애 확률을 낮춘다. 일시적으로 가용성이 더 중요한 연산만 일관성 수준을 낮추고 그 사실을 기록한다. 노드를 복구한 뒤 repair한다.

### 3. 쓰기 타임아웃인데 값은 일부 반영됨

- **현상**: 쓰기가 타임아웃으로 실패했는데, 다음 읽기에 그 값이 보였다가 또 다음 읽기에는 사라진다.
- **보이는 형태**: 클라이언트 재시도 없이도 값이 나타난다. Cassandra `read_repair = NONE` 테이블에서 두드러진다(문서의 "monotonic quorum reads" 미보장).
- **원인**: W 미만 복제본에만 쓰였고 되돌려지지 않았다. 그 복제본이 읽기 R개에 끼면 보이고, 안 끼면 안 보인다.
- **대처**: 쓰기 타임아웃은 "실패"가 아니라 "모름"으로 다룬다(03번). 멱등 키로 재시도한다. 기본 blocking 읽기 복구를 끄지 않는다.

### 4. repair를 안 돌림 → 지운 데이터가 되살아남

- **현상**: 지운 행이 몇 주 뒤 다시 조회된다.
- **보이는 형태**: 특정 노드를 거친 읽기에서만 보인다. 그 노드는 삭제 시점에 다운이었거나 힌트 창을 넘겼다.
- **원인**: 삭제 표시(tombstone)가 다른 복제본에서 gc grace(기본 10일) 뒤 지워졌는데, 그 노드에는 옛 값이 남아 있었다. 이후 읽기 복구·repair가 옛 값을 "살아 있는 데이터"로 퍼뜨린다(Cassandra 5.0 "Repair").
- **대처**: gc grace보다 짧은 주기로 모든 노드를 repair한다(기본값이면 7일). 오래 내려가 있던 노드는 repair 전에 서비스에 다시 넣지 않는다.

## 핵심 문장

- R + W > N이면 쓴 집합과 읽은 집합이 겹쳐, 읽은 R개 중 하나는 마지막 성공한 쓰기를 갖고 있다. 버전 비교가 전제다.
- R+W>N은 "대개 최신"이지 선형화가 아니다. sloppy quorum, 동시 쓰기, 부분 실패한 쓰기가 예외를 만든다.
- sloppy quorum은 가용성을 위해 대체 노드에 쓰고 힌트로 돌려준다. 숫자는 맞아도 노드 집합이 안 겹칠 수 있다.
- 놓친 쓰기는 읽기 복구(읽힌 것만)와 anti-entropy(전체, Merkle 트리)가 메운다. 보장은 anti-entropy 쪽이다.
- 정족수를 채울 수 없으면 쓰기는 거부된다. 그것이 일관성의 값이다.

## 관련 주제·근거

- 선행
  - [06-replication-strategies](../06-replication-strategies/2-summary.md) — 리더리스 복제, 읽기 복구
- 후속·연결
  - [07-consistency-models](../07-consistency-models/2-summary.md) — 선형화와의 거리
  - [08-cap-and-pacelc](../08-cap-and-pacelc/2-summary.md) — 정족수 미달 = 분할 시 가용성 포기
  - [27-chain-replication-and-striping](../27-chain-replication-and-striping/2-summary.md) — 앙상블·쓰기 정족수·ack 정족수(BookKeeper)
  - [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md) — 동시 쓰기의 해소
  - [03-partial-failure-and-timeouts](../03-partial-failure-and-timeouts/2-summary.md) — 타임아웃 = 모름 · [11-consensus-raft](../11-consensus-raft/2-summary.md) — 과반 정족수
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md) · [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)
- 논문·교재
  - DeCandia 외, "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007 — §4.2 일관 해싱·가상 노드, §4.3 preference list, §4.4 벡터 시계, §4.5 R·W(지연은 가장 느린 R·W개), §4.6 sloppy quorum·hinted handoff, §4.7 Merkle 트리 anti-entropy, §5 읽기 복구, §6 (3,2,2) <https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf>
  - DDIA 1판 5장 Leaderless Replication — Quorums for reading and writing, Limitations of Quorum Consistency, Sloppy Quorums and Hinted Handoff, Read repair and anti-entropy
  - Abadi 2012(R+W>N이어도 완전한 일관성 아님), Kleppmann 2015(정족수 + sloppy quorum·읽기 복구의 비선형화 경우)
- 제품 문서
  - Apache Cassandra Auto Repair(6.0에서 도입, 5.0.8로 백포트, 기본 꺼짐) <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/auto_repair.html> · DataStax Java Driver 4.17 Retries(오류별 재시도, 쓰기 타임아웃·요청 중단·오류 응답은 멱등 문장만 정책에 넘김) <https://docs.datastax.com/en/developer/java-driver/4.17/manual/core/retries/index.html>
  - Apache Cassandra 5.0 — Dynamo 절(Tunable Consistency, `ANY`, 쓰기는 모든 복제본에 전송, Merkle repair), Hints(`max_hint_window` 기본 3시간, 타임아웃 2초 예), Read repair(blocking 기본, monotonic quorum reads), Repair(증분·전체, gc grace 10일·7일 주기) <https://cassandra.apache.org/doc/5.0/cassandra/architecture/dynamo.html>
- 실험 목록
  - Java 21 시뮬레이션 N=3: [A] R·W 6조합 옛 값 비율(2만 회), [B] 유실 10%에서 복구 없음·읽기 복구·anti-entropy, [C] sloppy quorum 시나리오, [D] Merkle 비교 해시 수
  - etcd 3.6.5 일회용 3노드: 노드를 하나씩 정지하며 put 성공·실패
