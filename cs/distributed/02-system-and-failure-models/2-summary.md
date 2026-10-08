# distributed/02-system-and-failure-models — 시스템 모델: 시간 가정(동기·부분동기·비동기)과 고장 가정(crash-stop·crash-recovery·비잔틴) — 정리 (힌트)

## 해결하는 문제

분산 알고리즘이 "맞다"고 말하려면, **무엇이 일어날 수 있다고 가정했는지**부터 정해야 한다.

- *시스템 모델(system model)*: 알고리즘이 기대해도 되는 것과 견뎌야 하는 것을 적은 추상. 네트워크 지연·멈춤·시계 오차에 대한 **시간 가정**과, 노드가 어떻게 고장 나는지에 대한 **고장 가정** 두 축으로 정한다(DDIA 1판 8장 "System Model and Reality").

가정 없이 짠 코드는 가장 흔하게 이 지점에서 깨진다. **느린 노드와 죽은 노드를 구분하지 못한다.**

쉬운 예: 친구에게 메시지를 보냈는데 답이 없다.
- 바쁜가? 휴대폰을 잃어버렸나? 메시지가 안 갔나?
- 10분 기다리고 "잃어버렸나 보다" 하고 다른 친구에게 같은 부탁을 했다.
- 그런데 첫 친구는 그냥 바빴고, 나중에 부탁을 처리했다. 일이 두 번 됐다.

똑같은 구조다.\
"얼마나 기다리면 죽었다고 봐도 되나"는 **시간 가정**의 문제다.\
"죽었다가 다시 살아나 옛일을 계속할 수 있나"는 **고장 가정**의 문제다.

실무 예:
- 리더가 GC로 몇 초 멈췄다. 나머지가 새 리더를 뽑았다. 옛 리더가 깨어나 자기가 아직 리더인 줄 알고 쓰기를 계속한다(DDIA 8장 "Process Pauses").
- 분산 락의 lease가 만료됐는데 락을 쥐었던 클라이언트가 멈췄다 깨어나 파일을 덮어쓴다(DDIA 그림 8-4, HBase에서 실제로 있었던 버그로 소개).
- 장애 탐지 타임아웃을 너무 짧게 잡아, 멀쩡한 노드를 자꾸 죽었다고 판단해 리더 선거가 반복된다.

## 동작·원리

### 1. 시간 가정 세 가지

```text
              네트워크 지연·프로세스 멈춤·시계 오차에 대한 가정
  동기(synchronous)        ├──────────┤ 상한 Δ를 안다. 넘지 않는다고 가정한다
                           0          Δ

  부분 동기(partially       ├──────────┤~~~~~~~~~~┤──────────┤
   synchronous)            평소엔 상한 안   가끔 넘는다   다시 안으로(언젠가 안정)

  비동기(asynchronous)      ├──────────────────────────────→ 상한이 없다
                           시계도 없다고 본다 → 타임아웃을 쓸 수 없다
```

- *동기 모델*: 네트워크 지연, 프로세스 멈춤, 시계 오차에 **고정된 상한**이 있고 알고리즘이 그 값을 안다. 지연이 0이라는 뜻은 아니다. 대부분의 실제 시스템과 맞지 않는다(DDIA 8장).
- *부분 동기 모델*: DDIA 8장의 풀이로는 대부분은 동기처럼 굴지만 가끔 상한을 넘는다. 실제 시스템에 가장 가깝다. 원래 정의는 Dwork·Lynch·Stockmeyer 1988 "Consensus in the Presence of Partial Synchrony"에서 왔고, 논문 초록은 두 판을 든다.
  - 상한은 있지만 알고리즘이 그 값을 모른다.
  - 상한을 알지만 알 수 없는 어느 시점부터만 지켜진다. 그 전에는 상한을 넘는 일이 드물 필요도 없다.
- *비동기 모델*: 시간에 대해 아무 가정도 하지 않는다. 시계가 없다고 보므로 타임아웃도 못 쓴다. FLP 불가능성이 이 모델에서 증명됐다(25).

### 2. 고장 가정 세 가지

```text
  crash-stop        ●───────✝            한 번 멈추면 영영 안 돌아온다

  crash-recovery    ●───────✝ · · · ●────  멈췄다가 다시 돌아올 수 있다
                    [디스크]──────→[디스크]   안정 저장소는 남고, 메모리는 잃는다

  비잔틴(Byzantine)  ●───?거짓말?──?다른 말?─  무엇이든 한다(속이기·모순된 메시지 포함)
```

- *crash-stop*: 노드는 오직 멈춤으로만 고장 난다. 멈춘 뒤에는 영원히 사라진다.
- *crash-recovery*: 아무 때나 멈췄다가 알 수 없는 시간 뒤에 다시 응답할 수 있다. 디스크 같은 **안정 저장소(stable storage)**는 살아남고 메모리 상태는 잃는다고 가정한다.
- *비잔틴*: 노드가 무엇이든 할 수 있다. 다른 노드를 속이려는 행동도 포함한다. 비잔틴 내결함 알고리즘은 대부분 노드의 **3분의 2 초과**가 정상이어야 한다(예: 4대면 1대까지)(DDIA 8장 "Byzantine Faults").

DDIA 8장의 결론: 실제 시스템을 모델링할 때는 **부분 동기 + crash-recovery**가 대체로 가장 쓸모 있다.

### 3. 두 축을 합쳐 놓고 알고리즘을 놓아 보기

| 알고리즘·결과 | 시간 가정 | 고장 가정 | 무엇을 보장하나 |
|---|---|---|---|
| FLP 1985 | 비동기 | crash 1대 | 결정적 합의가 **항상 끝난다**는 보장이 불가능 |
| Raft(Ongaro–Ousterhout 2014) | 안전성은 시간에 의존하지 않음, 가용성은 `broadcastTime ≪ electionTimeout ≪ MTBF` 필요 | crash-recovery(`currentTerm`·`votedFor`·`log[]`를 응답 전에 안정 저장소에 기록) | 과반이 살아 있고 시간이 안정되면 진행 |
| Paxos(Lamport 2001) | 안전성은 선거 성공 여부와 무관, 진행은 무작위성이나 실제 시간(타임아웃)이 필요 | crash-recovery | 같음 |
| 비잔틴 합의(PBFT 등) | 31번에서 다룬다 | 비잔틴 | 노드의 3분의 2 초과가 정상일 때(DDIA 8장) |

- Raft 논문 §5.6: "안전성은 시간에 의존하면 안 된다. 사건이 예상보다 빠르거나 느리다는 이유만으로 틀린 결과를 내면 안 된다. 그러나 가용성은 시간에 의존할 수밖에 없다."
- Raft 그림 2: `currentTerm`·`votedFor`·`log[]`는 "RPC에 응답하기 전에 안정 저장소에 갱신"하는 영속 상태다. crash-recovery 가정을 코드로 옮긴 모양이다.
- Paxos Made Simple §2.4: FLP 때문에 제안자 선출은 무작위성이나 실제 시간(타임아웃)을 써야 한다. 그래도 안전성은 선출의 성공 여부와 무관하게 지켜진다.

### 4. 안전성과 활성 — 무엇은 "항상", 무엇은 "언젠가"

```text
  안전성(safety)  "나쁜 일은 일어나지 않는다"   깨지면 → 깨진 시점을 짚을 수 있다, 되돌릴 수 없다
                   예) 같은 펜싱 토큰을 두 번 주지 않는다, 한 임기에 리더가 둘이 아니다
  활성(liveness)   "좋은 일은 언젠가 일어난다"  지금은 아니어도 → 나중에 성립할 수 있다
                   예) 요청한 노드는 언젠가 응답을 받는다. "최종 일관성"도 활성이다
```

- DDIA 8장: 분산 알고리즘은 보통 **모든 상황에서 안전성**을 요구한다. 모든 노드가 죽거나 네트워크 전체가 끊겨도 틀린 결과를 내면 안 된다.
- 활성은 조건을 붙인다. 예: 과반이 살아 있고, 네트워크 중단이 언젠가 끝날 때에만 응답을 보장한다.
- 이 구분이 설계의 출발점이다. "시간이 어긋나면 느려질 수는 있어도 틀리지는 않게" 짠다.

### 5. 느린 것과 죽은 것 — 왜 구분이 안 되나

```text
  리더 L                       팔로워 F1·F2
  ────────────────────────────────────────────────────────
  하트비트 ──→                  "살아 있네"
  [GC 멈춤 시작 ··········]     하트비트가 안 온다
  [··········]                  선거 타임아웃 → F1이 새 리더(임기 +1)
  [·········· 멈춤 끝]          
  "나는 리더다" 쓰기 시도 ──→    "임기가 낮다, 거절" → L은 팔로워로 내려옴
  ────────────────────────────────────────────────────────
  L 입장: 시간이 거의 안 흐른 것 같다.   나머지 입장: L은 죽었었다.
```

- 프로세스가 오래 멈추는 원인(DDIA 8장 "Process Pauses"): stop-the-world GC, 가상 머신 일시 정지·라이브 마이그레이션, OS·하이퍼바이저의 컨텍스트 스위치(steal time), 동기 디스크 I/O(클래스 로딩 포함), 스왑으로 인한 페이지 폴트, `SIGSTOP`.
- 멈춘 노드는 **깨어난 뒤 시계를 다시 볼 때까지** 자기가 멈췄었다는 걸 모른다.
- 그래서 한 노드의 판단을 믿지 않고 **과반(정족수)이 결정한다**. 과반이 "죽었다"고 하면 본인이 살아 있다고 느껴도 죽은 것으로 취급하고 물러나야 한다(DDIA 8장 "The Truth Is Defined by the Majority").

### 실험 A: etcd 리더를 "죽이지 않고 멈추기"

etcd 3.6.5 3노드(전용 컨테이너)에서 리더 컨테이너를 `docker pause`로 얼렸다.
- `docker pause`는 Linux에서 freezer cgroup을 쓴다. `SIGSTOP`과 달리 프로세스는 자기가 멈춘 걸 감지하지 못한다(Docker 문서). GC 멈춤과 같은 모양이다.
- etcd 기본값: 하트비트 간격 100 ms, 선거 타임아웃 1000 ms(etcd v3.6 Tuning 문서). 이 실험은 기본값 그대로다.

```bash
docker pause sn-dw-w01-etcd2          # 리더를 얼린다 (프로세스는 살아 있다)
etcdctl --command-timeout=1s --endpoints=<나머지 둘> endpoint status -w json   # 0.6초 간격으로 반복
docker unpause sn-dw-w01-etcd2        # 4초쯤 뒤 녹인다
docker logs sn-dw-w01-etcd2 | grep "became"
```

(실험, etcd 3.6.5 3노드 전용 컨테이너 `sn-dw-w01-etcd1~3`, 기본 하트비트 100 ms·선거 타임아웃 1000 ms, 2026-10-01)

```text
[01:01:58.153] 시작: 리더 = sn-dw-w01-etcd2
    sn-dw-w01-etcd1  leader=d5f2ed71e5414281 term=4 is_leader=False
    sn-dw-w01-etcd2  leader=d5f2ed71e5414281 term=4 is_leader=True
    sn-dw-w01-etcd3  leader=d5f2ed71e5414281 term=4 is_leader=False
[01:01:58.343] docker pause sn-dw-w01-etcd2 (프로세스는 살아 있고 멈췄을 뿐)
[01:01:58.847] +567 ms, 나머지 두 노드의 상태:
    sn-dw-w01-etcd1  leader=d5f2ed71e5414281 term=4 is_leader=False
    sn-dw-w01-etcd3  leader=d5f2ed71e5414281 term=4 is_leader=False
[01:01:59.445] +1166 ms, 나머지 두 노드의 상태:
    sn-dw-w01-etcd1  leader=b45b868de165f93f term=5 is_leader=True
    sn-dw-w01-etcd3  leader=b45b868de165f93f term=5 is_leader=False
...
[01:02:01.970] 멈춘 옛 리더에 쓰기 시도(1초 타임아웃):
    Error: context deadline exceeded
[01:02:03.104] docker unpause sn-dw-w01-etcd2, 1초 뒤 세 노드:
    sn-dw-w01-etcd1  leader=b45b868de165f93f term=5 is_leader=True
    sn-dw-w01-etcd2  leader=b45b868de165f93f term=5 is_leader=False
    sn-dw-w01-etcd3  leader=b45b868de165f93f term=5 is_leader=False
[01:02:04.227] 옛 리더 로그(역할 변화):
     2026-10-01T01:01:45.509017Z d5f2ed71e5414281 became leader at term 4
     2026-10-01T01:02:03.082880Z d5f2ed71e5414281 became follower at term 5
[01:02:04.255] 나머지 노드 로그(선거):
     2026-10-01T01:01:59.361524Z b45b868de165f93f became pre-candidate at term 4
     2026-10-01T01:01:59.362061Z b45b868de165f93f became candidate at term 5
     2026-10-01T01:01:59.367688Z b45b868de165f93f became leader at term 5
```

- 관찰
  - 얼린 시각 01:01:58.343 → 다른 노드가 `pre-candidate`가 된 시각 01:01:59.361. 약 1.0초다. 6 ms 뒤 새 리더가 됐고 임기(term)가 4 → 5로 올랐다.
  - etcd raft는 선거 타임아웃을 매번 `[electionTimeout, 2×electionTimeout)` 범위에서 무작위로 고른다(`etcd-io/raft` `raft.go` `resetRandomizedElectionTimeout`). 기본값이면 1~2초 사이다. 사실 점검 때 다시 돌린 두 번은 1.39초·1.01초였다.
  - 클라이언트가 얼린 노드에 쓰려 하자 `context deadline exceeded`만 받았다. 클라이언트 입장에서 이 노드는 죽은 것과 구별되지 않는다.
  - 녹인 뒤 옛 리더는 더 높은 임기(5)를 보고 `became follower at term 5`로 물러났다. 과반의 결정이 본인 판단을 이긴다.
  - 실험을 세 번 했다(리더가 매번 바뀜). 재선출까지 걸린 시간과 리더 ID는 실행마다 다르다. 마지막에 본 각 멤버의 `etcd_server_leader_changes_seen_total`은 4(첫 선출 1 + 멈춤 3)였다.
- 해석: etcd는 이 경우 옛 리더가 쓰기를 커밋하지 못하게 막는다(과반 복제가 필요하므로). 그러나 **etcd 밖의 자원**(파일·DB)에 옛 리더나 옛 락 보유자가 직접 쓰는 것은 etcd가 막을 수 없다. 그래서 펜싱 토큰이 필요하다(장애 1, 12번).

### 실험 B: 고정 타임아웃 탐지기 vs φ accrual 탐지기

- *장애 탐지기(failure detector)*: 하트비트 같은 신호로 "저 노드가 죽은 것 같다"고 판정하는 부품. 비동기 모델에서는 완벽할 수 없고, 언제나 오판 가능성이 있다.
- *φ accrual 탐지기*: Hayashibara 외 2004. "죽었다/살았다" 두 값 대신 **의심 정도 φ**를 연속값으로 낸다. 최근 하트비트 간격의 평균·표준편차로 정규분포를 만들고, "지금까지 안 온 것"이 그 분포에서 얼마나 드문지를 φ = −log10(1 − F(경과 시간))으로 잰다. φ=8이면 대략 1억 분의 1 확률(10⁻⁸)로 드문 늦음이라는 뜻이다(정의에서 계산).
  - Akka(main 브랜치 `reference.conf`) 기본: `threshold = 8.0`, `heartbeat-interval = 1 s`, `acceptable-heartbeat-pause = 3 s`, `min-std-deviation = 100 ms`. `acceptable-heartbeat-pause`는 평균에 더해져 "이만큼의 공백은 정상"으로 본다.
  - Cassandra `cassandra.yaml`(trunk)의 `phi_convict_threshold` 주석 기본값도 8이다.

아래 Java 코드는 Akka `PhiAccrualFailureDetector.phi`의 근사식을 그대로 옮겼다. 하트비트는 시뮬레이션이다(시드 고정, 평균 1000 ms, σ 50 ms).

```java
static double phi(long timeDiff, double mean, double std) {      // Akka와 같은 로지스틱 근사
    double y = (timeDiff - mean) / std;
    double e = Math.exp(-y * (1.5976 + 0.070566 * y * y));
    return timeDiff > mean ? -Math.log10(e / (1.0 + e)) : -Math.log10(1.0 - 1.0 / (1.0 + e));
}
double phi(long now) {
    double mean = intervalMean(), std = Math.max(intervalStdDev(), minStdMs);   // 최근 간격들의 평균·표준편차
    return phi(now - lastHeartbeat, mean + acceptablePauseMs, std);   // 허용 공백을 평균에 더한다
}
```

(실험, Temurin 21.0.12, 시뮬레이션 — 출력에서 일부 행 생략)

```text
== GC 멈춤 2.5초 뒤 회복 (마지막 정상 하트비트 t=120094 ms)
  경과(ms) | 고정 1.5s | φ(pause 0) | 판정 | φ(pause 3s) | 판정
      1000 | 살아있음   |       0.30 | -    |        0.00 | -
      1500 | 살아있음   |       7.29 | -    |        0.00 | -
      2000 | 죽음     |      37.55 | 의심   |        0.00 | -
      3500 | 죽음     |        >99 | 의심   |        0.00 | -
      3750 | 살아있음   |       0.00 | -    |        0.00 | - <- 하트비트 도착(+3538)
== 120초에 크래시(영구) (마지막 정상 하트비트 t=120094 ms)
      4500 | 죽음     |        >99 | 의심   |        7.29 | -
      5000 | 죽음     |        >99 | 의심   |       37.55 | 의심
== 살아 있는 노드 600초, 간격 σ=50 ms: 고정 1.5s 오탐 0회 | φ>8 오탐 0회
== 살아 있는 노드 600초, 간격 σ=300 ms: 고정 1.5s 오탐 18회 | φ>8 오탐 0회
== 살아 있는 노드 600초, 간격 σ=500 ms: 고정 1.5s 오탐 86회 | φ>8 오탐 0회
```

- 관찰
  - 2.5초 GC 멈춤: 고정 1.5초와 φ(허용 공백 0)는 2초 무렵 "죽음/의심"으로 판정했다. 노드의 하트비트는 3.5초(+3538 ms)에 다시 왔다. **살아 있는 노드를 죽었다고 판단한 것**이다. φ(허용 공백 3초)는 끝까지 의심하지 않았다.
  - 진짜 크래시: φ(허용 공백 3초)는 5초 무렵에야 의심했다. 오판을 줄인 대가로 **진짜 고장을 3초 늦게 알아챈다**.
  - 하트비트 간격이 들쭉날쭉(σ 300·500 ms)한 살아 있는 노드: 고정 1.5초는 600초 동안 18회·86회 오탐했다. φ(허용 공백 0)는 흔들림을 분포로 배워서 0회였다.
- 해석: 장애 탐지는 **빨리 알아채기 vs 오판하지 않기**의 교환이다. 어떤 탐지기도 비동기 네트워크에서 둘 다 완벽하게 할 수는 없다. φ는 문턱 하나로 그 교환점을 고르게 해 주고, 네트워크 상태에 맞춰 자동으로 조정된다(DDIA 8장 "Timeouts and Unbounded Delays").

## 쓰이는 자료구조·알고리즘

- **φ accrual 장애 탐지기**: 최근 N개(Akka 기본 `max-sample-size = 1000`) 하트비트 간격을 담는 **고정 크기 큐(링 버퍼)** + 평균·분산의 누적합 + 정규분포 누적분포함수(CDF) 근사.
- **하트비트 + 타임아웃**: 고정 타임아웃 탐지기. 구현은 노드별 "마지막으로 들은 시각" 해시 맵과 타이머.
- **임기 번호(term·epoch·generation)**: 단조 증가 정수. 옛 리더를 알아보는 데 쓴다(실험 A의 term 4 → 5). 펜싱 토큰도 같은 생각이다.
- **정족수(quorum)**: 과반 투표. 같은 멤버 집합에서 뽑은 두 과반은 적어도 한 노드가 겹친다. 여기에 "겹친 노드는 한 임기에 한 번만 투표한다"(Raft) 같은 투표 규칙이 더해져야 결정이 두 개로 갈리지 않는다(09·11번).
- **lease(임대)**: 만료 시각이 있는 락. 시간 가정 위에 서 있으므로 멈춤에 약하다(10·12번).
- 단조 시계: 하트비트 간격은 벽시계가 아니라 단조 시계로 잰다(04번).

## 적용 — 풀어나가는 법

1. **부품마다 가정을 적는다.** 예: "DB 복제는 crash-recovery, 메시지 브로커는 at-least-once, 외부 결제사는 비잔틴은 아니지만 응답이 늦거나 사라질 수 있다."
2. **안전성 조건과 활성 조건을 나눈다.** "리더는 하나" 같은 안전성은 시간에 기대지 않게 짠다(정족수·임기·펜싱 토큰). "언젠가 응답"은 타임아웃에 기대도 된다.
3. **장애 탐지 문턱을 측정으로 고른다.** 하트비트 간격·RTT 분포를 재고, 오판 비용과 늦은 탐지 비용을 비교한다(03번).
4. **멈춤 원인을 줄이고 관측한다.** GC 로그, 스왑 끄기, VM steal time, 디스크 `fsync` 지연.
5. **자기 판단 대신 과반·토큰을 믿는다.** 깨어난 노드는 "내가 아직 리더인가"를 외부에 확인하거나, 자원 쪽에서 낡은 토큰을 거절하게 한다.

```java
// 자원 쪽 펜싱 검사 — 클라이언트가 스스로 락을 확인하는 것만으로는 부족하다(DDIA 8장 "Fencing tokens")
class FencedStore {
    private long highestToken = -1;
    synchronized void write(long fencingToken, String key, String value) {
        if (fencingToken < highestToken)
            throw new IllegalStateException("낡은 토큰 " + fencingToken + " < " + highestToken + " — 거절");
        highestToken = fencingToken;
        doWrite(key, value);
    }
}
```

진단 명령:
- 리더·임기 확인: `etcdctl --endpoints=… endpoint status -w table`(IS LEADER·RAFT TERM 열)
- 리더 교체 횟수: etcd 지표 `etcd_server_leader_changes_seen_total`, `etcd_server_has_leader`, `etcd_server_heartbeat_send_failures_total` (`curl -s http://<member>:2379/metrics`)
- 역할 변화 로그: `docker logs <etcd> | grep -E "became (pre-candidate|candidate|leader|follower)"`
- JVM 멈춤: `java -Xlog:gc*:file=gc.log …`, `jstat -gcutil <pid> 1000`
- 스왑·steal: `vmstat 1`(si/so·st 열)

## 장애 시나리오와 대처

### 1. 느림을 죽음으로 판단 → 이중 처리 (⚠ 커리큘럼)

- **현상**: 리더나 락 보유자가 GC·VM 정지로 몇 초 멈췄다. 그 사이 다른 노드가 이어받았고, 깨어난 옛 주인도 일을 계속해 같은 작업이 두 번 실행되거나 파일이 깨졌다.
- **보이는 형태**: 같은 시각 근처에 "리더가 됨" 로그가 두 노드에서 보인다. 같은 배치·메일·결제가 두 번 나간다. GC 로그에 수 초짜리 멈춤이 있다.
- **원인**: 부분 동기·crash-recovery 세계에서 "멈췄다 돌아온 노드"를 고려하지 않았다. lease·타임아웃은 상대의 상태를 알려 주지 않는다(실험 A·B).
- **대처**: 펜싱 토큰(단조 증가 번호를 자원이 검사), 임기 번호로 낡은 리더 거절, 과반 확인 후 쓰기. 자세한 구현은 12번(`coordination-and-fencing`).

### 2. 너무 민감한 탐지 → 리더 선거가 반복된다

- **현상**: 장애가 없는데 리더가 자주 바뀌고, 그때마다 쓰기가 잠깐 멈춘다.
- **보이는 형태**: `etcd_server_leader_changes_seen_total`이 계속 오른다. 로그에 `became candidate`가 잦다. 디스크가 느린 노드에서 특히 잦다.
- **원인**: 선거 타임아웃(또는 탐지 문턱)이 실제 지연 분포의 꼬리보다 짧다. etcd 문서: 디스크 `fsync` 지연이 길면 하트비트를 놓쳐 요청 타임아웃과 일시적 리더 상실이 생긴다.
- **대처**: RTT·디스크 지연을 재고 선거 타임아웃을 RTT의 10배 이상으로(etcd v3.6 Tuning 문서의 권장). 전 멤버가 같은 값을 써야 한다. etcd 디스크 우선순위(`ionice`)를 올린다. 고정 타임아웃 대신 φ 같은 적응형 탐지기를 쓴다(실험 B: 간격 σ 500 ms에서 고정 1.5초 오탐 86회 vs φ 0회).

### 3. crash-recovery 가정이 깨짐 — 디스크를 잃고 돌아온 노드

- **현상**: 데이터 디렉터리가 손상·삭제된 노드를 같은 이름으로 다시 띄웠다. 정족수 계산이 어긋나 이미 커밋된 기록을 잃을 위험이 생긴다.
- **보이는 형태**: 멤버가 빈 상태로 합류하려 하거나 클러스터 ID 불일치 오류가 난다.
- **원인**: Raft 같은 정족수 알고리즘은 노드가 **저장했다고 말한 것을 기억한다**고 가정한다. 기억을 잃은 노드는 이 가정을 깬다(DDIA 8장 "Mapping system models to the real world"의 기억 상실 사례).
- **대처**: etcd v3.6 런타임 재구성 문서대로 고장 난 멤버를 **제거하고 새 멤버로 추가**한다. 제거된 멤버의 데이터 디렉터리로 다시 띄우면 etcd가 종료한다. 문서에 실린 예시 문구는 "etcd: this member has been permanently removed from the cluster. Exiting."이다. 하지만 etcd 3.6.5에서 실제로 보이는 것은 아래 JSON 로그 두 줄이고 종료 코드는 1이다(문구 출처: `server/etcdserver/api/rafthttp/util.go`의 `errMemberRemoved`, `server/etcdserver/server.go`).

(실험, etcd 3.6.5 3노드 전용 컨테이너 `sn-dw-wcons-e1~3`, e3를 멈추고 `etcdctl member remove` → e3 다시 시작, 2026-10-01 — 시각은 실행마다 다르다)

```json
{"level":"warn","ts":"2026-10-01T06:04:31.247984Z","caller":"etcdserver/server.go:860","msg":"server error","error":"the member has been permanently removed from the cluster"}
{"level":"warn","ts":"2026-10-01T06:04:31.248114Z","caller":"etcdserver/server.go:861","msg":"data-dir used by this member must be removed"}
```

### 4. 비잔틴은 아니라고 가정했는데 데이터가 깨져 온다

- **현상**: 드물게 내용이 틀린 메시지나 디스크 블록이 나온다.
- **보이는 형태**: 역직렬화 실패, 체크섬 불일치, 설명할 수 없는 값.
- **원인**: 비트 뒤집힘·펌웨어 버그는 crash 모델 바깥이다. 그렇다고 같은 소프트웨어를 모든 노드에 깔면 비잔틴 내결함 알고리즘도 버그를 막지 못한다(DDIA 8장).
- **대처**: 비잔틴 알고리즘 대신 "약한 거짓말" 방어 — 애플리케이션 체크섬, 입력 검증, NTP 서버 여러 개(DDIA 8장 "Weak forms of lying"). 체크섬은 [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md).

## 핵심 문장

- 시스템 모델은 시간 가정(동기·부분 동기·비동기)과 고장 가정(crash-stop·crash-recovery·비잔틴)의 조합이다. 실제 시스템에는 부분 동기 + crash-recovery가 대체로 가장 맞다.
- 비동기 모델에서는 느린 노드와 죽은 노드를 원리적으로 구분할 수 없다.
- 좋은 분산 알고리즘은 안전성을 시간에 기대지 않고, 활성(진행)만 시간에 기댄다(Raft §5.6).
- 멈췄다 깨어난 노드는 자기가 멈췄었는지 모른다. 그래서 개별 노드 대신 과반이 결정하고, 옛 주인은 임기·펜싱 토큰으로 거절한다.
- 장애 탐지는 빨리 알아채기와 오판하지 않기의 교환이다. φ accrual은 그 교환점을 하트비트 분포에 맞춰 조정한다.

## 관련 주제·근거

- 선행
  - [01-why-distributed-and-fallacies](../01-why-distributed-and-fallacies/2-summary.md) — 부분 실패와 8가지 오류
- 후속
  - [03-partial-failure-and-timeouts](../03-partial-failure-and-timeouts/2-summary.md) — 결과를 모르는 상태, 타임아웃 고르기
  - [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md) — 시계 가정
  - [10-leader-election](../10-leader-election/2-summary.md) · [11-consensus-raft](../11-consensus-raft/2-summary.md) · [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) — 임기·정족수·펜싱 토큰
  - [25-impossibility-results](../25-impossibility-results/2-summary.md) — FLP
  - [31-byzantine-and-blockchain](../31-byzantine-and-blockchain/2-summary.md) — 비잔틴 고장 모델의 합의
  - reliability `01-fault-error-failure-availability` — [reliability/README](../../reliability/README.md), 기존 원고 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md)
- 연결
  - [ops-patterns/12-leader-election](../../ops-patterns/12-leader-election/2-summary.md) · [ops-patterns/11-distributed-lock](../../ops-patterns/11-distributed-lock/2-summary.md) — 리더 선출·분산 락 기존 노트
  - [os/06-signals](../../os/06-signals/2-summary.md) — `SIGSTOP`·`SIGCONT`
  - [os/12-swapping-and-page-replacement](../../os/12-swapping-and-page-replacement/2-summary.md) — 스왑이 만드는 멈춤
- 근거
  - DDIA 1판 8장 "Unreliable Networks"(장애 탐지·타임아웃·φ accrual), "Process Pauses", "Knowledge, Truth, and Lies"(과반·펜싱 토큰·비잔틴 3분의 2), "System Model and Reality"(시간·고장 모델, 안전성·활성, 기억 상실)
  - Dwork, Lynch, Stockmeyer, "Consensus in the Presence of Partial Synchrony", JACM 35(2), 1988
  - Fischer, Lynch, Paterson, "Impossibility of Distributed Consensus with One Faulty Process", JACM 32(2), 1985 <https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf>
  - Ongaro, Ousterhout, "In Search of an Understandable Consensus Algorithm", 2014 — 그림 2(영속 상태), §5.6 Timing and availability <https://raft.github.io/raft.pdf>
  - Lamport, "Paxos Made Simple", 2001 — §2.4 Progress <https://lamport.azurewebsites.net/pubs/paxos-simple.pdf>
  - Hayashibara 외, "The φ Accrual Failure Detector", JAIST IS-RR-2004-010, 2004
  - Akka 소스 `akka-remote/src/main/scala/akka/remote/PhiAccrualFailureDetector.scala`, `akka-cluster/src/main/resources/reference.conf`(main 브랜치, 2026-10-01 확인)
  - Apache Cassandra `conf/cassandra.yaml`(trunk) — `phi_convict_threshold: 8` 주석
  - etcd v3.6 문서 "Tuning"(하트비트 100 ms·선거 1000 ms, RTT 10배, 디스크), "Runtime reconfiguration"(고장 멤버 교체) <https://etcd.io/docs/v3.6/>
  - Docker 문서 `docker container pause`(freezer cgroup) <https://docs.docker.com/reference/cli/docker/container/pause/>
- 실험 목록
  - `pause.sh` — etcd 3.6.5 3노드 전용 컨테이너(`sn-dw-w01-etcd1~3`, 네트워크 `sn-dw-w01-net`)에서 리더를 `docker pause` 약 4초 → 재선출 시각·임기·옛 리더 강등 로그, 실험 뒤 `/metrics`의 리더 교체 횟수. 실험 후 컨테이너·네트워크 삭제.
  - `PhiAccrual.java` — Akka 근사식을 옮긴 φ 탐지기 vs 고정 1.5초 타임아웃, GC 멈춤 2.5초·크래시·간격 흔들림(σ 50·300·500 ms) 시뮬레이션. Temurin 21.0.12.
  - 제거된 멤버 재시작 — etcd 3.6.5 3노드 전용 컨테이너(`sn-dw-wcons-e1~3`, 네트워크 `sn-dw-wcons-net`)에서 e3를 `docker stop` → `etcdctl member remove` → `docker start` → `docker logs`(장애 3). 정합 점검 때 추가, 실험 후 컨테이너·네트워크 삭제.
