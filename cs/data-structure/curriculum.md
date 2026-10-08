# 자료구조 — `cs/data-structure/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §2에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 44 · 검수 완료 0

> **번호 = 권장 학습 순서**(2026-09-28 재번호). 기존 노트 폴더(`data-structure/01~35`)는 원래 번호 그대로이며 영역 표의 노트 링크 칸이 대응을 맡는다. 🔧 칸 = **"쓰이는 곳"** — 다른 영역 leaf로 역링크된다.
> 근거: CLRS 3판(이하 CLRS), Sedgewick 『Algorithms』 4판, 각 자료구조 원논문.

## 2.0 기초 (2026-09-28 — 기초판은 독립 leaf, 심화 leaf가 선행으로 링크)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `data-structures-basics` | 자료구조 개관 기초판 — ADT·연결 리스트/스택/큐·선택 기준·재귀·트리·BST를 한 편에 | 필수 | 초안(Claude) | [01-data-structures-basics](01-data-structures-basics/) · [../foundations/data-structures-basics](../foundations/data-structures-basics/) |

## 2.1 선형 구조

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 02 | `adt-and-cost-contracts` | ADT = 연산 + 비용 계약. 같은 인터페이스, 다른 비용 | 필수 | 초안(Claude) | [02-adt-and-cost-contracts](02-adt-and-cost-contracts/) |
| 03 | `dynamic-array` | 연속 메모리 + 용량 2배 확장 = 분할상환 O(1) | 필수 | 초안(Claude) | [01-dynamic-array](01-dynamic-array/) |
| 04 | `linked-list` | 포인터 연결, O(1) 삽입·삭제, 캐시 비친화 | 필수 | 초안(Claude) | [02-linked-list](02-linked-list/) |
| 05 | `stack` | LIFO — 호출·되돌리기·파싱 | 필수 | 초안(Claude) | [03-stack](03-stack/) |
| 06 | `queue-deque` | FIFO·양방향 큐 | 필수 | 초안(Claude) | [04-queue-deque](04-queue-deque/) |
| 25 | `ring-buffer` | 고정 크기 원형 버퍼 — 생산자/소비자, 덮어쓰기 정책 | 권장 | 초안(Claude) | [25-ring-buffer](25-ring-buffer/) |

## 2.2 해시

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `hashmap` | 체이닝·로드 팩터·리해시·트리화 | 필수 | 초안(Claude) | [05-hashmap](05-hashmap/) |
| 08 | `open-addressing` | 선형·이차 탐사·로빈후드, tombstone | 권장 | 초안(Claude) | [29-open-addressing](29-open-addressing/) |
| 23 | `consistent-hashing` | 해시 링·가상 노드 — 노드 증감 시 최소 재배치 | 필수 | 초안(Claude) | [31-consistent-hashing](31-consistent-hashing/) |

## 2.3 트리·힙·트라이

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 09 | `binary-search-tree` | 정렬 불변식, 탐색 O(h) | 필수 | 초안(Claude) | [06-binary-search-tree](06-binary-search-tree/) |
| 10 | `heap` | 완전 이진 트리 + 힙 순서, top/pop O(log n) | 필수 | 초안(Claude) | [07-heap](07-heap/) |
| 12 | `trie` | 문자 단위 분기 — 접두사 질의 | 권장 | 초안(Claude) | [09-trie](09-trie/) |
| 13 | `radix-trie` | 압축 트라이(PATRICIA) | 필수 | 초안(Claude) | [20-radix-trie](20-radix-trie/) |
| 16 | `b-tree` | 다분기·노드=페이지, 높이 3~4로 수억 행 | 필수 | 초안(Claude) | [15-b-tree](15-b-tree/) |
| 17 | `red-black-tree` | 색 규칙으로 높이 O(log n) 보장 | 권장 | 초안(Claude) | [16-red-black-tree](16-red-black-tree/) |
| 26 | `timer-structures` | 타이머 힙 vs 계층형 타이머 휠 | 권장 | 초안(Claude) | [26-timer-structures](26-timer-structures/) |
| 33 | `segment-tree` | 구간 질의·갱신 O(log n) | 심화 | 초안(Claude) | [13-segment-tree](13-segment-tree/) |
| 34 | `fenwick-tree` | 비트 트릭 누적합 | 심화 | 초안(Claude) | [17-fenwick-tree](17-fenwick-tree/) |
| 37 | `sparse-table` | 정적 RMQ O(1) | 심화 | 초안(Claude) | [22-sparse-table](22-sparse-table/) |
| 38 | `splay-tree` | 접근 시 루트로 — 지역성 적응 | 심화 | 초안(Claude) | [23-splay-tree](23-splay-tree/) |
| 39 | `spatial-index` | R-tree·쿼드트리·geohash | 심화 | 초안(Claude) | [25-spatial-index](25-spatial-index/) |
| 42 | `interval-tree` | 겹치는 구간 질의 | 심화 | 초안(Claude) | [30-interval-tree](30-interval-tree/) |

## 2.4 그래프·집합·확률적 구조

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 11 | `graph` | 인접 행렬 vs 리스트 | 필수 | 초안(Claude) | [08-graph](08-graph/) |
| 15 | `union-find` | 경로 압축 + 랭크 | 권장 | 초안(Claude) | [14-union-find](14-union-find/) |
| 20 | `bloom-filter` | "없음"은 확실, "있음"은 확률 | 필수 | 초안(Claude) | [11-bloom-filter](11-bloom-filter/) |
| 21 | `probabilistic-counting` | HyperLogLog·Count-Min | 권장 | 초안(Claude) | [19-probabilistic-counting](19-probabilistic-counting/) |
| 22 | `skip-list` | 확률적 다층 연결 리스트 | 권장 | 초안(Claude) | [12-skip-list](12-skip-list/) |
| 35 | `bitset` | 비트 단위 집합·Roaring | 권장 | 초안(Claude) | [18-bitset](18-bitset/) |

## 2.5 문자열·영속·동시성 구조

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 24 | `inverted-index` | 단어→문서 목록 | 권장 | 초안(Claude) | [32-inverted-index](32-inverted-index/) |
| 27 | `merkle-tree` | 해시의 트리 — 부분 검증 | 권장 | 초안(Claude) | [27-merkle-tree](27-merkle-tree/) |
| 29 | `concurrent-data-structures` | 락 기반·lock-free 큐·해시맵, ABA | 심화 | 초안(Claude) | [29-concurrent-data-structures](29-concurrent-data-structures/) |
| 36 | `suffix-array` | 모든 접미사 정렬 | 심화 | 초안(Claude) | [21-suffix-array](21-suffix-array/) |
| 40 | `persistent` | 구조 공유로 버전 유지 | 심화 | 초안(Claude) | [26-persistent](26-persistent/) |
| 41 | `rope` | 트리로 쪼갠 문자열 | 심화 | 초안(Claude) | [28-rope](28-rope/) |

## 2.6 시스템 구현형 (구현 챕터)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 14 | `lru-cache` | 해시맵 + 이중 연결 리스트, 교체 정책 계열(LRU/LFU/CLOCK/W-TinyLFU) | 필수 | 초안(Claude) | [10-lru-cache](10-lru-cache/) |
| 18 | `lsm-tree` | memtable + SSTable + compaction | 필수 | 초안(Claude) | [24-lsm-tree](24-lsm-tree/) |
| 19 | `lsm-merge-model` | LSM 병합 모델 — 레벨·티어 트레이드오프 | 심화 | 초안(Claude) | [19-lsm-merge-model](19-lsm-merge-model/) · [lsm-merge-model](lsm-merge-model/) |
| 28 | `resize-thrashing` | 동적 배열 확장/축소 임계값이 붙으면 resize 반복 | 권장 | 초안(Claude) | [../systems/thrashing](../systems/thrashing/) |
| 30 | `filesystem` | inode·디렉터리 트리 구현 | 권장 | 초안(Claude) | [33-filesystem](33-filesystem/) |
| 31 | `allocator` | free list·버디·단편화 | 권장 | 초안(Claude) | [35-allocator](35-allocator/) |
| 32 | `dependency-resolver` | 위상정렬·사이클·버전 해결 | 권장 | 초안(Claude) | [34-dependency-resolver](34-dependency-resolver/) |

## 2.7 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 43 | `ds-symptom-index` | 역색인: `ConcurrentModificationException`, 해시 성능 절벽, `StackOverflowError`, 무한 큐 OOM, resize 스파이크, 캐시 적중률 절벽 | 필수 | 초안(Claude) | [43-ds-symptom-index](43-ds-symptom-index/) |
| 44 | `ds-incidents` | 실사건: HashDoS(28C3, 2011) → Java 8 HashMap 트리화·Python 해시 랜덤화 · JDK7 HashMap 동시 resize 무한 루프 | 권장 | 초안(Claude) | [44-ds-incidents](44-ds-incidents/) |
