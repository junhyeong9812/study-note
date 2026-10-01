# database/38-lsm-storage-engine — 정답

## 정답

### 1. 쓰기 경로

```text
  Put ─┬─> WAL (순차 append, 선택)
       └─> memtable (스킵 리스트)
             | write_buffer_size(64MB) 참
             v
           immutable memtable (memtable 총수 상한 max_write_buffer_number = 2, 활성 포함)
             | 배경 flush
             v
  L0  SST SST SST SST   ← 4개(level0_file_num_compaction_trigger)면 L0 compaction → base level
  L1  목표 256MB (max_bytes_for_level_base) ← base level이 L1까지 올라온 큰 DB 기준
  L2  ×10, L3 ×10 …    ← 레벨이 목표 크기를 넘으면 한 파일을 골라 다음 레벨의 겹치는 파일과 병합
```

- 기본값은 RocksDB `options.h`·`advanced_options.h`(main, 2026-10 조회).
- 기본 `level_compaction_dynamic_level_bytes = true`에서는 L0가 항상 L1로 가지 않는다. 빈 DB에서는 맨 아래 레벨이 base level이고, 데이터가 커지면 위로 올라온다.
- flush 때 memtable 안에서 덮어써진 값·삭제로 가려진 값은 버린다(Overview). 단 살아 있는 스냅숏이 보는 버전은 남긴다(위키 Snapshot).
- memtable이 flush되면 해당 WAL은 지워도 된다.

### 2. L0 vs L1 이하

- L0: flush된 파일이 그대로 쌓인다. 파일끼리 **키 범위가 겹친다**.
- L1 이하: 레벨 전체가 **하나의 정렬된 run**이다. 파일끼리 겹치지 않는다.
- 점 조회 비용: L0는 파일을 **모두** 확인해야 한다(최신부터). L1 이하는 레벨당 한 파일이다(Tuning Guide). 그래서 L0 파일 수가 늘면 읽기가 느려지고, RocksDB는 L0 파일 수로 write stall을 건다.

### 3. Bloom filter

- (1 − e^(−k·n/m))^k, m/n = 10, k = 7 → (1 − e^(−0.7))^7 ≈ **0.82%**. RocksDB Tuning Guide도 기본 10비트면 약 1%라고 적는다. 단 필터 자체는 `filter_policy`로 켜야 생긴다(기본 nullptr).
- 일반 범위 스캔에는 소용없다(접두사 범위만은 `prefix_extractor` + 접두사 Bloom으로 줄일 수 있다). Bloom filter는 "이 **키**가 있나"만 답한다. 범위 `[a, b)`는 어느 파일에나 걸칠 수 있어 파일마다 열어 봐야 한다. 범위 스캔의 읽기 증폭 ≈ L0 파일 수 + 비어 있지 않은 레벨 수(Tuning Guide).

### 4. 세 증폭 계산

- 정의
  - 쓰기 증폭 = 장치에 쓴 바이트 / DB에 쓴 바이트.
  - 읽기 증폭 = 쿼리당 디스크 읽기 수.
  - 공간 증폭 = 디스크 위 크기 / 데이터 크기.
- 공간: (0.5 + 0.5 + 5 + 51 + 512) / 500 ≈ **1.14**.
- 쓰기: 1(L0로 flush) + 2(L0→L1, 두 레벨 크기가 같음) + 10 + 10 + 10 ≈ **33**. L1 아래로 한 레벨 내려갈 때마다 약 10배 크기의 다음 레벨과 섞여 다시 쓰인다.
- 50배, 500MB/s → 500 / 50 = **10MB/s**. 쓰기 증폭을 줄이면 받을 수 있는 쓰기가 그대로 는다(Tuning Guide).

### 5. Leveled vs Tiered

| | 쓰기 | 읽기 | 공간 |
|---|---|---|---|
| Leveled | 큼(레벨당 최악 ≈ 배율) | 작음(레벨당 한 파일) | 작음 |
| Tiered/Universal | 작음(레벨당 ≈ 1) | 큼(정렬 run 여러 개) | 큼 |

- RocksDB 위키 Compaction 페이지의 정리와 같다. 초안 [systems/lsm-tree](../../systems/lsm-tree/2-summary.md) 「[Claude 추가]」 A와도 같은 방향이다.
- 2배: compaction은 입력 파일을 다 읽어 새 파일을 쓴 뒤에야 입력을 지운다. Universal은 가장 큰 run까지 한 번에 병합할 수 있어, 그 순간 데이터 전체만큼의 출력이 입력과 공존한다(Tuning Guide "일시적으로 2배").

### 6. 큐의 tombstone

- 무슨 일: 반복자가 0부터 `Seek`하면 살아 있는 키를 만날 때까지 **tombstone 9만 9천 개(와 옛 값)를 하나씩 지나친다**.
  - 로컬 재현(예시, Python 최소 LSM 모형, 실제 RocksDB 아님): flush만 한 상태에서 198,001개, tombstone을 남긴 병합 뒤 99,001개, 맨 아래까지 병합해 tombstone을 버린 뒤 1개.
- 언제 사라지나: tombstone은 더 아래 레벨에 같은 키의 옛 값이 남아 있을 수 있어 대개 **가장 아래 레벨**까지 내려가서야 버려진다. 살아 있는 스냅숏이 그 키를 볼 수 있으면 더 늦어진다.
- 대처(위키 Queue Service, Delete-A-Range): 소비한 head를 기억해 거기서 `Seek`, `iterate_upper_bound` 설정, `DeleteRange`, 덮어쓰지 않는 키에는 `SingleDelete`, `CompactOnDeletionCollector`.

### 7. write stall

- 뜻: L0 파일이 `level0_slowdown_writes_trigger`(기본 20)에 닿았다. L0→L1 compaction이 flush를 못 따라간다. RocksDB가 쓰기를 `delayed_write_rate`로 늦춘다. 쓰기마다 보통 1ms쯤 잠든다.
- 완전히 멈춤
  - L0 파일 36개(`level0_stop_writes_trigger`).
  - 밀린 compaction 바이트가 `hard_pending_compaction_bytes_limit`(256GB).
  - flush 대기 memtable이 `max_write_buffer_number`에 닿음.
  - 한 column family가 걸려도 DB 전체 쓰기가 멈춘다.
- 손잡이(위키 Write Stalls): `max_background_jobs` 증가, `write_buffer_size` 증가(쓰기 증폭 감소), `min_write_buffer_number_to_merge` 증가, 지연 민감한 쓰기와 배치 쓰기 분리.
- 트리거를 크게 올리면: 쓰기는 안 막히지만 L0 파일과 밀린 병합이 쌓인다. 읽기 증폭과 공간 증폭이 폭주한다. stall은 그것을 막으려는 안전장치다.

### 8. B+트리 vs LSM

- B+트리: 제자리 갱신. 키가 들어갈 잎을 찾아가 그 페이지를 고친다.
  - 무작위 키: 매번 다른 잎을 dirty로 만든다. 행 하나를 위해 페이지 하나를 쓴다. 잎이 반쯤 찬 채 쪼개진다(08번 재현: 밀도 66%, WAL 1.6배, FPI 급증).
  - 증폭의 결: 무작위·소량·즉시.
- LSM: 덧붙이기. memtable에 모아 순차로 flush하고, 나중에 병합한다.
  - 무작위 키여도 디스크 쓰기는 순차다. 대신 한 바이트가 레벨을 내려가며 여러 번 다시 쓰인다(예시 WA ≈ 33). 읽기는 여러 곳을 본다.
  - 증폭의 결: 순차·대량·지연.
- 쓰기가 많고 키가 무작위면 LSM, 읽기 위주·제자리 갱신이면 B+트리가 단순하다.

### 9. 디스크가 안 준다

- tombstone 쪽
  - 삭제는 tombstone을 쓸 뿐이고, 옛 값과 tombstone은 대개 compaction이 가장 아래 레벨에 닿아야 사라진다(더 아래에 그 키가 없으면 중간 레벨에서도 버린다). 삭제가 한쪽 범위에 몰리면 그 범위의 compaction이 늦다.
  - 확인: 레벨별 크기·파일 수(`rocksdb.stats`), 범위 스캔 지연.
  - 대처: `DeleteRange`, `CompactOnDeletionCollector`, 필요하면 그 범위 `CompactRange`.
- 스냅숏·반복자 쪽
  - 반복자는 자기가 보는 파일의 참조를 잡아 삭제를 막는다. 스냅숏은 compaction이 그 스냅숏에 보이는 키를 지우지 못하게 한다(Overview).
  - 확인: 오래 도는 백업·분석 작업, 오래 열린 반복자·스냅숏이 있는지.
  - 대처: 긴 스캔을 끊어 반복자를 새로 만든다. 스냅숏을 바로 해제한다.
- PostgreSQL에서 긴 트랜잭션이 VACUUM을 막는 것(06번)과 같은 모양이다.
