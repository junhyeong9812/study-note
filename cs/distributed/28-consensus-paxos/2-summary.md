# distributed/28-consensus-paxos — Paxos 기본형: 제안 번호·두 단계·정족수 교집합 — 정리 (힌트)

## 해결하는 문제

여러 대가 **값 하나**에 동의해야 한다. 예: "지금 주 서버는 누구인가".\
기계가 죽고 메시지가 늦거나 사라져도, 한 번 정한 값은 바뀌면 안 된다.

```text
 주·대기 두 대 + "응답 없으면 넘어간다"의 실패 (MIT 6.5840 L4 노트의 예)
   C1 ── S1(주)      ║ 분할 ║      S2(대기) ── C2
   S1: "S2가 죽었다, 내가 계속 주"   S2: "S1이 죽었다, 내가 주"
   → 둘 다 주 서버로 쓰기를 받는다(split brain)
```

- 컴퓨터는 "상대가 죽었다"와 "네트워크가 끊겼다"를 구별하지 못한다. 보이는 것은 "응답 없음"뿐이다(L4 노트).
- *합의(consensus)*: 여러 노드가 값 하나를 정하는 것. Lamport 2001 2.1절의 안전성 조건은 셋이다.
  - 제안된 값만 선택될 수 있다.
  - 값은 하나만 선택된다.
  - 실제로 선택되지 않은 값을 "선택됐다"고 알게 되는 일은 없다.
  - MIT L4 노트는 이를 "한 번 합의하면 마음을 바꾸지 않는다"로 요약한다.
- Paxos(Lamport)는 이것을 **비잔틴이 아닌 장애**(멈춤·재시작·메시지 유실·지연·중복) 아래에서 푼다. 안전성은 타이밍과 무관하게 지키고, 진행은 "구별된 제안자 하나가 방해받지 않고 과반과 충분히 오래 통신할 수 있으면" 이룬다(2.4절, 아래 6).

쉬운 예: 동아리 회장 선출을 단체방 없이 쪽지로 한다.
- 쪽지는 늦게 오거나 안 온다. 누가 결석했는지도 모른다.
- 그래도 "과반이 같은 사람에게 서명한 회차가 있으면 그 사람이 회장, 이후 회차는 그 사람을 다시 확인만 한다"를 지키면 회장이 둘이 되지 않는다.

똑같은 구조다.\
실무 예: Raft 논문 10절은 Chubby와 Spanner가 Paxos 기반이라고 밝힌다고 적는다. 이 노트는 커리큘럼대로 **기본형(single-decree)**만 다루고, 실무의 로그 복제는 [11-consensus-raft](../11-consensus-raft/2-summary.md)로 배운다.

## 동작·원리

### 1. 세 역할

```text
 proposer(제안자) ── 값을 제안한다. 여럿일 수 있다
 acceptor(수락자) ── 제안을 받아들일지 정한다. 이들의 과반이 "선택"을 만든다
 learner(학습자)  ── 무엇이 선택됐는지 알아낸다
 실제 구현에서는 한 서버가 세 역할을 다 한다(Lamport 2001 2.5절)
```

- *선택됨(chosen)*: 같은 번호 n의 같은 값 v를 acceptor **과반**이 수락한 상태. 어느 한 서버가 혼자 알 수 있는 사실이 아니라 시스템 전체의 상태다(L4 노트: "chosen is system-wide property").

### 2. 제안 번호 — 누가 더 나중 시도인가

- 제안마다 번호 n을 붙인다. 번호는 서로 겹치지 않아야 한다. 제안자마다 **서로소인 번호 집합**에서 고른다(2.5절). 예: (라운드, 서버 ID) 쌍을 사전순으로 비교.
- 제안자는 자기가 쓴 가장 큰 번호를 디스크에 남기고, 다음엔 그보다 큰 번호로 시작한다(2.5절).

### 3. 두 단계

```text
 Proposer                       Acceptor들 (상태: np = 약속한 최대 번호, na/va = 수락한 최대 제안)
   │ 1a prepare(n) ───────────────> n > np 이면: np = n,  promise(n, na, va) 응답
   │ <─────────────── 1b promise      아니면 무시(또는 거절)
   │
   │  과반의 promise를 모으면 값 결정:
   │    promise 중 na가 가장 큰 것의 va  ← 이미 수락된 값이 있으면 그것을 이어받는다
   │    아무도 수락한 게 없으면 내 값
   │
   │ 2a accept(n, v) ─────────────> n >= np 이면: np = na = n, va = v,  accepted 응답
   │ <─────────────── 2b accepted     아니면 거절
   │
   │  과반이 accepted → v가 선택됨 → learner에게 알림
```

- 1단계의 promise는 두 가지 약속이다(Lamport 2001 2.2절).
  - "n보다 작은 번호의 제안은 앞으로 수락하지 않는다."
  - "내가 지금까지 수락한 것 중 번호가 가장 큰 제안은 이것이다."
- acceptor는 np·na·va를 **응답하기 전에 디스크에 남긴다**(2.5절). 재시작 뒤 잊으면 안전성이 깨진다(아래 실험 4).

### 4. 왜 안전한가 — 정족수 교집합

```text
 n=1에서 X가 선택된 과반   {S1, S3}
 n=2의 prepare를 받은 과반      {S2, S3}
                                   ^^ 겹치는 S3가 (1, X)를 promise에 실어 보낸다
 → n=2의 제안자는 자기 값 Y 대신 X를 제안해야 한다
```

- 과반 둘은 한 대 이상 겹친다. 그래서 이미 선택된 값이 있으면, 이후 번호의 1단계 과반 안에 그것을 수락한 acceptor가 적어도 하나 있다.
- 논문의 불변식 **P2c**: 번호 n·값 v의 제안이 나가면, 어떤 과반 S가 있어 (a) S의 누구도 n보다 작은 제안을 수락하지 않았거나 (b) S가 수락한 n 미만 제안 중 가장 큰 번호의 값이 v다. 1단계가 이 조건을 확인하는 절차다.
- "na가 **가장 큰** promise의 값"이어야 하는 이유(L4 노트): n=12의 제안자가 (10, A)와 (11, B)를 둘 다 보았다면 B를 골라야 한다. n=11이 이미 과반을 얻었을 수 있기 때문이다.

### 5. 실험: 규칙을 하나씩 빼면 정말 두 값이 선택되나

acceptor 3대, 메시지 도착 순서를 손으로 지정하는 Java 시뮬레이션이다. 표기는 L4 노트를 따른다(`p5` = prepare(5) 수신, `a5X` = accept(5, X) 수락, `x10X` = 거절).

(실험, Java 21 `PaxosSim.java`, 2026-10-01)

```text
== 1. 정상 규칙: S1이 X를 과반에 받게 하고 죽음 → S2가 Y로 n=2 시작
  S1: p1                a1X
  S2:       p1                      p2          a2X
  S3:             p1          a1X         p2          a2X
  선택된 (값, 번호): [X(n=1), X(n=2)]  → 안전
== 2. 결함: phase 2에서 약속에 실려 온 va를 무시하고 자기 값을 냄
  S1: p1                a1X
  S2:       p1                      p2          a2Y
  S3:             p1          a1X         p2          a2Y
  선택된 (값, 번호): [X(n=1), Y(n=2)]  → 안전성 위반! 서로 다른 값이 선택됨
== 3. 결함: accept가 n >= np를 검사하지 않음
  S1: p1                p2                a1A
  S2:       p1                p2                a1A   a2B
  S3:             p1                p2                      a2B
  선택된 (값, 번호): [A(n=1), B(n=2)]  → 안전성 위반! 서로 다른 값이 선택됨
== 4. 결함: S2가 재부팅하며 np를 디스크에 안 남김
  S1: p10                           a10X
  S2:       p10   p11         boot        a10X  a11Y
  S3:                   p11                           a11Y
  선택된 (값, 번호): [X(n=10), Y(n=11)]  → 안전성 위반! 서로 다른 값이 선택됨
== 4'. 같은 순서, np를 디스크에 남김(정상)
  S1: p10                           a10X
  S2:       p10   p11         boot        x10X  a11Y
  S3:                   p11                           a11Y
  선택된 (값, 번호): [Y(n=11)]  → 안전
```

- 관찰 1 — 정상 규칙에서는 S2가 Y를 원했는데도 S3의 promise에 실린 (1, X)를 이어받아 X를 다시 제안했다. 선택된 값은 X 하나다.
- 관찰 2 — 그 규칙을 빼자 n=1에서 X, n=2에서 Y가 각각 과반을 얻었다.
- 관찰 3 — accept에서 번호 검사를 빼면, 이미 n=2를 약속한 S1·S2가 n=1의 A를 수락해 A가 선택되고, 이어 B도 선택된다. L4 노트의 "for a while A was chosen, then changed to B".
- 관찰 4 — 재부팅에서 np만 잃어도 깨진다. 정상이면 S2는 a10X를 거절(`x10X`)하고 Y만 선택된다. 시뮬레이션은 결함을 "np만 잃음"으로 단순화했다.

### 6. 진행은 보장되지 않는다 — 결투하는 제안자

```text
 p: prepare(1) 완료 → q: prepare(2) 완료 → p의 accept(1) 거절 → p: prepare(3) 완료 → q의 accept(2) 거절 → …
```

(실험, 같은 시뮬레이션의 5번 — 출력 폭이 넓어 앞 110자만 `cut -c1-110`으로 보였다)

```text
== 5. 결투(dueling proposers) 3바퀴 — 선택된 값 없음(진행 없음, 안전성은 유지)
  S1: p1                p2                x1P               p3                x2Q               p4            
  S2:       p1                p2                x1P               p3                x2Q               p4      
  S3:             p1                p2                x1P               p3                x2Q               p4
  선택된 (값, 번호): []  → 안전
```

- 서로의 2단계를 1단계로 계속 무효로 만든다. 아무 값도 선택되지 않지만 두 값이 선택되지도 않는다.
- 논문 2.4절: 진행을 위해 **구별된 제안자(distinguished proposer, 사실상 리더)** 하나만 제안하게 한다. 그 리더를 믿을 만하게 뽑으려면 무작위나 실시간(타임아웃)이 필요하다 — FLP 불가능성의 귀결이다([25-impossibility-results](../25-impossibility-results/2-summary.md)). 안전성은 리더 선출이 성공하든 실패하든 유지된다.

### 7. 기본형에서 로그로 — Multi-Paxos (개요)

- 복제 상태 기계의 i번째 명령 = Paxos 인스턴스 i가 고른 값(Lamport 2001 3절).
- 리더 하나가 모든 인스턴스의 1단계를 한꺼번에 해 두면, 평소에는 명령마다 2단계만 돈다.
- 새 리더가 빈칸(예: 136·137번 미정)을 발견하면 no-op 명령으로 채워 뒤 명령을 실행할 수 있게 한다(3절). 단, 1단계 결과 제안할 값에 제약이 없는 칸에만 그렇다. 이미 수락된 값이 보고된 칸은 그 값을 제안해야 한다(논문 예의 135·140번).
- Raft는 이 구조를 리더·term·로그 일관성 규칙으로 더 구체화한 것으로 볼 수 있다.

| | Paxos 기본형(Lamport 2001) | Raft(2014) |
|---|---|---|
| 정하는 것 | 값 하나 | 로그 전체(연속된 칸) |
| 순서 번호 | 제안 번호 n | term |
| 1단계 | prepare/promise — 이전 수락값을 모아 이어받음 | 선거(RequestVote) — 투표자마다 "후보 로그가 내 것만큼 최신인가"를 검사, 과반 표를 얻은 후보는 커밋된 항목을 모두 가짐(§5.4.1) → 이어받을 필요를 줄임 |
| 2단계 | accept/accepted | AppendEntries |
| 리더 | 진행을 위한 선택 사항 | 필수 |
| 안전성의 뿌리 | 정족수 교집합 | 정족수 교집합 |

### 8. 실험: 정족수 크기와 교집합

5대에서 크기 k의 정족수 두 개를 모두 짝지어 서로소(겹치지 않음)인 쌍을 셌다.

(실험, `PaxosSim.java` 6번)

```text
== 6. N=5, 정족수 크기 2: 정족수 10개, 쌍 45개 중 서로소 15개
== 6. N=5, 정족수 크기 3: 정족수 10개, 쌍 45개 중 서로소 0개
```

- 과반(3)이면 서로소인 쌍이 0이다. 2로 줄이면 45쌍 중 15쌍이 겹치지 않아, 서로 모르는 두 무리가 각자 값을 정할 수 있다.
- 그래서 2f+1대는 f대 장애까지 견딘다(L4 노트). 과반은 "살아 있는 노드"가 아니라 **전체 노드**의 과반이다.

## 쓰이는 자료구조·알고리즘

- **제안 번호** — (라운드, 서버 ID)의 사전순 비교. 제안자별로 서로소인 번호 공간.
- **acceptor 영속 상태** — np(약속한 최대 번호), na·va(수락한 최대 제안). 응답 전에 fsync. DB의 WAL과 같은 재료 — [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md).
- **정족수 시스템** — 과반은 교집합이 보장되는 가장 단순한 정족수다. 논문은 과반의 일반화가 있다고 적는다(2.2절 "There is an obvious generalization of a majority").
- **두 단계 프로토콜** — 읽기(1단계: 과거 수락값 수집) → 쓰기(2단계: 수락 요청). 2PC와 이름은 비슷하지만 다르다. 2PC는 참가자 **전원**의 동의가 필요하고 코디네이터가 멈추면 막힌다. Paxos는 **과반**으로 진행한다([14번](../14-two-phase-commit/2-summary.md)).
- **인스턴스의 배열(로그)** — Multi-Paxos. 값에 제약이 없는 빈칸은 no-op으로 채운다.

## 적용 — 풀어나가는 법

### 1. 직접 구현하지 않는다

- 실무는 합의 라이브러리·저장소(etcd·ZooKeeper·Consul 등)를 쓴다. Paxos를 배우는 목적은 **정족수 교집합과 "이미 정해졌을 수 있으면 정해진 것처럼 행동한다"**라는 설계 원리를 읽어 내는 것이다(L4 노트: "if there's evidence that agreement *might* have been reached already, must act as if it had been").

### 2. 원리를 코드에서 알아보기 (Java)

```java
/** 제안 번호: 라운드가 같으면 서버 ID로 가른다 → 제안자끼리 번호가 겹치지 않는다 */
record Ballot(long round, int serverId) implements Comparable<Ballot> {
    public int compareTo(Ballot o) {
        int c = Long.compare(round, o.round);
        return c != 0 ? c : Integer.compare(serverId, o.serverId);
    }
    Ballot next() { return new Ballot(round + 1, serverId); }
}

/** acceptor: 상태를 디스크에 남긴 뒤에만 응답한다 */
final class Acceptor {
    private Ballot promised, acceptedBallot;   // np, na
    private String acceptedValue;              // va
    private final DurableStore disk;           // 설명용 — fsync까지 해 주는 저장소

    Acceptor(DurableStore disk) { this.disk = disk; }

    synchronized Optional<Promise> prepare(Ballot n) {
        if (promised != null && n.compareTo(promised) <= 0) return Optional.empty();
        promised = n;
        disk.save(promised, acceptedBallot, acceptedValue);      // 응답 전에 남긴다
        return Optional.of(new Promise(n, acceptedBallot, acceptedValue));
    }

    synchronized boolean accept(Ballot n, String v) {
        if (promised != null && n.compareTo(promised) < 0) return false;   // n >= np 검사
        promised = n; acceptedBallot = n; acceptedValue = v;
        disk.save(promised, acceptedBallot, acceptedValue);
        return true;
    }
}
```

- `DurableStore`·`Promise`는 설명용 이름이다.
- 시뮬레이션의 결함 3·4가 이 코드의 `n >= np` 검사와 `disk.save` 줄을 각각 뺀 경우다.

### 3. 다른 시스템을 읽을 때의 질문

1. 순서 번호(제안 번호·term·epoch)는 무엇이고 어디에 영속하나?
2. 결정에 필요한 정족수는 몇이고, 두 정족수가 겹치나?
3. 새 리더(제안자)는 이전에 수락된 값을 어떻게 이어받나?
4. 진행을 위해 무엇에 시간(타임아웃)을 쓰나? 안전성도 시간에 기대나?

## 장애 시나리오와 대처

커리큘럼은 이 주제의 ⚠ 칸을 "이해 난도 — Raft로 대체 학습"으로 둔다. 아래는 Paxos 계열 구현·설계에서 생기는 장애다.

### 1. 결투하는 제안자 → 진행 없음(livelock)

- 현상: 합의 요청이 끝나지 않고 재시도만 반복한다.
- 보이는 형태: 제안 번호가 빠르게 커지는데 선택된 값이 없다. 2단계 거절(더 큰 번호를 이미 약속함) 로그가 양쪽 제안자에서 번갈아 나온다. 위 실험 5와 같은 모양이다.
- 원인: 두 제안자가 서로의 2단계를 1단계로 무효화한다(논문 2.4절).
- 대처: 리더(구별된 제안자) 하나만 제안하게 한다. 리더 선출에 무작위 백오프·타임아웃을 쓴다.

### 2. acceptor가 상태를 잃은 채 복귀

- 현상: 디스크 교체·데이터 디렉터리 초기화 뒤 같은 ID로 돌아온 노드가 있는 클러스터에서 두 값이 선택된 흔적이 나온다.
- 보이는 형태: 같은 인스턴스에 대해 서로 다른 값을 적용한 복제본. 위 실험 4처럼 np를 잃은 노드가 더 작은 번호의 accept를 받아들인다.
- 원인: 안전성은 acceptor가 np·na·va를 기억한다는 가정 위에 있다. 교집합의 유일한 증인이 그 노드일 수 있다(L4 노트: "if lost, do not re-join!").
- 대처: 응답 전 fsync. 상태를 잃은 노드는 같은 멤버로 재가입시키지 않고 새 멤버로 넣는다.

### 3. 제안 번호가 겹친다

- 현상: 두 제안자가 같은 번호로 서로 다른 값을 제안한다.
- 보이는 형태: 같은 번호의 서로 다른 accept 요청이 로그에 있다. 시계 기반으로 번호를 만든 구현에서 두 서버의 시각이 같을 때 생긴다.
- 원인: 안전성 논증은 번호가 제안마다 유일하다고 가정한다(Lamport 2001 2.2절 "assuming unique proposal numbers").
- 대처: (라운드, 서버 ID)처럼 서로소 번호 공간을 쓴다. 쓴 최대 번호를 영속한다.

### 4. 값은 선택됐는데 아무도 모른다

- 현상: 클라이언트가 타임아웃을 받았는데, 나중에 보니 그 값이 선택돼 있었다.
- 보이는 형태: 요청은 실패로 기록됐지만 상태에 반영돼 있다.
- 원인: 선택은 acceptor 과반의 상태다. accepted 메시지가 learner에 도착하기 전에 유실될 수 있다(2.3절 "a value could be chosen with no learner ever finding out").
- 대처: learner가 acceptor에게 묻는다. acceptor 장애로 과반 수락 여부를 판별 못 하면, 제안자가 제안을 한 번 더 돌려 새 제안이 선택될 때 확인한다(같은 절). 클라이언트는 타임아웃을 "결과 모름"으로 다루고 멱등하게 재시도한다.

### 5. 과반을 못 모으는 분할

- 현상: 분할 중 소수 쪽 요청이 전부 멈춘다.
- 보이는 형태: prepare가 과반 promise를 못 모아 계속 재시도한다.
- 원인: 의도된 동작이다. 과반이 없으면 진행하지 않아 split brain을 막는다(L4 노트 "no majority -> cannot proceed").
- 대처: 홀수 대수와 장애 도메인 분산. 분할이 풀리면 과거 상태를 이어받아 정상 진행한다.

## 핵심 문장

- Paxos는 값 하나를 정하는 합의다. 선택됨 = 같은 번호의 같은 값을 acceptor 과반이 수락한 상태다.
- 1단계(prepare/promise)는 과거에 수락된 값을 모으는 읽기이고, 2단계(accept)는 그 값을 이어받아 쓰는 단계다.
- 과반 둘은 한 대 이상 겹치므로, 이미 선택된 값은 다음 과반 안의 누군가가 알려 준다. 5대에서 정족수 3이면 서로소 쌍이 0, 2면 45쌍 중 15쌍이었다.
- "가장 큰 na의 값 이어받기", "accept에서 n ≥ np 검사", "상태 영속" 중 하나만 빼도 시뮬레이션에서 두 값이 선택됐다.
- 안전성은 타이밍과 무관하지만 진행은 아니다. 제안자가 둘이면 서로를 끝없이 무효로 만들 수 있어, 리더 하나를 무작위·타임아웃으로 뽑는다.

## 관련 주제·근거

- 선행
  - [10-leader-election](../10-leader-election/2-summary.md) — 과반·임기, split brain
- 후속·연결
  - [11-consensus-raft](../11-consensus-raft/2-summary.md) — 같은 뿌리의 로그 합의(실무 학습 경로)
  - [31-byzantine-and-blockchain](../31-byzantine-and-blockchain/2-summary.md) — 거짓말하는 노드가 있으면 과반 대신 2f+1/3f+1
  - [14-two-phase-commit](../14-two-phase-commit/2-summary.md)(전원 동의 vs 과반)
  - [25-impossibility-results](../25-impossibility-results/2-summary.md)(FLP)
  - [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md) — 파티션별 합의
- 논문·강의
  - Lamport, "Paxos Made Simple", ACM SIGACT News 2001 — 2.1 문제, 2.2 P1·P2·P2a·P2b·P2c와 두 단계, 2.3 학습, 2.4 진행(결투·구별된 제안자·FLP), 2.5 구현(영속·서로소 번호), 3 상태 기계(Multi-Paxos·no-op) <https://lamport.azurewebsites.net/pubs/paxos-simple.pdf>
  - MIT 6.5840 Spring 2026 L4 "Fault-Tolerant Agreement, Paxos" 노트(의사 코드, 숙제 예시, n ≥ np 검사·np 영속이 필요한 반례) <https://pdos.csail.mit.edu/6.824/notes/l-paxos.txt>, 일정 <https://pdos.csail.mit.edu/6.824/schedule.html>
  - Ongaro & Ousterhout 2014 10절 Related work(Chubby·Spanner가 Paxos 기반이라고 밝힘) <https://raft.github.io/raft.pdf>
  - Kleppmann 『DDIA』 1판 9장 "Fault-Tolerant Consensus"
- 실험 목록
  - F `PaxosSim.java`(Java 21): 정상 규칙 vs 결함 3종(va 무시·n ≥ np 검사 없음·np 미영속)에서 선택된 값, 결투하는 제안자 3바퀴, N=5 정족수 크기 2·3의 서로소 쌍 수
