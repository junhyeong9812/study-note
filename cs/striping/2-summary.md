# cs/striping — Striping: 하나의 ledger를 여러 Bookie에 담자 (BookKeeper) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다.
> 원고는 내가 직접 쓴 `Striping.md`를 골격만 다듬은 것이다(2026-08-20). Kafka 쪽 전제는 [kafka-why-fast](../kafka-why-fast/)를 본다.

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
