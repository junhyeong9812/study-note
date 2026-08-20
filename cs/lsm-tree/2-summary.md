# cs/lsm-tree — LSM-Tree와 RUM Conjecture — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다.
> 원고는 내가 직접 쓴 `LSM-Tree.md`를 골격만 다듬은 것이다(2026-08-20).

## 전체 흐름

```text
문제   인덱스는 정렬돼야 검색이 빠른데, 정렬을 유지하려면 중간에 끼워넣어야 하고, 끼워넣으면 랜덤 쓰기가 된다
답     "정렬을 나중으로 미루자" — 랜덤 쓰기를 메모리(MemTable)에 흡수하고, 디스크에는 정렬된 불변 파일(SSTable)을 순차로만 내려보낸다
대가   읽기 — 같은 key가 여러 SSTable에 흩어짐(read amplification). Bloom filter·sparse index·compaction으로 갚는다
틀     RUM — Read/Update/Memory 중 둘을 좋게 하면 하나는 나빠진다. 쓰기 많으면 LSM, 읽기 중심이면 B-Tree
```

## 1. 해결하려는 문제

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

- **Bloom Filter** — "이 SSTable에 key 42가 확실히 없다"를 메모리에서 즉답. 없는 파일은 아예 안 읽는다. (있다고 답하면 실제로 있을 수도, 없을 수도 있다 — false positive만 허용)
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

이미 정렬된 파일들을 순차로 읽어 순차로 쓰는 작업이라 compaction도 순차 I/O다. 단, 호스트가 시키지 않은 쓰기라는 점에서 SSD의 GC와 같은 성격의 write amplification을 만든다.

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

## 핵심 문장

- LSM은 "정렬을 나중으로 미룬다" — 랜덤 쓰기를 메모리에 흡수하고 디스크엔 순차 쓰기만 보낸다.
- 수정·삭제도 쓰기다(새 레코드, tombstone). 불변 파일 + 최신 우선 읽기 = FTL과 같은 발상.
- 쓰기의 편함은 읽기가 갚는다(read amplification). Bloom filter는 "확실히 없다"만 즉답한다.
- Compaction은 LSM의 GC — 순차 I/O지만 호스트가 시키지 않은 쓰기(write amplification)다.
- RUM: 셋 중 둘만 고를 수 있다. Kafka는 key 조회가 없어서 LSM의 복잡도를 전부 생략할 수 있었다.

## 관련 자료

- 따라 친 원본 노트(직접 작성): `/home/jun/project/db-engine-lab/docs/study/LSM-Tree.md`
- 연결: [nand-flash](../nand-flash/) (FTL·GC·WAF — 하드웨어에서 같은 발상) · [kafka-why-fast](../kafka-why-fast/)
