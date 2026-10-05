# data-structure/19-lsm-merge-model — LSM 병합 모델: 레벨·티어 트레이드오프 — 정리 (힌트)

## 해결하는 문제

LSM 트리는 쓰기를 정렬된 불변 파일로 떨군다. 파일이 쌓이면 합쳐야 한다(compaction).\
**언제, 무엇을, 몇 개씩 합치느냐**가 병합 정책이고, 이 선택 하나로 같은 데이터·같은 엔진의 비용이 몇 배씩 달라진다.

```text
  같은 쓰기 100만 건 (시뮬레이션, 아래 실험)
                         디스크에 쓴 양      키 하나 찾을 때 열어 볼 run 수(최악)
  레벨(leveled),  T=10      13.2배                 3
  티어(tiered),   T=10       2.8배                 7
```

- 쓰기를 아끼면 읽기·공간이 비싸지고, 읽기·공간을 아끼면 쓰기가 비싸진다. 셋을 동시에 최소로 만드는 정책은 없다.
  - *compaction(병합)*: 정렬된 파일(run) 여러 개를 하나로 머지 소트하면서 같은 키의 옛 버전과 삭제 표시를 정리하는 백그라운드 작업.
  - *병합 정책(merge policy, compaction strategy)*: 어떤 run들을 언제 합칠지 정하는 규칙.

쉬운 예: 서류함 정리.
- 레벨 방식: 새 서류가 오면 그 서랍의 기존 묶음과 바로 합쳐 서랍마다 **한 묶음**만 유지한다. 찾기는 쉽지만 같은 서류를 여러 번 다시 정리한다.
- 티어 방식: 서랍마다 묶음을 T개까지 그냥 쌓아 두다가, T개가 차면 한꺼번에 합쳐 다음 서랍으로 보낸다. 정리는 덜 하지만 찾을 때 묶음을 여러 개 뒤진다.

똑같은 구조다.\
실무 예:
- (예시) 로그·지표처럼 쓰기만 많은 테이블을 레벨 방식으로 두었더니 SSD 쓰기량이 앱 쓰기량의 수십 배가 되고 compaction이 밀려 쓰기가 멈춘다(write stall).
- (예시) 갱신이 잦은 테이블을 티어 방식으로 두었더니 같은 키의 옛 버전이 여러 run에 남아 디스크가 데이터의 몇 배로 찬다.

기초(정렬은 memtable에서 끝나고 compaction은 머지 소트라는 점, 병합 비용은 락이 아니라 자원 경쟁이라는 점, 복제와 병합)는 원본 [data-structure/lsm-merge-model](../lsm-merge-model/2-summary.md) 「쓰기 경로」·「병합 비용의 본질」·「복제와 병합」 절에 있다. LSM 전체 구조와 구현은 [24-lsm-tree](../24-lsm-tree/2-summary.md), RocksDB 기본값·write stall·tombstone 장애는 [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)이 맡는다. 이 노트는 **병합 정책의 비용 모델과 선택**에 집중한다.

## 동작·원리

### 1. 공통 용어 — run, 레벨, 크기 비율 T

```text
  메모리 버퍼(memtable) ──flush──▶  Level 1   용량 ≈ 버퍼 × T
                                   Level 2   용량 ≈ 버퍼 × T²
                                   Level 3   용량 ≈ 버퍼 × T³      … 레벨 수 L ≈ log_T(N / 버퍼)
```

- *sorted run(정렬된 run)*: 키 범위가 서로 겹치지 않는 파일들의 묶음으로, 전체가 하나의 정렬된 목록처럼 읽히는 단위. 파일 여러 개일 수 있다.
  - 흔한 오해: "레벨당 파일이 1개다." — 레벨 방식에서 레벨당 하나인 것은 **run**이다. RocksDB L1 이상은 한 레벨이 키 범위로 나뉜 SST 파일 여러 개로 된 run 하나이고, L0만 겹치는 파일 여러 개다(RocksDB wiki Leveled Compaction).
- *크기 비율(size ratio) T*: 이웃 레벨 용량의 배수. RocksDB `max_bytes_for_level_multiplier` 기본 10(`advanced_options.h`), Cassandra LCS `fanout_size` 기본 10(Cassandra 문서 LCS).
- *쓰기 증폭(WA)*: 저장 장치에 쓴 바이트 ÷ 사용자가 쓴 바이트.
- *읽기 증폭(RA)*: 조회 하나에 읽는 run(또는 블록) 수.
- *공간 증폭(SA)*: 디스크 위 크기 ÷ 살아 있는 데이터 크기. 옛 버전·삭제 표시·병합 중 임시 사본이 키운다.

### 2. 레벨 방식 — 레벨마다 run 하나

```text
  Level i   [■■■■■■■■■■■■■■■■]  ← run 하나 (꽉 차면 다음 레벨과 병합)
               ▲ 위 레벨에서 새 run이 내려올 때마다 기존 run과 합쳐 다시 쓴다
  Level i+1 [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■]

  한 엔트리는 레벨 하나에 머무는 동안 평균 T/2번쯤 다시 쓰인다 → WA ≈ O(T · L)
  조회: 레벨마다 run 1개 → 최대 L개 (블룸 필터로 대부분 건너뜀)
```

- Dayan–Idreos(SIGMOD 2018, Dostoevsky)의 분석: 레벨 i에 j번째 run이 도착할 때마다 기존 run과 합치므로, 한 엔트리는 레벨이 찰 때까지 평균 T/2번(O(T)) 병합되고, 레벨 L개를 거쳐 O(T·L)번 병합된다.
- O'Neil 외(1996)의 원조 LSM 트리가 이 계열이다. RocksDB wiki는 고전 레벨 방식이 "읽기·쓰기 증폭을 대가로 공간 증폭을 최소화한다"고 적는다(Compaction 페이지).
- 실제 엔진은 레벨 전체가 아니라 **겹치는 파일만** 골라 합친다. RocksDB는 Ln에서 파일 하나를 골라 Ln+1의 겹치는 범위와 병합한다(wiki Leveled Compaction). 점근 성질은 같고 한 번의 병합 크기가 작아진다.

### 3. 티어 방식 — 레벨마다 run 여러 개

```text
  Level i   [■■■] [■■■] [■■■]   ← run이 T개 차면
                 ╲    │    ╱
                   한꺼번에 병합 → 새 run 하나
  Level i+1 [■■■■■■■■■] [■■■■■■■■■]   ← 여기에 run으로 추가만 (기존 run과 안 합침)

  한 엔트리는 레벨마다 1번 병합 → WA ≈ O(L)
  조회: 레벨마다 run 최대 T−1개 → 최대 (T−1)·L개
```

- RocksDB wiki: 티어 방식은 "한 레벨의 sorted run 전부를 합쳐 다음 레벨의 새 run을 만든다", "레벨당 쓰기 증폭은 1"이며 "읽기·공간 증폭을 대가로 쓰기 증폭을 최소화한다."
- RocksDB의 Universal compaction, Cassandra의 STCS(Size-Tiered, 기본 전략)가 이 계열이다.

### 4. 비용 표 — 같은 T, 다른 정책 (Dostoevsky 그림 3·4)

| 비용 | 레벨 | 티어 |
|---|---|---|
| 갱신(쓰기) I/O, 엔트리당 분할 상환 | O(T·L / B) | O(L / B) |
| 짧은 범위 조회 I/O | O(L) | O(T·L) |
| 점 조회(블룸 필터 없을 때 run 수) | 최대 L | 최대 (T−1)·L |
| 최악 공간 증폭(옛 버전으로 인한 추가분) | O(1/T)(가장 큰 레벨이 차 있거나 레벨 용량을 동적으로 맞출 때) | O(T) |

- B는 블록당 엔트리 수, L은 레벨 수다. 블룸 필터를 쓰면 점 조회 비용은 run마다의 오탐률 합으로 바뀐다(같은 논문·Monkey 2017).
- 공간 증폭 최악은 둘 다 **가장 큰 레벨의 옛 버전**에서 나온다. 티어는 가장 큰 레벨에 같은 키 집합의 run이 여러 개 있을 수 있어 O(T)다(논문 그림 4 설명). 레벨의 O(1/T)는 가장 큰 레벨이 용량만큼 찼다는 전제다. 덜 차 있으면 더 커질 수 있고, RocksDB처럼 레벨 용량을 동적으로 조정해 비율 T를 지키면 상한이 유지된다(논문 각주 4).
- 분할 상환(amortized) 비용이다. 한 번의 큰 병합이 순간적으로 디스크·CPU를 크게 쓰는 것은 따로 봐야 한다(장애 3).

### 5. T라는 손잡이 — 양 끝에서 두 정책이 만난다

```text
  T = 2                                       T = T_lim (레벨 1개)
  ───────────────────────────────────────────────────────────────
  레벨 수 같고, 두 번째 run이 오면           레벨: 정렬된 배열 하나 (쓰기마다 전체 재작성)
  바로 병합 → 레벨 = 티어 (같은 동작)         티어: 그냥 로그 (병합 없음, 조회는 전부 훑기)
```

- Dostoevsky: "크기 비율이 하한 2이면 레벨과 티어의 성능 특성이 수렴한다 — 레벨 수가 같고 두 번째 run이 들어올 때마다 병합이 일어난다." "T가 T_lim(저장소에 레벨 하나)이면 티어는 로그로, 레벨은 정렬된 배열로 퇴화한다."
- 그래서 T를 키우면: 레벨은 쓰기가 더 비싸지고 조회·공간이 더 싸진다. 티어는 반대다.

### 6. 섞어 쓰는 정책 — 레벨마다 다르게

```text
  작은 레벨 (자주 병합됨, 데이터는 적음)   →  티어로 두어 쓰기를 아낀다
  가장 큰 레벨 (데이터 대부분, 공간 좌우)  →  레벨로 두어 공간·조회를 아낀다
```

- RocksDB wiki는 기본 Level compaction을 **Tiered+Leveled**로 분류한다. L0는 겹치는 run 여러 개(티어), L1부터 레벨마다 run 하나(레벨)라서다. "레벨 방식보다 쓰기 증폭이 작고 티어 방식보다 공간 증폭이 작다."
- Dostoevsky의 *lazy leveling*: 가장 큰 레벨만 레벨, 나머지는 티어. 쓰기 O((T+L)/B)로 줄이면서 점 조회·긴 범위 조회·공간 증폭 상한은 레벨과 같게 유지한다(논문 §4.1). 점 조회가 같은 것은 레벨별 블룸 필터 오탐률을 최적 배분했을 때의 **기대 I/O** 기준이다. 블룸 필터가 없으면 작은 레벨마다 run을 최대 T−1개 봐야 해 레벨 방식(최대 L개)보다 많다.
- Cassandra 문서(latest = 5.0판, 2026-10 조회)는 UCS(Unified Compaction Strategy)를 "대부분의 워크로드에 좋은 선택이고 새 워크로드에 권장"한다고 적는다. 기본값은 여전히 STCS다("다른 전략이 맞지 않을 때의 폴백으로 유용해서").

### 실험: 레벨 vs 티어 병합 시뮬레이션 (시뮬레이션 명시)

실제 엔진이 아니라 정책의 방향만 보는 단순 모델이다.
- 버퍼 4,000개가 차면 flush. 레벨 방식은 레벨 i 용량 = 4,000 × T^(i+1), 넘치면 레벨 run 전체를 다음 레벨 run과 병합한다(실제 엔진의 파일 단위 부분 병합이 아님).
- 티어 방식은 레벨마다 run이 T개 차면 합쳐 다음 레벨에 run으로 추가한다.
- 키만 센다. 병합 때 같은 키는 최신만 남긴다. 삭제·블룸 필터·L0 특례 없음.

```python
def push_leveled(run_, i):
    nonlocal written
    while True:
        if len(levels) <= i: levels.append(None)
        cur = levels[i]
        new = run_ if cur is None else merge([run_, cur])
        written += len(new)                    # 레벨 i의 run을 통째로 다시 쓴다
        if len(new) <= B * T ** (i + 1):
            levels[i] = new; return
        levels[i] = None; run_ = new; i += 1   # 용량 초과 → 다음 레벨로 내려 병합

def push_tiered(run_, i):
    nonlocal written
    while True:
        if len(levels) <= i: levels.append([])
        levels[i].append(run_)
        if len(levels[i]) < T: return
        run_ = merge(levels[i]); written += len(run_)   # T개 run을 하나로
        levels[i] = []; i += 1
```

(실험, 호스트 Python 3.12.3, `python3 lsm_sim.py`, 쓰기 N=1,000,000, 버퍼 4,000, 시드 1, 2026-10-05 — 시뮬레이션)

```text
insert-unique T= 4 leveled  WA=10.78  runs= 2  hit-lookup runs= 1.96  miss-lookup runs= 2  SA=1.00
insert-unique T= 4 tiered   WA= 3.72  runs=10  hit-lookup runs= 8.20  miss-lookup runs=10  SA=1.00
insert-unique T=10 leveled  WA=13.24  runs= 3  hit-lookup runs= 2.85  miss-lookup runs= 3  SA=1.00
insert-unique T=10 tiered   WA= 2.80  runs= 7  hit-lookup runs= 5.81  miss-lookup runs= 7  SA=1.00
update-heavy  T= 4 leveled  WA= 6.67  runs= 3  hit-lookup runs= 2.24  miss-lookup runs= 3  SA=1.71
update-heavy  T= 4 tiered   WA= 2.89  runs= 7  hit-lookup runs= 2.66  miss-lookup runs= 7  SA=4.37
update-heavy  T=10 leveled  WA= 8.44  runs= 2  hit-lookup runs= 1.68  miss-lookup runs= 2  SA=1.33
update-heavy  T=10 tiered   WA= 1.98  runs=10  hit-lookup runs= 5.99  miss-lookup runs=10  SA=3.47
```

- `insert-unique`: 모든 키가 새 키. `update-heavy`: 키 10만 개에 100만 번 쓰기(같은 키를 평균 10번 덮어씀).
- `hit-lookup runs`: 있는 키를 최신 run부터 찾을 때 연 run 수 평균(블룸 필터 없음). `miss-lookup runs`: 없는 키 = 모든 run.
- 관찰
  - 같은 T에서 레벨의 WA가 티어의 2.3~4.7배였다(T=4: 10.78 vs 3.72, 6.67 vs 2.89 / T=10: 13.24 vs 2.80, 8.44 vs 1.98). T가 클수록 차이가 컸다.
  - 티어는 run 수가 7~10개로 레벨(2~3개)보다 많다. 없는 키 조회는 run 수만큼 연다.
  - 덮어쓰기가 많으면 티어의 공간 증폭이 3.47~4.37로 레벨(1.33~1.71)보다 크다. 새 키만 넣으면 옛 버전이 없어 둘 다 1.00이다.

T를 바꿔 본 결과(같은 모델, `insert-unique`):

```text
insert-unique T= 2  leveled WA=12.09 runs=5  |  tiered WA= 7.12 runs=6
insert-unique T= 4  leveled WA=10.78 runs=2  |  tiered WA= 3.72 runs=10
insert-unique T= 8  leveled WA=11.80 runs=3  |  tiered WA= 2.76 runs=12
insert-unique T=16  leveled WA=17.02 runs=2  |  tiered WA= 1.96 runs=25
```

- T가 커질수록 티어는 WA가 줄고 run이 늘었다(7.12 → 1.96, 6 → 25). 레벨은 T=4 이후 WA가 늘었다(10.78 → 17.02).
- T=2에서 둘이 가장 가까웠지만 같지는 않았다(12.09 vs 7.12). 이 모델의 레벨 방식이 "용량 초과 시 레벨 전체 이동"이라 논문 모델과 세부가 다르기 때문이다(해석).
- 레벨 수가 정수라서 T에 따라 계단처럼 변한다(T=4에서 run 2개, T=8에서 3개). 이 수치를 실제 엔진 설정값으로 옮기면 안 된다.

## 쓰이는 자료구조·알고리즘

- **이 주제가 쓰는 하위 구조**
  - k-way 병합(최소 힙) — compaction의 본체 → [algorithm/11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md), [07-heap](../07-heap/2-summary.md)
  - 블룸 필터 — run마다 "없음"을 싸게 거른다. 티어의 많은 run을 버티게 하는 장치 → [11-bloom-filter](../11-bloom-filter/2-summary.md)
  - memtable 정렬 구조(스킵 리스트) → [12-skip-list](../12-skip-list/2-summary.md)
  - 분할 상환 분석 — WA는 엔트리당 분할 상환 비용이다 → [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md)
- **이 주제를 쓰는 곳(🔧 compaction 전략)**
  - RocksDB: `kCompactionStyleLevel`(기본), `kCompactionStyleUniversal`, `kCompactionStyleFIFO`(오래된 파일을 버림, 캐시성 데이터), `kCompactionStyleNone` (wiki Compaction)
  - Cassandra: STCS(기본), LCS, TWCS(TTL이 붙은 시계열), UCS(새 워크로드 권장)
  - ClickHouse MergeTree의 파트 병합 → [database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 정책 고르는 순서

```text
  ① 워크로드를 잰다     쓰기:읽기 비율, 덮어쓰기·삭제 비율, 범위 조회 비중, TTL 여부
  ② 비싼 자원을 정한다   SSD 수명·쓰기 대역폭? 디스크 용량? 조회 p99?
  ③ 정책 고르기
       쓰기 많고 덮어쓰기 적음, 공간 여유 있음     → 티어(Universal·STCS)
       읽기·갱신·삭제 많음, 공간 비쌈               → 레벨(Level·LCS)
       시간 순 삽입 + TTL로 통째 만료               → 시간 창(TWCS)·FIFO
       판단이 어렵다                                → 하이브리드(RocksDB 기본, UCS)
  ④ T를 조정한다        레벨: T↑ = 조회·공간↓ 쓰기↑ / 티어: T↑ = 쓰기↓ 조회·공간↑
  ⑤ 운영에서 다시 잰다   WA·SA·run 수·조회 p99
```

### 2. 설정 예

RocksDB(C++ 옵션, 값은 `advanced_options.h`·`universal_compaction.h` 기본값):

```cpp
Options opt;
opt.compaction_style = kCompactionStyleLevel;          // 기본
opt.max_bytes_for_level_multiplier = 10;               // T, 기본 10
opt.level_compaction_dynamic_level_bytes = true;       // 기본 true — 마지막 레벨 기준으로 레벨 크기를 잡음

// 티어 쪽
opt.compaction_style = kCompactionStyleUniversal;
opt.compaction_options_universal.size_ratio = 1;                       // 기본 1 — T가 아니라 '파일 크기 비교 여유 %'
opt.compaction_options_universal.min_merge_width = 2;                  // 기본 2
opt.compaction_options_universal.max_size_amplification_percent = 200; // 기본 200
```

- wiki: `level_compaction_dynamic_level_bytes`를 켜면 데이터의 약 90%가 마지막 레벨, 9%가 그 앞 레벨에 있게 된다. 공간 증폭이 안정된다.

Cassandra(CQL):

```sql
ALTER TABLE shop.orders
  WITH compaction = {'class': 'LeveledCompactionStrategy', 'sstable_size_in_mb': 160, 'fanout_size': 10};
```

- LCS 기본 `sstable_size_in_mb` 160, `fanout_size` 10. 문서는 LCS가 "I/O·CPU를 더 쓰고 쓰기 위주 워크로드에는 좋은 선택이 아니다"라고 적는다.

### 3. 재는 법

```text
  WA  = 디스크 쓰기 바이트(iostat, 엔진 통계) ÷ 앱이 쓴 바이트
  SA  = 디스크 사용량 ÷ 논리 데이터 크기
  RA  = 조회당 읽은 run·블록 수 (엔진 통계: 조회당 SST 수)
  RocksDB: db->GetProperty("rocksdb.stats") 의 Compaction Stats — 레벨별 W-Amp(레벨 N+1에 쓴 바이트 ÷ 레벨 N에서 읽은 바이트)
  Cassandra: nodetool tablestats(SSTable 수, 레벨별 SSTable 수), nodetool tablehistograms(조회당 SSTable 수)
```

- 진단 흐름: 쓰기 정지·SSD 마모 → WA부터. 디스크 부족 → SA와 병합 중 임시 공간. 조회 p99 → 조회당 run 수·L0 파일 수.

### 4. 코테·면접에서 묻는 형태

- "쓰기가 초당 수십만 건인 로그 저장소에 어떤 compaction?" → 티어 계열 + 블룸 필터, 조회는 최근 데이터 위주라 run 수를 감수. TTL이면 시간 창.
- "같은 키를 자주 갱신하는 카운터 테이블?" → 레벨 계열. 티어면 옛 버전이 여러 run에 남아 공간·조회가 나빠진다(실험 update-heavy SA 3.47~4.37).

## 장애 시나리오와 대처

### 1. 쓰기 위주 워크로드에 레벨 방식 → 쓰기 증폭 폭증 (⚠ 커리큘럼)

- **현상**: 수집 서버의 SSD 쓰기량이 앱 쓰기량의 수십 배, SSD 마모 지표가 빨리 오른다. 피크 때 쓰기 지연이 튄다.
- **보이는 형태**: `iostat`의 쓰기 MB/s ÷ 앱 쓰기 MB/s가 크다. RocksDB Compaction Stats의 레벨별 W-Amp 합이 크다. compaction 대기 바이트 증가, write stall 로그(database/38).
- **원인**: 레벨 방식은 엔트리당 O(T·L)번 다시 쓴다(시뮬레이션에서 티어의 2.3~4.7배). 쓰기 비율이 높으면 그대로 디스크 대역폭이 된다.
- **대처**: 티어·하이브리드로 바꾸거나 T·memtable 크기를 조정한다(memtable을 키우면 L0 파일이 커지고 레벨 수가 준다). 시간 순 + TTL이면 TWCS·FIFO.

### 2. 갱신·삭제 많은 테이블에 티어 방식 → 공간 증폭 폭증 (⚠ 커리큘럼)

- **현상**: (예시) 논리 데이터는 100GB인데 디스크는 300GB 넘게 쓴다. 삭제해도 공간이 안 준다.
- **보이는 형태**: 디스크 사용량 ÷ 논리 크기가 크다(시뮬레이션 update-heavy 티어 3.47~4.37). SSTable 수가 많고 큰 SSTable끼리 오래 병합되지 않는다.
- **원인**: 티어는 같은 키의 옛 버전·tombstone이 여러 run에 남아 있다가, 같은 크기대 run이 T개 모여야 정리된다. 가장 큰 run들은 드물게 합쳐진다.
- **대처**: 레벨(LCS·Level)로 바꾸거나, Universal의 `max_size_amplification_percent`처럼 공간 증폭 상한으로 병합을 강제하는 설정을 쓴다. 삭제가 많으면 tombstone 정리 조건을 본다(database/38 §5).

### 3. 큰 run 병합 중 디스크가 찬다

- **현상**: 평소 디스크 50%인데 compaction 중 100%에 닿아 쓰기가 실패한다.
- **보이는 형태**: `No space left on device`, 병합 중 임시 출력 파일, 디스크 사용량 톱니 모양.
- **원인**: 병합 중에는 입력 run과 출력 run이 동시에 존재한다. 티어 방식은 가장 큰 run들을 통째로 합칠 때 일시적으로 2배까지 필요하다(RocksDB Tuning Guide — Universal, database/38 장애). 원본 노트도 "병합 중에는 원본과 결과물이 동시에 존재한다"를 공간 증폭 항목에 적었다.
- **대처**: 디스크 여유를 "평소 크기"가 아니라 "가장 큰 병합 시 최대"로 잡는다. 데이터를 여러 인스턴스·column family로 나눠 한 번의 병합 크기를 줄인다. 레벨 방식은 파일 단위로 조금씩 병합해 순간 필요 공간이 작다(Cassandra LCS 문서: STCS만큼 디스크를 먹지 않고 실행에 디스크의 약 10%만 필요).

### 4. 읽기 위주 워크로드에 티어 방식 → 조회 p99 상승

- **현상**: 쓰기는 빠른데 조회 지연 꼬리가 길다. 특히 없는 키 조회와 범위 조회가 느리다.
- **보이는 형태**: 조회당 SSTable 수 증가(`nodetool tablehistograms`), 블룸 필터 오탐으로 인한 불필요한 블록 읽기, 범위 스캔 시 run 수만큼 병합 반복자.
- **원인**: run이 (T−1)·L개까지 있어 범위 조회는 run마다 한 번씩 읽는다. 전체 키 블룸 필터는 점 조회만 돕고 범위 조회는 못 돕는다(database/38 §2). 예외로 RocksDB의 접두사(prefix) 블룸 필터는 한 접두사 안의 범위 `Seek`에서 그 접두사가 없는 run을 건너뛰게 해 준다(RocksDB wiki Prefix-Seek).
- **대처**: 레벨·하이브리드로, 또는 티어의 T를 줄인다. 점 조회 위주면 블룸 필터 비트를 늘린다.

### 5. 운영 중 전략을 바꿨더니 대량 compaction이 돈다

- **현상**: `ALTER TABLE … WITH compaction = {LCS}` 직후 몇 시간 동안 디스크·CPU가 포화되고 지연이 오른다.
- **보이는 형태**: compaction 대기 작업 수 급증(`nodetool compactionstats`), 디스크 쓰기 급증.
- **원인**: 기존 run 모양(티어)이 새 정책의 불변식(레벨마다 겹치지 않는 run)과 달라 데이터 상당 부분을 다시 병합해야 한다. [?: Cassandra 공식 문서에서 "전략 전환 시 전체 재병합" 문구는 확인하지 못함 — 원리상 추론과 운영 사례 글 근거]
- **대처**: 트래픽이 낮을 때, 노드 하나씩 바꾸고(Cassandra 문서: JMX로 한 노드에서만 전략을 바꿔 볼 수 있다) compaction 처리량 상한을 둔다. 바꾸기 전에 디스크 여유(최대 병합 크기)를 확보한다.

## 핵심 문장

- 병합 정책은 쓰기·읽기·공간 증폭 중 무엇을 내줄지의 선택이다. 셋 다 최소인 정책은 없다.
- 레벨 방식은 레벨마다 run 하나라 조회·공간이 싸고, 엔트리가 레벨마다 O(T)번 다시 쓰여 쓰기 증폭이 O(T·L)이다.
- 티어 방식은 레벨마다 run이 T−1개까지 쌓였다가 T개째에 한꺼번에 합쳐져 쓰기 증폭이 O(L)로 작고, 조회는 run 수만큼, 공간은 옛 버전만큼 비싸다.
- 크기 비율 T가 손잡이다. T=2에서 두 정책은 수렴하고, T가 커질수록 두 정책은 반대 방향으로 벌어진다.
- 실제 엔진은 하이브리드 쪽으로 간다. RocksDB 기본 Level은 L0 티어 + 나머지 레벨이고, Cassandra는 기본값이 STCS지만 새 워크로드에는 레벨·티어를 한 손잡이로 묶은 UCS를 권한다.

참고: 원본 「세 가지 증폭의 트레이드오프」 표의 "읽기 증폭 낮음(레벨당 파일 1개)"은 "레벨당 sorted run 1개"가 맞다. L1 이상은 키 범위로 나뉜 파일 여러 개가 run 하나를 이루고, L0는 겹치는 파일 여러 개다(RocksDB wiki Leveled Compaction).\
참고: 원본 「[Claude 추가]」의 "append-only + 불변이라는 발상은 SSD 내부 FTL과 정확히 같다"는 과장이다. 제자리 덮어쓰기를 피하고 나중에 모아 정리(GC·compaction)하는 발상은 같지만, FTL은 페이지·블록 단위 주소 변환과 지우기 단위 제약을 다루고 키 정렬·병합을 하지 않는다 → [systems/nand-flash](../../systems/nand-flash/2-summary.md).

## 관련 주제·근거

- 선행
  - 원본 [data-structure/lsm-merge-model](../lsm-merge-model/2-summary.md) — 정렬 시점, 병합 비용 = 자원 경쟁, 복제와 병합
  - [data-structure/24-lsm-tree](../24-lsm-tree/2-summary.md) — LSM 구조와 구현(커리큘럼 선행 18)
- 후속·연결
  - [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md) — RocksDB 기본값, 증폭 측정, write stall, tombstone
  - [database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md) — 파트 병합과 "Too many parts"
  - [algorithm/11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md) — compaction의 본체인 k-way 병합
  - [data-structure/11-bloom-filter](../11-bloom-filter/2-summary.md) — run 수를 버티게 하는 필터
  - [systems/lsm-tree](../../systems/lsm-tree/2-summary.md) — RUM 추측, Leveled vs Size-tiered 기초
  - [systems/nand-flash](../../systems/nand-flash/2-summary.md) — 장치 쪽 쓰기 증폭(FTL·GC)
- 논문·문서
  - O'Neil, Cheng, Gawlick, O'Neil, "The Log-Structured Merge-Tree (LSM-Tree)", Acta Informatica 33(4), 1996
  - Dayan, Idreos, "Dostoevsky: Better Space-Time Trade-Offs for LSM-Tree Based Key-Value Stores via Adaptive Removal of Superfluous Merging", SIGMOD 2018 — 레벨 O(T·L/B)·티어 O(L/B) 갱신 비용, 공간 증폭 O(1/T)·O(T), T=2 수렴·T_lim 퇴화, lazy leveling <https://nivdayan.github.io/dostoevsky.pdf>
  - Dayan, Athanassoulis, Idreos, "Monkey: Optimal Navigable Key-Value Store", SIGMOD 2017 — 블룸 필터 메모리 배분과 점 조회 비용
  - RocksDB wiki: Compaction(Leveled·Tiered·Tiered+Leveled·FIFO), Leveled Compaction(L0 겹침, 파일 단위 병합, dynamic level bytes 90%·9%), Universal Compaction, Compaction Stats and DB Status(W-Amp) <https://github.com/facebook/rocksdb/wiki/Compaction>
  - RocksDB `include/rocksdb/advanced_options.h`(`max_bytes_for_level_multiplier` 10, `level_compaction_dynamic_level_bytes` true, `compaction_style` 기본 Level), `universal_compaction.h`(`size_ratio` 1, `min_merge_width` 2, `max_size_amplification_percent` 200) — main 브랜치, 2026-10-05 조회
  - Apache Cassandra 문서(latest): Compaction overview(UCS·STCS 기본·LCS·TWCS), LCS(`sstable_size_in_mb` 160, `fanout_size` 10, L0 32개 초과 시 STCS 폴백) <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/overview.html>
- 실험 목록
  - 레벨 vs 티어 병합 정책 시뮬레이션(`lsm_sim.py`) — 호스트 Python 3.12.3, N=1,000,000·버퍼 4,000·T=2·4·8·10·16, 새 키만 / 키 10만 개 덮어쓰기, 2026-10-05. 실제 엔진이 아닌 단순 모델(레벨 전체 병합, 블룸 필터·삭제 없음)
