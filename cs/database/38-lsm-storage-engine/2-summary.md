# database/38-lsm-storage-engine — LSM 저장 엔진: memtable·SSTable·compaction·세 가지 증폭 — 정리 (힌트)

## 해결하는 문제

08번의 B+트리는 키가 들어갈 잎을 찾아가 **그 자리를** 고친다. 무작위 키가 쏟아지면 매번 다른 페이지를 읽고 고쳐 써야 한다(08번 재현: UUID 삽입의 WAL 1.6배, dirty 페이지 2.7배).\
LSM은 제자리를 고치지 않는다. 쓰기를 메모리에 모았다가 **정렬된 불변 파일**로 한 번에 순차로 쏟아 낸다. 정리는 나중에 배경에서 한다(compaction).

```text
  B+트리  put(k) → 잎을 찾아가 그 자리 수정     쓰기 = 무작위·즉시·소량
  LSM     put(k) → WAL 끝에 덧붙이고 memtable에  쓰기 = 순차·지연·대량  (정리 비용은 compaction이 나중에)
```

쉬운 예: 장부를 고치지 않고 정정 기록을 뒤에 덧붙이는 회계다. 최신 줄이 답이고, 결산 때 옛 줄을 정리한다(초안 §2와 같은 비유).

똑같은 구조다.\
정정 기록 = 새 버전·tombstone, 결산 = compaction.

실무 예:
- RocksDB(LevelDB 포크) 위에 MySQL 저장 엔진 MyRocks가 있다. RocksDB 위키 Delete-A-Range 페이지가 MyRocks의 테이블 삭제(테이블 ID 접두사 키 전부 삭제)를 예로 든다.
- 쓰기가 몰리면 RocksDB 로그에 `Stalling writes because we have 20 level-0 files`가 찍히고 쓰기 지연이 튄다.
- 오래된 항목을 앞에서부터 지우는 큐를 LSM 위에 만들면, 첫 항목 찾기가 점점 느려진다.

## 동작·원리

### 1. RocksDB의 쓰기 경로 (기본값은 RocksDB main 브랜치 `options.h`·`advanced_options.h`, 2026-10 조회)

```text
  Put(k,v) ─┬─> WAL (logfile, 순차 append, 선택)
            └─> memtable (기본 = 스킵 리스트, 정렬됨)
                   | write_buffer_size(기본 64MB) 차면
                   v
               immutable memtable ── (memtable 총수 상한 max_write_buffer_number = 2, 활성 포함)
                   | 배경 flush (같은 키의 덮어쓴 값·삭제된 값은 여기서 버림. 단 살아 있는 스냅숏이 보는 버전은 남김)
                   v
  L0   [SST][SST][SST][SST]         ← 파일끼리 키 범위가 겹친다. 4개(level0_file_num_compaction_trigger)면 L0 compaction
                                       (출력은 base level로 간다 — 아래 *base level* 풀이)
  L1   [SST|SST|SST|…]  목표 256MB   ← 레벨 안에서는 겹치지 않는 하나의 정렬된 run
  L2   [SST|SST|………………|SST]  ×10     (max_bytes_for_level_multiplier = 10)
  L3   …                        ×10
  Lmax 데이터의 대부분이 여기 산다
```

- *memtable*: 메모리의 정렬된 쓰기 버퍼다. RocksDB 기본 구현은 스킵 리스트다. 쓰기와 범위 스캔이 섞이면 정렬 집합이 필요해서다(RocksDB Overview). 벡터·접두사 해시 memtable도 고를 수 있다.
- *immutable memtable*: 찬 memtable은 읽기 전용으로 바뀌고 배경 스레드가 flush한다. 그동안 새 쓰기는 새 memtable에 쌓인다(파이프라이닝).
- *SST(SSTable)*: 키 순서로 정렬된 불변 파일. 블록(기본 4KB) 단위로 나뉘고 블록 색인과 필터를 가진다(Tuning Guide `block_size`).
- *base level*: L0가 병합되어 들어가는 첫 레벨이다. 기본값 `level_compaction_dynamic_level_bytes = true`에서는 L1로 고정되지 않는다. 빈 DB에서는 맨 아래 레벨이 base level이고, 데이터가 커지면 한 칸씩 위로 올라온다(`advanced_options.h` 주석). 그림의 "L1 목표 256MB"는 base level이 L1까지 올라온 큰 DB의 모양이다.
- *L0의 특수성*: flush된 파일이 그대로 쌓여 키 범위가 겹친다. 점 조회는 L0 파일을 **모두** 봐야 한다. L1부터는 레벨당 한 파일만 보면 된다(Tuning Guide).
- WAL은 memtable이 flush되면 지워도 된다(Overview). WAL이 memtable의 내구성을 맡는다. 초안 「[Claude 추가]」 C.

### 2. 읽기 경로

```text
  Get(k):  memtable → immutable memtable(들) → L0 파일 전부(최신부터) → L1 한 파일 → L2 한 파일 → …
           각 SST 앞에서 Bloom filter:  "확실히 없음" → 파일을 건너뜀
                                         "있을지도"   → 블록 색인 → 데이터 블록 읽기
           처음 만난 값이 답. 그것이 tombstone이면 "없음"
           (단순화: 스냅숏 조회는 그 스냅숏보다 새 기록을 건너뛰고, Merge 기록이면 아래 기록을 더 읽어 합친다)
```

- Bloom filter는 켜야 쓰인다. `BlockBasedTableOptions::filter_policy`의 기본값은 `nullptr`(필터 없음, `table.h`)이다. `NewBloomFilterPolicy(bits_per_key)`로 켤 때 `bits_per_key` 기본 10 → 거짓 양성 약 1%(RocksDB Tuning Guide). 초안 「[Claude 추가]」 B의 "확인 필요"는 이 문서로 확인된다.
  - 계산으로도 맞다: 키당 10비트, 해시 7개면 (1 − e^(−0.7))^7 ≈ 0.82%.
- 범위 스캔에는 Bloom filter가 소용없다. 범위 스캔의 읽기 증폭 ≈ L0 파일 수 + 비어 있지 않은 레벨 수(Tuning Guide).
  - 예외: `prefix_extractor`로 접두사 Bloom filter를 만들면 "접두사 XXX로 시작하는 키 전부" 같은 접두사 범위 조회는 줄일 수 있다(Tuning Guide).

### 3. 세 가지 증폭 — 정의와 재는 법 (RocksDB Tuning Guide)

```text
  쓰기 증폭(WA) = 저장 장치에 쓴 바이트 / DB에 쓴 바이트        예: DB 10MB/s, 디스크 30MB/s → 3
  읽기 증폭(RA) = 쿼리 하나당 디스크 읽기 수                      예: 페이지 5개를 읽어야 답 → 5
  공간 증폭(SA) = 디스크 위 파일 크기 / 실제 데이터 크기           예: 10MB를 넣었는데 100MB → 10
```

- Tuning Guide의 레벨 예시(L0 512MB, L1 512MB, L2 5GB, L3 51GB, L4 512GB, 데이터 500GB)
  - SA = (0.5 + 0.5 + 5 + 51 + 512)GB / 500GB ≈ **1.14**.
  - WA ≈ 1(L0로 flush) + 2(L0→L1, 두 레벨 크기가 같아서) + 10 + 10 + 10 = **33**. 한 바이트가 L1 아래로 내려갈 때마다 그 레벨의 약 10배와 섞여 다시 쓰인다. WAL 쓰기는 이 계산에 넣지 않았다.
- WA가 크면 디스크 대역폭이 병목이 된다. WA 50, 디스크 500MB/s면 DB는 10MB/s밖에 못 받는다(Tuning Guide). 플래시 수명도 준다.
- 재는 법: `DB::GetProperty("rocksdb.stats")`의 compaction 통계, 또는 `iostat`의 디스크 쓰기량 ÷ 앱의 쓰기량(Tuning Guide).

### 4. compaction 방식이 증폭을 맞바꾼다

| 방식 | 모양 | WA | RA | SA |
|---|---|---|---|---|
| Leveled (RocksDB 기본) | 레벨당 정렬 run 하나, 다음 레벨과 겹치는 파일만 병합 | 큼(레벨당 최악 ≈ 배율) | 작음 | 작음 |
| Tiered / Universal | 정렬 run 여러 개, 모아서 통째로 병합 (RocksDB Universal: L0 파일 하나·L1 이상은 레벨 하나가 각각 run) | 작음(레벨당 ≈ 1) | 큼 | 큼, 병합 중 일시적으로 2배까지 |

- RocksDB 위키: 고전 Leveled는 원조 LSM 논문(O'Neil 외)에서 왔고 공간 증폭을 줄이는 대신 읽기·쓰기 증폭을 낸다. Tiered는 쓰기 증폭을 줄이는 대신 읽기·공간 증폭을 낸다(Compaction 페이지). 위키는 RocksDB의 기본 Level compaction을 "Tiered+Leveled"로 분류한다. L0만 겹치는 run 여러 개이고 L1부터 레벨당 run 하나라서다.
- Universal은 `max_size_amplification_percent` 기본 200(100바이트 데이터가 300바이트까지). DB가 100GB를 넘으면 조심하라고 한다(Tuning Guide).
- 표의 방향은 초안 「[Claude 추가]」 A와 같다. 수식은 [lsm-merge-model](../../data-structure/lsm-merge-model/2-summary.md).

### 5. 삭제 = tombstone, 그리고 언제 사라지나

```text
  Delete(k) → (k, tombstone)을 쓴다. 옛 값은 아래 레벨에 그대로 있다.
  compaction이 tombstone을 옛 값과 만나게 해도, 더 아래 레벨에 같은 키의 더 옛 값이 있을 수 있다
  → tombstone은 보통 가장 아래 레벨(bottommost)까지 내려가서야 버려진다
    (단, 출력 레벨 아래에 그 키가 없고 스냅숏도 필요 없으면 중간 레벨 compaction에서도 버린다 — compaction_iterator.cc)
  예외: SingleDelete(덮어쓰지 않는 키 전용) — 원래 값을 만나면 함께 사라진다 (위키 Delete-A-Range)
```

- 스냅숏이 있으면 compaction은 그 스냅숏에 보이는 키를 지우지 않는다(Overview). 오래 열린 스냅숏이 옛 버전·tombstone을 붙든다. PostgreSQL의 긴 트랜잭션이 VACUUM을 막는 것과 같은 모양이다(06번).
- 범위 삭제
  - 키마다 `Delete()`를 부르면 tombstone 덩어리가 생긴다. 공간은 compaction 때까지 안 돌아오고, 반복자가 느려진다(위키 Delete-A-Range).
  - RocksDB 5.18+의 `DeleteRange(start, end)`는 범위 tombstone 하나로 대신한다(위키 DeleteRange).

### 6. write stall — 쓰기를 일부러 늦추는 장치

```text
  원인                               느리게 (slowdown)                         멈춤 (stop)
  flush 대기 memtable 과다            ≥ max_write_buffer_number − 1 (값이 3 초과일 때)   ≥ max_write_buffer_number
  L0 파일 과다                        level0_slowdown_writes_trigger = 20       level0_stop_writes_trigger = 36
  compaction 밀린 바이트 과다          soft_pending_compaction_bytes_limit 64GB  hard_…_limit 256GB
```

- 왜 늦추나: flush·compaction이 쓰기 속도를 못 따라가면 L0가 쌓여 읽기 증폭이, 밀린 병합이 쌓여 공간 증폭이 폭주한다. 그래서 쓰기를 `delayed_write_rate`까지 늦춘다(위키 Write Stalls).
- slowdown 중에는 쓰기마다 보통 1ms 정도 잠든다. stop이면 무기한 막힌다. 한 column family가 걸려도 **DB 전체** 쓰기가 멈춘다(위키 Write Stalls).
- 늦추지 말고 바로 실패를 받고 싶으면 `WriteOptions.no_slowdown = true` → `Status::Incomplete()`.

## 쓰이는 자료구조·알고리즘

- **스킵 리스트**: RocksDB 기본 memtable. 동시 삽입과 정렬 순회를 함께 한다. → [data-structure/12-skip-list](../../data-structure/12-skip-list/2-summary.md)
- **SSTable(정렬 불변 파일) + 블록 색인**: 파일 안은 이진 탐색, 범위는 순차 읽기.
- **Bloom filter**: SST마다 "확실히 없음" 판정. 키당 비트 수로 거짓 양성률과 메모리를 맞바꾼다. → [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **k-way 병합**: compaction과 범위 스캔 모두 여러 정렬 run을 힙으로 병합한다. 같은 키면 최신(시퀀스 번호가 큰 것)이 이긴다. → [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **WAL(append-only 로그)**: memtable의 내구성. 19번과 같은 원리.
- **LSM 전체**: 제자리 갱신 대신 덧붙이기 + 배경 병합. → [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)

## 적용 — 풀어나가는 법

**1) 워크로드로 고른다.**

```text
  쓰기 비중이 크고 키가 무작위(이벤트·로그·시계열·메시지)   → LSM이 유리 (쓰기가 순차)
  점 조회·범위 조회가 대부분, 갱신이 제자리               → B+트리가 단순
  공간이 비싸다(SSD 용량)                                → Leveled LSM이 SA 약 1.1대 (예시 계산)
  지연 꼬리가 중요하다                                   → LSM의 compaction·stall이 꼬리를 만든다. 대역폭 여유를 둔다
```

**2) 상태를 본다 (RocksDB).**

```text
  db->GetProperty("rocksdb.stats", &s)            레벨별 파일 수·크기·쓰기량(W-Amp)·stall 시간
  db->GetProperty("rocksdb.num-files-at-level0")  L0 파일 수
  LOG 파일: "Stalling writes because …" / "Stopping writes because …"
  iostat 디스크 쓰기량 ÷ 앱 쓰기량 = 쓰기 증폭
```

**3) write stall을 줄이는 손잡이 (위키 Write Stalls).**
- flush가 밀리면: `max_background_jobs` 증가, `max_write_buffer_number` 증가.
- L0·밀린 compaction이 원인이면: `max_background_jobs` 증가, `write_buffer_size` 증가(쓰기 증폭 감소), `min_write_buffer_number_to_merge` 증가.
- 대량 적재라면 위키 Write Stalls가 FAQ의 "가장 빠른 적재 방법"을 보라고 안내한다. 일반 쓰기 경로로 밀어 넣지 않는다.

**4) 삭제가 많은 키 설계.**
- 큐처럼 앞에서부터 지우는 패턴은 `<queue_id, seq>` 키로 두고(big-endian 순번), 소비한 마지막 순번을 기억해 **tombstone 구간을 순회하지 않는다**. 반복자에 `iterate_upper_bound`를 건다(위키 Queue Service).
- 범위를 통째로 지울 때는 `DeleteRange`. tombstone이 많은 파일을 먼저 compaction하도록 `CompactOnDeletionCollector`를 쓴다.

**5) 앱에서 (Java, RocksJava).**

```java
try (Options opt = new Options().setCreateIfMissing(true);
     RocksDB db = RocksDB.open(opt, "/data/queue")) {
    byte[] key = ByteBuffer.allocate(12).putInt(queueId).putLong(seq).array(); // big-endian → 순번 순 정렬
    db.put(key, payload);

    // 소비한 구간 [head, tail) 을 한 번에 지운다 — 키마다 delete() 대신 범위 tombstone 하나
    db.deleteRange(keyOf(queueId, oldHead), keyOf(queueId, newHead));

    try (ReadOptions ro = new ReadOptions()
             .setIterateUpperBound(new Slice(keyOf(queueId + 1, 0)));   // 다음 큐로 넘어가 tombstone을 훑지 않게
         RocksIterator it = db.newIterator(ro)) {
        it.seek(keyOf(queueId, newHead));   // 0부터가 아니라 기억한 head부터
        // ...
    }
}
```

## 장애 시나리오와 대처

**1) compaction 적체 → write stall (⚠)**
- 현상: 쓰기 폭주 뒤 쓰기 지연이 수 ms에서 수 초로 튀고, 결국 쓰기가 멈춘다. 읽기도 느려진다.
- 보이는 형태: RocksDB LOG에 `Stalling writes because we have 20 level-0 files`, `Stopping writes because of estimated pending compaction bytes …`. `rocksdb.stats`의 stall 시간 증가. 앱에서는 `Put` 지연 급증, `no_slowdown`이면 `Status::Incomplete()`.
- 원인: flush·compaction 처리량 < 들어오는 쓰기 × 쓰기 증폭. L0 파일이 20개(slowdown)·36개(stop)에 닿거나 밀린 compaction이 64GB·256GB를 넘는다(기본값). 한 column family 때문에 DB 전체가 멈출 수 있다.
- 대처: 배경 스레드를 늘린다. memtable을 키워 쓰기 증폭을 줄인다. 디스크 대역폭 여유를 확보한다. 지연에 민감한 쓰기와 배치 쓰기를 분리한다(저우선 쓰기). 트리거를 무작정 올리면 stall은 줄지만 읽기·공간 증폭이 커진다.

**2) tombstone 누적 → 범위 조회 느림 (⚠)**
- 현상: 오래된 항목을 앞에서부터 지우는 큐·TTL 테이블에서 "가장 오래된 살아 있는 항목"을 찾는 조회가 점점 느려진다. 데이터 양은 줄었는데 CPU·읽기가 는다.
- 보이는 형태: `Seek(<queue_id, 0>)` 지연 증가, 마지막 항목에서 `Next()`가 느리다(위키 Queue Service). 디스크 사용량이 삭제 뒤에도 줄지 않는다.
- 원인: 삭제는 tombstone을 쓸 뿐이다. 반복자는 살아 있는 키를 만날 때까지 tombstone을 하나하나 지나친다. tombstone은 대개 가장 아래 레벨까지 내려가야 사라진다.
  - 로컬 재현(예시, Python 최소 LSM 모형 — 저자 작성 시뮬레이션, 실제 RocksDB 아님): 10만 개를 넣고 앞 9만 9천 개를 지운 뒤 첫 살아 있는 키를 찾았다.

```text
  flush만 한 상태 (run 199개)                  지나친 항목 198,001개
  병합했지만 tombstone 유지 (맨 아래 아님)       지나친 항목 99,001개
  맨 아래까지 병합, tombstone 제거              지나친 항목 1개
```

- 대처: 시작 위치를 기억해 tombstone 구간을 건너뛴다. `iterate_upper_bound`를 건다. 범위 삭제는 `DeleteRange`. 덮어쓰지 않는 키는 `SingleDelete`. 삭제가 많은 범위를 먼저 compaction하게 한다(`CompactOnDeletionCollector`).

**3) 공간이 모자란다 — compaction 중 디스크 가득**
- 현상: 디스크 사용률이 데이터 크기의 2배 가까이 튀었다가 내려간다. 여유가 적으면 디스크가 차서 쓰기 오류가 난다.
- 보이는 형태: 디스크 사용량 톱니 모양. 디스크가 차면 쓰기가 실패한다(오류의 정확한 형태는 버전별 [?]).
- 원인: compaction은 입력 파일과 출력 파일이 잠시 공존한다. Universal(tiered)은 가장 큰 run을 포함한 병합에서 일시적으로 공간이 2배까지 필요하다(Tuning Guide).
- 대처: Universal이면 데이터를 여러 인스턴스로 나누고 동시 compaction 수를 제한한다(Tuning Guide의 샤딩 권고). Leveled로 바꾸거나 병합 중 최대치를 기준으로 디스크 여유를 잡는다.

**4) 오래 열린 스냅숏·반복자가 공간을 붙든다**
- 현상: 삭제·갱신을 계속하는데 디스크가 줄지 않는다. 오래된 SST 파일이 지워지지 않는다.
- 보이는 형태: 파일 수·디스크 사용량이 계속 증가. 오래 도는 백업·분석 작업과 시기가 겹친다.
- 원인: 반복자는 자기가 보는 파일들의 참조를 잡아 삭제를 막는다. 스냅숏은 compaction이 그 스냅숏에 보이는 키를 지우지 못하게 한다(Overview).
- 대처: 긴 스캔은 짧게 끊어 반복자를 다시 만든다. 끝난 스냅숏을 바로 해제한다.

## 핵심 문장

- LSM은 쓰기를 WAL + memtable(기본 스킵 리스트)에 받고, 차면 정렬된 불변 SST로 순차 flush한 뒤, 배경 compaction으로 레벨을 정리한다.
- 점 조회는 memtable → L0 전부 → 레벨마다 한 파일을 본다. Bloom filter를 켜면(`filter_policy`, 기본은 꺼짐) SST마다 "확실히 없음"을 걸러 준다(키당 10비트 ≈ 1%).
- 증폭은 셋이다. 쓰기(디스크 쓰기/DB 쓰기), 읽기(쿼리당 디스크 읽기), 공간(디스크/데이터). Leveled는 공간·읽기를 줄이고 쓰기를 내며(예시 WA ≈ 33), Tiered는 반대다.
- flush·compaction이 쓰기를 못 따라가면 RocksDB는 쓰기를 일부러 늦추거나 멈춘다(L0 20개 slowdown, 36개 stop이 기본).
- 삭제는 tombstone 쓰기다. tombstone은 대개 가장 아래 레벨에서야 사라지고, 그 전까지 범위 스캔이 하나씩 지나친다.

## 관련 주제·근거

기초(왜 LSM인가, 쓰기 경로, tombstone, Bloom filter, Leveled vs Size-tiered, RUM)는 기존 초안 [systems/lsm-tree](../../systems/lsm-tree/2-summary.md) §1~5와 「[Claude 추가]」 A~E에 있다. 자료구조 구현은 [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md), 병합 모델의 수식은 [lsm-merge-model](../../data-structure/lsm-merge-model/2-summary.md). 이 노트는 그 위에 **저장 엔진으로서의 동작**(RocksDB 기준 수치·기본값), 증폭을 재는 법, write stall·tombstone 장애를 채운다.

- 선행
  - [06-pages-and-tuple-layout](../06-pages-and-tuple-layout/2-summary.md) — 제자리 갱신하는 페이지 저장과의 대비
  - [data-structure/24 lsm-tree](../../data-structure/24-lsm-tree/2-summary.md) — LSM 자료구조 구현
  - 기존 초안 [systems/lsm-tree](../../systems/lsm-tree/2-summary.md) — 쓰기 경로·tombstone·Bloom·Leveled vs Size-tiered·RUM·Kafka 비교
- 연결
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) — 제자리 갱신 B+트리와 무작위 삽입의 비용
  - [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md) — 불변 파트 + 배경 병합(ClickHouse MergeTree)
  - [lsm-merge-model](../../data-structure/lsm-merge-model/2-summary.md) — 레벨·티어 트레이드오프 수식
  - [systems/nand-flash](../../systems/nand-flash/2-summary.md) — FTL·GC·쓰기 증폭의 하드웨어판
  - database [19-wal-and-logging](../19-wal-and-logging/2-summary.md) — WAL 원리.
- 문서·소스 (RocksDB, 2026-10 조회)
  - RocksDB Wiki: RocksDB Overview(memtable·logfile·sstfile, 스킵 리스트 기본, 파이프라이닝, 스냅숏과 compaction) <https://github.com/facebook/rocksdb/wiki/RocksDB-Overview>
  - RocksDB Wiki: RocksDB Tuning Guide(증폭 정의와 예시 WA 33·SA 1.14, Bloom 10비트 ≈ 1%, block_size 4KB, Universal 2배) <https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide>
  - RocksDB Wiki: Compaction · Leveled Compaction · Universal Compaction <https://github.com/facebook/rocksdb/wiki/Compaction>
  - RocksDB Wiki: Write Stalls <https://github.com/facebook/rocksdb/wiki/Write-Stalls>
  - RocksDB Wiki: Delete A Range Of Keys · DeleteRange · Implement Queue Service Using RocksDB <https://github.com/facebook/rocksdb/wiki/Implement-Queue-Service-Using-RocksDB>
  - facebook/rocksdb `include/rocksdb/options.h`(`write_buffer_size` 64MB, `level0_file_num_compaction_trigger` 4, `max_bytes_for_level_base` 256MB) · `include/rocksdb/advanced_options.h`(`max_write_buffer_number` 2, slowdown 20 / stop 36, 배율 10, soft 64GB / hard 256GB, `SkipListFactory`, `level_compaction_dynamic_level_bytes` 기본 true) · `include/rocksdb/table.h`(`filter_policy` 기본 nullptr) · `db/compaction/compaction_iterator.cc`(`KeyNotExistsBeyondOutputLevel`로 삭제 표시 제거) · 위키 Snapshot(flush·compaction이 스냅숏에 보이는 버전 보존) · Merge Operator
- 교재·논문: DDIA 1판 3장 "SSTables and LSM-Trees" · P. O'Neil 외, "The Log-Structured Merge-Tree (LSM-Tree)", Acta Informatica, 1996(RocksDB 위키 경유, 원문 미열람)
- 로컬 재현: Python 최소 LSM 모형(저자 작성)으로 tombstone 누적이 첫 살아 있는 키 탐색에 지나치는 항목 수, Bloom 거짓 양성률 계산식
