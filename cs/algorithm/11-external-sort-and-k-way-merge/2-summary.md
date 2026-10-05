# algorithm/11-external-sort-and-k-way-merge — 외부 정렬과 k-way 병합 — 정리 (힌트)

## 해결하는 문제

메모리에 올릴 수 있는 것보다 큰 데이터를 정렬해야 할 때가 있다.

```text
  메모리 64MB  <  정렬할 파일 128MB

  long[] all = new long[16_000_000];      → java.lang.OutOfMemoryError: Java heap space
```

- 메모리 안 정렬(퀵·병합·TimSort)은 "전부 메모리에 있다"를 전제한다.
- 디스크는 크지만 느리고, 임의 접근보다 순차 접근이 훨씬 싸다(HDD는 탐색 시간, SSD도 큰 블록 순차가 유리).
- 그래서 **메모리에 들어가는 조각만 정렬해 디스크에 두고(런), 정렬된 조각들을 순차로 읽으며 합친다(병합).**
  - *외부 정렬(external sort)*: 입력 전체가 주기억장치에 안 들어갈 때 보조기억장치(디스크)를 써서 하는 정렬.
  - *런(run)*: 정렬된 연속 조각. 외부 정렬의 중간 산출물이다.
  - *k-way 병합*: 정렬된 런 k개의 맨 앞 원소만 보고 가장 작은 것을 차례로 꺼내 하나의 정렬된 출력으로 합치는 것.

쉬운 예: 시험지 1,000장을 번호순으로 정리하는데 책상에 100장만 펼칠 수 있다.
- 100장씩 가져와 책상에서 정렬해 바닥에 묶음으로 쌓는다(런 10개).
- 10묶음의 맨 위 장만 보고 가장 작은 번호를 집어 낸다. 집은 묶음에서 다음 장을 올린다.

똑같은 구조다.\
실무 예:
- PostgreSQL에서 정렬이 `work_mem`(17판 기본 4MB)을 넘으면 `EXPLAIN ANALYZE`에 `Sort Method: external merge  Disk: …kB`가 찍힌다 → DB 쪽 동작은 [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md).
- LSM 저장 엔진의 compaction은 정렬된 SSTable 여러 개를 k-way 병합한다 → [data-structure/19-lsm-merge-model](../../data-structure/19-lsm-merge-model/2-summary.md).
- Hadoop MapReduce는 맵 출력을 메모리 버퍼(`mapreduce.task.io.sort.mb` 기본 100MB)에서 정렬해 디스크로 흘리고(spill), 한 번에 `mapreduce.task.io.sort.factor`(기본 10)개 스트림씩 병합한다(`mapred-default.xml`).

이 노트는 **알고리즘**(런 만들기, k-way 병합, 패스 수와 I/O, 팬인 선택)에 집중한다. DB 제품별 한도·계획 읽기는 database/41이 맡는다.

## 동작·원리

### 1. 두 단계 — 런 만들기와 병합

```text
  입력 파일 (N 블록)                      메모리 B 블록
  ┌────────────────────────────────┐
  │ 5 1 9 … │ 8 2 7 … │ 3 6 4 … │ …│
  └────────────────────────────────┘
        │ ① 런 만들기: B 블록씩 읽어 메모리에서 정렬 → 디스크에 쓰기
        ▼
  run0 [1 5 9 …]   run1 [2 7 8 …]   run2 [3 4 6 …]   …   ⌈N/B⌉개
        │ ② 병합: 각 런의 맨 앞만 메모리에 두고 최솟값을 계속 꺼낸다
        ▼            (입력 버퍼 k개 + 출력 버퍼 1개)
  ┌─────────────── 최소 힙 (k개) ────────────────┐
  │           (1,run0)                         │   pop → 출력
  │      (2,run1)    (3,run2)                  │   run0의 다음 값 5를 push
  └────────────────────────────────────────────┘
        ▼
  출력 [1 2 3 4 5 6 7 8 9 …]
```

- 런이 k개보다 많으면 병합을 여러 **패스**로 나눈다. 한 패스 = 데이터 전체를 한 번 읽고 한 번 쓰는 것.
  - *패스(pass)*: 데이터 전체를 한 번 훑어 읽고 쓰는 단위.
  - *팬인(fan-in)*: 한 번의 병합이 동시에 합치는 런 수 k. 메모리가 B 블록이면 런마다 입력 블록 1개 + 출력 1개라 k ≤ B − 1이다.

### 2. 패스 수와 I/O 비용 (CMU 15-445 Fall 2024 L11)

```text
  런 수        R = ⌈N / B⌉
  병합 패스     ⌈log_k R⌉            (k = 팬인, 최대 B − 1)
  총 패스      1 + ⌈log_(B−1) ⌈N/B⌉⌉
  총 I/O       2N × (총 패스)         (패스마다 N 블록 읽기 + N 블록 쓰기)

  예: 런 8개
    k = 8  →  8 → 1                     병합 패스 1
    k = 4  →  8 → 2 → 1                 병합 패스 2
    k = 2  →  8 → 4 → 2 → 1             병합 패스 3   (2-way 외부 병합 정렬: 1 + ⌈log₂ N⌉ 패스)
```

- 팬인을 키우면 패스가 줄어 디스크 I/O가 준다. 대신 런마다 받는 버퍼가 작아져 읽기가 잘게 쪼개진다(HDD에서는 탐색이 늘어난다).
- Hadoop 문서가 `io.sort.factor`를 "한 번에 병합하는 스트림 수 = 여는 파일 핸들 수"라고 적는 것도 같은 맞바꿈이다.
- 마지막 패스 결과를 디스크에 쓰지 않고 바로 소비자에게 흘리면 쓰기 한 번을 아낀다(PostgreSQL `tuplesort.c`가 이렇게 한다 — database/41 참고).

### 실험: 메모리(-Xmx64m)보다 큰 파일 정렬, 팬인별 패스 수

128MB 무작위 `long` 파일(1,600만 개)을 64MB 힙에서 정렬했다. 런은 200만 개(16MB)씩.

```java
// 1단계: chunk개씩 읽어 정렬해 런 파일로
while (true) {
    int n = 0;
    try { while (n < chunk) buf[n++] = is.readLong(); } catch (EOFException e) { n--; if (n < 0) n = 0; }
    if (n == 0) break;
    Arrays.sort(buf, 0, n);
    try (DataOutputStream os = out(run)) { for (int i = 0; i < n; i++) os.writeLong(buf[i]); }
    if (n < chunk) break;
}
// 2단계: 런 k개의 맨 앞만 힙에 — {값, 런 번호}
PriorityQueue<long[]> heap = new PriorityQueue<>((x, y) -> Long.compare(x[0], y[0]));
for (int i = 0; i < ins.length; i++) heap.add(new long[]{ins[i].readLong(), i});
while (!heap.isEmpty()) {
    long[] top = heap.poll();
    os.writeLong(top[0]);
    try { top[0] = ins[(int) top[1]].readLong(); heap.add(top); } catch (EOFException e) { }
}
// 런이 k보다 많으면 k개씩 묶어 병합하는 패스를 런이 1개 될 때까지 반복
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `-Xmx64m`, 입력 128,000,000바이트, 2026-10-05)

```text
$ java -Xmx64m InMem.java data/in.bin
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
	at InMem.main(InMem.java:5)
	...

$ java -Xmx64m ExtSort.java data/in.bin 2000000 8
입력 128,000,000바이트, 런 8개 (런당 최대 16,000,000바이트)
병합 패스 1: 런 8개 → 1개
병합 패스 1회, 디스크에 쓴 바이트 256,000,000 (입력의 2.0배), 12024ms
검증: 정렬됨=true 개수 16,000,000/16,000,000 합 일치=true

$ java -Xmx64m ExtSort.java data/in.bin 2000000 4
병합 패스 1: 런 8개 → 2개
병합 패스 2: 런 2개 → 1개
병합 패스 2회, 디스크에 쓴 바이트 384,000,000 (입력의 3.0배), 15409ms

$ java -Xmx64m ExtSort.java data/in.bin 2000000 2
병합 패스 1: 런 8개 → 4개
병합 패스 2: 런 4개 → 2개
병합 패스 3: 런 2개 → 1개
병합 패스 3회, 디스크에 쓴 바이트 512,000,000 (입력의 4.0배), 17092ms
```

- 같은 메모리에서 전부 올리는 정렬은 OOM, 외부 정렬은 개수·합·정렬 여부 검증을 통과했다.
- 쓴 바이트는 (1 + 병합 패스) × 입력이다. 표의 공식 2N × 패스의 "쓰기" 절반과 맞는다.
- 시간은 두 번째 실행에서 k=8 12,175ms, k=2 15,427ms였다(사실 점검 재실행: k=8 10,384ms, k=4 12,814ms, k=2 14,658ms). 실행마다 다르고, 파일이 페이지 캐시에 머물러 실제 디스크 I/O가 일부만 일어났을 수 있다(해석 — 측정 환경 한정). 결정적인 지표는 패스 수와 쓴 바이트다.

### 3. k-way 병합에서 최솟값 찾기 — 선형 vs 힙

```text
  선형 탐색: 매 출력마다 k개 머리를 다 비교             → 원소당 k − 1 비교
  최소 힙  : 루트가 최솟값, pop 후 다음 값 push          → 원소당 O(log k) 비교
  토너먼트/패자 트리(loser tree): 이긴 경로만 다시 겨룸    → 원소당 약 ⌈log₂ k⌉ 비교 (Knuth TAOCP 3권 5.4.1)
```

(실험, 같은 환경, `java KCmp.java`, 원소 2²⁰개를 k개 런으로 나눔, 2026-10-05)

```text
k=  2  원소당 비교: 선형 1.00  힙 1.00  (log2 k = 1)
k=  8  원소당 비교: 선형 7.00  힙 5.87  (log2 k = 3)
k= 64  원소당 비교: 선형 63.00  힙 11.77  (log2 k = 6)
k=512  원소당 비교: 선형 510.75  힙 17.22  (log2 k = 9)
```

- k가 작으면 둘이 비슷하고, k가 커지면 선형이 k에 비례해 늘어난다.
- `PriorityQueue`는 `poll`(아래로 내리기) + `add`(위로 올리기)를 따로 해서 원소당 약 2 log₂ k 비교가 들었다. 루트를 바꿔 끼우고 한 번만 내리면(replace-top) 줄어든다.

### 4. 런을 더 길게 — 대체 선택(replacement selection)

```text
  메모리 M개짜리 최소 힙
  ① 힙에서 최솟값을 꺼내 현재 런에 쓴다 (마지막 출력값 last 갱신)
  ② 입력에서 다음 값 v를 읽는다
       v ≥ last → 이번 런에 넣을 수 있다   → 힙에 (현재 런 번호, v)
       v < last → 이번 런에는 늦었다        → 힙에 (다음 런 번호, v)
  ③ 힙 전체가 "다음 런"이면 런을 끊는다
```

- 무작위 입력에서 런 길이 평균이 메모리 크기의 약 2배가 된다(Knuth TAOCP 3권 5.4.1).
- 이미 정렬된 입력은 런 하나, 역순 입력은 메모리 크기 그대로다.

(실험, 같은 환경, `java RunGen.java`, n=2,000,000, M=10,000, 2026-10-05 — 메모리 안 시뮬레이션)

```text
random   n=2,000,000 M=10,000  잘라서 정렬: 런 200개(평균 10,000) | 대체 선택: 런 101개(평균 19,801)
sorted   n=2,000,000 M=10,000  잘라서 정렬: 런 200개(평균 10,000) | 대체 선택: 런 1개(평균 2,000,000)
reversed n=2,000,000 M=10,000  잘라서 정렬: 런 200개(평균 10,000) | 대체 선택: 런 200개(평균 10,000)
```

- 런이 절반이면 병합 패스가 줄 수 있다(팬인이 런 수 근처일 때).
- 대신 힙에 원소를 하나씩 넣고 빼니 캐시 지역성이 나빠 런 만들기 CPU가 "잘라서 퀵소트"보다 무거울 수 있다. PostgreSQL은 9.6에서 외부 정렬 런 만들기를 퀵소트로 바꿨다. 릴리스 노트의 이유는 "전형적인 캐시 크기·데이터 양에서 CPU 캐시를 더 잘 쓴다"이다. 대체 선택은 정렬할 튜플 수가 `replacement_sort_tuples`(기본 150,000)보다 작을 때 **첫 런**에만 남겼다(9.6 문서 19.4). 11에서 그 설정을 없앴다 — "Replacement sorts were determined to be no longer useful"(PostgreSQL 11.0 릴리스 노트).

## 쓰이는 자료구조·알고리즘

- **이 주제가 쓰는 하위 구조**
  - 최소 힙(우선순위 큐) — k-way 병합, 대체 선택 → [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
  - 2-way 병합 — 병합의 원형 → [algorithm/02-merge-sort](../02-merge-sort/2-summary.md)
  - 메모리 안 정렬 — 런 만들기 → [09-sorting-in-practice](../09-sorting-in-practice/2-summary.md), [03-quick-sort](../03-quick-sort/2-summary.md)
  - 버퍼(블록 단위 읽기·쓰기) — 순차 I/O → [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md)
- **이 주제를 쓰는 곳(🔧)**
  - DB `ORDER BY`·`GROUP BY`·`DISTINCT`·정렬 병합 조인 → [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md), [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md)
  - LSM compaction → [data-structure/19-lsm-merge-model](../../data-structure/19-lsm-merge-model/2-summary.md), [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)
  - MapReduce·Spark shuffle의 정렬 기반 spill·merge
  - 대사(reconciliation): 내부 원장과 외부 거래 파일을 같은 키로 정렬해 나란히 훑기
  - 유닉스 `sort` 명령: 큰 입력은 임시 파일로 나눠 병합한다(GNU coreutils `sort`의 `-S`(버퍼 크기)·`--batch-size`(한 번에 병합할 입력 수)·`-T`(임시 디렉터리) 옵션) [?: 버전별 기본값은 확인하지 않음]

## 적용 — 풀어나가는 법

### 1. 설계 순서

```text
  ① 메모리 예산 M을 정한다             (힙 전체가 아니라 정렬에 쓸 몫)
  ② 런 크기 ≈ M → 런 수 R = ⌈N / M⌉
  ③ 팬인 k: 런마다 버퍼 ≥ 수백 KB~수 MB가 되게 → k ≈ M / 버퍼
  ④ 병합 패스 = ⌈log_k R⌉  → 1이면 이상적
  ⑤ 임시 디스크 = 입력 × (1~2배) 확보, 끝나면 지운다
  ⑥ 검증: 개수·합(체크섬)·단조성 (값끼리 상쇄된 오류는 원소별 개수 비교로)
```

- 계산 예 (예시): 입력 100GB, 메모리 1GB → 런 100개. 런당 버퍼 8MB면 k ≈ 128 ≥ 100 → 병합 1패스. 총 읽기·쓰기 각 2번(런 만들기 1 + 병합 1).

### 2. 코테·면접 — k개 정렬 리스트 병합

```java
// LeetCode 23 "Merge k Sorted Lists" 형태: O(N log k)
ListNode mergeKLists(ListNode[] lists) {
    PriorityQueue<ListNode> pq = new PriorityQueue<>(Comparator.comparingInt(n -> n.val));
    for (ListNode h : lists) if (h != null) pq.add(h);
    ListNode dummy = new ListNode(0), tail = dummy;
    while (!pq.isEmpty()) {
        ListNode n = pq.poll();
        tail.next = n; tail = n;
        if (n.next != null) pq.add(n.next);
    }
    return dummy.next;
}
```

- "정렬된 것 k개를 합친다"를 보면 힙 + 각 머리를 떠올린다. 전부 모아 다시 정렬하면 O(N log N)이다.

### 3. 실무 — 큰 CSV를 키로 정렬해 대사하기

```text
  내부 원장.csv (2억 행)          외부 정산.csv (2억 행)
        │ 외부 정렬 (키=거래ID)            │ 외부 정렬
        ▼                                ▼
  정렬된 원장 ──────── 두 포인터로 나란히 읽기 ──────── 정렬된 정산
                 같은 키: 금액 비교 / 한쪽만: 누락 보고
```

- 정렬 병합 방식은 메모리를 거의 안 쓰고 두 파일을 한 번씩만 읽는다. 해시 조인은 한쪽이 메모리에 들어갈 때 유리하다.
- 셸로 끝낼 수 있으면 `sort -t, -k1,1 -S 1G -T /big/tmp`처럼 버퍼와 임시 디렉터리를 정해 쓴다. 기본 임시 디렉터리(`/tmp`)가 작은 tmpfs이면 디스크가 찬다.

### 4. 진단

- JVM: `OutOfMemoryError: Java heap space`가 정렬 코드에서 나면 "전체를 메모리에"를 의심한다. `jcmd <pid> GC.heap_info`로 힙 한도를 확인한다.
- DB: 계획에 `external merge`, `Disk:` 크기, 임시 파일 통계(`pg_stat_database.temp_bytes`) → database/41 §적용.
- 디스크: `iostat -x 1`에서 정렬 중 쓰기량이 입력의 몇 배인지 본다 → (1 + 병합 패스) 배 근처면 패스 수를 줄일 여지가 있다.

## 장애 시나리오와 대처

### 1. 정렬 메모리 초과 → 디스크 스필로 쿼리가 느려진다 (⚠ 커리큘럼)

- **현상**: 대시보드 쿼리가 평소보다 수십 배 느리다.
- **보이는 형태**: `Sort Method: external merge  Disk: 26936kB`(PostgreSQL), 임시 파일 증가, 디스크 쓰기 급증.
- **원인**: 정렬 대상이 연산당 메모리 한도(`work_mem` 등)를 넘어 런 만들기 + 병합 패스로 넘어갔다. 패스마다 데이터 전체를 다시 읽고 쓴다(PostgreSQL은 마지막 병합 결과를 디스크에 쓰지 않고 호출자에게 바로 넘긴다 — `tuplesort.c` 머리 주석 "final merge is then performed on-the-fly").
- **대처**: 정렬 대상 줄이기(필요한 열만, `LIMIT` → Top-N 힙), 정렬 순서와 맞는 인덱스, 세션·쿼리 단위로 메모리 올리기. 전역으로 올리면 동시 쿼리 수만큼 곱해진다 → database/41 장애 2.
  - database/41의 로컬 재현에서는 스필이 곧 느림은 아니었다(페이지 캐시). "스필 = 수십 배"는 디스크가 실제로 읽히고 패스가 여러 번일 때다.

### 2. 전체를 메모리에 올리다 OOM

- **현상**: 월말 배치에서 `OutOfMemoryError`로 작업이 죽는다. 평소 데이터에서는 된다.
- **보이는 형태**: `java.lang.OutOfMemoryError: Java heap space`, 컨테이너면 OOMKilled → [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md).
- **원인**: `readAllLines` → `sort` 같은 메모리 안 정렬. 데이터가 자라면 한도를 넘는다. 병합 정렬 계열은 추가 버퍼까지 든다.
- **대처**: 외부 정렬(실험: `-Xmx64m`에서 128MB 정렬 성공) 또는 DB에 정렬을 맡긴다. 메모리 예산을 고정하고 입력 크기와 무관하게 만든다.

### 3. 팬인이 작아 패스가 많다

- **현상**: 외부 정렬이 디스크를 오래 점유한다.
- **보이는 형태**: 쓴 바이트가 입력의 여러 배(실험: k=2에서 4.0배, k=8에서 2.0배). 로그에 병합 패스가 여러 번.
- **원인**: 팬인 k를 너무 작게(기본값 그대로) 두었다.
- **대처**: 메모리 안에서 k를 키운다. 단 런마다 버퍼가 너무 작아지면 읽기가 잘게 쪼개지니 균형을 맞춘다. 파일 핸들 한도(`ulimit -n`)도 확인한다.

### 4. 임시 공간이 디스크를 채운다

- **현상**: 정렬 작업 중 같은 디스크를 쓰는 다른 서비스가 `No space left on device`로 실패한다.
- **보이는 형태**: 임시 디렉터리 급증, `df`에서 100%.
- **원인**: 런 파일 + 병합 출력이 동시에 존재해 입력의 약 2배 공간이 필요하다. 중간에 죽으면 임시 파일이 남는다.
- **대처**: 임시 디렉터리를 전용 볼륨으로(`sort -T`, DB `temp_tablespaces`), 임시 파일 크기 상한(PostgreSQL `temp_file_limit`), 병합이 끝난 런은 바로 지운다(실험 코드도 병합 직후 삭제).

### 5. 병합 결과가 조용히 틀린다

- **현상**: 정렬된 파일의 행 수가 입력보다 적다. 아무 에러도 없다.
- **보이는 형태**: 대사 차이가 갑자기 늘어난다.
- **원인**: 마지막 덜 찬 런을 버리는 경계 버그, EOF 처리 실수, 런마다 다른 비교자(로캘·대소문자)로 정렬 → 병합 전제(각 런이 같은 순서로 정렬됨)가 깨진다.
- **대처**: 끝에 개수·합·단조성을 검증한다(실험 코드의 "검증" 줄). 이 셋은 누락·순서 오류를 싸게 잡는 검사일 뿐, 통과해도 원소가 보존됐다는 증명은 아니다(입력 `[1,2,3,4]` → 출력 `[1,1,4,4]`도 통과). 완전히 확인하려면 원소별 개수(다중집합)까지 비교한다. 비교자를 한 곳에서 정의해 런 만들기와 병합이 같은 것을 쓰게 한다.

## 핵심 문장

- 외부 정렬은 "메모리만큼 정렬해 런으로 쓰기"와 "런 k개를 힙으로 병합하기" 두 단계다.
- 비용은 비교가 아니라 패스 수다. 총 I/O ≈ 2N × (1 + ⌈log_k ⌈N/B⌉⌉)이고, 팬인 k를 키우면 패스가 준다.
- k-way 병합은 최소 힙으로 원소당 O(log k) 비교, 선형 탐색이면 k − 1 비교다.
- 대체 선택은 무작위 입력에서 런 길이를 메모리의 약 2배로 늘린다.
- 런 파일과 출력이 공존해 임시 공간이 입력의 약 2배 든다. 결과는 개수·합·단조성으로 1차 검증한다(완전한 검증은 원소별 개수 비교).

## 관련 주제·근거

- 선행
  - [algorithm/02-merge-sort](../02-merge-sort/2-summary.md) — 2-way 병합(커리큘럼 선행 06)
  - [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) — 최소 힙(커리큘럼 선행 ds 10)
  - [algorithm/09-sorting-in-practice](../09-sorting-in-practice/2-summary.md) — 비교자 계약
- 후속·연결
  - [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md) — DB의 외부 정렬·Top-N·해시 집계·스필
  - [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md) — 정렬 병합 조인
  - [data-structure/19-lsm-merge-model](../../data-structure/19-lsm-merge-model/2-summary.md), [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md), [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md) — compaction = k-way 병합
  - [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md) — 측정 시간이 페이지 캐시에 좌우되는 이유
  - [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md)
- 교재·문서
  - CMU 15-445/645 Fall 2024 Lecture #11 Sorting & Aggregation Algorithms — 2-way 외부 병합 정렬 1 + ⌈log₂ N⌉ 패스, 일반 1 + ⌈log_(B−1)⌈N/B⌉⌉, I/O 2N × 패스, 이중 버퍼링, B+tree로 정렬 대체 <https://15445.courses.cs.cmu.edu/fall2024/notes/11-sorting.pdf>
  - Knuth, TAOCP 3권 5.4 External Sorting — 5.4.1 다방향 병합과 대체 선택(무작위 입력에서 런 길이 약 2배), 토너먼트(패자) 트리
  - PostgreSQL 9.6.0 릴리스 노트 — 외부 정렬 런을 퀵소트로(CPU 캐시) <https://www.postgresql.org/docs/release/9.6.0/>, 9.6 문서 19.4 `replacement_sort_tuples`(기본 150,000, 첫 런만) <https://www.postgresql.org/docs/9.6/runtime-config-resource.html>
  - PostgreSQL 11.0 릴리스 노트 — `replacement_sort_tuples` 제거 <https://www.postgresql.org/docs/release/11.0/>
  - CLRS 3판 6.5 연습 6.5-9(k개 정렬 리스트를 힙으로 O(n lg k)에 병합), 2.3(병합)
  - Apache Hadoop `mapred-default.xml` — `mapreduce.task.io.sort.factor` 10, `mapreduce.task.io.sort.mb` 100, `mapreduce.map.sort.spill.percent` 0.80 <https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/mapred-default.xml>
- 실험 목록(모두 2026-10-05, OpenJDK 21.0.12 Temurin, docker `--cpus=2`)
  - `-Xmx64m`에서 128MB `long` 파일: 메모리 안 정렬 OOM(`InMem.java`) vs 외부 정렬 팬인 8·4·2(`ExtSort.java`, 런 8개, 패스·쓴 바이트·검증, 두 번 실행)
  - k-way 병합 원소당 비교 수: 선형 vs `PriorityQueue`(`KCmp.java`, k = 2·8·64·512)
  - 런 만들기: 잘라서 정렬 vs 대체 선택(`RunGen.java`, 무작위·정렬·역순)
