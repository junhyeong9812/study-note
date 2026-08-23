# cs/striping — Striping: 하나의 ledger를 여러 Bookie에 담자 (BookKeeper) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다.
> 원고는 내가 직접 쓴 `db-engine-lab/docs/study/Striping.md`(2026-08-20)다. 본문 1~6절은 원고 그대로(소제목 번호·문단 배치만 정리, 오탈자만 교정).
> 「전체 흐름」「핵심 문장」은 원고를 압축한 것이고, 맨 아래 「[Claude 추가]」 절만 원고에 없던 내용이다. Kafka 쪽 전제는 [kafka-why-fast](../kafka-why-fast/)를 본다.

## 전체 흐름

```text
Kafka의 제약   한 파티션 = 한 리더 디스크. 복제본은 전량 사본이라 쓰기를 나눠 갖지 않는다 → 파티션 처리량 상한 = 디스크 1대
발상           한 줄기 데이터를 조각내 여러 디스크에 나눠 쓰자 (RAID 0과 같은 아이디어)
제어           E(ensemble) ≥ Qw(write quorum) ≥ Qa(ack quorum) — 복제·분산·정족수를 숫자 셋으로 동시에 얻는다
구조적 차이    리더가 없다. 클라이언트가 Qw개 Bookie에 직접 병렬 전송, 순서는 entry ID + 단일 writer 규칙으로 보장
내부           Journal(쓰기, fsync) / Ledger(읽기) 디스크 분리 → 읽기가 쓰기를 방해하지 않는다
대가           Broker + BookKeeper + ZooKeeper 운영 복잡도, Bookie당 디스크 2개 이상
```

## 1. Kafka의 한계 — 한 파티션 = 한 디스크

```text
Partition 0 의 리더 = Broker 1
  Producer ──> Broker 1 ── [디스크 1개]   ← 이 파티션의 처리량 상한 = 이 디스크 한 대
```

Broker 2, 3에 복사본이 있긴 하지만 똑같은 데이터 사본이다. 쓰기를 나눠 갖는 게 아니라 각자 전량을 다 쓴다. 더 빠르게 하려면 파티션을 늘리는 수밖에 없다.

## 2. Striping의 발상

```text
메시지: m1 m2 m3 m4 m5 m6

Kafka (복제)                BookKeeper (striping)
  Broker1: m1 m2 m3 m4        Bookie1: m1    m4
  Broker2: m1 m2 m3 m4        Bookie2: m2    m5
  Broker3: m1 m2 m3 m4        Bookie3: m3    m6
  처리량 = 디스크 1개분        처리량 = 디스크 3개분
```

용어: **Ledger** = append-only 로그 하나(Kafka의 파티션에 해당) · **Bookie** = 저장 노드(브로커에 해당) · **Entry** = 레코드 하나.

## 3. 세 개의 숫자 — E, Qw, Qa

```text
E  (Ensemble)  이 ledger에 참여하는 Bookie 총 인원
Qw (Write)     entry 하나를 실제로 몇 개에 복제할지
Qa (Ack)       몇 개에게서 응답받으면 성공 처리할지
항상 E ≥ Qw ≥ Qa
```

E=5, Qw=3, Qa=2:

```text
Bookie:     B1  B2  B3  B4  B5
entry 1 →   ●   ●   ●
entry 2 →       ●   ●   ●
entry 3 →           ●   ●   ●
entry 4 →   ●           ●   ●
entry 5 →   ●   ●           ●        ← 한 칸씩 밀며 순환
```

- 각 entry는 3벌 → 2대까지 죽어도 안전 (**복제**)
- 5대 전부가 일을 나눠 함 → 쓰기 부하가 5대에 분산 (**striping**)
- 2대만 응답하면 즉시 성공 → 느린 한 대가 전체를 붙잡지 않는다 (**straggler 회피** → [straggler](../straggler/))

Kafka의 `acks=all`은 ISR 전원을 기다리므로 가장 느린 팔로워가 전체 속도를 결정한다. Qa는 "빠른 다수만 기다린다"는 정족수(quorum) 방식이라 지연 시간의 꼬리가 짧다.

## 4. 리더가 없다

```text
Kafka        Producer → [Leader] → Follower들이 fetch.   리더 죽음 → 선출 절차 → 그동안 해당 파티션 중단
BookKeeper   Client가 Qw개 Bookie에 직접 병렬 전송. Bookie는 서로를 모름, 조율은 클라이언트가.   Bookie 죽음 → 그 자리만 교체하고 계속
```

순서 보장은 리더가 아니라 **entry ID**와 **"하나의 ledger에는 오직 한 명의 writer만 존재한다"**는 규칙으로 이뤄진다.

Bookie 사망 대응이 특히 가볍다: E=5 중 B3 사망 → 그 시점 이후 entry부터 B6를 대신 투입(ensemble change) → 이미 쓴 데이터는 그대로 두고 백그라운드에서 복제본 수 복구 → 서비스 중단 없음. Kafka는 브로커를 늘리면 파티션 데이터를 통째로 물리적으로 옮겨야 하지만(수 TB), BookKeeper는 새 데이터부터 새 Bookie를 쓰면 된다.

## 5. Bookie 내부의 디스크 분리

```text
      쓰기 요청
    ┌────┴────┐
    ↓         ↓
[Journal]  [Memtable] ──(비동기)──> [Ledger 디스크]
 순수 append만                          ↑ 읽기는 여기서
 → 여기서 fsync하고 즉시 ack
```

- Journal 디스크: 쓰기만. 순수 순차 append. **fsync 후 ack**하므로 전원 차단에도 유실 없음.
- Ledger 디스크: 읽기 담당. 백그라운드로 정리해서 기록.

효과: **읽기가 쓰기를 방해하지 않는다.** Kafka는 컨슈머가 한참 뒤처지면 그 랜덤 읽기가 디스크를 점유해 쓰기 지연까지 튄다. BookKeeper는 물리 디스크가 분리돼 이 간섭이 없다. 또 Kafka는 페이지 캐시를 믿고 fsync를 생략(복제로 보완)하지만, BookKeeper는 저널에 fsync를 해도 순차 append 전용 디스크라 감당이 된다 — 내구성 보장이 더 강하다.

## 6. 비교와 결론

```text
                  Kafka                      BookKeeper
파티션당 처리량    디스크 1대                  디스크 E대
확장              데이터 물리 이동 필요        새 데이터부터 새 노드 사용
지연 꼬리         가장 느린 replica에 좌우     Qa 정족수로 회피
읽기/쓰기 간섭    있다                        디스크 분리로 없음
내구성            복제에 의존                 저널 fsync + 복제
복잡도            브로커만                    Broker + Bookie + ZK
디스크 대수       적음                        Bookie당 2개 이상
생태계            압도적                      상대적으로 작음
```

BookKeeper가 기술적으로 더 정교하지만 Kafka가 여전히 지배적인 건, 대부분의 경우 "파티션을 늘리면 해결되는 문제"이고 운영 복잡도가 그 대가보다 크기 때문이다.

## 핵심 문장

- Kafka의 복제는 전량 사본이라 쓰기를 나누지 않는다 — 한 파티션의 상한은 디스크 한 대다.
- Striping은 RAID 0의 발상이고, E ≥ Qw ≥ Qa 세 숫자로 복제·분산·정족수를 한 번에 얻는다.
- 리더가 없으면 순서는 누가 보장하나 — entry ID + 단일 writer.
- Journal/Ledger 디스크 분리는 "읽기가 쓰기를 방해하지 않는다"를 물리적으로 보장한다.
- 정교함이 채택을 결정하지 않는다 — 운영 복잡도가 대가보다 크면 단순한 쪽이 이긴다.

## 관련 자료

- 따라 친 원본 노트(직접 작성): `/home/jun/project/db-engine-lab/docs/study/Striping.md`
- 연결: [kafka-why-fast](../kafka-why-fast/) §5 · [straggler](../straggler/) (Qa가 곧 quorum 대응)

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 내용이다. 복습 대상은 1~6절이고, 이 절은 확장 읽을거리다.

### A. RAID 0과의 공통점·차이 — 처리량은 같은 발상, 내구성은 정반대

- 공통점: 한 줄기 데이터를 여러 디스크에 돌아가며 나눠 쓰면 처리량이 디스크 수만큼 늘어난다. 원고의 "처리량 = 디스크 3개분"이 바로 RAID 0의 셈법이다.
- 차이: RAID 0은 복제가 없어서 디스크 한 대가 죽으면 전체 데이터를 잃는다(내구성은 오히려 디스크 1대보다 나빠진다). BookKeeper는 striping과 복제(Qw벌)를 한 메커니즘에 같이 넣었기 때문에 "분산하면서도 죽어도 된다"가 성립한다. 즉 E로 처리량을, Qw로 내구성을 따로 조절하는 것이 RAID 0에는 없는 축이다.
- 또 RAID 0은 고정 크기 블록(stripe unit) 단위로 잘라 한 컨트롤러가 배치하고, BookKeeper는 entry 단위로 클라이언트가 배치한다 — 분산의 주체와 단위가 다르다.

### B. E / Qw / Qa 조합의 트레이드오프, 그리고 Qa < Qw일 때 fencing·recovery가 필요한 이유

- Qw를 올리면 내구성과 쓰기 증폭(디스크 부하)이 같이 오르고, Qa를 내리면 지연 꼬리는 짧아지지만 "ack된 순간 실제로 Qa벌만 안전하다"는 뜻이 된다. E > Qw면 striping 효과가, E = Qw면 단순 복제에 가까워진다(원고 §2 Kafka 방식 그림이 사실상 E = Qw = 3인 경우).
- Qa < Qw이면 writer가 죽은 시점에 "어떤 entry는 Qa벌, 어떤 entry는 Qw벌, 어떤 entry는 0~1벌"처럼 복제 상태가 들쭉날쭉하게 남는다. 그래서 ledger를 닫는 쪽(recovery)이 먼저 모든 Bookie에 **fencing**(이 ledger에 더 이상 쓰기를 받지 말라)을 걸어 옛 writer의 늦은 쓰기를 차단하고, Bookie들을 읽어 "Qa 정족수에 도달한 마지막 entry"까지를 확정 지점으로 닫는다. 단일 writer 규칙(§4)이 장애 시에도 유지되게 만드는 장치다.
- 읽기 쪽에서는 **LAC(Last Add Confirmed)** — writer가 ack 받은 마지막 entry ID — 까지만 읽도록 해서, 아직 정족수에 못 미친 entry를 독자가 보지 못하게 한다. Qa가 Qw의 과반이어야 하는지 등 정족수 간 교집합 조건은 버전별 기본값이 달라 (확인 필요).

### C. ensemble change — "그 자리만 교체"가 실제로 어떻게 기록되나

- ledger의 메타데이터(ZooKeeper 등 메타 저장소)에는 "entry N부터는 이 Bookie 집합"이라는 **fragment 목록**이 쌓인다. Bookie 장애 시 writer가 새 Bookie를 뽑아 새 fragment를 메타데이터에 추가하기만 하면 되므로, 원고 §4의 "이미 쓴 데이터는 그대로"가 성립한다.
- 빠진 복제본은 별도 프로세스(auditor가 under-replicated ledger를 찾고 replication worker가 복사)가 백그라운드에서 채운다 — Kafka의 파티션 재할당처럼 전량을 옮기는 게 아니라 모자란 fragment만 옮긴다.
- 대신 읽는 쪽은 entry ID → fragment → Bookie 집합을 메타데이터로 찾아가야 하므로, ledger가 잘게 쪼개질수록 메타데이터가 커진다. 그래서 Pulsar는 ledger를 주기적으로 rollover해 크기를 제한한다.

### D. Pulsar — BookKeeper 위에서 broker를 stateless로 만든 구조

- Pulsar 토픽의 데이터는 broker가 아니라 BookKeeper의 ledger 묶음(managed ledger)에 있다. broker는 "현재 이 토픽을 서빙하는 담당자"일 뿐 디스크를 갖지 않으므로, broker가 죽거나 추가돼도 데이터 이동 없이 토픽 소유권만 다른 broker로 넘기면 된다.
- 이것이 원고 §6 "확장: 새 데이터부터 새 노드 사용"의 실제 운영 효과다 — 서빙 계층(broker)과 저장 계층(bookie)을 따로 늘릴 수 있다. 대가는 원고가 말한 대로 구성요소가 셋(broker·bookie·메타 저장소)이라는 점.

### E. Kafka의 대응 — Tiered Storage(KIP-405), 그리고 무엇은 해결되지 않나

- KIP-405 Tiered Storage는 오래된 세그먼트를 object storage로 내려보내 broker 로컬 디스크에는 최근 데이터만 남긴다. 원고 §6의 "확장 = 수 TB 물리 이동" 고통을 줄이는 쪽의 대응이다(옮길 로컬 데이터가 작아진다). 정식 도입 버전은 (확인 필요).
- 그러나 "한 파티션의 쓰기 상한 = 리더 디스크 1대"라는 원고 §1의 제약은 그대로다 — 쓰기는 여전히 리더 한 대가 받는다. 즉 Tiered Storage는 저장·확장 문제의 답이지 striping의 대체물이 아니다.
- 더 나아가 KRaft(ZooKeeper 제거)로 운영 복잡도를 줄이고, 최근에는 object storage에 직접 쓰는 "diskless" 계열 제안(KIP-1150 등, 확인 필요)도 논의된다 — 방향이 "리더 디스크를 없앤다"는 점에서 BookKeeper와 다른 길로 같은 제약을 푸는 시도다.
