# sorting-and-graph — 정렬 6종·그래프 탐색 4종을 리소스 제한 컨테이너에서 실측

- 원본: `/home/jun/project/sorting-and-graph` · 기간: 2026-01-17 ~ 2026-01-20 (git 커밋 기준) · 스택: Java 21 + Spring Boot 3.5.0, Gradle 8.x, Docker (리소스 제한 프로필)
- 상태: **완료** (정렬·그래프 벤치마크 문서 + 알고리즘별 개념 문서)

## 무엇을 알고 싶었나 — 질문·가설

- O(n log n) vs O(n²)의 시간복잡도 차이가 **실제 실행 시간으로 얼마나 벌어지는가**.
- 데이터 상태(RANDOM / NEARLY_SORTED / REVERSED)가 각 정렬 알고리즘 성능에 어떤 영향을 주는가 (특히 Insertion Sort).
- 그래프 탐색 4종(DFS 재귀/반복, BFS, Bidirectional BFS)은 모두 O(V+E)인데, 실측에서도 비슷한가.
- 메모리 vs 속도 트레이드오프(Merge Sort의 O(n) 추가 메모리 vs Heap Sort의 in-place)를 수치로 확인.

## 실험 환경과 방법

| 항목 | 값 |
|------|-----|
| 실행 형태 | Spring Boot API 서버 2개(sorting :8081~8083, graph :8091~8093)를 Docker로 기동, `GET /api/sort/benchmark`·`GET /api/graph/benchmark` 호출 |
| 리소스 프로필 | low(1 core/256MB) · medium(2 cores/512MB) · high(4 cores/1GB) |
| 정렬 입력 | dataSize 10,000 / 50,000 / 100,000 · dataType RANDOM / NEARLY_SORTED / REVERSED |
| 그래프 입력 | nodeCount 1,000 / 100,000 · RANDOM · SPARSE(간선 수 = 노드 수) |

## 결과

### 정렬 — 100,000개 RANDOM, Low 리소스 (256MB, 1 core)

| 순위 | 알고리즘 | 실행 시간 | 메모리 사용 |
|-----|---------|----------|------------|
| 1 | Quick Sort | 7.6ms | 0KB |
| 2 | Merge Sort | 9.8ms | 10,502KB |
| 3 | Heap Sort | 10.9ms | 0KB |
| 4 | Insertion Sort | 463ms | 0KB |
| 5 | Selection Sort | 4,089ms | 206KB |
| 6 | Bubble Sort | 14,033ms | 206KB |

출처: `/home/jun/project/sorting-and-graph/docs/sorting/BENCHMARK.md`

### 정렬 — O(n²) vs O(n log n) 증가율 (RANDOM)

| 데이터 크기 | Quick Sort | Bubble Sort | 배율 차이 |
|------------|------------|-------------|----------|
| 10,000 | 1.9ms | 54ms | 28배 |
| 50,000 | 3.5ms | 3,238ms | 925배 |
| 100,000 | 7.6ms | 14,033ms | 1,846배 |

출처: `/home/jun/project/sorting-and-graph/docs/sorting/BENCHMARK.md`

원본 관찰: 10,000→50,000 (5배)에서 Quick Sort는 이론(≈5.8배)보다 좋은 1.8배(캐시 효율), Bubble Sort는 이론(25배)보다 나쁜 60배.

### 정렬 — 데이터 상태별 (10,000개)

| 알고리즘 | RANDOM | NEARLY_SORTED | REVERSED |
|---------|--------|---------------|----------|
| Merge Sort | 1.6ms | 0.4ms | 0.3ms |
| Quick Sort | 1.9ms | 0.5ms | 0.3ms |
| Heap Sort | 2.1ms | 0.7ms | 0.7ms |
| Insertion Sort | 29.7ms | **3.8ms** | 15.8ms |
| Selection Sort | 42.2ms | 34.3ms | 28.1ms |
| Bubble Sort | 54.1ms | 28.7ms | 72.4ms |

출처: `/home/jun/project/sorting-and-graph/docs/sorting/BENCHMARK.md`

### 그래프 탐색 — 100,000 노드 (SPARSE, RANDOM, 간선 100,000)

| 순위 | 알고리즘 | 실행 시간 | 메모리 사용 | 방문 노드 |
|-----|---------|----------|------------|----------|
| 1 | Bidirectional BFS | 38.8ms | 19,016KB | 100,000 |
| 2 | DFS (Iterative) | 39.3ms | 18,092KB | 100,000 |
| 3 | BFS | 48.6ms | 22,069KB | 100,000 |
| 4 | DFS (Recursive) | 48.9ms | 17,860KB | 100,000 |

출처: `/home/jun/project/sorting-and-graph/docs/graph/BENCHMARK.md`

1,000 노드에서는 전 알고리즘 0.73~0.97ms로 근소 (DFS 재귀가 0.73ms로 1위). 노드 100배 증가에 시간 약 50~60배 증가 — 원본은 "선형에 가까움"으로 평가.

## 종합 결론

- **복잡도 차이는 규모가 커질수록 기하급수로 벌어진다** — 100,000개에서 Quick 7.6ms vs Bubble 14,033ms (1,846배).
- **Insertion Sort는 거의 정렬된 데이터에서 7.8배 빨라진다** (29.7ms → 3.8ms) — "거의 정렬된 데이터·소규모(<50)"라는 예외 조건의 실증.
- **Merge Sort는 빠르지만 O(n) 추가 메모리** — 100,000개에서 ~10MB. 메모리 제한 환경에선 in-place인 Heap Sort가 대안.
- **그래프 탐색 4종은 실측에서도 비슷** (모두 O(V+E)) — 선택 기준은 속도보다 성질: 최단 경로는 BFS, 깊은 그래프는 DFS(Iterative, 스택 오버플로우 방지), 두 노드 간 경로는 Bidirectional BFS.
- 리소스 프로필 비교에서 100,000개 High(1GB/4core)가 Low보다 오히려 느린 케이스 존재 (Quick 7.6→13.1ms) — 원본은 수치만 제시, 원인 분석은 문서에 없음.

## 한계·남은 질문

- 반복 측정·편차(신뢰구간) 기록 없음 — 각 셀이 단일 실측값.
- Low vs High 리소스에서 결과가 역전된 원인(JIT·GC·코어 경합 등) 미분석.
- 그래프는 SPARSE·RANDOM 조합만 실측 — DENSE 그래프, 가중 그래프(다익스트라 등) 없음.
- 1,000,000+ 노드 예측치(~500ms)는 외삽이며 실측 아님.

## 원본 문서 지도

| 문서 | 내용 |
|------|------|
| `README.md` | 결과 요약, API 사용법, 리소스 프로필, 학습 포인트 |
| `docs/sorting/BENCHMARK.md` | 정렬 실측 전체 (크기별·상태별·리소스별·메모리·선택 가이드) |
| `docs/graph/BENCHMARK.md` | 그래프 실측 전체 (노드 수별·메모리·스케일링·선택 가이드) |
| `docs/sorting/*.md` | 알고리즘별 개념 문서 (bubble/selection/insertion/merge/quick/heap) |
| `docs/graph/dfs.md`, `docs/graph/bfs.md` | DFS·BFS 개념 문서 |
