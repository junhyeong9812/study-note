# cs/lsm-tree — LSM-Tree와 RUM Conjecture — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 원고는 내가 직접 쓴 `db-engine-lab/docs/study/LSM-Tree.md`(2026-08-20). 1~6절은 원고 그대로(골격·오탈자만 다듬음).
> 「전체 흐름」「핵심 문장」은 원고를 압축한 것이고, 맨 아래 「[Claude 추가]」 절만 원고에 없던 내용이다. 본문 중 원고에 없던 문장은 ` *(Claude 보강)*`으로 표시했다.

## 전체 흐름

```text
문제   인덱스는 정렬돼야 검색이 빠른데, 정렬을 유지하려면 중간에 끼워넣어야 하고, 끼워넣으면 랜덤 쓰기가 된다
답     "정렬을 나중으로 미루자" — 랜덤 쓰기를 메모리(MemTable)에 흡수하고, 디스크에는 정렬된 불변 파일(SSTable)을 순차로만 내려보낸다
대가   읽기 — 같은 key가 여러 SSTable에 흩어짐(read amplification). Bloom filter·sparse index·compaction으로 갚는다
틀     RUM — Read/Update/Memory 중 둘을 좋게 하면 하나는 나빠진다. 쓰기 많으면 LSM, 읽기 중심이면 B-Tree
```

## 1. 해결하려는 문제

DB의 고민은 이거다. 인덱스는 정렬되어 있어야 검색이 빠른데, 정렬을 유지하려면 중간에 끼워넣어야 하고, 중간에 끼워넣으면 랜덤 쓰기가 된다.

B-Tree에 새 데이터를 삽입하면: 트리를 타고 내려가 위치를 찾고(랜덤 읽기) → 그 페이지를 고쳐서 다시 쓰고(랜덤 쓰기) → 페이지가 꽉 찼으면 분할 → 부모도 수정 → 연쇄 랜덤 쓰기. 정렬을 **즉시** 유지하려는 비용이다. LSM-Tree의 답은 정렬을 나중으로 미루는 것이다.

## 2. 기본 구조와 쓰기 경로

```text
메모리   MemTable (정렬된 자료구조)        ← 여기에 먼저 쓴다
            │ 꽉 차면 통째로 flush (순차 쓰기)
디스크   SSTable (정렬된 불변 파일)        ← 한 번 쓰면 절대 수정 안 함
         SSTable
         SSTable ...
```

1. WAL에 append — 장애 대비 로그, 순차 쓰기
2. MemTable에 삽입 — 메모리라서 정렬 유지가 저렴
3. MemTable이 꽉 차면 이미 정렬된 상태 그대로 파일로 쏟아낸다 — 완전한 순차 쓰기
4. 그 파일(SSTable)은 불변, 이후 절대 고치지 않음

**핵심: 랜덤 쓰기를 메모리에 흡수하고, 디스크에는 순차 쓰기만 내려보낸다.**

수정과 삭제도 쓰기다. `id=42를 "B"로 수정` → 기존 것 안 고치고 새로 (42,"B")를 쓴다. `id=42 삭제` → (42, tombstone)이라는 삭제 표시를 쓴다. 읽을 때 최신 것을 우선하면 된다. append-only + 불변이라는 점에서 SSD의 FTL과 정확히 같은 발상이다(→ nand-flash).

## 3. 읽기와 그 대가

쓰기가 편해진 대가는 읽기가 치른다. 같은 key가 여러 SSTable에 흩어져 있을 수 있다.

```text
"id=42 줘" → MemTable → SSTable-1(최신) → SSTable-2 → SSTable-3 ...   ← 최악엔 전부 뒤짐 (read amplification)
```

보조 장치:

- **Bloom Filter** — "이 SSTable에 key 42가 확실히 없다"를 메모리에서 즉답. 없는 파일은 아예 안 읽는다. (있다고 답하면 실제로 있을 수도, 없을 수도 있다 — false positive만 허용) *(Claude 보강)*
- **Sparse Index** — SSTable 안의 대략적 위치를 찾아주는 색인
- **SSTable 내부 정렬** — 이진 탐색 가능, 범위 스캔도 순차 읽기

## 4. Compaction — LSM의 GC

SSTable이 계속 쌓이면 읽기가 느려지고 공간도 낭비된다. 여러 SSTable을 병합 정렬해 하나로 합치는 작업을 백그라운드로 돌린다.

```text
SSTable-1: (1,A) (5,X) (9,C)
SSTable-2: (5,Y) (7,D)                ← 5가 중복, 2가 최신
        ↓ compaction
새 SSTable: (1,A) (5,Y) (7,D) (9,C)    ← 옛 5는 버림, tombstone도 여기서 실제 삭제
```

이미 정렬된 파일들을 순차로 읽어 순차로 쓰는 작업이라 compaction도 순차 I/O다. 단, 호스트가 시키지 않은 쓰기라는 점에서 SSD의 GC와 같은 성격의 write amplification을 만든다. *(Claude 보강)*

```text
Leveled      레벨별로 크기를 10배씩 키우며 계층 관리 — 읽기 빠름, 공간 효율 좋음, 쓰기 증폭 큼
Size-tiered  비슷한 크기끼리 합침 — 쓰기 증폭 적음, 읽기 느림, 공간 낭비
```

## 5. RUM Conjecture

Read / Update / Memory(공간) 중 둘을 좋게 하면 하나는 나빠진다. LSM을 이해하는 가장 좋은 틀이다.

```text
             B-Tree             LSM-Tree
쓰기         랜덤, 느림          순차, 빠름
읽기(단건)   빠름(경로 하나)     여러 곳 확인 필요
공간         페이지 단편화       압축 잘 됨
배경 작업    적음               compaction 부담
```

쓰기가 많으면 LSM, 읽기 중심이면 B-Tree가 일반적인 선택이다. RocksDB, Cassandra, HBase, LevelDB, ScyllaDB, InfluxDB가 LSM 계열이다.

## 6. Kafka와 LSM-Tree의 관계

목적이 다르다.

```text
Kafka  key로 조회할 일이 없음 → offset으로 위치만 알면 됨 → 정렬도, compaction도, Bloom filter도 필요 없음 → 순수 append-only 로그
LSM    key로 조회해야 함 → 정렬 필요 → 그래서 compaction이라는 대가를 지불
```

Kafka는 LSM에서 "쓰기는 순차로"라는 부분만 취하고, key 조회라는 요구사항이 없어서 나머지 복잡도를 전부 생략한 형태다.
Kafka의 log compaction은 이름은 비슷하지만 "key별 최신 값만 남기는" 별개 기능이다.

## 핵심 문장

- LSM은 "정렬을 나중으로 미룬다" — 랜덤 쓰기를 메모리에 흡수하고 디스크엔 순차 쓰기만 보낸다.
- 수정·삭제도 쓰기다(새 레코드, tombstone). 불변 파일 + 최신 우선 읽기 = FTL과 같은 발상.
- 쓰기의 편함은 읽기가 갚는다(read amplification). Bloom filter는 "확실히 없다"만 즉답한다.
- Compaction은 LSM의 GC — 병합 정렬이라 순차 I/O이고, 옛 값과 tombstone이 여기서 실제로 사라진다.
- RUM: 셋 중 둘만 고를 수 있다. Kafka는 key 조회가 없어서 LSM의 복잡도를 전부 생략할 수 있었다(log compaction은 이름만 비슷한 별개 기능).

## 관련 자료

- 원본: 내가 직접 쓴 LSM-Tree 노트(이 파일 1~6절, 2026-08-20) — `/home/jun/project/db-engine-lab/docs/study/LSM-Tree.md`
- 연결: [nand-flash](../nand-flash/) (FTL·GC·WAF — 하드웨어에서 같은 발상) · [kafka-why-fast](../kafka-why-fast/)

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 내용이다. 복습 대상은 1~6절이고, 이 절은 확장 읽을거리다.

### A. Leveled vs Size-tiered — 증폭 세 개의 트레이드오프

- **Size-tiered(STCS)**: 비슷한 크기의 SSTable이 N개 모이면 합쳐 한 단계 큰 파일을 만든다. 한 레코드가 평생 다시 쓰이는 횟수가 적어 **write amp가 작다**. 대신 같은 key 범위가 여러 파일에 겹쳐 있어 읽을 때 뒤질 파일이 많고(read amp), 합치는 동안 입력·출력이 공존해 최악엔 디스크가 2배 필요하다(space amp).
- **Leveled(LCS)**: L0를 빼면 각 레벨 안에서는 key 범위가 겹치지 않는다. 한 key는 레벨당 파일 하나만 보면 되니 **read amp·space amp가 작다**. 대신 한 파일을 다음 레벨로 내릴 때 겹치는 파일들을 전부 다시 써야 해서 write amp가 크다(레벨 배율이 10이면 레벨당 ~10배 수준으로 흔히 설명한다).
- 정리: 읽기·공간을 사면 쓰기를 내고, 쓰기를 사면 읽기·공간을 낸다 — RUM이 compaction 전략 안에서도 그대로 반복된다.

### B. Bloom filter가 읽기 비용을 깎는 방식

- SSTable마다 그 파일의 key들을 k개 해시로 비트 배열에 찍어 둔다. 조회 시 비트가 하나라도 0이면 "확실히 없음" — 디스크를 건드리지 않는다. 전부 1이면 "있을지도" — 그때만 파일을 연다.
- 가장 큰 효과는 **없는 key 조회(point miss)** 와 "최신 값이 있는 파일 하나만 열기"에서 난다. 범위 스캔에는 도움이 안 된다(범위는 어느 파일에나 걸칠 수 있다).
- false positive 비율은 비트 수/key 수로 조절한다. key당 10비트 정도에서 ~1% 수준이 흔히 인용된다(확인 필요). 메모리(M)를 더 써서 읽기(R)를 사는 RUM 트레이드다.

### C. WAL + MemTable 복구

- MemTable은 메모리라 프로세스가 죽으면 사라진다. 그래서 MemTable에 넣기 전에 WAL에 먼저 append한다(순차 쓰기라 싸다).
- 재시작 시 WAL을 처음부터 재생(replay)해 MemTable을 복원하고, MemTable이 flush되어 SSTable이 되면 그 구간의 WAL은 버린다. 즉 WAL의 수명 = MemTable의 수명.
- 내구성은 WAL을 언제 fsync하느냐로 결정된다(매 쓰기 / 주기적). 이 선택이 쓰기 지연과 손실 가능 구간을 맞바꾼다.

### D. 같은 LSM, 다른 선택 — LevelDB / RocksDB / Cassandra

- **LevelDB**: Google의 원형. Leveled compaction, 단일 스레드 compaction, 단일 column family.
- **RocksDB**: LevelDB 포크(Meta). 멀티스레드 compaction, column family, Leveled를 기본으로 두되 Universal(size-tiered 계열)·FIFO 등 전략 선택 가능. SSD·멀티코어 전제로 튜닝 노브가 매우 많다.
- **Cassandra**: 노드마다 LSM 저장소를 둔 분산 DB. 기본 STCS, 읽기 중심 테이블엔 LCS, 시계열엔 TWCS(시간 창 단위로만 합침 — 오래된 창은 다시 안 건드려 write amp를 줄인다)를 고른다.

### E. B-Tree와의 정면 비교 — in-place vs out-of-place

- B-Tree는 **in-place update**: 값이 있는 페이지를 찾아 그 자리에서 고친다. 한 key = 한 위치라 읽기가 단순하고, 갱신된 페이지만 다시 쓰니 쓰기 양 자체는 적지만 그 쓰기가 랜덤이다.
- LSM은 **out-of-place update**: 옛 값은 두고 새 값을 다른 곳에 append한다. 쓰기는 순차가 되지만 "어느 것이 최신인가"를 읽을 때 풀어야 하고, 옛 값을 치우는 compaction이 따라온다.
- 그래서 같은 증폭이라도 결이 다르다: B-Tree는 한 줄 고치려고 페이지(수 KB) 하나를 통째로 쓰는 **쓰기 증폭**, LSM은 한 레코드가 레벨을 내려가며 여러 번 다시 쓰이는 **쓰기 증폭** — 전자는 랜덤·소량·즉시, 후자는 순차·대량·지연이다. SSD에서는 랜덤 소량 쓰기가 FTL의 GC를 더 자극하므로 LSM 쪽 증폭이 상대적으로 싸게 먹히는 경우가 많다.
